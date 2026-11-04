"""Exercise failed model startup through the real inference service and web proxy."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from smoke_vercel_local import ROOT, free_port, read, wait_ready


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    results = []
    for option, code in (
        ("--checkpoint", "CHECKPOINT_MISSING"),
        ("--backbone-dir", "BACKBONE_MISSING"),
    ):
        backend_port, web_port = free_port(), free_port()
        token = "readiness-smoke-test-token"
        missing = args.output_dir / "private-missing-model-sentinel"
        backend_env = dict(os.environ, TORUK_BACKEND_TOKEN=token)
        web_env = dict(
            backend_env,
            TORUK_BACKEND_URL=f"http://127.0.0.1:{backend_port}",
            PORT=str(web_port),
        )
        with (
            (args.output_dir / f"{code}-backend.log").open("w", encoding="utf-8") as backend_log,
            (args.output_dir / f"{code}-web.log").open("w", encoding="utf-8") as web_log,
        ):
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            backend = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "toruk_lm.inference_server",
                    option,
                    str(missing),
                    "--port",
                    str(backend_port),
                ],
                env=backend_env,
                cwd=ROOT,
                stdout=backend_log,
                stderr=subprocess.STDOUT,
                creationflags=flags,
            )
            web = subprocess.Popen(
                ["node", "web/vercel/scripts/dev.mjs"],
                env=web_env,
                cwd=ROOT,
                stdout=web_log,
                stderr=subprocess.STDOUT,
                creationflags=flags,
            )
            try:
                origin = f"http://127.0.0.1:{backend_port}"
                proxy = f"http://127.0.0.1:{web_port}"
                wait_ready(origin + "/api/status", backend)
                wait_ready(proxy + "/api/status", web)
                _, status = read(proxy + "/api/status")
                assert isinstance(status, dict) and status["ready"] is False
                assert status["error_code"] == code
                _, alias = read(origin + "/status")
                assert isinstance(alias, dict) and alias["error_code"] == code
                assert read(origin + "/healthz")[0] == 503
                post_code, post = read(
                    proxy + "/api/chat", {"messages": [{"role": "user", "content": "Hello"}]}
                )
                assert post_code == 503 and isinstance(post, dict) and "answer" not in post
                assert post["error_code"] == code
                assert "sentinel" not in json.dumps(status) + json.dumps(post)
                assert token not in json.dumps(status) + json.dumps(post)
                results.append({"status": status, "chat_http_status": post_code})
            finally:
                for process in (web, backend):
                    process.terminate()
                    process.wait(timeout=10)
        log = (args.output_dir / f"{code}-backend.log").read_text(encoding="utf-8")
        assert f"CHAT DISABLED [{code}]" in log
        assert "Readiness service only" in log
        assert "inference listening" not in log
        assert "sentinel" not in log and token not in log
    (args.output_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
