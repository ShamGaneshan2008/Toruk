"""Focused checks for routing invariance, gradients and checkpoint separation."""

import importlib
import json
import random
from dataclasses import asdict

import pytest
import torch

from toruk_lm.integrated_memory import (
    IntegratedConfig,
    IntegratedSession,
    load_integrated,
    padded,
    text_tokens,
)
from toruk_lm.pooled_router import FORMAT, PooledRouterLM, load_pooled
from toruk_lm.tokenizer import ByteTokenizer


def driver(monkeypatch):
    monkeypatch.syspath_prepend("scripts")
    return importlib.import_module("study_routing_v2")


def model():
    torch.set_num_threads(1)
    torch.manual_seed(31)
    return PooledRouterLM(IntegratedConfig(width=8))


def test_routing_is_permutation_and_padding_invariant_but_values_are_ordered():
    lm = model()
    a = text_tokens("Set Ada color red.", 64)
    b = text_tokens("Ada red color Set.", 64)
    assert sorted(a) == sorted(b)
    pooled = lm.routing_vector(padded([a, b]))
    torch.testing.assert_close(pooled[0], pooled[1])
    single = lm.routing_vector(padded([a]))
    mixed = lm.routing_vector(padded([a, a + [13, 14]]))
    torch.testing.assert_close(single[0], mixed[0])
    assert not torch.allclose(lm.encode(padded([a])), lm.encode(padded([b])))


@pytest.mark.parametrize(
    "tokens", [torch.tensor([[1, 0, 3]]), torch.tensor([[0, 0]]), torch.tensor([[259]])]
)
def test_router_rejects_invalid_input(tokens):
    with pytest.raises(ValueError):
        model().routing_vector(tokens)


def test_new_training_objective_reaches_memory_and_answer_layers(monkeypatch):
    study = driver(monkeypatch)
    from toruk_lm.integrated_study import make_case

    row = make_case("train", "preservation", 0, random.Random(3))
    lm = model()
    loss, _ = study.loss_for(lm, [row])
    loss.backward()
    for layer in (lm.embedding, lm.encoder, lm.value, lm.write_address, lm.read_address, lm.output):
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in layer.parameters())


def test_new_checkpoint_reload_and_state_influence(tmp_path):
    lm = model()
    path = tmp_path / "new.pt"
    torch.save(
        {
            "format": FORMAT,
            "tokenizer": ByteTokenizer.fingerprint,
            "boundary": "optimizer-step",
            "variant": "integrated",
            "config": asdict(lm.config),
            "model": lm.state_dict(),
        },
        path,
    )
    restored, _ = load_pooled(path)
    before = IntegratedSession(lm, "test")
    after = IntegratedSession(restored, "test")
    for session in (before, after):
        session.consume("Set Ada color red.")
        session.consume("Change Ada color blue.")
    assert torch.equal(before.state, after.state)
    assert before.answer("What is Ada's color?") == after.answer("What is Ada's color?")
    local = padded([[1, 8]])
    query = padded([[4, 9]])
    h1, r1, _ = lm.prepare(local, query, lm.initial_state())
    h2, r2, _ = lm.prepare(local, query, torch.ones_like(lm.initial_state()))
    assert not torch.allclose(r1, r2) and not torch.allclose(h1, h2)
    with pytest.raises(ValueError, match="incompatible"):
        load_integrated(path)
    saved = torch.load(path, weights_only=True)
    saved["format"] = "toruk-integrated-lm-v1"
    old = tmp_path / "old.pt"
    torch.save(saved, old)
    with pytest.raises(ValueError, match="incompatible"):
        load_pooled(old)


def test_world_oracle_stress_and_registered_drift(monkeypatch, tmp_path):
    study = driver(monkeypatch)
    rows = study.worlds()
    assert len(rows) == 504
    for row in rows:
        truth = {}
        evidence = {}
        for i, event in enumerate(row["events"]):
            if event["operation"] != "claim":
                truth[event["key"]] = event["value"]
                evidence[event["key"]] = i
        for question in row["questions"]:
            assert question["expected"] == truth.get(question["key"], "?")
            assert question["evidence"] == (
                [evidence[question["key"]]] if question["key"] in evidence else []
            )
    for base in rows[::3]:
        partners = [r for r in rows if r["id"] == base["id"]]
        assert [r["load"] for r in partners] == [0, 8, 32]
        assert all(p["events"][:8] == base["events"][:8] for p in partners)
    source = tmp_path / "kernel.py"
    source.write_text("initial")
    (tmp_path / "registration.json").write_text(
        json.dumps({"files": {str(source): study.file_identity(source)}})
    )
    study.verify_registered(tmp_path)
    source.write_text("changed")
    with pytest.raises(ValueError, match="drift"):
        study.verify_registered(tmp_path)
