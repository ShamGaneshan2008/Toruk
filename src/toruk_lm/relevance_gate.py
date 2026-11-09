"""Research-only lexical admission before the unchanged recurrent turn ranking."""

import hashlib
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

from toruk_lm.context_selection import terms


class LexicalAdmissionSelector:
    """Only query-overlapping older user turns may compete for the two slots.

    All recurrent summaries and state updates still run in original order.
    No evidence text is rewritten and no checkpoint is trained or changed.
    """

    kind = "toruk-lexical-admission-v3"

    def __init__(self, ranker: Any) -> None:
        self.ranker = ranker
        self.model = ranker.model
        self.sha256 = hashlib.sha256(
            Path(__file__).read_bytes() + ranker.sha256.encode()
        ).hexdigest()
        self.checkpoint_sha256 = ranker.sha256
        self.last_trace: dict[str, Any] = {}

    @torch.inference_mode()
    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        if len(messages) <= 3:
            self.last_trace = {"admitted": [], "short_history": True}
            return list(range(len(messages))), False
        keep = set(range(len(messages) - 3, len(messages)))
        query_terms = terms(messages[-1]["content"])
        query = self.ranker._summary(messages[-1]["content"], self.model.initial_state())[0]
        memory = self.model.initial_state()
        ranked: list[tuple[float, int]] = []
        candidates = []
        term_calls = 1
        scanned_bytes = len(messages[-1]["content"].encode())
        for index, message in enumerate(messages[:-1]):
            # Deliberately stream even rejected/assistant/recent turns exactly as before.
            summary, memory = self.ranker._summary(message["content"], memory)
            if index in keep:
                continue
            overlap = set()
            if message["role"] == "user":
                overlap = query_terms & terms(message["content"])
                term_calls += 1
                scanned_bytes += len(message["content"].encode())
            admitted = message["role"] == "user" and bool(overlap)
            similarity = float(F.cosine_similarity(summary, query, dim=0).item())
            if admitted:
                ranked.append((similarity, index))
            candidates.append({"index": index, "role": message["role"],
                               "overlap": sorted(overlap), "admitted": admitted,
                               "cosine": similarity})
        keep.update(index for _, index in sorted(ranked, reverse=True)[:2])
        self.last_trace = {"query_terms": sorted(query_terms), "candidates": candidates,
                           "admitted": [index for _, index in ranked],
                           "gate_term_calls": term_calls, "gate_scan_bytes": scanned_bytes}
        return sorted(keep), bool(ranked)
