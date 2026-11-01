"""Run matched local chat probes on a pinned Ollama backbone."""

import argparse
import ctypes
import json
import urllib.request
from pathlib import Path

from toruk_lm.ollama_chat import OLLAMA_ORIGIN, OllamaChatBackend

REFUSAL = (
    "I'm sorry for any confusion, but as a chatbot, I don't have the capability "
    "to access or interact with online content."
)
EARLIER = [
    {"role": "user", "content": "hello"},
    {"role": "assistant", "content": "Hello! How can I help you today?"},
    {"role": "user", "content": "what are you?"},
    {"role": "assistant", "content": "I'm a chatbot designed to assist users with various topics."},
    {"role": "user", "content": "i am JinSakai"},
    {
        "role": "assistant",
        "content": (
            "I'm sorry for any confusion, but as a chatbot, I don't have the ability "
            "to assist with specific queries or provide information about specific topics."
        ),
    },
]


def available_ram_gib() -> float:
    fields = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong)
        for name in (
            "ullTotalPhys",
            "ullAvailPhys",
            "ullTotalPageFile",
            "ullAvailPageFile",
            "ullTotalVirtual",
            "ullAvailVirtual",
            "ullAvailExtendedVirtual",
        )
    ]
    memory = type("MemoryStatus", (ctypes.Structure,), {"_fields_": fields})()
    memory.dwLength = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise OSError("Cannot read Windows memory status")
    return round(memory.ullAvailPhys / 2**30, 3)


def running_model(model_name: str) -> dict:
    with urllib.request.urlopen(OLLAMA_ORIGIN + "/api/ps", timeout=5) as response:
        models = json.load(response)["models"]
    return next(model for model in models if model["name"] == model_name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--selector-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ram_before = available_ram_gib()
    backend = OllamaChatBackend(args.model, args.digest, args.selector_checkpoint)
    rows = []
    for mode in ("BASELINE", "TORUK"):
        history = list(EARLIER)
        for prompt, budget in (
            ("open youtube", 32),
            ("what is 5", 32),
            ("what is 5+5", 32),
            ("what is 5+5", 64),
        ):
            history.append({"role": "user", "content": prompt})
            result = backend.reply_with_metrics(history, budget, mode=mode)
            rows.append(
                {
                    "mode": mode,
                    "scenario": "generated_conversation",
                    "request": list(history),
                    "budget": budget,
                    "response": result,
                }
            )
            history.append({"role": "assistant", "content": result["answer"]})
        fresh = [{"role": "user", "content": "what is 5+5"}]
        rows.append(
            {
                "mode": mode,
                "scenario": "fresh_math",
                "request": fresh,
                "budget": 32,
                "response": backend.reply_with_metrics(fresh, 32, mode=mode),
            }
        )
        matched = [
            *EARLIER,
            {"role": "user", "content": "open youtube"},
            {"role": "assistant", "content": REFUSAL},
            {"role": "user", "content": "what is 5"},
            {"role": "assistant", "content": REFUSAL},
            {"role": "user", "content": "what is 5+5"},
        ]
        rows.append(
            {
                "mode": mode,
                "scenario": "matched_refusal_history",
                "request": matched,
                "budget": 32,
                "response": backend.reply_with_metrics(matched, 32, mode=mode),
            }
        )
    loaded = running_model(args.model)
    report = {
        "model": backend.model_id,
        "digest": args.digest,
        "available_ram_gib_before": ram_before,
        "available_ram_gib_after": available_ram_gib(),
        "ollama_size_vram_bytes": loaded["size_vram"],
        "ollama_context_length": loaded["context_length"],
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
