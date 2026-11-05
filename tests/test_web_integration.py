"""Actual page handlers -> Node HTTP proxy -> Python HTTP inference contract.

The backend is explicitly a fixture, never a claimed neural model. Real-model
tests remain separately opt-in. CI installs Node so this path cannot silently skip.
"""

import json
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from toruk_lm.inference_server import make_handler

ROOT = Path(__file__).resolve().parents[1]


def test_page_proxy_python_http_contract(tmp_path):
    node = shutil.which("node")
    if node is None:
        if os.environ.get("CI"):
            pytest.fail("CI must install Node to run the web integration contract")
        pytest.skip("Node is required for the HTTP web integration contract")

    class FixtureBackend:
        ready = True
        model_id = "integration-fixture-not-a-language-model"
        backbone_id = "integration-fixture"
        context = 32
        calls = []

        def reply_with_metrics(self, messages, budget, mode, temperature, top_p):
            self.calls.append(messages)
            return {
                "answer": "Fixture response.",
                "metrics": {
                    "backend": "Toruk",
                    "model": self.model_id,
                    "backbone": self.backbone_id,
                    "mode": mode,
                    "memory_used": False,
                    "input_tokens": 20,
                    "selected_context_tokens": 20,
                    "output_tokens": 2,
                    "total_tokens": 22,
                    "response_ms": 0.0,
                    "selected_message_ids": [f"m{i}" for i in range(len(messages))],
                },
            }

    backend = FixtureBackend()
    token = secrets.token_urlsafe(24)
    http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(backend, None, token))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = os.environ.copy()
    # A local fixture uses HTTP; production/preview still require HTTPS in the proxy.
    for name in ("VERCEL_ENV", "TORUK_TEST_CONTEXT"):
        env.pop(name, None)
    env.update(
        TORUK_BACKEND_URL=f"http://127.0.0.1:{http.server_port}",
        TORUK_BACKEND_TOKEN=token,
        PORT=str(port),
        TORUK_LIVE_WEB_URL=f"http://127.0.0.1:{port}",
        TORUK_TEST_BACKBONE=backend.backbone_id,
    )
    process = None
    try:
        with (tmp_path / "node-proxy.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [node, "web/vercel/scripts/dev.mjs"],
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            deadline = time.monotonic() + 15
            while True:
                assert process.poll() is None, (tmp_path / "node-proxy.log").read_text(
                    encoding="utf-8"
                )
                try:
                    with urlopen(env["TORUK_LIVE_WEB_URL"] + "/api/status", timeout=1) as response:
                        status = json.load(response)
                    assert status["ready"] and status["model"] == backend.model_id
                    break
                except URLError:
                    if time.monotonic() > deadline:
                        pytest.fail("Node proxy failed to start")
                    time.sleep(0.05)
            # Direct invocation keeps node:test in one process for reliable timeout cleanup.
            result = subprocess.run(
                [node, "web/vercel/tests/ui.test.mjs"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=45,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert len(backend.calls) == 6
            assert backend.calls[2][1] == {"role": "assistant", "content": "Fixture response."}
            assert backend.calls[2][-1]["content"] == "What is my name?"
            assert backend.calls[4][-1]["content"].startswith("Correction:")
            assert len(backend.calls[5]) == 1, "New chat must clear prior turns"
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)
