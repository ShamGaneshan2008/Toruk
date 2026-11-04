"""Bounded heuristic context selection; not the learned M6 memory model."""

import hashlib
import re
from pathlib import Path

STOP_WORDS = frozenset(
    "a an the is are was were be been to of for in on at and or my your me i it its "
    "what which who how does did do now only answer with please tell earlier".split()
)


def terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold())) - STOP_WORDS


class LexicalContextSelector:
    """Keep latest three turns and at most two query-ranked older user messages."""

    def __init__(self, kind: str = "lexical-v1") -> None:
        if kind not in ("lexical-v1", "lexical-v2"):
            raise ValueError("Unknown heuristic selector")
        self.selector_id = kind
        self.sha256 = hashlib.sha256(Path(__file__).read_bytes() + kind.encode()).hexdigest()

    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        recent = set(range(max(0, len(messages) - 3), len(messages)))
        query = terms(messages[-1]["content"])
        candidates = [i for i, m in enumerate(messages) if i not in recent and m["role"] == "user"]
        ranked = sorted(
            candidates,
            key=lambda i: (len(query & terms(messages[i]["content"])), i),
            reverse=True,
        )
        keep = recent | set(ranked[:2])
        if self.selector_id == "lexical-v2":
            # Treat an explicitly marked correction as dependent on its preceding
            # user fact even when it replaces the subject with a pronoun. Add at
            # most two messages, in chronological order; never rewrite evidence.
            additions = 0
            for anchor in sorted(ranked[:2]):
                following = [
                    i for i in range(anchor + 1, len(messages) - 1) if messages[i]["role"] == "user"
                ]
                for index in following:
                    if not re.match(
                        r"^(correction\s*:|actually\b|i was mistaken\b|update\s*:)",
                        messages[index]["content"].strip(),
                        re.I,
                    ):
                        break
                    if index not in keep:
                        if additions == 2:
                            break
                        keep.add(index)
                        additions += 1
        return sorted(keep), bool(candidates)
