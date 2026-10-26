"""Local browser-proxy-inference smoke with pinned backbone and M6 selector."""

import json
import os
import subprocess
import sys
from pathlib import Path

from smoke_vercel_local import free_port, read, wait_ready

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/chat-foundation-001"


def main() -> None:
    backend_port, web_port = free_port(), free_port()
    token = "local-chat-foundation-smoke-token"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    backend_env = dict(os.environ, TORUK_BACKEND_TOKEN=token)
    web_env = dict(
        os.environ,
        TORUK_BACKEND_URL=f"http://127.0.0.1:{backend_port}",
        TORUK_BACKEND_TOKEN=token,
        PORT=str(web_port),
    )
    with (
        (ARTIFACT / "backend-integration.log").open("w", encoding="utf-8") as backend_log,
        (ARTIFACT / "web-integration.log").open("w", encoding="utf-8") as web_log,
    ):
        backend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "toruk_lm.inference_server",
                "--backbone-dir",
                "artifacts/chat-foundation-001/backbone",
                "--selector-checkpoint",
                "artifacts/m6-validation-001/recurrent/checkpoint.pt",
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
            page_code, page = read(base + "/")
            assert page_code == 200 and isinstance(page, str)
            assert "BASELINE: recent turns" in page and "TORUK: selected turns" in page
            _, status = read(base + "/api/status")
            assert isinstance(status, dict) and status["ready"] and status["memory_supported"]
            fixture = json.loads((ROOT / "configs/chat-foundation-eval-v1.json").read_text())
            messages = next(
                case["messages"] for case in fixture["cases"] if case["id"] == "long_retrieval"
            )
            results = {}
            for mode in ("BASELINE", "TORUK"):
                code, response = read(
                    base + "/api/chat",
                    {
                        "messages": messages,
                        "mode": mode,
                        "max_new_tokens": 16,
                        "temperature": 0,
                        "top_p": 1,
                    },
                )
                assert code == 200 and isinstance(response, dict)
                assert response["metrics"]["mode"] == mode
                assert response["metrics"]["backbone"] == status["backbone"]
                results[mode] = response
            assert results["TORUK"]["metrics"]["memory_used"] is True
            assert (
                results["TORUK"]["metrics"]["selected_context_tokens"]
                < results["BASELINE"]["metrics"]["selected_context_tokens"]
            )
            backend.terminate()
            backend.wait(timeout=10)
            outage_code, outage = read(
                base + "/api/chat", {"messages": [{"role": "user", "content": "Hello"}]}
            )
            assert outage_code == 503 and isinstance(outage, dict) and "answer" not in outage
            print(
                json.dumps(
                    {
                        "page": "PASS",
                        "model": status["model"],
                        "baseline": results["BASELINE"],
                        "toruk": results["TORUK"],
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
