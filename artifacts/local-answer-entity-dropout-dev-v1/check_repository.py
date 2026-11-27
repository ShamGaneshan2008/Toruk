"""Sequential repository verification, enclosed by an external lifetime Job."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
OUT = RUN / "verification/execution"


def main():
    commands = [
        ("focused", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/test_entity_dropout_dev.py", "tests/test_value_start_replication_v2.py",
                     "tests/test_lifetime_job.py", "tests/test_lifetime_job_v2.py",
                     "--basetemp", str(RUN / "pytest-tmp-postrun")]),
        ("ruff", [sys.executable, "-m", "ruff", "check", "."]),
        ("format", [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "scripts"]),
        ("mypy", [sys.executable, "-m", "mypy"]),
        ("mypy-linux", [sys.executable, "-m", "mypy", "--platform", "linux"]),
        ("mypy-study", [sys.executable, "-m", "mypy", "--follow-imports=silent",
                        "scripts/diagnose_value_start_v2.py", "scripts/local_answer_entity_dropout.py",
                        "scripts/audit_entity_dropout_dev.py"]),
        ("frozen-sources", [sys.executable, "scripts/check_frozen_sources.py"]),
        ("dependencies", [sys.executable, "-m", "pip", "check"]),
        ("diff-check", ["git", "diff", "--check"]),
        ("cached-diff-check", ["git", "diff", "--cached", "--check"]),
    ]
    environment = dict(os.environ, MYPYPATH=str(ROOT / "src"))
    results = []
    for name, command in commands:
        began = time.perf_counter()
        with (OUT / (name + ".stdout.log")).open("xb") as stdout, (OUT / (name + ".stderr.log")).open("xb") as stderr:
            result = subprocess.run(command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr)
        results.append(dict(name=name, command=command, returncode=result.returncode,
                            wall=time.perf_counter()-began))
    receipt = dict(status="PASS" if all(r["returncode"] == 0 for r in results) else "FAIL",
                   checks=results, hosted_ci="NOT_RUN", model_research_fits=0)
    for path in (OUT / "checks.json", RUN / "verification-checks.json"):
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
    print(json.dumps(receipt, indent=2))
    if receipt["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
