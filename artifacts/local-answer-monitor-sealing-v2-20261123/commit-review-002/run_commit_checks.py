"""Commit review checks only. No paired-batch execution or model operations."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REVIEW = Path(__file__).resolve().parent
OUT = REVIEW.parent
ROOT = OUT.parents[1]

def main():
    logs = REVIEW / "check-logs"
    logs.mkdir(exist_ok=False)
    py = sys.executable
    commands = [
        ("mypy", [py, "-B", "-m", "mypy", "--follow-imports=silent", "--cache-dir",
                  str(OUT / "mypy-cache-review-002"), "scripts/lifetime_job_v2.py"]),
        ("ruff-lint", [py, "-B", "-m", "ruff", "check", "--no-cache", "."]),
        ("ruff-format", [py, "-B", "-m", "ruff", "format", "--check", "--no-cache",
                         "src", "tests", "scripts"]),
        ("staged-whitespace", ["git", "diff", "--cached", "--check"]),
        ("retest-seal", [py, "-B", "scripts/lifetime_job_v2.py", "verify", "--directory",
                        str(OUT / "tests-execution-002"), "--expected-seal-sha256",
                        "996a74cfd4dada2201bef85c6c9cb41ebaa6deed612652dd77637827a81e4f00"]),
        ("prior-check-seal", [py, "-B", "scripts/lifetime_job_v2.py", "verify", "--directory",
                             str(OUT / "checks-execution-001"), "--expected-seal-sha256",
                             "84769890bd0d05fd6c4d02e6700d47b475a9e72e79ae53e74a60f1d4ef5633f0"]),
    ]
    results = []
    for label, command in commands:
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        for suffix, raw in (("stdout", process.stdout), ("stderr", process.stderr)):
            with (logs / f"{label}.{suffix}.log").open("x", encoding="utf-8", newline="\n") as f:
                f.write(raw)
        results.append(dict(check=label, command=command, returncode=process.returncode))
        if process.returncode:
            break
    testlog = (OUT / "tests-execution-002/output.log").read_text()
    assert "24 passed" in testlog
    original = json.loads((ROOT / "artifacts/local-answer-paired-batch-dev-v1/artifact-inventory.json").read_text())
    for name, meta in original["files"].items():
        path = ROOT / name
        assert path.stat().st_size == meta["bytes"] and hashlib.sha256(
            path.read_bytes()).hexdigest() == meta["sha256"], name
    previous = json.loads((OUT / "inventory.json").read_text())
    for name, meta in previous["files"].items():
        path = ROOT / name
        assert path.stat().st_size == meta["bytes"] and hashlib.sha256(
            path.read_bytes()).hexdigest() == meta["sha256"], name
    assert not subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT).strip()
    report = dict(
        status="PASS" if len(results) == len(commands) and
               all(p["returncode"] == 0 for p in results) else "FAIL",
        base_evidence_commit="392e002caa203d17a837fde7e759187e59a81301",
        checks=results,
        disposable_tests=dict(count=24, result="24 passed in 6.20s",
            command=[py, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/test_lifetime_job_v2.py", "tests/test_lifetime_job.py",
                     "--basetemp", "artifacts/local-answer-monitor-sealing-v2-20261123/pytest-tmp-002"]),
        original_paired_batch_files_unchanged=337,prior_v2_inventory_files_unchanged=130,
        original_v1_seals_or_gates_modified=False,paired_batch_v1_executed=False,
        model_fit_or_checkpoint_loading=False,heldout_data_access=False,push=False,
        lifecycle_review=dict(
            seal_after_watch_returns=True,
            watch_closes_descendants_and_streams_before_final_cost=True,
            final_cost_written_before_seal=True,
            premature_workload_pass_failure_path_found=False,
            incomplete_lifetimes_or_receipts_rejected=True,
            stopped_workloads_remain_stop=True,
            seal_publication_failure_retains_records_and_rejects_verification=True,
            assumptions="Execution API and observer-owned output directory; fabricated receipts or unrelated writers are outside the contract."
        ))
    with (REVIEW / "final-review.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("checks","disposable_tests")}, indent=2))
    assert report["status"] == "PASS"

if __name__ == "__main__":
    main()
