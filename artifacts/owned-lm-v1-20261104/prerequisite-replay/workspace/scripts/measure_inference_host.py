"""Measure a specified local backend; no download, upload, or deployment."""

import argparse
import concurrent.futures
import hashlib
import importlib.metadata
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import psutil
from smoke_vercel_local import free_port


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--checkpoint", type=Path)
    source.add_argument("--backbone-dir", type=Path)
    parser.add_argument("--selector-checkpoint", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    token = secrets.token_urlsafe(32)
    port = free_port()
    origin = f"http://127.0.0.1:{port}"
    command = [sys.executable, "-m", "toruk_lm.inference_server", "--port", str(port)]
    command += (
        ["--checkpoint", str(args.checkpoint)]
        if args.checkpoint
        else ["--backbone-dir", str(args.backbone_dir)]
    )
    if args.selector_checkpoint:
        command += ["--selector-checkpoint", str(args.selector_checkpoint)]

    def call(path: str, body: dict | None = None, secret: str = token) -> tuple[int, dict]:
        request = urllib.request.Request(
            origin + path,
            data=json.dumps(body).encode() if body else None,
            headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    peak = {"rss_sum_bytes": 0, "private_sum_bytes": 0}
    stop = threading.Event()
    started = time.perf_counter()
    with (args.output_dir / "backend.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command, env=dict(os.environ, TORUK_BACKEND_TOKEN=token), stdout=log, stderr=log
        )

        def sample() -> None:
            root = psutil.Process(process.pid)
            while not stop.wait(0.02):
                try:
                    infos = [p.memory_info() for p in [root, *root.children(recursive=True)]]
                    peak["rss_sum_bytes"] = max(peak["rss_sum_bytes"], sum(i.rss for i in infos))
                    peak["private_sum_bytes"] = max(
                        peak["private_sum_bytes"], sum(getattr(i, "private", 0) for i in infos)
                    )
                except psutil.Error:
                    pass

        sampler = threading.Thread(target=sample, daemon=True)
        sampler.start()
        try:
            while True:
                if process.poll() is not None or time.perf_counter() - started > 150:
                    raise RuntimeError("Backend startup failed")
                try:
                    _, status = call("/healthz")
                    if not status["ready"]:
                        raise RuntimeError("Requested model unavailable")
                    break
                except urllib.error.URLError:
                    time.sleep(0.1)
            startup = time.perf_counter() - started
            payload = {
                "messages": [{"role": "user", "content": "Hello"}],
                "max_new_tokens": 64,
                "mode": "BASELINE",
            }
            generations = []
            for _ in range(2):
                before = time.perf_counter()
                code, result = call("/api/infer", payload)
                assert code == 200 and result["metrics"]["model"] == status["model"]
                generations.append(
                    {"wall_seconds": time.perf_counter() - before, "metrics": result["metrics"]}
                )
            barrier = threading.Barrier(4)

            def overlap(_: int) -> int:
                barrier.wait(timeout=10)
                return call("/api/infer", payload)[0]

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                concurrent_statuses = list(pool.map(overlap, range(4)))
            assert call("/api/infer", payload, "wrong")[0] == 401
            dependencies = {}
            for name in ("torch", "transformers", "safetensors", "numpy", "sympy", "networkx"):
                dist = importlib.metadata.distribution(name)
                dependencies[name] = {
                    "version": dist.version,
                    "installed_bytes": sum(
                        dist.locate_file(f).stat().st_size
                        for f in dist.files or []
                        if dist.locate_file(f).is_file()
                    ),
                }
            result = {
                "scope": "local Windows only; exact requested model; not a host test",
                "status": status,
                "startup_seconds": startup,
                "startup_plus_first_response_seconds": startup + generations[0]["wall_seconds"],
                "generations": generations,
                "four_concurrent_http_statuses": concurrent_statuses,
                "peak_process_tree": peak,
                "dependencies": dependencies,
            }
            if args.checkpoint:
                result["checkpoint"] = {
                    "path": str(args.checkpoint),
                    "bytes": args.checkpoint.stat().st_size,
                    "sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
                }
            (args.output_dir / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result, indent=2))
        finally:
            stop.set()
            sampler.join(timeout=2)
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
