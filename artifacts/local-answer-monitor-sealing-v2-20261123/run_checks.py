"""Record read-only validation of sealing v2 and byte preservation of committed evidence."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]

def main():
    py = sys.executable
    logdir = OUT / "checks-execution-001"
    commands = [
        ("lint", [py, "-B", "-m", "ruff", "check", "--no-cache", "."], 0, None),
        ("format", [py, "-B", "-m", "ruff", "format", "--check", "--no-cache",
                    "src", "tests", "scripts"], 0, None),
        ("types", [py, "-B", "-m", "mypy", "--follow-imports=silent",
                   "--cache-dir", str(OUT / "mypy-cache"), "scripts/lifetime_job_v2.py"], 0, None),
        ("diff-check", ["git", "diff", "--check"], 0, None),
        ("staged-diff-check", ["git", "diff", "--cached", "--check"], 0, None),
        ("v1-registered-auditor", [py, "-B", "scripts/paired_batch_dev.py", "audit"],
         1, "observation seal"),
        ("v1-independent-auditor", [py, "-I", "-S", "-B",
         "artifacts/local-answer-paired-batch-dev-v1/verify_saved.py"],
         2, "OBSERVATIONS_VERIFIED_WITH_REGISTERED_SEAL_FAILURE"),
        ("frozen-sources", [py, "-B", "scripts/check_frozen_sources.py"], 0, None),
    ]
    results = []
    for name, command, expected, needle in commands:
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        for suffix, raw in (("stdout", process.stdout), ("stderr", process.stderr)):
            with (logdir / f"{name}.{suffix}.log").open("x", encoding="utf-8", newline="\n") as f:
                f.write(raw)
        match = process.returncode == expected and (
            needle is None or needle in process.stdout + process.stderr)
        results.append(dict(name=name, command=command, returncode=process.returncode,
                            expected_returncode=expected, matched_expectation=match,
                            note="Existing v1 failure retained" if expected else "PASS" if match else "FAIL"))
        if not match:
            break
    original = json.loads((ROOT / "artifacts/local-answer-paired-batch-dev-v1/artifact-inventory.json").read_text())
    for name, meta in original["files"].items():
        path = ROOT / name
        assert path.stat().st_size == meta["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == meta["sha256"], name
    review = json.loads((ROOT / "artifacts/local-answer-paired-batch-v1-preservation-20261123/review.json").read_text())
    paths = set(subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=ROOT
    ).decode().splitlines())
    assert len(paths) == 335
    assert not any(p.endswith(".pt") for p in paths)
    assert not subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT).strip()
    assert not subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT).strip()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip() == (
        "392e002caa203d17a837fde7e759187e59a81301")
    assert not review["facts"]["registered_integrity_gate_passed"]
    testlog = (OUT / "tests-execution-001/output.log").read_text()
    assert "24 passed" in testlog
    source = (ROOT / "scripts/lifetime_job_v2.py").read_text()
    tests = (ROOT / "tests/test_lifetime_job_v2.py").read_text()
    assert "import torch" not in source + tests and "toruk_lm" not in source + tests
    record = dict(status="V2_CHECKS_PASS_WITH_V1_FAILURES_UNCHANGED",
        commands=results, all_expectations_met=len(results)==len(commands) and
                all(r["matched_expectation"] for r in results),
        focused_tests=24, focused_tests_passed=True,
        tests_model_construction=False, tests_checkpoint_loading=False,
        original_inventoried_files_unchanged=337,
        evidence_commit="392e002caa203d17a837fde7e759187e59a81301",
        evidence_commit_files=335, weights_committed=False, registered_v1_integrity_pass=False,
        harness_fix_committed=False)
    with (OUT / "checks.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    print(json.dumps(record, indent=2))
    assert record["all_expectations_met"]

if __name__ == "__main__":
    main()
