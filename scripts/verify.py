"""Local equivalents of the Python and web CI jobs, each with retained evidence."""

import argparse
import shutil
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
    # Resolve npm.cmd explicitly on Windows; npm is not a Python module.
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm") or "npm"
    commands = {
        "web-check": [npm, "--prefix", "web/vercel", "run", "check"],
        "web-tests": [npm, "--prefix", "web/vercel", "test"],
        "install-local": ["-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."],
        "package": ["-m", "pip", "check"],
        "import": ["-c", "import toruk_lm; print(toruk_lm.__version__)"],
        "help": ["-m", "toruk_lm", "--help"],
        "diagnose": ["-m", "toruk_lm", "diagnose"],
        "frozen-sources": ["scripts/check_frozen_sources.py"],
        "lint": ["-m", "ruff", "check", "."],
        "format": ["-m", "ruff", "format", "--check", "src", "tests", "scripts"],
        "types": ["-m", "mypy"],
        "types-linux": ["-m", "mypy", "--platform", "linux"],
        "tests": ["-m", "pytest", "-q"],
        "independent-cases": [
            "scripts/independent_replication.py",
            "validate-cases",
            "--run",
            str(options.output_dir.resolve() / "independent-cases"),
        ],
        "owned-lm-smoke": [
            "scripts/study_owned_lm.py",
            "--config",
            "configs/owned-lm-smoke-v1.json",
            "--output",
            str(options.output_dir.resolve() / "owned-lm-smoke"),
        ],
        "owned-lm-validate": [
            "scripts/validate_owned_reproduction.py",
            "--config",
            "configs/owned-lm-smoke-v1.json",
            "--run",
            str(options.output_dir.resolve() / "owned-lm-smoke"),
        ],
        "conversation-data": [
            "scripts/conversation_readiness.py",
            "validate",
            "--output",
            str(options.output_dir.resolve() / "conversation-data"),
        ],
        "owned-lm-generate": [
            "-m",
            "toruk_lm.owned_lm",
            "generate",
            "--checkpoint",
            str(options.output_dir.resolve() / "owned-lm-smoke/models/23-memory_on/checkpoint.pt"),
            "--prompt",
            "Experimental CPU smoke",
            "--max-new-tokens",
            "4",
        ],
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
        "build": [
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(options.output_dir.resolve() / "package"),
        ],
        "diff-check": ["git", "diff", "--check"],
        "staged-diff-check": ["git", "diff", "--cached", "--check"],
    }
    failures = []
    for label, args in commands.items():
        external = label in {"web-check", "web-tests", "diff-check", "staged-diff-check"}
        command = args if external else [sys.executable, *args]
        timeout = 420 if label == "tests" else 300 if label.startswith("types") else 120
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
