"""Path A: one routing intervention; frozen baseline comparison and raw evidence."""

import argparse
import importlib.metadata
import json
import os
import random
import subprocess
import sys
import threading
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import psutil
import qualify_memory as q
import torch
from torch.nn import functional as F

from toruk_lm.data import sha256_file
from toruk_lm.integrated_memory import (
    IntegratedConfig,
    load_integrated,
    padded,
    text_tokens,
)
from toruk_lm.integrated_study import (
    KEYS,
    VALUES,
    file_identity,
    peak_bytes,
    read_data,
    verify_seal,
)
from toruk_lm.pooled_router import FORMAT, PooledRouterLM, load_pooled
from toruk_lm.tokenizer import ByteTokenizer

OLD = q.OLD
PROTOCOL = Path("docs/research/routing-v2-protocol.md")
METHODS = ("recent", "lexical", "learned", "old", "new", "new_zero")


class MemorySample:
    def __enter__(self):
        self.stop = threading.Event()
        self.samples = []
        self.process = psutil.Process()
        self.thread = threading.Thread(target=self.sample, daemon=True)
        self.thread.start()
        return self

    def sample(self):
        while not self.stop.is_set():
            rss = self.process.memory_info().rss
            self.samples.append(rss)
            if rss > 2 * 1024**3:
                os._exit(86)
            self.stop.wait(0.005)

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()


def loss_for(model, rows):
    config = model.config
    longest = max(len(row["events"]) for row in rows)
    if longest > config.max_records:
        raise ValueError("training world exceeds bounded unroll")
    records, labels = [], []
    for row in rows:
        records += [text_tokens(e["text"], config.record_tokens) for e in row["events"]]
        records += [[1]] * (longest - len(row["events"]))
        labels += [e["address"] for e in row["events"]] + [-100] * (longest - len(row["events"]))
    tokens = padded(records)
    encoded = model.encode(tokens).reshape(len(rows), longest, config.width)
    routing = model.routing_vector(tokens).reshape(len(rows), longest, config.width)
    addresses = model.write_address(routing)
    state = model.initial_state(len(rows))
    for i in range(longest):
        updated = model.routed_update(state, encoded[:, i], routing[:, i])
        active = torch.tensor([i < len(row["events"]) for row in rows])[:, None, None]
        state = torch.where(active, updated, state)
    local = padded(
        [
            ByteTokenizer().encode("\n".join(e["text"] for e in r["events"]) + "\n")[
                -config.local_tokens :
            ]
            for r in rows
        ]
    )
    queries = padded([text_tokens(r["query"], config.query_tokens) for r in rows])
    hidden, read, reads = model.prepare(local, queries, state)
    answers = [ByteTokenizer().encode(r["answer"]) + [2] for r in rows]
    logits, _ = model.decode(padded([[1] + a[:-1] for a in answers]), hidden, read)
    answer_ce = F.cross_entropy(
        logits.reshape(-1, 259), padded(answers).reshape(-1), ignore_index=0
    )
    write_ce = F.cross_entropy(addresses.reshape(-1, 7), torch.tensor(labels))
    read_ce = F.cross_entropy(reads, torch.tensor([r["query_key"] for r in rows]))
    loss = answer_ce + 0.25 * (write_ce + read_ce)
    return loss, {
        "loss": loss.item(),
        "answer_ce": answer_ce.item(),
        "write_ce": write_ce.item(),
        "read_ce": read_ce.item(),
    }


def routes(model, texts, query):
    records = [text_tokens(t, model.config.record_tokens) for t in texts]
    question = text_tokens(query, model.config.query_tokens)
    with torch.no_grad():
        if isinstance(model, PooledRouterLM):
            return model.route_ids(records, question)
        writes = model.write_address(model.encode(padded(records))).argmax(-1).tolist()
        read = int(model.read_address(model.encode(padded([question]))).argmax().item())
        return writes, read


def train(run, seed, steps=800):
    verify_registered(run)
    output = run / "train" / f"new-{seed}.pt"
    if output.exists():
        raise ValueError("checkpoint already exists")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    rng = random.Random(seed)
    rows = read_data(OLD / "data", "train", training=True)
    with MemorySample() as memory:
        model = PooledRouterLM(IntegratedConfig())
        optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
        curve = []
        started = time.perf_counter()
        model.train()
        for step in range(steps):
            batch = rng.sample(rows, 16)
            optimizer.zero_grad(set_to_none=True)
            loss, metrics = loss_for(model, batch)
            if not torch.isfinite(loss):
                raise ValueError("nonfinite objective")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            if step == 0 or (step + 1) % 100 == 0 or step + 1 == steps:
                curve.append({"step": step + 1, **metrics})
                print(seed, curve[-1], flush=True)
        elapsed = time.perf_counter() - started
        record = {
            "format": FORMAT,
            "boundary": "optimizer-step",
            "variant": "integrated",
            "config": asdict(model.config),
            "seed": seed,
            "next_step": steps,
            "tokenizer": ByteTokenizer.fingerprint,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "torch_rng": torch.get_rng_state(),
            "python_rng": rng.getstate(),
            "curve": curve,
            "training_seconds": elapsed,
            "data_sha256": sha256_file(OLD / "data/manifest.json"),
            "parameters": sum(p.numel() for p in model.parameters()),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        torch.save(record, output)
    q.dump(
        output.with_suffix(".json"),
        {
            k: record[k]
            for k in (
                "format",
                "seed",
                "next_step",
                "config",
                "tokenizer",
                "curve",
                "training_seconds",
                "data_sha256",
                "parameters",
            )
        }
        | {
            "sha256": sha256_file(output),
            "sampled_peak_rss": max(memory.samples),
            "peak_process_bytes": peak_bytes(),
        },
    )


def development(run, seed):
    verify_registered(run)
    torch.set_num_threads(1)
    model, _ = load_pooled(run / "train" / f"new-{seed}.pt")
    results = []
    for row in read_data(OLD / "data", "dev"):
        texts = [e["text"] for e in row["events"]]
        answer = q.infer(model, None, texts, row["query"], "integrated", "dev")
        writes, read = routes(model, texts, row["query"])
        results.append(
            {
                "id": row["id"],
                "category": row["category"],
                "expected": row["answer"],
                "answer": answer["answer"],
                "correct": answer["answer"] == row["answer"],
                "read_correct": read == row["query_key"],
                "write_correct": sum(
                    p == e["address"] for p, e in zip(writes, row["events"], strict=True)
                ),
                "write_records": len(writes),
            }
        )
    q.dump(run / "development" / f"new-{seed}.json", results)
    print("Development", seed, "exact", sum(r["correct"] for r in results), "/", len(results))


def worlds():
    rows = []
    for seed in (8101, 8102, 8103):
        rng = random.Random(seed)
        for cat in q.CATS:
            for number in range(8):
                first, kept, other, absent, junk, spare = rng.sample(range(6), 6)
                old, new, valid = rng.sample(VALUES, 3)

                def event(key, value, operation):
                    name, field = KEYS[key]
                    marker = {"set": "Set", "revise": "Change", "claim": "Claim"}[operation]
                    return {
                        "text": f"{name} {value} {field} {marker}.",
                        "key": key,
                        "value": value,
                        "operation": operation,
                        "address": 6 if operation == "claim" else key,
                    }

                base = [
                    event(first, old, "set"),
                    event(kept, valid, "set"),
                    event(other, rng.choice(VALUES), "set"),
                    event(first, new, "revise"),
                ]
                distractors = [
                    event(rng.choice((junk, spare)), rng.choice(VALUES), "set") for _ in range(36)
                ]
                for load in (0, 8, 32):
                    events = base + distractors[: 4 + load]
                    if cat == "ambiguity":
                        events += [event(absent, old, "claim"), event(absent, new, "claim")]
                    targets = (
                        [kept]
                        if cat == "preservation"
                        else [other]
                        if cat == "distant"
                        else [absent]
                        if cat in ("unknown", "ambiguity")
                        else [first, kept]
                        if cat == "multi"
                        else [first]
                    )
                    truth = {}
                    evidence = {}
                    for i, e in enumerate(events):
                        if e["operation"] != "claim":
                            truth[e["key"]] = e["value"]
                            evidence[e["key"]] = i
                    questions = []
                    for key in targets:
                        name, field = KEYS[key]
                        questions.append(
                            {
                                "query": f"{field}? {name}'s is What",
                                "expected": truth.get(key, "?"),
                                "key": key,
                                "evidence": [evidence[key]] if key in evidence else [],
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


def registered_files():
    return [
        Path(__file__).relative_to(Path.cwd()),
        Path("scripts/qualify_memory.py"),
        Path("tests/test_pooled_router.py"),
        PROTOCOL,
        Path("pyproject.toml"),
        *Path("src/toruk_lm").glob("*.py"),
        OLD / "freeze.json",
        q.SELECTOR,
        *(OLD / "data" / f"{s}.jsonl" for s in ("train", "dev", "final")),
        *(q.checkpoint_for(m, s) for m in ("recent", "integrated") for s in (31, 47)),
    ]


def register(run):
    verify_seal(OLD / "freeze.json", q.checkpoint_for("integrated", 31), OLD / "data", q.SELECTOR)
    q.verify(Path("artifacts/qualification-v1-20261103"))
    run.mkdir(parents=True, exist_ok=False)
    q.dump(
        run / "registration.json",
        {
            "utc": datetime.now(UTC).isoformat(),
            "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "files": {p.as_posix(): file_identity(p) for p in registered_files()},
            "config": {
                "steps": 800,
                "batch": 16,
                "lr": 0.003,
                "seeds": [31, 47],
                "evaluation_seeds": [8101, 8102, 8103],
                "device": "cpu",
                "threads": 1,
            },
            "tokenizer": ByteTokenizer.fingerprint,
            "python": sys.version,
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("torch", "psutil", "pytest", "ruff", "mypy", "build", "transformers")
            },
            "host": {
                "logical_cpus": psutil.cpu_count(),
                "ram": psutil.virtual_memory().total,
                "available_ram": psutil.virtual_memory().available,
            },
            "prior_evidence": "qualification-v1 useful gates FAIL; original negatives retained",
        },
    )
    (run / "initial-status.txt").write_text(
        subprocess.check_output(["git", "status", "--short"], text=True)
    )
    print("Registered sources and protocol; final worlds not generated")


def verify_registered(run):
    for name, digest in json.loads((run / "registration.json").read_text())["files"].items():
        if file_identity(Path(name)) != digest:
            raise ValueError(f"registration drift: {name}")


def freeze(run):
    verify_registered(run)
    rows = worlds()
    seen = set()
    for row in rows:
        identity = (
            tuple(e["text"] for e in row["events"]),
            tuple(a["query"] for a in row["questions"]),
        )
        if identity in seen:
            raise ValueError("duplicate final world")
        seen.add(identity)
    historical = set()
    for split in ("train", "dev", "final"):
        for r in read_data(OLD / "data", split):
            historical.add((tuple(e["text"] for e in r["events"]), r["query"]))
    for r in json.loads(Path("artifacts/qualification-v1-20261103/final.json").read_text()):
        for question in r["questions"]:
            historical.add((tuple(e["text"] for e in r["events"]), question["query"]))
    if any(
        (tuple(e["text"] for e in r["events"]), a["query"]) in historical
        for r in rows
        for a in r["questions"]
    ):
        raise ValueError("historical final overlap")
    q.dump(run / "final.json", rows)
    files = [
        run / "registration.json",
        run / "final.json",
        *(run / "train" / f"new-{s}.pt" for s in (31, 47)),
        *(run / "development" / f"new-{s}.json" for s in (31, 47)),
    ]
    q.dump(
        run / "freeze.json",
        {
            "utc": datetime.now(UTC).isoformat(),
            "files": {p.as_posix(): file_identity(p) for p in files},
            "decision": "Fixed 800-step checkpoints; no metric-guided changes; retain dev failures",
        },
    )
    registration = json.loads((run / "registration.json").read_text())
    for name in registration["files"]:
        path = Path(name)
        if path.suffix in (".py", ".md", ".toml"):
            target = run / "source" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    print("Frozen", len(rows), "worlds; no final answers generated")


def verify_final(run):
    verify_registered(run)
    for name, digest in json.loads((run / "freeze.json").read_text())["files"].items():
        if file_identity(Path(name)) != digest:
            raise ValueError(f"final drift: {name}")


def evaluate(run, method, seed):
    verify_final(run)
    output = run / "raw" / f"{method}-{seed}.json"
    if output.exists():
        raise ValueError("evaluation already exists")
    torch.set_num_threads(1)
    started = time.perf_counter()
    diagnostic_seconds = 0.0
    with MemorySample() as memory:
        checkpoint = (
            run / "train" / f"new-{seed}.pt"
            if method.startswith("new")
            else q.checkpoint_for("integrated" if method == "old" else method, seed)
        )
        model, _ = (
            load_pooled(checkpoint) if method.startswith("new") else load_integrated(checkpoint)
        )
        selector = q.ChatRelevanceSelector(q.SELECTOR) if method == "learned" else None
        mode = (
            "zero" if method == "new_zero" else "integrated" if method in ("old", "new") else method
        )
        predictions = []
        for row in json.loads((run / "final.json").read_text()):
            texts = [e["text"] for e in row["events"]]
            answers = []
            for question in row["questions"]:
                answer = q.infer(model, selector, texts, question["query"], mode, "frozen")
                answer.update(question)
                answer["correct"] = answer["answer"] == question["expected"]
                answer["unsupported"] = question["expected"] == "?" and answer["answer"] != "?"
                answer["evidence_suffix_exposed"] = all(
                    i in answer["suffix_record_ids"] for i in question["evidence"]
                )
                answer["evidence_ingested"] = all(
                    i in answer["selected_record_ids"] for i in question["evidence"]
                )
                answer["extra_routing_embedding_positions"] = (
                    answer["update_tokens"] + len(question["query"].encode())
                    if method.startswith("new")
                    else 0
                )
                diagnostic_start = time.perf_counter()
                if method in ("old", "new", "new_zero"):
                    writes, read = routes(model, texts, question["query"])
                    answer["read_predicted"] = read
                    answer["read_correct"] = read == question["key"]
                    answer["write_predictions"] = writes
                    answer["write_correct"] = sum(
                        p == e["address"] for p, e in zip(writes, row["events"], strict=True)
                    )
                    answer["write_records"] = len(writes)
                diagnostic_seconds += time.perf_counter() - diagnostic_start
                answers.append(answer)
            predictions.append(
                {k: row[k] for k in ("id", "eval_seed", "category", "load")}
                | {"answers": answers, "correct": all(a["correct"] for a in answers)}
            )
    q.dump(
        output,
        {
            "method": method,
            "seed": seed,
            "checkpoint_sha256": file_identity(checkpoint),
            "freeze_sha256": file_identity(run / "freeze.json"),
            "process_seconds": time.perf_counter() - started,
            "diagnostic_seconds": diagnostic_seconds,
            "sampled_peak_rss": max(memory.samples),
            "samples": len(memory.samples),
            "high_water_bytes": peak_bytes(),
            "predictions": predictions,
        },
    )
    print(method, seed, "exact load0", sum(p["correct"] for p in predictions if p["load"] == 0))


def analyze(run):
    verify_final(run)
    results = {}
    clusters = {}
    examples = {}
    for method in METHODS:
        results[method] = {}
        clusters[method] = defaultdict(list)
        for seed in (31, 47):
            raw = json.loads((run / "raw" / f"{method}-{seed}.json").read_text())
            current = {
                "sampled_peak_rss": raw["sampled_peak_rss"],
                "process_seconds": raw["process_seconds"],
            }
            for load in (0, 8, 32):
                rows = [p for p in raw["predictions"] if p["load"] == load]
                cell = q.summarize(rows)
                answers = [a for p in rows for a in p["answers"]]
                known = [a for a in answers if a["evidence"]]
                cell.update(
                    evidence_queries=len(known),
                    evidence_suffix_exposed=sum(a["evidence_suffix_exposed"] for a in known),
                    evidence_ingested=sum(a["evidence_ingested"] for a in known),
                    extra_routing_embedding_positions=sum(
                        a["extra_routing_embedding_positions"] for a in answers
                    ),
                )
                if method in ("old", "new", "new_zero"):
                    cell.update(
                        read_correct=sum(a["read_correct"] for a in answers),
                        read_queries=len(answers),
                        write_correct=sum(a["write_correct"] for a in answers),
                        write_records=sum(a["write_records"] for a in answers),
                    )
                current[str(load)] = cell
                if load == 0:
                    for p in rows:
                        clusters[method][p["id"]].append(int(p["correct"]))
            current["eval_seeds"] = {
                str(s): q.summarize(
                    [p for p in raw["predictions"] if p["load"] == 0 and p["eval_seed"] == s]
                )
                for s in (8101, 8102, 8103)
            }
            results[method][str(seed)] = current
    uncertainty = {}
    for method in METHODS:
        values = {i: sum(v) / len(v) for i, v in clusters[method].items()}
        uncertainty[method] = {"accuracy95": q.bootstrap(values)}
        for baseline in ("recent", "lexical", "old"):
            diffs = {i: value - sum(clusters[baseline][i]) / 2 for i, value in values.items()}
            uncertainty[method][f"difference_vs_{baseline}95"] = q.bootstrap(diffs)
    # Route differences use world clusters too; retain the two read/write denominators.
    for metric in ("read", "write"):
        delta = defaultdict(list)
        for seed in (31, 47):
            old = {
                p["id"]: p
                for p in json.loads((run / "raw" / f"old-{seed}.json").read_text())["predictions"]
                if p["load"] == 0
            }
            new = [
                p
                for p in json.loads((run / "raw" / f"new-{seed}.json").read_text())["predictions"]
                if p["load"] == 0
            ]
            for p in new:

                def value(row, metric=metric):
                    answers = row["answers"]
                    return (
                        sum(a["read_correct"] for a in answers) / len(answers)
                        if metric == "read"
                        else sum(a["write_correct"] for a in answers)
                        / sum(a["write_records"] for a in answers)
                    )

                delta[p["id"]].append(value(p) - value(old[p["id"]]))
        uncertainty[f"target_{metric}_world_macro_difference95"] = q.bootstrap(
            {i: sum(v) / 2 for i, v in delta.items()}
        )
    for seed in (31, 47):
        old = {
            p["id"]: p
            for p in json.loads((run / "raw" / f"old-{seed}.json").read_text())["predictions"]
            if p["load"] == 0
        }
        new = [
            p
            for p in json.loads((run / "raw" / f"new-{seed}.json").read_text())["predictions"]
            if p["load"] == 0
        ]
        examples[str(seed)] = {
            name: [{"old": old[p["id"]], "new": p} for p in new if predicate(p, old[p["id"]])][:5]
            for name, predicate in {
                "gains": lambda n, o: n["correct"] and not o["correct"],
                "regressions": lambda n, o: o["correct"] and not n["correct"],
                "unsupported": lambda n, o: any(a["unsupported"] for a in n["answers"]),
                "known_failures": lambda n, o: (
                    not n["correct"] and all(a["expected"] != "?" for a in n["answers"])
                ),
            }.items()
        }
    q.dump(run / "summary.json", {"methods": results, "uncertainty": uncertainty})
    q.dump(run / "examples.json", examples)
    lines = [
        "| Method | Exact /168 seed31/47 | Known /120 | Unsupported /48 | Selected tokens "
        "| Forward positions | Extra routing positions | Latency ms | RSS MiB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in results.items():
        cols = [method]
        for key in (
            "correct",
            "known_correct",
            "unsupported",
            "selected_tokens",
            "forward_positions",
            "extra_routing_embedding_positions",
            "response_ms",
        ):
            cols.append(" / ".join(f"{seeds[str(s)]['0'][key]:.1f}" for s in (31, 47)))
        cols.append(
            " / ".join(f"{seeds[str(s)]['sampled_peak_rss'] / 1024**2:.1f}" for s in (31, 47))
        )
        lines.append("| " + " | ".join(cols) + " |")
    (run / "table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("register", "train", "development", "freeze", "evaluate", "run", "analyze"),
    )
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=(31, 47))
    parser.add_argument("--method", choices=METHODS)
    args = parser.parse_args()
    if args.command == "register":
        register(args.run)
    elif args.command == "freeze":
        freeze(args.run)
    elif args.command == "analyze":
        analyze(args.run)
    elif args.command in ("train", "development", "evaluate"):
        if args.seed is None:
            parser.error("--seed required")
        if args.command == "train":
            train(args.run, args.seed)
        elif args.command == "development":
            development(args.run, args.seed)
        else:
            if args.method is None:
                parser.error("--method required")
            evaluate(args.run, args.method, args.seed)
    else:
        for index, seed in enumerate((31, 47)):
            for method in METHODS[index:] + METHODS[:index]:
                command = [
                    sys.executable,
                    "scripts/check.py",
                    "--timeout",
                    "180",
                    "--output-dir",
                    str(args.run / "checks"),
                    f"final-{method}-{seed}",
                    "--",
                    sys.executable,
                    __file__,
                    "evaluate",
                    "--run",
                    str(args.run),
                    "--method",
                    method,
                    "--seed",
                    str(seed),
                ]
                if subprocess.run(command, timeout=195).returncode:
                    raise RuntimeError(f"failed evaluation {method}-{seed}")


if __name__ == "__main__":
    main()
