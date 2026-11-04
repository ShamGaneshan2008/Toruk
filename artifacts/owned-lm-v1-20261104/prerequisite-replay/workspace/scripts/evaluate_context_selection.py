"""Matched synthetic evaluation through a real local Node proxy and model worker."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import random
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from check import source_identity
from smoke_vercel_local import ROOT, free_port, read, wait_ready

from toruk_lm.chat_foundation import backbone_spec
from toruk_lm.inference_server import validate_request

ABSTENTION = re.compile(
    r"unknown|don't know|do not know|cannot determine|can't determine|conflict|not provided|"
    r"not specified|not enough information|unclear|impossible to determine|haven't provided|"
    r"haven't told|don't have",
    re.I,
)


def contains(text: str, phrase: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase.casefold()) + r"(?!\w)", text.casefold()))


def score(answer: str, case: dict[str, Any]) -> dict[str, bool]:
    correct = any(contains(answer, x) for x in case["accepted"]) and not any(
        contains(answer, x) for x in case["forbidden"]
    )
    return {
        "correct": correct,
        "unsupported_flag": not correct and not bool(ABSTENTION.search(answer)),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for mode in ("BASELINE", "TORUK"):
        group = [r for r in rows if r["mode"] == mode]
        valid = [r for r in group if r.get("http_status") == 200 and "metrics" in r]
        tokens = [r["metrics"]["selected_context_tokens"] for r in valid]
        output[mode] = {
            "n": len(group),
            "correct": sum(r["score"]["correct"] for r in group),
            "unsupported_flags": sum(r["score"]["unsupported_flag"] for r in group),
            "failures": len(group) - len(valid),
            "mean_selected_tokens": statistics.mean(tokens) if tokens else None,
            "median_selected_tokens": statistics.median(tokens) if tokens else None,
            "selected_tokens": sum(tokens),
            "output_tokens": sum(r["metrics"]["output_tokens"] for r in valid),
            "available_tokens": sum(r["metrics"]["input_tokens"] for r in valid),
            "mean_e2e_ms": statistics.mean(r["e2e_ms"] for r in valid) if valid else None,
            "median_e2e_ms": statistics.median(r["e2e_ms"] for r in valid) if valid else None,
            "all_evidence_retained": sum(r["all_evidence_retained"] for r in valid),
        }
    baseline, toruk = output["BASELINE"], output["TORUK"]
    output["selected_token_reduction_pct"] = (
        100 * (1 - toruk["selected_tokens"] / baseline["selected_tokens"])
        if baseline["selected_tokens"]
        else None
    )
    output["target_met_on_this_fixture"] = bool(
        not baseline["failures"]
        and not toruk["failures"]
        and output["selected_token_reduction_pct"] >= 35
        and toruk["correct"] >= baseline["correct"]
        and toruk["unsupported_flags"] <= baseline["unsupported_flags"]
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--backbone-dir", type=Path, required=True)
    parser.add_argument("--context-selector", choices=("lexical-v1", "lexical-v2"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = args.fixture.read_bytes()
    fixture = json.loads(raw)
    if fixture["schema"] != "toruk-context-eval-v1":
        parser.error("Only the versioned synthetic evaluation schema is supported")
    settings = fixture["settings"]
    if settings != {"max_new_tokens": 32, "temperature": 0, "top_p": 1}:
        parser.error("Decoding differs from frozen protocol")
    for case in fixture["cases"]:
        validate_request({"messages": case["messages"], **settings})
        if not set(case["required_evidence"]) <= {f"m{i}" for i in range(len(case["messages"]))}:
            parser.error("Invalid evidence identifiers")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    model_files = {}
    for name in (
        "toruk-backbone.json",
        "config.json",
        "generation_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
    ):
        model_files[name] = hashlib.sha256((args.backbone_dir / name).read_bytes()).hexdigest()
    spec = backbone_spec(json.loads((args.backbone_dir / "toruk-backbone.json").read_text()))
    result: dict[str, Any] = {
        "schema": "toruk-context-result-v1",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "fixture": fixture,
        "selector": args.context_selector,
        "backbone": spec,
        "model_files_sha256": model_files,
        "source": source_identity(),
        "libraries": {
            name: importlib.metadata.version(name)
            for name in ("torch", "transformers", "safetensors")
        },
        "generation_config": json.loads((args.backbone_dir / "generation_config.json").read_text()),
        "tokenizer_config": json.loads((args.backbone_dir / "tokenizer_config.json").read_text()),
        "settings": settings,
        "status": "RUNNING",
        "rows": [],
    }
    backend_port, web_port = free_port(), free_port()
    env = dict(os.environ, TORUK_BACKEND_TOKEN="context-evaluation-local-token")
    web_env = dict(env, TORUK_BACKEND_URL=f"http://127.0.0.1:{backend_port}", PORT=str(web_port))
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with (
        (args.output_dir / "backend.log").open("w", encoding="utf-8") as bl,
        (args.output_dir / "web.log").open("w", encoding="utf-8") as wl,
    ):
        backend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "toruk_lm.inference_server",
                "--backbone-dir",
                str(args.backbone_dir),
                "--context-selector",
                args.context_selector,
                "--port",
                str(backend_port),
            ],
            cwd=ROOT,
            env=env,
            stdout=bl,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        web = subprocess.Popen(
            ["node", "web/vercel/scripts/dev.mjs"],
            cwd=ROOT,
            env=web_env,
            stdout=wl,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        path = args.output_dir / "raw.json"
        try:
            origin = f"http://127.0.0.1:{web_port}"
            wait_ready(f"http://127.0.0.1:{backend_port}/api/status", backend)
            wait_ready(origin + "/api/status", web)
            _, status = read(f"http://127.0.0.1:{backend_port}/api/status")
            assert isinstance(status, dict) and status["ready"] and status["memory_supported"]
            assert status["model"] == f"{spec['model']}@{spec['revision'][:12]}"
            result["backend_status"] = status
            # One unscored, fixed warmup per mode. Request order is balanced by a fixed RNG.
            for mode in ("BASELINE", "TORUK"):
                assert (
                    read(
                        origin + "/api/chat",
                        {
                            "messages": [{"role": "user", "content": "Hello"}],
                            "mode": mode,
                            **settings,
                        },
                    )[0]
                    == 200
                )
            rng = random.Random(23)
            for case in fixture["cases"]:
                modes = ["BASELINE", "TORUK"]
                rng.shuffle(modes)
                for mode in modes:
                    payload = {"messages": case["messages"], "mode": mode, **settings}
                    start = time.perf_counter()
                    code, response = read(origin + "/api/chat", payload)
                    elapsed = (time.perf_counter() - start) * 1000
                    row: dict[str, Any] = {
                        "id": case["id"],
                        "category": case["category"],
                        "mode": mode,
                        "request": payload,
                        "http_status": code,
                        "e2e_ms": round(elapsed, 3),
                    }
                    if code == 200:
                        assert isinstance(response, dict)
                        row.update(response)
                        row["score"] = score(response["answer"], case)
                        selected = set(response["metrics"]["selected_message_ids"])
                        row["required_evidence"] = case["required_evidence"]
                        row["all_evidence_retained"] = set(case["required_evidence"]) <= selected
                        row["selected_evidence"] = [
                            {"id": f"m{i}", **message}
                            for i, message in enumerate(case["messages"])
                            if f"m{i}" in selected
                        ]
                    else:
                        row.update(
                            error=response, score={"correct": False, "unsupported_flag": False}
                        )
                    result["rows"].append(row)
                    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            result["summary"] = summarize(result["rows"])
            result["status"] = "COMPLETE"
            path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result["summary"], indent=2))
        finally:
            for process in (web, backend):
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
