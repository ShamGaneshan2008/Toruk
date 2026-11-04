"""Frozen paired chat evaluation; no model training or prompt tuning."""

import argparse
import ctypes
import json
import platform
import string
import time
from pathlib import Path
from typing import Any

from toruk_lm.chat_foundation import PretrainedChatBackend

MAX_PRIVATE_BYTES = 3 * 1024**3


def private_bytes() -> int | None:
    if platform.system() != "Windows":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
            ("PrivateUsage", ctypes.c_size_t),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    process = ctypes.windll.kernel32.GetCurrentProcess
    process.restype = ctypes.c_void_p
    info = ctypes.windll.psapi.GetProcessMemoryInfo
    info.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong)
    info.restype = ctypes.c_int
    if not info(process(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.PrivateUsage)


def correct(answer: str, case: dict[str, Any]) -> bool:
    normalized = answer.casefold().strip(string.whitespace + string.punctuation)
    accepted = [value.casefold() for value in case["accepted"]]
    forbidden = [value.casefold() for value in case["forbidden"]]
    match = (
        any(value in normalized for value in accepted)
        if case.get("match") == "contains"
        else normalized in accepted
    )
    return match and not any(value in normalized for value in forbidden)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in rows if "metrics" in row]
    return {
        "quality_correct": sum(bool(row.get("correct")) for row in rows),
        "quality_total": len(rows),
        "failures": len(rows) - len(successes),
        "input_tokens": sum(row["metrics"]["input_tokens"] for row in successes),
        "selected_tokens": sum(row["metrics"]["selected_context_tokens"] for row in successes),
        "output_tokens": sum(row["metrics"]["output_tokens"] for row in successes),
        "latency_ms": sum(row["metrics"]["response_ms"] for row in successes),
        "memory_used_cases": sum(row["metrics"]["memory_used"] for row in successes),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired BASELINE/TORUK chat evaluation")
    parser.add_argument("--backbone-dir", type=Path, required=True)
    parser.add_argument("--selector-checkpoint", type=Path, required=True)
    parser.add_argument(
        "--fixture", type=Path, default=Path("configs/chat-foundation-eval-v1.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh output file")
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    if fixture.get("kind") != "chat-foundation-eval-v1" or len(fixture["cases"]) != 7:
        parser.error("expected frozen seven-category fixture")
    started = time.perf_counter()
    backend = PretrainedChatBackend(args.backbone_dir, args.selector_checkpoint)
    result: dict[str, Any] = {
        "fixture": str(args.fixture),
        "model": backend.model_id,
        "selector": backend.selector.checkpoint_id if backend.selector else None,
        "modes": {"BASELINE": [], "TORUK": []},
        "status": "RUNNING",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in fixture["cases"]:
        for mode in ("BASELINE", "TORUK"):
            try:
                response = backend.reply_with_metrics(
                    case["messages"],
                    fixture["max_new_tokens"],
                    mode=mode,
                    temperature=fixture["temperature"],
                    top_p=fixture["top_p"],
                )
                row = {
                    "id": case["id"],
                    "category": case["category"],
                    "answer": response["answer"],
                    "correct": correct(response["answer"], case),
                    "metrics": response["metrics"],
                }
            except Exception as error:
                row = {"id": case["id"], "category": case["category"], "error": str(error)}
            result["modes"][mode].append(row)
            observed = private_bytes()
            result["private_bytes"] = observed
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            if observed is not None and observed > MAX_PRIVATE_BYTES:
                raise MemoryError("Chat evaluation exceeded 3 GiB private memory limit")
    baseline = summarize(result["modes"]["BASELINE"])
    toruk = summarize(result["modes"]["TORUK"])
    result["summary"] = {"BASELINE": baseline, "TORUK": toruk}
    result["efficiency_verified"] = (
        baseline["quality_correct"] > 0
        and toruk["quality_correct"] > 0
        and toruk["memory_used_cases"] > 0
        and toruk["quality_correct"] >= baseline["quality_correct"]
        and toruk["failures"] <= baseline["failures"]
        and toruk["selected_tokens"] < baseline["selected_tokens"]
    )
    result["seconds"] = round(time.perf_counter() - started, 3)
    result["status"] = "COMPLETE"
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(
        json.dumps(
            {"efficiency_verified": result["efficiency_verified"], "seconds": result["seconds"]}
        )
    )


if __name__ == "__main__":
    main()
