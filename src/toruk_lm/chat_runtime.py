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


STARTUP_ERRORS = {
    "CHECKPOINT_MISSING": "The selected demo model is missing. Start Toruk with the installed "
    "chat backbone; see the local chat guide.",
    "CHECKPOINT_INCOMPATIBLE": "Unsupported checkpoint. Start Toruk with a supported chat model; "
    "see the local chat guide.",
    "CHECKPOINT_INVALID": "The selected demo model cannot be read. Use the chat backbone "
    "described in the local chat guide.",
    "BACKBONE_MISSING": "Chat model files are missing. Complete the local model setup, "
    "then restart Toruk.",
    "BACKBONE_INVALID": "Chat model files failed verification. Restore the pinned model "
    "using the local chat guide, then restart Toruk.",
    "CHAT_DEPENDENCIES_MISSING": "Chat support is not installed. Complete the chat dependency "
    "setup in the local chat guide, then restart Toruk.",
    "BACKBONE_INCOMPATIBLE": "The installed chat model cannot load. Check the local chat setup "
    "and restart Toruk.",
    "SELECTOR_UNAVAILABLE": "The optional Toruk memory model cannot load. Start basic chat "
    "without the optional memory model, or restore the evaluated memory model.",
    "STARTUP_TIMEOUT": "Chat model startup timed out. Close unused applications and restart "
    "Toruk; check that the laptop has enough available memory.",
    "MODEL_LOAD_FAILED": "The chat model could not start. Check the backend terminal and "
    "the local chat guide, then restart Toruk.",
    "WORKER_STOPPED": "The chat model stopped. Restart the backend, then retry the connection.",
}


class ModelStartupError(ChatError):
    """Only the allowlisted code crosses the worker or public status boundary."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        self.code = code if code in STARTUP_ERRORS else "MODEL_LOAD_FAILED"
        super().__init__(detail or STARTUP_ERRORS[self.code])


class ChatBackend(Protocol):
    label: str
    context: int

    def reply(self, messages: list[dict[str, str]], max_new_tokens: int) -> str: ...


class OrdinaryChatBackend:
    """Load only ordinary checkpoints and use Toruk's existing generator."""

    def __init__(self, checkpoint: Path) -> None:
        setup(23, 1)
        if not checkpoint.is_file():
            raise ModelStartupError("CHECKPOINT_MISSING")
        try:
            saved = load_checkpoint(checkpoint)
            self.model = load_model(checkpoint)
        except ValueError as error:
            if "unsupported checkpoint format" in str(error):
                raise ModelStartupError(
                    "CHECKPOINT_INCOMPATIBLE",
                    "Unsupported checkpoint. Local chat accepts toruk-ordinary-v1 only; "
                    "controlled and recurrent checkpoints use a different inference path.",
                ) from error
            raise ModelStartupError(
                "CHECKPOINT_INVALID", f"Checkpoint validation failed: {error}"
            ) from error
        except (OSError, RuntimeError) as error:
            raise ModelStartupError(
                "CHECKPOINT_INVALID", f"Cannot load checkpoint: {error}"
            ) from error
        self.tokenizer = ByteTokenizer()
        self.context = self.model.config.context
        self.label = (
            f"Smoke fixture (not chat-trained) · {checkpoint.resolve()} · "
            f"{saved['format']} · context {self.context}"
        )
        self.model_id = f"toruk-ordinary-v1:{sha256_file(checkpoint)[:12]}"
        self.backbone_id = "Toruk ordinary byte LM (smoke fixture; not chat-trained)"

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
                "backbone": self.backbone_id,
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
