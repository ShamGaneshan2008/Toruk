"""Compare fresh inference with a saved recall experiment, excluding timing and RSS."""

import argparse
import json
from pathlib import Path
from typing import Any

FIELDS = (
    "case",
    "answer",
    "prompt_ids",
    "correct",
    "unsupported",
    "failure",
    "evidence_retained",
    "selected_evidence",
    "scan_bytes",
    "source_bytes",
)
METRICS = ("input_tokens", "selected_context_tokens", "output_tokens", "selected_message_ids")


def compare(reference: Path, replay: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"reference": str(reference), "replay": str(replay), "stages": {}}
    for stage in ("development", "heldout"):
        runs = []
        for directory in (reference, replay):
            rows = [
                json.loads(line)
                for line in (directory / f"{stage}.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            keyed = {(row["case"]["id"], row["method"]): row for row in rows}
            if len(rows) != 48 or len(keyed) != 48:
                raise ValueError(f"Incomplete or duplicate {stage} rows in {directory}")
            runs.append(keyed)
        original, fresh = runs
        if original.keys() != fresh.keys():
            raise ValueError(f"Case/method mismatch in {stage}")
        differences = []
        for key, row in original.items():
            other = fresh[key]
            changed = [field for field in FIELDS if row[field] != other[field]]
            changed.extend(
                f"metrics.{field}"
                for field in METRICS
                if row["metrics"][field] != other["metrics"][field]
            )
            if changed:
                differences.append({"case": key[0], "method": key[1], "fields": changed})
        result["stages"][stage] = {"rows": 48, "differences": differences}
    result["exact_reproduction"] = all(
        not stage["differences"] for stage in result["stages"].values()
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.reference, args.replay)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
    if not result["exact_reproduction"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
