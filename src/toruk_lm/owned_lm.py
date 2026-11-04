"""Toruk-owned experimental byte LM: direct recurrent state-to-token prediction."""

from dataclasses import asdict, dataclass
from typing import TypeAlias

import torch
from torch import Tensor

from toruk_lm.model import CausalLM, ModelConfig, loss_sum
from toruk_lm.recurrent import RecurrentLM
from toruk_lm.tokenizer import ByteTokenizer

FORMAT = "toruk-owned-next-token-v1"
VARIANTS = ("ordinary", "ordinary_matched", "memory_off", "memory_on")


@dataclass(frozen=True)
class OwnedConfig:
    context: int = 32
    width: int = 32
    heads: int = 4
    layers: int = 2
    slots: int = 4
    max_document_tokens: int = 384

    def __post_init__(self) -> None:
        if any(type(value) is not int or value <= 0 for value in asdict(self).values()):
            raise ValueError("owned LM dimensions must be positive integers")
        if self.context > 128 or self.width > 64 or self.layers > 3 or self.slots > 8:
            raise ValueError("owned LM exceeds bounded CPU model budget")
        if self.max_document_tokens > 512 or self.max_document_tokens < self.context:
            raise ValueError("owned LM document budget must be context..512")
        self.decoder()

    def decoder(self, *, matched: bool = False) -> ModelConfig:
        width, heads = self.width, self.heads
        if matched:

            def count(d: int) -> int:
                return 12 * self.layers * d * d + (520 + self.context + 13 * self.layers) * d

            extra = self.layers * (4 * width * width + 6 * width)
            extra += 4 * width * width + 2 * width + 2 * self.slots * width
            target = count(width) + extra
            width = min(range(4, 65, 2), key=lambda d: abs(count(d) - target))
            heads = 2
        return ModelConfig(self.context, width, heads, self.layers)


class OwnedMemoryLM(RecurrentLM):
    """Preserve the existing core's algebra; expose actual read/update removals.

    Full mode is numerically identical to RecurrentLM. No label or text-selection
    interface exists here: only token IDs and a bounded floating-point state.
    """

    def forward(
        self,
        tokens: Tensor,
        memory: Tensor,
        *,
        read_memory: bool = True,
        update_memory: bool = True,
    ) -> tuple[Tensor, Tensor, Tensor]:
        if tokens.dtype != torch.long or tokens.ndim != 2:
            raise ValueError("owned LM requires a long [batch, context] token matrix")
        if not 0 < tokens.shape[1] <= self.config.context:
            raise ValueError("owned LM context bound exceeded")
        if (tokens < 0).any() or (tokens >= 259).any():
            raise ValueError("invalid byte token")
        if memory.shape != (len(tokens), self.slots, self.config.width):
            raise ValueError("memory shape mismatch")
        if memory.dtype != self.slot_gate.dtype or memory.device != self.slot_gate.device:
            raise ValueError("memory dtype/device mismatch")
        if not torch.isfinite(memory).all():
            raise ValueError("nonfinite memory")
        padding = tokens.eq(0)
        if padding.all(dim=1).any() or (padding[:, :-1] & ~padding[:, 1:]).any():
            raise ValueError("nonempty right-padded tokens required")
        if read_memory and update_memory:
            return super().forward(tokens, memory)
        length = tokens.shape[1]
        x = self.backbone.embedding(tokens)
        x = x + self.backbone.position(torch.arange(length, device=tokens.device))
        causal = torch.ones(length, length, dtype=torch.bool, device=tokens.device).triu(1)
        for block, reader, norm in zip(
            self.backbone.blocks, self.readers, self.read_norms, strict=True
        ):
            x = block(x, causal, padding)
            if read_memory:
                read, _ = reader(norm(x), memory, memory, need_weights=False)
                x = x + read
        hidden = self.backbone.norm(x)
        logits = self.backbone.output(hidden).masked_fill(padding[..., None], 0)
        valid = (~padding)[..., None]
        summary = (hidden * valid).sum(1) / valid.sum(1).clamp_min(1)
        if not update_memory:
            return logits, memory, summary
        joined = torch.cat((summary[:, None].expand_as(memory), memory), -1)
        proposal = torch.tanh(self.proposal(joined) + self.slot_proposal)
        gate = torch.sigmoid(self.gate(joined) + self.slot_gate)
        return logits, (1 - gate) * memory + gate * proposal, summary


OwnedModel: TypeAlias = CausalLM | OwnedMemoryLM


def build_model(config: OwnedConfig, variant: str) -> OwnedModel:
    if variant not in VARIANTS:
        raise ValueError("unknown owned LM variant")
    if variant.startswith("ordinary"):
        return CausalLM(config.decoder(matched=variant == "ordinary_matched"))
    return OwnedMemoryLM(config.decoder(), config.slots)


def segment(
    model: OwnedModel, tokens: Tensor, state: Tensor | None, *, read: bool, write: bool
) -> tuple[Tensor, Tensor | None]:
    if isinstance(model, OwnedMemoryLM):
        if state is None:
            raise ValueError("recurrent state is required")
        if not read and not write:
            return model.backbone(tokens), state
        logits, updated, _ = model(tokens, state, read_memory=read, update_memory=write)
        return logits, updated
    return model(tokens), None


def document_loss(
    model: OwnedModel, text: str, *, read: bool, write: bool, maximum: int
) -> tuple[Tensor, int, int]:
    """Score each non-BOS target once; a new state is mandatory per document."""
    tokens = ByteTokenizer().encode(text, document=True)
    if len(tokens) - 1 > maximum:
        raise ValueError("document exceeds bounded BPTT budget")
    state = model.initial_state() if isinstance(model, OwnedMemoryLM) else None
    total: Tensor | None = None
    count = positions = 0
    for start in range(0, len(tokens) - 1, model.config.context):
        inputs = tokens[start : min(start + model.config.context, len(tokens) - 1)]
        targets = tokens[start + 1 : start + 1 + len(inputs)]
        logits, state = segment(model, torch.tensor([inputs]), state, read=read, write=write)
        summed, n = loss_sum(logits, torch.tensor([targets]))
        total = summed if total is None else total + summed
        count += n
        positions += len(inputs)
    assert total is not None
    return total, count, positions


class OwnedSession:
    """Explicit single-document state; no module-global or cross-document memory."""

    def __init__(self, model: OwnedModel, *, read: bool = True, write: bool = True) -> None:
        self.model, self.read, self.write = model, read, write
        self.reset()

    def reset(self) -> None:
        self.state = self.model.initial_state() if isinstance(self.model, OwnedMemoryLM) else None
        self.prefix: list[int] = []
        self.last_logits: Tensor | None = None
        self.tokens_read = self.forward_positions = self.commits = 0

    def clone(self) -> "OwnedSession":
        other = OwnedSession(self.model, read=self.read, write=self.write)
        other.state = self.state.clone() if self.state is not None else None
        other.prefix = list(self.prefix)
        other.last_logits = self.last_logits.clone() if self.last_logits is not None else None
        other.tokens_read, other.forward_positions, other.commits = (
            self.tokens_read,
            self.forward_positions,
            self.commits,
        )
        return other

    @torch.no_grad()
    def consume(self, tokens: list[int]) -> Tensor:
        if not tokens or any(type(t) is not int or not 1 <= t < 259 for t in tokens):
            raise ValueError("nonempty valid byte tokens required")
        self.model.eval()
        cursor = 0
        while cursor < len(tokens):
            take = min(self.model.config.context - len(self.prefix), len(tokens) - cursor)
            self.prefix.extend(tokens[cursor : cursor + take])
            cursor += take
            logits, updated = segment(
                self.model,
                torch.tensor([self.prefix]),
                self.state,
                read=self.read,
                write=self.write,
            )
            self.last_logits = logits[0, -1].clone()
            self.forward_positions += len(self.prefix)
            self.tokens_read += take
            if len(self.prefix) == self.model.config.context:
                self.state = updated
                self.prefix = []
                self.commits += int(isinstance(self.model, OwnedMemoryLM) and self.write)
        assert self.last_logits is not None
        return self.last_logits.clone()

    @torch.no_grad()
    def generate(self, prefix: str, budget: int = 16) -> dict[str, object]:
        if not 1 <= budget <= 32:
            raise ValueError("generation budget must be 1..32")
        if self.tokens_read:
            raise ValueError("reset session before a new document")
        if len(prefix.encode()) + 1 > 512:
            raise ValueError("generation prefix exceeds CPU smoke budget")
        logits = self.consume([1, *ByteTokenizer().encode(prefix)])
        generated = []
        for _ in range(budget):
            scores = logits.clone()
            scores[:2] = -torch.inf
            token = int(scores.argmax().item())
            generated.append(token)
            if token == 2:
                break
            logits = self.consume([token])
        return {
            "answer": ByteTokenizer().decode(generated),
            "generated_ids": generated,
            "input_tokens": len(ByteTokenizer().encode(prefix)) + 1,
            "forward_positions": self.forward_positions,
            "commits": self.commits,
            "allocated_state_bytes": self.state.numel() * self.state.element_size()
            if self.state is not None
            else 0,
            "budget_exhausted": generated[-1] != 2,
        }


if __name__ == "__main__":
    from toruk_lm.owned_training import main

    main()
