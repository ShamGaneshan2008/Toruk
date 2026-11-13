"""Invoke existing verify.py with explicit development-only verification coverage.

The default verifier launches historical held-out studies. Keep its source
unchanged, record skips, and limit pytest to disposable-fixture regression tests.
This is deliberately not a receipt for the unfiltered full repository suite.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import verify

ALLOWED = {
    "web-check",
    "web-tests",
    "install-local",
    "package",
    "import",
    "help",
    "diagnose",
    "frozen-sources",
    "lint",
    "format",
    "types",
    "types-linux",
    "tests",
    "build",
    "diff-check",
    "staged-diff-check",
}
FIXTURE_TESTS = [
    "tests/test_segment_delta.py",
    "tests/test_foundation.py",
    "tests/test_recurrent.py",
    "tests/test_controlled_validation.py",
    "tests/test_chat.py",
    "tests/test_web_integration.py",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    directory = args.output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    original_run = subprocess.run
    coverage = dict(
        invoked="scripts/verify.py:main (unchanged)",
        full_suite=False,
        reason="User forbids held-out access/evaluation and repeat research studies",
        skipped=[],
        selected_tests=FIXTURE_TESTS,
        commands=[],
    )

    def filtered(command, **kwargs):
        if len(command) < 2 or command[1] != "scripts/check.py":
            return original_run(command, **kwargs)
        boundary = command.index("--")
        label = command[boundary - 1]
        if label not in ALLOWED:
            coverage["skipped"].append(label)
            print(f"SKIP {label}: development-only verification boundary", flush=True)
            return subprocess.CompletedProcess(command, 0)
        if label == "tests":
            command = [
                *command[: boundary + 1],
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *FIXTURE_TESTS,
                "-o",
                f"cache_dir={directory / 'pytest-cache'}",
                "--basetemp",
                str(directory / "pytest-tmp"),
            ]
        coverage["commands"].append(dict(label=label, command=command))
        return original_run(command, **kwargs)

    started = time.perf_counter()
    try:
        verify.subprocess.run = filtered
        sys.argv = ["scripts/verify.py", "--output-dir", str(directory)]
        result = verify.main()
    finally:
        verify.subprocess.run = original_run
        coverage["wall_seconds"] = time.perf_counter() - started
        (directory / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    print("Coverage: development-safe subset; historical research and unscoped tests skipped.")
    return result


if __name__ == "__main__":
    sys.exit(main())
