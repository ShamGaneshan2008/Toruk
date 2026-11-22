"""Single receipt for repository checks: no model imports, training or inference."""

import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = BASE / "verification"
PYTHON = [sys.executable, "-B"]


def main():
    commands = [
        (
            "probe-saved",
            [*PYTHON, str(BASE / "verify_saved.py"), "--output", str(OUT / "audit-recheck.json")],
        ),
        ("probe-documents", [*PYTHON, str(BASE / "verify_documents.py")]),
        (
            "preserved-diagnosis-documents",
            [*PYTHON, "artifacts/local-answer-first-byte-v1/verify_document.py"],
        ),
        (
            "original-study-saved",
            [
                *PYTHON,
                "artifacts/local-answer-dev-v1/verify_saved.py",
                "--output",
                str(OUT / "original-study-recheck.json"),
            ],
        ),
        ("frozen-sources", [*PYTHON, "scripts/check_frozen_sources.py"]),
        ("ruff-lint", [*PYTHON, "-m", "ruff", "check", "."]),
        ("ruff-format", [*PYTHON, "-m", "ruff", "format", "--check", "src", "tests", "scripts"]),
        ("dependencies", [*PYTHON, "-m", "pip", "check"]),
        ("diff-check", ["git", "diff", "--check"]),
    ]
    receipts = []
    try:
        for name, command in commands:
            began = time.perf_counter()
            with (OUT / f"{name}.log").open("xb") as stream:
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
                raise RuntimeError(f"offline check failed: {name}")
    finally:
        with (OUT / "checks.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(dict(checks=receipts, model_execution=False), stream, indent=2)
            stream.write("\n")


if __name__ == "__main__":
    main()
