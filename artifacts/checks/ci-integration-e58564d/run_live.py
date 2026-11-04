"""Temporary local full-stack integration check; always stop owned processes."""

import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

import psutil


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_ready(url, processes, token=None):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if any(p.poll() is not None for p in processes):
            raise RuntimeError("owned test service exited before readiness")
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            with urlopen(Request(url, headers=headers), timeout=2) as response:
                if json.load(response).get("ready"):
                    return
        except (OSError, ValueError):
            pass
        time.sleep(.2)
    raise TimeoutError("local test stack did not become ready")


def main():
    output = Path(__file__).parent
    backend_port, web_port = free_port(), free_port()
    env = os.environ.copy()
    env.pop("VERCEL_ENV", None)
    env.update(TORUK_BACKEND_TOKEN=secrets.token_urlsafe(24),
               TORUK_BACKEND_URL=f"http://127.0.0.1:{backend_port}",
               TORUK_LIVE_WEB_URL=f"http://127.0.0.1:{web_port}",
               TORUK_TEST_CONTEXT="lexical-v2", PORT=str(web_port),
               PYTHONIOENCODING="utf-8")
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node unavailable")
    processes = []
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        with (output / "live-backend.log").open("w", encoding="utf-8") as log:
            processes.append(subprocess.Popen([
                sys.executable, "-m", "toruk_lm.inference_server", "--backbone-dir",
                "artifacts/qwen-chat-001/backbone", "--context-selector", "lexical-v2",
                "--host", "127.0.0.1", "--port", str(backend_port),
            ], env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags))
            wait_ready(env["TORUK_BACKEND_URL"] + "/api/status", processes, env["TORUK_BACKEND_TOKEN"])
            with (output / "live-web.log").open("w", encoding="utf-8") as web_log:
                processes.append(subprocess.Popen([node, "web/vercel/scripts/dev.mjs"],
                    env=env, stdout=web_log, stderr=subprocess.STDOUT, creationflags=flags))
                wait_ready(env["TORUK_LIVE_WEB_URL"] + "/api/status", processes)
                result = subprocess.run([node, "--test", "web/vercel/tests/*.test.mjs"],
                    env=env, timeout=150)
                return result.returncode
    finally:
        owned = []
        for process in processes:
            try:
                parent = psutil.Process(process.pid)
                owned.extend(parent.children(recursive=True))
                owned.append(parent)
            except psutil.NoSuchProcess:
                pass
        for process in reversed(owned):
            try:
                process.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(owned, timeout=5)
        for process in alive:
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(alive, timeout=5)


if __name__ == "__main__":
    sys.exit(main())
