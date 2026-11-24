"""Numerical/data/gate contracts. Disposable gradients only; zero research fitting."""

import ast
import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import value_start_replication_v2 as study  # noqa: E402


def test_first_mask_native_shift_and_fixed_padding():
    docs = [dict(prefix="r" * 31 + "a=b\na?=", text="r" * 31 + "a=b\na?=b")]
    x, y, answer, first = study.batch_tensors(docs)
    assert x.shape == (1, 64) and first.sum() == 1
    index = len(docs[0]["prefix"].encode())
    assert first[0, index] and y[0, index] == ord("b") + 3
    assert y[0, index + 1] == 2 and not first[0, index + 1]
    assert first[answer].sum() == 1


@pytest.mark.parametrize("extra", [0, 15])
def test_loss_and_gradients_equal_explicit_weighted_ce(extra):
    torch.manual_seed(900731)
    logits = torch.randn(2, 6, 259, requires_grad=True)
    y = torch.tensor([[4, 5, 6, 7, 2, -100], [8, 9, 10, 11, 12, 2]])
    answer = torch.tensor(
        [[False, False, True, True, True, False], [False, False, False, True, True, True]]
    )
    first = torch.zeros_like(answer)
    first[0, 2] = True
    first[1, 3] = True
    loss, stats = study.loss_from_logits(logits, y, answer, first, extra)
    ce = torch.nn.functional.cross_entropy(
        logits.transpose(1, 2), y, ignore_index=-100, reduction="none"
    )
    weights = y.ne(-100).float() + extra * first.float()
    expected = (ce * weights).sum() / weights.sum()
    torch.testing.assert_close(loss, expected)
    actual_grad = torch.autograd.grad(loss, logits, retain_graph=True)[0]
    expected_grad = torch.autograd.grad(expected, logits)[0]
    torch.testing.assert_close(actual_grad, expected_grad)
    assert stats["first_targets"] == 2 and stats["weighted_denominator"] == int(weights.sum())


def test_saved_strong_schedule_exposure_and_split_integrity():
    files = study.data.datasets()
    prior = study.read(study.OLD / "train-labels.json") + study.read(study.OLD / "dev-labels.json")
    result = study.data.validate(files, prior)
    assert result["dev_overlap_v1_and_known"] == 0
    schedules = {
        key: study.data.schedule(files, axes["shuffle"]) for key, axes in study.CROSSED.items()
    }
    assert len(study.ORDER) == 16 and len(study.CROSSED) == 4
    for left, a in study.CROSSED.items():
        for right, b in study.CROSSED.items():
            assert (schedules[left] == schedules[right]) == (a["shuffle"] == b["shuffle"])
            assert all(
                len(row["ids"]) == 8 and row["padded_forward_positions"] == 512
                for row in schedules[left]
            )


def test_separate_outcomes_do_not_repair_eos_or_malformed_values():
    ids = [ord("l") + 3, ord("a") + 3]
    result = study.outcome(ids, "la")
    assert result["value_exact"] and not result["exact"] and not result["eos"]
    assert not result["wrong_first"] and not result["malformed"]
    assert study.outcome([*ids, 2], "la")["exact"]
    assert study.outcome([35, *ids, 2], "la")["malformed"]
    assert study.outcome([ord("x") + 3] * 6, "la")["repetition"]


def test_candidate_mastery_and_control_floor_are_distinct():
    good = dict(exact=96, eos=96, wrong_first=0, malformed=0, repetition=0)
    result = {study.identity(s, v, a): dict(good) for s, v, a in study.ORDER}
    key = next(iter(study.CROSSED)) + "-ordinary"
    result[key + "-uniform"].update(exact=92, wrong_first=4)
    assert study.eligible(result) and not study.mastery(result[key + "-uniform"])
    result[key + "-first16"]["exact"] = 95
    assert not study.eligible(result)
    result[key + "-first16"]["exact"] = 96
    result[key + "-uniform"]["exact"] = 89
    assert not study.eligible(result)


def test_training_loader_rejects_development_before_opening_files():
    with pytest.raises(ValueError, match="non-training"):
        study.checked_data("dev-labels.json", training=True)


def test_runtime_answers_are_custom_and_workers_do_not_seal_monitors():
    source = Path(study.__file__).read_text()
    tree = ast.parse(source)
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert "toruk_lm.owned_lm" in imports
    assert not any(
        m and any(x in m for x in ("transformers", "ollama", "chat_foundation", "requests"))
        for m in imports
    )
    assert "observation-seal.json" not in source
    assert "seal_closed_run" not in source


def test_aggregate_gain_cannot_rescue_pair_regression_or_tie():
    good = dict(
        exact=23,
        eos=24,
        malformed=0,
        repetition=0,
        known_context_gain=10,
        categories=dict(city=7, code=8, unknown=8),
    )
    results = {
        study.identity(s, v, a): dict(good, categories=dict(good["categories"]))
        for s, v, a in study.ORDER
    }
    for key, record in results.items():
        if key.endswith("-uniform"):
            record.update(exact=22, categories=dict(city=7, code=7, unknown=8))
    assert study.compare_development(results)["improved"]
    key = study.identity(next(iter(study.CROSSED)), "ordinary", "uniform")
    results[key]["exact"] = 23
    assert not study.compare_development(results)["improved"]
    results[key]["exact"] = 24
    assert not study.compare_development(results)["improved"]


def test_initialization_lookup_is_independent_of_shuffle():
    source = Path(study.__file__).read_text()
    assert 'setup(CROSSED[seed]["initialization"], 1)' in source
    assert "setup(seed, 1)" not in source
    assert {v["initialization"] for v in study.CROSSED.values()} == {601, 947}
    assert {v["shuffle"] for v in study.CROSSED.values()} == {1301, 1709}
