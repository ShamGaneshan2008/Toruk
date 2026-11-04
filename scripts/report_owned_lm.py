"""Summarize immutable owned-LM raw outputs without additional model inference."""

import argparse
import json
from pathlib import Path
from typing import Any

from toruk_lm.owned_training import write_json


def report(run: Path) -> dict:
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    groups: dict[str, list[dict[str, Any]]] = {}
    failures: list[dict[str, Any]] = []
    for path in sorted((run / "heldout").glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        key = (
            result["variant"]
            + "/"
            + ("rolling" if result["rolling_diagnostic"] else result["ablation"])
        )
        groups.setdefault(key, []).append(result)
        if key == "memory_on/full":
            failures.extend(
                {
                    "seed": result["seed"],
                    "id": row["id"],
                    "category": row["category"],
                    "expected": row["expected"],
                    "answer": row["generation"]["answer"],
                    "evidence": row["evidence"],
                }
                for row in result["rows"]
                if not row["correct"]
            )
    aggregates = {}
    table = [
        "| Variant / inference | NLL seeds | Correct | Unsupported unknown | Wrong nonempty | "
        "Train s | Inference s | Forward positions |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, results in groups.items():
        rows = [row for result in results for row in result["rows"]]
        variant = results[0]["variant"]
        training = [
            value for name, value in summary["training"].items() if name.endswith("-" + variant)
        ]
        # Exclude ordinary_matched when aggregating ordinary.
        train_seconds = sum(value["seconds"] for value in training)
        value = {
            "nll_seeds": {str(result["seed"]): result["nll"] for result in results},
            "perplexity_seeds": {
                str(result["seed"]): result["byte_perplexity"] for result in results
            },
            "correct": sum(row["correct"] for row in rows),
            "n": len(rows),
            "unsupported_unknown": sum(row["unsupported"] for row in rows),
            "wrong_nonempty": sum(row["wrong_nonempty"] for row in rows),
            "stale": sum(row["stale"] for row in rows),
            "empty": sum(row["empty"] for row in rows),
            "invalid_utf8": sum(row["invalid_utf8"] for row in rows),
            "budget_exhausted": sum(row["generation"]["budget_exhausted"] for row in rows),
            "training_seconds": train_seconds,
            "training_cpu_seconds": sum(value["cpu_seconds"] for value in training),
            "training_targets": sum(value["training_targets_total"] for value in training),
            "generation_seconds": sum(row["generation_seconds"] for row in rows),
            "nll_seconds": sum(row["nll_seconds"] for row in rows),
            "generation_forward_positions": sum(
                row["generation"]["forward_positions"] for row in rows
            ),
            "prompt_tokens": sum(row["generation"]["input_tokens"] for row in rows),
            "generated_tokens": sum(len(row["generation"]["generated_ids"]) for row in rows),
            "memory_commits": sum(row["generation"]["commits"] for row in rows),
            "allocated_state_bytes": max(
                row["generation"]["allocated_state_bytes"] for row in rows
            ),
            "selector_work": 0,
            "peak_process_rss": max(
                result["memory"]["process_lifetime_peak_rss"] for result in results
            ),
            "categories": {
                category: {
                    "correct": sum(row["correct"] for row in rows if row["category"] == category),
                    "n": sum(row["category"] == category for row in rows),
                }
                for category in results[0]["categories"]
            },
        }
        aggregates[key] = value
        losses = "/".join(f"{nll:.4f}" for nll in value["nll_seeds"].values())
        table.append(
            f"| {key} | {losses} | {value['correct']}/{len(rows)} | "
            f"{value['unsupported_unknown']} | {value['wrong_nonempty']} | "
            f"{train_seconds:.2f} | {value['generation_seconds']:.3f} | "
            f"{value['generation_forward_positions']} |"
        )
    write_json(run / "aggregates.json", aggregates)
    write_json(run / "failed-cases.json", failures)
    (run / "table.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print("\n".join(table))
    print(
        json.dumps(
            {
                "study_seconds": summary["seconds"],
                "cpu_seconds": summary["cpu_seconds"],
                "criterion": summary["criterion"],
                "aggregates": aggregates,
            },
            indent=2,
        )
    )
    return aggregates


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    report(parser.parse_args().run)
