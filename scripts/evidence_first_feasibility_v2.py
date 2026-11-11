"""Separate registered disposable 64-step stress check. Never the 48-case study."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import evidence_first_rehearsal as base
import psutil
from evidence_first_policy import IntegrityError, Provenance, make_view, reslice

ROOT = base.ROOT
OLD = ROOT / "artifacts/evidence-first-prototype/rehearsal-001"
RUN = ROOT / "artifacts/evidence-first-prototype/feasibility-v2"
PROTOCOL = ROOT / "docs/research/evidence-first-feasibility-v2-protocol.md"
LIMITS = {
    "request_wall_seconds": 60,
    "request_cpu_seconds": 120,
    "stage_wall_seconds": 240,
    "stage_cpu_seconds": 480,
    "total_stage_wall_seconds": 960,
    "total_stage_cpu_seconds": 1920,
    "memory_bytes": 6 * 1024**3,
    "disk_bytes": 3 * 1024**3,
    "sample_seconds": 0.05,
    "max_monitor_gap_seconds": 5,
}
ORDER = (("T", "L"), ("L", "T"))


def old_inventory() -> dict[str, str]:
    freeze = base.read(OLD / "rehearsal-freeze.json")
    base.verify_bindings(freeze["bindings"])
    seal = base.read(OLD / "output-sha256.json")
    protected = dict(freeze["bindings"])
    for name, expected in seal["files"].items():
        path = OLD / name
        if base.file_sha(path) != expected:
            raise IntegrityError("rehearsal-001 seal changed: " + name)
        protected[path.relative_to(ROOT).as_posix()] = expected
    for path in (
        OLD / "output-sha256.json",
        ROOT / "docs/research/evidence-first-answer-path-decision.md",
        ROOT / "docs/research/evidence-first-prototype-rehearsal.md",
    ):
        protected[path.relative_to(ROOT).as_posix()] = base.file_sha(path)
    return protected


def audit_old_rejections(tokenizer: Any) -> list[dict]:
    """Offline inspection only; never a callback into generation."""
    cases = {c["id"]: c for c in base.read(OLD / "disposable-inputs.json")}
    result = []
    for path in sorted(OLD.glob("pass-*/*/requests.jsonl")):
        for row in base.rows(path):
            policy = row["policy"]
            if not policy or policy["reason"] != "unsupported synthesis output":
                continue
            view = make_view(
                cases[row["case"]]["messages"], row["selected_indices"], row["fitted_indices"]
            )
            values = tuple(reslice(view, Provenance(**p)) for p in policy["sources"])
            decoded = tokenizer.decode(row["generated_ids"], skip_special_tokens=True)
            assert decoded == row["raw_generated"] == policy["generated"]
            allowed = {sep.join(values) for sep in ("; ", " and ", ", ", "\n")}
            complete = not policy["coverage"]["omitted"] and not policy["coverage"]["unparsed"]
            missing = [i for i, value in enumerate(values) if value not in decoded]
            result.append(
                {
                    "cell": row["cell"],
                    "pass": row["pass"],
                    "case": row["case"],
                    "source_spans": policy["sources"],
                    "premises": values,
                    "decoded": decoded,
                    "complete_parsed_coverage": complete,
                    "missing_premise_indices": missing,
                    "matches_only_one_premise": decoded in values,
                    "accepted_by_frozen_contract": decoded in allowed,
                    "implementation_defect_demonstrated": (decoded in allowed or not complete),
                    "cause": "contract: required premise omitted"
                    if missing
                    else "contract: outside exact ordered-combination forms",
                }
            )
    if len(result) != 4 or any(r["implementation_defect_demonstrated"] for r in result):
        raise IntegrityError("audit needs review; do not change policy automatically")
    return result


def stress_cases(tokenizer: Any) -> list[dict]:
    from qwen_long_history import envelope

    cases = []
    specifications = (
        (
            32,
            "QuartzSpindle",
            "weave code",
            "ultraviolet braid",
            "AmberCompass",
            "trace code",
            "moss arc",
        ),
        (
            48,
            "VioletCaliper",
            "edge note",
            "saffron rivet",
            "SilverBobbin",
            "notch note",
            "cobalt bead",
        ),
    )
    for size, left, field1, value1, right, field2, value2 in specifications:
        candidate = None
        for padding in range(24):
            messages = [
                {"role": "user" if i % 2 == 0 else "assistant", "content": "No assertion."}
                for i in range(size - 1)
            ]
            tail = [f'{left}\'s {field1} is "{value1}".', f'{right}\'s {field2} is "{value2}".']
            for i in range(padding):
                tail[i % 2] += f'\n{left}\'s calibration {i} is "steady patterned sample".'
            for i, text in enumerate(tail, size - 3):
                messages[i] = {"role": "user", "content": text}
            messages.append(
                {
                    "role": "user",
                    "content": f"In turns m{size - 3},m{size - 2}: Combine {left}'s {field1} "
                    f"and {right}'s {field2}.",
                }
            )
            ids = tokenizer.apply_chat_template(
                envelope(messages, [0, 2, size - 3, size - 2, size - 1]),
                tokenize=True,
                add_generation_prompt=True,
                return_dict=False,
            )
            if len(ids) > 500:
                break
            candidate = {
                "id": f"stress-{left.casefold()}",
                "disposable": True,
                "messages": messages,
            }
        if candidate is None:
            raise IntegrityError("stress sources cannot fit")
        cases.append(candidate)
    validate_cases(cases)
    return cases


def validate_cases(cases: list[dict]) -> None:
    if (
        len(cases) != 2
        or len({c["id"] for c in cases}) != 2
        or {len(c["messages"]) for c in cases} != {32, 48}
        or any(set(c) != {"id", "disposable", "messages"} or not c["disposable"] for c in cases)
    ):
        raise ValueError("only two new disposable 32/48-turn stress inputs, without annotations")


def register() -> dict:
    start = time.perf_counter() - max(0.0, time.time() - psutil.Process().create_time())
    RUN.mkdir(parents=True, exist_ok=False)
    protected = old_inventory()
    old = base.read(OLD / "rehearsal-freeze.json")
    for name, expected in old["assets"].items():
        if base.file_sha(Path(name)) != expected:
            raise IntegrityError("pinned runtime asset drift")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        old["backbone_directory"], local_files_only=True, trust_remote_code=False
    )
    base.write(RUN / "rehearsal-001-synthesis-audit.json", audit_old_rejections(tokenizer))
    base.write(RUN / "disposable-stress-inputs.json", stress_cases(tokenizer))
    names = [
        str(Path(__file__).relative_to(ROOT)),
        str(PROTOCOL.relative_to(ROOT)),
        "tests/test_evidence_first_feasibility_v2.py",
        "scripts/evidence_first_policy.py",
        "scripts/evidence_first_rehearsal.py",
    ]
    names += [n for n in old["bindings"] if n.startswith("src/")]
    names += ["scripts/qwen_long_history.py", "scripts/qualify_answer_backbone.py"]
    names += [
        p.relative_to(ROOT).as_posix()
        for p in (RUN / "rehearsal-001-synthesis-audit.json", RUN / "disposable-stress-inputs.json")
    ]
    bindings = {n: base.file_sha(ROOT / n) for n in sorted(set(names))}
    with zipfile.ZipFile(RUN / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in bindings:
            archive.write(ROOT / name, name)
    bindings[(RUN / "source.zip").relative_to(ROOT).as_posix()] = base.file_sha(RUN / "source.zip")
    record = {
        "schema": "disposable-feasibility-v2",
        "scope": "64-step resource stress only",
        "registered_48_case_study": False,
        "registered_benchmark_cases_created": 0,
        "heldout_authorized": False,
        "production_change": False,
        "new_training": False,
        "requests": 12,
        "cases": 2,
        "replays": 4,
        "cold_workers": 4,
        "order": ORDER,
        "limits": LIMITS,
        "old_proposal_assessment_only": {"wall": 14, "cpu": 27},
        "min_new_tokens": 64,
        "max_new_tokens": 64,
        "seed": 81751,
        "torch_threads": 2,
        "diagnostic_eos_suppression": True,
        "model_helpers": 0,
        "generation_retries": 0,
        "bindings": bindings,
        "protected": protected,
        "assets": old["assets"],
        "backbone_directory": old["backbone_directory"],
        "selector_checkpoint": old["selector_checkpoint"],
        "dependencies": {n: importlib.metadata.version(n) for n in old["dependencies"]},
        "cap_rule": (
            "twice pooled maxima; stage=S+49*R; overall=8*stage+max(old A,ceil(48*v2 shared))"
        ),
    }
    base.write(RUN / "registration.json", record)
    base.write(
        RUN / "preparation-cost.json",
        {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time(),
            "memory": psutil.Process().memory_info()._asdict(),
            "disk_bytes": base.disk_bytes([Path(n) for n in old["assets"]] + list(RUN.rglob("*"))),
            "new_generations": 0,
        },
    )
    print(
        json.dumps(
            {
                "registered": "disposable feasibility-v2 only",
                "requests": 12,
                "registered_benchmark_cases": 0,
            }
        )
    )
    return record


def verify() -> dict:
    record = base.read(RUN / "registration.json")
    if (
        record["schema"] != "disposable-feasibility-v2"
        or record["requests"] != 12
        or record["limits"] != LIMITS
        or record["order"] != [list(x) for x in ORDER]
    ):
        raise IntegrityError("stress registration drift")
    base.verify_bindings(record["bindings"])
    base.verify_bindings(record["protected"])
    return record


class StressDecoder(base.Decoder):
    """EOS suppression only; no token values or answer strings are forced."""

    def generate_once(self, tokens: Any) -> tuple[list[int], str]:
        import torch

        with torch.inference_mode():
            output = self.backend.model.generate(
                input_ids=tokens,
                min_new_tokens=64,
                max_new_tokens=64,
                do_sample=False,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
                use_cache=True,
            )
        ids = output[0, tokens.shape[-1] :].tolist()
        return ids, str(self.tokenizer.decode(ids, skip_special_tokens=True))


def stable(row: dict) -> dict:
    value = base.stable(row)
    value["backbone_work"] = row["backbone_work"]
    return value


def worker(selector_name: str, pass_number: int) -> None:
    start, cpu_start = time.perf_counter(), time.process_time()
    folder = RUN / f"pass-{pass_number}" / selector_name
    folder.mkdir(parents=True, exist_ok=False)
    record = verify()
    for name, expected in record["assets"].items():
        if base.file_sha(Path(name)) != expected:
            raise IntegrityError("asset drift")
    for name, expected in record["dependencies"].items():
        if importlib.metadata.version(name) != expected:
            raise IntegrityError("dependency drift")
    cases = base.read(RUN / "disposable-stress-inputs.json")
    validate_cases(cases)
    import torch
    from transformers import GenerationConfig

    from toruk_lm.chat_foundation import PretrainedChatBackend, TorukContextSelector
    from toruk_lm.context_selection import LexicalContextSelector
    from toruk_lm.relevance_gate import LexicalAdmissionSelector

    torch.manual_seed(81751)
    torch.use_deterministic_algorithms(True)
    backend = PretrainedChatBackend(Path(record["backbone_directory"]))
    backend.system_prompt = ""
    backend.model.generation_config = GenerationConfig(
        do_sample=False,
        num_beams=1,
        repetition_penalty=1.0,
        use_cache=True,
        min_new_tokens=64,
        max_new_tokens=64,
        temperature=1.0,
        top_p=1.0,
        eos_token_id=backend.tokenizer.eos_token_id,
        pad_token_id=backend.tokenizer.pad_token_id,
    )
    selector = (
        LexicalAdmissionSelector(TorukContextSelector(Path(record["selector_checkpoint"])))
        if selector_name == "T"
        else LexicalContextSelector("lexical-v1")
    )
    setup = {
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu_start,
    }
    base.write(folder / "setup.json", setup)
    work = {"positions": 0, "calls": 0}

    def hook(module, args, kwargs):
        tokens = kwargs.get("input_ids", args[0] if args else None)
        if tokens is not None:
            work["positions"] += tokens.numel()
            work["calls"] += 1

    backend.model.register_forward_pre_hook(hook, with_kwargs=True)
    first = None
    with (folder / "requests.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for index, case in enumerate(cases + [cases[0]]):
            progress = {
                "active": True,
                "index": index,
                "case": case["id"],
                "pid": os.getpid(),
                "started": time.monotonic(),
                "worker_cpu_started": time.process_time(),
            }
            base.progress(folder / "progress.json", progress)
            diagnostics: dict = {}
            row: dict = {}
            work.update(positions=0, calls=0)
            try:
                if psutil.Process().children(recursive=True):
                    raise IntegrityError("unaccounted helper process")
                row = base.execute(
                    case["messages"], selector, StressDecoder(backend), True, diagnostics
                )
                row.update(
                    {
                        "index": index,
                        "case": case["id"],
                        "cell": selector_name,
                        "pass": pass_number,
                        "replay": index == 2,
                        "failure": None,
                        "diagnostic_eos_suppression": True,
                        "backbone_work": dict(work),
                    }
                )
                if row["lm_calls"] != 1 or len(row["generated_ids"]) != 64:
                    raise IntegrityError("64-step workload was not exercised")
                if work != {"positions": row["fitted_prompt_tokens"] + 63, "calls": 64}:
                    raise IntegrityError("unlogged backbone work")
                tail = len(case["messages"]) - 3
                if not 440 <= row["fitted_prompt_tokens"] <= 512 or not {tail, tail + 1} <= set(
                    row["fitted_indices"]
                ):
                    raise IntegrityError("near-budget premise fit failed")
                if (
                    row["cost"]["request_wall_seconds"] > LIMITS["request_wall_seconds"]
                    or row["cost"]["request_cpu_seconds"] > LIMITS["request_cpu_seconds"]
                ):
                    raise IntegrityError("completed request safety cap")
                if index == 0:
                    first = stable(row)
                if index == 2 and stable(row) != first:
                    raise IntegrityError("replay disagreement")
                if psutil.Process().children(recursive=True):
                    raise IntegrityError("unexpected child helper")
            except Exception as error:
                stream.write(
                    json.dumps(
                        {
                            **row,
                            **diagnostics,
                            "index": index,
                            "case": case["id"],
                            "cell": selector_name,
                            "pass": pass_number,
                            "failure": f"{type(error).__name__}: {error}",
                            "elapsed_wall_seconds": time.monotonic() - progress["started"],
                            "elapsed_cpu_seconds": time.process_time()
                            - progress["worker_cpu_started"],
                        }
                    )
                    + "\n"
                )
                stream.flush()
                raise
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            base.progress(folder / "progress.json", {"active": False, "index": index})
    base.write(
        folder / "worker.json",
        {
            "pid": os.getpid(),
            "lifecycle_cpu_seconds": time.process_time(),
            "worker_wall_seconds": time.perf_counter() - start,
            "requests": 3,
            "setup": setup,
            "memory": psutil.Process().memory_info()._asdict(),
            "generation_config": backend.model.generation_config.to_dict(),
            "torch_threads": torch.get_num_threads(),
        },
    )


def run_stage(record: dict, selector: str, number: int, stages: list[dict]) -> dict:
    start, cpu_start = time.perf_counter(), time.process_time()
    folder = RUN / f"pass-{number}" / selector
    command = [
        sys.executable,
        str(Path(__file__)),
        "worker",
        "--selector",
        selector,
        "--pass-number",
        str(number),
    ]
    usage: dict[int, float] = {}
    peaks = {"rss": 0, "private": 0, "disk": 0}
    request_peaks: dict[str, dict] = {}
    parent_peak = 0
    max_gap = 0.0
    last = start
    active = {}
    reason = None
    inputs = [Path(n) for n in record["assets"]] + [ROOT / n for n in record["bindings"]]
    with (RUN / f"pass-{number}-{selector}.log").open("x", encoding="utf-8") as log:
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
                max_gap = max(max_gap, now - last)
                last = now
                rss, private, used = base.snapshot(process)
                parent = psutil.Process().memory_info()
                parent_private = getattr(parent, "private", parent.rss)
                parent_peak = max(parent_peak, parent_private)
                rss, private = rss + parent.rss, private + parent_private
                for pid, seconds in used.items():
                    usage[pid] = max(usage.get(pid, 0), seconds)
                disk = base.disk_bytes(inputs + list(RUN.rglob("*")))
                for key, value in (("rss", rss), ("private", private), ("disk", disk)):
                    peaks[key] = max(peaks[key], value)
                active = base.read_progress(folder / "progress.json")
                if active.get("active"):
                    p = request_peaks.setdefault(str(active["index"]), {})
                    for key, value in (("rss", rss), ("private", private), ("disk", disk)):
                        p[key] = max(p.get(key, 0), value)
                elapsed = now - start
                cpu = sum(usage.values()) + time.process_time() - cpu_start
                if private > LIMITS["memory_bytes"] or disk > LIMITS["disk_bytes"]:
                    reason = "memory/disk safety ceiling"
                elif elapsed > 240 or cpu > 480:
                    reason = "cold worker safety ceiling"
                elif (
                    sum(s["wall_seconds"] for s in stages) + elapsed > 960
                    or sum(s["cpu_seconds"] for s in stages) + cpu > 1920
                ):
                    reason = "overall cold-worker safety ceiling"
                elif max_gap > 5:
                    reason = "monitor gap"
                elif active.get("active") and (
                    time.monotonic() - active["started"] > 60
                    or usage.get(active["pid"], 0) - active["worker_cpu_started"] > 120
                ):
                    reason = "request safety ceiling"
                if reason:
                    break
                time.sleep(LIMITS["sample_seconds"])
        except Exception as error:
            reason = f"monitor failure: {type(error).__name__}: {error}"
        finally:
            base.terminate(child)
        code = child.wait()
    final = folder / "worker.json"
    if final.exists():
        info = base.read(final)
        usage[info["pid"]] = max(usage.get(info["pid"], 0), info["lifecycle_cpu_seconds"])
        peaks["private"] = max(
            peaks["private"], info["memory"].get("peak_pagefile", 0) + parent_peak
        )
    entries = base.rows(folder / "requests.jsonl")
    if active.get("active") and not any(r["index"] == active["index"] for r in entries):
        row = {
            "index": active["index"],
            "case": active["case"],
            "cell": selector,
            "pass": number,
            "failure": reason or "interrupted worker",
            "lm_calls": None,
            "executed_input_tokens": None,
            "executed_output_tokens": None,
            "elapsed_wall_seconds": time.monotonic() - active["started"],
            "request_cpu_lower_bound": max(
                0, usage.get(active["pid"], 0) - active["worker_cpu_started"]
            ),
        }
        with (folder / "requests.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row) + "\n")
        entries.append(row)
    if code or not final.exists() or len(entries) != 3 or any(r.get("failure") for r in entries):
        reason = reason or "worker/requests incomplete; see saved log"
    for row in entries:
        if row.get("failure"):
            continue
        p = request_peaks.setdefault(str(row["index"]), {})
        p["sampled"] = "private" in p
        p["end_memory"] = row["memory_end"]
        p["private_peak_upper_bound"] = peaks["private"]
        p["disk_peak_upper_bound"] = peaks["disk"]
    result = {
        "cell": selector,
        "pass": number,
        "command": command,
        "returncode": code,
        "failure": reason,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": sum(usage.values()) + time.process_time() - cpu_start,
        "controller_cpu_seconds": time.process_time() - cpu_start,
        "peak_private_bytes": peaks["private"],
        "peak_rss_bytes": peaks["rss"],
        "peak_disk_bytes": peaks["disk"],
        "max_monitor_gap_seconds": max_gap,
        "per_request_resources": request_peaks,
        "requests": len(entries),
    }
    if (
        result["wall_seconds"] > 240
        or result["cpu_seconds"] > 480
        or peaks["private"] > LIMITS["memory_bytes"]
    ):
        result["failure"] = result["failure"] or "final worker safety ceiling"
    base.write(RUN / f"pass-{number}-{selector}-cost.json", result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("cell", "pass", "failure", "requests", "wall_seconds", "cpu_seconds")
            }
        ),
        flush=True,
    )
    return result


def propose_caps(
    data: list[dict], stages: list[dict], shared_wall: float, shared_cpu: float
) -> dict:
    old_summary = base.read(OLD / "summary.json")
    old_rows = [r for p in OLD.glob("pass-*/*/requests.jsonl") for r in base.rows(p)]
    pooled = old_rows + data
    rw = math.ceil(2 * max(r["cost"]["request_wall_seconds"] for r in pooled))
    rc = math.ceil(2 * max(r["cost"]["request_cpu_seconds"] for r in pooled))
    residuals = {}
    for resource in ("wall", "cpu"):
        observed = max(
            s[f"{resource}_seconds"]
            - sum(
                r["cost"][f"request_{resource}_seconds"]
                for r in data
                if (r["cell"], r["pass"]) == (s["cell"], s["pass"])
            )
            for s in stages
        )
        residuals[resource] = max(
            observed, old_summary["proposed_caps"][f"max_nonrequest_{resource}_seconds"]
        )
    w, c = math.ceil(2 * residuals["wall"]) + 49 * rw, math.ceil(2 * residuals["cpu"]) + 49 * rc
    aw = max(old_summary["proposed_caps"]["shared_wall_seconds"], math.ceil(48 * shared_wall))
    ac = max(old_summary["proposed_caps"]["shared_cpu_seconds"], math.ceil(48 * shared_cpu))
    return {
        "request_wall_seconds": rw,
        "request_cpu_seconds": rc,
        "max_nonrequest_wall_seconds": residuals["wall"],
        "max_nonrequest_cpu_seconds": residuals["cpu"],
        "cell_pass_wall_seconds": w,
        "cell_pass_cpu_seconds": c,
        "shared_wall_seconds": aw,
        "shared_cpu_seconds": ac,
        "overall_wall_seconds": 8 * w + aw,
        "overall_cpu_seconds": 8 * c + ac,
        "memory_bytes": LIMITS["memory_bytes"],
        "disk_bytes": LIMITS["disk_bytes"],
        "status": "proposal only; 48-case study remains unregistered",
    }


def audit_completed(record: dict, stages: list[dict], failure: str | None) -> list[dict]:
    verify()
    data = [r for p in sorted(RUN.glob("pass-*/*/requests.jsonl")) for r in base.rows(p)]
    if failure:
        return data
    if len(data) != 12 or len(stages) != 4:
        raise IntegrityError("stress request arithmetic")
    for selector in ("T", "L"):
        first = base.rows(RUN / "pass-1" / selector / "requests.jsonl")
        second = base.rows(RUN / "pass-2" / selector / "requests.jsonl")
        if [stable(r) for r in first] != [stable(r) for r in second]:
            raise IntegrityError("cross-pass disagreement")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        record["backbone_directory"], local_files_only=True, trust_remote_code=False
    )
    cases = {c["id"]: c for c in base.read(RUN / "disposable-stress-inputs.json")}
    for row in data:
        ids = tokenizer.apply_chat_template(
            row["prompt_messages"], tokenize=True, add_generation_prompt=True, return_dict=False
        )
        if (
            ids != row["prompt_ids"]
            or tokenizer.decode(row["generated_ids"], skip_special_tokens=True)
            != row["raw_generated"]
        ):
            raise IntegrityError("native prompt/decode disagreement")
        view = make_view(
            cases[row["case"]]["messages"], row["selected_indices"], row["fitted_indices"]
        )
        if json.loads(json.dumps(asdict(view.manifest))) != row["manifest"]:
            raise IntegrityError("manifest drift")
        values = tuple(reslice(view, Provenance(**p)) for p in row["policy"]["sources"])
        if row["policy"]["route"] == "synthesis" and row["payload"] not in {
            sep.join(values) for sep in ("; ", " and ", ", ", "\n")
        }:
            raise IntegrityError("unsupported published synthesis")
    return data


def run() -> dict:
    start = time.perf_counter() - max(0.0, time.time() - psutil.Process().create_time())
    record = verify()
    base.write(RUN / "execution-started.json", {"requests_authorized": 12, "retries": 0})
    stages: list[dict] = []
    failure = None
    sleep_state = None
    try:
        if sys.platform == "win32":
            import ctypes

            sleep_state = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
            if not sleep_state:
                raise RuntimeError("sleep prevention failed")
        for number, order in enumerate(ORDER, 1):
            for selector in order:
                stage = run_stage(record, selector, number, stages)
                stages.append(stage)
                if stage["failure"]:
                    failure = stage["failure"]
                    break
            if failure:
                break
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        if sleep_state:
            import ctypes

            ctypes.windll.kernel32.SetThreadExecutionState(sleep_state)
    try:
        data = audit_completed(record, stages, failure)
    except Exception as error:
        failure = f"audit: {type(error).__name__}: {error}"
        data = [r for p in RUN.glob("pass-*/*/requests.jsonl") for r in base.rows(p)]
    prep = base.read(RUN / "preparation-cost.json")
    stage_wall, stage_cpu = (
        sum(s["wall_seconds"] for s in stages),
        sum(s["cpu_seconds"] for s in stages),
    )
    shared_wall = prep["wall_seconds"] + time.perf_counter() - start - stage_wall
    shared_cpu = (
        prep["cpu_seconds"] + time.process_time() - sum(s["controller_cpu_seconds"] for s in stages)
    )
    complete = failure is None and len(data) == 12
    valid = [r for r in data if not r.get("failure")]
    result = {
        "status": "COMPLETE" if complete else "STOPPED",
        "failure": failure,
        "scope": "64-step disposable resource diagnostic; no quality comparison",
        "requests": len(data),
        "lm_calls": sum(r.get("lm_calls") or 0 for r in data),
        "input_tokens": sum(r.get("executed_input_tokens") or 0 for r in data),
        "output_tokens": sum(r.get("executed_output_tokens") or 0 for r in data),
        "requests_with_unknown_lm_accounting": sum(
            any(
                r.get(k) is None
                for k in ("lm_calls", "executed_input_tokens", "executed_output_tokens")
            )
            for r in data
        ),
        "requests_with_64_generated_tokens": sum(len(r["generated_ids"]) == 64 for r in valid),
        "max_request_wall_seconds": max(
            (r["cost"]["request_wall_seconds"] for r in valid), default=0
        ),
        "max_request_cpu_seconds": max(
            (r["cost"]["request_cpu_seconds"] for r in valid), default=0
        ),
        "old_proposal_exceedances": [
            {
                "cell": r["cell"],
                "pass": r["pass"],
                "index": r["index"],
                "case": r["case"],
                "wall_seconds": r["cost"]["request_wall_seconds"],
                "cpu_seconds": r["cost"]["request_cpu_seconds"],
            }
            for r in valid
            if r["cost"]["request_wall_seconds"] > 14 or r["cost"]["request_cpu_seconds"] > 27
        ],
        "cold_wall_seconds": stage_wall,
        "cold_cpu_seconds": stage_cpu,
        "shared_wall_seconds": shared_wall,
        "shared_cpu_seconds": shared_cpu,
        "total_wall_seconds": stage_wall + shared_wall,
        "total_cpu_seconds": stage_cpu + shared_cpu,
        "peak_private_bytes": max(
            [
                prep["memory"].get("peak_pagefile", 0),
                psutil.Process().memory_info().peak_pagefile,
                *[s["peak_private_bytes"] for s in stages],
            ]
        ),
        "peak_disk_bytes": max([prep["disk_bytes"], *[s["peak_disk_bytes"] for s in stages]]),
        "proposed_caps": propose_caps(valid, stages, shared_wall, shared_cpu) if complete else None,
        "registered_benchmark_cases": 0,
        "heldout_inputs": 0,
        "extra_history_lookups": 0,
        "preserved_rehearsal_001": True,
    }
    base.write(RUN / "summary.json", result)
    base.verify_bindings(record["protected"])
    base.write(
        RUN / "output-sha256.json",
        {
            "files": {
                p.relative_to(RUN).as_posix(): base.file_sha(p)
                for p in sorted(RUN.rglob("*"))
                if p.is_file()
            }
        },
    )
    print(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "run", "worker"))
    parser.add_argument("--selector", choices=("T", "L"))
    parser.add_argument("--pass-number", type=int, choices=(1, 2))
    args = parser.parse_args()
    if args.action == "register":
        register()
        return 0
    if args.action == "worker":
        if args.selector is None or args.pass_number is None:
            parser.error("worker needs selector and pass")
        worker(args.selector, args.pass_number)
        return 0
    return int(run()["status"] != "COMPLETE")


if __name__ == "__main__":
    sys.exit(main())
