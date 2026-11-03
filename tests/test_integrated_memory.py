"""Causal read, learned-write gradients, streaming boundaries and resume integrity."""

import json
import random
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from toruk_lm.data import sha256_file
from toruk_lm.integrated_memory import (
    FORMAT,
    IntegratedConfig,
    IntegratedMemoryLM,
    IntegratedSession,
    load_integrated,
    padded,
    text_tokens,
)
from toruk_lm.integrated_study import (
    batch_loss,
    make_case,
    make_data,
    read_data,
    seal,
    train,
    verify_seal,
)
from toruk_lm.tokenizer import ByteTokenizer


def small_model(variant="integrated"):
    torch.set_num_threads(1)
    torch.manual_seed(17)
    return IntegratedMemoryLM(IntegratedConfig(width=8), variant)


def save_model(path: Path, model: IntegratedMemoryLM):
    torch.save(
        {
            "format": FORMAT,
            "tokenizer": ByteTokenizer.fingerprint,
            "boundary": "optimizer-step",
            "config": asdict(model.config),
            "variant": model.variant,
            "model": model.state_dict(),
        },
        path,
    )


def test_answer_decoder_is_causal_and_reads_state():
    model = small_model()
    state = model.initial_state()
    local, question = padded([[1, 6]]), padded([[8, 9]])
    hidden, read, _ = model.prepare(local, question, state)
    prefix = torch.tensor([[1, 30, 31, 32]])
    a, _ = model.decode(prefix, hidden, read)
    prefix[0, -1] = 40
    b, _ = model.decode(prefix, hidden, read)
    assert torch.equal(a[:, :-1], b[:, :-1])
    other_hidden, other_read, _ = model.prepare(local, question, torch.ones_like(state))
    c, _ = model.decode(prefix, other_hidden, other_read)
    assert not torch.allclose(b, c)
    ordinary = small_model("ordinary")
    a_hidden, a_read, _ = ordinary.prepare(local, question, state)
    b_hidden, b_read, _ = ordinary.prepare(local, question, torch.ones_like(state))
    assert torch.equal(a_hidden, b_hidden) and torch.equal(a_read, b_read)


def test_answer_loss_reaches_writer_and_reader_without_runtime_gold():
    model = small_model()
    rows = [make_case("train", "correction", 0, random.Random(1))]
    loss, _ = batch_loss(model, rows)
    loss.backward()
    for layer in (model.value, model.write_address, model.read_address, model.output):
        assert layer.weight.grad is not None and layer.weight.grad.abs().sum() > 0


def test_session_is_bounded_questions_branch_and_reload_continues(tmp_path):
    model = small_model()
    checkpoint = tmp_path / "model.pt"
    save_model(checkpoint, model)
    session = IntegratedSession(model, sha256_file(checkpoint))
    for _ in range(100):
        session.consume("Set Ada color blue.")
    assert session.state.numel() == 6 * 8
    assert len(session.local) <= model.config.local_tokens
    before = session.state.clone()
    answer = session.answer("What is Ada's color?")
    assert torch.equal(before, session.state)
    path = tmp_path / "session.pt"
    session.save(path)
    restored = IntegratedSession.restore(model, checkpoint, path)
    assert restored.answer("What is Ada's color?") == answer
    session.consume("Change Ada color red.")
    restored.consume("Change Ada color red.")
    assert torch.equal(session.state, restored.state)
    assert session.local == restored.local and restored.records == 101
    clean = IntegratedSession(model, sha256_file(checkpoint))
    assert clean.records == 0 and not clean.state.any()
    with pytest.raises(ValueError, match="fresh"):
        session.save(path)


@pytest.mark.parametrize("corruption", ["identity", "nan", "shape", "dtype", "local"])
def test_incompatible_session_is_rejected(tmp_path, corruption):
    model = small_model()
    checkpoint, path = tmp_path / "model.pt", tmp_path / "session.pt"
    save_model(checkpoint, model)
    IntegratedSession(model, sha256_file(checkpoint)).save(path)
    saved = torch.load(path, weights_only=True)
    if corruption == "identity":
        saved["checkpoint_sha256"] = "different-model"
    elif corruption == "nan":
        saved["state"].fill_(float("nan"))
    elif corruption == "shape":
        saved["state"] = torch.zeros(1, 1, 1)
    elif corruption == "dtype":
        saved["state"] = saved["state"].double()
    else:
        saved["local"] = [1] * 97
    torch.save(saved, path)
    with pytest.raises(ValueError):
        IntegratedSession.restore(model, checkpoint, path)


def test_checkpoint_version_nonfinite_weights_and_input_bounds(tmp_path):
    model = small_model()
    path = tmp_path / "model.pt"
    save_model(path, model)
    restored, _ = load_integrated(path)
    assert all(
        torch.equal(a, b) for a, b in zip(model.parameters(), restored.parameters(), strict=True)
    )
    saved = torch.load(path, weights_only=True)
    saved["format"] = "toruk-controlled-v1"
    torch.save(saved, path)
    with pytest.raises(ValueError, match="incompatible"):
        load_integrated(path)
    saved["format"] = FORMAT
    saved["model"]["embedding.weight"].fill_(float("inf"))
    torch.save(saved, path)
    with pytest.raises(ValueError, match="nonfinite"):
        load_integrated(path)
    with pytest.raises(ValueError):
        text_tokens("a" * 65, 64)
    with pytest.raises(ValueError):
        model.encode(torch.tensor([[4, 0, 5]]))


def test_world_splits_oracle_and_training_resume(tmp_path):
    data = tmp_path / "data"
    make_data(data)
    ids = set()
    for split in ("train", "dev", "final"):
        for row in read_data(data, split):
            assert row["world"] not in ids
            ids.add(row["world"])
            truth = {}
            for event in row["events"]:
                if event["operation"] != "claim":
                    truth[event["key"]] = event["value"]
            assert row["answer"] == truth.get(row["query_key"], "?")
    with pytest.raises(ValueError, match="training"):
        read_data(data, "final", training=True)
    config = IntegratedConfig(width=8)
    full, partial, resumed = (tmp_path / name for name in ("full.pt", "part.pt", "resume.pt"))
    train(data, full, "integrated", 7, 4, config)
    train(data, partial, "integrated", 7, 2, config)
    train(data, resumed, "integrated", 7, 4, config, partial)
    a, b = torch.load(full, weights_only=True), torch.load(resumed, weights_only=True)
    assert all(torch.equal(a["model"][key], b["model"][key]) for key in a["model"])
    with pytest.raises(ValueError, match="mismatch"):
        train(data, tmp_path / "bad.pt", "integrated", 8, 5, config, partial)


def test_freeze_binds_source_data_checkpoint_and_selector(tmp_path):
    data = tmp_path / "data"
    make_data(data)
    checkpoint = tmp_path / "model.pt"
    save_model(checkpoint, small_model())
    protocol, selector = tmp_path / "protocol.md", tmp_path / "selector.json"
    protocol.write_text("frozen protocol")
    selector.write_text("selector bytes")
    freeze = tmp_path / "freeze.json"
    seal(data, [checkpoint], selector, protocol, freeze)
    verify_seal(freeze, checkpoint, data, selector)
    protocol.write_text("changed after freeze")
    with pytest.raises(ValueError, match="freeze mismatch"):
        verify_seal(freeze, checkpoint, data, selector)
    protocol.write_text("frozen protocol")
    alternate = tmp_path / "other-selector.json"
    alternate.write_text("other selector")
    with pytest.raises(ValueError, match="selector"):
        verify_seal(freeze, checkpoint, data, alternate)
    assert json.loads(freeze.read_text())["format"] == "toruk-integrated-freeze-v1"
