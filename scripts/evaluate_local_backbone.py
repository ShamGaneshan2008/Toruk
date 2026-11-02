"""Exploratory paired replay on a pinned local Ollama model; never rewrites v2 results."""

import argparse
import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

from evaluate_chat_release_v2 import aggregate, score_answer, validate_fixture
from probe_ollama_backbone import available_ram_gib

from toruk_lm.ollama_chat import OLLAMA_ORIGIN, OllamaChatBackend


def gpu_memory_mib() -> dict[str, int] | None:
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5,
        )
        total, used, free = (int(part.strip()) for part in output.splitlines()[0].split(","))
        return {"total": total, "used": used, "free": free}
    except (OSError, ValueError, subprocess.SubprocessError, IndexError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--selector-checkpoint", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=Path("configs/chat-release-eval-v2.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh output path; historical experiments are immutable")
    raw = args.fixture.read_bytes()
    fixture = json.loads(raw)
    validate_fixture(fixture)
    before = {"available_ram_gib": available_ram_gib(), "gpu_memory_mib": gpu_memory_mib()}
    backend = OllamaChatBackend(args.model, args.digest, args.selector_checkpoint)
    rows = []
    started = time.perf_counter()
    for case in fixture["cases"]:
        messages = [{"role": item["role"], "content": item["content"]} for item in case["messages"]]
        for mode in ("BASELINE", "TORUK"):
            try:
                response = backend.reply_with_metrics(
                    messages,
                    fixture["max_new_tokens"],
                    mode=mode,
                    temperature=fixture["temperature"],
                    top_p=fixture["top_p"],
                )
                row = {
                    "id": case["id"],
                    "category": case["category"],
                    "mode": mode,
                    "messages": messages,
                    "answer": response["answer"],
                    "score": score_answer(response["answer"], case),
                    "metrics": response["metrics"],
                }
            except Exception as error:
                row = {
                    "id": case["id"],
                    "category": case["category"],
                    "mode": mode,
                    "messages": messages,
                    "error": f"{type(error).__name__}: {error}",
                    "score": score_answer("", case),
                }
            rows.append(row)
            print(f"{case['id']} {mode}: {row['score']['quality']}", flush=True)
    with urllib.request.urlopen(OLLAMA_ORIGIN + "/api/ps", timeout=5) as response:
        loaded = json.load(response)["models"]
    running = next((item for item in loaded if item["name"] == args.model), None)
    summary = {
        mode: aggregate([row for row in rows if row["mode"] == mode])
        for mode in ("BASELINE", "TORUK")
    }
    result = {
        "schema": "toruk-local-backbone-exploratory-v1",
        "note": "Exploratory reuse of the frozen v2 fixture; no preregistered success claim.",
        "fixture": str(args.fixture),
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "model": backend.model_id,
        "digest": args.digest,
        "selector_sha256": backend.selector.sha256 if backend.selector else None,
        "settings": {key: fixture[key] for key in ("max_new_tokens", "temperature", "top_p")},
        "memory_before": before,
        "memory_after": {
            "available_ram_gib": available_ram_gib(),
            "gpu_memory_mib": gpu_memory_mib(),
        },
        "ollama_loaded": running,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "summary": summary,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
