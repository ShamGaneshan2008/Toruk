"""Fresh checkpoint inference replay before conversational pilot work."""

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

import torch

from toruk_lm.owned_data import load_data
from toruk_lm.owned_training import evaluate, load, write_json


def stable(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: stable(item)
            for key, item in value.items()
            if key not in {"seconds", "cpu_seconds", "memory", "generation_seconds", "nll_seconds"}
        }
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def replay(reference: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    rows = load_data(reference / "data/heldout.json", "heldout")
    results = []
    start = time.perf_counter()
    for source in sorted((reference / "heldout").glob("*.json")):
        old = json.loads(source.read_text(encoding="utf-8"))
        checkpoint = Path(old["checkpoint"])
        model, saved = load(checkpoint)
        new = evaluate(
            checkpoint,
            rows,
            output / source.name,
            budget=16,
            ablation=old["ablation"],
            rolling=old["rolling_diagnostic"],
        )
        if stable(old) != stable(new):
            raise ValueError(f"owned inference did not reproduce: {source.name}")
        results.append(
            {
                "condition": source.stem,
                "nll": new["nll"],
                "correct": new["correct"],
                "questions": new["questions"],
                "parameters": sum(p.numel() for p in model.parameters()),
                "training_targets": saved["targets"],
                "seconds": new["seconds"],
                "memory": new["memory"],
            }
        )
    write_json(
        output / "replay.json",
        {
            "status": "PASS",
            "conditions": results,
            "answers": sum(row["questions"] for row in results),
            "seconds": time.perf_counter() - start,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "new_training_targets": 0,
        },
    )
    print(f"PASS: {len(results)} conditions / {sum(row['questions'] for row in results)} answers")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    replay(args.reference, args.output)
