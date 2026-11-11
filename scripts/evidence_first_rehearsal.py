"""One disposable 40-request runtime rehearsal; never a registered quality benchmark.

No held-out loaders, benchmark registration, accuracy scorer, model helpers or
retries. Existing research selectors, prompt, fit and controls remain unchanged.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil
from evidence_first_policy import IntegrityError, answer, make_view, reslice

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = ROOT / "artifacts/evidence-first-prototype"
CELLS = ("T-LM", "L-LM", "T-P", "L-P")
LIMITS = {
    "request_wall_seconds": 30,
    "stage_wall_seconds": 240,
    "stage_cpu_seconds": 480,
    "total_stage_wall_seconds": 1920,
    "total_stage_cpu_seconds": 3840,
    "memory_bytes": 6 * 1024**3,
    "disk_bytes": 3 * 1024**3,
    "monitor_sample_seconds": 0.05,
    "max_monitor_gap_seconds": 5,
}


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2)
        stream.write("\n")


def file_sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def disk_bytes(paths: list[Path]) -> int:
    return sum(p.stat().st_size for p in set(paths) if p.is_file())


def progress(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.01)


def read_progress(path: Path) -> dict:
    for attempt in range(5):
        try:
            return read(path) if path.exists() else {}
        except (PermissionError, json.JSONDecodeError):
            if attempt == 4:
                raise
            time.sleep(0.01)
    raise AssertionError("unreachable")


def synthetic_cases(tokenizer: Any) -> list[dict]:
    """Only four new disposable inputs, no gold answers or evaluator route labels."""

    def case(identifier: str, size: int, tail: list[str], question: str) -> dict:
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": "No assertion."}
            for i in range(size - 1)
        ]
        for i, text in enumerate(tail, size - 1 - len(tail)):
            messages[i] = {"role": "user", "content": text}
        messages.append({"role": "user", "content": question})
        return {"id": identifier, "disposable": True, "messages": messages}

    cases = [
        case(
            "runtime-asterweft",
            32,
            ['AsterWeft\'s splice key is "  ζ\twoven-8  ".'],
            "In turns m30: Copy AsterWeft's splice key.",
        ),
        case(
            "runtime-meridiangauge",
            48,
            ["This fragment has unsupported syntax.", 'MeridianGauge\'s seal is "fluted-62".'],
            "What is MeridianGauge's latch code?",
        ),
        case(
            "runtime-sablepress",
            32,
            [
                'SablePress\'s tension mark is "ochre-29".\nSablePress\'s jig is "notch-53".',
                'Correction: SablePress\'s tension mark is "umber-71".',
            ],
            "In turns m29,m30: What is SablePress's tension mark?",
        ),
    ]
    # Tokenizer-only padding targets the input cap, never semantic outcomes.
    # Both last-two-turn premises must survive even the lexical control's two
    # additional older turns. Fillers are unrelated well-formed declarations.
    from qwen_long_history import envelope

    synthesis = None
    for count in range(24):
        tail = [
            'CinderLoom\'s north reading is "17 23 31 47 59 61 73 89".',
            'TidalForge\'s south reading is "19 29 37 43 53 67 79 97".',
        ]
        for i in range(count):
            tail[i % 2] += f'\nCinderLoom\'s calibration note {i} is "stable sample segment".'
        candidate = case(
            "runtime-cinderloom",
            48,
            tail,
            "In turns m45,m46: Combine CinderLoom's north reading and TidalForge's south reading.",
        )
        count_ids = tokenizer.apply_chat_template(
            envelope(candidate["messages"], [0, 2, 45, 46, 47]),
            tokenize=True,
            add_generation_prompt=True,
            return_dict=False,
        )
        if len(count_ids) > 500:
            break
        synthesis = candidate
    if synthesis is None:
        raise ValueError("near-budget disposable input cannot fit")
    cases.append(synthesis)
    validate_cases(cases)
    return cases


def validate_cases(cases: list[dict]) -> None:
    if len(cases) != 4 or len({c["id"] for c in cases}) != 4:
        raise ValueError("exactly four distinct disposable cases required")
    for case in cases:
        if (
            not case.get("disposable")
            or set(case) != {"id", "disposable", "messages"}
            or len(case["messages"]) not in {32, 48}
        ):
            raise ValueError("disposable inputs only; no gold, split or route annotations")


def tracked_bindings() -> dict[str, str]:
    names = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "src"],
            cwd=ROOT,
        )
        .decode()
        .split("\0")
    )
    # Hash source/configuration only. Do not open any experiment case datasets.
    names += [
        "pyproject.toml",
        "configs/qwen-development-v5.json",
        "scripts/qwen_long_history.py",
        "scripts/qualify_answer_backbone.py",
        "scripts/evidence_first_policy.py",
        "scripts/evidence_first_rehearsal.py",
        "tests/test_evidence_first_policy.py",
        "tests/test_evidence_first_rehearsal.py",
    ]
    return {n: file_sha(ROOT / n) for n in sorted(set(names)) if n}


def verify_bindings(bindings: dict[str, str]) -> None:
    for name, expected in bindings.items():
        if file_sha(ROOT / name) != expected:
            raise IntegrityError("frozen source/input drift: " + name)


def prepare(run: Path) -> dict:
    started, cpu = time.perf_counter(), time.process_time()
    run.mkdir(parents=True, exist_ok=False)
    write(
        run / "started.json",
        {
            "utc": datetime.now(UTC).isoformat(),
            "purpose": "disposable resource sizing only",
            "git_status": subprocess.check_output(
                ["git", "status", "--short"], cwd=ROOT, text=True
            ),
            "heldout_records_read": 0,
            "registered_benchmark_cases_created": 0,
        },
    )
    config = read(ROOT / "configs/qwen-development-v5.json")
    directory = Path(config["backbone_directory"])
    checkpoint = Path(config["selector_checkpoint"])
    assets = [p for p in directory.iterdir() if p.is_file()] + [checkpoint]
    asset_hashes = {str(p): file_sha(p) for p in assets}
    # Verify the same pinned asset bytes as the completed v5 development run.
    old = read(ROOT / "artifacts/qwen-development-v5/attempt-002/registration.json")
    for name, expected in asset_hashes.items():
        known = old["bindings"].get(name)
        if (
            Path(name).name
            in {
                "model.safetensors",
                "tokenizer.json",
                "tokenizer_config.json",
                "config.json",
                "checkpoint.pt",
            }
            and known is None
        ):
            raise IntegrityError("missing pinned asset identity: " + name)
        if known is not None and expected != known:
            raise IntegrityError("pinned asset drift: " + name)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        directory, local_files_only=True, trust_remote_code=False
    )
    cases = synthetic_cases(tokenizer)
    write(run / "disposable-inputs.json", cases)
    protocol = run / "decision-at-freeze.md"
    protocol.write_bytes(
        (ROOT / "docs/research/evidence-first-answer-path-decision.md").read_bytes()
    )
    bindings = tracked_bindings()
    bindings[protocol.relative_to(ROOT).as_posix()] = file_sha(protocol)
    bindings[(run / "disposable-inputs.json").relative_to(ROOT).as_posix()] = file_sha(
        run / "disposable-inputs.json"
    )
    with zipfile.ZipFile(run / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in bindings:
            archive.write(ROOT / name, name)
    bindings[(run / "source.zip").relative_to(ROOT).as_posix()] = file_sha(run / "source.zip")
    freeze = {
        "schema": "evidence-first-disposable-runtime-v1",
        "quality_benchmark": False,
        "heldout_authorized": False,
        "production_change": False,
        "requests_planned": 40,
        "generation_retries": 0,
        "case_count": 4,
        "passes": 2,
        "limits": LIMITS,
        "order": [list(CELLS), list(reversed(CELLS))],
        "bindings": bindings,
        "assets": asset_hashes,
        "backbone_directory": str(directory),
        "selector_checkpoint": str(checkpoint),
        "seed": 81751,
        "torch_threads": 2,
        "max_input_tokens": 512,
        "max_output_tokens": 64,
        "dependencies": {
            n: importlib.metadata.version(n)
            for n in ("torch", "transformers", "tokenizers", "safetensors", "psutil")
        },
        "cap_rule": "R=ceil(2*max request); stage=ceil(2*max nonrequest)+49*R; total=8*stage+A",
        "interpretation": "resource sizing only; no scores, policy selection or savings claim",
    }
    write(run / "rehearsal-freeze.json", freeze)
    write(
        run / "preparation-cost.json",
        {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "memory": psutil.Process().memory_info()._asdict(),
            "disk_bytes": disk_bytes(assets + list(run.rglob("*"))),
            "new_generations": 0,
        },
    )
    return freeze


@contextlib.contextmanager
def phase(cost: dict, name: str):
    wall, cpu = time.perf_counter(), time.process_time()
    try:
        yield
    finally:
        cost[name + "_wall_seconds"] = cost.get(name + "_wall_seconds", 0) + (
            time.perf_counter() - wall
        )
        cost[name + "_cpu_seconds"] = cost.get(name + "_cpu_seconds", 0) + (
            time.process_time() - cpu
        )


def execute(
    messages: list[dict],
    selector: Any,
    backend: Any,
    proposed_policy: bool,
    diagnostics: dict | None = None,
) -> dict:
    """Integration seam used identically by T and L, without modifying selectors."""
    from qwen_long_history import envelope, fit_context

    wall, cpu = time.perf_counter(), time.process_time()
    cost: dict[str, float] = {}
    trace = diagnostics if diagnostics is not None else {}
    trace.update(
        {"cost": cost, "lm_calls": 0, "executed_input_tokens": 0, "executed_output_tokens": 0}
    )
    token_work: dict[str, int] = {"calls": 0, "positions": 0}

    def encode(prompt: list[dict]) -> Any:
        with phase(cost, "tokenization"):
            tokens = backend._tokens(prompt)
        token_work["calls"] += 1
        token_work["positions"] += tokens.numel()
        return tokens

    full = encode(envelope(messages, list(range(len(messages)))))
    with phase(cost, "selection"):
        selected = selector.select(messages)[0]
    with phase(cost, "fit_including_tokenization"):
        fitted, tokens, positions = fit_context(messages, selected, encode, 512)
    with phase(cost, "manifest"):
        view = make_view(messages, selected, fitted)
    prompt = envelope(messages, fitted)
    generated_ids = []
    raw_generated = None
    lm_calls = 0

    def generate() -> str:
        nonlocal generated_ids, raw_generated, lm_calls
        if lm_calls:
            raise IntegrityError("no LM retries or helpers")
        lm_calls += 1
        trace["lm_calls"] = lm_calls
        trace["executed_input_tokens"] = tokens.numel()
        trace["executed_output_tokens"] = None
        with phase(cost, "lm"):
            generated_ids, raw_generated = backend.generate_once(tokens)
        trace["executed_output_tokens"] = len(generated_ids)
        if len(generated_ids) > 64:
            raise IntegrityError("LM output bound")
        return raw_generated

    def count_payload(text: str) -> int:
        with phase(cost, "payload_tokenization"):
            return len(backend.tokenizer.encode(text, add_special_tokens=False))

    if proposed_policy:
        with phase(cost, "policy_including_lm"):
            result = answer(view, token_count=count_payload, generate=generate)
        payload = result.payload
        # No quality score: verify structural support/provenance only.
        if result.route == "copy" and (
            len(result.sources) != 1 or reslice(view, result.sources[0]) != payload
        ):
            raise IntegrityError("unsupported direct copy")
        if result.state == "absent-in-complete-scope" and (
            result.coverage is None or not result.coverage.complete
        ):
            raise IntegrityError("false absence certificate")
        policy = asdict(result)
    else:
        # Preserve the original LM prompt, fitting, generation and strip behavior.
        payload = generate().strip()
        policy = None
    for name in ("lm", "policy_including_lm", "payload_tokenization"):
        cost.setdefault(name + "_wall_seconds", 0.0)
        cost.setdefault(name + "_cpu_seconds", 0.0)
    for dimension in ("wall", "cpu"):
        # This residual includes routing, grammar parsing, coverage, copying and
        # validation. It is a subset of request cost, not another additive total.
        cost[f"parsing_policy_validation_{dimension}_seconds"] = max(
            0.0,
            cost[f"policy_including_lm_{dimension}_seconds"]
            - cost[f"lm_{dimension}_seconds"]
            - cost[f"payload_tokenization_{dimension}_seconds"],
        )
    row = {
        "payload": payload,
        "policy": policy,
        "manifest": asdict(view.manifest),
        "fitted_sources": [
            {
                "turn": s.interval.turn,
                "start": s.interval.start,
                "end": s.interval.end,
                "content": s.raw.decode(),
                "revision": s.revision,
                "sha256": s.turn_sha256,
            }
            for s in view.sources
        ],
        "selection_omissions": [t.id for t in view.manifest.turns if not t.selected],
        "fit_evictions": [t.id for t in view.manifest.turns if t.selected and not t.fitted],
        "selected_indices": selected,
        "fitted_indices": fitted,
        "prompt_messages": prompt,
        "prompt_ids": tokens[0].tolist(),
        "generated_ids": generated_ids,
        "raw_generated": raw_generated,
        "lm_calls": lm_calls,
        "executed_input_tokens": tokens.numel() if lm_calls else 0,
        "executed_output_tokens": len(generated_ids),
        "fitted_prompt_tokens": tokens.numel(),
        "full_tokenizer_positions": full.numel(),
        "fit_tokenizer_positions": positions,
        "tokenizer_work": token_work,
        "answer_bytes": len(payload.encode()),
        "answer_equivalent_bpe": count_payload(payload),
        "history_bytes": sum(len(m["content"].encode()) for m in messages),
        "fitted_bytes": sum(len(s.raw) for s in view.sources),
        "extra_history_lookups": 0,
        "selector_sha256": selector.sha256,
        "model": backend.model_id,
        "cost": cost,
        "memory_end": psutil.Process().memory_info()._asdict(),
    }
    row["cost"]["request_wall_seconds"] = time.perf_counter() - wall
    row["cost"]["request_cpu_seconds"] = time.process_time() - cpu
    return row


class Decoder:
    """Thin research adapter; no changes to the production backend."""

    def __init__(self, backend: Any):
        self.backend = backend
        self.tokenizer = backend.tokenizer
        self.model_id = backend.model_id

    def _tokens(self, prompt: list[dict]) -> Any:
        return self.backend._tokens(prompt)

    def generate_once(self, tokens: Any) -> tuple[list[int], str]:
        import torch

        with torch.inference_mode():
            output = self.backend.model.generate(
                input_ids=tokens,
                max_new_tokens=64,
                do_sample=False,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
                use_cache=True,
            )
        generated = output[0, tokens.shape[-1] :].tolist()
        return generated, str(self.tokenizer.decode(generated, skip_special_tokens=True))


def stable(row: dict) -> dict:
    return {
        k: row[k]
        for k in (
            "payload",
            "policy",
            "manifest",
            "fitted_sources",
            "selected_indices",
            "fitted_indices",
            "prompt_ids",
            "generated_ids",
            "lm_calls",
            "executed_input_tokens",
            "executed_output_tokens",
        )
    }


def worker(run: Path, cell: str, pass_number: int) -> None:
    start, cpu_start = time.perf_counter(), time.process_time()
    folder = run / f"pass-{pass_number}" / cell
    folder.mkdir(parents=True, exist_ok=False)
    status = folder / "progress.json"
    freeze = read(run / "rehearsal-freeze.json")
    verify_bindings(freeze["bindings"])
    for name, expected in freeze["assets"].items():
        if file_sha(Path(name)) != expected:
            raise IntegrityError("asset drift")
    for name, expected in freeze["dependencies"].items():
        if importlib.metadata.version(name) != expected:
            raise IntegrityError("dependency drift")
    cases = read(run / "disposable-inputs.json")
    validate_cases(cases)
    import torch
    from transformers import GenerationConfig

    from toruk_lm.chat_foundation import PretrainedChatBackend, TorukContextSelector
    from toruk_lm.context_selection import LexicalContextSelector
    from toruk_lm.relevance_gate import LexicalAdmissionSelector

    torch.manual_seed(81751)
    torch.use_deterministic_algorithms(True)
    backend = PretrainedChatBackend(Path(freeze["backbone_directory"]))
    backend.system_prompt = ""
    backend.model.generation_config = GenerationConfig(
        do_sample=False,
        num_beams=1,
        repetition_penalty=1.0,
        use_cache=True,
        eos_token_id=backend.tokenizer.eos_token_id,
        pad_token_id=backend.tokenizer.pad_token_id,
        max_new_tokens=64,
        temperature=1.0,
        top_p=1.0,
    )
    selector = (
        LexicalAdmissionSelector(TorukContextSelector(Path(freeze["selector_checkpoint"])))
        if cell.startswith("T-")
        else LexicalContextSelector("lexical-v1")
    )
    setup = {
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu_start,
    }
    write(folder / "setup.json", setup)
    adapter = Decoder(backend)
    sequence = cases + [cases[0]]
    first = None
    with (folder / "requests.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for i, case in enumerate(sequence):
            if psutil.Process().children(recursive=True):
                raise IntegrityError("unaccounted child helper in worker")
            tick, request_cpu = time.perf_counter(), time.process_time()
            progress(
                status,
                {
                    "active": True,
                    "index": i,
                    "case": case["id"],
                    "started": time.monotonic(),
                    "worker_cpu_started": request_cpu,
                },
            )
            diagnostics: dict = {}
            try:
                row = execute(case["messages"], selector, adapter, cell.endswith("-P"), diagnostics)
                row.update(
                    {
                        "index": i,
                        "case": case["id"],
                        "cell": cell,
                        "pass": pass_number,
                        "replay": i == 4,
                        "failure": None,
                    }
                )
                if i == 0:
                    first = stable(row)
                if i == 4 and stable(row) != first:
                    raise IntegrityError("deterministic replay disagreement")
                if case["id"] == "runtime-cinderloom":
                    if not 440 <= row["fitted_prompt_tokens"] <= 512:
                        raise IntegrityError("near-budget rehearsal workload not established")
                    if not {45, 46} <= set(row["fitted_indices"]) or row["lm_calls"] != 1:
                        raise IntegrityError("two-premise LM workload not exercised")
                if psutil.Process().children(recursive=True):
                    raise IntegrityError("unexpected child helper")
            except Exception as error:
                stream.write(
                    json.dumps(
                        {
                            "index": i,
                            "case": case["id"],
                            "cell": cell,
                            "pass": pass_number,
                            "replay": i == 4,
                            "failure": f"{type(error).__name__}: {error}",
                            "elapsed_wall_seconds": time.perf_counter() - tick,
                            "elapsed_cpu_seconds": time.process_time() - request_cpu,
                            **diagnostics,
                        }
                    )
                    + "\n"
                )
                stream.flush()
                raise
            stream.write(json.dumps(row, ensure_ascii=True) + "\n")
            stream.flush()
            progress(status, {"active": False, "index": i, "case": case["id"]})
    write(
        folder / "worker.json",
        {
            "pid": os.getpid(),
            "lifecycle_cpu_seconds": time.process_time(),
            "worker_wall_seconds": time.perf_counter() - start,
            "setup": setup,
            "requests": 5,
            "memory": psutil.Process().memory_info()._asdict(),
            "torch_threads": torch.get_num_threads(),
            "generation_config": backend.model.generation_config.to_dict(),
        },
    )


def snapshot(process: Any) -> tuple[int, int, dict[int, float]]:
    rss = private = 0
    usage = {}
    try:
        members = [process, *process.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0, 0, {}
    for member in members:
        try:
            memory = member.memory_info()
            times = member.cpu_times()
            rss += memory.rss
            private += getattr(memory, "private", getattr(memory, "data", memory.rss))
            usage[member.pid] = times.user + times.system
        except psutil.NoSuchProcess:
            pass
    return rss, private, usage


def terminate(child: Any) -> None:
    if child.poll() is None:
        with contextlib.suppress(psutil.NoSuchProcess):
            for descendant in psutil.Process(child.pid).children(recursive=True):
                with contextlib.suppress(psutil.NoSuchProcess):
                    descendant.kill()
        child.kill()


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def run_stage(
    run: Path, freeze: dict, cell: str, pass_number: int, prior_wall: float, prior_cpu: float
) -> dict:
    wall, cpu = time.perf_counter(), time.process_time()
    folder = run / f"pass-{pass_number}" / cell
    # Worker creates its own folder exactly once. Logs live outside that folder.
    log_path = run / f"pass-{pass_number}-{cell}.log"
    command = [
        sys.executable,
        str(Path(__file__)),
        "worker",
        "--run",
        str(run),
        "--cell",
        cell,
        "--pass-number",
        str(pass_number),
    ]
    usage: dict[int, float] = {}
    peak_rss = peak_private = peak_disk = peak_parent_private = 0
    per_request: dict[str, dict] = {}
    reason = None
    max_gap = 0.0
    previous_sample = time.perf_counter()
    active = {}
    assets = [Path(name) for name in freeze["assets"]]
    source_paths = [ROOT / name for name in freeze["bindings"]]
    with log_path.open("x", encoding="utf-8") as log:
        child = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        process = psutil.Process(child.pid)
        try:
            while child.poll() is None:
                now = time.perf_counter()
                max_gap = max(max_gap, now - previous_sample)
                previous_sample = now
                rss, private, used = snapshot(process)
                parent_memory = psutil.Process().memory_info()
                rss += parent_memory.rss
                parent_private = getattr(parent_memory, "private", parent_memory.rss)
                peak_parent_private = max(peak_parent_private, parent_private)
                private += parent_private
                peak_rss, peak_private = max(peak_rss, rss), max(peak_private, private)
                for pid, seconds in used.items():
                    usage[pid] = max(usage.get(pid, 0), seconds)
                disk = disk_bytes(assets + source_paths + list(run.rglob("*")))
                peak_disk = max(peak_disk, disk)
                elapsed = now - wall
                used_cpu = sum(usage.values()) + time.process_time() - cpu
                active = read_progress(folder / "progress.json")
                if active.get("active"):
                    entry = per_request.setdefault(
                        str(active["index"]),
                        {"peak_rss_bytes": 0, "peak_private_bytes": 0, "peak_disk_bytes": 0},
                    )
                    for key, value in (
                        ("peak_rss_bytes", rss),
                        ("peak_private_bytes", private),
                        ("peak_disk_bytes", disk),
                    ):
                        entry[key] = max(entry[key], value)
                if private > LIMITS["memory_bytes"]:
                    reason = "private memory cap"
                elif disk > LIMITS["disk_bytes"]:
                    reason = "disk cap"
                elif elapsed > LIMITS["stage_wall_seconds"]:
                    reason = "stage wall cap"
                elif used_cpu > LIMITS["stage_cpu_seconds"]:
                    reason = "stage CPU cap"
                elif prior_wall + elapsed > LIMITS["total_stage_wall_seconds"]:
                    reason = "total stage wall cap"
                elif prior_cpu + used_cpu > LIMITS["total_stage_cpu_seconds"]:
                    reason = "total stage CPU cap"
                elif max_gap > LIMITS["max_monitor_gap_seconds"]:
                    reason = "monitor gap"
                elif (
                    active.get("active")
                    and time.monotonic() - active["started"] > LIMITS["request_wall_seconds"]
                ):
                    reason = "request wall cap"
                if reason:
                    terminate(child)
                    break
                time.sleep(LIMITS["monitor_sample_seconds"])
        except Exception as error:
            reason = f"monitor failure: {type(error).__name__}: {error}"
        finally:
            terminate(child)
        code = child.wait()
    worker_path = folder / "worker.json"
    if worker_path.exists():
        final = read(worker_path)
        usage[final["pid"]] = max(usage.get(final["pid"], 0), final["lifecycle_cpu_seconds"])
        os_peak = final["memory"].get("peak_pagefile", 0) + peak_parent_private
        peak_private = max(peak_private, os_peak)
        if os_peak > LIMITS["memory_bytes"]:
            reason = "OS private-memory cap"
    elif code == 0:
        reason = "missing worker completion receipt"
    completed = rows(folder / "requests.jsonl")
    if code and reason is None:
        reason = "worker failed; see retained log and request receipt"
    if active.get("active") and not any(r["index"] == active["index"] for r in completed):
        interrupted = {
            "index": active["index"],
            "case": active["case"],
            "cell": cell,
            "pass": pass_number,
            "replay": active["index"] == 4,
            "failure": reason or "interrupted worker",
            "lm_calls": None,
            "executed_input_tokens": None,
            "executed_output_tokens": None,
            "elapsed_wall_seconds": time.monotonic() - active["started"],
            "worker_request_cpu_lower_bound_seconds": max(
                0.0, usage.get(child.pid, 0) - active["worker_cpu_started"]
            ),
            "accounting": "all lifecycle work charged; interrupted LM token count unavailable",
        }
        with (folder / "requests.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(interrupted) + "\n")
        completed.append(interrupted)
    if (len(completed) != 5 or any(r.get("failure") for r in completed)) and reason is None:
        reason = "incomplete/failed requests"
    # Fast policy routes may fit between monitor samples: retain end-of-request
    # memory plus a conservative whole-stage upper bound for their private/RSS peaks.
    for row in completed:
        if row.get("failure"):
            continue
        index = str(row["index"])
        memory = row["memory_end"]
        entry = per_request.setdefault(index, {})
        entry["end_private_bytes"] = memory.get("private", memory["rss"])
        entry["end_rss_bytes"] = memory["rss"]
        entry["private_peak_upper_bound_bytes"] = peak_private
        entry["disk_peak_upper_bound_bytes"] = peak_disk
        entry["sampled_during_request"] = "peak_private_bytes" in entry
    result = {
        "cell": cell,
        "pass": pass_number,
        "command": command,
        "returncode": code,
        "failure": reason,
        "wall_seconds": time.perf_counter() - wall,
        "cpu_seconds": sum(usage.values()) + time.process_time() - cpu,
        "controller_cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": peak_rss,
        "peak_private_bytes": peak_private,
        "peak_disk_bytes": peak_disk,
        "max_monitor_gap_seconds": max_gap,
        "requests_recorded": len(completed),
        "per_request_resources": per_request,
        "active_at_stop": active,
        "cpu_scope": "controller plus sampled child tree, reconciled with final worker CPU",
        "disk_scope": (
            "unique runtime assets, frozen sources/inputs and run files; excludes installed runtime"
        ),
    }
    if (
        result["wall_seconds"] > LIMITS["stage_wall_seconds"]
        or result["cpu_seconds"] > LIMITS["stage_cpu_seconds"]
    ):
        result["failure"] = result["failure"] or "final stage resource cap"
    write(run / f"pass-{pass_number}-{cell}-cost.json", result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "cell",
                    "pass",
                    "failure",
                    "requests_recorded",
                    "wall_seconds",
                    "cpu_seconds",
                )
            }
        ),
        flush=True,
    )
    return result


def check_pairs(run: Path) -> None:
    for pass_number in (1, 2):
        for selector in ("T", "L"):
            controls = rows(run / f"pass-{pass_number}" / f"{selector}-LM/requests.jsonl")
            proposed = rows(run / f"pass-{pass_number}" / f"{selector}-P/requests.jsonl")
            for control, candidate in zip(controls, proposed, strict=False):
                if control.get("failure") or candidate.get("failure"):
                    raise IntegrityError("failed matched request")
                for key in (
                    "case",
                    "manifest",
                    "fitted_sources",
                    "fitted_indices",
                    "prompt_ids",
                    "prompt_messages",
                    "selected_indices",
                ):
                    if control[key] != candidate[key]:
                        raise IntegrityError("matched evidence/prompt drift: " + key)
    for cell in CELLS:
        first = rows(run / "pass-1" / cell / "requests.jsonl")
        second = rows(run / "pass-2" / cell / "requests.jsonl")
        if first and second and [stable(r) for r in first] != [stable(r) for r in second]:
            raise IntegrityError("cross-pass disagreement")


def propose_caps(
    data: list[dict], stages: list[dict], shared_wall: float, shared_cpu: float
) -> dict:
    rw = math.ceil(2 * max(r["cost"]["request_wall_seconds"] for r in data))
    rc = math.ceil(2 * max(r["cost"]["request_cpu_seconds"] for r in data))
    residual_wall = max(
        s["wall_seconds"]
        - sum(
            r["cost"]["request_wall_seconds"]
            for r in data
            if r["cell"] == s["cell"] and r["pass"] == s["pass"]
        )
        for s in stages
    )
    residual_cpu = max(
        s["cpu_seconds"]
        - sum(
            r["cost"]["request_cpu_seconds"]
            for r in data
            if r["cell"] == s["cell"] and r["pass"] == s["pass"]
        )
        for s in stages
    )
    w = math.ceil(2 * residual_wall) + 49 * rw
    c = math.ceil(2 * residual_cpu) + 49 * rc
    aw, ac = math.ceil(2 * shared_wall * 48 / 4), math.ceil(2 * shared_cpu * 48 / 4)
    return {
        "request_wall_seconds": rw,
        "request_cpu_seconds": rc,
        "max_nonrequest_wall_seconds": residual_wall,
        "max_nonrequest_cpu_seconds": residual_cpu,
        "cell_pass_wall_seconds": w,
        "cell_pass_cpu_seconds": c,
        "shared_wall_seconds": aw,
        "shared_cpu_seconds": ac,
        "overall_wall_seconds": 8 * w + aw,
        "overall_cpu_seconds": 8 * c + ac,
        "memory_bytes": LIMITS["memory_bytes"],
        "disk_bytes": LIMITS["disk_bytes"],
        "status": "proposed only; no benchmark registration or quality/efficiency claim",
    }


def audit(
    run: Path, stages: list[dict], failure: str | None, lifetime_wall: float, controller_cpu: float
) -> dict:
    started, cpu = time.perf_counter(), time.process_time()
    freeze = read(run / "rehearsal-freeze.json")
    verify_bindings(freeze["bindings"])
    if failure is None:
        check_pairs(run)
    data = [
        r
        for n in (1, 2)
        for cell in CELLS
        for r in rows(run / f"pass-{n}" / cell / "requests.jsonl")
    ]
    complete = failure is None and len(data) == 40 and len(stages) == 8
    if complete and any(r.get("failure") for r in data):
        complete = False
        failure = "failed request"
    prep = read(run / "preparation-cost.json")
    audit_wall, audit_cpu = time.perf_counter() - started, time.process_time() - cpu
    stage_wall = sum(s["wall_seconds"] for s in stages)
    stage_cpu = sum(s["cpu_seconds"] for s in stages)
    # Controller is already included in stage CPU; add only its disjoint work.
    outside_cpu = max(0.0, controller_cpu - sum(s["controller_cpu_seconds"] for s in stages))
    shared_wall = max(0.0, lifetime_wall - stage_wall) + audit_wall
    shared_cpu = outside_cpu + audit_cpu
    caps = propose_caps(data, stages, shared_wall, shared_cpu) if complete else None
    disk_peak = max([prep["disk_bytes"], *[s["peak_disk_bytes"] for s in stages]])
    current_logs = disk_bytes(list(run.rglob("*")))
    projected_disk = disk_peak + 12 * current_logs
    if caps is not None:
        caps["projected_48_case_disk_bytes_conservative"] = projected_disk
        caps["fixed_memory_disk_fit"] = (
            projected_disk <= LIMITS["disk_bytes"]
            and max(s["peak_private_bytes"] for s in stages) <= LIMITS["memory_bytes"]
        )
    result = {
        "status": "COMPLETE" if complete else "STOPPED",
        "failure": failure,
        "interpretation": "disposable feasibility only; no accuracy scores or quality claim",
        "requests": len(data),
        "expected_requests": 40,
        "cold_workers": len(stages),
        "lm_calls": sum(r.get("lm_calls") or 0 for r in data),
        "executed_input_tokens": sum(r.get("executed_input_tokens") or 0 for r in data),
        "executed_output_tokens": sum(r.get("executed_output_tokens") or 0 for r in data),
        "requests_with_unknown_lm_accounting": sum(
            any(
                r.get(k) is None
                for k in ("lm_calls", "executed_input_tokens", "executed_output_tokens")
            )
            for r in data
        ),
        "nonoverlapping_cold_stage_wall_seconds": stage_wall,
        "nonoverlapping_cold_stage_cpu_seconds": stage_cpu,
        "shared_wall_seconds": shared_wall,
        "shared_cpu_seconds": shared_cpu,
        "total_wall_seconds": stage_wall + shared_wall,
        "total_cpu_seconds": stage_cpu + shared_cpu,
        "preparation": prep,
        "audit_wall_seconds": audit_wall,
        "audit_cpu_seconds": audit_cpu,
        "peak_private_bytes": max(
            [prep["memory"].get("peak_pagefile", 0), *[s["peak_private_bytes"] for s in stages]]
        ),
        "peak_disk_bytes": disk_peak,
        "proposed_caps": caps,
        "registered_cases_created": 0,
        "registered_requests": 0,
        "extra_history_lookups": 0,
        "new_training": False,
        "heldout_records_read": 0,
    }
    write(run / "summary.json", result)
    return result


def rehearse(run: Path) -> dict:
    # Include controller interpreter/import setup: process CPU is lifetime CPU;
    # approximate the pre-main wall interval from OS process creation time. Each
    # child cold stage has an independently measured monotonic launch boundary.
    start = time.perf_counter() - max(0.0, time.time() - psutil.Process().create_time())
    cpu_start = 0.0
    stages = []
    failure = None
    sleep_state = None
    try:
        if sys.platform == "win32":
            import ctypes

            sleep_state = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
            if not sleep_state:
                raise RuntimeError("sleep inhibition failed")
        freeze = prepare(run)
        for pass_number, order in enumerate(freeze["order"], 1):
            for cell in order:
                stage = run_stage(
                    run,
                    freeze,
                    cell,
                    pass_number,
                    sum(s["wall_seconds"] for s in stages),
                    sum(s["cpu_seconds"] for s in stages),
                )
                stages.append(stage)
                if stage["failure"]:
                    failure = stage["failure"]
                    break
                check_pairs(run)
            if failure:
                break
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
        if not (run / "rehearsal-freeze.json").exists():
            write(
                run / "preflight-failure.json",
                {
                    "failure": failure,
                    "wall_seconds": time.perf_counter() - start,
                    "cpu_seconds": time.process_time() - cpu_start,
                    "generations": 0,
                    "no_rerun_authorized": True,
                },
            )
            raise
    finally:
        if sleep_state:
            import ctypes

            ctypes.windll.kernel32.SetThreadExecutionState(sleep_state)
    return audit(run, stages, failure, time.perf_counter() - start, time.process_time() - cpu_start)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("rehearse", "worker"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--cell", choices=CELLS)
    parser.add_argument("--pass-number", type=int, choices=(1, 2))
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to(NAMESPACE.resolve()) or run == NAMESPACE.resolve():
        parser.error("use a new child directory of artifacts/evidence-first-prototype")
    if args.action == "worker":
        if args.cell is None or args.pass_number is None:
            parser.error("worker requires cell and pass")
        worker(run, args.cell, args.pass_number)
        return 0
    if run.exists():
        parser.error("single-use run directory already exists; no overwrite or rerun")
    result = rehearse(run)
    print(json.dumps(result, indent=2))
    return int(result["status"] != "COMPLETE")


if __name__ == "__main__":
    sys.exit(main())
