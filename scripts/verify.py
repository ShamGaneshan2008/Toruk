"""Local equivalents of the CPU CI job, each with retained evidence."""

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from check import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts/checks" / datetime.now(UTC).strftime("run-%Y%m%dT%H%M%S%fZ"),
    )
    options = parser.parse_args()
    pipeline = options.output_dir.resolve() / "pipeline"
    commands = {
        "install-local": ["-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."],
        "package": ["-m", "pip", "check"],
        "import": ["-c", "import toruk_lm; print(toruk_lm.__version__)"],
        "help": ["-m", "toruk_lm", "--help"],
        "diagnose": ["-m", "toruk_lm", "diagnose"],
        "lint": ["-m", "ruff", "check", "."],
        "format": ["-m", "ruff", "format", "--check", "src", "tests", "scripts"],
        "types": ["-m", "mypy"],
        "types-linux": ["-m", "mypy", "--platform", "linux"],
        "tests": ["-m", "pytest", "-q"],
        "reproduce": [
            "-m",
            "toruk_lm",
            "reproduce",
            "--config",
            "configs/foundation.json",
            "--output",
            str(pipeline),
        ],
        "validate": [
            "-m",
            "toruk_lm",
            "validate",
            "--manifest",
            str(pipeline / "data/manifest.json"),
            "--config",
            "configs/foundation.json",
            "--checkpoint",
            str(pipeline / "train/checkpoint.pt"),
        ],
        "summarize": [
            "-m",
            "toruk_lm",
            "summarize",
            "--run",
            str(pipeline),
            "--output",
            str(options.output_dir.resolve() / "tables"),
        ],
        "research-config": [
            "-m",
            "toruk_lm",
            "validate-config",
            "--config",
            "configs/reproduce-smoke-v1.json",
        ],
        "research-smoke": [
            "-m",
            "toruk_lm",
            "reproduce",
            "--config",
            "configs/reproduce-smoke-v1.json",
            "--output",
            str(options.output_dir.resolve() / "research-smoke"),
        ],
        "build": ["-m", "build", "--no-isolation"],
        "diff-check": ["git", "diff", "--check"],
        "staged-diff-check": ["git", "diff", "--cached", "--check"],
    }
    failures = []
    for label, args in commands.items():
        command = args if args[0] == "git" else [sys.executable, *args]
        timeout = 300 if label.startswith("types") or label == "tests" else 120
        if args[0] == "git":
            command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args[1:]]
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/check.py",
                "--timeout",
                str(timeout),
                "--output-dir",
                str(options.output_dir),
                f"{options.prefix}-{label}" if options.prefix else label,
                "--",
                *command,
            ],
            cwd=ROOT,
            timeout=timeout + 15,
        )
        if completed.returncode:
            failures.append(label)
    print("Failed checks:", failures)
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
