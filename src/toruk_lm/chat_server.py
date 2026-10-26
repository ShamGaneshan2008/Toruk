"""Localhost-only HTTP shell for Toruk's ordinary checkpoint generator."""

import argparse
import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from toruk_lm.chat_runtime import ChatController, ChatError, OrdinaryChatBackend

MAX_REQUEST_BYTES = 4096
PAGE = Path(__file__).with_name("chat_ui.html")


def create_controller(checkpoint: Path) -> ChatController:
    try:
        return ChatController(OrdinaryChatBackend(checkpoint))
    except ChatError as error:
        logging.error("Checkpoint load failed: %s", error)
        return ChatController(None, str(error))


def make_handler(controller: ChatController) -> type[BaseHTTPRequestHandler]:
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
            if self.path == "/api/status":
                self._json(HTTPStatus.OK, controller.status())
            elif self.path == "/":
                body = PAGE.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(body)
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})

        def do_POST(self) -> None:
            if self.path not in ("/api/chat", "/api/clear"):
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= MAX_REQUEST_BYTES:
                    raise ChatError("Request is too large.")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ChatError("Expected a JSON object.")
                if self.path == "/api/clear":
                    self._json(HTTPStatus.OK, controller.clear())
                else:
                    self._json(
                        HTTPStatus.OK,
                        controller.send(data.get("message"), data.get("max_new_tokens", 32)),
                    )
            except (ValueError, json.JSONDecodeError) as error:
                self._json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid request: {error}"})
            except ChatError as error:
                status = (
                    HTTPStatus.SERVICE_UNAVAILABLE
                    if not controller.status()["ready"]
                    else HTTPStatus.BAD_REQUEST
                )
                self._json(status, {"error": str(error)})

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimental Toruk local chat page")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    controller = create_controller(args.checkpoint)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(controller))
    logging.info("Toruk local chat at http://127.0.0.1:%s", args.port)
    logging.info("Model: %s", controller.status()["model"])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping local chat")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
