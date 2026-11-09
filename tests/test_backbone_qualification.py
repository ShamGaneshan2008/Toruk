"""Quality and resource contracts without candidate model inference."""

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from qualify_answer_backbone import (  # noqa: E402
    SYSTEM,
    aggregate,
    leakage,
    make_cases,
    messages,
    passed,
    score,
    sha,
    tree_stats,
    verify,
    write,
)


def test_new_data_deterministic_and_separated_from_successor():
    dev = make_cases("development", 81711, 2)
    held = make_cases("heldout", 81731, 5)
    assert held == make_cases("heldout", 81731, 5)
    assert len(dev) == 12 and len(held) == 30
    legacy = json.loads((ROOT / "artifacts/m6-successor-v1/execution/heldout.json").read_bytes())
    assert leakage(dev, held, legacy)["status"] == "PASS"
    bad = copy.deepcopy(held)
    bad[0]["expected"] = dev[0]["expected"]
    with pytest.raises(ValueError, match="overlap"):
        leakage(dev, bad, legacy)


def test_generation_uses_only_identical_instruction_and_reference():
    case = make_cases("heldout", 81731, 1)[0]
    before = messages(case)
    case["expected"] = "OFFLINE_LABEL_CANARY"
    case["alternatives"] = ["OTHER_OFFLINE_CANARY"]
    assert messages(case) == before
    assert before[0] == {"role": "system", "content": SYSTEM}
    assert all(set(m) == {"role", "content"} for m in before)
    with pytest.raises(ValueError, match="new qualification"):
        messages({"messages": [{"role": "user", "content": "old heldout"}]})


def test_known_scoring_rejects_wrong_negated_and_mixed_values():
    case = make_cases("heldout", 81731, 1)[0]
    assert score(case["expected"], case)["correct"]
    assert not score(case["alternatives"][0], case)["correct"]
    assert not score("not " + case["expected"], case)["correct"]
    assert not score(case["expected"] + " or " + case["alternatives"][0], case)["correct"]
    assert not score("UNKNOWN", case)["correct"]


def test_exact_literal_preserves_internal_spaces():
    case = next(c for c in make_cases("heldout", 81731, 1) if c["kind"] == "literal")
    assert score(case["expected"], case)["correct"]
    assert not score(case["expected"].replace("  ", " "), case)["correct"]
    assert not score('"' + case["expected"] + '"', case)["correct"]


def test_valid_abstentions_and_guessing_are_distinguished():
    case = next(c for c in make_cases("heldout", 81731, 1) if c["kind"] == "missing")
    for answer in (
        "UNKNOWN",
        "The access phrase is not known.",
        "It is not available.",
        "I don't know.",
    ):
        assert score(answer, case)["correct"], answer
    for answer in ("KEY1234", "Unknown; the phrase is KEY1234.", "I don't know, maybe code7."):
        assert not score(answer, case)["correct"], answer


def test_both_quality_floors_and_completion_are_required():
    result = {"cases": 30, "known_cases": 25, "correct": 18, "known_correct": 15}
    assert passed(result, True)
    assert not passed(result, False)
    assert not passed({**result, "correct": 17}, True)
    assert not passed({**result, "known_correct": 14}, True)
    assert not passed({**result, "cases": 29}, True)


def test_replay_is_charged_but_not_counted_as_an_extra_question():
    row = {
        "kind": "binding",
        "is_replay": False,
        "score": {
            "correct": True,
            "abstention": False,
            "wrong_listed_value": False,
            "unsupported_response_proxy": False,
        },
        "wall_seconds": 2,
        "cpu_seconds": 3,
        "metrics": {"selected_context_tokens": 100, "output_tokens": 2},
    }
    result = aggregate([row, {**row, "is_replay": True}])
    assert result["cases"] == 1 and result["correct"] == 1
    assert result["online_cpu_seconds"] == 6 and result["online_wall_seconds"] == 4
    assert result["prompt_tokens"] == 200


def test_resource_meter_includes_launcher_descendant_and_cpu():
    class Process:
        def __init__(self, pid, size, children):
            self.pid, self.size, self.descendants = pid, size, children

        def children(self, recursive):
            assert recursive
            return self.descendants

        def memory_info(self):
            return SimpleNamespace(rss=self.size, private=self.size * 2)

        def cpu_times(self):
            return SimpleNamespace(user=2.0, system=1.0)

    child = Process(2, 100_000_000, [])
    launcher = Process(1, 1_000_000, [child])
    assert tree_stats(launcher) == (101_000_000, 202_000_000, {1: 3.0, 2: 3.0})


def test_hash_drift_and_output_overwrite_fail_closed(tmp_path):
    artifact = tmp_path / "candidate.json"
    write(artifact, {"identity": "pinned"})
    write(
        tmp_path / "registration.json",
        {"bindings": {str(artifact): sha(artifact)}, "dependencies": {}},
    )
    verify(tmp_path)
    with pytest.raises(FileExistsError):
        write(artifact, {"identity": "new"})
    artifact.write_text("changed")
    with pytest.raises(ValueError, match="drift"):
        verify(tmp_path)
