"""Matched counterfactuals and offline scores cannot replace generated answers."""

from pathlib import Path

import pytest
import torch

from toruk_lm.copy_diagnostic import generate
from toruk_lm.owned_lm import OwnedConfig, build_model


@pytest.fixture
def challenge(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import adversarial_twins

    return adversarial_twins


def test_counterfactuals_have_different_equal_length_targets_and_matched_context(challenge):
    rows = challenge.cases("unit", dict(seed=99, worlds_per_kind=2, unknown_worlds=2))
    for world in {r["world"] for r in rows if r["kind"] != "unknown"}:
        for location in ("local", "distant"):
            a, b = [r for r in rows if r["world"] == world and r["location"] == location]
            assert a["expected"] != b["expected"]
            assert len(a["expected"]) == len(b["expected"])
            assert a["history"].replace(a["expected"], "VALUE") == b["history"].replace(
                b["expected"], "VALUE"
            )
            assert a["query"] == b["query"] and a["alternative"] == b["expected"]
    assert len({(len(r["history"] + r["query"]) + 1) % 32 for r in rows}) > 1
    assert all(r["history"].endswith("\n") for r in rows)


def test_offline_target_order_does_not_change_scores_weights_or_generation(challenge):
    torch.set_num_threads(1)
    torch.manual_seed(7)
    model = build_model(OwnedConfig(width=8, heads=2, layers=1, slots=2), "memory_on")
    history, query = "If unknown answer ?.\nAda's tag is blue.\n", "Answer Ada's tag? "
    before = generate(model, history, query, 4)["generated_ids"]
    a = challenge.preference(model, history, query, ["blue", "gold"], False)
    b = challenge.preference(model, history, query, ["gold", "blue"], False)
    assert [s["logp"] for s in a["scores"]] == [s["logp"] for s in b["scores"]][::-1]
    assert before == generate(model, history, query, 4)["generated_ids"]


def test_heldout_and_retry_guards_precede_worker_start(challenge, tmp_path, monkeypatch):
    monkeypatch.setattr(challenge, "verify", lambda p: {"config": {}})
    with pytest.raises(ValueError, match="development must finish"):
        challenge.phase_run(tmp_path, "heldout")
    (tmp_path / "dev").mkdir()
    with pytest.raises(ValueError, match="no retries"):
        challenge.phase_run(tmp_path, "dev")
