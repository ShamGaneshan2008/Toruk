"""Local equivalents of the CPU CI job, each with retained evidence."""

import subprocess
import sys

from check import ROOT


def main():
    commands = {
        "install-local": ["-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."],
        "package": ["-m", "pip", "check"],
        "import": ["-c", "import toruk_lm; print(toruk_lm.__version__)"],
        "help": ["-m", "toruk_lm", "--help"],
        "diagnose": ["-m", "toruk_lm", "diagnose"],
        "lint": ["-m", "ruff", "check", "."],
        "format": ["-m", "ruff", "format", "--check", "src", "tests", "scripts"],
        "types": ["-m", "mypy"],
        "tests": ["-m", "pytest", "-q"],
        "build": ["-m", "build", "--no-isolation"],
        "diff-check": ["git", "diff", "--check"],
    }
    failures = []
    for label, args in commands.items():
        command = args if args[0] == "git" else [sys.executable, *args]
        completed = subprocess.run(
            [sys.executable, "scripts/check.py", label, "--", *command],
            cwd=ROOT,
            timeout=135,
        )
        if completed.returncode:
            failures.append(label)
    print("Failed checks:", failures)
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
