"""Portable contracts replacing unsupported archival-environment assumptions."""

import hashlib
import json
from types import SimpleNamespace

import ci_contracts as contract
import pytest


def test_committed_probe_inputs_and_plan_without_research_weights():
    base = contract.ROOT / contract.PROBE
    registration = contract.read(base / "registration.json")
    for name, digest in registration["data"].items():
        assert hashlib.sha256((base / name).read_bytes()).hexdigest() == digest
    prefixes, labels, plan = (
        contract.read(base / name)
        for name in ("prefix-inputs.json", "gold-evaluator.json", "plan.json")
    )
    assert len(prefixes) == len(labels) == 32 and len(plan) == 260
    assert sum(r["phase"] == "prefix" for r in plan) == 132
    assert sum(r["phase"] == "teacher" for r in plan) == 128
    assert sum(r["replay"] for r in plan) == 4
    for case, label in zip(prefixes, labels, strict=True):
        ids = [1, *(b + 3 for b in case["prefix"].encode())]
        assert ids == case["input_ids"] == label["full_document_ids"][:54]
        assert ids[-2:] == [66, 64] and len(case["prefix"].encode()) == 53
        assert label["full_document_ids"][54] == label["expected_first_id"]
        assert label["mask_positions"] == [53, 54, 55]


def test_missing_optional_weights_are_not_a_reproduction_pass(tmp_path):
    directory = tmp_path / contract.PROBE
    directory.mkdir(parents=True)
    (directory / "registration.json").write_bytes(
        (contract.ROOT / contract.PROBE / "registration.json").read_bytes()
    )
    result = contract.check_probe_checkpoints(tmp_path)
    assert result["status"] == "MISSING_INPUTS"
    assert len(contract.missing_probe_checkpoints(tmp_path)) == 4
    assert not list(tmp_path.rglob("*.pt")) and not result["model_loaded"]


def test_changed_checkpoint_catalog_is_rejected(tmp_path):
    path = tmp_path / contract.PROBE / "registration.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"checkpoints": {}}')
    with pytest.raises(ValueError, match="registration changed"):
        contract.check_probe_checkpoints(tmp_path)


def test_current_attributes_are_checked_separately():
    assert contract.current_attributes()["scripts/lifetime_job.py"]["eol"] == "lf"


def test_historical_attributes_match_manifest_publication_blob():
    raw, source = contract.historical_attributes(
        contract.ROOT, contract.ATTRIBUTE_BASE, contract.ATTRIBUTE_SHA
    )
    assert hashlib.sha256(raw).hexdigest() == contract.ATTRIBUTE_SHA
    assert source.startswith(("git:", "artifacts/"))


def test_shallow_checkout_snapshot_is_hash_checked(tmp_path, monkeypatch):
    path = tmp_path / contract.ATTRIBUTE_SNAPSHOT
    path.parent.mkdir(parents=True)
    path.write_bytes((contract.ROOT / contract.ATTRIBUTE_SNAPSHOT).read_bytes())
    monkeypatch.setattr(
        contract.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=128, stdout=b"")
    )
    assert (
        contract.historical_attributes(tmp_path, contract.ATTRIBUTE_BASE, contract.ATTRIBUTE_SHA)[1]
        == contract.ATTRIBUTE_SNAPSHOT
    )
    path.write_bytes(b"tampered test-only snapshot")
    with pytest.raises(ValueError, match="hash mismatch"):
        contract.historical_attributes(tmp_path, contract.ATTRIBUTE_BASE, contract.ATTRIBUTE_SHA)


def test_existing_wrong_git_blob_cannot_fall_back_to_snapshot(monkeypatch):
    monkeypatch.setattr(
        contract.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=b"wrong Git blob"),
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        contract.historical_attributes(
            contract.ROOT, contract.ATTRIBUTE_BASE, contract.ATTRIBUTE_SHA
        )


@pytest.mark.parametrize("status,code", [("PASS", 0), ("MISSING_INPUTS", 2), ("FAIL", 1)])
def test_local_checkpoint_cli_exit_policy(monkeypatch, capsys, status, code):
    import check_local_research_checkpoints as checker

    monkeypatch.setattr(checker, "check_probe_checkpoints", lambda: dict(status=status))
    with pytest.raises(SystemExit) as stopped:
        checker.main()
    assert stopped.value.code == code
    assert json.loads(capsys.readouterr().out)["status"] == status


@pytest.mark.parametrize("seed", [601, 947])
def test_disposable_models_repeat_within_current_runtime(seed):
    from answer_trainability_dev import PARAMETERS, initial_hash, make_model

    from toruk_lm.engine import setup

    for variant in PARAMETERS:
        setup(seed, 1)
        first = make_model(variant)
        setup(seed, 1)
        second = make_model(variant)
        assert initial_hash(first) == initial_hash(second)
        assert sum(p.numel() for p in first.parameters()) == PARAMETERS[variant]
