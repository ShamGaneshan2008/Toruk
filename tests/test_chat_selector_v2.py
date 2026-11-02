"""Protocol v2 split, scorer, and trained-checkpoint checks."""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))

from scripts.build_chat_selector_data_v2 import CATEGORIES, FRAMES, make_case
from scripts.evaluate_chat_selector_v2 import LexicalSelector, score
from toruk_lm.chat_selector import ChatRelevanceSelector


def test_split_templates_and_worlds_are_disjoint() -> None:
    assert len({FRAMES[split] for split in ("train", "dev", "final")}) == 3
    cases = {
        split: make_case(split, "long_recall", 1, random.Random(7))
        for split in ("train", "dev", "final")
    }
    assert len({case["world"] for case in cases.values()}) == 3
    assert len({case["messages"][0]["content"] for case in cases.values()}) == 3


def test_v2_evidence_labels_and_bounds() -> None:
    for category in CATEGORIES:
        case = make_case("final", category, 1, random.Random(7))
        assert len(case["messages"]) <= 20
        assert sum(len(item["content"].encode()) for item in case["messages"]) < 8192
        assert all(index < len(case["messages"]) - 3 for index in case["evidence_ids"])
        if category == "multi_fact":
            assert len(case["evidence_ids"]) == 2
        if category == "unknown":
            assert case["evidence_ids"] == [] and case["expected"] == []
        if category in ("correction", "conflict"):
            assert case["forbidden"] and case["evidence_ids"] != [0]


def test_frozen_answer_rules() -> None:
    case = {"expected": ["Mysuru", "FINALCODE01"], "forbidden": ["Nashik"]}
    assert score("Mysuru and FINALCODE01", case) == (True, False)
    assert score("Mysuru only", case) == (False, False)
    assert score("Mysuru and FINALCODE01, formerly Nashik", case) == (False, True)
    unknown = {"expected": [], "forbidden": []}
    assert score("I do not know; it was not supplied.", unknown) == (True, False)
    assert score("The code is FINALCODE01", unknown) == (False, True)


def test_lexical_baseline_is_bounded() -> None:
    case = make_case("final", "multi_fact", 1, random.Random(7))
    selected, used = LexicalSelector().select(case["messages"])
    assert used and len(selected) <= 5
    assert selected[-3:] == list(range(len(case["messages"]) - 3, len(case["messages"])))


def test_separate_trained_checkpoint_loads() -> None:
    path = Path("artifacts/chat-selector-v2-20261101/selector.json")
    if not path.exists():
        return
    selector = ChatRelevanceSelector(path)
    assert selector.sha256 == "abd9d2d1c20edb3ad5cf3282f8a26fca49fb44d508d4ba2ada5ebc9c666b7548"
    assert selector.kind == "toruk-chat-selector-v2"
    case = make_case("final", "correction", 1, random.Random(7))
    selected, used = selector.select(case["messages"])
    assert used and len(selected) <= 5
