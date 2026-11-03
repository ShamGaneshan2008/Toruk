"""Synthetic supervised memory study. Gold labels stay outside the runtime module."""

import argparse
import ctypes
import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

from toruk_lm.chat_selector import ChatRelevanceSelector
from toruk_lm.data import sha256_file, write_json
from toruk_lm.integrated_memory import (
    FORMAT,
    IntegratedConfig,
    IntegratedMemoryLM,
    IntegratedSession,
    load_integrated,
    padded,
    text_tokens,
)
from toruk_lm.tokenizer import ByteTokenizer

DATA_FORMAT = "toruk-integrated-worlds-v1"
CATEGORIES = ("correction", "preservation", "long_recall", "local", "unknown", "conflict")
KEYS = [(name, field) for name in ("Ada", "Ben", "Cyd") for field in ("color", "pet")]
VALUES = ("red", "blue", "green", "cat", "dog", "owl")


def peak_bytes() -> int | None:
    if sys.platform != "win32":
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("faults", ctypes.c_ulong),
            ("peak", ctypes.c_size_t),
            ("working", ctypes.c_size_t),
            ("rest", ctypes.c_size_t * 6),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi = ctypes.windll.psapi
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return int(counters.peak)
    return None


def render(split: str, key: int, value: str, operation: str) -> str:
    name, field = KEYS[key]
    frames = {
        "train": {
            "set": "Set {n} {f} {v}.",
            "revise": "Change {n} {f} {v}.",
            "claim": "Claim {n} {f} {v}.",
        },
        "dev": {
            "set": "For {n}, {f} is {v}.",
            "revise": "Update {n}: {f} is {v}.",
            "claim": "Maybe {n}: {f} is {v}.",
        },
        "final": {
            "set": "Record {n}: {f}={v}.",
            "revise": "Replace {n}: {f}={v}.",
            "claim": "Unconfirmed {n}: {f}={v}.",
        },
    }
    return frames[split][operation].format(n=name, f=field, v=value)


def make_case(split: str, category: str, number: int, rng: random.Random) -> dict[str, Any]:
    keys = rng.sample(range(6), 6)
    first, preserved, other, distractor, spare, absent = keys
    old, new, valid = rng.sample(VALUES, 3)
    events: list[dict[str, Any]] = []

    def event(key: int, value: str, operation: str = "set") -> None:
        events.append(
            {
                "text": render(split, key, value, operation),
                "key": key,
                "value": value,
                "operation": operation,
                "address": 6 if operation == "claim" else key,
            }
        )

    event(first, old)
    event(preserved, valid)
    event(other, rng.choice(VALUES))
    event(first, new, "revise")
    for _index in range(rng.randint(4, 7)):
        event(rng.choice((distractor, spare)), rng.choice(VALUES))
    query_key = first
    if category == "preservation":
        query_key = preserved
    elif category == "local":
        query_key = other
        event(other, rng.choice(VALUES), "revise")
    elif category in ("unknown", "conflict"):
        query_key = absent
        if category == "conflict":
            event(absent, old, "claim")
            event(absent, new, "claim")
    # Independent event oracle: later authoritative writes replace only their key.
    truth: dict[int, str] = {}
    for item in events:
        if item["operation"] in ("set", "revise"):
            truth[item["key"]] = item["value"]
    name, field = KEYS[query_key]
    question = {
        "train": f"What is {name}'s {field}?",
        "dev": f"Tell me {name}'s {field}.",
        "final": f"Which {field} belongs to {name}?",
    }[split]
    answer = truth.get(query_key, "?")
    assert answer == (
        "?"
        if category in ("unknown", "conflict")
        else valid
        if category == "preservation"
        else events[-1]["value"]
        if category == "local"
        else new
    )
    return {
        "id": f"{split}-{category}-{number:03d}",
        "world": f"{split}-{category}-{number}",
        "split": split,
        "category": category,
        "events": events,
        "query": question,
        "query_key": query_key,
        "answer": answer,
        "obsolete": old if query_key == first else None,
    }


def make_data(directory: Path) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "format": DATA_FORMAT,
        "splits": {},
        "slots": 6,
        "shared_symbol_inventory": KEYS,
        "values": VALUES,
    }
    seen: set[str] = set()
    for split, seed, size in (("train", 4101, 64), ("dev", 5101, 16), ("final", 6101, 16)):
        rng = random.Random(seed)
        rows = [make_case(split, cat, index, rng) for cat in CATEGORIES for index in range(size)]
        for row in rows:
            identity = json.dumps([item["text"] for item in row["events"]]) + row["query"]
            if identity in seen:
                raise ValueError("duplicate world text")
            seen.add(identity)
        path = directory / f"{split}.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
        manifest["splits"][split] = {"seed": seed, "cases": len(rows), "sha256": sha256_file(path)}
    write_json(directory / "manifest.json", manifest)
    return manifest


def read_data(directory: Path, split: str, *, training: bool = False) -> list[dict[str, Any]]:
    if training and split != "train":
        raise ValueError("training may only consume the training split")
    manifest = json.loads((directory / "manifest.json").read_text())
    if (
        manifest["format"] != DATA_FORMAT
        or sha256_file(directory / f"{split}.jsonl") != (manifest["splits"][split]["sha256"])
    ):
        raise ValueError("dataset identity mismatch")
    rows = [json.loads(line) for line in (directory / f"{split}.jsonl").read_text().splitlines()]
    if len(rows) != manifest["splits"][split]["cases"] or any(r["split"] != split for r in rows):
        raise ValueError("split mismatch")
    return rows


def batch_loss(
    model: IntegratedMemoryLM, rows: list[dict[str, Any]]
) -> tuple[torch.Tensor, dict[str, float]]:
    config = model.config
    count = len(rows)
    longest = max(len(row["events"]) for row in rows)
    if longest > config.max_records:
        raise ValueError("training world exceeds bounded unroll")
    records: list[list[int]] = []
    labels: list[int] = []
    for row in rows:
        records.extend(text_tokens(item["text"], config.record_tokens) for item in row["events"])
        records.extend([[1]] * (longest - len(row["events"])))
        labels.extend(
            [item["address"] for item in row["events"]] + [-100] * (longest - len(row["events"]))
        )
    encoded = model.encode(padded(records)).reshape(count, longest, config.width)
    address_logits = model.write_address(encoded)
    state = model.initial_state(count)
    if model.variant == "integrated":
        for index in range(longest):
            updated, _ = model.update_vectors(state, encoded[:, index])
            active = torch.tensor([index < len(row["events"]) for row in rows])[:, None, None]
            state = torch.where(active, updated, state)
    local = padded(
        [
            ByteTokenizer().encode("\n".join(item["text"] for item in row["events"]) + "\n")[
                -config.local_tokens :
            ]
            for row in rows
        ]
    )
    queries = padded([text_tokens(row["query"], config.query_tokens) for row in rows])
    hidden, read, read_logits = model.prepare(local, queries, state)
    answers = [ByteTokenizer().encode(row["answer"]) + [2] for row in rows]
    previous = padded([[1] + answer[:-1] for answer in answers])
    targets = padded(answers)
    logits, _ = model.decode(previous, hidden, read)
    language_loss = F.cross_entropy(logits.reshape(-1, 259), targets.reshape(-1), ignore_index=0)
    write_loss = F.cross_entropy(address_logits.reshape(-1, config.slots + 1), torch.tensor(labels))
    read_loss = F.cross_entropy(read_logits, torch.tensor([row["query_key"] for row in rows]))
    # Same addressing supervision for both methods; only integrated state reaches answers.
    loss = language_loss + 0.25 * (write_loss + read_loss)
    return loss, {
        "loss": loss.item(),
        "answer_ce": language_loss.item(),
        "write_ce": write_loss.item(),
        "read_ce": read_loss.item(),
    }


def train(
    directory: Path,
    output: Path,
    variant: str,
    seed: int,
    steps: int,
    config: IntegratedConfig,
    resume: Path | None = None,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("use a fresh checkpoint path")
    rows = read_data(directory, "train", training=True)
    identity = sha256_file(directory / "manifest.json")
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    rng = random.Random(seed)
    model = IntegratedMemoryLM(config, variant)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    first, curve = 0, []
    if resume:
        model, saved = load_integrated(resume)
        if (
            saved["data_sha256"] != identity
            or saved["variant"] != variant
            or (saved["config"] != asdict(config) or saved["seed"] != seed)
        ):
            raise ValueError("resume data/configuration mismatch")
        optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
        optimizer.load_state_dict(saved["optimizer"])
        torch.set_rng_state(saved["torch_rng"])
        rng.setstate(saved["python_rng"])
        first, curve = saved["next_step"], saved["curve"]
    if steps <= first:
        raise ValueError("steps must exceed saved optimizer boundary")
    started = time.perf_counter()
    model.train()
    for step in range(first, steps):
        batch = rng.sample(rows, 16)
        optimizer.zero_grad(set_to_none=True)
        loss, metrics = batch_loss(model, batch)
        if not torch.isfinite(loss):
            raise ValueError("nonfinite training objective")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        if step == 0 or (step + 1) % 100 == 0 or step + 1 == steps:
            curve.append({"step": step + 1, **metrics})
            print(json.dumps({"variant": variant, "seed": seed, **curve[-1]}), flush=True)
    elapsed = time.perf_counter() - started
    record = {
        "format": FORMAT,
        "boundary": "optimizer-step",
        "config": asdict(config),
        "variant": variant,
        "tokenizer": ByteTokenizer.fingerprint,
        "data_sha256": identity,
        "seed": seed,
        "next_step": steps,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "torch_rng": torch.get_rng_state(),
        "python_rng": rng.getstate(),
        "curve": curve,
        "training_seconds": elapsed,
        "training_peak_process_bytes": peak_bytes(),
        "parameters": sum(p.numel() for p in model.parameters()),
        "batch_size": 16,
        "lr": 0.003,
        "threads": 1,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(record, output)
    summary = {
        key: record[key]
        for key in (
            "variant",
            "seed",
            "next_step",
            "curve",
            "parameters",
            "training_seconds",
            "training_peak_process_bytes",
        )
    }
    summary["sha256"] = sha256_file(output)
    write_json(output.with_suffix(".json"), summary)
    return summary


def evaluate(
    checkpoint: Path,
    directory: Path,
    split: str,
    selector_path: Path | None = None,
    zero_state: bool = False,
) -> dict[str, Any]:
    model, saved = load_integrated(checkpoint)
    torch.set_num_threads(1)
    rows = read_data(directory, split)
    selector = ChatRelevanceSelector(selector_path) if selector_path else None
    if selector and model.variant != "ordinary":
        raise ValueError("external selector diagnostic requires the ordinary decoder")
    checkpoint_hash = sha256_file(checkpoint)
    predictions = []
    started = time.perf_counter()
    for row in rows:
        case_started = time.perf_counter()
        session = IntegratedSession(model, checkpoint_hash)
        events = row["events"]
        if len(events) > model.config.max_records:
            raise ValueError("evaluation world exceeds bounded unroll")
        history_bytes = sum(len(item["text"].encode()) + 1 for item in events)
        selected_ids = list(range(len(events)))
        selector_ms = 0.0
        if selector:
            messages = [{"role": "user", "content": item["text"]} for item in events]
            messages.append({"role": "user", "content": row["query"]})
            selection_started = time.perf_counter()
            ids, _ = selector.select(messages)
            selector_ms = 1000 * (time.perf_counter() - selection_started)
            selected_ids = [index for index in ids if index < len(events)]
        with torch.no_grad():
            for index in selected_ids:
                session.consume(events[index]["text"])
            if zero_state:
                session.state.zero_()
            before = session.state.clone()
            tokens = session.answer(row["query"])
            assert torch.equal(before, session.state)
        answer = ByteTokenizer().decode(tokens)
        query_tokens = len(ByteTokenizer().encode(row["query"]))
        decoded = len(tokens)
        forwarded = session.update_tokens + len(session.local) + query_tokens + decoded
        predictions.append(
            {
                "id": row["id"],
                "category": row["category"],
                "query": row["query"],
                "expected": row["answer"],
                "answer": answer,
                "generated_ids": tokens,
                "correct": answer == row["answer"],
                "unsupported": row["answer"] == "?" and answer != "?",
                "obsolete_answer": bool(row["obsolete"] and answer == row["obsolete"]),
                "history_input_tokens": history_bytes,
                "history_bytes_scanned": history_bytes,
                "selected_prompt_tokens": len(session.local) + query_tokens,
                "memory_update_tokens": session.update_tokens,
                "decoder_steps": decoded,
                "total_forward_token_positions": forwarded,
                "state_bytes": session.state.numel() * session.state.element_size()
                if model.variant == "integrated"
                else 0,
                "memory_update_records": len(selected_ids) if model.variant == "integrated" else 0,
                "memory_slot_update_cells": len(selected_ids)
                * model.config.slots
                * model.config.width
                if model.variant == "integrated"
                else 0,
                "local_bytes": len(session.local),
                "selected_record_ids": selected_ids,
                "selector_ms": selector_ms,
                "response_ms": 1000 * (time.perf_counter() - case_started),
            }
        )
    totals: dict[str, Any] = {
        "cases": len(rows),
        "correct": sum(p["correct"] for p in predictions),
        "unsupported": sum(p["unsupported"] for p in predictions),
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in predictions:
        grouped[item["category"]].append(item)
    totals["categories"] = {
        cat: {"correct": sum(p["correct"] for p in values), "cases": len(values)}
        for cat, values in grouped.items()
    }
    for key in (
        "history_input_tokens",
        "selected_prompt_tokens",
        "memory_update_tokens",
        "total_forward_token_positions",
        "decoder_steps",
        "response_ms",
    ):
        totals[key] = sum(p[key] for p in predictions)
    return {
        "format": "toruk-integrated-eval-v1",
        "split": split,
        "variant": "external-selector-diagnostic"
        if selector
        else "integrated-zero-state"
        if zero_state
        else model.variant,
        "checkpoint_sha256": sha256_file(checkpoint),
        "config": saved["config"],
        "selector_sha256": selector.sha256 if selector else None,
        "data_manifest_sha256": sha256_file(directory / "manifest.json"),
        "seconds": time.perf_counter() - started,
        "peak_process_bytes": peak_bytes(),
        "totals": totals,
        "predictions": predictions,
    }


def file_identity(path: Path) -> str:
    raw = path.read_bytes()
    if path.suffix == ".py":
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def seal(
    directory: Path, checkpoints: list[Path], selector: Path, protocol: Path, output: Path
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("use a fresh freeze path")
    files = [
        Path(__file__),
        Path(__file__).with_name("integrated_memory.py"),
        Path(__file__).with_name("tokenizer.py"),
        Path(__file__).with_name("chat_selector.py"),
        Path(__file__).with_name("data.py"),
        protocol,
        selector,
        *checkpoints,
        directory / "manifest.json",
        *(directory / f"{s}.jsonl" for s in ("train", "dev", "final")),
    ]
    record = {
        "format": "toruk-integrated-freeze-v1",
        "sealed_utc": datetime.now(UTC).isoformat(),
        "files": {
            p.relative_to(Path.cwd()).as_posix()
            if p.is_relative_to(Path.cwd())
            else p.as_posix(): file_identity(p)
            for p in files
        },
        "source_hashing": "Python files normalized to LF; all other files raw bytes",
        "checkpoints": [sha256_file(p) for p in checkpoints],
        "selector_sha256": sha256_file(selector),
        "data_manifest_sha256": sha256_file(directory / "manifest.json"),
    }
    write_json(output, record)
    return record


def verify_seal(freeze: Path, checkpoint: Path, directory: Path, selector: Path | None) -> None:
    frozen = json.loads(freeze.read_text())
    if frozen.get("format") != "toruk-integrated-freeze-v1":
        raise ValueError("invalid final freeze")
    for name, digest in frozen["files"].items():
        if file_identity(Path(name)) != digest:
            raise ValueError(f"freeze mismatch: {name}")
    if sha256_file(checkpoint) not in frozen["checkpoints"]:
        raise ValueError("checkpoint is outside the frozen comparison")
    if sha256_file(directory / "manifest.json") != frozen["data_manifest_sha256"]:
        raise ValueError("evaluation data is outside the frozen comparison")
    if selector and sha256_file(selector) != frozen["selector_sha256"]:
        raise ValueError("selector is outside the frozen comparison")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    data = sub.add_parser("data")
    data.add_argument("--output", type=Path, required=True)
    fit = sub.add_parser("train")
    fit.add_argument("--data", type=Path, required=True)
    fit.add_argument("--output", type=Path, required=True)
    fit.add_argument("--variant", choices=("ordinary", "integrated"), required=True)
    fit.add_argument("--steps", type=int, default=800)
    fit.add_argument("--seed", type=int, default=31)
    fit.add_argument("--width", type=int, default=48)
    fit.add_argument("--resume", type=Path)
    check = sub.add_parser("evaluate")
    check.add_argument("--data", type=Path, required=True)
    check.add_argument("--checkpoint", type=Path, required=True)
    check.add_argument("--split", choices=("train", "dev", "final"), default="dev")
    check.add_argument("--output", type=Path, required=True)
    check.add_argument("--selector", type=Path)
    check.add_argument("--zero-state", action="store_true")
    check.add_argument("--freeze", type=Path)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("--data", type=Path, required=True)
    freeze.add_argument("--checkpoints", type=Path, nargs="+", required=True)
    freeze.add_argument("--selector", type=Path, required=True)
    freeze.add_argument("--protocol", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "data":
        make_data(args.output)
    elif args.command == "train":
        train(
            args.data,
            args.output,
            args.variant,
            args.seed,
            args.steps,
            IntegratedConfig(width=args.width),
            args.resume,
        )
    elif args.command == "freeze":
        seal(args.data, args.checkpoints, args.selector, args.protocol, args.output)
    else:
        if args.output.exists():
            parser.error("use a fresh evaluation output")
        if args.split == "final":
            if args.freeze is None:
                parser.error("final evaluation requires a sealed --freeze record")
            verify_seal(args.freeze, args.checkpoint, args.data, args.selector)
        result = evaluate(args.checkpoint, args.data, args.split, args.selector, args.zero_state)
        write_json(args.output, result)
        print(json.dumps(result["totals"], indent=2))


if __name__ == "__main__":
    main()
