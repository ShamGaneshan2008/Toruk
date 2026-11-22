"""Zero-forward contracts: saved inputs, pure-vector metrics and registration guard."""

import ast
import io
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import first_byte_probe as probe  # noqa: E402


def test_exact_saved_inputs_and_260_record_plan():
    prefixes, labels, originals, checkpoints, plan = probe.inputs_from_saved()
    assert len(prefixes) == len(labels) == 32 and len(plan) == 260
    assert sum(p["phase"] == "prefix" for p in plan) == 132
    assert sum(p["replay"] for p in plan) == 4
    assert plan[132]["phase"] == "teacher" and plan[-1]["id"] == "train-079"
    assert list(checkpoints) == list(probe.CELLS)
    for case, label in zip(prefixes, labels, strict=True):
        assert case["input_ids"] == label["full_document_ids"][:54]
        assert label["full_document_ids"][54] == label["expected_first_id"]
        assert label["mask_positions"] == [53, 54, 55]
        assert len(case["prefix"].encode()) == 53 and case["input_ids"][-2:] == [66, 64]
        assert case["id"] in originals["947-ordinary"]


def test_metrics_rank_margin_and_suppression_without_model():
    logits = [-1000.0] * 259
    logits[0] = 100.0
    logits[1] = 99.0
    logits[119] = 3.0
    logits[118] = 2.0
    logits[112] = 1.0
    result = probe.measurement(logits, 112)
    assert result["predicted_first_id"] == 119 and result["expected_rank"] == 3
    assert result["expected_minus_predicted_margin"] == -2
    assert result["winner_minus_runner_up"] == 1
    assert result["expected_probability_eligible"] == pytest.approx(
        math.exp(1) / (math.exp(1) + math.exp(2) + math.exp(3))
    )
    assert result["expected_probability_full"] < result["expected_probability_eligible"]
    assert not result["near_tied_decision"] and not result["near_tied_gold"]


def test_ties_use_lowest_id_and_correct_gold_zero_margin_is_not_near_gold():
    logits = [-1000.0] * 259
    logits[111] = logits[112] = 4.0
    wrong = probe.measurement(logits, 112)
    correct = probe.measurement(logits, 111)
    assert wrong["predicted_first_id"] == 111 and wrong["expected_rank"] == 2
    assert wrong["near_tied_gold"] and wrong["near_tied_decision"]
    assert not correct["near_tied_gold"] and correct["near_tied_decision"]
    assert wrong["tied_winners"] == 2


def test_nonfinite_raw_result_is_preserved_before_stop():
    class SavedVector:
        def detach(self):
            return self

        def tolist(self):
            return [float("nan") if i == 42 else 0.0 for i in range(259)]

    stream = io.StringIO()
    with pytest.raises(probe.ProbeStop, match="NONFINITE"):
        probe.vector_record(stream, dict(id="numeric-fixture"), SavedVector())
    saved = json.loads(stream.getvalue())
    assert saved["logits"][42] == "nan" and saved["nonfinite_indices"] == [42]


def test_model_loading_requires_registration_before_any_model_import(monkeypatch, tmp_path):
    monkeypatch.setattr(probe, "RUN", tmp_path / "unregistered")
    with pytest.raises(probe.ProbeStop, match="registration required"):
        probe.load_saved("947-ordinary")


def test_no_training_or_answer_generation_calls_in_probe_source():
    tree = ast.parse(Path(probe.__file__).read_text(encoding="utf-8"))
    calls = [n.func for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert not any(
        isinstance(n, ast.Attribute) and n.attr in {"generate", "backward", "step"} for n in calls
    )
    assert not any(isinstance(n, ast.Name) and n.id in {"AdamW", "Adam", "SGD"} for n in calls)
