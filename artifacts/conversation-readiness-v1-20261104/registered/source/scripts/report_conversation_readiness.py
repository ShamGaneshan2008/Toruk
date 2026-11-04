"""Derived diagnostic summary; semantic review is post-hoc and never model input."""

import argparse
import json
from pathlib import Path

from toruk_lm.owned_training import write_json


def report(run: Path) -> None:
    diagnostics = json.loads((run / "diagnostics.json").read_text(encoding="utf-8"))
    rows = diagnostics["rows"]
    review = []
    for row in rows:
        # Human-reviewed equivalences in this diagnostic: missing terminal period
        # on Unknown, and the two full-sentence expressions of 5+5=10. These do
        # not change the fixed exact score, readiness gate or any training input.
        semantic = row["scores"]["exact"]
        note = "Exact score retained."
        if row["origin"] == "external_pretrained":
            if row["category"] == "uncertainty" and row["raw_answer"] == "Unknown":
                semantic, note = True, "Appropriate uncertainty; punctuation-only exact mismatch."
            if row["raw_answer"] in (
                "The sum of five plus five is ten.",
                "The sum of 5 and 5 is 10.",
            ):
                semantic, note = True, "Correct math in prose; no refusal carryover."
        review.append(
            {
                "case": row["case"],
                "origin": row["origin"],
                "semantic_correct": semantic,
                "note": note,
                "unknown_false_assertion": (
                    row["category"] == "uncertainty"
                    and row["origin"] == "toruk_owned"
                    and "is red" in row["raw_answer"]
                ),
                "review_scope": "False assertions classified only on insufficient-evidence cases.",
            }
        )
    write_json(run / "posthoc-semantic-review.json", review)
    aggregates = {}
    for origin in ("toruk_owned", "external_pretrained"):
        selected = [row for row in rows if row["origin"] == origin]
        judged = [row for row in review if row["origin"] == origin]
        aggregates[origin] = {
            "n": len(selected),
            "exact": sum(row["scores"]["exact"] for row in selected),
            "posthoc_semantic": sum(row["semantic_correct"] for row in judged),
            "unknown_false_assertions": sum(row["unknown_false_assertion"] for row in judged),
            "seconds": sum(row["seconds"] for row in selected),
            "cpu_seconds": sum(row["cpu_seconds"] for row in selected),
            "peak_rss": max(row["memory"]["process_lifetime_peak_rss"] for row in selected),
            "errors": sum(bool(row.get("error")) for row in selected),
            "repeated_word_trigrams": sum(row["scores"]["repeated_trigrams"] for row in selected),
            "unique_nonempty_outputs": len(
                {row["raw_answer"] for row in selected if row["raw_answer"]}
            ),
            "prompt_tokens": sum(
                row.get("generation", {}).get("input_tokens", 0)
                if origin == "toruk_owned"
                else row["response"]["metrics"]["selected_context_tokens"]
                for row in selected
            ),
            "output_tokens": sum(
                len(row.get("generation", {}).get("generated_ids", []))
                if origin == "toruk_owned"
                else row["response"]["metrics"]["output_tokens"]
                for row in selected
            ),
            "owned_forward_positions": sum(
                row.get("generation", {}).get("forward_positions", 0) for row in selected
            ),
            "categories": {
                category: {
                    "n": sum(row["category"] == category for row in selected),
                    "exact": sum(
                        row["scores"]["exact"] for row in selected if row["category"] == category
                    ),
                }
                for category in sorted({row["category"] for row in selected})
            },
        }
    write_json(run / "aggregates.json", aggregates)
    table = [
        "| Case | Expected | Owned before: raw output | External Qwen: raw output | Pilot |",
        "|---|---|---|---|---|",
    ]
    for owned in (row for row in rows if row["origin"] == "toruk_owned"):
        external = next(
            row
            for row in rows
            if row["origin"] == "external_pretrained" and row["case"] == owned["case"]
        )

        def cell(text: str) -> str:
            return (
                "`"
                + json.dumps(text, ensure_ascii=True).replace("|", "\\|").replace("`", "\\u0060")
                + "`"
            )

        table.append(
            f"| {owned['case']} | {cell(owned['expected'])} | "
            f"{cell(owned.get('error') or owned['raw_answer'])} | "
            f"{cell(external['raw_answer'])} | NOT_RUN |"
        )
    (run / "raw-output-table.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print(json.dumps(aggregates, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    report(parser.parse_args().run)
