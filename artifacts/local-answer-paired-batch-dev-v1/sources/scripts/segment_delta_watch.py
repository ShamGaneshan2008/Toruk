"""Bounded offline process-tree watcher; retain partial evidence and never retry."""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psutil


def write(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def watch(
    command: list[str], directory: Path, root: Path, seconds: float, memory: int, disk: int
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=False)
    started, before = time.perf_counter(), time.process_time()
    usage: dict[int, float] = {}
    peak = peak_rss = peak_disk = 0
    failure = None
    previous = started
    with (directory / "output.log").open("x", encoding="utf-8") as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        process = psutil.Process(child.pid)
        with (directory / "resources.jsonl").open("x", encoding="utf-8") as trace:
            while child.poll() is None:
                now = time.perf_counter()
                private = rss = 0
                try:
                    members = [process, *process.children(recursive=True)]
                except psutil.NoSuchProcess:
                    # The process may exit between poll() and children(). Final
                    # worker lifetime CPU/OS memory below reconcile this boundary.
                    members = []
                for member in members:
                    try:
                        c = member.cpu_times()
                        usage[member.pid] = max(usage.get(member.pid, 0), c.user + c.system)
                        info = member.memory_info()
                        value = getattr(info, "private", None)
                        if value is None or value <= 0:
                            raise RuntimeError("private-memory observation unavailable")
                        private += value
                        rss += info.rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                size = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                peak, peak_rss, peak_disk = (
                    max(peak, private),
                    max(peak_rss, rss),
                    max(peak_disk, size),
                )
                sample = dict(
                    elapsed=now - started,
                    gap=now - previous,
                    private=private,
                    rss=rss,
                    cpu=sum(usage.values()) + time.process_time() - before,
                    disk=size,
                )
                trace.write(json.dumps(sample) + "\n")
                trace.flush()
                if now - previous > 5:
                    failure = "monitoring gap over five seconds"
                elif private > memory:
                    failure = "process-tree private-memory cap"
                elif size > disk:
                    failure = "disk cap"
                elif now - started > seconds or sample["cpu"] > seconds:
                    failure = "CPU/wall cap"
                previous = now
                if failure:
                    for member in reversed(members):
                        try:
                            member.kill()
                        except psutil.NoSuchProcess:
                            pass
                    break
                time.sleep(0.05)
        code = child.wait(timeout=10)
    final = directory / "worker.json"
    if final.exists():
        worker = json.loads(final.read_text(encoding="utf-8"))
        usage[worker["pid"]] = max(usage.get(worker["pid"], 0), worker["lifetime_cpu"])
        peak = max(peak, worker["os_peak_private"])
    elif code == 0:
        failure = failure or "worker cost receipt missing"
    wall = time.perf_counter() - started
    cpu = sum(usage.values()) + time.process_time() - before
    if wall > seconds or cpu > seconds or peak > memory:
        failure = failure or "final lifecycle resource cap"
    result = dict(
        command=command,
        returncode=code,
        failure=failure,
        wall=wall,
        cpu=cpu,
        peak_private=peak,
        peak_rss=peak_rss,
        peak_disk=peak_disk,
        controller_cpu=time.process_time() - before,
        pid_cpu=usage,
        status="PASS" if code == 0 and failure is None else "STOP",
    )
    write(directory / "cost.json", result)
    return result


def worker_receipt(directory: Path, started: float, setup: float) -> None:
    process = psutil.Process(os.getpid())
    info = process.memory_info()
    peak = getattr(info, "peak_pagefile", 0)
    if peak <= 0:
        raise RuntimeError("Windows OS peak private memory unavailable")
    c = process.cpu_times()
    write(
        directory / "worker.json",
        dict(
            pid=os.getpid(),
            lifetime_cpu=c.user + c.system,
            worker_wall=time.perf_counter() - started,
            cold_setup_wall=setup,
            os_peak_private=peak,
            memory=info._asdict(),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seconds", type=float, required=True)
    parser.add_argument("--memory", type=int, default=2 * 1024**3)
    parser.add_argument("--disk", type=int, default=128 * 1024**2)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    result = watch(command, args.directory, args.root, args.seconds, args.memory, args.disk)
    print(json.dumps(result))
    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
