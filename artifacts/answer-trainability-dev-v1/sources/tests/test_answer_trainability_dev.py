"""Disposable numerical contracts; never fit or generate study answers."""

import importlib.util
import sys
from pathlib import Path

import pytest
import torch

from toruk_lm.engine import setup
from toruk_lm.owned_lm import OwnedConfig, OwnedSession, build_model

SPEC = importlib.util.spec_from_file_location(
    "answer_trainability_dev",
    Path(__file__).resolve().parents[1] / "scripts/answer_trainability_dev.py",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
assert SPEC and SPEC.loader
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


def test_static_split_validation_local_placement_and_scorer():
    files = study.data_files()
    study.validate_data(files)
    assert study.score([111, 100, 2], "la")
    for wrong in ([111, 100], [35, 111, 100, 2], [111, 100, 35, 2], [2]):
        assert not study.score(wrong, "la")
    assert study.classify([2]) == dict(eos=True, malformed=True, repetitive=False)
    assert study.classify([111, 100, 2]) == dict(eos=True, malformed=False, repetitive=False)
    assert study.classify([119, 124, 64] * 2)["malformed"]
    assert study.classify([119, 124] * 3)["repetitive"]
    files["dev-labels.json"][0]["gold"] = "wrong"
    with pytest.raises(ValueError, match="source"):
        study.validate_data(files)


def test_declared_parameter_counts_without_study_training():
    setup(901231, 1)
    for variant, count in study.PARAMETERS.items():
        assert sum(p.numel() for p in study.make_model(variant).parameters()) == count


@pytest.mark.parametrize("variant", ["ordinary_matched", "memory_on"])
def test_target_offsets_stream_alignment_and_no_future_answer_leak(variant):
    setup(901233, 1)
    model = build_model(OwnedConfig(context=8, width=8, heads=2, layers=1, slots=2), variant)
    prefix = "abcdefg" + "x=b\nx?="
    doc = dict(prefix=prefix, text=prefix + "b")
    x, y, answer = study.make_batch([doc], context=8)
    assert answer.sum() == 2
    assert y[0, len(prefix)] == ord("b") + 3 and y[0, len(prefix) + 1] == 2
    logits = study.forward_batch(model, x)
    session = OwnedSession(model)
    consumed = session.consume([1, *(b + 3 for b in prefix.encode())])
    assert torch.allclose(consumed, logits[0, len(prefix)], atol=1e-6)
    changed = dict(prefix=prefix, text=prefix + "c")
    changed_x, _, _ = study.make_batch([changed], context=8)
    assert torch.equal(
        logits[:, : len(prefix) + 1], study.forward_batch(model, changed_x)[:, : len(prefix) + 1]
    )


@pytest.mark.parametrize("weight", [1, 16])
def test_partition_loss_and_gradients_equal_direct_weighted_ce(weight):
    setup(901237, 1)
    model = torch.nn.Linear(3, 259)
    inputs = torch.randn(2, 5, 3)
    targets = torch.tensor([[3, 4, 5, 6, 2], [8, 9, 10, 2, -100]])
    mask = torch.tensor([[False, False, False, True, True], [False, False, True, True, False]])
    logits = model(inputs)
    h, a, stats = study.loss_parts(logits, targets, mask, weight)
    direct = torch.autograd.grad(h + a, list(model.parameters()), retain_graph=True)
    logits_gradient = torch.autograd.grad(h + a, logits, retain_graph=True)[0]
    assert torch.allclose(logits_gradient.norm(dim=-1), stats["token_logit_gradient_l2"], atol=1e-7)
    study.gradient_parts(model, h, a)
    for parameter, expected in zip(model.parameters(), direct, strict=True):
        assert torch.allclose(parameter.grad, expected, atol=1e-6)
    assert stats["denominator"] == 5 + 4 * weight
    assert float(stats["token_weighted_loss"].sum()) == pytest.approx(float((h + a).detach()))
    if weight == 1:
        ce = torch.nn.functional.cross_entropy(logits.transpose(1, 2), targets)
        assert float((h + a).detach()) == pytest.approx(float(ce.detach()))
