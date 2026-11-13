"""Numerical contracts on disposable fixtures, separate from registered dev cases."""

import sys
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from toruk_lm.engine import load_checkpoint, setup
from toruk_lm.owned_lm import OwnedMemoryLM
from toruk_lm.owned_training import load as load_owned
from toruk_lm.segment_delta import (
    DeltaConfig,
    ResearchSession,
    SegmentDeltaLM,
    build_model,
    delta_update,
    document_loss,
)
from toruk_lm.segment_delta_training import FitConfig, fit, load

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from segment_delta_data import factual, score, validate  # noqa: E402


@pytest.fixture
def config():
    setup(19, 1)
    return DeltaConfig(context=8, width=8, heads=2, rank=4, ff=24, maximum=96)


def test_shapes_counts_state_and_old_recurrent_algebra():
    setup(19, 1)
    config = DeltaConfig()
    for variant, count in (("ordinary", 13914), ("recurrent", 14288), ("delta", 14277)):
        model = build_model(variant, config)
        assert sum(p.numel() for p in model.parameters()) == count
    delta = SegmentDeltaLM(config)
    state = delta.initial_state(2)
    assert state.shape == (2, 8, 8) and state.dtype == torch.float32
    assert state[0].numel() * state.element_size() == 256
    logits, next_state = delta(torch.ones(2, 24, dtype=torch.long), state)
    assert logits.shape == (2, 24, 259) and torch.isfinite(next_state).all()
    recurrent = build_model("recurrent", config)
    assert isinstance(recurrent, OwnedMemoryLM)
    assert recurrent.initial_state().numel() * 4 == 256


def test_causal_logits_padding_and_entering_state_immutable(config):
    model = SegmentDeltaLM(config)
    tokens = torch.tensor([[1, 33, 34, 35, 36]])
    state = model.initial_state()
    before = state.clone()
    logits, proposed = model(tokens, state)
    changed = tokens.clone()
    changed[0, -1] = 99
    assert torch.equal(logits[:, :-1], model(changed, state)[0][:, :-1])
    assert torch.equal(state, before)
    padded = torch.tensor([[1, 33, 34, 35, 36, 0, 0]])
    padded_logits, padded_state = model(padded, state)
    assert torch.allclose(padded_logits[:, :5], logits, atol=1e-6)
    assert torch.allclose(padded_state, proposed, atol=1e-6)
    assert torch.count_nonzero(padded_logits[:, 5:]) == 0
    for invalid in (torch.tensor([[0, 0]]), torch.tensor([[1, 0, 20]])):
        with pytest.raises(ValueError, match="right-padded"):
            model(invalid, state)
    with pytest.raises(ValueError, match="shape"):
        model(tokens, torch.zeros(1, 3, 3))
    with pytest.raises(ValueError, match="dtype"):
        model(tokens, state.double())
    with pytest.raises(ValueError, match="nonfinite"):
        model(tokens, state + torch.nan)


def test_exact_same_key_correction_and_orthogonal_preservation():
    state = torch.zeros(1, 2, 2)
    key = torch.tensor([[1.0, 0.0]])
    state = delta_update(state, key, torch.tensor([[2.0, 3.0]]), torch.ones(1, 1))
    state = delta_update(
        state, torch.tensor([[0.0, 1.0]]), torch.tensor([[7.0, 8.0]]), torch.ones(1, 1)
    )
    state = delta_update(state, key, torch.tensor([[4.0, 5.0]]), torch.ones(1, 1))
    assert torch.equal(state, torch.tensor([[[4.0, 5.0], [7.0, 8.0]]]))
    # This numerical property does not assert that training learns matching keys.


def test_future_loss_gradients_cross_segment_and_actual_ablations(config):
    model = SegmentDeltaLM(config)
    x = torch.tensor([[1, 14, 15, 16, 17, 18, 19, 20]])
    initial = model.initial_state()
    _, state = model(x, initial)
    later, unchanged = model(x, state, write=False)
    later.square().mean().backward()
    for parameter in (
        model.key.weight,
        model.value.weight,
        model.beta.weight,
        model.queries[0].weight,
    ):
        assert parameter.grad is not None and torch.isfinite(parameter.grad).all()
        assert parameter.grad.abs().sum() > 0
    assert torch.equal(unchanged, state)
    without, _ = model(x, state, read=False, write=False)
    assert not torch.allclose(later, without)
    assert torch.equal(without, model.backbone(x))


def test_one_commit_partial_recompute_reset_clone_and_deterministic_replay(config):
    model = SegmentDeltaLM(config)
    stream = [1, *range(20, 51)]
    full, pieces = ResearchSession(model), ResearchSession(model)
    expected = full.consume(stream)
    for i in range(0, len(stream), 3):
        actual = pieces.consume(stream[i : i + 3])
    assert torch.equal(actual, expected) and torch.equal(pieces.state, full.state)
    assert full.commits == pieces.commits == 4
    prefix = ResearchSession(model)
    prefix.consume(stream[:4])
    assert torch.count_nonzero(prefix.state) == 0
    clone = prefix.clone()
    prefix.consume(stream[4:8])
    assert clone.commits == 0 and torch.count_nonzero(clone.state) == 0
    clone.consume(stream[4:8])
    assert torch.equal(prefix.state, clone.state)
    clone.reset()
    assert clone.tokens_read == 0 and not clone.prefix
    a = clone.generate("disposable fixture")
    b = ResearchSession(model).generate("disposable fixture")
    assert a == b
    with pytest.raises(ValueError, match="reset"):
        clone.generate("second document")
    with pytest.raises(ValueError, match="budget"):
        ResearchSession(model).generate("a" * 193)


def test_loss_document_isolation_target_accounting_and_gold_not_in_generation(config):
    model = SegmentDeltaLM(config)
    text = "disposable local text then a delayed byte."
    first, n, _, _ = document_loss(model, text)
    document_loss(model, "a different document")
    second, count, _, _ = document_loss(model, text)
    assert n == count == len(text.encode()) + 1 and torch.equal(first, second)
    case = dict(prefix="not a registered case", gold="one")
    prediction = ResearchSession(model).generate(case["prefix"])
    case["gold"] = "two"
    assert prediction == ResearchSession(model).generate(case["prefix"])
    assert score([ord("?") + 3, 2], "?")
    assert not score([35, ord("?") + 3, 2], "?")
    assert not score([ord("?") + 3], "?")


@pytest.mark.parametrize("variant", ["ordinary", "recurrent", "delta"])
def test_checkpoint_resume_exact_and_incompatible_rejected(tmp_path, config, variant):
    docs = [
        dict(id="numeric-a", split="train", text="random fixture ABCDE " * 2),
        dict(id="numeric-b", split="train", text="random fixture FGHIJ " * 2),
    ]
    identity = dict(test="disposable-fixture", runtime=str(torch.__version__))
    options = FitConfig(seed=29)
    direct, partial, resumed = [
        tmp_path / f"{variant}-{name}.pt" for name in ("direct", "part", "resume")
    ]
    fit(variant, config, options, docs, direct, identity, steps=2)
    fit(variant, config, options, docs, partial, identity, steps=1)
    fit(variant, config, options, docs, resumed, identity, steps=2, resume=partial)
    model, _, saved = load(direct, identity)
    restored, _, replay = load(resumed, identity)
    for key, value in model.state_dict().items():
        assert torch.equal(value, restored.state_dict()[key])
    assert saved["targets"] == replay["targets"] and replay["next_document_cursor"] == 4
    assert ResearchSession(model).generate("numeric fixture") == ResearchSession(restored).generate(
        "numeric fixture"
    )
    assert saved["config"] == asdict(config)
    with pytest.raises(ValueError, match="identity"):
        load(direct, dict(test="other"))
    with pytest.raises(ValueError, match="unsupported"):
        load_checkpoint(direct)
    with pytest.raises(ValueError, match="unsupported"):
        load_owned(direct)
    payload = torch.load(direct, weights_only=True)
    payload["boundary"] = "mid-document"
    bad = tmp_path / "bad.pt"
    torch.save(payload, bad)
    with pytest.raises(ValueError, match="boundary"):
        load(bad, identity)
    payload["format"] = "toruk-ordinary-v1"
    torch.save(payload, bad)
    with pytest.raises(ValueError, match="incompatible"):
        load(bad, identity)
    with pytest.raises(ValueError, match="training documents"):
        fit(
            variant,
            config,
            options,
            [dict(id="dev", split="dev", text="fixture")],
            tmp_path / "leak.pt",
            identity,
            steps=1,
        )


def test_fresh_fixture_label_validation_without_registered_data():
    inputs, labels = factual("disposable", 6, 900799)
    validate([dict(id="train-only", split="train", text="fixture")], inputs, labels, [])
    labels[0]["gold"] = "changed"
    with pytest.raises(ValueError, match="label/source"):
        validate([dict(id="train-only", split="train", text="fixture")], inputs, labels, [])
