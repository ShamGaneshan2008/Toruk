import json

import pytest
import torch

from toruk_lm.engine import setup
from toruk_lm.model import ModelConfig
from toruk_lm.recurrent import RecurrentLM, Session
from toruk_lm.worlds import make_worlds


def tiny():
    setup(9, 1)
    return RecurrentLM(ModelConfig(context=4, width=8, heads=2, layers=1), slots=2).eval()


def test_causality_write_timing_and_later_writer_gradients():
    model = tiny()
    x = torch.tensor([[1, 10, 11, 12]])
    changed = x.clone()
    changed[0, 2:] = torch.tensor([90, 91])
    state = model.initial_state()
    before = state.clone()
    logits, updated, _ = model(x, state)
    other, _, _ = model(changed, state)
    torch.testing.assert_close(logits[:, :2], other[:, :2], rtol=0, atol=0)
    torch.testing.assert_close(state, before, rtol=0, atol=0)
    # Same-segment logits cannot depend on the writer; later-segment logits must.
    same_grads = torch.autograd.grad(
        logits.sum(), model.proposal.weight, allow_unused=True, retain_graph=True
    )
    assert same_grads == (None,)
    later = model(torch.tensor([[30, 31]]), updated)[0]
    later.square().mean().backward()
    assert model.proposal.weight.grad is not None
    assert model.proposal.weight.grad.abs().sum() > 0
    assert model.gate.weight.grad.abs().sum() > 0
    assert model.readers[0].in_proj_weight.grad.abs().sum() > 0
    assert torch.isfinite(model.proposal.weight.grad).all()


def test_padding_lane_isolation_and_fixed_capacity():
    model = tiny()
    memory = model.initial_state(2)
    x = torch.tensor([[1, 12, 0, 0], [0, 0, 0, 0]])
    logits, updated, summary = model(x, memory)
    assert torch.isfinite(logits).all() and torch.isfinite(summary).all()
    assert torch.equal(updated[1], memory[1])
    alone = model(torch.tensor([[1, 12]]), memory[:1])
    torch.testing.assert_close(logits[:1, :2], alone[0], atol=1e-6, rtol=1e-6)
    torch.testing.assert_close(updated[:1], alone[1], atol=1e-6, rtol=1e-6)
    x[1] = torch.tensor([90, 91, 92, 93])
    changed = model(x, memory)
    torch.testing.assert_close(updated[0], changed[1][0], rtol=0, atol=0)
    for _ in range(20):
        _, updated, _ = model(x, updated)
        assert updated.shape == (2, 2, 8)
        assert updated.numel() * updated.element_size() == 128


@torch.no_grad()
def test_session_commit_parity_reset_clone_and_independence():
    model = tiny()
    session = Session(model)
    inputs = [1, 10, 11, 12, 13, 14]
    manual_logits, memory, _ = model(torch.tensor([inputs[:4]]), model.initial_state())
    first = session.consume(inputs[:4])
    torch.testing.assert_close(first, manual_logits[0, -1], rtol=0, atol=0)
    torch.testing.assert_close(session.memory, memory, rtol=0, atol=0)
    assert session.writes == 1
    session.consume(inputs[4:])
    assert session.writes == 1 and session.prefix == inputs[4:]
    copy = session.clone()
    copy.consume([25])
    assert session.prefix == inputs[4:]
    copy.memory.add_(2)
    assert not torch.equal(copy.memory, session.memory)
    session.flush()
    expected = model(torch.tensor([inputs[4:]]), memory)[1]
    torch.testing.assert_close(session.memory, expected, rtol=0, atol=0)
    assert session.writes == 2 and session.prefix == []
    independent = Session(model)
    independent.consume([1, 99])
    session.reset()
    assert torch.equal(session.memory, model.initial_state()) and not session.prefix
    session.consume(inputs[:4])
    torch.testing.assert_close(session.memory, memory, rtol=0, atol=0)
    assert independent.prefix == [1, 99]


def test_drained_document_resume_reload_and_mismatch_rejection(tmp_path):
    from toruk_lm.controlled import evaluate_controlled, load_controlled, train_controlled

    data = tmp_path / "data"
    make_worlds(data, worlds_per_split=2)
    config = ModelConfig(context=64, width=8, heads=2, layers=1)
    train, validation = data / "train.jsonl", data / "validation.jsonl"
    args = dict(train_data=train, validation=validation, variant="recurrent", config=config)
    train_controlled(**args, output=tmp_path / "full", steps=2)
    train_controlled(**args, output=tmp_path / "part", steps=1)
    checkpoint = tmp_path / "part/checkpoint.pt"
    train_controlled(**args, output=tmp_path / "resume", steps=2, resume=checkpoint)
    full_model, full = load_controlled(tmp_path / "full/checkpoint.pt")
    resumed_model, resumed = load_controlled(tmp_path / "resume/checkpoint.pt")
    for name in full["model"]:
        torch.testing.assert_close(full["model"][name], resumed["model"][name], rtol=0, atol=0)
    for name in full["optimizer"]["state"]:
        for field in full["optimizer"]["state"][name]:
            torch.testing.assert_close(
                full["optimizer"]["state"][name][field],
                resumed["optimizer"]["state"][name][field],
                rtol=0,
                atol=0,
            )
    assert torch.equal(full["torch_rng"], resumed["torch_rng"])
    assert full["python_rng"] == resumed["python_rng"]
    assert isinstance(full_model, RecurrentLM) and isinstance(resumed_model, RecurrentLM)
    scored = evaluate_controlled(tmp_path / "full/checkpoint.pt", validation, tmp_path / "eval", 2)
    again = evaluate_controlled(
        tmp_path / "resume/checkpoint.pt", validation, tmp_path / "again", 2
    )
    assert scored["groups"] == again["groups"]
    left = json.loads((tmp_path / "eval/predictions.json").read_text())
    right = json.loads((tmp_path / "again/predictions.json").read_text())
    assert [p["generated_ids"] for p in left] == [p["generated_ids"] for p in right]
    with pytest.raises(ValueError, match="mismatch"):
        train_controlled(**args, output=tmp_path / "bad", steps=3, seed=99, resume=checkpoint)
    with pytest.raises(ValueError, match="budget"):
        train_controlled(**args, output=tmp_path / "budget", steps=1, max_segments=2)
    tampered = dict(full, boundary="mid-document")
    torch.save(tampered, tmp_path / "bad.pt")
    with pytest.raises(ValueError, match="boundary"):
        load_controlled(tmp_path / "bad.pt")
