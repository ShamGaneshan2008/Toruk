"""Repository checks in a separate measured scope; no scientific fitting or inference."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
DIRECTORY = Path(sys.argv[1]).resolve()
assert DIRECTORY.is_relative_to(RUN / "verification") and DIRECTORY.is_dir()
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job import controller_record  # noqa: E402

environment = dict(os.environ, MYPYPATH=str(ROOT / "src"))
commands = {
    "focused": ["-m", "pytest", "-q", "-p", "no:cacheprovider",
                "tests/test_city_contrastive_dev.py", "tests/test_value_start_replication_v2.py",
                "tests/test_lifetime_job.py", "tests/test_lifetime_job_v2.py",
                "--basetemp", str(RUN / "verification/postrun-temp")],
    "lint": ["-m", "ruff", "check", "."],
    "format": ["-m", "ruff", "format", "--check", "src", "tests", "scripts"],
    "types": ["-m", "mypy"],
    "types-linux": ["-m", "mypy", "--platform", "linux"],
    "study-types": ["-m", "mypy", "--follow-imports=silent",
                    "scripts/city_contrastive_dev.py", "scripts/audit_city_contrastive_dev.py"],
    "frozen-sources": ["scripts/check_frozen_sources.py"],
    "dependencies": ["-m", "pip", "check"],
    "cli-help": ["-m", "toruk_lm", "--help"],
    "diagnose": ["-m", "toruk_lm", "diagnose"],
}

with controller_record(DIRECTORY):
    records = []
    for name, args in commands.items():
        cmd = [sys.executable, "-B", *args]
        start, cpu = time.perf_counter(), time.process_time()
        try:
            result = subprocess.run(cmd, cwd=ROOT, env=environment, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=180)
            status = "PASS" if result.returncode == 0 else "FAIL"
            output = result.stdout + result.stderr
            code = result.returncode
        except subprocess.TimeoutExpired as error:
            status, output, code = "FAIL", repr(error), None
        with (DIRECTORY / f"{name}.log").open("x", encoding="utf-8") as stream:
            stream.write(output)
        records.append(dict(name=name, command=cmd, status=status, returncode=code,
                            wall_seconds=time.perf_counter()-start))
        print(json.dumps(records[-1]), flush=True)
    receipt = dict(status="PASS" if all(r["status"] == "PASS" for r in records) else "FAIL",
                   checks=records, full_suite="NOT_RUN: contains unrelated scientific fits and held-out work",
                   hosted_ci="NOT_RUN", note="No research-quality result follows from software checks.")
    for path in (DIRECTORY / "checks.json", RUN / "verification/checks.json"):
        with path.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2);stream.write("\n")
    if receipt["status"] != "PASS":
        raise SystemExit(1)
