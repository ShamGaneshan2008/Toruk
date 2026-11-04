"""Checks of the frozen offline rubric, not assertions of model capability."""

import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "recall_study", Path(__file__).resolve().parents[1] / "scripts/recall_study.py"
)
assert SPEC and SPEC.loader
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


def test_splits_and_exact_scoring() -> None:
    splits = [study.cases(name) for name in ("training", "development", "heldout")]
    assert len({row["id"] for split in splits for row in split}) == 36
    assert len({split[0]["groups"][0][0] for split in splits}) == 3
    quote = splits[1][2]
    expected = quote["groups"][0][0]
    assert study.score(expected, quote)["correct"]
    assert not study.score(expected.replace("  ", " "), quote)["correct"]
    assert not study.score('"' + expected + '"', quote)["correct"]


def test_uncertainty_does_not_excuse_asserting_a_candidate() -> None:
    ambiguous = study.cases("development")[-2]
    assert study.score("Which project do you mean?", ambiguous)["correct"]
    answer = "Which project? The code is " + ambiguous["forbidden"][0]
    result = study.score(answer, ambiguous)
    assert not result["correct"] and result["unsupported"]
    missing = study.cases("development")[-1]
    assert study.score("I don't know.", missing)["correct"]
    assert study.score("1234", missing)["unsupported"]
