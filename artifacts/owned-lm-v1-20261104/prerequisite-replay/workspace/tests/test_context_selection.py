"""Correction grouping, bounded selection, and frozen evaluation accounting."""

import json
import sys
from pathlib import Path

import pytest

from toruk_lm.context_selection import LexicalContextSelector
from toruk_lm.inference_server import validate_request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_context_selection import score  # noqa: E402


def conversation():
    history = []
    for text in (
        "The pickup location is North Dock.",
        "Correction: it is South Dock.",
        "The pickup location label is printed on paper.",
        "The garden has trees and a bench.",
        "Lunch uses rice and vegetables.",
    ):
        history.extend([{"role": "user", "content": text}, {"role": "assistant", "content": "OK"}])
    return [*history, {"role": "user", "content": "What is the pickup location?"}]


def test_correction_survives_without_query_terms_and_selection_is_verbatim():
    messages = conversation()
    original = json.dumps(messages)
    before, _ = LexicalContextSelector("lexical-v1").select(messages)
    after, used = LexicalContextSelector("lexical-v2").select(messages)
    assert 0 in before and 2 not in before
    assert {0, 2} <= set(after)
    assert after == sorted(set(after)) and used
    assert len(after) <= 7 and after[-3:] == [8, 9, 10]
    assert json.dumps(messages) == original


def test_short_histories_and_repeated_calls_have_no_persistent_state():
    selector = LexicalContextSelector("lexical-v2")
    short = [{"role": "user", "content": "Hi"}]
    assert selector.select(short) == ([0], False)
    first = selector.select(conversation())
    selector.select(short)
    assert selector.select(conversation()) == first
    with pytest.raises(ValueError):
        LexicalContextSelector("missing")


def test_correction_expansion_is_bounded_even_with_a_long_chain():
    messages = conversation()
    for i in (2, 4, 6):
        messages[i]["content"] = f"Correction: it is Dock {i}."
    selected, _ = LexicalContextSelector("lexical-v2").select(messages)
    assert len(selected) <= 7
    assert selected[-1] == len(messages) - 1


def test_frozen_splits_are_disjoint_and_fit_request_limits():
    dev = json.loads((ROOT / "configs/context-eval-dev-v1.json").read_text())
    final = json.loads((ROOT / "configs/context-eval-final-v1.json").read_text())
    assert {c["id"] for c in dev["cases"]}.isdisjoint({c["id"] for c in final["cases"]})
    assert len(final["cases"]) == 12
    assert len({c["category"] for c in final["cases"]}) == 6
    for fixture in (dev, final):
        for case in fixture["cases"]:
            validate_request({"messages": case["messages"], **fixture["settings"]})


def test_scoring_rejects_stale_answers_and_does_not_count_abstention_as_invention():
    case = {"accepted": ["South Dock"], "forbidden": ["North Dock"]}
    assert score("South Dock", case) == {"correct": True, "unsupported_flag": False}
    assert score("North Dock", case) == {"correct": False, "unsupported_flag": True}
    assert score("I don't know", case) == {"correct": False, "unsupported_flag": False}
    assert not score("South Dock and North Dock", case)["correct"]
