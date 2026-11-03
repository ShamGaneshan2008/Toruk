"""Local browser-proxy-inference smoke with pinned backbone and M6 selector."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from evaluate_chat_release_v2 import score_answer
from smoke_vercel_local import free_port, read, wait_ready

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/chat-foundation-001"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backbone-dir", type=Path, default=ARTIFACT / "backbone")
    parser.add_argument("--ollama-model")
    parser.add_argument("--ollama-digest")
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
    if bool(args.ollama_model) != bool(args.ollama_digest):
        parser.error("--ollama-model requires --ollama-digest and vice versa")
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
                *(
                    ["--ollama-model", args.ollama_model, "--ollama-digest", args.ollama_digest]
                    if args.ollama_model
                    else ["--backbone-dir", str(args.backbone_dir)]
                ),
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
            wait_ready(
                f"http://127.0.0.1:{backend_port}/api/status",
                backend,
                timeout=180 if args.ollama_model else 60,
            )
            wait_ready(base + "/api/status", web)
            page_code, page = read(base + "/")
            assert page_code == 200 and isinstance(page, str)
            assert "BASELINE: recent turns" in page and "TORUK: selected turns" in page
            _, status = read(base + "/api/status")
            assert isinstance(status, dict) and status["ready"]
            if args.ollama_model:
                assert status["model"] == f"ollama/{args.ollama_model}@{args.ollama_digest[:12]}"
                assert status["backbone"] == f"ollama/{args.ollama_model}"
            else:
                manifest = json.loads(
                    (args.backbone_dir / "toruk-backbone.json").read_text(encoding="utf-8")
                )
                assert status["model"] == f"{manifest['model']}@{manifest['revision'][:12]}"
                assert status["backbone"] == manifest["model"]
            assert status["memory_supported"] is (not args.baseline_only)
            if not args.baseline_only:
                selector_hash = hashlib.sha256(args.selector_checkpoint.read_bytes()).hexdigest()
                assert status["selector_sha256"] == selector_hash
                selector_kind = "toruk-m6-controlled-qa"
                if args.selector_checkpoint.suffix.lower() == ".json":
                    metadata = json.loads(args.selector_checkpoint.read_text(encoding="utf-8"))
                    selector_kind = (
                        "toruk-chat-selector-v2"
                        if metadata.get("protocol") == "chat-selector-v2"
                        else "toruk-chat-selector-v1"
                    )
                assert status["selector_kind"] == (selector_kind)
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
                if args.ollama_model:
                    assert response["metrics"]["selector_sha256"] == status["selector_sha256"]
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
            protocol = (ROOT / "configs/chat-qualification-v1.json").read_bytes()
            if args.chat_probes:
                scenarios = json.loads(protocol)["scenarios"]
                modes = ("BASELINE",) if args.baseline_only else ("BASELINE", "TORUK")
                for probe_mode in modes:
                    mode_probes = {}
                    for name, scenario in scenarios.items():
                        history = []
                        turns: list[dict[str, Any]] = []
                        for prompt in scenario["prompts"]:
                            history.append({"role": "user", "content": prompt})
                            request_body = {
                                "messages": list(history),
                                "mode": probe_mode,
                                "max_new_tokens": args.max_new_tokens,
                                "temperature": 0,
                                "top_p": 1,
                            }
                            code, answer = read(base + "/api/chat", request_body)
                            turns.append(
                                {"request": request_body, "http_status": code, "response": answer}
                            )
                            assert code == 200 and isinstance(answer, dict)
                            assert answer["metrics"]["model"] == status["model"]
                            history.append({"role": "assistant", "content": answer["answer"]})
                        turns[-1]["score"] = score_answer(turns[-1]["response"]["answer"], scenario)
                        mode_probes[name] = turns
                    if args.baseline_only:
                        probes = mode_probes
                    else:
                        probes[probe_mode] = mode_probes
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
                "status": status,
                "quality_claim": "Development probes; HTTP success does not establish quality.",
                "probe_protocol_sha256": hashlib.sha256(protocol).hexdigest(),
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
