"""Local browser-proxy-inference smoke with pinned backbone and M6 selector."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from smoke_vercel_local import free_port, read, wait_ready

from toruk_lm.chat_foundation import BACKBONE_ID, BACKBONE_REVISION

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/chat-foundation-001"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backbone-dir", type=Path, default=ARTIFACT / "backbone")
    parser.add_argument(
        "--selector-checkpoint",
        type=Path,
        default=ROOT / "artifacts/m6-validation-001/recurrent/checkpoint.pt",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Explicitly test pretrained chat without Toruk memory",
    )
    parser.add_argument("--chat-probes", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, choices=(32, 64), default=32)
    parser.add_argument("--output-dir", type=Path, default=ARTIFACT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
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
        (args.output_dir / "backend-integration.log").open("w", encoding="utf-8") as backend_log,
        (args.output_dir / "web-integration.log").open("w", encoding="utf-8") as web_log,
    ):
        backend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "toruk_lm.inference_server",
                "--backbone-dir",
                str(args.backbone_dir),
                *(
                    []
                    if args.baseline_only
                    else ["--selector-checkpoint", str(args.selector_checkpoint)]
                ),
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
            assert isinstance(status, dict) and status["ready"]
            assert status["model"] == f"{BACKBONE_ID}@{BACKBONE_REVISION[:12]}"
            assert status["memory_supported"] is (not args.baseline_only)
            fixture = json.loads((ROOT / "configs/chat-foundation-eval-v1.json").read_text())
            messages = next(
                case["messages"] for case in fixture["cases"] if case["id"] == "long_retrieval"
            )
            results = {}
            for mode in ("BASELINE",) if args.baseline_only else ("BASELINE", "TORUK"):
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
            if not args.baseline_only:
                assert results["TORUK"]["metrics"]["memory_used"] is True
                assert (
                    results["TORUK"]["metrics"]["selected_context_tokens"]
                    < results["BASELINE"]["metrics"]["selected_context_tokens"]
                )
            else:
                assert not results["BASELINE"]["metrics"]["memory_used"]
                code, unsupported = read(
                    base + "/api/chat",
                    {"messages": [{"role": "user", "content": "Hello"}], "mode": "TORUK"},
                )
                assert code == 400 and isinstance(unsupported, dict) and "answer" not in unsupported
            probes = {}
            if args.chat_probes:
                scenarios = {
                    "arithmetic": ["What is 2 + 3?"],
                    "follow_up": ["My name is Mira.", "What is my name?"],
                    "correction": [
                        "My favorite color is blue.",
                        "Correction: my favorite color is green. What is my favorite color now?",
                    ],
                }
                for name, prompts in scenarios.items():
                    history = []
                    turns = []
                    for prompt in prompts:
                        history.append({"role": "user", "content": prompt})
                        code, answer = read(
                            base + "/api/chat",
                            {
                                "messages": history,
                                "mode": "BASELINE",
                                "max_new_tokens": args.max_new_tokens,
                                "temperature": 0,
                                "top_p": 1,
                            },
                        )
                        turns.append(
                            {
                                "request": {"messages": list(history)},
                                "http_status": code,
                                "response": answer,
                            }
                        )
                        assert code == 200 and isinstance(answer, dict)
                        assert answer["metrics"]["model"] == status["model"]
                        history.append({"role": "assistant", "content": answer["answer"]})
                    probes[name] = turns
            backend.terminate()
            backend.wait(timeout=10)
            outage_code, outage = read(
                base + "/api/chat", {"messages": [{"role": "user", "content": "Hello"}]}
            )
            assert outage_code == 503 and isinstance(outage, dict) and "answer" not in outage
            report = {
                "page": "PASS",
                "mode": "BASELINE" if args.baseline_only else "BASELINE and TORUK",
                "model": status["model"],
                "probe_settings": {
                    "max_new_tokens": args.max_new_tokens,
                    "temperature": 0,
                    "top_p": 1,
                },
                "baseline": results["BASELINE"],
                "toruk": results.get("TORUK"),
                "probes": probes,
                "outage_status": outage_code,
            }
            (args.output_dir / "results.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(report, indent=2))
        finally:
            for process in (web, backend):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
