"""Research-only fixed-budget selection with the existing learned ranking."""

import hashlib
from pathlib import Path
from typing import Any

from toruk_lm.source_spans import SourceSpanSelector


class RankBudgetSelector:
    """Retain the top two earlier user turns without an absolute score cutoff."""

    kind = "toruk-rank-budget-v1"

    def __init__(self, ranker: Any) -> None:
        self.ranker = ranker
        self.sha256 = hashlib.sha256(
            Path(__file__).read_bytes() + ranker.sha256.encode()
        ).hexdigest()

    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        if len(messages) <= 3:
            return list(range(len(messages))), False
        keep = set(range(len(messages) - 3, len(messages)))
        query = messages[-1]["content"]
        scored = [
            (
                self.ranker.score(query, message["content"], message["role"], index, len(messages)),
                index,
            )
            for index, message in enumerate(messages[:-3])
            if message["role"] == "user"
        ]
        keep.update(index for _, index in sorted(scored, reverse=True)[:2])
        return sorted(keep), bool(scored)


class RankBudgetEnvelopeSelector(SourceSpanSelector):
    """Use the unchanged envelope and bounds with fixed-budget learned ranking."""

    kind = "toruk-rank-budget-envelope-v1"

    def __init__(self, ranker: Any) -> None:
        super().__init__(RankBudgetSelector(ranker))
