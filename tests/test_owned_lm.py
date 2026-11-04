"""Mechanistic and complete-document next-token LM regression checks."""

from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from toruk_lm.engine import load_checkpoint, setup
from toruk_lm.owned_data import cases, digest, write_data
from toruk_lm.owned_lm import (
    OwnedConfig,
    OwnedMemoryLM,
    OwnedSession,
    build_model,
    document_loss,
)
from toruk_lm.owned_training import evaluate, load, train, train_indices
from toruk_lm.recurrent import RecurrentLM


@pytest.fixture
def config():
    setup(23, 1)
    return OwnedConfig(context=8, width=8, heads=2, layers=1, slots=2)


def test_original_algebra_and_causal_predictions(config):
    model = OwnedMemoryLM(config.decoder(), config.slots)
    original = RecurrentLM(config.decoder(), config.slots)
    original.load_state_dict(model.state_dict())
    tokens = torch.tensor([[1, 20, 40, 80, 90]])
    state = model.initial_state()
    for actual, expected in zip(model(tokens, state), original(tokens, state), strict=True):
        assert torch.equal(actual, expected)
    changed = tokens.clone()
    changed[0, -1] = 100
    assert torch.equal(model(tokens, state)[0][:, :-1], model(changed, state)[0][:, :-1])


def test_direct_memory_effect_and_writer_gradient(config):
    model = OwnedMemoryLM(config.decoder(), config.slots)
    tokens = torch.tensor([[1, 33, 34, 35, 36, 37, 38, 39]])
    _, state, _ = model(tokens, model.initial_state())
    assert state.abs().max() <= 1
    future, _, _ = model(tokens, state)
    empty, _, _ = model(tokens, model.initial_state())
    assert not torch.allclose(future, empty)
    future.square().mean().backward()
    assert model.proposal.weight.grad.abs().sum() > 0
    assert model.gate.weight.grad.abs().sum() > 0
    assert model.readers[0].in_proj_weight.grad.abs().sum() > 0
    off, unchanged, _ = model(tokens, state, read_memory=False, update_memory=False)
    assert torch.equal(unchanged, state)
    assert torch.equal(off, model.backbone(tokens))


def test_stream_reset_clone_and_bounds(config):
    model = OwnedMemoryLM(config.decoder(), config.slots)
    tokens = [1, *range(20, 65)]
    whole, chunks = OwnedSession(model), OwnedSession(model)
    expected = whole.consume(tokens)
    for start in range(0, len(tokens), 3):
        actual = chunks.consume(tokens[start : start + 3])
        assert len(chunks.prefix) < config.context
        assert chunks.state.numel() == config.slots * config.width
        assert chunks.state.abs().max() <= 1
    assert torch.equal(actual, expected)
    clone = chunks.clone()
    assert torch.equal(chunks.consume([50]), clone.consume([50]))
    clone.reset()
    assert clone.tokens_read == 0 and torch.count_nonzero(clone.state) == 0
    assert torch.equal(clone.consume(tokens), expected)
    with pytest.raises(ValueError, match="reset"):
        clone.generate("new")
    with pytest.raises(ValueError, match="budget"):
        OwnedSession(model).generate("a" * 513)
    with pytest.raises(ValueError, match="context"):
        model(torch.ones(1, 9, dtype=torch.long), model.initial_state())
    with pytest.raises(ValueError, match="nonfinite"):
        model(torch.ones(1, 2, dtype=torch.long), model.initial_state() + torch.nan)


def test_documents_reset_and_all_targets_once(config):
    model = build_model(config, "memory_on")
    first, n, work = document_loss(
        model, "first document long enough", read=True, write=True, maximum=384
    )
    document_loss(model, "unrelated", read=True, write=True, maximum=384)
    replay, _, _ = document_loss(
        model, "first document long enough", read=True, write=True, maximum=384
    )
    assert torch.equal(first, replay)
    assert n == work == len("first document long enough") + 1
    with pytest.raises(ValueError, match="budget"):
        document_loss(model, "too long", read=True, write=True, maximum=2)


@pytest.mark.parametrize("variant", ("ordinary", "memory_off", "memory_on"))
def test_exact_optimizer_boundary_resume(config, tmp_path, variant):
    documents = cases("train", 1)[:2]
    full, first, resumed = [tmp_path / f"{name}.pt" for name in ("full", "first", "resumed")]
    train(config, variant, documents, full, steps=4, seed=23, batch=1)
    train(config, variant, documents, first, steps=2, seed=23, batch=1)
    train(config, variant, documents, resumed, steps=4, seed=23, batch=1, resume=first)
    _, a = load(full)
    _, b = load(resumed)
    for name in a["model"]:
        assert torch.equal(a["model"][name], b["model"][name]), name
    assert torch.equal(a["torch_rng"], b["torch_rng"])
    assert a["targets"] == b["targets"]
    for parameter in a["optimizer"]["state"]:
        for key, value in a["optimizer"]["state"][parameter].items():
            assert torch.equal(value, b["optimizer"]["state"][parameter][key])
    with pytest.raises(ValueError, match="resume"):
        train(config, variant, documents, tmp_path / "bad.pt", steps=5, seed=24, resume=first)
    with pytest.raises(ValueError, match="unsupported"):
        load_checkpoint(full)


def test_load_rejects_format_drift_corruption(config, tmp_path):
    path = tmp_path / "model.pt"
    train(config, "memory_on", cases("train", 1)[:1], path, steps=1, seed=23, batch=1)
    _, payload = load(path)
    for field, value, message in (
        ("format", "toruk-ordinary-v1", "unsupported"),
        ("runtime", {}, "identity"),
        ("next_step", -1, "progress"),
    ):
        changed = {**payload, field: value}
        torch.save(changed, tmp_path / "bad.pt")
        with pytest.raises(ValueError, match=message):
            load(tmp_path / "bad.pt")
    payload["model"]["slot_gate"][0, 0] = torch.nan
    torch.save(payload, tmp_path / "nan.pt")
    with pytest.raises(ValueError, match="nonfinite"):
        load(tmp_path / "nan.pt")


def test_dataset_is_separate_and_generation_excludes_gold(config, tmp_path):
    manifest = write_data(tmp_path / "data", {"train": 2, "dev": 1, "heldout": 1}, 384)
    assert len({split["sha256"] for split in manifest["splits"].values()}) == 3
    path = tmp_path / "model.pt"
    train(config, "memory_on", cases("train", 1), path, steps=1, seed=23, batch=1)
    dev = cases("dev", 1)[:1]
    first = evaluate(path, dev, tmp_path / "first.json", budget=4)
    dev[0]["answer"] = "unseen gold answer"
    dev[0]["text"] = dev[0]["prefix"] + dev[0]["answer"] + "\n"
    second = evaluate(path, dev, tmp_path / "second.json", budget=4)
    assert first["rows"][0]["generation"] == second["rows"][0]["generation"]
    assert first["rows"][0]["prefix_sha256"] == digest(dev[0]["prefix"])
    assert len(first["rows"][0]["generation"]["generated_ids"]) <= 4


def test_matched_parameters_and_common_order():
    config = OwnedConfig()
    counts = {
        variant: sum(p.numel() for p in build_model(config, variant).parameters())
        for variant in ("ordinary", "ordinary_matched", "memory_on")
    }
    assert counts == {"ordinary": 43072, "ordinary_matched": 56620, "memory_on": 56064}
    assert abs(counts["ordinary_matched"] / counts["memory_on"] - 1) < 0.01
    assert train_indices(6, 2, 2, 23) == train_indices(6, 2, 2, 23)
    assert asdict(config)["max_document_tokens"] == 384


def test_metadata_restoration_never_waives_runtime(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "owned_prerequisites", Path(__file__).parents[1] / "scripts/replay_owned_prerequisites.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root, reference = tmp_path / "root", tmp_path / "reference"
    (reference / "source").mkdir(parents=True)
    root.mkdir()
    archived = reference / "source/pyproject.toml"
    archived.write_text("old metadata", encoding="utf-8")
    expected = module.file_identity(archived)
    assert module.registered_source(root, reference, "pyproject.toml", expected) == archived
    (reference / "source/runtime.py").write_text("archived", encoding="utf-8")
    with pytest.raises(ValueError):
        module.registered_source(root, reference, "runtime.py", expected)
