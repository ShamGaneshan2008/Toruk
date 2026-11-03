"""Experimental routing intervention with a distinct, explicit checkpoint format."""

from pathlib import Path
from typing import Any

import torch
from torch import Tensor

from toruk_lm.integrated_memory import IntegratedConfig, IntegratedMemoryLM, padded
from toruk_lm.tokenizer import ByteTokenizer

FORMAT = "toruk-pooled-router-v2"


class PooledRouterLM(IntegratedMemoryLM):
    """Change address inputs only; preserve value encoding and answer computation."""

    def __init__(self, config: IntegratedConfig) -> None:
        super().__init__(config, "integrated")

    def routing_vector(self, tokens: Tensor) -> Tensor:
        if tokens.ndim != 2 or not 0 < tokens.shape[1] <= 256:
            raise ValueError("bounded token matrix required")
        if tokens.dtype != torch.long or (tokens < 0).any() or (tokens >= 259).any():
            raise ValueError("invalid byte tokens")
        mask = tokens.ne(0)
        if (mask.sum(1) == 0).any() or (tokens.eq(0)[:, :-1] & mask[:, 1:]).any():
            raise ValueError("nonempty right-padded input required")
        return (self.embedding(tokens) * mask[..., None]).sum(1) / mask.sum(1)[:, None]

    def routed_update(self, state: Tensor, encoded: Tensor, routing: Tensor) -> Tensor:
        self.check_state(state, len(encoded))
        weights = self.write_address(routing).softmax(-1)[:, : self.config.slots, None]
        proposed = self.value(encoded).tanh()[:, None]
        return (1 - weights) * state + weights * proposed

    def update(self, state: Tensor, record: Tensor) -> Tensor:
        if record.shape[1] > self.config.record_tokens:
            raise ValueError("record exceeds update budget")
        return self.routed_update(state, self.encode(record), self.routing_vector(record))

    def prepare(self, local: Tensor, query: Tensor, state: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        if local.shape[1] > self.config.local_tokens or query.shape[1] > self.config.query_tokens:
            raise ValueError("local context or query exceeds budget")
        self.check_state(state, len(query))
        question = self.encode(query)
        address = self.read_address(self.routing_vector(query))
        read = torch.bmm(address.softmax(-1)[:, None], state).squeeze(1)
        hidden = self.initial(torch.cat((self.encode(local), question, read), -1)).tanh()
        return hidden[None], read, address

    @torch.no_grad()
    def route_ids(self, records: list[list[int]], query: list[int]) -> tuple[list[int], int]:
        writes = self.write_address(self.routing_vector(padded(records))).argmax(-1).tolist()
        read = int(self.read_address(self.routing_vector(padded([query]))).argmax().item())
        return writes, read


def load_pooled(path: Path) -> tuple[PooledRouterLM, dict[str, Any]]:
    saved: dict[str, Any] = torch.load(path, map_location="cpu", weights_only=True)
    if (
        saved.get("format") != FORMAT
        or saved.get("tokenizer") != ByteTokenizer.fingerprint
        or saved.get("boundary") != "optimizer-step"
        or saved.get("variant") != "integrated"
    ):
        raise ValueError("incompatible pooled-router checkpoint")
    model = PooledRouterLM(IntegratedConfig(**saved["config"]))
    model.load_state_dict(saved["model"], strict=True)
    if any(not torch.isfinite(value).all() for value in model.state_dict().values()):
        raise ValueError("nonfinite routing weights")
    model.eval()
    return model, saved
