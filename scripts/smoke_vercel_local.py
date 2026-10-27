"""Bounded end-to-end smoke for local Toruk inference and Vercel-style proxy."""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/vercel-feasibility-001"
TOKEN = "local-smoke-token"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def read(url: str, body: dict | None = None) -> tuple[int, dict | str]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        url,
        data,
        {"Content-Type": "application/json"} if data is not None else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode()
            return response.status, json.loads(
                raw
            ) if response.headers.get_content_type() == "application/json" else raw
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def wait_ready(url: str, process: subprocess.Popen) -> None:
    until = time.monotonic() + 60
    while time.monotonic() < until:
        if process.poll() is not None:
            raise RuntimeError(f"server exited: {process.returncode}")
        try:
            if read(url)[0] == 200:
                return
        except (OSError, TimeoutError):
            time.sleep(0.2)
    raise TimeoutError(f"server did not start: {url}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", default="artifacts/minimal-lm-demo-001/train/checkpoint.pt")
    parser.add_argument("--output-dir", type=Path, default=ARTIFACT)
    args = parser.parse_args()
    artifact = args.output_dir.resolve()
    artifact.mkdir(parents=True, exist_ok=True)
    backend_port, web_port = free_port(), free_port()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    backend_env = dict(os.environ, TORUK_BACKEND_TOKEN=TOKEN)
    web_env = dict(
        os.environ,
        TORUK_BACKEND_URL=f"http://127.0.0.1:{backend_port}",
        TORUK_BACKEND_TOKEN=TOKEN,
        PORT=str(web_port),
    )
    with (
        (artifact / "backend-smoke.log").open("w", encoding="utf-8") as backend_log,
        (artifact / "web-smoke.log").open("w", encoding="utf-8") as web_log,
    ):
        backend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "toruk_lm.inference_server",
                "--checkpoint",
                args.checkpoint,
                "--port",
                str(backend_port),
            ],
            cwd=ROOT,
            env=backend_env,
            stdout=backend_log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        web = subprocess.Popen(
            ["node", "web/vercel/scripts/dev.mjs"],
            cwd=ROOT,
            env=web_env,
            stdout=web_log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        try:
            base = f"http://127.0.0.1:{web_port}"
            wait_ready(f"http://127.0.0.1:{backend_port}/api/status", backend)
            wait_ready(base + "/api/status", web)
            page_status, page = read(base + "/")
            assert isinstance(page, str)
            assert page_status == 200 and "Experimental chat." in page
            status_code, status = read(base + "/api/status")
            assert isinstance(status, dict)
            assert status_code == 200 and status["ready"] and status["backend"] == "Toruk"
            code, result = read(
                base + "/api/chat",
                {"messages": [{"role": "user", "content": "Hello"}], "max_new_tokens": 16},
            )
            assert isinstance(result, dict)
            assert code == 200 and result["answer"]
            metrics = result["metrics"]
            assert metrics["backend"] == "Toruk" and metrics["output_tokens"] <= 16
            assert not metrics["memory_used"]
            comparison_path = artifact / f"comparison-smoke-{uuid4().hex[:12]}.json"
            comparison = subprocess.run(
                [
                    sys.executable,
                    "scripts/compare_chat_context.py",
                    "--plain-url",
                    f"http://127.0.0.1:{backend_port}",
                    "--output",
                    str(comparison_path),
                ],
                cwd=ROOT,
                env=backend_env,
                capture_output=True,
                text=True,
                timeout=45,
                check=True,
            )
            comparison_result = json.loads(comparison.stdout)
            assert comparison_result["status"] == "NO_VALID_CONTEXT_PATH"
            assert not comparison_result["efficiency_claim"]
            backend.terminate()
            backend.wait(timeout=10)
            outage_code, outage = read(
                base + "/api/chat",
                {"messages": [{"role": "user", "content": "Hello"}], "max_new_tokens": 16},
            )
            assert isinstance(outage, dict)
            assert outage_code == 503 and "error" in outage and "answer" not in outage
            print(
                json.dumps(
                    {
                        "page": "PASS",
                        "chat": "PASS",
                        "backend": status["model"],
                        "answer": result["answer"],
                        "metrics": metrics,
                        "comparison_status": comparison_result["status"],
                        "comparison_path": str(comparison_path.relative_to(ROOT)),
                        "plain_exact_accuracy": comparison_result["plain"]["exact_accuracy"],
                        "outage_status": outage_code,
                    },
                    indent=2,
                )
            )
        finally:
            for process in (web, backend):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
