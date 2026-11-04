import json
import subprocess
import sys
from pathlib import Path

import pytest


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


def test_missing_executable_retains_failure_evidence(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/check.py"
    executable = str(tmp_path / "does-not-exist.exe")
    completed = subprocess.run(
        [sys.executable, str(script), "--output-dir", str(tmp_path), "missing", "--", executable],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 1
    record = json.loads((tmp_path / "missing.json").read_text())
    assert record["status"] == "FAIL"
    assert record["returncode"] is None
    assert record["command"] == [executable]
    assert "FileNotFoundError" in (tmp_path / "missing.log").read_text()
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("trailing_whitespace", [False, True])
def test_verify_detects_staged_whitespace(tmp_path, monkeypatch, trailing_whitespace):
    # Exercise Git's real staged diff while leaving expensive unrelated checks
    # to the full verification suite.
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    content = b"staged change \n" if trailing_whitespace else b"staged change\n"
    (tmp_path / "example.txt").write_bytes(content)
    subprocess.run(
        ["git", "add", "--", "example.txt"], cwd=tmp_path, check=True, capture_output=True
    )
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import verify

    original_run = subprocess.run

    def run_check(command, **kwargs):
        child = command[command.index("--") + 1 :]
        if child[0] == "git":
            return original_run(child, cwd=tmp_path, capture_output=True, text=True)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(verify, "ROOT", tmp_path)
    monkeypatch.setattr(verify.subprocess, "run", run_check)
    monkeypatch.setattr(sys, "argv", ["verify.py", "--output-dir", str(tmp_path / "checks")])
    assert verify.main() == int(trailing_whitespace)
