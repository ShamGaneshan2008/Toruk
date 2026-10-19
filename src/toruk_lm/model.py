"""Ordinary causal decoder. No recurrent memory or attention cache."""

from dataclasses import dataclass

import torch
from torch import Tensor, nn
from torch.nn import functional as F


@dataclass(frozen=True)
class ModelConfig:
    context: int = 64
    width: int = 32
    heads: int = 4
    layers: int = 2
    vocab_size: int = 259

    def __post_init__(self) -> None:
        if min(self.context, self.width, self.heads, self.layers) <= 0:
            raise ValueError("model dimensions must be positive")
        if self.width % self.heads:
            raise ValueError("width must be divisible by heads")
        if self.vocab_size != 259:
            raise ValueError("this version requires the fixed byte tokenizer")


class DecoderBlock(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.norm1 = nn.LayerNorm(config.width)
        self.attention = nn.MultiheadAttention(config.width, config.heads, batch_first=True)
        self.norm2 = nn.LayerNorm(config.width)
        self.ff = nn.Sequential(
            nn.Linear(config.width, 4 * config.width),
            nn.GELU(),
            nn.Linear(4 * config.width, config.width),
        )

    def forward(self, x: Tensor, causal: Tensor, padding: Tensor) -> Tensor:
        normalized = self.norm1(x)
        attended, _ = self.attention(
            normalized,
            normalized,
            normalized,
            attn_mask=causal,
            key_padding_mask=padding,
            need_weights=False,
        )
        x = x + attended
        return x + self.ff(self.norm2(x))


class CausalLM(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.width, padding_idx=0)
        self.position = nn.Embedding(config.context, config.width)
        self.blocks = nn.ModuleList(DecoderBlock(config) for _ in range(config.layers))
        self.norm = nn.LayerNorm(config.width)
        self.output = nn.Linear(config.width, config.vocab_size, bias=False)

    def forward(self, tokens: Tensor) -> Tensor:
        if tokens.ndim != 2 or not 0 < tokens.shape[1] <= self.config.context:
            raise ValueError("expected [batch, 1..context] tokens")
        padding = tokens.eq(0)
        if padding.all(dim=1).any():
            raise ValueError("fully padded examples are not supported")
        if (padding[:, :-1] & ~padding[:, 1:]).any():
            raise ValueError("only right padding is supported")
        length = tokens.shape[1]
        positions = torch.arange(length, device=tokens.device)
        x = self.embedding(tokens) + self.position(positions)
        causal = torch.ones(length, length, dtype=torch.bool, device=tokens.device).triu(1)
        for block in self.blocks:
            x = block(x, causal, padding)
        return self.output(self.norm(x))


def loss_sum(logits: Tensor, targets: Tensor) -> tuple[Tensor, int]:
    """Targets are shifted by the loader; -100 marks padding, including no-target positions."""
    count = int(targets.ne(-100).sum().item())
    if count == 0:
        raise ValueError("batch contains no valid targets")
    return F.cross_entropy(
        logits.reshape(-1, logits.shape[-1]),
        targets.reshape(-1),
        ignore_index=-100,
        reduction="sum",
    ), count


@torch.no_grad()
def generate(model: CausalLM, prefix: list[int], max_new_tokens: int) -> list[int]:
    if max_new_tokens < 0:
        raise ValueError("max_new_tokens must be nonnegative")
    model.eval()
    history = list(prefix) or [1]
    result: list[int] = []
    device = next(model.parameters()).device
    for _ in range(max_new_tokens):
        # The ordinary LM sees at most context tokens, including during evaluation.
        tokens = torch.tensor([history[-model.config.context :]], device=device)
        logits = model(tokens)[0, -1].clone()
        logits[:2] = -torch.inf  # PAD and BOS are not generated document text.
        token = int(logits.argmax().item())
        result.append(token)
        history.append(token)
        if token == 2:
            break
    return result
