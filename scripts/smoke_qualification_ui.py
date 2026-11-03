"""Run existing page-handler tests through the real local Qwen proxy."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from smoke_vercel_local import ROOT, free_port, wait_ready


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    backend_port, web_port = free_port(), free_port()
    backend_env = dict(os.environ, TORUK_BACKEND_TOKEN="qualification-local-test-token")
    web_env = dict(
        backend_env, TORUK_BACKEND_URL=f"http://127.0.0.1:{backend_port}", PORT=str(web_port)
    )
    test_env = dict(os.environ, TORUK_LIVE_WEB_URL=f"http://127.0.0.1:{web_port}")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    processes = []
    with (
        (args.output_dir / "backend.log").open("w", encoding="utf-8") as backend_log,
        (args.output_dir / "proxy.log").open("w", encoding="utf-8") as proxy_log,
    ):
        try:
            backend = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "toruk_lm.inference_server",
                    "--backbone-dir",
                    "artifacts/qwen-chat-001/backbone",
                    "--port",
                    str(backend_port),
                ],
                cwd=ROOT,
                env=backend_env,
                stdout=backend_log,
                stderr=subprocess.STDOUT,
                creationflags=flags,
            )
            processes.append(backend)
            web = subprocess.Popen(
                ["node", "web/vercel/scripts/dev.mjs"],
                cwd=ROOT,
                env=web_env,
                stdout=proxy_log,
                stderr=subprocess.STDOUT,
                creationflags=flags,
            )
            processes.append(web)
            wait_ready(f"http://127.0.0.1:{backend_port}/api/status", backend, timeout=60)
            wait_ready(f"http://127.0.0.1:{web_port}/api/status", web)
            completed = subprocess.run(
                ["node", "--test", "web/vercel/tests/ui.test.mjs"],
                cwd=ROOT,
                env=test_env,
                timeout=150,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            (args.output_dir / "page-handlers.log").write_text(
                completed.stdout + completed.stderr, encoding="utf-8"
            )
            print(completed.stdout + completed.stderr)
            return completed.returncode
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(main())
