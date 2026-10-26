"""Stateless, token-protected Toruk inference for a separate host."""

import argparse
import hmac
import json
import logging
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from toruk_lm.chat_foundation import PretrainedChatBackend, validate_sampling
from toruk_lm.chat_runtime import (
    MAX_MESSAGE_BYTES,
    MAX_MESSAGES,
    MAX_NEW_TOKENS,
    ChatError,
    OrdinaryChatBackend,
)

MAX_BODY_BYTES = 16_384
MAX_HISTORY_BYTES = 8_192


def validate_request(value: object) -> tuple[list[dict[str, str]], int, str, float, float]:
    if not isinstance(value, dict):
        raise ChatError("Expected a JSON object.")
    messages = value.get("messages")
    budget = value.get("max_new_tokens", 32)
    mode = value.get("mode", "BASELINE")
    if mode not in ("BASELINE", "TORUK"):
        raise ChatError("Mode must be BASELINE or TORUK.")
    temperature, top_p = validate_sampling(value.get("temperature", 0), value.get("top_p", 1))
    if not isinstance(messages, list) or not 1 <= len(messages) <= MAX_MESSAGES:
        raise ChatError(f"Provide 1–{MAX_MESSAGES} messages.")
    if type(budget) is not int or not 1 <= budget <= MAX_NEW_TOKENS:
        raise ChatError(f"Generation length must be 1–{MAX_NEW_TOKENS} tokens.")
    clean: list[dict[str, str]] = []
    total = 0
    for message in messages:
        if not isinstance(message, dict):
            raise ChatError("Each message must be an object.")
        role, content = message.get("role"), message.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str) or not content.strip():
            raise ChatError("Messages need a user/assistant role and nonempty text.")
        size = len(content.encode("utf-8"))
        if size > MAX_MESSAGE_BYTES:
            raise ChatError(f"Each message is limited to {MAX_MESSAGE_BYTES} UTF-8 bytes.")
        total += size
        clean.append({"role": role, "content": content})
    if total > MAX_HISTORY_BYTES:
        raise ChatError("Conversation is too long; start a new chat.")
    if clean[-1]["role"] != "user":
        raise ChatError("The final message must be from the user.")
    return clean, budget, mode, temperature, top_p


def make_handler(
    backend: OrdinaryChatBackend | PretrainedChatBackend | None,
    load_error: str | None,
    token: str,
) -> type[BaseHTTPRequestHandler]:
    gate = threading.Semaphore(1)
    public_error = (
        load_error
        if load_error and "Unsupported checkpoint" in load_error
        else "Toruk model is unavailable or incompatible; check inference-host logs."
    )

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: HTTPStatus, value: dict[str, Any]) -> None:
            body = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path != "/api/status":
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            self._json(
                HTTPStatus.OK,
                {
                    "ready": backend is not None,
                    "backend": "Toruk",
                    "model": backend.model_id if backend else "Unavailable",
                    "backbone": getattr(backend, "backbone_id", "Toruk ordinary byte LM")
                    if backend
                    else "Unavailable",
                    "context_tokens": backend.context if backend else None,
                    "memory_supported": bool(getattr(backend, "selector", None)),
                    "modes": ["BASELINE", "TORUK"]
                    if getattr(backend, "selector", None)
                    else ["BASELINE"],
                    "error": public_error if backend is None else None,
                },
            )

        def do_POST(self) -> None:
            if self.path != "/api/infer":
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            supplied = self.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied, f"Bearer {token}"):
                self._json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized."})
                return
            if backend is None:
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": public_error})
                return
            if not gate.acquire(blocking=False):
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Inference is busy; retry."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY_BYTES:
                    raise ChatError("Request body is too large or empty.")
                messages, budget, mode, temperature, top_p = validate_request(
                    json.loads(self.rfile.read(length))
                )
                result = backend.reply_with_metrics(
                    messages, budget, mode=mode, temperature=temperature, top_p=top_p
                )
                logging.info("inference %s", json.dumps(result["metrics"], sort_keys=True))
                self._json(HTTPStatus.OK, result)
            except ChatError as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            except ValueError as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            except Exception:
                logging.exception("Inference failed")
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Toruk inference failed."})
            finally:
                gate.release()

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Protected stateless Toruk inference service")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--checkpoint", type=Path)
    source.add_argument("--backbone-dir", type=Path)
    parser.add_argument("--selector-checkpoint", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    token = os.environ.get("TORUK_BACKEND_TOKEN", "")
    if not token:
        parser.error("TORUK_BACKEND_TOKEN must be set")
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    backend: OrdinaryChatBackend | PretrainedChatBackend | None
    try:
        if args.backbone_dir:
            backend = PretrainedChatBackend(args.backbone_dir, args.selector_checkpoint)
        else:
            if args.selector_checkpoint:
                parser.error("--selector-checkpoint requires --backbone-dir")
            backend = OrdinaryChatBackend(args.checkpoint)
        error = None
    except ChatError as failure:
        backend, error = None, str(failure)
        logging.error("Checkpoint load failed: %s", failure)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(backend, error, token))
    logging.info("Toruk inference listening on %s:%s", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping Toruk inference")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
