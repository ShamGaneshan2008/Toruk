"""Source invariants and compatibility; model behavior is measured separately."""

from pathlib import Path

import pytest

from toruk_lm.chat_runtime import ChatError
from toruk_lm.chat_selector import ChatRelevanceSelector
from toruk_lm.source_spans import SourceSpanSelector, envelope

CHECKPOINT = Path("artifacts/chat-selector-v2-20261101/selector.json")


def test_exact_spans_correction_and_unrelated_fact() -> None:
    messages = [
        {"role": "user", "content": 'Mira code: "A:  b!?"; occupation: botanist.'},
        {"role": "user", "content": "Correction: Mira city is Jaipur."},
        {"role": "user", "content": "Give the code, occupation and city."},
    ]
    rendered = envelope(messages)[0]["content"]
    for message in messages:
        assert message["content"] in rendered
    assert rendered.index(messages[0]["content"]) < rendered.index(messages[1]["content"])
    assert "role=user" in rendered


def test_clear_ambiguous_and_missing_preserve_question() -> None:
    for records in (
        [],
        ["Project Birch code A1."],
        ["Project Birch code A1.", "Project Cedar code B2."],
    ):
        messages = [{"role": "user", "content": record} for record in records]
        messages.append({"role": "user", "content": "What is its code?"})
        text = envelope(messages)[0]["content"]
        assert text.endswith("What is its code?")
        for record in records:
            assert record in text
        assert "ask which one" in text


def test_old_checkpoint_and_selection_are_unchanged() -> None:
    old = ChatRelevanceSelector(CHECKPOINT)
    raw = CHECKPOINT.read_bytes()
    new = SourceSpanSelector(old)
    messages = [{"role": "user", "content": f"record {i}"} for i in range(10)]
    assert new.select(messages) == old.select(messages)
    assert CHECKPOINT.read_bytes() == raw
    assert new.kind != old.kind


def test_budgets_reject_without_partial_source_truncation() -> None:
    selector = SourceSpanSelector(ChatRelevanceSelector(CHECKPOINT))
    with pytest.raises(ChatError, match="input budget"):
        selector.select([{"role": "user", "content": "x"}] * 65)
    with pytest.raises(ChatError, match="storage budget"):
        selector.select([{"role": "user", "content": "é" * 2100}])
    with pytest.raises(ChatError, match="input budget"):
        selector.select([{"role": "user", "content": "x" * 16385}])
