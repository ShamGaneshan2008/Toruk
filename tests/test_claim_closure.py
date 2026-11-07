"""Closure statistics preserve pairing and reject leakage or changed frozen inputs."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def closure(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import research_claim_closure

    return research_claim_closure


def test_bootstrap_keeps_both_fitted_seeds_in_each_question_block(closure):
    left = {"a": {31: 1, 47: 0}, "b": {31: 0, 47: 1}}
    right = {"a": {31: 0, 47: 1}, "b": {31: 1, 47: 0}}
    result = closure.paired_interval(left, right, resamples=100, seed=741)
    assert result["delta"] == result["low"] == result["high"] == 0
    assert result["questions"] == 2
    with pytest.raises(ValueError, match="question identity"):
        closure.paired_interval(left, {"a": right["a"]}, resamples=100, seed=741)
    with pytest.raises(ValueError, match="training seed"):
        closure.paired_interval(left, right | {"a": {31: 0}}, resamples=100, seed=741)


def test_leakage_audit_distinguishes_shared_answer_inventory_from_duplicate_documents(closure):
    datasets = {
        split: [{"text": split + " document", "answer": "red"}]
        for split in ("train", "dev", "heldout")
    }
    result = closure.leakage(datasets)
    assert result["heldout_answers_in_train_inventory"] == 1
    assert not any(result["exact_document_overlaps"].values())
    datasets["heldout"][0]["text"] = "train document"
    with pytest.raises(ValueError, match="exact document leakage"):
        closure.leakage(datasets)


def test_modified_frozen_input_is_rejected_before_model_loading(closure, tmp_path, monkeypatch):
    source = tmp_path / "source.py"
    source.write_text("original", encoding="utf-8")
    package = tmp_path / "package"
    package.mkdir()
    (package / "registration.json").write_text(
        json.dumps({"inputs": {"source.py": closure.sha(source)}}), encoding="utf-8"
    )
    monkeypatch.setattr(closure, "ROOT", tmp_path)
    source.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen closure input changed"):
        closure.analyze(package, tmp_path / "nonexistent run")
