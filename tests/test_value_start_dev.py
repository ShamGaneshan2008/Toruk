"""Numerical/data/gate contracts. Disposable gradients only; zero research fitting."""

import ast
import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import value_start_dev as study  # noqa: E402


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
    data = study.local.datasets()
    study.local.validate(data)
    old = study.read(study.PAIRED / "batch-schedules.json")
    for seed in (601, 947):
        batches = old[f"{seed}-city-shuffled"]
        assert len(batches) == 1536
        assert all(len(b["ids"]) == 8 and b["padded_forward_positions"] == 512 for b in batches)
    for name, value in data.items():
        assert value == study.read(study.OLD / name)


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
    results = {study.identity(s, v, a): dict(good) for s, v, a in study.ORDER}
    results["947-ordinary-uniform"].update(exact=92, wrong_first=4)
    assert study.eligible(results)
    assert not study.mastery(results["947-ordinary-uniform"])
    results["947-ordinary-first16"]["exact"] = 95
    assert not study.eligible(results)
    results["947-ordinary-first16"]["exact"] = 96
    results["947-ordinary-uniform"]["exact"] = 89
    assert not study.eligible(results)


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
