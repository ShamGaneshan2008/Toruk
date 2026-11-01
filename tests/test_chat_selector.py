"""Checks for the separate trained chat selector and frozen scoring rules."""

import json
import random
from pathlib import Path

import pytest

from scripts.build_chat_selector_data import make_case
from toruk_lm.chat_runtime import ChatError
from toruk_lm.chat_selector import FEATURES, FORMAT, ChatRelevanceSelector, features


def checkpoint(path: Path, weights: list[float], threshold: float = 0.5) -> Path:
    path.write_text(
        json.dumps(
            {
                "format": FORMAT,
                "features": list(FEATURES),
                "weights": weights,
                "bias": -2,
                "threshold": threshold,
            }
        )
    )
    return path


def test_features_retain_query_evidence_cues() -> None:
    good = features("What is Mira's city?", "Mira's city is Pune.", "user", 0, 19)
    bad = features("What is Mira's city?", "Tara likes chess.", "user", 2, 19)
    assert good[0] > bad[0]
    assert good[2] == 1 and bad[2] == 0


def test_trained_selector_keeps_evidence_and_recent_turns(tmp_path: Path) -> None:
    weights = [5, 2, 2, 1, 0, 0, 0, 0]
    selector = ChatRelevanceSelector(checkpoint(tmp_path / "selector.json", weights))
    messages = [
        {"role": "user", "content": "Mira's city is Pune."},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": "Tara likes chess."},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": "A new topic."},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": "What is Mira's city?"},
    ]
    selected, used = selector.select(messages)
    assert used and selected == [0, 4, 5, 6]
    assert selector.kind == FORMAT and len(selector.sha256) == 64


def test_unknown_can_select_no_old_turns(tmp_path: Path) -> None:
    selector = ChatRelevanceSelector(
        checkpoint(tmp_path / "selector.json", [0] * len(FEATURES), 0.8)
    )
    messages = [{"role": "user", "content": "Old unrelated note."}] * 4
    messages[-1] = {"role": "user", "content": "What is my secret code?"}
    selected, used = selector.select(messages)
    assert used and selected == [1, 2, 3]


def test_rejects_wrong_checkpoint_format(tmp_path: Path) -> None:
    path = tmp_path / "selector.json"
    path.write_text(json.dumps({"format": "toruk-controlled-v1", "weights": []}))
    with pytest.raises(ChatError, match="Incompatible"):
        ChatRelevanceSelector(path)


def test_generated_splits_and_evidence_labels_are_distinct() -> None:
    cases = {
        split: make_case(split, "correction", 0, random.Random(7))
        for split in ("train", "dev", "final")
    }
    assert len({case["messages"][0]["content"] for case in cases.values()}) == 3
    assert all(case["evidence_ids"] == [8] for case in cases.values())
    assert all(case["expected"] not in case["messages"][0]["content"] for case in cases.values())
    assert all(len(case["messages"]) == 19 for case in cases.values())
