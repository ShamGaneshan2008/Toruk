"""Training-only view, parity and prospective gate contracts; no research fits."""

import copy

import local_answer_entity_dropout as study
import pytest
import value_start_replication_data as data


def test_anonymous_views_preserve_native_answer_and_target_positions():
    import torch

    files = data.datasets()
    for doc, label in zip(files["train-documents.json"], files["train-labels.json"], strict=True):
        before = copy.deepcopy(doc)
        new = study.anonymize(doc, label["canonical"][0])
        assert doc == before and new["gold"] == doc["gold"]
        assert new["prefix"].count("ref") == 2 and new["prefix"].endswith("?=")
        x, y, a, first = study.v2.batch_tensors([doc, new])
        assert torch.equal(a[0], a[1]) and torch.equal(first[0], first[1])
        assert torch.equal(y[0][a[0]], y[1][a[1]])
        assert x.shape == (2, 64)


def test_exact_half_exposures_without_rng_or_extra_documents():
    for index in range(96):
        assert (
            sum(study.chosen_view("drop50", epoch, index) == "anonymous" for epoch in range(128))
            == 64
        )
        assert all(study.chosen_view("uniform", epoch, index) == "original" for epoch in range(128))


def test_anonymization_rejects_missing_or_inconsistent_mentions():
    with pytest.raises(ValueError):
        study.anonymize(dict(prefix="bek city?=", text="bek city?=la", gold="la"), "bek")


def test_anonymous_training_has_no_development_canonical_overlap():
    files = data.datasets()
    anonymous = {("ref", *r["canonical"][1:]) for r in files["train-labels.json"]}
    dev = {tuple(r["canonical"]) for r in files["dev-labels.json"]}
    assert not anonymous & dev


def test_training_gate_requires_original_input_exact_eos_and_format():
    m = dict(exact=96, eos=96, wrong_first=0, malformed=0, repetition=0)
    assert study.v2.mastery(m)
    for field, value in (
        ("exact", 95),
        ("eos", 95),
        ("malformed", 1),
        ("wrong_first", 1),
        ("repetition", 1),
    ):
        assert not study.v2.mastery(dict(m, **{field: value}))


def test_scorer_does_not_trim_or_insert_eos():
    expected = [ord(c) + 3 for c in "la"]
    assert study.v2.outcome([*expected, 2], "la")["exact"]
    assert not study.v2.outcome(expected, "la")["exact"]
    assert not study.v2.outcome([*expected, 35, 2], "la")["exact"]


def test_order_and_caps_are_fixed_independent_axes():
    assert len(set(study.ORDER)) == len(study.ORDER) == 16
    assert study.CAPS["fit"] == 90 and study.CAPS["overall"] == 1800
    assert {study.v2.CROSSED[s]["initialization"] for s, _, _ in study.ORDER} == {601, 947}
    assert {study.v2.CROSSED[s]["shuffle"] for s, _, _ in study.ORDER} == {1301, 1709}


def test_ceiling_tie_is_allowed_but_nonceiling_tie_and_regressions_fail():
    perfect = dict(exact=24, eos=24, categories=dict(city=8, code=8, unknown=8))
    imperfect = dict(exact=23, eos=24, categories=dict(city=7, code=8, unknown=8))
    assert study.pair_gate(perfect, perfect)
    assert study.pair_gate(imperfect, perfect)
    assert not study.pair_gate(imperfect, imperfect)
    assert not study.pair_gate(perfect, imperfect)
    assert not study.pair_gate(perfect, dict(perfect, eos=23))
