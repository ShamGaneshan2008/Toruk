"""Research-only segment delta byte LM. No pretrained model, selector or chat imports."""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import TypeAlias

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from toruk_lm.model import CausalLM, ModelConfig, loss_sum
from toruk_lm.owned_lm import OwnedConfig, OwnedMemoryLM
from toruk_lm.tokenizer import ByteTokenizer


@dataclass(frozen=True)
class DeltaConfig:
    context: int = 24
    width: int = 16
    heads: int = 4
    layers: int = 1
    rank: int = 8
    ff: int = 116
    slots: int = 4
    maximum: int = 192

    def __post_init__(self) -> None:
        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):
            raise ValueError("positive integer delta dimensions required")
        if (
            self.context > 32
            or self.width > 32
            or self.layers > 2
            or self.rank > 16
            or self.ff > 128
            or self.slots > 8
            or not self.context <= self.maximum <= 192
        ):
            raise ValueError("configuration exceeds small research budget")
        self.decoder()

    def decoder(self) -> ModelConfig:
        return ModelConfig(self.context, self.width, self.heads, self.layers)


def delta_update(state: Tensor, key: Tensor, value: Tensor, beta: Tensor) -> Tensor:
    """Functional rank-one delta rule; normalized key and beta in [0,1] expected."""
    error = value - torch.bmm(key[:, None], state).squeeze(1)
    return state + beta[:, :, None] * key[:, :, None] * error[:, None]


class SegmentDeltaLM(nn.Module):
    def __init__(self, config: DeltaConfig) -> None:
        super().__init__()
        self.delta_config = config
        self.config = config.decoder()
        self.backbone = CausalLM(self.config)
        for block in self.backbone.blocks:
            block.ff = nn.Sequential(
                nn.Linear(config.width, config.ff), nn.GELU(), nn.Linear(config.ff, config.width)
            )
        self.read_norms = nn.ModuleList(nn.LayerNorm(config.width) for _ in range(config.layers))
        self.queries = nn.ModuleList(
            nn.Linear(config.width, config.rank, bias=False) for _ in range(config.layers)
        )
        self.read_outputs = nn.ModuleList(
            nn.Linear(config.rank, config.width, bias=False) for _ in range(config.layers)
        )
        self.key = nn.Linear(config.width, config.rank)
        self.value = nn.Linear(config.width, config.rank)
        self.beta = nn.Linear(config.width, 1)

    def initial_state(self, batch: int = 1) -> Tensor:
        if type(batch) is not int or batch < 1:
            raise ValueError("positive integer batch required")
        rank = self.delta_config.rank
        return self.key.weight.new_zeros(batch, rank, rank)

    def forward(
        self, tokens: Tensor, state: Tensor, *, read: bool = True, write: bool = True
    ) -> tuple[Tensor, Tensor]:
        if tokens.dtype != torch.long or tokens.ndim != 2:
            raise ValueError("long [batch, length] token matrix required")
        if not 0 < tokens.shape[1] <= self.config.context or tokens.shape[0] < 1:
            raise ValueError("local context bound")
        if (tokens < 0).any() or (tokens >= 259).any():
            raise ValueError("invalid byte IDs")
        padding = tokens.eq(0)
        if padding.all(dim=1).any() or (padding[:, :-1] & ~padding[:, 1:]).any():
            raise ValueError("nonempty right-padded input required")
        rank = self.delta_config.rank
        if state.shape != (tokens.shape[0], rank, rank):
            raise ValueError("delta state shape mismatch")
        if state.dtype != self.key.weight.dtype or state.device != self.key.weight.device:
            raise ValueError("delta state dtype/device mismatch")
        if not torch.isfinite(state).all():
            raise ValueError("nonfinite delta state")
        length = tokens.shape[1]
        x = self.backbone.embedding(tokens)
        x = x + self.backbone.position(torch.arange(length, device=tokens.device))
        causal = torch.ones(length, length, dtype=torch.bool, device=tokens.device).triu(1)
        for block, norm, query, output in zip(
            self.backbone.blocks, self.read_norms, self.queries, self.read_outputs, strict=True
        ):
            x = block(x, causal, padding)
            if read:
                q = F.normalize(query(norm(x)), dim=-1, eps=1e-6)
                x = x + output(torch.bmm(q, state))
        hidden = self.backbone.norm(x)
        logits = self.backbone.output(hidden).masked_fill(padding[..., None], 0)
        updated = state
        if write:
            keys = F.normalize(self.key(hidden), dim=-1, eps=1e-6)
            values, strengths = self.value(hidden).tanh(), self.beta(hidden).sigmoid()
            for t in range(length):
                proposed = delta_update(updated, keys[:, t], values[:, t], strengths[:, t])
                updated = torch.where(padding[:, t, None, None], updated, proposed)
        return logits, updated


ResearchModel: TypeAlias = CausalLM | OwnedMemoryLM | SegmentDeltaLM
VARIANTS = ("ordinary", "recurrent", "delta")


def build_model(variant: str, config: DeltaConfig) -> ResearchModel:
    if variant not in VARIANTS:
        raise ValueError("unknown segment delta study variant")
    if variant == "delta":
        return SegmentDeltaLM(config)
    owned = OwnedConfig(
        context=config.context,
        width=config.width,
        heads=config.heads,
        layers=config.layers,
        slots=config.slots,
        max_document_tokens=config.maximum,
    )
    if variant == "ordinary":
        return CausalLM(owned.decoder(matched=True))
    return OwnedMemoryLM(owned.decoder(), config.slots)


def initial_state(model: ResearchModel) -> Tensor | None:
    return None if isinstance(model, CausalLM) else model.initial_state()


def segment(
    model: ResearchModel, tokens: Tensor, state: Tensor | None, *, read: bool, write: bool
) -> tuple[Tensor, Tensor | None]:
    if isinstance(model, CausalLM):
        return model(tokens), None
    if state is None:
        raise ValueError("state required")
    if isinstance(model, SegmentDeltaLM):
        return model(tokens, state, read=read, write=write)
    logits, updated, _ = model(tokens, state, read_memory=read, update_memory=write)
    return logits, updated


def document_loss(
    model: ResearchModel,
    text: str,
    *,
    maximum: int = 192,
    read: bool = True,
    write: bool = True,
    answer_start: int | None = None,
) -> tuple[Tensor, int, Tensor, int]:
    """One canonical next-token target per position, with full-document BPTT.

    answer_start is an evaluator-only target offset; never changes the forward
    path or training loss. No training caller passes an answer offset.
    """
    tokens = ByteTokenizer().encode(text, document=True)
    if len(tokens) - 1 > maximum:
        raise ValueError("document exceeds BPTT budget")
    state = initial_state(model)
    total = next(model.parameters()).new_zeros(())
    answer = total.clone()
    count = answer_count = 0
    for start in range(0, len(tokens) - 1, model.config.context):
        inputs = tokens[start : min(start + model.config.context, len(tokens) - 1)]
        targets = tokens[start + 1 : start + 1 + len(inputs)]
        logits, state = segment(model, torch.tensor([inputs]), state, read=read, write=write)
        summed, n = loss_sum(logits, torch.tensor([targets]))
        total, count = total + summed, count + n
        if answer_start is not None:
            offset = max(0, answer_start - start)
            if offset < len(inputs):
                part, size = loss_sum(logits[:, offset:], torch.tensor([targets[offset:]]))
                answer, answer_count = answer + part, answer_count + size
    return total, count, answer, answer_count


class ResearchSession:
    """Uncommitted segment state is never fed back into the same local prefix."""

    def __init__(self, model: ResearchModel, *, read: bool = True, write: bool = True) -> None:
        self.model, self.read, self.write = model, read, write
        self.reset()

    def reset(self) -> None:
        self.state = initial_state(self.model)
        self.prefix: list[int] = []
        self.last_logits: Tensor | None = None
        self.tokens_read = self.forward_positions = self.commits = 0
        self.read_positions = self.write_positions = 0

    def clone(self) -> "ResearchSession":
        other = ResearchSession(self.model, read=self.read, write=self.write)
        other.state = self.state.clone() if self.state is not None else None
        other.prefix = list(self.prefix)
        other.last_logits = self.last_logits.clone() if self.last_logits is not None else None
        for name in (
            "tokens_read",
            "forward_positions",
            "commits",
            "read_positions",
            "write_positions",
        ):
            setattr(other, name, getattr(self, name))
        return other

    @torch.no_grad()
    def consume(self, tokens: list[int]) -> Tensor:
        if not tokens or any(type(t) is not int or not 1 <= t < 259 for t in tokens):
            raise ValueError("nonempty valid token IDs required")
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
            if self.state is not None:
                self.read_positions += len(self.prefix) * self.model.config.layers * int(self.read)
                self.write_positions += len(self.prefix) * int(self.write)
            self.tokens_read += take
            if len(self.prefix) == self.model.config.context:
                self.state = updated
                self.prefix = []
                self.commits += 1
        assert self.last_logits is not None
        return self.last_logits.clone()

    def state_sha256(self) -> str:
        data = self.state.detach().numpy().tobytes() if self.state is not None else b"ordinary"
        data += json.dumps(self.prefix).encode()
        return hashlib.sha256(data).hexdigest()

    @torch.no_grad()
    def generate(self, prefix: str, budget: int = 8) -> dict[str, object]:
        if self.tokens_read:
            raise ValueError("reset before a new document")
        if not 1 <= budget <= 8 or len(prefix.encode()) + 1 > 192:
            raise ValueError("bounded generation input/budget required")
        input_ids = [1, *ByteTokenizer().encode(prefix)]
        logits = self.consume(input_ids)
        generated = []
        for index in range(budget):
            scores = logits.clone()
            scores[:2] = -torch.inf
            token = int(scores.argmax().item())
            generated.append(token)
            if token == 2:
                break
            if index + 1 < budget:
                logits = self.consume([token])
        return dict(
            input_ids=input_ids,
            generated_ids=generated,
            budget_exhausted=generated[-1] != 2,
            tokens_read=self.tokens_read,
            forward_positions=self.forward_positions,
            recomputed_positions=self.forward_positions - self.tokens_read,
            commits=self.commits,
            read_positions=self.read_positions,
            write_positions=self.write_positions,
            state_bytes=self.state.numel() * self.state.element_size()
            if self.state is not None
            else 0,
            local_buffer_bytes=len(self.prefix) * 8,
            state_sha256=self.state_sha256(),
        )
