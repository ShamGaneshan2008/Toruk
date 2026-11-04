"""Low confidence must not waste the fixed evidence budget; bounds still apply."""

from typing import Any

import pytest

from toruk_lm.chat_runtime import ChatError
from toruk_lm.rank_budget import RankBudgetEnvelopeSelector, RankBudgetSelector


class Ranker:
    sha256 = "frozen-ranker"

    def score(self, query: str, content: str, role: str, index: int, total: int) -> float:
        return {"original": 0.15, "revision": 0.12, "noise": 0.01}.get(content, 0.001)


def messages() -> list[dict[str, str]]:
    return [
        {"role": "user", "content": "original"},
        {"role": "assistant", "content": "ack"},
        {"role": "user", "content": "revision"},
        {"role": "assistant", "content": "ack"},
        {"role": "user", "content": "noise"},
        {"role": "assistant", "content": "ack"},
        {"role": "user", "content": "question"},
    ]


def test_retains_low_scoring_evidence_and_revision_in_source_order() -> None:
    turns = messages()
    selector = RankBudgetEnvelopeSelector(Ranker())
    assert selector.select(turns) == ([0, 2, 4, 5, 6], True)
    assert turns == messages()  # Never edit source text or synthesize answers.


def test_budget_is_fixed_even_when_every_score_is_positive() -> None:
    turns = [{"role": "user", "content": "original"} for _ in range(30)]
    indices, used = RankBudgetSelector(Ranker()).select(turns)
    assert used and indices == [25, 26, 27, 28, 29]


@pytest.mark.parametrize("count", [1, 2, 3])
def test_short_histories_are_preserved(count: int) -> None:
    assert RankBudgetSelector(Ranker()).select(messages()[:count]) == (list(range(count)), False)


def test_assistant_turns_do_not_compete_as_evidence() -> None:
    turns = messages()
    turns[0]["role"] = "assistant"
    assert RankBudgetSelector(Ranker()).select(turns)[0] == [2, 4, 5, 6]


def test_envelope_still_rejects_oversized_input_and_sources() -> None:
    selector = RankBudgetEnvelopeSelector(Ranker())
    with pytest.raises(ChatError, match="input budget"):
        selector.select([{"role": "user", "content": "x" * 16385}])
    with pytest.raises(ChatError, match="storage budget"):
        selector.select([{"role": "user", "content": "x" * 4097}])


def test_identity_includes_the_underlying_checkpoint() -> None:
    ranker: Any = Ranker()
    old = RankBudgetEnvelopeSelector(ranker).sha256
    ranker.sha256 = "different-checkpoint"
    assert RankBudgetEnvelopeSelector(ranker).sha256 != old
