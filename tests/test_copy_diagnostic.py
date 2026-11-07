"""A genuine query-only read intervention with matched inputs and frozen weights."""

from pathlib import Path

import pytest
import torch

from toruk_lm.copy_diagnostic import generate, make_cases
from toruk_lm.owned_lm import OwnedConfig, OwnedSession, build_model


def test_gap_intervention_moves_only_evidence_and_preserves_total_length():
    rows = make_cases("test", 99, 2, [0, 32, 64, 128, 256], 351)
    for world in {r["world_id"] for r in rows}:
        selected = [r for r in rows if r["world_id"] == world]
        assert len({r["expected"] for r in selected}) == 1
        assert len({r["question"] for r in selected}) == 1
        assert len({r["history"].replace(r["evidence"], "") for r in selected}) == 1
        for row in selected:
            assert len((row["history"] + row["question"]).encode()) == 351
            end = row["history"].index(row["evidence"]) + len(row["evidence"])
            assert len(row["history"][end:].encode()) == row["gap"]
    with pytest.raises(ValueError, match="gap does not fit"):
        make_cases("test", 99, 1, [1000], 351)


def test_query_read_gate_preserves_history_and_legacy_baseline():
    torch.set_num_threads(1)
    torch.manual_seed(7)
    model = build_model(OwnedConfig(width=8, heads=2, layers=1, slots=2), "memory_on")
    row = make_cases("test", 100, 1, [0], 351)[0]
    weights = {k: v.clone() for k, v in model.state_dict().items()}
    baseline = generate(model, row["history"], row["question"], 4)
    legacy = OwnedSession(model).generate(row["history"] + row["question"], 4)
    changed = generate(model, row["history"], row["question"], 4, query_read_off=True)
    assert baseline["generated_ids"] == legacy["generated_ids"]
    assert baseline["history_state_sha256"] == changed["history_state_sha256"]
    assert baseline["history_reader_calls"] == changed["history_reader_calls"] > 0
    assert baseline["query_answer_reader_calls"] > 0
    assert changed["query_answer_reader_calls"] == 0
    assert baseline["input_tokens"] == changed["input_tokens"] == 352
    assert all(torch.equal(v, model.state_dict()[k]) for k, v in weights.items())
    assert all(
        not module._forward_hooks and not module._forward_pre_hooks for module in model.modules()
    )


def test_diagnostic_rejects_ordinary_read_gate_and_unbounded_input():
    model = build_model(OwnedConfig(width=8, heads=2, layers=1), "ordinary")
    with pytest.raises(ValueError, match="owned memory model"):
        generate(model, "history", "question", 4, query_read_off=True)
    with pytest.raises(ValueError, match="<=384"):
        generate(model, "x" * 384, "question", 4)


def test_heldout_requires_development_and_started_phases_cannot_retry(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import copy_gap_probe

    monkeypatch.setattr(copy_gap_probe, "verify", lambda p: {"config": {}})
    with pytest.raises(ValueError, match="development execution"):
        copy_gap_probe.run_phase(tmp_path, "heldout")
    (tmp_path / "dev").mkdir()
    with pytest.raises(ValueError, match="phase already started"):
        copy_gap_probe.run_phase(tmp_path, "dev")
