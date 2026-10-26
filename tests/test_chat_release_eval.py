"""Frozen v2 rubric checks before any model evaluation."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_chat_release_v2 import score_answer, validate_fixture  # noqa: E402


def test_frozen_fixture_shape_and_categories():
    fixture = json.loads((ROOT / "configs/chat-release-eval-v2.json").read_text(encoding="utf-8"))
    validate_fixture(fixture)
    assert len(fixture["cases"]) == 20


def test_quality_rubrics_handle_exact_fact_correction_and_uncertainty():
    exact = {"accepted": ["HELLO"], "forbidden": [], "exact": True}
    assert score_answer("Hello.", exact)["quality"] is True
    assert score_answer("Hello there", exact)["quality"] is False
    fact = {"accepted": ["Rome"], "forbidden": ["Milan"], "factual_expected": True}
    assert score_answer("The capital is Rome.", fact)["factual_correct"] is True
    assert score_answer("Rome and Milan", fact)["quality"] is False
    corrected = {
        "accepted": ["Thursday"],
        "forbidden": ["Tuesday"],
        "correction_expected": True,
    }
    assert score_answer("Thursday", corrected)["correction_correct"] is True
    assert score_answer("Tuesday", corrected)["correction_correct"] is False
    unknown = {"accepted": ["do not know"], "forbidden": [], "unsupported_case": True}
    assert score_answer("I do not know.", unknown)["unsupported_answer"] is False
    assert score_answer("1234", unknown)["unsupported_answer"] is True


def test_invalid_fixture_is_rejected():
    with pytest.raises(ValueError):
        validate_fixture({"kind": "toruk-chat-release-eval-v2", "cases": []})
