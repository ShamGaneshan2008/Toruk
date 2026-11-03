"""Experimental neural slot memory and byte answer decoder; no symbolic fact parser."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn

from toruk_lm.data import sha256_file
from toruk_lm.tokenizer import ByteTokenizer

FORMAT = "toruk-integrated-lm-v1"
STATE_FORMAT = "toruk-integrated-state-v1"


@dataclass(frozen=True)
class IntegratedConfig:
    width: int = 48
    slots: int = 6
    local_tokens: int = 96
    record_tokens: int = 64
    query_tokens: int = 64
    max_records: int = 16
    answer_tokens: int = 12

    def __post_init__(self) -> None:
        if any(type(v) is not int or v <= 0 for v in asdict(self).values()):
            raise ValueError("positive integer dimensions required")
        if self.width > 128 or self.slots > 32 or max(asdict(self).values()) > 256:
            raise ValueError("configuration exceeds CPU prototype budget")


def text_tokens(text: str, limit: int) -> list[int]:
    tokens = ByteTokenizer().encode(text)
    if not tokens or len(tokens) > limit:
        raise ValueError("empty or over-budget text")
    return tokens


def padded(rows: list[list[int]]) -> Tensor:
    if not rows or any(not row for row in rows):
        raise ValueError("nonempty token rows required")
    result = torch.zeros(len(rows), max(map(len, rows)), dtype=torch.long)
    for index, row in enumerate(rows):
        result[index, : len(row)] = torch.tensor(row)
    return result


class IntegratedMemoryLM(nn.Module):
    """Learned addressing/overwrite, dense values, and autoregressive byte generation.

    Slot-address labels are an explicit training inductive bias. Runtime receives
    only text, never event labels, reference answers, entities, or parsed values.
    """

    def __init__(self, config: IntegratedConfig, variant: str = "integrated") -> None:
        super().__init__()
        if variant not in ("ordinary", "integrated"):
            raise ValueError("unknown integrated-study variant")
        self.config, self.variant = config, variant
        width = config.width
        self.embedding = nn.Embedding(259, width, padding_idx=0)
        self.encoder = nn.GRU(width, width, batch_first=True)
        self.write_address = nn.Linear(width, config.slots + 1)
        self.value = nn.Linear(width, width)
        self.read_address = nn.Linear(width, config.slots)
        self.initial = nn.Linear(3 * width, width)
        self.decoder = nn.GRU(2 * width, width, batch_first=True)
        self.output = nn.Linear(width, 259)

    def initial_state(self, batch: int = 1) -> Tensor:
        return self.embedding.weight.new_zeros(batch, self.config.slots, self.config.width)

    def check_state(self, state: Tensor, batch: int) -> None:
        if state.shape != (batch, self.config.slots, self.config.width):
            raise ValueError("state shape mismatch")
        if state.dtype != self.embedding.weight.dtype or not torch.isfinite(state).all():
            raise ValueError("state must contain finite model-dtype values")
        if state.device != self.embedding.weight.device:
            raise ValueError("state device mismatch")

    def encode(self, tokens: Tensor) -> Tensor:
        if tokens.ndim != 2 or tokens.shape[1] == 0 or tokens.shape[1] > 256:
            raise ValueError("bounded token matrix required")
        if tokens.dtype != torch.long or (tokens < 0).any() or (tokens >= 259).any():
            raise ValueError("invalid byte tokens")
        lengths = tokens.ne(0).sum(1)
        if (lengths == 0).any() or (tokens.eq(0)[:, :-1] & tokens.ne(0)[:, 1:]).any():
            raise ValueError("nonempty right-padded input required")
        hidden, _ = self.encoder(self.embedding(tokens))
        return hidden[torch.arange(len(tokens), device=tokens.device), lengths - 1]

    def update_vectors(self, state: Tensor, encoded: Tensor) -> tuple[Tensor, Tensor]:
        self.check_state(state, len(encoded))
        addresses = self.write_address(encoded)
        weights = addresses.softmax(-1)[:, : self.config.slots, None]
        proposed = self.value(encoded).tanh()[:, None]
        return (1 - weights) * state + weights * proposed, addresses

    def update(self, state: Tensor, record: Tensor) -> Tensor:
        if record.shape[1] > self.config.record_tokens:
            raise ValueError("record exceeds update budget")
        result, _ = self.update_vectors(state, self.encode(record))
        return result

    def prepare(self, local: Tensor, query: Tensor, state: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        if local.shape[1] > self.config.local_tokens or query.shape[1] > self.config.query_tokens:
            raise ValueError("local context or query exceeds budget")
        self.check_state(state, len(query))
        question = self.encode(query)
        address = self.read_address(question)
        read = torch.bmm(address.softmax(-1)[:, None], state).squeeze(1)
        if self.variant == "ordinary":
            read = torch.zeros_like(read)
        hidden = self.initial(torch.cat((self.encode(local), question, read), -1)).tanh()
        return hidden[None], read, address

    def decode(self, previous: Tensor, hidden: Tensor, read: Tensor) -> tuple[Tensor, Tensor]:
        inputs = torch.cat(
            (self.embedding(previous), read[:, None].expand(-1, previous.shape[1], -1)), -1
        )
        output, hidden = self.decoder(inputs, hidden)
        return self.output(output), hidden

    @torch.no_grad()
    def answer(self, local: list[int], query: list[int], state: Tensor) -> list[int]:
        self.eval()
        hidden, read, _ = self.prepare(padded([local]), padded([query]), state)
        previous = torch.tensor([[1]])
        result = []
        for _ in range(self.config.answer_tokens):
            logits, hidden = self.decode(previous, hidden, read)
            scores = logits[0, -1].clone()
            scores[:2] = -torch.inf
            token = int(scores.argmax().item())
            result.append(token)
            if token == 2:
                break
            previous = torch.tensor([[token]])
        return result


def load_integrated(path: Path) -> tuple[IntegratedMemoryLM, dict[str, Any]]:
    saved: dict[str, Any] = torch.load(path, map_location="cpu", weights_only=True)
    if (
        not isinstance(saved, dict)
        or saved.get("format") != FORMAT
        or saved.get("tokenizer") != ByteTokenizer.fingerprint
        or saved.get("boundary") != "optimizer-step"
    ):
        raise ValueError("incompatible integrated checkpoint")
    model = IntegratedMemoryLM(IntegratedConfig(**saved["config"]), saved["variant"])
    model.load_state_dict(saved["model"], strict=True)
    if any(not torch.isfinite(value).all() for value in model.state_dict().values()):
        raise ValueError("nonfinite integrated weights")
    model.eval()
    return model, saved


class IntegratedSession:
    """Fixed float32 state and bounded local bytes; questions never mutate history."""

    def __init__(self, model: IntegratedMemoryLM, checkpoint_sha256: str) -> None:
        self.model, self.checkpoint_sha256 = model, checkpoint_sha256
        self.state = model.initial_state()
        self.local = [1]
        self.records = self.input_tokens = self.update_tokens = 0

    @torch.no_grad()
    def consume(self, text: str) -> None:
        tokens = text_tokens(text, self.model.config.record_tokens)
        if self.model.variant == "integrated":
            self.state = self.model.update(self.state, padded([tokens]))
            self.update_tokens += len(tokens)
        self.local = (self.local + tokens + [13])[-self.model.config.local_tokens :]
        self.records += 1
        self.input_tokens += len(tokens) + 1

    def answer(self, question: str) -> list[int]:
        return self.model.answer(
            self.local, text_tokens(question, self.model.config.query_tokens), self.state
        )

    def save(self, path: Path) -> None:
        if path.exists():
            raise ValueError("use a fresh state path")
        torch.save(
            {
                "format": STATE_FORMAT,
                "checkpoint_sha256": self.checkpoint_sha256,
                "state": self.state,
                "local": self.local,
                "records": self.records,
                "input_tokens": self.input_tokens,
                "update_tokens": self.update_tokens,
            },
            path,
        )

    @classmethod
    def restore(
        cls, model: IntegratedMemoryLM, checkpoint: Path, path: Path
    ) -> "IntegratedSession":
        saved = torch.load(path, map_location="cpu", weights_only=True)
        if saved.get("format") != STATE_FORMAT or saved.get("checkpoint_sha256") != sha256_file(
            checkpoint
        ):
            raise ValueError("state/checkpoint identity mismatch")
        model.check_state(saved["state"], 1)
        local = saved["local"]
        if (
            not isinstance(local, list)
            or not 0 < len(local) <= model.config.local_tokens
            or any(type(t) is not int or not 1 <= t < 259 for t in local)
            or any(
                type(saved.get(k)) is not int or saved[k] < 0
                for k in ("records", "input_tokens", "update_tokens")
            )
        ):
            raise ValueError("invalid bounded session")
        session = cls(model, saved["checkpoint_sha256"])
        session.state, session.local = saved["state"], local
        session.records, session.input_tokens = saved["records"], saved["input_tokens"]
        session.update_tokens = saved["update_tokens"]
        return session
