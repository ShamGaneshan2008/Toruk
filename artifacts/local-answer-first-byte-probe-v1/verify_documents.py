"""Verify links, table values and whitespace without loading any model."""

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def main():
    audit = json.loads((BASE / "audit.json").read_text(encoding="utf-8"))
    report = ROOT / "docs/research/local-answer-first-byte-probe-v1-results.md"
    text = report.read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| train-")]
    assert len(rows) == len(audit["failures"]) == 16
    for line, case in zip(rows, audit["failures"], strict=True):
        cells = [part.strip() for part in line.split("|")[1:-1]]
        expected = [
            case["id"],
            f"{case['expected_id']}/{case['predicted_id']}",
            f"{case['signed_gold_vs_best_other']:.6f}",
            f"{case['expected_probability_eligible']:.6f}",
        ]
        expected.extend(
            f"{case['controls'][cell]['signed_gold_vs_best_other']:.6f}"
            for cell in ("601-ordinary", "601-recurrent", "947-recurrent")
        )
        assert cells == expected, case["id"]
        assert case["rank"] == 2 and all(c["rank"] == 1 for c in case["controls"].values())
    measured = [json.loads(line) for line in (BASE / "measurements.jsonl").read_text().splitlines()]
    assert len(measured) == 260
    assert not any(m["near_tied_gold"] or m["near_tied_decision"] for m in measured)
    assert "30.1875 s" in text and "44.734275 s" in text and "696156160 bytes" in text
    assert "3.671875 /1.839691 s" in text
    documents = [report, ROOT / "docs/research/local-answer-first-byte-probe-v1-protocol.md"]
    source_files = [
        ROOT / "scripts/first_byte_probe.py",
        ROOT / "tests/test_first_byte_probe.py",
        BASE / "verify_saved.py",
        Path(__file__),
        BASE / "run_offline_checks.py",
    ]
    links = 0
    for path in documents + source_files:
        raw = path.read_bytes()
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n"), path
        assert all(line == line.rstrip() for line in raw.decode("utf-8").splitlines()), path
    for path in documents:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            assert (path.parent / target).is_file(), target
            links += 1
    print(
        json.dumps(
            dict(
                status="PASS",
                failure_rows=16,
                passing_comparisons=48,
                measurements=260,
                links=links,
                model_execution=False,
            )
        )
    )


if __name__ == "__main__":
    main()
