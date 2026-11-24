"""Disposable process/log tests only. No research checkpoints or model imports."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lifetime_job_v2 as sealing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _hashes(directory: Path) -> dict[str, str]:
    return {
        p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.rglob("*")
        if p.is_file()
    }


def _run(tmp_path: Path, code: str, **kwargs):
    directory = tmp_path / "run"
    return sealing.watch_and_seal(
        [sys.executable, "-B", "-c", code], directory, tmp_path, 5, **kwargs
    )


def test_normal_exit_closes_receipt_streams_and_seals_stable_bytes(tmp_path: Path):
    payload = tmp_path / "run" / "payload.txt"
    code = (
        f"from pathlib import Path; Path({str(payload)!r}).write_text('normal'); "
        "print('done',flush=True)"
    )
    result = _run(tmp_path, code)
    assert result.cost["status"] == "PASS"
    assert result.cost["complete_process_lifetimes"] and result.cost["active_processes"] == 0
    manifest = sealing.verify_seal(result.seal_path.parent, expected_seal_sha256=result.seal_sha256)
    assert set(manifest["files"]) == {"payload.txt", "output.log", "resources.jsonl", "cost.json"}
    assert manifest["files"]["cost.json"]["sha256"] == manifest["final_receipt_sha256"]
    before = _hashes(result.seal_path.parent)
    time.sleep(0.15)
    sealing.verify_seal(result.seal_path.parent, expected_seal_sha256=result.seal_sha256)
    assert _hashes(result.seal_path.parent) == before


@pytest.mark.parametrize("mode", ["timeout", "observer-interruption", "failure", "abrupt"])
def test_stopped_workloads_retain_partial_output_and_complete_receipt(tmp_path: Path, mode: str):
    directory = tmp_path / "run"
    payload = directory / "partial.txt"
    code = (
        f"from pathlib import Path; Path({str(payload)!r}).write_text('partial'); "
        "import subprocess,sys,time,os; print('before stop',flush=True); "
    )
    if mode in ("timeout", "observer-interruption"):
        code += (
            "subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(5)']); "
            "time.sleep(5)"
        )
        result = sealing.watch_and_seal(
            [sys.executable, "-B", "-c", code],
            directory,
            tmp_path,
            0.6 if mode == "timeout" else 5,
            interrupt_after=0.5 if mode == "observer-interruption" else None,
        )
        assert result.cost["failure"] == (
            "CPU/wall cap" if mode == "timeout" else "observer interrupted"
        )
        assert result.cost["total_processes"] >= 2
    else:
        code += "sys.exit(7)" if mode == "failure" else "os._exit(9)"
        result = _run(tmp_path, code)
        assert result.cost["returncode"] == (7 if mode == "failure" else 9)
    assert payload.read_text() == "partial"
    assert result.cost["status"] == "STOP" and result.cost["active_processes"] == 0
    assert result.cost["complete_process_lifetimes"]
    manifest = sealing.verify_seal(directory, expected_seal_sha256=result.seal_sha256)
    assert manifest["workload_status"] == "STOP"
    assert "partial.txt" in manifest["files"]
    before = _hashes(directory)
    time.sleep(0.1)
    sealing.verify_seal(directory, expected_seal_sha256=result.seal_sha256)
    assert _hashes(directory) == before


def test_late_descendant_log_and_payload_write_precede_final_cost_and_seal(tmp_path: Path):
    directory = tmp_path / "run"
    payload = directory / "late.txt"
    leaf = (
        f"import time; from pathlib import Path; time.sleep(.25); "
        f"Path({str(payload)!r}).write_text('late payload'); print('late stdout',flush=True)"
    )
    code = (
        f"import subprocess,sys,os; subprocess.Popen([sys.executable,'-B','-c',{leaf!r}]); "
        "print('parent exits first',flush=True); os._exit(0)"
    )
    result = _run(tmp_path, code)
    assert result.cost["status"] == "PASS" and result.cost["total_processes"] >= 2
    assert result.cost["active_processes"] == 0 and result.cost["wall"] >= 0.25
    assert payload.read_text() == "late payload"
    assert "late stdout" in (directory / "output.log").read_text()
    samples = [json.loads(s) for s in (directory / "resources.jsonl").read_text().splitlines()]
    assert samples[-1]["active"] == 0
    manifest = sealing.verify_seal(directory, expected_seal_sha256=result.seal_sha256)
    assert "late.txt" in manifest["files"]
    before = _hashes(directory)
    time.sleep(0.2)
    assert _hashes(directory) == before


@pytest.mark.parametrize(
    "mutation", ["payload", "monitor", "receipt", "added-file", "removed-file"]
)
def test_post_seal_mutations_are_detected(tmp_path: Path, mutation: str):
    directory = tmp_path / "run"
    payload = directory / "payload.txt"
    code = f"from pathlib import Path; Path({str(payload)!r}).write_text('original'); print('done')"
    result = _run(tmp_path, code)
    if mutation == "added-file":
        (directory / "unexpected.txt").write_text("unexpected")
    elif mutation == "removed-file":
        # Remove only a disposable file created in this test, never existing research evidence.
        payload.unlink()
    else:
        path = (
            payload
            if mutation == "payload"
            else directory / ("resources.jsonl" if mutation == "monitor" else "cost.json")
        )
        if mutation == "payload":
            path.write_text("tampered")  # Same byte count as "original".
        else:
            with path.open("a", encoding="utf-8") as stream:
                stream.write("\n")
    with pytest.raises(sealing.SealError, match="sealed output|receipt changed"):
        sealing.verify_seal(directory, expected_seal_sha256=result.seal_sha256)


def test_overwrite_and_reseal_refusal_preserve_existing_valid_run(tmp_path: Path):
    result = _run(tmp_path, "print('completed')")
    directory = result.seal_path.parent
    before = _hashes(directory)
    with pytest.raises(sealing.SealError, match="existing output"):
        _run(tmp_path, "raise RuntimeError('must never execute')")
    with pytest.raises(sealing.SealError, match="seal already exists"):
        sealing.seal_closed_run(directory)
    assert before == _hashes(directory)


def test_missing_final_receipt_retains_failure_marker_and_partial_output(tmp_path: Path):
    directory = tmp_path / "partial"
    directory.mkdir()
    payload = directory / "partial.txt"
    payload.write_text("retained")
    with pytest.raises(sealing.SealError, match="final cost receipt missing"):
        sealing.seal_closed_run(directory)
    assert payload.read_text() == "retained"
    assert (directory / sealing.FAILURE_NAME).is_file()
    assert not (directory / sealing.SEAL_NAME).exists()
    with pytest.raises(sealing.SealError, match="failure marker"):
        sealing.verify_seal(directory)


def test_interrupted_seal_publication_retains_incomplete_seal_and_failure(
    tmp_path: Path, monkeypatch
):
    directory = tmp_path / "run"
    cost = sealing.watch([sys.executable, "-B", "-c", "print('done')"], directory, tmp_path, 5)
    assert cost["status"] == "PASS"
    original_write = sealing._write_new

    def interrupted_write(path, value):
        if path.name == sealing.SEAL_NAME:
            with path.open("x", encoding="utf-8") as stream:
                stream.write('{"incomplete":')
            raise KeyboardInterrupt("disposable seal-publication interruption")
        original_write(path, value)

    monkeypatch.setattr(sealing, "_write_new", interrupted_write)
    with pytest.raises(KeyboardInterrupt):
        sealing.seal_closed_run(directory)
    assert (directory / sealing.SEAL_NAME).read_text() == '{"incomplete":'
    assert (directory / sealing.FAILURE_NAME).is_file()
    assert (directory / "cost.json").is_file()
    with pytest.raises(sealing.SealError, match="failure marker"):
        sealing.verify_seal(directory)


def test_cli_verification_and_trusted_seal_digest(tmp_path: Path):
    result = _run(tmp_path, "print('CLI fixture')")
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts/lifetime_job_v2.py"),
        "verify",
        "--directory",
        str(result.seal_path.parent),
        "--expected-seal-sha256",
        result.seal_sha256,
    ]
    output = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    assert json.loads(output.stdout)["integrity"] == "PASS"
    with result.seal_path.open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(sealing.SealError, match="seal digest changed"):
        sealing.verify_seal(result.seal_path.parent, expected_seal_sha256=result.seal_sha256)


def test_unclosed_final_receipt_cannot_be_sealed(tmp_path: Path):
    directory = tmp_path / "partial"
    directory.mkdir()
    (directory / "cost.json").write_text(
        json.dumps(
            dict(
                complete_process_lifetimes=False, active_processes=1, returncode=259, status="STOP"
            )
        )
    )
    with pytest.raises(sealing.SealError, match="not closed"):
        sealing.seal_closed_run(directory)
    assert (directory / sealing.FAILURE_NAME).is_file()
    assert not (directory / sealing.SEAL_NAME).exists()


def test_cli_run_uses_observer_owned_sealing(tmp_path: Path):
    directory = tmp_path / "cli"
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts/lifetime_job_v2.py"),
        "run",
        "--directory",
        str(directory),
        "--root",
        str(tmp_path),
        "--seconds",
        "5",
        "--",
        sys.executable,
        "-B",
        "-c",
        "print('CLI run fixture',flush=True)",
    ]
    output = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    result = json.loads(output.stdout)
    assert result["workload_status"] == "PASS"
    sealing.verify_seal(directory, expected_seal_sha256=result["seal_sha256"])
