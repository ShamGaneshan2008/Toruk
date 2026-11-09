"""Additive development-only v2 controller; deliberately no held-out entry point."""

import argparse
import ctypes
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/qwen-long-history-v2.json"
PROTOCOL = ROOT / "docs/research/qwen-long-history-v2-protocol.md"
TESTS = ROOT / "tests/test_qwen_long_history_v2.py"
ARMS = ("full", "recent", "lexical", "toruk")


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def append(path: Path, value: Any) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value) + "\n")
        stream.flush()


def cpu() -> float:
    value = psutil.Process().cpu_times()
    return float(value.user + value.system)


def clocks() -> dict[str, float]:
    unbiased = ctypes.c_ulonglong()
    ctypes.windll.kernelbase.QueryUnbiasedInterruptTimePrecise(ctypes.byref(unbiased))
    return {
        "utc_seconds": time.time(),
        "perf_seconds": time.perf_counter(),
        "awake_seconds": unbiased.value / 10_000_000,
    }


def elapsed(start: dict[str, float], end: dict[str, float]) -> float:
    return max(
        end["utc_seconds"] - start["utc_seconds"], end["perf_seconds"] - start["perf_seconds"]
    )


def interruption(
    start: dict[str, float], previous: dict[str, float], now: dict[str, float], config: dict
) -> str | None:
    if any(now[k] < previous[k] for k in now):
        return "clock moved backwards"
    if elapsed(previous, now) > config["max_monitor_gap_seconds"]:
        return "monitor gap; suspension or scheduling interruption"
    if (
        elapsed(start, now) - (now["awake_seconds"] - start["awake_seconds"])
        > config["max_suspended_gap_seconds"]
    ):
        return "elapsed/awake divergence; suspected suspension"
    return None


def propose_limits(stage: dict, rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("no measured requests")
    wall_max = max(r["request_wall_seconds"] for r in rows)
    cpu_max = max(r["request_cpu_seconds"] for r in rows)
    wall = math.ceil(max(120, 2 * (stage["wall_seconds"] + 20 * wall_max)) / 30) * 30
    used_cpu = math.ceil(max(240, 2 * (stage["cpu_seconds"] + 20 * cpu_max)) / 60) * 60
    if wall > 600 or used_cpu > 1200:
        raise ValueError("measured rehearsal exceeds preregistered proposal ceiling")
    return {
        "wall_seconds": wall,
        "cpu_seconds": used_cpu,
        "max_request_wall": wall_max,
        "max_request_cpu": cpu_max,
    }


def verify_bindings(bindings: dict[str, str]) -> None:
    for name, expected in bindings.items():
        if sha(Path(name)) != expected:
            raise ValueError("identity drift: " + name)


def paths_under(run: Path) -> Path:
    run = run.resolve()
    if not run.is_relative_to(ROOT / "artifacts/qwen-long-history-v2"):
        raise ValueError("output must be under this checkout's fresh v2 artifact namespace")
    return run


def legacy_module(source: Path) -> Any:
    sys.path.insert(0, str(source / "scripts"))
    return importlib.import_module("qwen_long_history")


def preserve_inventory(source: Path) -> dict[str, Any]:
    names = (
        subprocess.check_output(
            [
                "git",
                "-c",
                f"safe.directory={source.as_posix()}",
                "-C",
                str(source),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ]
        )
        .decode()
        .split("\0")
    )
    paths = {source / n for n in names if n and (source / n).is_file()}
    # Explicitly include ignored checkpoints/model assets consumed by the three studies.
    for folder in ("m6-successor-v1", "backbone-qualification-v1", "qwen-long-history-v1"):
        paths.update(p for p in (source / "artifacts" / folder).rglob("*") if p.is_file())
    bindings, unreadable = {}, []
    for p in sorted(paths):
        try:
            bindings[str(p)] = sha(p)
        except PermissionError as error:
            stat = p.stat()
            unreadable.append(
                {
                    "path": str(p),
                    "error": str(error),
                    "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                }
            )
    return {"bindings": bindings, "unreadable": unreadable}


def prepare(run: Path) -> None:
    config = read(CONFIG)
    source = Path(config["source_checkout"])
    oldrun = source / config["source_run"]
    oldreg = read(oldrun / "registration.json")
    for name, digest in oldreg["bindings"].items():
        if sha(source / name) != digest:
            raise ValueError("v1 binding drift: " + name)
    if (oldrun / "freeze.json").exists() or list(oldrun.glob("heldout-*")):
        raise ValueError("v1 held-out boundary requires investigation")
    run.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter(), cpu()
    inventory = preserve_inventory(source)
    write(run / "preservation-before.json", inventory)
    write(
        run / "starting-state.json",
        {
            "cwd": str(ROOT),
            "source_checkout": str(source),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "source_status": subprocess.check_output(
                [
                    "git",
                    "-c",
                    f"safe.directory={source.as_posix()}",
                    "-C",
                    str(source),
                    "status",
                    "--short",
                ],
                text=True,
            ),
            "utc": datetime.now(UTC).isoformat(),
        },
    )
    saved = read(oldrun / "development-toruk-cost.json")
    row = json.loads((oldrun / "development-toruk-answers.jsonl").read_text().splitlines()[0])
    write(
        run / "v1-status-and-diagnosis.json",
        {
            "status": "BLOCKED",
            "heldout_completed": {a: 0 for a in ARMS},
            "v1_registration_sha256": sha(oldrun / "registration.json"),
            "stage_cost_unchanged": saved,
            "completed_request": {
                k: row[k]
                for k in (
                    "request_cpu_seconds",
                    "request_wall_seconds",
                    "selector_cpu_seconds",
                    "selector_wall_seconds",
                    "generation_cpu_seconds",
                    "generation_wall_seconds",
                    "work",
                )
            },
            "last_progress": read(oldrun / "development-toruk-progress.json"),
            "power_events": read(
                source / "artifacts/qwen-long-history-v1/windows-power-events.json"
            ),
            "interpretation": (
                "Cold stage spans suspension and partial second request; not selector-call wall. "
                "No exact awake-time subtraction or v1 pass. Killed-worker CPU is sampled, "
                "potentially incomplete."
            ),
        },
    )
    legacy = legacy_module(source)
    dev, held = read(oldrun / "development.json"), read(oldrun / "heldout.json")
    prior = []
    prior_leakage = read(oldrun / "leakage.json")
    for name, digest in prior_leakage["source_files"].items():
        path = source / name
        if sha(path) != digest:
            raise ValueError("prior overlap input drift: " + name)
        data = (
            [json.loads(s) for s in path.read_text(encoding="utf-8-sig").splitlines()]
            if path.suffix == ".jsonl"
            else read(path)
        )
        prior.extend(legacy.records(data))
    prior, current_sources, skipped = legacy.previous_cases(oldrun)
    overlap = legacy.check_overlap(dev, held, prior)
    write(
        run / "overlap.json",
        {
            **overlap,
            "source_files": current_sources,
            "intentional_overlap": "Exact v1/v2 carryover, not independent replication",
            "skipped": skipped,
            "boundary": "Only the copied development file is reachable by rehearsal workers",
        },
    )
    write(
        run / "heldout-manifest.json",
        {
            "path_read_only": str(oldrun / "heldout.json"),
            "sha256": sha(oldrun / "heldout.json"),
            "cases": len(held),
            "known": sum(c["expected"] != "UNKNOWN" for c in held),
            "generated_answers": 0,
            "execution_authorized": False,
        },
    )
    rehearsal = run / "rehearsal"
    rehearsal.mkdir()
    with (rehearsal / "development.json").open("xb") as stream:
        stream.write((oldrun / "development.json").read_bytes())
    old_ids = read(oldrun / "full-prompt-ids.json")
    write(rehearsal / "full-prompt-ids.json", {c["id"]: old_ids[c["id"]] for c in dev})
    worker_config = oldreg["config"].copy()
    for name in ("backbone_directory", "selector_checkpoint"):
        worker_config[name] = str(source / worker_config[name])
    bindings = {str(source / name): digest for name, digest in oldreg["bindings"].items()}
    for p in (
        Path(__file__),
        CONFIG,
        PROTOCOL,
        TESTS,
        rehearsal / "development.json",
        rehearsal / "full-prompt-ids.json",
        run / "overlap.json",
        run / "heldout-manifest.json",
        run / "v1-status-and-diagnosis.json",
    ):
        bindings[str(p.resolve())] = sha(p)
    with zipfile.ZipFile(run / "v2-source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for p in (Path(__file__), CONFIG, PROTOCOL, TESTS):
            archive.writestr(p.relative_to(ROOT).as_posix(), p.read_bytes())
        archive.writestr("inherited-v1-source.zip", (oldrun / "source.zip").read_bytes())
    bindings[str(run / "v2-source.zip")] = sha(run / "v2-source.zip")
    registration = {
        **oldreg,
        "config": worker_config,
        "bindings": bindings,
        "schema": "qwen-long-history-v2-development-only",
        "v2_config": config,
        "heldout_execution_authorized": False,
        "prepared_utc": datetime.now(UTC).isoformat(),
    }
    write(rehearsal / "registration.json", registration)
    write(
        run / "preparation-cost.json",
        {
            "wall_seconds": time.perf_counter() - started[0],
            "cpu_seconds": cpu() - started[1],
            "scope": "Inventory, offline diagnosis, overlap and registration; shared overhead",
        },
    )
    print(
        json.dumps(
            {
                "prepared": str(run),
                "v1_status": "BLOCKED",
                "heldout_completed": 0,
                "bindings": len(bindings),
                "preserved_files": len(inventory["bindings"]),
                "unreadable_inventory_files": len(inventory["unreadable"]),
            }
        ),
        flush=True,
    )


def progress(path: Path, retry_log: Path, config: dict) -> dict:
    for attempt in range(config["monitor_read_attempts"]):
        try:
            return read(path) if path.exists() else {}
        except PermissionError as error:
            append(
                retry_log,
                {"utc": datetime.now(UTC).isoformat(), "attempt": attempt + 1, "error": str(error)},
            )
            if attempt + 1 == config["monitor_read_attempts"]:
                raise
            time.sleep(config["monitor_read_delay_seconds"])
    raise AssertionError("unreachable")


def sample_tree(child: subprocess.Popen, usage: dict, known: dict) -> tuple[int, int, int]:
    processes = []
    try:
        parent = psutil.Process(child.pid)
        processes = [parent, *parent.children(recursive=True)]
    except psutil.NoSuchProcess:
        pass
    rss, private, os_private = 0, 0, 0
    for p in processes:
        try:
            key = f"{p.pid}:{p.create_time()}"
            known[key] = p
            c, m = p.cpu_times(), p.memory_info()._asdict()
            usage[key] = max(usage.get(key, 0), c.user + c.system)
            rss += m["rss"]
            private += m.get("private", m["vms"])
            os_private += m.get("peak_pagefile", m.get("private", m["vms"]))
        except psutil.NoSuchProcess:
            pass
    return rss, private, os_private


def terminate(child: subprocess.Popen, known: dict) -> None:
    try:
        for p in psutil.Process(child.pid).children(recursive=True):
            known[f"{p.pid}:{p.create_time()}"] = p
    except psutil.NoSuchProcess:
        pass
    for p in reversed(list(known.values())):
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    if child.poll() is None:
        child.kill()
    child.wait(timeout=10)


def stage(run: Path, arm: str, totals: dict) -> dict:
    rehearsal = run / "rehearsal"
    reg = read(rehearsal / "registration.json")
    config = reg["v2_config"]
    start, before = clocks(), cpu()
    cost_path = rehearsal / f"development-{arm}-v2-cost.json"
    write(
        rehearsal / f"development-{arm}-v2-started.json",
        {
            "clocks": start,
            "arm": arm,
            "heldout": False,
            "registration_sha256": sha(rehearsal / "registration.json"),
        },
    )
    verify_bindings(reg["bindings"])
    command = [
        config["runtime_python"],
        "-B",
        "-X",
        "utf8",
        str(Path(config["source_checkout"]) / "scripts/qwen_long_history.py"),
        "worker",
        "--run",
        str(rehearsal),
        "--split",
        "development",
        "--arm",
        arm,
    ]
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PYTHONPATH": str(Path(config["source_checkout"]) / "src"),
    }
    usage: dict[str, float] = {}
    known: dict[str, Any] = {}
    failure, active = None, {}
    peak_rss = peak_private = peak_os_private = 0
    previous, last_heartbeat = clocks(), 0.0
    child = None
    with (rehearsal / f"development-{arm}.log").open("x", encoding="utf-8") as log:
        try:
            child = subprocess.Popen(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=ROOT,
                env=environment,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            while True:
                rss, private, os_private = sample_tree(child, usage, known)
                peak_rss = max(peak_rss, rss)
                peak_private, peak_os_private = (
                    max(peak_private, private),
                    max(peak_os_private, os_private),
                )
                now = clocks()
                active = progress(
                    rehearsal / f"development-{arm}-progress.json",
                    rehearsal / f"development-{arm}-read-retries.jsonl",
                    config,
                )
                wall = elapsed(start, now)
                used_cpu = sum(usage.values()) + cpu() - before
                failure = interruption(start, previous, now, config)
                if (
                    peak_private > config["memory_bytes"]
                    or peak_os_private > config["memory_bytes"]
                ):
                    failure = "private memory cap"
                elif (
                    wall > config["rehearsal_stage_wall_seconds"]
                    or used_cpu > config["rehearsal_stage_cpu_seconds"]
                ):
                    failure = "stage time cap"
                elif (
                    totals["wall_seconds"] + wall > config["rehearsal_total_wall_seconds"]
                    or totals["cpu_seconds"] + used_cpu > config["rehearsal_total_cpu_seconds"]
                ):
                    failure = "cumulative time cap"
                elif (
                    active.get("active")
                    and time.monotonic() - active["started"] > config["request_wall_seconds"]
                ):
                    failure = "request timeout"
                if now["perf_seconds"] - last_heartbeat >= config["heartbeat_seconds"] or failure:
                    disk = sum(p.stat().st_size for p in run.rglob("*") if p.is_file())
                    disk += sum(
                        (Path(config["source_checkout"]) / p).stat().st_size
                        for p in reg["model_files"]
                    )
                    if disk > config["disk_bytes"]:
                        failure = "disk cap"
                    append(
                        rehearsal / f"development-{arm}-heartbeats.jsonl",
                        {
                            "clocks": now,
                            "elapsed_seconds": wall,
                            "cpu_seconds": used_cpu,
                            "rss_bytes": rss,
                            "private_bytes": private,
                            "disk_bytes": disk,
                            "monitor_gap_seconds": elapsed(previous, now),
                            "active": active,
                            "failure": failure,
                        },
                    )
                    last_heartbeat = now["perf_seconds"]
                previous = now
                if failure or child.poll() is not None:
                    break
                time.sleep(config["sample_seconds"])
        except BaseException as error:
            failure = f"{type(error).__name__}: {error}"
        finally:
            if child is not None:
                terminate(child, known)
    end = clocks()
    worker_path = rehearsal / f"development-{arm}-worker.json"
    worker = read(worker_path) if worker_path.exists() else None
    if worker:
        keys = [k for k in usage if k.startswith(str(worker["pid"]) + ":")]
        key = keys[0] if keys else str(worker["pid"]) + ":final"
        usage[key] = max(usage.get(key, 0), worker["lifecycle_cpu_seconds"])
        peak_os_private = max(peak_os_private, worker["memory"].get("peak_pagefile", 0))
    if not worker and not failure:
        failure = "worker final telemetry missing"
    if child is not None and child.returncode and not failure:
        failure = "worker exited nonzero"
    if peak_os_private > config["memory_bytes"]:
        failure = "OS private memory cap"
    final_wall, final_cpu = elapsed(start, end), sum(usage.values()) + cpu() - before
    if not failure and (
        final_wall > config["rehearsal_stage_wall_seconds"]
        or final_cpu > config["rehearsal_stage_cpu_seconds"]
        or totals["wall_seconds"] + final_wall > config["rehearsal_total_wall_seconds"]
        or totals["cpu_seconds"] + final_cpu > config["rehearsal_total_cpu_seconds"]
    ):
        failure = "final stage/cumulative time cap"
    result = {
        "arm": arm,
        "command": command,
        "start": start,
        "end": end,
        "wall_seconds": final_wall,
        "cpu_seconds": final_cpu,
        "controller_cpu_seconds": cpu() - before,
        "cpu_by_process": usage,
        "peak_rss_bytes": peak_rss,
        "peak_private_bytes": peak_private,
        "peak_os_private_bytes": peak_os_private,
        "last_active_request": active,
        "worker_final_telemetry": worker is not None,
        "cpu_complete": worker is not None,
        "failure": failure,
        "returncode": child.returncode if child else None,
        "scope": (
            "stage controller + worker tree; sampled peaks; final worker CPU when present; "
            "no sleep subtraction"
        ),
    }
    write(cost_path, result)
    print(
        json.dumps({k: result[k] for k in ("arm", "wall_seconds", "cpu_seconds", "failure")}),
        flush=True,
    )
    return result


def rehearse(run: Path) -> None:
    lifecycle_start, lifecycle_cpu = clocks(), cpu()
    write(run / "rehearsal-started.json", {"utc": datetime.now(UTC).isoformat(), "heldout": False})
    reg = read(run / "rehearsal/registration.json")
    verify_bindings(reg["bindings"])
    acquired = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    write(
        run / "power-request-start.json",
        {"acquired": bool(acquired), "flags": "ES_CONTINUOUS|ES_SYSTEM_REQUIRED"},
    )
    totals = {"wall_seconds": 0.0, "cpu_seconds": 0.0}
    stages = []
    try:
        if not acquired:
            raise RuntimeError("power request failed; no worker authorized")
        for arm in reg["v2_config"]["rehearsal_order"]:
            result = stage(run, arm, totals)
            stages.append(result)
            for key in totals:
                totals[key] += result[key]
            if result["failure"]:
                break
    finally:
        restored = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        write(
            run / "power-request-end.json",
            {"restored": bool(restored), "utc": datetime.now(UTC).isoformat()},
        )
        write(
            run / "rehearsal-cost.json",
            {
                "totals": totals,
                "stages": stages,
                "complete": len(stages) == 4 and all(not s["failure"] for s in stages),
                "heldout_completed": 0,
            },
        )
        write(
            run / "rehearsal-lifecycle-cost.json",
            {
                "wall_seconds": elapsed(lifecycle_start, clocks()),
                "controller_cpu_seconds": cpu() - lifecycle_cpu,
                "stage_wall_sum": totals["wall_seconds"],
                "stage_cpu_sum": totals["cpu_seconds"],
                "note": (
                    "Lifecycle wall includes orchestration between stages; controller CPU overlaps "
                    "stage CPU. Do not add overlaps twice."
                ),
            },
        )


def freeze_proposal(run: Path) -> None:
    reg = read(run / "rehearsal/registration.json")
    verify_bindings(reg["bindings"])
    measured = read(run / "rehearsal-cost.json")
    if not measured["complete"]:
        raise ValueError("rehearsal incomplete; cannot freeze ready proposal")
    limits = {}
    for arm in ARMS:
        path = run / f"rehearsal/development-{arm}-answers.jsonl"
        rows = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]
        if len(rows) != 8 or sum(not r["is_replay"] for r in rows) != 7:
            raise ValueError("development completion mismatch")
        replay = rows[-1]
        if not replay["is_replay"] or any(
            replay[k] != rows[0][k]
            for k in ("answer", "score", "prompt_ids", "generated_ids", "selected_indices", "work")
        ):
            raise ValueError("deterministic replay failed")
        limits[arm] = propose_limits(next(s for s in measured["stages"] if s["arm"] == arm), rows)
    preservation = read(run / "preservation-before.json")
    verify_bindings(preservation["bindings"])
    for item in preservation["unreadable"]:
        stat = Path(item["path"]).stat()
        if stat.st_size != item["size"] or stat.st_mtime_ns != item["mtime_ns"]:
            raise ValueError("unreadable inventory file metadata changed: " + item["path"])
    write(
        run / "preservation-after.json",
        {
            "hash_checked_files": len(preservation["bindings"]),
            "all_readable_hashes_unchanged": True,
            "metadata_only_files": preservation["unreadable"],
            "limitation": "Permission-denied files checked by size/mtime only, not content hashes",
        },
    )
    outputs = {str(p): sha(p) for p in sorted(run.rglob("*")) if p.is_file()}
    write(
        run / "proposed-freeze.json",
        {
            "status": "PROPOSED_FROZEN; heldout NOT AUTHORIZED",
            "heldout_completed": {a: 0 for a in ARMS},
            "registered_inputs": reg["bindings"],
            "output_bindings": outputs,
            "heldout_stage_limits": limits,
            "cumulative_wall_seconds": measured["totals"]["wall_seconds"]
            + sum(v["wall_seconds"] for v in limits.values()),
            "cumulative_cpu_seconds": measured["totals"]["cpu_seconds"]
            + sum(v["cpu_seconds"] for v in limits.values()),
            "frozen_utc": datetime.now(UTC).isoformat(),
            "success_criteria": reg["config"]["criteria"],
            "scope": "Runtime-qualified proposal only; no heldout score or selector advantage",
        },
    )
    print(json.dumps({"proposal": str(run / "proposed-freeze.json"), "limits": limits}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "rehearse", "freeze-proposal"))
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = paths_under(args.run)
    {"prepare": prepare, "rehearse": rehearse, "freeze-proposal": freeze_proposal}[args.action](run)


if __name__ == "__main__":
    main()
