"""Schedule, gate, padding and registration contracts; no study fitting or generation."""

import copy
import random
import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import paired_batch_dev as study  # noqa: E402

from toruk_lm.engine import setup  # noqa: E402


def test_exact_frozen_data_and_complete_exposure_schedules():
    files = study.original.datasets()
    study.original.validate(files)
    for name in files:
        assert files[name] == study.read(study.OLD / name)
    documents, labels = files["train-documents.json"], files["train-labels.json"]
    schedules = {
        f"{s}-{a}": study.schedule(documents, labels, s, a) for s in study.SEEDS for a in study.ARMS
    }
    study.validate_schedules(documents, labels, schedules)
    for seed in study.SEEDS:
        ids = [d["id"] for d in documents]
        for epoch in (0, 1, 127):
            expected = list(ids)
            random.Random(seed + epoch).shuffle(expected)
            actual = [
                i
                for b in schedules[f"{seed}-original"][epoch * 12 : (epoch + 1) * 12]
                for i in b["ids"]
            ]
            assert actual == expected
    broken = copy.deepcopy(schedules)
    broken["947-city-paired"][0]["ids"][0] = "train-095"
    with pytest.raises(ValueError):
        study.validate_schedules(documents, labels, broken)


@pytest.mark.parametrize("variant", ["ordinary", "recurrent"])
def test_padding_preserves_valid_loss_gradients_and_fixed_work_on_disposable_cases(variant):
    setup(900399, 1)
    model = study.make_model(variant)
    other = copy.deepcopy(model)
    documents = [
        dict(prefix="X" * 31 + "a=b\na?=", text="X" * 31 + "a=b\na?=b"),
        dict(prefix="Y" * 31 + "c=dd\nc?=", text="Y" * 31 + "c=dd\nc?=dd"),
    ]
    fixed, stats = study.batch_objective(model, documents)
    dynamic, original_stats = study.original.batch_objective(other, documents)
    torch.testing.assert_close(fixed, dynamic, atol=1e-6, rtol=1e-6)
    assert stats["forward_positions"] == 128
    assert stats["history_targets"] == original_stats["history_targets"]
    assert stats["answer_targets"] == original_stats["answer_targets"]
    fixed.backward()
    dynamic.backward()
    for a, b in zip(model.parameters(), other.parameters(), strict=True):
        torch.testing.assert_close(a.grad, b.grad, atol=2e-6, rtol=2e-5)


def test_mastery_is_strict_and_eos_is_separate():
    m = dict(exact=96, eos=96, malformed=0, repetitive=0, city_first_errors=0, city_near_ties=0)
    assert study.training_mastery(m)
    for key, value in dict(
        exact=95, eos=95, malformed=1, repetitive=1, city_first_errors=1, city_near_ties=1
    ).items():
        assert not study.training_mastery(dict(m, **{key: value}))


def test_fixed_models_initialize_to_original_hashes_without_updates():
    for seed in study.SEEDS:
        for variant in study.PARAMETERS:
            setup(seed, 1)
            model = study.make_model(variant)
            expected = study.read(
                study.OLD / "stages" / f"train-{seed}-{variant}" / "training-summary.json"
            )["initial_sha256"]
            assert study.initial_hash(model) == expected
            assert sum(p.numel() for p in model.parameters()) == study.PARAMETERS[variant]


def test_unregistered_loading_stops_before_model_loading(monkeypatch, tmp_path):
    monkeypatch.setattr(study, "RUN", tmp_path / "absent")
    with pytest.raises(FileNotFoundError):
        study.load(947, "ordinary", "city-paired")


def test_primary_rejects_target_failure_and_does_not_credit_matched_control():
    good = dict(exact=96, eos=96, malformed=0, repetitive=0, city_first_errors=0, city_near_ties=0)
    results = {
        study.cell(s, v, a): dict(good)
        for s in study.SEEDS
        for v in study.PARAMETERS
        for a in study.ARMS
    }
    assert study.primary_verdict(results) == "NO_PAIRING_SPECIFIC_SUPPORT_COMPARATOR_MATCHES"
    results[study.cell(947, "ordinary", "city-paired")]["exact"] = 80
    assert study.primary_verdict(results) == "REJECT_PAIRED_SUFFICIENCY_AT_ORDINARY947"
