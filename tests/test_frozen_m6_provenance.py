"""Frozen identity is raw bytes, not a name, serialization-equivalent model or new manifest."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_frozen_m6 import (  # noqa: E402
    EXPECTED_SHA256,
    historical_contract,
    inspect_candidate,
    sha256_file,
)


def test_historical_hash_bindings_and_source_archive_agree():
    contract = historical_contract()
    assert set(contract["bindings"].values()) == {EXPECTED_SHA256}
    assert contract["config"]["variant"] == "recurrent"
    assert contract["config"]["slots"] == 4
    assert contract["parameters"] == 57088
    assert contract["steps"] == 12


def test_candidate_hash_is_raw_bytes_and_independent_of_path(tmp_path):
    first = tmp_path / "checkpoint.pt"
    second = tmp_path / "renamed backup with spaces.pt"
    payload = b"PK\x03\x04checkpoint\r\n\x00binary\xff\n"
    first.write_bytes(payload)
    shutil.copyfile(first, second)
    assert sha256_file(first) == sha256_file(second) == hashlib.sha256(payload).hexdigest()
    second.write_bytes(payload.replace(b"\r\n", b"\n"))
    assert sha256_file(first) != sha256_file(second)


def test_missing_and_different_candidates_block_before_loading(tmp_path, monkeypatch):
    import toruk_lm.controlled

    def must_not_load(*args, **kwargs):
        pytest.fail("unverified candidate reached checkpoint deserialization")

    monkeypatch.setattr(toruk_lm.controlled, "load_controlled", must_not_load)
    path = tmp_path / "checkpoint.pt"
    assert inspect_candidate(path)["candidate_status"] == "MISSING"
    path.write_bytes(b"not a checkpoint; not the original")
    result = inspect_candidate(path)
    assert result["candidate_status"] == "IDENTITY_MISMATCH"
    assert result["m6_reproduction"] == "BLOCKED"


def test_rewritten_manifest_cannot_redefine_original_identity(tmp_path):
    for relative in (
        "artifacts/m6-validation-001/recurrent/metrics.json",
        "artifacts/m6-validation-001/manifest.json",
        "artifacts/m6-handoff/manifest.json",
        "artifacts/chat-release-v2/raw.json",
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    path = tmp_path / "artifacts/m6-validation-001/manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["files"]["recurrent/checkpoint.pt"] = "0" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="bindings disagree"):
        historical_contract(tmp_path)
