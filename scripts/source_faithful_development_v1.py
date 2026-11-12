"""Single-use source-faithful development v1. No synthesis, training or held-out loaders."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import evidence_first_rehearsal as base
import psutil
from evidence_first_policy import IntegrityError, Provenance, bind_request, make_view, reslice

ROOT = base.ROOT
RUN = ROOT / "artifacts/source-faithful-development-v1"
PROTOCOL = ROOT / "docs/research/source-faithful-development-v1-protocol.md"
BASE_COMMIT = "bf0f7482f21687db9788d2bfc4555cca5b0dd879"
ORDER = (base.CELLS, tuple(reversed(base.CELLS)))
LIMITS = {
    "request_wall_seconds": 26,
    "request_cpu_seconds": 51,
    "stage_wall_seconds": 360,
    "stage_cpu_seconds": 714,
    "total_stage_wall_seconds": 2880,
    "total_stage_cpu_seconds": 5712,
    "shared_wall_seconds": 120,
    "shared_cpu_seconds": 120,
    "overall_wall_seconds": 3000,
    "overall_cpu_seconds": 5832,
    "memory_bytes": 6 * 1024**3,
    "disk_bytes": 3 * 1024**3,
    "sample_seconds": 0.05,
    "max_monitor_gap_seconds": 5,
}
GATES = {
    "correct": 10,
    "category_correct": 2,
    "policy_gain": 2,
    "selector_gain": 2,
    "support_correct": 12,
    "token_saving": 0.20,
    "cpu_saving": 0.10,
    "wall_saving": 0.10,
    "regressions": 0,
    "both_passes_required": True,
}


def authored_cases() -> tuple[list[dict], list[dict]]:
    """Hand-authored gold, independent of policy parsing, selectors and model outputs."""
    cases: list[dict] = []
    labels: list[dict] = []

    def add(
        category,
        entity,
        field,
        tail,
        payload,
        source=None,
        *,
        full=False,
        unparsed=False,
        conflict=False,
        corrections=(),
    ):
        size = 32 if len(cases) % 2 == 0 else 48
        start = size - 1 - len(tail)
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": "No assertion."}
            for i in range(size - 1)
        ]
        for i, text in enumerate(tail, start):
            messages[i] = {"role": "user", "content": text}
        scope = list(range(size - 1)) if full else list(range(start, size - 1))
        prefix = "" if full else "In turns " + ",".join(f"m{i}" for i in scope) + ": "
        messages.append({"role": "user", "content": prefix + f"What is {entity}'s {field}?"})
        identifier = f"sf1-{len(cases) + 1:02d}-{entity.casefold()}"

        def span(spec):
            turn, value = spec
            raw = tail[turn].encode()
            needle = ('"' + value + '"').encode()
            if raw.count(needle) != 1:
                raise ValueError("manual label literal must be unique in its source turn")
            offset = raw.index(needle) + 1
            return {
                "turn": f"m{start + turn}",
                "start": offset,
                "end": offset + len(value.encode()),
                "value": value,
            }

        cases.append({"id": identifier, "messages": messages})
        labels.append(
            {
                "id": identifier,
                "category": category,
                "binding": [entity.casefold(), field],
                "scope": [f"m{i}" for i in scope],
                "payload": payload,
                "covered_state": "ambiguous/conflicting"
                if conflict
                else "supported"
                if source
                else "absent-in-complete-scope",
                "unparsed_turns": [f"m{start}"] if unparsed else [],
                "source": span(source) if source else None,
                "corrections": [[span(left), span(right)] for left, right in corrections],
            }
        )

    add(
        "copy",
        "OrchidLathe",
        "etching",
        ['OrchidLathe\'s etching is "  λ\tetch-406  ".'],
        "  λ\tetch-406  ",
        (0, "  λ\tetch-406  "),
    )
    add(
        "copy",
        "BasaltPrism",
        "weft",
        ['BasaltPrism\'s weft is "cafe\u0301  Δ/8".'],
        "cafe\u0301  Δ/8",
        (0, "cafe\u0301  Δ/8"),
    )
    add(
        "copy",
        "WillowDynamo",
        "stencil",
        ['WillowDynamo\'s stencil is "A\tB   C/509".'],
        "A\tB   C/509",
        (0, "A\tB   C/509"),
    )
    add(
        "binding",
        "PewterHarbor",
        "berth",
        [
            'PewterHarbor\'s berth is "south stair 214".\nPewterHarbor\'s docket is "docket-875".',
            'VelvetHarbor\'s berth is "north pontoon 635".',
        ],
        "south stair 214",
        (0, "south stair 214"),
    )
    add(
        "binding",
        "LinenBeacon",
        "signal",
        [
            'LinenBeacon\'s signal is "spiral-342".\nLinenBeacon\'s parcel is "parcel-981".',
            'GarnetBeacon\'s signal is "diagonal-756".',
        ],
        "spiral-342",
        (0, "spiral-342"),
    )
    add(
        "binding",
        "PorcelainRook",
        "stamp",
        ['PorcelainRook\'s stamp is "reed-163".', 'PorcelainRook\'s stamp is "bark-824".'],
        "UNKNOWN",
        conflict=True,
    )
    add(
        "correction",
        "HazelWinch",
        "tension",
        [
            'HazelWinch\'s tension is "12 kN".\nHazelWinch\'s spindle is "slot-417".',
            'Correction: HazelWinch\'s tension is "19 kN".',
        ],
        "19 kN",
        (1, "19 kN"),
        corrections=(((0, "12 kN"), (1, "19 kN")),),
    )
    add(
        "correction",
        "MarbleShuttle",
        "socket",
        [
            'MarbleShuttle\'s socket is "oval-268".\nMarbleShuttle\'s pitch is "6 mm".',
            'Correction: MarbleShuttle\'s pitch is "9 mm".',
        ],
        "oval-268",
        (0, "oval-268"),
    )
    add(
        "correction",
        "IndigoCistern",
        "valve",
        [
            'IndigoCistern\'s valve is "port-153".',
            'Correction: IndigoCistern\'s valve is "port-627".\n'
            'Correction: IndigoCistern\'s valve is "port-948".',
        ],
        "port-948",
        (1, "port-948"),
        corrections=(((0, "port-153"), (1, "port-627")), ((1, "port-627"), (1, "port-948"))),
    )
    add(
        "coverage",
        "CopperAviary",
        "password",
        ['CopperAviary\'s medallion is "grooved-572".'],
        "UNKNOWN",
    )
    add(
        "coverage",
        "SatinViaduct",
        "rendezvous",
        ['SatinViaduct\'s rendezvous is "west arch 386".'],
        "west arch 386",
        (0, "west arch 386"),
        full=True,
    )
    add(
        "coverage",
        "CedarGyroscope",
        "key",
        [
            "A workshop note describes weather without assigning a key.",
            'CedarGyroscope\'s collar is "knurled-693".',
        ],
        "UNKNOWN",
        unparsed=True,
    )
    return cases, labels


def validate_labels(cases: list[dict], labels: list[dict]) -> None:
    if len(cases) != 12 or len(labels) != 12 or len({c["id"] for c in cases}) != 12:
        raise IntegrityError("exactly twelve unique fresh development cases")
    for case, label in zip(cases, labels, strict=True):
        if set(case) != {"id", "messages"} or case["id"] != label["id"]:
            raise IntegrityError("input/label separation")
        messages = case["messages"]
        if len(messages) not in {32, 48}:
            raise IntegrityError("development history bounds")
        view = make_view(messages, list(range(len(messages))), list(range(len(messages))))
        request = bind_request(view)
        if request is None or request.synthesis or list(request.scope) != label["scope"]:
            raise IntegrityError("only frozen single-field requests")
        if list(request.bindings[0]) != label["binding"]:
            raise IntegrityError("manual requested binding mismatch")
        spans = [label["source"]] if label["source"] else []
        spans += [s for pair in label["corrections"] for s in pair]
        for span in spans:
            raw = messages[int(span["turn"][1:])]["content"].encode()
            if raw[span["start"] : span["end"]] != span["value"].encode():
                raise IntegrityError("manual UTF-8 span mismatch")
        if label["source"] and label["payload"] != label["source"]["value"]:
            raise IntegrityError("full-scope gold must equal manual source bytes")


def expected_state(label: dict, row: dict) -> str:
    """Independent annotated coverage oracle; no policy parser or resolver call."""
    available = {s["turn"]: (s["start"], s["end"]) for s in row["fitted_sources"]}
    turns = {t["id"]: t for t in row["manifest"]["turns"]}
    if label["unparsed_turns"] or any(
        available.get(t) != (0, turns[t]["length"]) for t in label["scope"]
    ):
        return "coverage-incomplete"
    return label["covered_state"]


def score(label: dict, row: dict) -> dict:
    result = {
        "case": label["id"],
        "category": label["category"],
        "payload_correct": row["payload"].encode() == label["payload"].encode(),
    }
    policy = row["policy"]
    if policy is None:
        return {**result, "support_correct": None, "provenance_correct": None}
    state = expected_state(label, row)
    supported = state == "supported"

    def same(actual, wanted):
        if wanted is None:
            return False
        turn = next(t for t in row["manifest"]["turns"] if t["id"] == wanted["turn"])
        return (
            all(actual[k] == wanted[k] for k in ("turn", "start", "end"))
            and actual["revision"] == row["manifest"]["revision"]
            and actual["turn_sha256"] == turn["sha256"]
            and actual["role"] == turn["role"]
            and actual["chronology"] == turn["chronology"]
        )

    provenance = (
        (
            len(policy["sources"]) == 1
            and same(policy["sources"][0], label["source"])
            and policy["route"] == "copy"
            and result["payload_correct"]
            and len(policy["corrections"]) == len(label["corrections"])
            and all(
                same(a, b)
                for pair, wanted in zip(policy["corrections"], label["corrections"], strict=True)
                for a, b in zip(pair, wanted, strict=True)
            )
        )
        if supported
        else (
            not policy["sources"] and policy["route"] == "abstain" and row["payload"] == "UNKNOWN"
        )
    )
    return {
        **result,
        "expected_state": state,
        "support_correct": policy["state"] == state and policy["scope"] == label["scope"],
        "provenance_correct": provenance,
    }


def freeze() -> dict:
    start = time.perf_counter() - max(0, time.time() - psutil.Process().create_time())
    RUN.mkdir(parents=True, exist_ok=False)
    if (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        != BASE_COMMIT
    ):
        raise IntegrityError("unexpected development baseline")
    if (
        subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
        != "main"
    ):
        raise IntegrityError("main required")
    old = base.read(ROOT / "artifacts/evidence-first-prototype/rehearsal-001/rehearsal-freeze.json")
    base.verify_bindings(old["assets"])
    cases, labels = authored_cases()
    validate_labels(cases, labels)
    # Compare only previously observed disposable inputs, not any held-out case file.
    previous = []
    for name in (
        "rehearsal-001/disposable-inputs.json",
        "feasibility-v2/disposable-stress-inputs.json",
    ):
        previous += base.read(ROOT / "artifacts/evidence-first-prototype" / name)
    old_text = "\n".join(m["content"] for c in previous for m in c["messages"])
    for label in labels:
        entity = label["binding"][0]
        if entity in old_text.casefold() or (label["source"] and label["payload"] in old_text):
            raise IntegrityError("overlap with observed disposable material")
    base.write(RUN / "inputs.json", cases)
    base.write(RUN / "labels-evaluator-only.json", labels)
    (RUN / "protocol-at-freeze.md").write_bytes(PROTOCOL.read_bytes())
    bindings = base.tracked_bindings()
    for name in (
        "scripts/source_faithful_development_v1.py",
        "tests/test_source_faithful_development_v1.py",
        "docs/research/source-faithful-development-v1-protocol.md",
    ):
        bindings[name] = base.file_sha(ROOT / name)
    for path in RUN.iterdir():
        bindings[path.relative_to(ROOT).as_posix()] = base.file_sha(path)
    # Preserve old decisions, implementation, reports and all saved experimental bytes.
    portable = base.read(ROOT / "artifacts/evidence-first-prototype/portable-record/manifest.json")
    protected = {name: base.file_sha(ROOT / name) for name in portable["files"]}
    protected["artifacts/evidence-first-prototype/portable-record/manifest.json"] = base.file_sha(
        ROOT / "artifacts/evidence-first-prototype/portable-record/manifest.json"
    )
    with zipfile.ZipFile(RUN / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in bindings:
            archive.write(ROOT / name, name)
    bindings[(RUN / "source.zip").relative_to(ROOT).as_posix()] = base.file_sha(RUN / "source.zip")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        old["backbone_directory"], local_files_only=True, trust_remote_code=False
    )
    for label in labels:
        if len(tokenizer.encode(label["payload"], add_special_tokens=False)) > 64:
            raise IntegrityError("manual payload exceeds cap")
    record = {
        "schema": "source-faithful-development-v1",
        "utc": datetime.now(UTC).isoformat(),
        "base_commit": BASE_COMMIT,
        "synthesis_excluded": True,
        "old_48_case_study_registered": False,
        "heldout_records_read": 0,
        "bindings": bindings,
        "protected": protected,
        "assets": old["assets"],
        "backbone_directory": old["backbone_directory"],
        "selector_checkpoint": old["selector_checkpoint"],
        "model_identity": base.read(Path(old["backbone_directory"]) / "toruk-backbone.json"),
        "dependencies": {
            n: importlib.metadata.version(n)
            for n in ("torch", "transformers", "tokenizers", "safetensors", "psutil")
        },
        "decoding": {
            "seed": 81751,
            "dtype": "float32",
            "threads": 2,
            "do_sample": False,
            "num_beams": 1,
            "repetition_penalty": 1.0,
            "use_cache": True,
            "max_new_tokens": 64,
            "min_new_tokens": 0,
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token_id": tokenizer.pad_token_id,
        },
        "limits": LIMITS,
        "gates": GATES,
        "order": ORDER,
        "requests": [
            {"pass": n, "cell": cell, "case": case["id"], "index": i, "replay": i == 12}
            for n, order in enumerate(ORDER, 1)
            for cell in order
            for i, case in enumerate(cases + [cases[0]])
        ],
        "case_count": 12,
        "request_count": 104,
        "max_lm_calls": 52,
        "gold_review": (
            "authored source-linked labels; structural validation; no independent human review"
        ),
    }
    base.write(RUN / "registration.json", record)
    base.write(
        RUN / "registration-cost.json",
        {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time(),
            "new_generations": 0,
            "memory": psutil.Process().memory_info()._asdict(),
            "disk_bytes": base.disk_bytes(
                [Path(n) for n in record["assets"]]
                + [ROOT / n for n in bindings]
                + list(RUN.rglob("*"))
            ),
        },
    )
    print(
        json.dumps(
            {
                "registration_sha256": base.file_sha(RUN / "registration.json"),
                "requests_frozen": 104,
                "generations": 0,
            }
        ),
        flush=True,
    )
    return record


def verify_freeze() -> dict:
    marker = RUN / "execution-started.json"
    if marker.exists() and base.read(marker)["registration_sha256"] != base.file_sha(
        RUN / "registration.json"
    ):
        raise IntegrityError("registration drift")
    record = base.read(RUN / "registration.json")
    for key in ("bindings", "protected", "assets"):
        base.verify_bindings(record[key])
    if record["limits"] != LIMITS or record["gates"] != GATES:
        raise IntegrityError("gate/cap drift")
    for name, version in record["dependencies"].items():
        if importlib.metadata.version(name) != version:
            raise IntegrityError("dependency drift")
    return record


def worker(cell: str, number: int) -> None:
    start, cpu = time.perf_counter(), time.process_time()
    folder = RUN / f"pass-{number}" / cell
    folder.mkdir(parents=True, exist_ok=False)
    record = verify_freeze()
    # Never read evaluator labels in a worker.
    cases = base.read(RUN / "inputs.json")
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
        max_new_tokens=64,
        temperature=1.0,
        top_p=1.0,
        eos_token_id=backend.tokenizer.eos_token_id,
        pad_token_id=backend.tokenizer.pad_token_id,
    )
    selector = (
        LexicalAdmissionSelector(TorukContextSelector(Path(record["selector_checkpoint"])))
        if cell.startswith("T-")
        else LexicalContextSelector("lexical-v1")
    )
    base.write(
        folder / "setup.json",
        {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu},
    )
    adapter = base.Decoder(backend)
    first = None
    with (folder / "requests.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for i, case in enumerate(cases + [cases[0]]):
            tick, request_cpu = time.perf_counter(), time.process_time()
            base.progress(
                folder / "progress.json",
                {
                    "active": True,
                    "index": i,
                    "case": case["id"],
                    "pid": os.getpid(),
                    "started": time.monotonic(),
                    "worker_cpu_started": request_cpu,
                },
            )
            diagnostics: dict = {}
            identity = {
                "case": case["id"],
                "cell": cell,
                "pass": number,
                "index": i,
                "replay": i == 12,
            }
            try:
                if psutil.Process().children(recursive=True):
                    raise IntegrityError("unexpected child helper")
                row = base.execute(
                    case["messages"], selector, adapter, cell.endswith("-P"), diagnostics
                )
                row.update(identity, failure=None)
                if cell.endswith("-P") and (
                    row["lm_calls"] or row["policy"]["route"] == "synthesis"
                ):
                    raise IntegrityError("synthesis excluded; no policy LM calls permitted")
                if (
                    row["cost"]["request_wall_seconds"] > 26
                    or row["cost"]["request_cpu_seconds"] > 51
                ):
                    raise IntegrityError("request cap")
                if i == 0:
                    first = base.stable(row)
                if i == 12 and base.stable(row) != first:
                    raise IntegrityError("replay disagreement")
            except Exception as error:
                row = {
                    **identity,
                    "failure": f"{type(error).__name__}: {error}",
                    "elapsed_wall_seconds": time.perf_counter() - tick,
                    "elapsed_cpu_seconds": time.process_time() - request_cpu,
                    **diagnostics,
                }
                stream.write(json.dumps(row) + "\n")
                stream.flush()
                raise
            stream.write(json.dumps(row, ensure_ascii=True) + "\n")
            stream.flush()
            base.progress(folder / "progress.json", {"active": False, "index": i})
    base.write(
        folder / "worker.json",
        {
            "pid": os.getpid(),
            "lifecycle_cpu_seconds": time.process_time(),
            "worker_wall_seconds": time.perf_counter() - start,
            "memory": psutil.Process().memory_info()._asdict(),
            "requests": 13,
            "torch_threads": torch.get_num_threads(),
            "generation_config": backend.model.generation_config.to_dict(),
        },
    )


def run_stage(record: dict, cell: str, number: int, stages: list[dict]) -> dict:
    start, cpu_start = time.perf_counter(), time.process_time()
    folder = RUN / f"pass-{number}" / cell
    command = [
        sys.executable,
        str(Path(__file__)),
        "worker",
        "--cell",
        cell,
        "--pass-number",
        str(number),
    ]
    usage: dict[int, float] = {}
    peaks = {"rss": 0, "private": 0, "disk": 0}
    request_peaks: dict[str, dict] = {}
    parent_peak, max_gap = 0, 0.0
    last = start
    active: dict = {}
    reason = None
    paths = [Path(n) for n in record["assets"]] + [ROOT / n for n in record["bindings"]]
    with (RUN / f"pass-{number}-{cell}.log").open("x", encoding="utf-8") as log:
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
                max_gap, last = max(max_gap, now - last), now
                rss, private, used = base.snapshot(process)
                parent = psutil.Process().memory_info()
                parent_private = getattr(parent, "private", parent.rss)
                parent_peak = max(parent_peak, parent_private)
                rss, private = rss + parent.rss, private + parent_private
                for pid, seconds in used.items():
                    usage[pid] = max(usage.get(pid, 0), seconds)
                disk = base.disk_bytes(paths + list(RUN.rglob("*")))
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
                    reason = "memory/disk cap"
                elif elapsed > 360 or cpu > 714:
                    reason = "cold worker cap"
                elif (
                    sum(s["wall_seconds"] for s in stages) + elapsed > 2880
                    or sum(s["cpu_seconds"] for s in stages) + cpu > 5712
                ):
                    reason = "overall cold-worker cap"
                elif max_gap > 5:
                    reason = "monitor gap"
                elif active.get("active") and (
                    time.monotonic() - active["started"] > 26
                    or usage.get(active["pid"], 0) - active["worker_cpu_started"] > 51
                ):
                    reason = "request cap"
                if reason:
                    break
                time.sleep(0.05)
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
            "cell": cell,
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
    if code or not final.exists() or len(entries) != 13 or any(r.get("failure") for r in entries):
        reason = reason or "worker/requests incomplete; see saved log"
    for row in entries:
        if row.get("failure"):
            continue
        p = request_peaks.setdefault(str(row["index"]), {})
        p.update(
            sampled="private" in p,
            end_memory=row["memory_end"],
            private_peak_upper_bound=peaks["private"],
            disk_peak_upper_bound=peaks["disk"],
        )
    result = {
        "cell": cell,
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
        "cpu_scope": "controller plus sampled worker descendants, reconciled to lifetime CPU",
    }
    if (
        result["wall_seconds"] > 360
        or result["cpu_seconds"] > 714
        or peaks["private"] > LIMITS["memory_bytes"]
    ):
        result["failure"] = result["failure"] or "final worker cap"
    base.write(RUN / f"pass-{number}-{cell}-cost.json", result)
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


def saving(candidate: float, control: float, threshold: float) -> bool:
    return control > 0 and candidate <= (1 - threshold) * control


def decide(scores: dict, costs: dict, integrity: bool) -> dict:
    policies = {}
    details = {}
    for selector in ("T", "L"):
        proposed, control = selector + "-P", selector + "-LM"
        gates = []
        for number in ("1", "2"):
            s, c = scores[number][proposed], scores[number][control]
            accuracy = lambda rows: sum(r["payload_correct"] for r in rows)  # noqa: E731
            correct = accuracy(s)
            stronger = max(accuracy(scores[number][name]) for name in ("T-LM", "L-LM"))
            comparisons = {
                "accuracy": correct >= 10,
                "categories": all(
                    sum(r["payload_correct"] for r in s if r["category"] == category) >= 2
                    for category in ("copy", "binding", "correction", "coverage")
                ),
                "own_gain": correct >= accuracy(c) + 2,
                "stronger_control_gain": correct >= stronger + 2,
                "no_regression": all(
                    not old["payload_correct"] or new["payload_correct"]
                    for new, old in zip(s, c, strict=True)
                ),
                "support_provenance": all(
                    r["support_correct"] and r["provenance_correct"] for r in s
                ),
                "integrity": integrity,
            }
            for dimension, threshold in (("tokens", 0.2), ("cpu", 0.1), ("wall", 0.1)):
                comparisons[dimension + "_saving"] = saving(
                    costs[number][proposed][dimension], costs[number][control][dimension], threshold
                )
            details[f"{proposed}/pass-{number}"] = comparisons
            gates.append(all(comparisons.values()))
        policies[proposed] = all(gates)
    selector_checks = []
    for number in ("1", "2"):
        t, lexical = scores[number]["T-P"], scores[number]["L-P"]
        checks = {
            "both_policy_gates": all(policies.values()),
            "gain": sum(r["payload_correct"] for r in t)
            >= sum(r["payload_correct"] for r in lexical) + 2,
            "no_regression": all(
                not b["payload_correct"] or a["payload_correct"]
                for a, b in zip(t, lexical, strict=True)
            ),
        }
        for dimension, threshold in (("tokens", 0.2), ("cpu", 0.1), ("wall", 0.1)):
            checks[dimension + "_saving"] = saving(
                costs[number]["T-P"][dimension], costs[number]["L-P"][dimension], threshold
            )
        details["T-P_vs_L-P/pass-" + number] = checks
        selector_checks.append(all(checks.values()))
    learned = all(selector_checks)
    outcome = (
        "bounded selector result"
        if learned
        else "shared policy only"
        if all(policies.values())
        else "single selector-policy combination only"
        if any(policies.values())
        else "reject policy adoption and selector contribution under v1"
    )
    return {
        "policy_gates": policies,
        "learned_selector_gate": learned,
        "outcome": outcome,
        "checks": details,
    }


def evaluate(rows: list[dict], stages: list[dict], shared: dict, integrity: bool) -> dict:
    labels = base.read(RUN / "labels-evaluator-only.json")
    scores: dict = {str(n): {} for n in (1, 2)}
    costs: dict = {str(n): {} for n in (1, 2)}
    for n in (1, 2):
        for cell in base.CELLS:
            selected = [r for r in rows if r["pass"] == n and r["cell"] == cell]
            main = [r for r in selected if not r["replay"]]
            if len(main) != 12 or any(r.get("failure") for r in selected):
                return {
                    "status": "FAIL/UNESTABLISHED",
                    "reason": "incomplete run",
                    "scores": scores,
                }
            scores[str(n)][cell] = [
                score(label, row) for label, row in zip(labels, main, strict=True)
            ]
            stage = next(s for s in stages if s["pass"] == n and s["cell"] == cell)
            costs[str(n)][cell] = {
                "tokens": sum(
                    r["executed_input_tokens"] + r["executed_output_tokens"] for r in selected
                ),
                "cpu": stage["cpu_seconds"] + shared["cpu_seconds"] / 8,
                "wall": stage["wall_seconds"] + shared["wall_seconds"] / 8,
            }
    return {"scores": scores, "costs_for_gates": costs, **decide(scores, costs, integrity)}


def run() -> dict:
    start = time.perf_counter() - max(0, time.time() - psutil.Process().create_time())
    base.write(
        RUN / "execution-started.json",
        {
            "utc": datetime.now(UTC).isoformat(),
            "registration_sha256": base.file_sha(RUN / "registration.json"),
            "no_retry": True,
        },
    )
    stages: list[dict] = []
    failure = None
    sleep_state = None
    try:
        record = verify_freeze()
        preparation = base.read(RUN / "registration-cost.json")
        memory = preparation["memory"]
        if (
            preparation["wall_seconds"] > 120
            or preparation["cpu_seconds"] > 120
            or preparation["disk_bytes"] > LIMITS["disk_bytes"]
            or memory.get("private", memory["rss"]) > LIMITS["memory_bytes"]
        ):
            raise IntegrityError("preparation cap; no inference allowed")
        if sys.platform == "win32":
            import ctypes

            sleep_state = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
            if not sleep_state:
                raise IntegrityError("sleep inhibition failed")
        for n, order in enumerate(record["order"], 1):
            for cell in order:
                stage = run_stage(record, cell, n, stages)
                stages.append(stage)
                if stage["failure"]:
                    raise IntegrityError(stage["failure"])
                base.check_pairs(RUN)
                verify_freeze()
                shared_wall = (
                    preparation["wall_seconds"]
                    + time.perf_counter()
                    - start
                    - sum(s["wall_seconds"] for s in stages)
                )
                shared_cpu = (
                    preparation["cpu_seconds"]
                    + time.process_time()
                    - sum(s["controller_cpu_seconds"] for s in stages)
                )
                if shared_wall > 120 or shared_cpu > 120:
                    raise IntegrityError("shared cap; stop before another worker")
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        if sleep_state:
            import ctypes

            ctypes.windll.kernel32.SetThreadExecutionState(sleep_state)
    # All available raw outputs sealed BEFORE labels are opened for scoring.
    base.write(
        RUN / "raw-output-seal.json",
        {
            "files": {
                p.relative_to(RUN).as_posix(): base.file_sha(p)
                for p in sorted(RUN.rglob("*"))
                if p.is_file()
            },
            "failure": failure,
        },
    )
    rows = [
        r
        for n, order in enumerate(ORDER, 1)
        for cell in order
        for r in base.rows(RUN / f"pass-{n}" / cell / "requests.jsonl")
    ]
    preparation = base.read(RUN / "registration-cost.json")
    stage_wall, stage_cpu = (sum(s[k] for s in stages) for k in ("wall_seconds", "cpu_seconds"))
    # Controller stage CPU was already included in stage receipts; charge the rest once.
    shared = {
        "wall_seconds": preparation["wall_seconds"] + time.perf_counter() - start - stage_wall,
        "cpu_seconds": preparation["cpu_seconds"]
        + time.process_time()
        - sum(s["controller_cpu_seconds"] for s in stages),
    }
    audit_start, audit_cpu = time.perf_counter(), time.process_time()
    report = evaluate(rows, stages, shared, failure is None)
    audit_wall, audit_used = time.perf_counter() - audit_start, time.process_time() - audit_cpu
    shared["wall_seconds"] += audit_wall
    shared["cpu_seconds"] += audit_used
    # Recompute gate allocations after charging the evaluator, without re-reading model outputs.
    if "costs_for_gates" in report:
        for costs in report["costs_for_gates"].values():
            for cost in costs.values():
                cost["wall"] += audit_wall / 8
                cost["cpu"] += audit_used / 8
        report.update(decide(report["scores"], report["costs_for_gates"], failure is None))
    if (
        shared["wall_seconds"] > 120
        or shared["cpu_seconds"] > 120
        or stage_wall + shared["wall_seconds"] > 3000
        or stage_cpu + shared["cpu_seconds"] > 5832
    ):
        failure = failure or "shared/overall cap"
        if "costs_for_gates" in report:
            report.update(decide(report["scores"], report["costs_for_gates"], False))
    successful = [r for r in rows if not r.get("failure")]
    summary = {
        "status": "COMPLETE" if failure is None else "STOPPED",
        "failure": failure,
        "registration_sha256": base.file_sha(RUN / "registration.json"),
        "requests_recorded": len(rows),
        "requests_planned": 104,
        "lm_calls": sum(r.get("lm_calls") or 0 for r in rows),
        "input_tokens": sum(r.get("executed_input_tokens") or 0 for r in rows),
        "output_tokens": sum(r.get("executed_output_tokens") or 0 for r in rows),
        "failed_requests": [r for r in rows if r.get("failure")],
        "unknown_token_counts": sum(r.get("executed_output_tokens") is None for r in rows),
        "stage_wall_seconds": stage_wall,
        "stage_cpu_seconds": stage_cpu,
        "shared": shared,
        "total_wall_seconds": stage_wall + shared["wall_seconds"],
        "total_cpu_seconds": stage_cpu + shared["cpu_seconds"],
        "max_request_wall_seconds": max(
            (r["cost"]["request_wall_seconds"] for r in successful), default=0
        ),
        "max_request_cpu_seconds": max(
            (r["cost"]["request_cpu_seconds"] for r in successful), default=0
        ),
        "peak_private_bytes": max((s["peak_private_bytes"] for s in stages), default=0),
        "peak_disk_bytes": max((s["peak_disk_bytes"] for s in stages), default=0),
        "max_monitor_gap_seconds": max((s["max_monitor_gap_seconds"] for s in stages), default=0),
        "finalization_boundary": (
            "summary/report/seal serialization outside instrumented total; outer command retained"
        ),
        "report": report,
    }
    base.write(RUN / "results.json", summary)
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
    print(json.dumps({k: v for k, v in summary.items() if k != "report"}, indent=2), flush=True)
    return summary


def verify_completed() -> dict:
    record = verify_freeze()
    for seal in ("output-sha256.json", "raw-output-seal.json"):
        for name, expected in base.read(RUN / seal)["files"].items():
            if base.file_sha(RUN / name) != expected:
                raise IntegrityError("sealed output drift: " + name)
    base.check_pairs(RUN)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        record["backbone_directory"], local_files_only=True, trust_remote_code=False
    )
    cases = {c["id"]: c for c in base.read(RUN / "inputs.json")}
    count = copies = 0
    for path in sorted(RUN.glob("pass-*/*/requests.jsonl")):
        for row in base.rows(path):
            if row.get("failure"):
                continue
            count += 1
            prompt_ids = tokenizer.apply_chat_template(
                row["prompt_messages"], tokenize=True, add_generation_prompt=True, return_dict=False
            )
            if prompt_ids != row["prompt_ids"]:
                raise IntegrityError("native prompt IDs")
            if (
                row["lm_calls"]
                and tokenizer.decode(row["generated_ids"], skip_special_tokens=True)
                != row["raw_generated"]
            ):
                raise IntegrityError("native answer IDs")
            view = make_view(
                cases[row["case"]]["messages"], row["selected_indices"], row["fitted_indices"]
            )
            if asdict(view.manifest) != row["manifest"]:
                # JSON changes immutable tuples to lists; use a JSON round trip.
                if json.loads(json.dumps(asdict(view.manifest))) != row["manifest"]:
                    raise IntegrityError("manifest reconstruction")
            if row["policy"] and row["policy"]["route"] == "copy":
                copies += 1
                if reslice(view, Provenance(**row["policy"]["sources"][0])) != row["payload"]:
                    raise IntegrityError("copy reconstruction")
    result = base.read(RUN / "results.json")
    return {
        "status": "PASS",
        "saved_rows": count,
        "direct_copies": copies,
        "new_generations": 0,
        "registration_sha256": base.file_sha(RUN / "registration.json"),
        "study_status": result["status"],
        "protected_files": len(record["protected"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run", "worker", "verify"))
    parser.add_argument("--cell", choices=base.CELLS)
    parser.add_argument("--pass-number", type=int, choices=(1, 2))
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    elif args.action == "worker":
        if args.cell is None or args.pass_number is None:
            parser.error("worker requires cell and pass")
        worker(args.cell, args.pass_number)
    elif args.action == "verify":
        print(json.dumps(verify_completed(), indent=2))
    else:
        return int(run()["status"] != "COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
