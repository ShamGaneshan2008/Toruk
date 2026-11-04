"""Report the fixed-budget experiment against its reproduced envelope control."""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_rows(run: Path, stage: str, method: str) -> list[dict[str, Any]]:
    return [
        row
        for line in (run / f"{stage}.jsonl").read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["method"] == method
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    baseline = json.loads((args.reference / "summary.json").read_text(encoding="utf-8"))
    candidate = json.loads((args.run / "summary.json").read_text(encoding="utf-8"))
    before, after = baseline["heldout"]["new"], candidate["heldout"]["new"]
    gates = {
        "correct_at_least_6": after["correct"] >= 6,
        "unsupported_proxy_at_most_2": after["unsupported_proxy"] <= 2,
        "request_ms_per_correct_at_least_10_percent_lower": (
            after["correct"] > 0
            and after["request_ms"] / after["correct"]
            <= 0.9 * before["request_ms"] / before["correct"]
        ),
    }
    result: dict[str, Any] = {
        "gates": gates,
        "success": all(gates.values()),
        "before": before,
        "after": after,
        "changes": {},
        "distant_facts": {},
        "baseline_parity": {},
    }
    for stage in ("development", "heldout"):
        original = read_rows(args.reference, stage, "new")
        fresh = read_rows(args.run, stage, "new")
        if len(original) != 12 or len(fresh) != 12:
            raise ValueError("incomplete comparison")
        changes = []
        for old, new in zip(original, fresh, strict=True):
            if old["case"] != new["case"]:
                raise ValueError("evaluation questions changed")
            if old["answer"] != new["answer"] or old["correct"] != new["correct"]:
                changes.append(
                    {
                        "id": old["case"]["id"],
                        "before": old["answer"],
                        "after": new["answer"],
                        "before_correct": old["correct"],
                        "after_correct": new["correct"],
                        "before_evidence_retained": old["evidence_retained"],
                        "after_evidence_retained": new["evidence_retained"],
                    }
                )
        result["changes"][stage] = changes
        result["distant_facts"][stage] = {}
        for label, rows in (("before", original), ("after", fresh)):
            known = [row for row in rows if row["case"]["task"] in ("exact", "gist", "vague_clear")]
            result["distant_facts"][stage][label] = {
                "correct": sum(row["correct"] for row in known),
                "n": len(known),
                "all_marked_sources_retained": sum(row["evidence_retained"] for row in known),
                "failures": dict(Counter(row["failure"] for row in rows if row["failure"])),
            }
        for method in ("recent", "lexical", "old"):
            a = read_rows(args.reference, stage, method)
            b = read_rows(args.run, stage, method)
            parity = len(a) == len(b) == 12 and all(
                x["case"] == y["case"]
                and x["prompt_ids"] == y["prompt_ids"]
                and x["answer"] == y["answer"]
                for x, y in zip(a, b, strict=True)
            )
            result["baseline_parity"][f"{stage}/{method}"] = parity
            if not parity:
                raise ValueError(f"baseline changed: {stage}/{method}")
    output = args.run / "comparison.json"
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"gates": gates, "success": result["success"]}, indent=2))


if __name__ == "__main__":
    main()
