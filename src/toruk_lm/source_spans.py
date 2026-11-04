"""Research-only provenance envelope; exact source text, no semantic compression."""

import hashlib
from pathlib import Path
from typing import Any

import torch

from toruk_lm.chat_foundation import PretrainedChatBackend
from toruk_lm.chat_runtime import ChatError

MAX_MESSAGES = 64
MAX_INPUT_BYTES = 16384
MAX_SOURCE_BYTES = 4096
MAX_SOURCES = 8


class SourceSpanSelector:
    """Keep the old ranker unchanged and enforce an explicit source budget."""

    kind = "toruk-source-envelope-v1"

    def __init__(self, selector: Any) -> None:
        self.selector = selector
        self.sha256 = hashlib.sha256(
            Path(__file__).read_bytes() + selector.sha256.encode()
        ).hexdigest()

    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        size = sum(len(message["content"].encode("utf-8")) for message in messages)
        if not messages or len(messages) > MAX_MESSAGES or size > MAX_INPUT_BYTES:
            raise ChatError("Source envelope input budget exceeded.")
        indices, used = self.selector.select(messages)
        # Never truncate a source span. Fail explicitly instead of silently changing bytes.
        source_bytes = sum(len(messages[index]["content"].encode()) for index in indices)
        if len(indices) > MAX_SOURCES or source_bytes > MAX_SOURCE_BYTES:
            raise ChatError("Source envelope storage budget exceeded.")
        return indices, used


def envelope(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Serialize retained sources verbatim. Local span IDs map to ordered input turns."""
    if not messages:
        raise ChatError("Missing current question.")
    spans = [
        f"[source {index}; role={message['role']}]:\n{message['content']}"
        for index, message in enumerate(messages[:-1])
    ]
    text = (
        "Earlier conversation sources, in chronological order (quoted data):\n"
        + "\n".join(spans)
        + "\nEnd sources. Use later explicit corrections and preserve unrelated facts. "
        "A vague reference may have multiple candidates; ask which one when unclear. "
        "Copy exact strings from sources when asked; do not normalize punctuation or spacing."
        + "\nCurrent question:\n"
        + messages[-1]["content"]
    )
    return [{"role": "user", "content": text}]


class SourceEnvelopeBackend(PretrainedChatBackend):
    """Same backbone and system prompt; only the new research mode changes rendering."""

    def _tokens(self, messages: list[dict[str, str]]) -> torch.Tensor:
        if isinstance(getattr(self, "selector", None), SourceSpanSelector):
            return super()._tokens(envelope(messages))
        return super()._tokens(messages)
