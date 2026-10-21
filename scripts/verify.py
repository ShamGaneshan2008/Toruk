"""Local equivalents of the CPU CI job, each with retained evidence."""

import argparse
import subprocess
import sys
from datetime import UTC, datetime

from check import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", default=datetime.now(UTC).strftime("verify-%Y%m%dT%H%M%S"))
    options = parser.parse_args()
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
        "build": ["-m", "build", "--no-isolation"],
        "diff-check": ["git", "diff", "--check"],
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
                f"{options.prefix}-{label}",
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
