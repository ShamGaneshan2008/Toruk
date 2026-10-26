"""Bounded local text continuation behind the experimental chat page."""

import threading
import time
from pathlib import Path
from typing import Protocol

from toruk_lm.data import sha256_file
from toruk_lm.engine import load_checkpoint, load_model, setup
from toruk_lm.model import generate
from toruk_lm.tokenizer import ByteTokenizer

MAX_MESSAGE_BYTES = 1024
MAX_NEW_TOKENS = 64
MAX_MESSAGES = 20


class ChatError(Exception):
    """A readable request or local inference error."""


class ChatBackend(Protocol):
    label: str
    context: int

    def reply(self, messages: list[dict[str, str]], max_new_tokens: int) -> str: ...


class OrdinaryChatBackend:
    """Load only ordinary checkpoints and use Toruk's existing generator."""

    def __init__(self, checkpoint: Path) -> None:
        setup(23, 1)
        try:
            saved = load_checkpoint(checkpoint)
            self.model = load_model(checkpoint)
        except ValueError as error:
            if "unsupported checkpoint format" in str(error):
                raise ChatError(
                    "Unsupported checkpoint. Local chat accepts toruk-ordinary-v1 only; "
                    "controlled and recurrent checkpoints use a different inference path."
                ) from error
            raise ChatError(f"Checkpoint validation failed: {error}") from error
        except (OSError, RuntimeError) as error:
            raise ChatError(f"Cannot load checkpoint: {error}") from error
        self.tokenizer = ByteTokenizer()
        self.context = self.model.config.context
        self.label = f"{checkpoint.resolve()} · {saved['format']} · context {self.context}"
        self.model_id = f"toruk-ordinary-v1:{sha256_file(checkpoint)[:12]}"

    def reply(self, messages: list[dict[str, str]], max_new_tokens: int) -> str:
        return str(self.reply_with_metrics(messages, max_new_tokens)["answer"])

    def reply_with_metrics(
        self,
        messages: list[dict[str, str]],
        max_new_tokens: int,
        mode: str = "BASELINE",
        temperature: float = 0,
        top_p: float = 1,
    ) -> dict[str, object]:
        if mode != "BASELINE":
            raise ChatError(
                "TORUK mode requires a compatible recurrent selector and chat backbone."
            )
        if temperature != 0 or top_p != 1:
            raise ChatError("The ordinary demo checkpoint supports greedy decoding only.")
        # These are plain-text continuation cues. The model was not trained as a chat assistant.
        prompt = (
            "".join(
                f"{'User' if message['role'] == 'user' else 'Toruk'}: {message['content']}\n"
                for message in messages
            )
            + "Toruk:"
        )
        prefix = [self.tokenizer.bos_id, *self.tokenizer.encode(prompt)]
        started = time.perf_counter()
        ids = generate(self.model, prefix, max_new_tokens)
        return {
            "answer": self.tokenizer.decode(ids),
            "metrics": {
                "input_tokens": len(prefix),
                "selected_context_tokens": min(len(prefix), self.context),
                "output_tokens": len(ids),
                "total_tokens": min(len(prefix), self.context) + len(ids),
                "response_ms": round((time.perf_counter() - started) * 1000, 3),
                "backend": "Toruk",
                "model": self.model_id,
                "backbone": "Toruk ordinary byte LM",
                "mode": mode,
                "memory_used": False,
                "selected_message_ids": [f"m{index}" for index in range(len(messages))],
            },
        }


class ChatController:
    """One local transcript. A clear invalidates an in-flight reply."""

    def __init__(self, backend: ChatBackend | None, load_error: str | None = None) -> None:
        self.backend = backend
        self.load_error = load_error
        self.messages: list[dict[str, str]] = []
        self.busy = False
        self.revision = 0
        self.lock = threading.Lock()

    def status(self) -> dict[str, object]:
        with self.lock:
            return {
                "ready": self.backend is not None,
                "error": self.load_error,
                "model": self.backend.label if self.backend else "No supported checkpoint loaded",
                "context": self.backend.context if self.backend else None,
                "busy": self.busy,
                "messages": list(self.messages),
                "max_new_tokens": MAX_NEW_TOKENS,
            }

    def clear(self) -> dict[str, object]:
        with self.lock:
            self.revision += 1
            self.messages = []
        return self.status()

    def send(self, content: object, max_new_tokens: object) -> dict[str, object]:
        if not isinstance(content, str) or not content.strip():
            raise ChatError("Enter a message before sending.")
        content = content.strip()
        if len(content.encode("utf-8")) > MAX_MESSAGE_BYTES:
            raise ChatError(f"Message exceeds {MAX_MESSAGE_BYTES} UTF-8 bytes.")
        if type(max_new_tokens) is not int or not 1 <= max_new_tokens <= MAX_NEW_TOKENS:
            raise ChatError(f"Generation length must be 1–{MAX_NEW_TOKENS} tokens.")
        with self.lock:
            if self.backend is None:
                raise ChatError(self.load_error or "No supported checkpoint loaded.")
            if self.busy:
                raise ChatError("Generation is already in progress.")
            self.busy = True
            revision = self.revision
            proposed = [*self.messages, {"role": "user", "content": content}]
            proposed = proposed[-MAX_MESSAGES:]
            backend = self.backend
        try:
            answer = backend.reply(proposed, max_new_tokens)
        except Exception as error:
            with self.lock:
                self.busy = False
            raise ChatError(f"Generation failed: {error}") from error
        with self.lock:
            self.busy = False
            if self.revision != revision:
                raise ChatError("Chat was cleared while generation was running.")
            self.messages = [*proposed, {"role": "assistant", "content": answer}][-MAX_MESSAGES:]
        return self.status()
