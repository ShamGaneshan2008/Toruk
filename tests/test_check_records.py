import json
import subprocess
import sys
from pathlib import Path


def test_check_preserves_existing_evidence(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/check.py"
    command = [
        sys.executable,
        str(script),
        "--output-dir",
        str(tmp_path),
        "example",
        "--",
        sys.executable,
        "-c",
        "print('original evidence')",
    ]
    first = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert first.returncode == 0, first.stderr
    record = (tmp_path / "example.json").read_bytes()
    log = (tmp_path / "example.log").read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert repeated.returncode == 2
    assert "evidence already exists" in repeated.stderr
    assert (tmp_path / "example.json").read_bytes() == record
    assert (tmp_path / "example.log").read_bytes() == log
    assert json.loads(record)["status"] == "PASS"


def test_timed_out_check_retains_partial_output(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/check.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-dir",
            str(tmp_path),
            "--timeout",
            "1",
            "timeout",
            "--",
            sys.executable,
            "-u",
            "-c",
            "import time; print('partial stdout'); time.sleep(10)",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1
    assert "partial stdout" in (tmp_path / "timeout.log").read_text()
    assert json.loads((tmp_path / "timeout.json").read_text())["status"] == "FAIL"
