"""Independent qualification guards, pair scoring and interventions."""

import importlib.util
from pathlib import Path

import pytest
import torch

from toruk_lm.integrated_memory import IntegratedConfig, IntegratedMemoryLM

SPEC = importlib.util.spec_from_file_location("qualify_memory", Path("scripts/qualify_memory.py"))
q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q)


def test_worlds_and_stress_pairs():
    rows = q.make_worlds()
    assert len(rows) == 504
    for base in rows[::3]:
        pair = [r for r in rows if r["id"] == base["id"]]
        assert [r["load"] for r in pair] == [0, 8, 32]
        assert all(r["events"][:8] == base["events"][:8] for r in pair)
        assert all(r["questions"] == base["questions"] for r in pair)
        assert len(base["questions"]) == (2 if base["category"] == "multi" else 1)
        for r in pair:
            truth = {}
            for event in r["events"]:
                if event["operation"] != "claim" and "value" in event:
                    truth[event["key"]] = event["value"]
            for question in r["questions"]:
                name = question["query"].split()[-1].rstrip(".")
                field = question["query"].split()[1]
                key = q.KEYS.index((name, field))
                assert question["expected"] == truth.get(key, "?")


def test_selectors_never_receive_gold():
    texts = ["Fact Ada: color=red.", "Fact Ben: pet=owl."] + ["noise"] * 5
    assert q.choose(texts, "Give color for Ada.", "lexical", None) == [0, 4, 5, 6]
    assert q.choose(texts, "Give color for Ada.", "position", None) == [3, 4, 5, 6]


def test_interventions_count_actual_work():
    torch.manual_seed(1)
    torch.set_num_threads(1)
    model = IntegratedMemoryLM(IntegratedConfig())
    texts = ["Fact Ada: color=red.", "Amend Ada: color=blue."]
    full = q.infer(model, None, texts, "Give color for Ada.", "integrated", "test")
    bypass = q.infer(model, None, texts, "Give color for Ada.", "no_correction", "test")
    half = q.infer(model, None, texts, "Give color for Ada.", "half_capacity", "test")
    assert full["selected_tokens"] == bypass["selected_tokens"]
    assert full["update_tokens"] - bypass["update_tokens"] == len(texts[1].encode())
    assert full["update_cells"] == 2 * bypass["update_cells"]
    assert half["effective_state_bytes"] == 576
    assert half["allocated_state_bytes"] == 1152


def test_bootstrap_preserves_pairing_and_freeze_rejects_drift(tmp_path):
    assert q.bootstrap({"7101-correction-0": 0.0, "7101-correction-1": 0.0}) == [0, 0]
    data = tmp_path / "data.json"
    data.write_text("original")
    q.dump(
        tmp_path / "freeze.json",
        {"format": "toruk-qualification-v1", "files": {str(data): q.file_identity(data)}},
    )
    q.verify(tmp_path)
    data.write_text("changed")
    with pytest.raises(ValueError, match="freeze mismatch"):
        q.verify(tmp_path)
