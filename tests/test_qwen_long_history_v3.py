"""Candidate admission must not change streaming state, evidence bytes or budgets."""

import copy
import importlib.util
from pathlib import Path

import pytest
import torch

from toruk_lm.relevance_gate import LexicalAdmissionSelector


class FakeModel:
    def initial_state(self):
        return torch.tensor([0.0])


class FakeRanker:
    sha256 = "unchanged-checkpoint"

    def __init__(self):
        self.model = FakeModel()
        self.seen = []
        self.states = []

    def _summary(self, content, state):
        self.seen.append(content)
        self.states.append(float(state.item()))
        vector = (
            torch.tensor([1.0, 0.0])
            if "ACK" in content or "noise" in content or content.startswith("Which")
            else torch.tensor([0.8, 0.6])
        )
        return vector, state + 1


def history():
    return [
        {"role": "user", "content": "Vela flower is iris; folder is gray."},
        {"role": "assistant", "content": "ACK Vela flower."},
        {"role": "user", "content": "Update Vela folder to white; flower unchanged."},
        {"role": "assistant", "content": "ACK"},
        {"role": "user", "content": "noise unrelated"},
        {"role": "assistant", "content": "noise ACK"},
        {"role": "user", "content": "Which flower belongs to Vela?"},
    ]


def test_admission_excludes_high_scoring_acknowledgement_and_keeps_update():
    ranker = FakeRanker()
    selected, used = LexicalAdmissionSelector(ranker).select(history())
    assert selected == [0, 2, 4, 5, 6] and used
    assert ranker.seen == [history()[-1]["content"], *[m["content"] for m in history()[:-1]]]
    assert ranker.states == [0, 0, 1, 2, 3, 4, 5]


def test_rejected_user_noise_does_not_consume_an_older_slot():
    messages = history()
    messages[2]["content"] = "noise unrelated"
    selector = LexicalAdmissionSelector(FakeRanker())
    assert selector.select(messages)[0] == [0, 4, 5, 6]
    assert selector.last_trace["admitted"] == [0]
    assert selector.last_trace["gate_term_calls"] == 3


def test_no_overlap_has_no_fallback_or_answer_extraction():
    messages = history()
    messages[-1]["content"] = "Describe destinations."
    assert LexicalAdmissionSelector(FakeRanker()).select(messages) == ([4, 5, 6], False)


def test_exact_bytes_and_input_objects_preserved():
    messages = history()
    messages[0]["content"] = 'Vela flower label is "X:  Q-7!".'
    original = copy.deepcopy(messages)
    selected, _ = LexicalAdmissionSelector(FakeRanker()).select(messages)
    assert 0 in selected and messages == original
    assert "X:  Q-7!" in messages[0]["content"]


def test_top_two_and_latest_three_budget_in_source_order():
    messages = [{"role": "user", "content": "Vela flower"} for _ in range(12)]
    assert LexicalAdmissionSelector(FakeRanker()).select(messages)[0] == [7, 8, 9, 10, 11]


@pytest.mark.parametrize("n", [1, 2, 3])
def test_short_history_unchanged(n):
    assert LexicalAdmissionSelector(FakeRanker()).select(history()[:n]) == (list(range(n)), False)


def test_identity_binds_original_checkpoint():
    ranker = FakeRanker()
    before = LexicalAdmissionSelector(ranker).sha256
    ranker.sha256 = "different"
    assert LexicalAdmissionSelector(ranker).sha256 != before


def test_model_boundary_rejects_heldout_or_extra_ids():
    path = Path(__file__).resolve().parents[1] / "scripts/qwen_long_history_v3.py"
    spec = importlib.util.spec_from_file_location("dev_v3_contract", path)
    assert spec and spec.loader
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    cases = [{"id": f"case-development-{i}"} for i in range(7)]
    allowed = {c["id"] for c in cases}
    runner.validate_development(cases, allowed)
    cases[-1] = {"id": "case-heldout-0"}
    with pytest.raises(ValueError, match="seven sealed"):
        runner.validate_development(cases, allowed)
