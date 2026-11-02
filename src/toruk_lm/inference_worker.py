"""Killable model process: a deadline never leaves abandoned generation running."""

import multiprocessing as mp
import os
import threading
import time
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

from toruk_lm.chat_runtime import ChatError, ModelStartupError


def model_worker(
    pipe: Connection,
<<<<<<< HEAD
    source: Path,
    selector: Path | None,
    pretrained: bool,
    context_selector: str | None = None,
=======
    source: Path | str,
    selector: Path | None,
    pretrained: bool,
    ollama_digest: str | None,
>>>>>>> origin/main
) -> None:
    def watch_parent() -> None:
        parent = mp.parent_process()
        while parent is not None:
            if not parent.is_alive():
                os._exit(0)
            time.sleep(1)

    threading.Thread(target=watch_parent, daemon=True).start()
    from toruk_lm.chat_foundation import PretrainedChatBackend
    from toruk_lm.chat_runtime import OrdinaryChatBackend
    from toruk_lm.ollama_chat import OllamaChatBackend

    try:
<<<<<<< HEAD
        backend = (
            PretrainedChatBackend(source, selector, context_selector)
            if pretrained
            else OrdinaryChatBackend(source)
        )
    except Exception as error:
        code = error.code if isinstance(error, ModelStartupError) else "MODEL_LOAD_FAILED"
        # Never send exception text, paths, credentials or user content to the parent.
        pipe.send({"startup_error": code})
        pipe.close()
        return
    try:
=======
        backend: OllamaChatBackend | PretrainedChatBackend | OrdinaryChatBackend
        if ollama_digest is not None:
            backend = OllamaChatBackend(str(source), ollama_digest, selector)
        elif pretrained:
            assert isinstance(source, Path)
            backend = PretrainedChatBackend(source, selector)
        else:
            assert isinstance(source, Path)
            backend = OrdinaryChatBackend(source)
>>>>>>> origin/main
        pipe.send(
            {
                "model_id": backend.model_id,
                "backbone_id": getattr(backend, "backbone_id", "Toruk ordinary byte LM"),
                "context": backend.context,
                "selector": bool(getattr(backend, "selector", None)),
                "selector_id": getattr(backend, "selector_id", None),
                "selector_sha256": getattr(getattr(backend, "selector", None), "sha256", None),
                "selector_kind": getattr(getattr(backend, "selector", None), "kind", None),
                "backbone_revision": getattr(backend, "backbone_revision", None),
                "backbone_sha256": getattr(backend, "backbone_sha256", None),
                "backbone_digest": getattr(backend, "backbone_digest", None),
            }
        )
        while True:
            args, kwargs = pipe.recv()
            try:
                pipe.send((True, backend.reply_with_metrics(*args, **kwargs)))
            except ChatError:
                pipe.send((False, "Invalid or unsupported model request."))
            except Exception:
                pipe.send((False, "Model generation failed."))
    except (Exception, KeyboardInterrupt):
        # Exceptions may contain user text or private paths. Never print them.
        pipe.close()


class ProcessBackend:
    model_id: str
    backbone_id: str
    context: int
    selector: bool
    selector_sha256: str | None

    def __init__(
        self,
<<<<<<< HEAD
        source: Path,
        selector: Path | None,
        pretrained: bool,
        timeout: float = 45,
        context_selector: str | None = None,
=======
        source: Path | str,
        selector: Path | None,
        pretrained: bool,
        timeout: float = 45,
        ollama_digest: str | None = None,
>>>>>>> origin/main
    ) -> None:
        self.timeout = timeout
        context = mp.get_context("spawn")
        self.pipe, child = context.Pipe()
        self.process = context.Process(
<<<<<<< HEAD
            target=model_worker, args=(child, source, selector, pretrained, context_selector)
=======
            target=model_worker, args=(child, source, selector, pretrained, ollama_digest)
>>>>>>> origin/main
        )
        self.process.start()
        child.close()
        try:
<<<<<<< HEAD
            if not self.pipe.poll(120):
                raise ModelStartupError("STARTUP_TIMEOUT")
=======
            if not self.pipe.poll(180 if ollama_digest is not None else 120):
                raise ChatError("Model startup timed out.")
>>>>>>> origin/main
            metadata = self.pipe.recv()
            if "startup_error" in metadata:
                raise ModelStartupError(metadata["startup_error"])
            for name, value in metadata.items():
                setattr(self, name, value)
        except ModelStartupError:
            self.close()
            raise
        except (EOFError, OSError, ChatError) as error:
            self.close()
            raise ModelStartupError("MODEL_LOAD_FAILED") from error

    @property
    def ready(self) -> bool:
        return self.process.is_alive()

    def reply_with_metrics(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        if not self.ready:
            raise ChatError("Model worker unavailable; restart service.")
        try:
            self.pipe.send((args, kwargs))
            if not self.pipe.poll(self.timeout):
                self.close()
                raise TimeoutError("Generation deadline exceeded; restart service.")
            success, result = self.pipe.recv()
        except TimeoutError:
            raise
        except (EOFError, OSError) as error:
            self.close()
            raise ChatError("Model worker unavailable; restart service.") from error
        if not success:
            raise ChatError(result)
        return dict(result)

    def close(self) -> None:
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(timeout=2)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=2)
        self.pipe.close()
