"""Bind actual replay inputs, including copied runs, before loading or generation."""

import importlib
import json
import shutil

import pytest


@pytest.fixture
def replay_module(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("replay_routing_v2")


@pytest.fixture
def sealed(tmp_path, replay_module):
    reference = tmp_path / "reference"
    inputs = tmp_path / "copied"
    for name in (
        "registration.json",
        "final.json",
        "development/new-31.json",
        "development/new-47.json",
        "train/new-31.pt",
        "train/new-47.pt",
    ):
        target = reference / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((name + "\n").encode())
    frozen = {
        "files": {
            p.as_posix(): replay_module.file_identity(p)
            for p in reference.rglob("*")
            if p.is_file()
        }
    }
    (reference / "freeze.json").write_text(json.dumps(frozen))
    shutil.copytree(reference, inputs)
    return reference, inputs


def test_copied_run_binds_all_consumed_paths(sealed, replay_module):
    reference, inputs = sealed
    paths = replay_module.bind_run_files(reference, inputs)
    assert paths["final.json"] == inputs / "final.json"
    assert paths["train/new-31.pt"] == inputs / "train/new-31.pt"
    assert all(p.is_relative_to(inputs) for p in paths.values())


@pytest.mark.parametrize(
    "name", ["final.json", "train/new-31.pt", "train/new-47.pt", "registration.json"]
)
def test_tampered_alias_rejected_while_original_still_valid(sealed, replay_module, name):
    reference, inputs = sealed
    (inputs / name).write_bytes(b"altered consumed input")
    with pytest.raises(ValueError, match="consumed input differs"):
        replay_module.bind_run_files(reference, inputs)
    replay_module.bind_run_files(reference, reference)


def test_missing_alias_checkpoint_and_modified_seal_rejected(sealed, replay_module):
    reference, inputs = sealed
    (inputs / "train/new-31.pt").unlink()
    with pytest.raises(ValueError, match="consumed input differs"):
        replay_module.bind_run_files(reference, inputs)
    shutil.copyfile(reference / "train/new-31.pt", inputs / "train/new-31.pt")
    (inputs / "freeze.json").write_text("{}")
    with pytest.raises(ValueError, match="consumed input differs"):
        replay_module.bind_run_files(reference, inputs)


def test_undeclared_or_ambiguous_identity_refused(sealed, replay_module):
    reference, _ = sealed
    path = reference / "final.json"
    with pytest.raises(ValueError, match="not uniquely declared"):
        replay_module.declared_digest({}, path)
    files = {str(path): "one", str(reference / "nested" / ".." / "final.json"): "two"}
    with pytest.raises(ValueError, match="not uniquely declared"):
        replay_module.declared_digest(files, path)


def test_reference_answer_tampering_is_not_a_new_baseline(tmp_path, replay_module):
    raw = tmp_path / "raw.json"
    raw.write_text("original answers")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"files": {"raw.json": replay_module.file_identity(raw)}})
    )
    replay_module.verify_reference_file(tmp_path, raw)
    raw.write_text("changed answers")
    with pytest.raises(ValueError, match="consumed input differs"):
        replay_module.verify_reference_file(tmp_path, raw)
