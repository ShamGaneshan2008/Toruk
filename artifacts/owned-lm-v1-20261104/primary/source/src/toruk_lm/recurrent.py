"""Bounded segment memory. Updates occur strictly after current-segment logits."""

from collections.abc import Callable

import torch
from torch import Tensor, nn

from toruk_lm.model import CausalLM, ModelConfig

Decision = Callable[[Tensor, Tensor, Tensor], bool]


class RecurrentLM(nn.Module):
    def __init__(self, config: ModelConfig, slots: int = 4) -> None:
        super().__init__()
        if slots <= 0:
            raise ValueError("slots must be positive")
        self.config, self.slots = config, slots
        self.backbone = CausalLM(config)
        self.readers = nn.ModuleList(
            nn.MultiheadAttention(config.width, config.heads, batch_first=True)
            for _ in range(config.layers)
        )
        self.read_norms = nn.ModuleList(nn.LayerNorm(config.width) for _ in range(config.layers))
        self.proposal = nn.Linear(2 * config.width, config.width)
        self.gate = nn.Linear(2 * config.width, config.width)
        self.slot_proposal = nn.Parameter(torch.zeros(slots, config.width))
        self.slot_gate = nn.Parameter(torch.zeros(slots, config.width))
        nn.init.normal_(self.slot_proposal, std=0.02)

    def initial_state(self, batch: int = 1) -> Tensor:
        return self.slot_gate.new_zeros(batch, self.slots, self.config.width)

    def forward(self, tokens: Tensor, memory: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        if tokens.ndim != 2 or not 0 < tokens.shape[1] <= self.config.context:
            raise ValueError("expected [batch, 1..context] tokens")
        if memory.shape != (tokens.shape[0], self.slots, self.config.width):
            raise ValueError("memory shape mismatch")
        if memory.dtype != self.slot_gate.dtype or not torch.isfinite(memory).all():
            raise ValueError("invalid memory dtype/values")
        padding = tokens.eq(0)
        if (padding[:, :-1] & ~padding[:, 1:]).any():
            raise ValueError("only right padding is supported")
        active = ~padding.all(dim=1)
        # Avoid all-masked attention NaNs; original padding still masks the writer/loss.
        safe_tokens = tokens.clone()
        safe_tokens[~active, 0] = 1
        safe_padding = safe_tokens.eq(0)
        length = tokens.shape[1]
        x = self.backbone.embedding(safe_tokens)
        x = x + self.backbone.position(torch.arange(length, device=tokens.device))
        causal = torch.ones(length, length, dtype=torch.bool, device=tokens.device).triu(1)
        for block, reader, norm in zip(
            self.backbone.blocks, self.readers, self.read_norms, strict=True
        ):
            x = block(x, causal, safe_padding)
            read, _ = reader(norm(x), memory, memory, need_weights=False)
            x = x + read
        hidden = self.backbone.norm(x)
        logits = self.backbone.output(hidden).masked_fill(padding[..., None], 0)
        valid = (~padding)[..., None]
        summary = (hidden * valid).sum(1) / valid.sum(1).clamp_min(1)
        joined = torch.cat((summary[:, None].expand_as(memory), memory), dim=-1)
        proposal = torch.tanh(self.proposal(joined) + self.slot_proposal)
        gate = torch.sigmoid(self.gate(joined) + self.slot_gate)
        updated = (1 - gate) * memory + gate * proposal
        updated = torch.where(active[:, None, None], updated, memory)
        return logits, updated, summary


class Session:
    """Single-document inference state. Clone before questions; flush boundaries are explicit."""

    def __init__(self, model: RecurrentLM, decide: Decision | None = None) -> None:
        self.model, self.decide = model, decide
        self.memory = model.initial_state()
        self.prefix: list[int] = []
        self.last_logits: Tensor | None = None
        self.tokens_read = 0
        self.forward_tokens = 0
        self.writes = 0
        self.accepted = 0

    def clone(self) -> "Session":
        other = Session(self.model, self.decide)
        other.memory = self.memory.clone()
        other.prefix = list(self.prefix)
        other.last_logits = self.last_logits.clone() if self.last_logits is not None else None
        other.tokens_read, other.forward_tokens = self.tokens_read, self.forward_tokens
        other.writes, other.accepted = self.writes, self.accepted
        return other

    def reset(self) -> None:
        self.memory = self.model.initial_state()
        self.prefix = []
        self.last_logits = None
        self.tokens_read = self.forward_tokens = self.writes = self.accepted = 0

    def commit(self, proposed: Tensor, summary: Tensor) -> None:
        accept = self.decide is None or self.decide(self.memory, proposed, summary)
        self.writes += 1
        if accept:
            self.memory = proposed.clone()
            self.accepted += 1
        self.prefix = []

    @torch.no_grad()
    def consume(self, tokens: list[int]) -> Tensor:
        if not tokens:
            raise ValueError("nonempty input required")
        self.model.eval()
        for token in tokens:
            if not 1 <= token < self.model.config.vocab_size:
                raise ValueError("invalid session token")
            self.prefix.append(token)
            x = torch.tensor([self.prefix], device=self.memory.device)
            logits, proposed, summary = self.model(x, self.memory)
            self.tokens_read += 1
            self.forward_tokens += len(self.prefix)
            self.last_logits = logits[0, -1].clone()
            if len(self.prefix) == self.model.config.context:
                self.commit(proposed, summary)
        assert self.last_logits is not None
        return self.last_logits.clone()

    @torch.no_grad()
    def flush(self) -> None:
        if self.prefix:
            x = torch.tensor([self.prefix], device=self.memory.device)
            _, proposed, summary = self.model(x, self.memory)
            self.forward_tokens += len(self.prefix)
            self.commit(proposed, summary)

    @torch.no_grad()
    def generate(self, question_tokens: list[int], budget: int = 16) -> list[int]:
        if budget <= 0:
            raise ValueError("positive generation budget required")
        logits = self.consume(question_tokens)
        result = []
        for _ in range(budget):
            scores = logits.clone()
            scores[:2] = -torch.inf
            token = int(scores.argmax().item())
            result.append(token)
            if token == 2:
                break
            logits = self.consume([token])
        return result
