"""Static repository verification only; no fits, generated answers or model smoke."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
PYTHON = [sys.executable, "-B"]


def main():
    commands = [
        ("ruff", [*PYTHON, "-m", "ruff", "check", "--no-cache", "."]),
        (
            "format",
            [*PYTHON, "-m", "ruff", "format", "--check", "--no-cache", "src", "tests", "scripts"],
        ),
        (
            "type-study",
            [
                *PYTHON,
                "-m",
                "mypy",
                "--follow-imports=silent",
                "scripts/value_start_replication_v2.py",
                "scripts/value_start_replication_data.py",
            ],
        ),
        (
            "type-auditor",
            [
                *PYTHON,
                "-m",
                "mypy",
                "--allow-untyped-defs",
                "--follow-imports=silent",
                "scripts/audit_value_start_replication_v2.py",
            ],
        ),
        ("frozen", [*PYTHON, "scripts/check_frozen_sources.py"]),
        ("dependencies", [*PYTHON, "-m", "pip", "check"]),
        ("diff", ["git", "diff", "--check"]),
        ("cached-diff", ["git", "diff", "--cached", "--check"]),
    ]
    os.environ["MYPYPATH"] = str(ROOT / "src")
    records = []
    try:
        for name, command in commands:
            began = time.perf_counter()
            with (BASE / "verification" / f"{name}.log").open("xb") as stream:
                process = subprocess.run(
                    command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False
                )
            record = dict(
                name=name,
                command=command,
                returncode=process.returncode,
                wall=time.perf_counter() - began,
            )
            records.append(record)
            print(json.dumps(record), flush=True)
            if process.returncode:
                raise RuntimeError(name + " failed; keep logs")
    finally:
        with (BASE / "verification/checks.json").open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            json.dump(
                dict(checks=records, hosted_ci="NOT_RUN", new_model_forwards=0),
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")


if __name__ == "__main__":
    main()
