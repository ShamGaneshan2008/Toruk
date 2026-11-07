"""Frozen local launch gate: real proxy/server/model calls, never canned answers."""

import argparse
import concurrent.futures
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import psutil
from smoke_vercel_local import free_port

from toruk_lm.data import sha256_file, write_json

GATE = Path("configs/chat-launch-gate-v1.json")
OWNED = Path("artifacts/conversation-format-v1-20261105/models/candidate/checkpoint.pt")
SELECTOR = Path("artifacts/chat-selector-v2-20261101/selector.json")
MODES: dict[str, dict[str, Any]] = {
    "qwen-recent": {"backbone": "artifacts/qwen-chat-001/backbone", "mode": "BASELINE"},
    "qwen-trained-v2": {
        "backbone": "artifacts/qwen-chat-001/backbone",
        "mode": "TORUK",
        "selector": str(SELECTOR),
    },
    "qwen-lexical-v2": {
        "backbone": "artifacts/qwen-chat-001/backbone",
        "mode": "TORUK",
        "heuristic": "lexical-v2",
    },
    "smollm-recent": {"backbone": "artifacts/chat-foundation-001/backbone", "mode": "BASELINE"},
    "ordinary-smoke": {
        "checkpoint": "artifacts/foundation-001/train/checkpoint.pt",
        "mode": "BASELINE",
    },
}


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def register(run: Path) -> None:
    run.mkdir(parents=True, exist_ok=False)
    gate = read(GATE)
    cases = read(Path(gate["frozen_cases"]))
    cases.append(
        {
            "id": "natural-hello",
            "category": "basic",
            "messages": [{"role": "user", "content": "Hello!"}],
            "answer": "",
            "accepted": ["hello", "hi", "hey"],
        }
    )
    scenarios = read(Path(gate["generated_scenarios"]))["scenarios"]
    suite = {
        "cases": cases,
        "scenarios": scenarios,
        "repetition_prompts": ["what is 5+5"] * 3,
        "repetition_history": cases[-2]["messages"][:-1],
    }
    assert cases[-2]["id"] == "test-observed-full-refusal"
    write_json(run / "suite.json", suite)
    paths = [
        GATE,
        Path(gate["frozen_cases"]),
        Path(gate["generated_scenarios"]),
        Path(__file__),
        OWNED,
        SELECTOR,
        run / "suite.json",
    ]
    paths += [
        Path("src/toruk_lm") / name
        for name in (
            "chat_foundation.py",
            "inference_server.py",
            "inference_worker.py",
            "owned_lm.py",
        )
    ]
    registration = {
        "schema": "toruk-chat-launch-registration-v1",
        "gate": gate,
        "modes": MODES,
        "files": {str(p): sha256_file(p) for p in paths},
        "starting_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "starting_tree_before_task": "clean (observed before gate changes)",
        "note": "Historical published probes; no new training. Gates frozen before new model calls.",
    }
    write_json(run / "registration.json", registration)


def score(answer: str, case: dict[str, Any]) -> dict[str, Any]:
    answer = answer.strip()
    expected = case.get("answer", "")
    category = case.get("category", "generated")
    if "accepted" in case:
        lower = answer.lower()
        correct = any(
            bool(re.search(r"\b" + re.escape(item) + r"\b", lower))
            if category == "basic"
            else item.lower() in lower
            for item in case["accepted"]
        ) and not any(item.lower() in lower for item in case.get("forbidden", []))
    elif category in ("instruction", "exact"):
        correct = answer == expected
    elif category == "uncertainty":
        correct = any(
            item in answer.lower()
            for item in (
                "unavailable",
                "don't know",
                "do not know",
                "not provided",
                "haven't",
                "cannot determine",
                "can't determine",
                "not enough",
                "don't have",
                "do not have",
            )
        )
    else:
        correct = bool(re.search(r"(?<!\w)" + re.escape(expected) + r"(?!\w)", answer))
        if case.get("obsolete"):
            correct = correct and case["obsolete"] not in answer
        if category in ("math", "refusal", "repetition"):
            correct = correct and not bool(
                re.search(
                    r"(?:can't|cannot|unable|don't have).*(?:access|browse|youtube|internet)",
                    answer,
                    re.I,
                )
            )
    triples = list(
        zip(answer.lower().split(), answer.lower().split()[1:], answer.lower().split()[2:])
    )
    return {
        "quality": bool(correct),
        "strict_exact": answer == expected if expected else None,
        "unsupported_proxy": bool(category == "uncertainty" or case.get("unsupported_case"))
        and not correct,
        "repeated_trigrams": len(triples) - len(set(triples)),
    }


def verify(run: Path) -> dict[str, Any]:
    reg = read(run / "registration.json")
    for name, expected in reg["files"].items():
        if sha256_file(Path(name)) != expected:
            raise ValueError(f"Registered input changed: {name}")
    return reg


def call(
    url: str, payload: Any = None, *, token: str | None = None, raw: bytes | None = None
) -> tuple[int, Any]:
    data = raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=70) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def aggregate(rows: list[dict[str, Any]], gate: dict[str, Any]) -> dict[str, Any]:
    categories: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        categories[row["category"]].append(row["score"]["quality"])
    counts = {
        key: {"correct": sum(values), "cases": len(values)} for key, values in categories.items()
    }
    q = gate["quality_gate"]
    passed = sum(row["score"]["quality"] for row in rows)
    unsupported = sum(row["score"]["unsupported_proxy"] for row in rows)
    repetition = sum(row["score"]["repeated_trigrams"] for row in rows)
    refusal_failures = sum(
        not r["score"]["quality"] for r in rows if r["category"] in ("refusal", "repetition")
    )
    exact_failures = sum(not r["score"]["quality"] for r in rows if r["category"] == "exact")
    http_ok = sum(r["http_status"] == 200 for r in rows)
    success = (
        passed / len(rows) >= q["minimum_overall_fraction"]
        and all(
            c["correct"] / c["cases"] >= q["minimum_each_category_fraction"]
            for c in counts.values()
        )
        and unsupported <= q["maximum_unsupported_unknown"]
        and refusal_failures <= q["maximum_refusal_math_failures"]
        and exact_failures <= q["maximum_exact_string_failures"]
        and repetition <= q["maximum_repeated_trigrams"]
        and http_ok == len(rows)
    )
    numeric = Counter()
    for row in rows:
        for key, value in row.get("response", {}).get("metrics", {}).items():
            if type(value) in (int, float):
                numeric[key] += value
    replies = Counter(r.get("content", "") for r in rows)
    return {
        "quality_gate": "PASS" if success else "FAIL",
        "correct": passed,
        "cases": len(rows),
        "categories": counts,
        "unsupported_proxy": unsupported,
        "repeated_trigrams": repetition,
        "refusal_math_failures": refusal_failures,
        "exact_string_failures": exact_failures,
        "http_ok": http_ok,
        "summed_metrics": dict(numeric),
        "distinct_replies": len(replies),
        "most_common_reply_count": replies.most_common(1)[0][1],
    }


def evaluate(run: Path, name: str) -> None:
    reg = verify(run)
    directory = run / name
    directory.mkdir(parents=True, exist_ok=False)
    spec = reg["modes"][name]
    backend_port, web_port = free_port(), free_port()
    origin, web_origin = f"http://127.0.0.1:{backend_port}", f"http://127.0.0.1:{web_port}"
    token = secrets.token_urlsafe(32)
    env = dict(os.environ, TORUK_BACKEND_TOKEN=token)
    env.pop("VERCEL_ENV", None)
    web_env = dict(env, TORUK_BACKEND_URL=origin, PORT=str(web_port))
    command = [sys.executable, "-m", "toruk_lm.inference_server", "--port", str(backend_port)]
    command += (
        ["--backbone-dir", spec["backbone"]]
        if "backbone" in spec
        else ["--checkpoint", spec["checkpoint"]]
    )
    if "selector" in spec:
        command += ["--selector-checkpoint", spec["selector"]]
    if "heuristic" in spec:
        command += ["--context-selector", spec["heuristic"]]
    stop = threading.Event()
    peak = {"rss_sum_bytes": 0, "private_sum_bytes": 0}
    rows: list[dict[str, Any]] = []
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with (
        (directory / "backend.log").open("w", encoding="utf-8") as log,
        (directory / "web.log").open("w", encoding="utf-8") as web_log,
    ):
        started = time.perf_counter()
        process = subprocess.Popen(command, env=env, stdout=log, stderr=log, creationflags=flags)
        web = subprocess.Popen(
            ["node", "web/vercel/scripts/dev.mjs"],
            env=web_env,
            stdout=web_log,
            stderr=web_log,
            creationflags=flags,
        )

        def sample() -> None:
            root = psutil.Process(process.pid)
            while not stop.wait(0.05):
                try:
                    info = [p.memory_info() for p in [root, *root.children(recursive=True)]]
                    peak["rss_sum_bytes"] = max(peak["rss_sum_bytes"], sum(i.rss for i in info))
                    peak["private_sum_bytes"] = max(
                        peak["private_sum_bytes"], sum(getattr(i, "private", 0) for i in info)
                    )
                except psutil.Error:
                    pass

        sampler = threading.Thread(target=sample, daemon=True)
        sampler.start()

        def cpu_seconds() -> float:
            try:
                root = psutil.Process(process.pid)
                values = [p.cpu_times() for p in [root, *root.children(recursive=True)]]
                return sum(c.user + c.system for c in values)
            except psutil.Error:
                return 0.0

        def request(case: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
            payload = {
                "messages": list(messages),
                "mode": spec["mode"],
                "max_new_tokens": reg["gate"]["external_output_tokens"],
                "temperature": 0,
                "top_p": 1,
            }
            tick, cpu = time.perf_counter(), cpu_seconds()
            code, result = call(web_origin + "/api/chat", payload)
            metrics = result.get("metrics", {})
            if code == 200:
                assert metrics["model"] == status["model"] and metrics["mode"] == spec["mode"]
                assert metrics["backbone"] == status["backbone"]
            answer = result.get("answer", "")
            row = {
                "id": case["id"],
                "category": case["category"],
                "request": payload,
                "http_status": code,
                "response": result,
                "content": answer,
                "score": score(answer, case),
                "wall_seconds": time.perf_counter() - tick,
                "inference_tree_cpu_seconds": cpu_seconds() - cpu,
            }
            rows.append(row)
            return row

        try:
            while True:
                if process.poll() is not None or time.perf_counter() - started > 125:
                    raise RuntimeError("Backend startup failed or exceeded budget")
                try:
                    _, status = call(web_origin + "/api/status")
                    if status["ready"]:
                        break
                    if status.get("error_code") not in (None, "BACKEND_UNAVAILABLE"):
                        raise RuntimeError(f"Requested model unavailable: {status['error_code']}")
                except urllib.error.URLError:
                    pass
                time.sleep(0.1)
            startup = time.perf_counter() - started
            direct_status = call(origin + "/api/status")[1]
            assert direct_status["model"] == status["model"]
            assert call(origin + "/status")[1]["model"] == status["model"]
            assert call(origin + "/healthz")[0] == 200
            suite = read(run / "suite.json")
            for case in suite["cases"]:
                request(case, case["messages"])
            for key, case in suite["scenarios"].items():
                history: list[dict[str, str]] = []
                for index, prompt in enumerate(case["prompts"]):
                    history.append({"role": "user", "content": prompt})
                    descriptor = {
                        **case,
                        "id": f"generated-{key}-{index}",
                        "category": "generated-" + key,
                    }
                    row = request(descriptor, history)
                    row["scored_final_turn"] = index == len(case["prompts"]) - 1
                    if not row["content"]:
                        row["scored_final_turn"] = True
                        row["rollout_stopped"] = "No assistant reply; remaining turns not sent."
                        break
                    history.append({"role": "assistant", "content": row["content"]})
            history = list(suite["repetition_history"])
            for index, prompt in enumerate(suite["repetition_prompts"]):
                history.append({"role": "user", "content": prompt})
                row = request(
                    {"id": f"refusal-repeat-{index}", "category": "repetition", "answer": "10"},
                    history,
                )
                if not row["content"]:
                    for remaining in range(index + 1, len(suite["repetition_prompts"])):
                        rows.append(
                            {
                                **row,
                                "id": f"refusal-repeat-{remaining}",
                                "http_status": 0,
                                "response": {
                                    "error": "Not sent: previous assistant reply unavailable."
                                },
                            }
                        )
                    break
                history.append({"role": "assistant", "content": row["content"]})
            # A simultaneous burst measures the one-generation admission policy, not queue throughput.
            barrier = threading.Barrier(4)
            payload = {
                "messages": [
                    {"role": "user", "content": "Explain photosynthesis in four sentences."}
                ],
                "max_new_tokens": 64,
                "mode": spec["mode"],
            }

            def overlap(_: int) -> dict[str, Any]:
                barrier.wait(timeout=10)
                tick = time.perf_counter()
                code, body = call(web_origin + "/api/chat", payload)
                return {"code": code, "seconds": time.perf_counter() - tick, "body": body}

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                concurrent = list(pool.map(overlap, range(4)))
            checks = {
                "identity": True,
                "health_aliases": True,
                "unauthorized_401": call(origin + "/api/infer", payload, token="incorrect")[0]
                == 401,
                "bad_json_400": call(web_origin + "/api/chat", raw=b"{")[0] == 400,
                "tokens_400": call(web_origin + "/api/chat", {**payload, "max_new_tokens": 65})[0]
                == 400,
                "message_bytes_400": call(
                    web_origin + "/api/chat",
                    {**payload, "messages": [{"role": "user", "content": "x" * 1025}]},
                )[0]
                == 400,
                "selector_mode_400": True
                if spec["mode"] == "TORUK"
                else call(web_origin + "/api/chat", {**payload, "mode": "TORUK"})[0] == 400,
            }
            if name == "qwen-recent":
                completed = subprocess.run(
                    ["node", "web/vercel/tests/ui.test.mjs"],
                    env=dict(
                        web_env,
                        TORUK_LIVE_WEB_URL=web_origin,
                        TORUK_TEST_BACKBONE=status["backbone"],
                    ),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=120,
                    creationflags=flags,
                )
                (directory / "live-ui.log").write_text(
                    completed.stdout + completed.stderr, encoding="utf-8"
                )
                checks["live_page_handlers"] = completed.returncode == 0
            process.terminate()
            process.wait(timeout=10)
            code, outage = call(web_origin + "/api/chat", payload)
            checks["outage_503"] = code == 503 and "answer" not in outage
            checks["secret_redaction"] = token not in json.dumps([status, rows, concurrent, outage])
            scored = [r for r in rows if r.get("scored_final_turn", True)]
            summary = aggregate(scored, reg["gate"])
            summary["all_request_metric_totals"] = aggregate(rows, reg["gate"])["summed_metrics"]
            summary["request_count"] = len(rows)
            checks["single_generation_slot"] = sorted(c["code"] for c in concurrent) == [
                200,
                503,
                503,
                503,
            ]
            checks["bounded_latency"] = all(r["wall_seconds"] <= 45 for r in rows)
            checks["bounded_startup"] = startup <= 120
            write_json(
                directory / "results.json",
                {
                    "status": status,
                    "direct_status": direct_status,
                    "startup_seconds": startup,
                    "peak_process_tree": peak,
                    "rows": rows,
                    "summary": summary,
                    "reliability": checks,
                    "concurrent": concurrent,
                    "reliability_gate": "PASS" if all(checks.values()) else "FAIL",
                    "scope": "Local Windows process tree; no Linux/cloud capacity guarantee.",
                },
            )
            print(
                json.dumps(
                    {
                        "mode": name,
                        "correct": summary["correct"],
                        "cases": summary["cases"],
                        "quality_gate": summary["quality_gate"],
                        "reliability": checks,
                    }
                )
            )
        finally:
            stop.set()
            sampler.join(timeout=2)
            for child in (web, process):
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=10)


def owned(run: Path) -> None:
    from toruk_lm.engine import setup
    from toruk_lm.owned_lm import OwnedSession
    from toruk_lm.owned_training import load

    reg = verify(run)
    target = run / "owned-cli.json"
    if target.exists():
        raise ValueError("use a fresh output path")
    setup(0, 1)
    model, _ = load(OWNED)
    rows = []
    for case in read(run / "suite.json")["cases"][:-1]:
        tick, cpu = time.perf_counter(), time.process_time()
        raw = ""
        generated: dict[str, Any] = {}
        try:
            generated = OwnedSession(model).generate(
                case["prefix"], reg["gate"]["owned_output_tokens"]
            )
            raw = str(generated["answer"])
            content = json.loads(raw)
            if not isinstance(content, str):
                raise ValueError("invalid owned response framing")
            result = {"answer": raw, "metrics": generated}
            code = 0  # This model is a research CLI, not an HTTP chat mode.
        except (ValueError, TypeError) as error:
            content, result, code = "", {"error": str(error), "generation": generated}, 0
        rows.append(
            {
                "id": case["id"],
                "category": case["category"],
                "content": content,
                "http_status": code,
                "response": result,
                "score": score(content, case),
                "raw_answer": raw,
                "seconds": time.perf_counter() - tick,
                "cpu_seconds": time.process_time() - cpu,
            }
        )
    write_json(
        target,
        {
            "origin": "Toruk-trained research CLI, not exposed by the chat server",
            "model": "toruk-owned-next-token-v1@" + sha256_file(OWNED),
            "checkpoint_bytes": OWNED.stat().st_size,
            "rows": rows,
            "summary": aggregate(rows, reg["gate"]),
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "evaluate", "owned"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--mode", choices=tuple(MODES), default="qwen-recent")
    args = parser.parse_args()
    if args.action == "register":
        register(args.run)
    elif args.action == "owned":
        owned(args.run)
    else:
        evaluate(args.run, args.mode)
