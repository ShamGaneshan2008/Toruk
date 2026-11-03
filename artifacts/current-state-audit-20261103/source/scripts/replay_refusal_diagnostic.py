"""Replay saved refusal histories without replacing their backbone or selector."""

import argparse
import hashlib
import json
from pathlib import Path

from toruk_lm.chat_foundation import PretrainedChatBackend


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--backbone-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh output path")
    reference = json.loads(args.reference.read_text())
    backend = PretrainedChatBackend(args.backbone_dir)
    if backend.model_id != reference["model"]:
        raise ValueError("refusing comparison with a different backbone")
    rows = []
    for original in reference["rows"]:
        if original["response"]["metrics"]["mode"] != "BASELINE":
            continue
        if original["scenario"] not in ("fresh_math", "full_history_matched"):
            continue
        budget = original.get("max_new_tokens", reference.get("max_new_tokens", 32))
        response = backend.reply_with_metrics(
            original["request"], budget, mode="BASELINE", temperature=0, top_p=1
        )
        old = original["response"]
        rows.append(
            {
                "scenario": original["scenario"],
                "history": original["request"],
                "settings": {
                    "mode": "BASELINE",
                    "temperature": 0,
                    "top_p": 1,
                    "max_new_tokens": budget,
                },
                "before": old,
                "after": response,
                "same_answer": old["answer"] == response["answer"],
                "same_prompt_token_counts": all(
                    old["metrics"][key] == response["metrics"][key]
                    for key in ("input_tokens", "selected_context_tokens")
                ),
            }
        )
    report = {
        "model": backend.model_id,
        "reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
        "backbone_manifest": json.loads((args.backbone_dir / "toruk-backbone.json").read_text()),
        "generation_config": backend.model.generation_config.to_dict(),
        "rows": rows,
        "historical_toruk_replay": (
            "BLOCKED: original evaluated M6 selector absent; not substituted"
        ),
        "interpretation": (
            "Diagnostic only. An identical refusal is backbone/history behavior, "
            "not a transport fix."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(
            row["scenario"],
            row["settings"]["max_new_tokens"],
            "same",
            row["same_answer"],
            "prompt counts match",
            row["same_prompt_token_counts"],
            repr(row["after"]["answer"]),
        )


if __name__ == "__main__":
    main()
