"""Check the new report against saved records; no model execution."""

import hashlib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    summary = read(BASE / "summary.json")
    report = ROOT / "docs/research/local-answer-first-token-review-v1-results.md"
    text = report.read_text(encoding="utf-8")
    table = [line for line in text.splitlines() if line.startswith("| train-")]
    assert len(table) == len(summary["case_comparisons"]) == 16
    for row, case in zip(table, summary["case_comparisons"], strict=True):
        parts = [p.strip() for p in row.split("|")[1:-1]]
        expected = [case["id"], f"{case['expected_id']}/{case['error_id']}"]
        for cell in ("947-ordinary", "601-ordinary", "601-recurrent", "947-recurrent"):
            expected.append(f"{case['cells'][cell]['expected_minus_observed_error']:.6f}")
            assert case["cells"][cell]["expected_rank"] == (2 if cell == "947-ordinary" else 1)
        assert parts == expected
    reg = read(BASE / "registration.json")
    assert hashlib.sha256((BASE / "registration.json").read_bytes()).hexdigest() in text
    for path in (ROOT / reg_path for reg_path in reg["sources"]):
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == reg["sources"][path.relative_to(ROOT).as_posix()]
        )
    for name in (
        "docs/research/local-answer-first-token-review-v1-protocol.md",
        "docs/research/local-answer-paired-batch-v1-proposal.md",
    ):
        assert reg["sources"][name] in text
    records = [json.loads(line) for line in (BASE / "records.jsonl").read_text().splitlines()]
    assert len(records) == 260 and all(r["reproduces_archived_first"] for r in records)
    assert sum(r["reference_observed_error_id"] is not None for r in records) == 128
    assert all(
        r["isolated_forward_cpu_wall"] is None and not r["new_forward_pass"] for r in records
    )
    assert summary["missing_m_reproduced"]
    new_cost = read(BASE / "execution/cost.json")
    assert new_cost["complete_process_lifetimes"] and new_cost["active_processes"] == 0
    assert new_cost["status"] == "PASS" and new_cost["cpu"] == 3.65625
    assert new_cost["cpu"] == new_cost["user_cpu"] + new_cost["kernel_cpu"]
    assert new_cost["wall"] <= 60 and new_cost["peak_private"] <= 2147483648
    assert all(r["returncode"] == 0 for r in read(BASE / "checks.json")["commands"])
    links = 0
    docs = [
        report,
        ROOT / "docs/research/local-answer-first-token-review-v1-protocol.md",
        ROOT / "docs/research/local-answer-paired-batch-v1-proposal.md",
    ]
    for path in docs:
        raw = path.read_bytes()
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
        assert all(line == line.rstrip() for line in raw.decode("utf-8").splitlines())
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", raw.decode("utf-8")):
            assert (path.parent / link).is_file(), link
            links += 1
    print(
        json.dumps(
            dict(
                status="PASS",
                cases=16,
                comparisons=64,
                records=260,
                reference_error_records=128,
                links=links,
                model_execution=False,
            )
        )
    )


if __name__ == "__main__":
    main()
