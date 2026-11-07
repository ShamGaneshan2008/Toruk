import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_unicode_output_does_not_fail_a_check_on_a_legacy_console(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/check.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--output-dir",
            str(tmp_path),
            "unicode",
            "--",
            sys.executable,
            "-c",
            "import sys; sys.stdout.buffer.write(chr(0x2714).encode('utf-8'))",
        ],
        env={**os.environ, "PYTHONIOENCODING": "ascii"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "\\u2714" in completed.stdout
    assert (tmp_path / "unicode.log").read_text(encoding="utf-8") == "\u2714"
    assert json.loads((tmp_path / "unicode.json").read_text())["status"] == "PASS"


def test_check_fingerprint_covers_web_sources_and_ignores_generated_trees(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import check

    monkeypatch.setattr(check, "ROOT", tmp_path)
    for name in ("pyproject.toml", "MANIFEST.in", "main.py", ".gitignore"):
        (tmp_path / name).write_text("", encoding="utf-8")
    for name in (
        "web/vercel/public/index.html",
        "web/vercel/public/chat_state.js",
        "web/vercel/scripts/dev.mjs",
        "web/vercel/package.json",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("initial", encoding="utf-8")
    original = check.source_identity()
    changed = tmp_path / "web/vercel/public/chat_state.js"
    assert changed.relative_to(tmp_path).as_posix() in original["source_files"]
    changed.write_text("changed", encoding="utf-8")
    updated = check.source_identity()
    assert updated["source_sha256"] != original["source_sha256"]
    for directory in ("web/vercel/node_modules", "web/vercel/.vercel", "web/vercel/dist"):
        path = tmp_path / directory / "generated.js"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not repository source", encoding="utf-8")
    assert check.source_identity() == updated


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


@pytest.mark.parametrize("failed_check", [None, "web-check", "web-tests"])
def test_verify_runs_web_checks_and_propagates_failures(tmp_path, monkeypatch, failed_check):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import verify

    commands = {}

    def run_check(command, **kwargs):
        separator = command.index("--")
        label = command[separator - 1]
        commands[label] = command[separator + 1 :]
        return subprocess.CompletedProcess(command, int(label == failed_check))

    npm = str(tmp_path / "npm.cmd")
    monkeypatch.setattr(verify.shutil, "which", lambda name: npm)
    monkeypatch.setattr(verify.subprocess, "run", run_check)
    monkeypatch.setattr(sys, "argv", ["verify.py", "--output-dir", str(tmp_path / "checks")])
    assert verify.main() == int(failed_check is not None)
    assert commands["web-check"] == [npm, "--prefix", "web/vercel", "run", "check"]
    assert commands["web-tests"] == [npm, "--prefix", "web/vercel", "test"]
    assert "tests" in commands, "A web failure must still retain Python verification evidence"
