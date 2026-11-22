"""Bounded saved-only derivation and offline verification controller."""

import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job import controller_record  # noqa: E402


def main():
    python = [sys.executable, "-B"]
    commands = [
        ("derive", [*python, "scripts/audit_first_token_margins.py", "derive"]),
        ("audit", [*python, "scripts/audit_first_token_margins.py", "audit"]),
        (
            "focused-tests",
            [
                *python,
                "-m",
                "pytest",
                "-q",
                "tests/test_first_byte_probe.py",
                "tests/test_first_token_margin_review.py",
                "-o",
                f"cache_dir={BASE / 'pytest-cache'}",
                "--basetemp",
                str(BASE / "pytest-tmp"),
            ],
        ),
        (
            "original-study-audit",
            [
                *python,
                "artifacts/local-answer-dev-v1/verify_saved.py",
                "--output",
                str(BASE / "original-study-audit.json"),
            ],
        ),
        (
            "diagnosis-documents",
            [*python, "artifacts/local-answer-first-byte-v1/verify_document.py"],
        ),
        (
            "probe-documents",
            [*python, "artifacts/local-answer-first-byte-probe-v1/verify_documents.py"],
        ),
        ("frozen-sources", [*python, "scripts/check_frozen_sources.py"]),
        ("lint", [*python, "-m", "ruff", "check", "."]),
        ("format", [*python, "-m", "ruff", "format", "--check", "src", "tests", "scripts"]),
        (
            "type",
            [
                *python,
                "-m",
                "mypy",
                "--follow-imports=skip",
                "scripts/audit_first_token_margins.py",
            ],
        ),
        ("dependencies", [*python, "-m", "pip", "check"]),
        ("diff-check", ["git", "diff", "--check"]),
    ]
    receipts = []
    write = lambda name, value: (BASE / name).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    # Pre-freeze editing/check time is outside this Job, and is not invented.
    write(
        "preflight.json",
        dict(
            before_review_freeze=True,
            cpu_wall_unknown=True,
            model_forwards=0,
            lint_attempts=[dict(e501_errors=5), dict(e501_errors=1), dict(e501_errors=0)],
            resolution="formatting and one wrapped string literal before freeze",
            type_check="PASS in both pre-freeze invocations",
            training_attempts=0,
        ),
    )
    with controller_record(BASE / "execution"):
        try:
            for name, command in commands:
                began = time.perf_counter()
                with (BASE / f"{name}.log").open("xb") as stream:
                    process = subprocess.run(
                        command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False
                    )
                receipts.append(
                    dict(
                        name=name,
                        command=command,
                        returncode=process.returncode,
                        wall=time.perf_counter() - began,
                    )
                )
                print(json.dumps(receipts[-1]), flush=True)
                if process.returncode:
                    raise RuntimeError(f"review failed: {name}")
        finally:
            write(
                "checks.json",
                dict(commands=receipts, new_forward_passes=0, complete_cost="execution/cost.json"),
            )


if __name__ == "__main__":
    main()
