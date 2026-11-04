"""Training-only rendering, semantic preservation, role and gate checks."""

import importlib
import json
import random

import pytest

from toruk_lm.integrated_study import make_case


@pytest.fixture
def experiment(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("value_fidelity_dev")


def test_augmentation_preserves_semantics_and_input_row(experiment):
    row = make_case("train", "preservation", 0, random.Random(31))
    before = repr(row)
    changed = experiment.augment(row, random.Random(5))
    assert repr(row) == before
    assert changed["answer"] == row["answer"] and changed["query_key"] == row["query_key"]
    assert sorted(changed["query"]) == sorted(row["query"])
    for a, b in zip(changed["events"], row["events"], strict=True):
        assert sorted(a["text"]) == sorted(b["text"])
        assert {k: v for k, v in a.items() if k != "text"} == {
            k: v for k, v in b.items() if k != "text"
        }


def test_development_orders_are_disjoint_from_train_and_prior_final(experiment):
    assert not set(experiment.TRAIN_ORDERS) & set(experiment.DEV_ORDERS)
    assert not set(experiment.TRAIN_QUERIES) & set(experiment.DEV_QUERIES)
    assert ("n", "v", "f", "o") not in experiment.TRAIN_ORDERS + experiment.DEV_ORDERS
    assert ("f", "n", "i", "w") not in experiment.TRAIN_QUERIES + experiment.DEV_QUERIES


def test_development_oracle_and_evidence_ids(experiment):
    worlds = experiment.make_development()
    assert len(worlds) == 168 and {w["role"] for w in worlds} == {"development-only"}
    assert {w["eval_seed"] for w in worlds} == {9101, 9102, 9103}
    assert worlds == experiment.make_development()
    for world in worlds:
        truth, evidence = {}, {}
        for i, event in enumerate(world["events"]):
            if event["operation"] != "claim":
                truth[event["key"]], evidence[event["key"]] = event["value"], i
        assert len(world["questions"]) == (2 if world["category"] == "multi" else 1)
        for query in world["questions"]:
            assert query["expected"] == truth.get(query["key"], "?")
            assert query["evidence"] == (
                [evidence[query["key"]]] if query["key"] in evidence else []
            )


def test_world_sampling_is_independent_from_render_rng(experiment):
    worlds = [make_case("train", "correction", i, random.Random(i)) for i in range(20)]
    first, second = random.Random(31), random.Random(31)
    render = random.Random(200031)
    for _ in range(3):
        original = first.sample(worlds, 16)
        altered = [experiment.augment(row, render) for row in second.sample(worlds, 16)]
        assert [r["id"] for r in original] == [r["id"] for r in altered]


def test_gate_refuses_abstention_ties_and_requires_memory_reliance(experiment):
    good = {
        "accuracy": 0.9,
        "known_correct": 108,
        "known_worlds": 120,
        "unsupported": 0,
        "unknown_queries": 48,
        "categories": {c: {"correct": 22, "worlds": 24} for c in ("correction", "preservation")},
    }
    zero = {"known_correct": 0, "known_worlds": 120}
    assert experiment.gate(good, zero)["status"] == "PASS"
    assert experiment.gate(good, good)["status"] == "FAIL"
    abstain = good | {"known_correct": 0, "accuracy": 48 / 168}
    assert experiment.gate(abstain, zero)["status"] == "FAIL"
    hallucinate = good | {"unsupported": 3}
    assert experiment.gate(hallucinate, zero)["status"] == "FAIL"


def test_registration_binds_consumed_development_copy(experiment, tmp_path):
    original = tmp_path / "original-development.json"
    original.write_text("registered worlds")
    # Declaration uses development.json in the original directory, not the copy.
    reference = tmp_path / "reference"
    reference.mkdir()
    source = reference / "development.json"
    source.write_bytes(original.read_bytes())
    copied = tmp_path / "copied"
    copied.mkdir()
    registration = {
        "recipe": experiment.RECIPE,
        "files": {str(source): experiment.file_identity(source)},
    }
    (copied / "registration.json").write_text(json.dumps(registration))
    (copied / "development.json").write_bytes(source.read_bytes())
    experiment.verify(copied)
    (copied / "development.json").write_text("different consumed worlds")
    with pytest.raises(ValueError, match="consumed development"):
        experiment.verify(copied)
