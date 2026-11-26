"""Classify each original failure and verify unchanged-code reproduction offline."""

import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent


def failures(path):
    return [line.split(" - ")[0].removeprefix("FAILED ")
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.startswith("FAILED tests/")]


def main():
    original = json.loads((BASE / "original-failures.json").read_text())
    expected = [line.split(" - ")[0].removeprefix("FAILED ") for line in original["failures"]]
    repeated = failures(BASE / "reproduced-ubuntu-job.log")
    # Hosted lines carry timestamps; inspect their summary text without modifying logs.
    if not repeated:
        repeated = ["tests/" + line.split("FAILED tests/", 1)[1].split(" - ")[0]
                    for line in (BASE / "reproduced-ubuntu-job.log").read_text(encoding="utf-8").splitlines()
                    if "FAILED tests/" in line]
    assert len(expected) == len(repeated) == 28 and set(expected) == set(repeated)
    records = []
    for node, raw in zip(expected, original["failures"], strict=True):
        if "test_first_byte_probe.py" in node:
            category = "optional-local-checkpoints"
            fix = "Explicit missing-input skip; portable plan checks and separate exact-hash CLI"
        elif "test_lifetime_job.py" in node:
            category = "native-Windows-Job"
            fix = "Run unchanged test on Windows; explicit Ubuntu skip"
        elif "test_lifetime_job_v2.py" in node:
            category = "sealer-fixture-outside-checkout"
            fix = "Confine fresh pytest temporary files to checkout; native creation on Windows"
            if "interrupted_seal_publication" in node:
                category = "native-Windows-Job"
                fix = "Run unchanged test on Windows; explicit Ubuntu skip"
            if "missing_final_receipt" in node or "unclosed_final_receipt" in node:
                fix = "Checkout-confined fixture; keep unchanged portable rejection test on both OSes"
        elif "test_paired_batch_dev.py" in node:
            category = "archived-runtime-initialization"
            fix = "Keep recorded expected hashes; qualify archival test by runtime; diagnose both OSes"
        elif "test_qwen_development_v4.py" in node:
            category = "historical-versus-current-attributes"
            fix = "Verify original publication blob/hash-bound shallow snapshot; check current attrs separately"
        else:
            assert "test_qwen_long_history_v2.py" in node
            category = "native-ctypes-windll"
            fix = "Run unchanged test on Windows; explicit Ubuntu skip"
        records.append(dict(nodeid=node, original_failure=raw, category=category, fix=fix,
                            reproduced_on_unchanged_ubuntu=True))
    result = dict(original_run=45439669299, reproduced_job=139824029804,
                  original_count=28, repeated_count=28,
                  category_counts=dict(Counter(r["category"] for r in records)), failures=records)
    (BASE / "failure-classification.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["| Original failed test | Classification | Repair / execution contract |",
             "| --- | --- | --- |"]
    lines += [f"| `{r['nodeid']}` | {r['category']} | {r['fix']} |" for r in records]
    (BASE / "failure-table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "failures"}))


if __name__ == "__main__":
    main()
