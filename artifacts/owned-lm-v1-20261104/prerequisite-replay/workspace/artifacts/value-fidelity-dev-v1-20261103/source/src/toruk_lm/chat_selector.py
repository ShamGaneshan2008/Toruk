"""Small supervised turn ranker for bounded conversational evidence selection."""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from toruk_lm.chat_runtime import ChatError

FORMAT = "toruk-chat-selector-v1"
FEATURES = (
    "query_coverage",
    "shared_terms",
    "subject_match",
    "slot_match",
    "correction_marker",
    "relative_position",
    "is_user",
    "length_log",
)
STOP = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "do",
    "does",
    "for",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "now",
    "of",
    "please",
    "the",
    "to",
    "was",
    "what",
    "where",
    "which",
    "who",
    "with",
    "you",
    "your",
}


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP


def features(query: str, content: str, role: str, index: int, total: int) -> list[float]:
    q, c = words(query), words(content)
    shared = q & c
    query_words = re.findall(r"[a-z0-9]+", query.lower())
    subject = query_words[query_words.index("s") - 1] if "s" in query_words else ""
    # The learned scorer receives simple lexical/position cues, not answer labels.
    return [
        len(shared) / max(1, len(q)),
        min(len(shared), 4) / 4,
        float(bool(subject and subject in c)),
        float(bool(q & c and len(shared) >= 2)),
        float(
            bool(re.search(r"\b(correction|corrected|updated|actually|changed)\b", content.lower()))
        ),
        index / max(1, total - 1),
        float(role == "user"),
        min(math.log1p(len(content)) / 8, 1),
    ]


class ChatRelevanceSelector:
    """Rank all earlier turns; retain at most two plus three recent turns."""

    def __init__(self, checkpoint: Path) -> None:
        raw = checkpoint.read_bytes()
        try:
            saved = json.loads(raw)
        except ValueError as error:
            raise ChatError("Invalid trained chat selector checkpoint.") from error
        if (
            not isinstance(saved, dict)
            or saved.get("format") != FORMAT
            or saved.get("features") != list(FEATURES)
            or not isinstance(saved.get("weights"), list)
            or len(saved["weights"]) != len(FEATURES)
            or not all(type(x) in (int, float) and math.isfinite(x) for x in saved["weights"])
            or type(saved.get("bias")) not in (int, float)
            or type(saved.get("threshold")) not in (int, float)
            or not 0 < saved["threshold"] < 1
        ):
            raise ChatError("Incompatible trained chat selector checkpoint.")
        self.weights = [float(x) for x in saved["weights"]]
        self.bias = float(saved["bias"])
        self.threshold = float(saved["threshold"])
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.checkpoint_id = self.sha256[:12]
        self.kind = (
            "toruk-chat-selector-v2" if saved.get("protocol") == "chat-selector-v2" else FORMAT
        )

    def score(self, query: str, content: str, role: str, index: int, total: int) -> float:
        value = self.bias + sum(
            weight * feature
            for weight, feature in zip(
                self.weights, features(query, content, role, index, total), strict=True
            )
        )
        return 1 / (1 + math.exp(-max(-40, min(40, value))))

    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        if len(messages) <= 3:
            return list(range(len(messages))), False
        keep = set(range(len(messages) - 3, len(messages)))
        query = messages[-1]["content"]
        scored = [
            (self.score(query, message["content"], message["role"], index, len(messages)), index)
            for index, message in enumerate(messages[:-3])
            if message["role"] == "user"
        ]
        keep.update(
            index for score, index in sorted(scored, reverse=True)[:2] if score >= self.threshold
        )
        return sorted(keep), bool(scored)


def load_chat_selector(checkpoint: Path) -> Any:
    if checkpoint.suffix.lower() == ".json":
        return ChatRelevanceSelector(checkpoint)
    from toruk_lm.chat_foundation import TorukContextSelector

    return TorukContextSelector(checkpoint)
