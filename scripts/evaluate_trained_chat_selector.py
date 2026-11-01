"""One held-out paired chat run for the frozen v1 selector protocol."""

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

from evaluate_local_backbone import gpu_memory_mib
from probe_ollama_backbone import available_ram_gib

from toruk_lm.chat_selector import FORMAT
from toruk_lm.ollama_chat import OllamaChatBackend

UNKNOWN = (
    "don't know",
    "do not know",
    "not supplied",
    "not provided",
    "no information",
    "cannot determine",
)


def contains(answer: str, value: str) -> bool:
    return (
        re.search(r"(?<!\w)" + re.escape(value.casefold()) + r"(?!\w)", answer.casefold())
        is not None
    )


def score(answer: str, case: dict) -> tuple[bool, bool]:
    if case["expected"] is None:
        uncertainty = any(phrase in answer.casefold() for phrase in UNKNOWN)
        fabricated = bool(re.search(r"\b(?:TRAIN|DEV|FINAL)KEY\d+\b", answer, re.I))
        return uncertainty and not fabricated, not uncertainty or fabricated
    correct = contains(answer, case["expected"])
    if case["forbidden"]:
        correct = correct and not contains(answer, case["forbidden"])
    return correct, False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--selector-checkpoint", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh output path; do not overwrite final results")
    manifest_raw = (args.data_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    final_raw = (args.data_dir / "final.jsonl").read_bytes()
    if hashlib.sha256(final_raw).hexdigest() != manifest["split_sha256"]["final"]:
        raise ValueError("final split hash mismatch")
    saved = json.loads(args.selector_checkpoint.read_text(encoding="utf-8"))
    if (
        saved.get("format") != FORMAT
        or saved.get("data_manifest_sha256") != hashlib.sha256(manifest_raw).hexdigest()
        or saved.get("train_sha256") != manifest["split_sha256"]["train"]
        or saved.get("dev_sha256") != manifest["split_sha256"]["dev"]
    ):
        raise ValueError("selector checkpoint is not bound to this frozen dataset")
    cases = [json.loads(line) for line in final_raw.splitlines()]
    if any(case["split"] != "final" for case in cases):
        raise ValueError("final split label mismatch")
    memory_before = {"available_ram_gib": available_ram_gib(), "gpu_memory_mib": gpu_memory_mib()}
    backend = OllamaChatBackend(args.model, args.digest, args.selector_checkpoint)
    started = time.perf_counter()
    rows = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        for mode in ("BASELINE", "TORUK"):
            try:
                response = backend.reply_with_metrics(
                    case["messages"], 32, mode=mode, temperature=0, top_p=1
                )
                answer, metrics = response["answer"], response["metrics"]
                quality, unsupported = score(answer, case)
                selected = {int(value[1:]) for value in metrics["selected_message_ids"]}
                row = {
                    "id": case["id"],
                    "category": case["category"],
                    "mode": mode,
                    "messages": case["messages"],
                    "evidence_ids": case["evidence_ids"],
                    "expected": case["expected"],
                    "forbidden": case["forbidden"],
                    "answer": answer,
                    "quality": quality,
                    "unsupported": unsupported,
                    "evidence_retained": all(index in selected for index in case["evidence_ids"])
                    if case["evidence_ids"]
                    else None,
                    "unknown_older_selected": len(
                        selected - set(range(len(case["messages"]) - 3, len(case["messages"])))
                    )
                    > 0
                    if not case["evidence_ids"]
                    else None,
                    "metrics": metrics,
                }
            except Exception as error:
                row = {
                    "id": case["id"],
                    "category": case["category"],
                    "mode": mode,
                    "messages": case["messages"],
                    "evidence_ids": case["evidence_ids"],
                    "expected": case["expected"],
                    "forbidden": case["forbidden"],
                    "error": f"{type(error).__name__}: {error}",
                    "quality": False,
                    "unsupported": case["expected"] is None,
                    "evidence_retained": False if case["evidence_ids"] else None,
                    "unknown_older_selected": None,
                }
            rows.append(row)
            args.output.write_text(
                json.dumps({"status": "RUNNING", "rows": rows}, indent=2) + "\n", encoding="utf-8"
            )
            print(case["id"], mode, row["quality"], flush=True)
    summary = {}
    for mode in ("BASELINE", "TORUK"):
        subset = [row for row in rows if row["mode"] == mode]
        valid = [row for row in subset if "metrics" in row]
        summary[mode] = {
            "quality": sum(row["quality"] for row in subset),
            "cases": len(subset),
            "unsupported_unknown": sum(row["unsupported"] for row in subset),
            "errors": len(subset) - len(valid),
            "known_evidence_retained": sum(row["evidence_retained"] is True for row in subset),
            "known_evidence_cases": sum(row["evidence_retained"] is not None for row in subset),
            "unknown_older_selected": sum(row["unknown_older_selected"] is True for row in subset),
            "selected_tokens": sum(row["metrics"]["selected_context_tokens"] for row in valid),
            "output_tokens": sum(row["metrics"]["output_tokens"] for row in valid),
            "total_prompt_eval_tokens": sum(
                row["metrics"]["total_prompt_eval_tokens"] for row in valid
            ),
            "selector_scan_bytes": sum(row["metrics"]["selector_scan_bytes"] for row in valid),
            "selector_ms": round(sum(row["metrics"]["selector_ms"] for row in valid), 3),
            "response_ms": round(sum(row["metrics"]["response_ms"] for row in valid), 3),
        }
    result = {
        "schema": "toruk-chat-selector-final-v1",
        "status": "COMPLETE",
        "protocol": "docs/research/chat-selector-v1-protocol.md",
        "data_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "final_sha256": manifest["split_sha256"]["final"],
        "selector_sha256": backend.selector.sha256 if backend.selector else None,
        "selector_kind": getattr(backend.selector, "kind", None),
        "model": backend.model_id,
        "digest": args.digest,
        "settings": {"temperature": 0, "top_p": 1, "max_new_tokens": 32, "max_prompt_tokens": 512},
        "memory_before": memory_before,
        "memory_after": {
            "available_ram_gib": available_ram_gib(),
            "gpu_memory_mib": gpu_memory_mib(),
        },
        "wall_seconds": round(time.perf_counter() - started, 3),
        "summary": summary,
        "rows": rows,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
