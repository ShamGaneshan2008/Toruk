"""Frozen-checkpoint independent qualification; never fits on final answers."""

import argparse
import importlib.metadata
import json
import random
import re
import subprocess
import sys
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import psutil
import torch

from toruk_lm.chat_selector import ChatRelevanceSelector
from toruk_lm.integrated_memory import IntegratedSession, load_integrated, text_tokens
from toruk_lm.integrated_study import KEYS, VALUES, file_identity, peak_bytes, verify_seal
from toruk_lm.tokenizer import ByteTokenizer

ROOT = Path(__file__).resolve().parents[1]
OLD = Path("artifacts/integrated-memory-v1-20261102")
SELECTOR = Path("artifacts/chat-selector-v2-20261101/selector.json")
PROTOCOL = Path("docs/research/qualification-v1-protocol.md")
METHODS = (
    "recent",
    "lexical",
    "learned",
    "position",
    "integrated",
    "zero",
    "no_correction",
    "no_preservation",
    "half_capacity",
)
CATS = ("correction", "preservation", "distant", "ambiguity", "distraction", "multi", "unknown")


def dump(path, value):
    if path.exists():
        raise ValueError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def event_record(key, value, operation="set"):
    name, field = KEYS[key]
    marker = {"set": "Fact", "revise": "Amend", "claim": "Rumor"}[operation]
    return {
        "text": f"{marker} {name}: {field}={value}.",
        "key": key,
        "value": value,
        "operation": operation,
    }


def make_worlds():
    rows = []
    for seed in (7101, 7102, 7103):
        rng = random.Random(seed)
        for cat in CATS:
            for number in range(8):
                first, kept, other, absent, junk, spare = rng.sample(range(6), 6)
                old, new, valid = rng.sample(VALUES, 3)
                base = [
                    event_record(first, old),
                    event_record(kept, valid),
                    event_record(other, rng.choice(VALUES)),
                    event_record(first, new, "revise"),
                ]
                # One fixed distractor stream; load changes only its prefix length.
                extras = []
                for _ in range(36):
                    name, field = KEYS[rng.choice((junk, spare))]
                    extras.append(
                        {
                            "text": f"Fact {name}: {field}={rng.choice(VALUES)}.",
                            "key": KEYS.index((name, field)),
                            "operation": "set",
                        }
                    )
                for load in (0, 8, 32):
                    events = list(base) + extras[: 4 + load]
                    if cat == "ambiguity":
                        events += [
                            event_record(absent, old, "claim"),
                            event_record(absent, new, "claim"),
                        ]
                    targets = (
                        [kept]
                        if cat == "preservation"
                        else [other]
                        if cat == "distant"
                        else [absent]
                        if cat in ("ambiguity", "unknown")
                        else [first, kept]
                        if cat == "multi"
                        else [first]
                    )
                    truth = {first: new, kept: valid, other: base[2]["value"]}
                    questions = []
                    for target in targets:
                        name, field = KEYS[target]
                        questions.append(
                            {
                                "query": f"Give {field} for {name}.",
                                "expected": truth.get(target, "?"),
                            }
                        )
                    rows.append(
                        {
                            "id": f"{seed}-{cat}-{number}",
                            "eval_seed": seed,
                            "category": cat,
                            "load": load,
                            "events": events,
                            "questions": questions,
                        }
                    )
    return rows


def choose(texts, query, method, selector):
    if method not in ("lexical", "learned", "position"):
        return list(range(len(texts)))
    recent = set(range(max(0, len(texts) - 2), len(texts)))
    if method == "learned":
        ids, _ = selector.select([{"role": "user", "content": t} for t in texts + [query]])
        return [i for i in ids if i < len(texts)]
    candidates = range(max(0, len(texts) - 2))
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    ranked = sorted(
        candidates,
        key=lambda i: (
            len(terms & set(re.findall(r"[a-z0-9]+", texts[i].lower())))
            if method == "lexical"
            else 0,
            i,
        ),
        reverse=True,
    )
    return sorted(recent | set(ranked[:2]))


def checkpoint_for(method, seed):
    variant = "ordinary" if method in METHODS[:4] else "integrated"
    return OLD / "train" / f"{variant}-{seed}.pt"


def freeze(run):
    # Refuse drift in the original sealed experiment before deriving evidence.
    verify_seal(OLD / "freeze.json", checkpoint_for("integrated", 31), OLD / "data", SELECTOR)
    run.mkdir(parents=True, exist_ok=False)
    rows = make_worlds()
    identities = set()
    historical = set()
    for split in ("train", "dev", "final"):
        for line in (OLD / "data" / f"{split}.jsonl").read_text().splitlines():
            row = json.loads(line)
            historical.add((tuple(e["text"] for e in row["events"]), row["query"]))
    for row in rows:
        identity = (
            tuple(e["text"] for e in row["events"]),
            tuple(q["query"] for q in row["questions"]),
        )
        if identity in identities:
            raise ValueError("duplicate final world")
        identities.add(identity)
        if any((identity[0], q["query"]) in historical for q in row["questions"]):
            raise ValueError("historical overlap")
    dump(run / "final.json", rows)
    files = [
        Path(__file__).relative_to(ROOT),
        PROTOCOL,
        SELECTOR,
        OLD / "freeze.json",
        run / "final.json",
        Path("tests/test_qualification.py"),
        Path("pyproject.toml"),
    ]
    files += list(Path("src/toruk_lm").glob("*.py"))
    files += [checkpoint_for(m, s) for s in (31, 47) for m in ("recent", "integrated")]
    files += [OLD / "data" / f"{split}.jsonl" for split in ("train", "dev", "final")]
    files += [OLD / "train" / f"{v}-{s}.json" for v in ("ordinary", "integrated") for s in (31, 47)]
    frozen = {
        "format": "toruk-qualification-v1",
        "utc": datetime.now(UTC).isoformat(),
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "files": {p.as_posix(): file_identity(p) for p in files},
        "python": sys.version,
        "packages": {
            p: importlib.metadata.version(p)
            for p in ("torch", "psutil", "pytest", "ruff", "mypy", "build", "transformers")
        },
        "training": "existing seeds 31,47; no new optimization",
        "historical_overlap": 0,
        "worlds_including_stress": len(rows),
    }
    dump(run / "freeze.json", frozen)
    for p in files:
        if p.suffix in (".py", ".md", ".toml"):
            target = run / "source" / p
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
    (run / "initial-status.txt").write_text(
        subprocess.check_output(["git", "status", "--short"], text=True), encoding="utf-8"
    )
    (run / "branch-graph.txt").write_text(
        subprocess.check_output(
            ["git", "log", "--graph", "--oneline", "--decorate", "-20", "--all"], text=True
        ),
        encoding="utf-8",
    )
    print("Frozen", len(rows), "worlds; no predictions generated")


def verify(run):
    frozen = json.loads((run / "freeze.json").read_text())
    if frozen["format"] != "toruk-qualification-v1":
        raise ValueError("wrong freeze format")
    for name, expected in frozen["files"].items():
        if file_identity(Path(name)) != expected:
            raise ValueError(f"freeze mismatch: {name}")


def infer(model, selector, texts, query, method, checkpoint_hash):
    start = time.perf_counter()
    ids = choose(texts, query, method, selector)
    session = IntegratedSession(model, checkpoint_hash)
    update_records = 0
    with torch.no_grad():
        for i in ids:
            if method == "no_correction" and texts[i].startswith("Amend "):
                tokens = text_tokens(texts[i], model.config.record_tokens)
                session.local = (session.local + tokens + [13])[-model.config.local_tokens :]
            else:
                if method == "no_preservation":
                    session.state.zero_()
                session.consume(texts[i])
                update_records += model.variant == "integrated"
                if method == "half_capacity":
                    session.state[:, 3:] = 0
        if method == "zero":
            session.state.zero_()
        generated = session.answer(query)
    elapsed = 1000 * (time.perf_counter() - start)
    query_tokens = len(ByteTokenizer().encode(query))
    remaining = model.config.local_tokens
    contributing = []
    for i in reversed(ids):
        if remaining <= 0:
            break
        contributing.append(i)
        remaining -= len(texts[i].encode()) + 1
    state_bytes = 1152 if model.variant == "integrated" else 0
    return {
        "answer": ByteTokenizer().decode(generated),
        "generated_ids": generated,
        "selected_record_ids": ids,
        "suffix_record_ids": sorted(contributing),
        "history_tokens_scanned": sum(len(t.encode()) + 1 for t in texts),
        "selected_tokens": len(session.local) + query_tokens,
        "update_tokens": session.update_tokens,
        "forward_positions": session.update_tokens
        + len(session.local)
        + query_tokens
        + len(generated),
        "update_cells": update_records * 6 * 48,
        "allocated_state_bytes": state_bytes,
        "effective_state_bytes": state_bytes // 2 if method == "half_capacity" else state_bytes,
        "response_ms": elapsed,
    }


def evaluate(run, method, seed):
    verify(run)
    output = run / "raw" / f"{method}-{seed}.json"
    if output.exists():
        raise ValueError("use a fresh evaluation output")
    stop = threading.Event()
    samples = []
    process = psutil.Process()

    def sample():
        while not stop.is_set():
            rss = process.memory_info().rss
            samples.append(rss)
            if rss > 2 * 1024**3:
                # The parent also retains failure/timeout logs.
                import os

                os._exit(86)
            stop.wait(0.005)

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    started = time.perf_counter()
    try:
        torch.set_num_threads(1)
        checkpoint = checkpoint_for(method, seed)
        model, _ = load_integrated(checkpoint)
        selector = ChatRelevanceSelector(SELECTOR) if method == "learned" else None
        digest = file_identity(checkpoint)
        predictions = []
        for row in json.loads((run / "final.json").read_text()):
            samples.append(process.memory_info().rss)
            texts = [e["text"] for e in row["events"]]
            answers = [
                infer(model, selector, texts, q["query"], method, digest) for q in row["questions"]
            ]
            for answer, question in zip(answers, row["questions"], strict=True):
                answer.update(question)
                answer["correct"] = answer["answer"] == question["expected"]
                answer["unsupported"] = question["expected"] == "?" and answer["answer"] != "?"
            predictions.append(
                {k: row[k] for k in ("id", "eval_seed", "category", "load")}
                | {"answers": answers, "correct": all(a["correct"] for a in answers)}
            )
            samples.append(process.memory_info().rss)
    finally:
        stop.set()
        sampler.join()
    dump(
        output,
        {
            "method": method,
            "training_seed": seed,
            "checkpoint_sha256": digest,
            "freeze_sha256": file_identity(run / "freeze.json"),
            "sampled_peak_rss": max(samples),
            "rss_samples": len(samples),
            "process_high_water_bytes": peak_bytes(),
            "seconds": time.perf_counter() - started,
            "predictions": predictions,
        },
    )
    print(
        method,
        seed,
        "worlds",
        len(predictions),
        "correct load0",
        sum(p["correct"] for p in predictions if p["load"] == 0),
    )


def summarize(predictions):
    answers = [a for p in predictions for a in p["answers"]]
    known = [p for p in predictions if all(a["expected"] != "?" for a in p["answers"])]
    unknown = [a for a in answers if a["expected"] == "?"]
    result = {
        "worlds": len(predictions),
        "correct": sum(p["correct"] for p in predictions),
        "accuracy": sum(p["correct"] for p in predictions) / len(predictions),
        "known_correct": sum(p["correct"] for p in known),
        "known_worlds": len(known),
        "unsupported": sum(a["unsupported"] for a in unknown),
        "unknown_queries": len(unknown),
    }
    for key in (
        "history_tokens_scanned",
        "selected_tokens",
        "update_tokens",
        "forward_positions",
        "update_cells",
        "response_ms",
    ):
        result[key] = sum(a[key] for a in answers)
    result["categories"] = {
        cat: {
            "correct": sum(p["correct"] for p in predictions if p["category"] == cat),
            "worlds": sum(p["category"] == cat for p in predictions),
        }
        for cat in CATS
    }
    return result


def bootstrap(values):
    """Values are paired world clusters, already averaged over training seeds."""
    groups = defaultdict(list)
    for identity, value in values.items():
        parts = identity.split("-")
        groups[tuple(parts[:2])].append(value)
    rng = random.Random(9301)
    estimates = sorted(
        sum(rng.choice(group) for group in groups.values() for _ in group) / len(values)
        for _ in range(2000)
    )
    return [estimates[49], estimates[1949]]


def analyze(run):
    verify(run)
    methods = {}
    paired = {}
    for method in METHODS:
        raw = [json.loads((run / "raw" / f"{method}-{s}.json").read_text()) for s in (31, 47)]
        methods[method] = {
            str(s): {
                str(load): summarize([p for p in r["predictions"] if p["load"] == load])
                for load in (0, 8, 32)
            }
            | {
                "sampled_peak_rss": r["sampled_peak_rss"],
                "process_high_water_bytes": r["process_high_water_bytes"],
            }
            for s, r in zip((31, 47), raw, strict=True)
        }
        paired[method] = {
            p["id"]: sum(
                int(
                    next(q for q in r["predictions"] if q["id"] == p["id"] and q["load"] == 0)[
                        "correct"
                    ]
                )
                for r in raw
            )
            / 2
            for p in raw[0]["predictions"]
            if p["load"] == 0
        }
    uncertainty = {}
    for method in METHODS:
        values = paired[method]
        uncertainty[method] = {"accuracy_95": bootstrap(values)}
        for baseline in ("recent", "lexical"):
            differences = {i: value - paired[baseline][i] for i, value in values.items()}
            uncertainty[method][f"difference_vs_{baseline}_95"] = bootstrap(differences)
    dump(
        run / "summary.json",
        {
            "methods": methods,
            "uncertainty": uncertainty,
            "note": "Conditional on two training seeds; clustered worlds, load 0",
        },
    )
    lines = [
        "| Method | Accuracy seed31/47 | Unsupported /48 seed31/47 | Selected tokens "
        "seed31/47 | Forward positions seed31/47 | Latency ms seed31/47 | Sampled RSS MiB "
        "seed31/47 | Accuracy 95% |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        parts = [method]
        for key in (
            "correct",
            "unsupported",
            "selected_tokens",
            "forward_positions",
            "response_ms",
        ):
            parts.append(" / ".join(f"{seeds[str(s)]['0'][key]:.1f}" for s in (31, 47)))
        parts.append(
            " / ".join(f"{seeds[str(s)]['sampled_peak_rss'] / 1024**2:.1f}" for s in (31, 47))
        )
        parts.append("–".join(f"{v:.3f}" for v in uncertainty[method]["accuracy_95"]))
        lines.append("| " + " | ".join(parts) + " |")
    (run / "table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "evaluate", "analyze", "run"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--method", choices=METHODS)
    parser.add_argument("--seed", type=int, choices=(31, 47))
    args = parser.parse_args()
    if args.command == "freeze":
        freeze(args.run)
    elif args.command == "evaluate":
        if args.method is None or args.seed is None:
            parser.error("evaluate requires --method and --seed")
        evaluate(args.run, args.method, args.seed)
    elif args.command == "analyze":
        analyze(args.run)
    else:
        for offset, seed in enumerate((31, 47)):
            order = METHODS[offset:] + METHODS[:offset]
            for method in order:
                command = [
                    sys.executable,
                    "scripts/qualify_memory.py",
                    "evaluate",
                    "--run",
                    str(args.run),
                    "--method",
                    method,
                    "--seed",
                    str(seed),
                ]
                wrapped = [
                    sys.executable,
                    "scripts/check.py",
                    "--timeout",
                    "180",
                    "--output-dir",
                    str(args.run / "checks"),
                    f"final-{method}-{seed}",
                    "--",
                    *command,
                ]
                if subprocess.run(wrapped, timeout=195).returncode:
                    raise RuntimeError(f"failed cell {method}-{seed}; retain evidence")


if __name__ == "__main__":
    main()
