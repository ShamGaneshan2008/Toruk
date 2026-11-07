"""Apply the frozen launch probes to the already installed, digest-pinned Ollama model."""

import argparse
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
from pathlib import Path
from typing import Any

import psutil
from qualify_chat_launch import aggregate, call, score, verify
from smoke_vercel_local import free_port

from toruk_lm.data import sha256_file, write_json

DIGEST = "a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72"


def run_ollama(root: Path, selected: bool) -> None:
    reg = verify(root)
    name = "ollama-trained-v2" if selected else "ollama-recent"
    output = root / name
    output.mkdir(parents=True, exist_ok=False)
    mode = "TORUK" if selected else "BASELINE"
    write_json(
        output / "registration.json",
        {
            "parent_registration_sha256": sha256_file(root / "registration.json"),
            "driver_sha256": sha256_file(Path(__file__)),
            "model": "llama3.2:latest",
            "digest": DIGEST,
            "selector": selected,
            "gate": reg["gate"],
            "scope": "Existing local Ollama service; no downloads or training.",
        },
    )
    backend_port, web_port = free_port(), free_port()
    origin, web_origin = f"http://127.0.0.1:{backend_port}", f"http://127.0.0.1:{web_port}"
    token = secrets.token_urlsafe(32)
    env = dict(os.environ, TORUK_BACKEND_TOKEN=token)
    env.pop("VERCEL_ENV", None)
    command = [
        sys.executable,
        "-m",
        "toruk_lm.inference_server",
        "--ollama-model",
        "llama3.2:latest",
        "--ollama-digest",
        DIGEST,
        "--port",
        str(backend_port),
    ]
    if selected:
        command += ["--selector-checkpoint", "artifacts/chat-selector-v2-20261101/selector.json"]
    rows: list[dict[str, Any]] = []
    peak = {"inference_client_rss_bytes": 0, "all_ollama_process_rss_bytes": 0}
    stop = threading.Event()
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    with (
        (output / "backend.log").open("w", encoding="utf-8") as log,
        (output / "web.log").open("w", encoding="utf-8") as web_log,
    ):
        start = time.perf_counter()
        backend = subprocess.Popen(command, env=env, stdout=log, stderr=log, creationflags=flags)
        web = subprocess.Popen(
            ["node", "web/vercel/scripts/dev.mjs"],
            env=dict(env, TORUK_BACKEND_URL=origin, PORT=str(web_port)),
            stdout=web_log,
            stderr=web_log,
            creationflags=flags,
        )

        def sample() -> None:
            while not stop.wait(0.1):
                try:
                    process = psutil.Process(backend.pid)
                    peak["inference_client_rss_bytes"] = max(
                        peak["inference_client_rss_bytes"],
                        sum(
                            p.memory_info().rss
                            for p in [process, *process.children(recursive=True)]
                        ),
                    )
                    ollama_bytes = 0
                    for process in psutil.process_iter(["name"]):
                        if "ollama" in (process.info["name"] or "").lower():
                            try:
                                ollama_bytes += process.memory_info().rss
                            except psutil.Error:
                                pass
                    peak["all_ollama_process_rss_bytes"] = max(
                        peak["all_ollama_process_rss_bytes"], ollama_bytes
                    )
                except psutil.Error:
                    pass

        thread = threading.Thread(target=sample, daemon=True)
        thread.start()

        def request(case: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
            payload = {
                "messages": list(messages),
                "mode": mode,
                "max_new_tokens": 64,
                "temperature": 0,
                "top_p": 1,
            }
            tick = time.perf_counter()
            code, response = call(web_origin + "/api/chat", payload)
            if code == 200:
                assert response["metrics"]["model"] == status["model"]
                assert response["metrics"]["backbone_digest"] == DIGEST
                assert response["metrics"]["mode"] == mode
            content = response.get("answer", "")
            row = {
                "id": case["id"],
                "category": case["category"],
                "request": payload,
                "http_status": code,
                "response": response,
                "content": content,
                "score": score(content, case),
                "wall_seconds": time.perf_counter() - tick,
            }
            rows.append(row)
            with (output / "raw.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row) + "\n")
            if len(rows) % 10 == 0:
                print(json.dumps({"mode": name, "requests_recorded": len(rows)}), flush=True)
            return row

        try:
            while time.perf_counter() - start < 185:
                try:
                    _, status = call(web_origin + "/api/status")
                    if status["ready"]:
                        break
                    if status.get("error_code") not in (None, "BACKEND_UNAVAILABLE"):
                        raise RuntimeError(status["error_code"])
                except urllib.error.URLError:
                    pass
                time.sleep(0.1)
            else:
                raise TimeoutError("Ollama startup exceeded the existing worker startup budget")
            startup = time.perf_counter() - start
            assert status["model"] == f"ollama/llama3.2:latest@{DIGEST[:12]}"
            model_snapshot = call("http://127.0.0.1:11434/api/ps")[1]
            suite = json.loads((root / "suite.json").read_text())
            for case in suite["cases"]:
                request(case, case["messages"])
            for key, case in suite["scenarios"].items():
                history: list[dict[str, str]] = []
                for index, prompt in enumerate(case["prompts"]):
                    history.append({"role": "user", "content": prompt})
                    row = request(
                        {**case, "id": f"generated-{key}-{index}", "category": "generated-" + key},
                        history,
                    )
                    row["scored_final_turn"] = index == len(case["prompts"]) - 1
                    if not row["content"]:
                        row["scored_final_turn"] = True
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
                    break
                history.append({"role": "assistant", "content": row["content"]})
            backend.terminate()
            backend.wait(timeout=10)
            outage_code, outage = call(
                web_origin + "/api/chat",
                {"messages": [{"role": "user", "content": "Hello"}], "mode": mode},
            )
            scored = [r for r in rows if r.get("scored_final_turn", True)]
            write_json(
                output / "results.json",
                {
                    "status": status,
                    "startup_seconds": startup,
                    "peak_processes": peak,
                    "ollama_model_snapshot_not_peak": model_snapshot,
                    "rows": rows,
                    "summary": aggregate(scored, reg["gate"]),
                    "all_request_metrics": aggregate(rows, reg["gate"])["summed_metrics"],
                    "identity_gate": "PASS",
                    "outage_503": outage_code == 503 and "answer" not in outage,
                    "scope": (
                        "Ollama GPU memory snapshot is not peak VRAM; process RSS includes "
                        "all local Ollama processes and may include unrelated service work. "
                        "No matched CPU-only total-cost comparison."
                    ),
                },
            )
            print(json.dumps({"mode": name, "summary": aggregate(scored, reg["gate"])}))
        except Exception as error:
            write_json(
                output / "execution-failure.json",
                {"type": type(error).__name__, "error": str(error), "rows_retained": len(rows)},
            )
            raise
        finally:
            stop.set()
            thread.join(timeout=2)
            for child in (web, backend):
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--selector", action="store_true")
    args = parser.parse_args()
    run_ollama(args.run, args.selector)
