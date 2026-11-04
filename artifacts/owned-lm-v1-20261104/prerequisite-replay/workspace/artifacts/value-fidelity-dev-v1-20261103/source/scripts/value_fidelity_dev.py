"""Fixed-budget training-rendering intervention; development only, no final split."""

import argparse
import copy
import importlib.metadata
import json
import random
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import study_routing_v2 as study
import torch

from toruk_lm.integrated_memory import IntegratedConfig, load_integrated
from toruk_lm.integrated_study import KEYS, file_identity, make_case, peak_bytes, read_data
from toruk_lm.pooled_router import FORMAT, PooledRouterLM, load_pooled
from toruk_lm.tokenizer import ByteTokenizer

Row = dict[str, Any]
RECIPE = "value-fidelity-dev-v1"
PROTOCOL = Path("docs/research/value-fidelity-dev-v1-protocol.md")
TRAIN_ORDERS = (
    ("o", "n", "f", "v"),
    ("n", "o", "v", "f"),
    ("f", "v", "o", "n"),
    ("f", "n", "v", "o"),
)
DEV_ORDERS = (("v", "f", "n", "o"), ("n", "f", "o", "v"))
TRAIN_QUERIES = (
    ("w", "i", "n", "f"),
    ("n", "w", "f", "i"),
    ("f", "i", "w", "n"),
    ("i", "n", "f", "w"),
)
DEV_QUERIES = (("w", "n", "i", "f"), ("i", "f", "n", "w"))
METHODS = ("recent", "lexical", "old", "augmented", "zero")
OLD = Path("artifacts/routing-v2-20261103")


def record_text(event: Row, order: tuple[str, ...]) -> str:
    name, field = KEYS[event["key"]]
    atoms = {
        "o": {"set": "Set", "revise": "Change", "claim": "Claim"}[event["operation"]],
        "n": name,
        "f": field,
        "v": event["value"],
    }
    return " ".join(atoms[key] for key in order) + "."


def query_text(key: int, order: tuple[str, ...]) -> str:
    name, field = KEYS[key]
    atoms = {"w": "What", "i": "is", "n": name + "'s", "f": field + "?"}
    return " ".join(atoms[key] for key in order)


def augment(row: Row, rng: random.Random) -> Row:
    result = copy.deepcopy(row)
    for event in result["events"]:
        event["text"] = record_text(event, rng.choice(TRAIN_ORDERS))
    result["query"] = query_text(result["query_key"], rng.choice(TRAIN_QUERIES))
    return result


def make_development() -> list[Row]:
    worlds = []
    seen = set()
    mapping = {
        "distant": "long_recall",
        "ambiguity": "conflict",
        "distraction": "correction",
        "multi": "preservation",
    }
    for seed in (9101, 9102, 9103):
        rng = random.Random(seed)
        for category in study.q.CATS:
            for number in range(8):
                row = make_case("train", mapping.get(category, category), number, rng)
                events = row["events"]
                for event in events:
                    event["text"] = record_text(event, rng.choice(DEV_ORDERS))
                corrected = next(e["key"] for e in events if e["operation"] == "revise")
                targets = (
                    [corrected, row["query_key"]]
                    if category == "multi"
                    else [events[2]["key"]]
                    if category == "distant"
                    else [row["query_key"]]
                )
                truth, evidence = {}, {}
                for i, event in enumerate(events):
                    if event["operation"] != "claim":
                        truth[event["key"]] = event["value"]
                        evidence[event["key"]] = i
                questions = [
                    {
                        "query": query_text(key, rng.choice(DEV_QUERIES)),
                        "key": key,
                        "expected": truth.get(key, "?"),
                        "evidence": [evidence[key]] if key in evidence else [],
                    }
                    for key in targets
                ]
                identity = (tuple(e["text"] for e in events), tuple(q["query"] for q in questions))
                if identity in seen:
                    raise ValueError("duplicate development world")
                seen.add(identity)
                worlds.append(
                    {
                        "id": f"{seed}-{category}-{number}",
                        "category": category,
                        "eval_seed": seed,
                        "load": 0,
                        "role": "development-only",
                        "events": events,
                        "questions": questions,
                    }
                )
    return worlds


def source_paths() -> list[Path]:
    return [
        Path(__file__).relative_to(Path.cwd()),
        PROTOCOL,
        Path("tests/test_value_fidelity_dev.py"),
        Path("scripts/study_routing_v2.py"),
        Path("scripts/qualify_memory.py"),
        Path("pyproject.toml"),
        *Path("src/toruk_lm").glob("*.py"),
        study.q.OLD / "data/manifest.json",
        study.q.OLD / "data/train.jsonl",
        *(OLD / "train" / f"new-{s}.pt" for s in (31, 47)),
        *(study.q.checkpoint_for("recent", s) for s in (31, 47)),
    ]


def register(run: Path) -> None:
    study.verify_final(OLD)
    run.mkdir(parents=True, exist_ok=False)
    study.q.dump(
        run / "development.json", {"role": "development-only", "worlds": make_development()}
    )
    paths = source_paths() + [run / "development.json"]
    study.q.dump(
        run / "registration.json",
        {
            "recipe": RECIPE,
            "utc": datetime.now(UTC).isoformat(),
            "files": {p.as_posix(): file_identity(p) for p in paths},
            "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "config": {
                "steps": 800,
                "batch_size": 16,
                "lr": 0.003,
                "seeds": [31, 47],
                "augmentation_seed_offset": 200000,
                "threads": 1,
                "timeout_seconds": 180,
                "rss_limit_bytes": 2 * 1024**3,
                "final_split": "not generated or opened",
            },
            "python": sys.version,
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("torch", "psutil", "pytest", "mypy", "ruff", "transformers", "build")
            },
        },
    )
    for path in paths:
        if path.suffix in (".py", ".md", ".toml"):
            target = run / "source" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    (run / "initial-status.txt").write_text(
        subprocess.check_output(["git", "status", "--short"], text=True)
    )
    print("Registered", len(make_development()), "development worlds; no final split")


def verify(run: Path, *, models: bool = False) -> Row:
    record = json.loads((run / "registration.json").read_text())
    if record["recipe"] != RECIPE:
        raise ValueError("wrong training recipe")
    for name, digest in record["files"].items():
        if file_identity(Path(name)) != digest:
            raise ValueError(f"registered input drift: {name}")
    development_hashes = [
        digest for name, digest in record["files"].items() if Path(name).name == "development.json"
    ]
    if (
        len(development_hashes) != 1
        or file_identity(run / "development.json") != development_hashes[0]
    ):
        raise ValueError("consumed development data differs from registration")
    if models:
        seal = json.loads((run / "models.json").read_text())
        if seal["registration_sha256"] != file_identity(run / "registration.json"):
            raise ValueError("model seal belongs to a different registration")
        for name, digest in seal["files"].items():
            actual = run / name
            if file_identity(actual) != digest:
                raise ValueError(f"consumed checkpoint drift: {actual}")
    return record


def train(run: Path, seed: int) -> None:
    registration = verify(run)
    output = run / "train" / f"augmented-{seed}.pt"
    if output.exists():
        raise ValueError("checkpoint already exists")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)
    world_rng, render_rng = random.Random(seed), random.Random(seed + 200000)
    rows = read_data(study.q.OLD / "data", "train", training=True)
    training_history_tokens = recurrent_positions = routing_positions = 0
    with study.MemorySample() as memory:
        model = PooledRouterLM(IntegratedConfig())
        optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
        curve = []
        started = time.perf_counter()
        model.train()
        for step in range(800):
            batch = [augment(row, render_rng) for row in world_rng.sample(rows, 16)]
            longest = max(len(r["events"]) for r in batch)
            record_size = max(len(e["text"].encode()) for r in batch for e in r["events"])
            query_size = max(len(r["query"].encode()) for r in batch)
            answer_size = max(len(r["answer"].encode()) + 1 for r in batch)
            local_size = max(
                min(96, len(("\n".join(e["text"] for e in r["events"]) + "\n").encode()))
                for r in batch
            )
            recurrent_positions += 16 * (
                longest * record_size + local_size + query_size + answer_size
            )
            routing_positions += 16 * (longest * record_size + query_size)
            training_history_tokens += sum(
                len(e["text"].encode()) + 1 for r in batch for e in r["events"]
            )
            optimizer.zero_grad(set_to_none=True)
            loss, metrics = study.loss_for(model, batch)
            if not torch.isfinite(loss):
                raise ValueError("nonfinite objective")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            optimizer.step()
            if step == 0 or (step + 1) % 100 == 0:
                curve.append({"step": step + 1, **metrics})
                print(seed, curve[-1], flush=True)
        elapsed = time.perf_counter() - started
        record = {
            "format": FORMAT,
            "boundary": "optimizer-step",
            "variant": "integrated",
            "config": asdict(model.config),
            "training_recipe": RECIPE,
            "seed": seed,
            "next_step": 800,
            "tokenizer": ByteTokenizer.fingerprint,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "torch_rng": torch.get_rng_state(),
            "python_rng": world_rng.getstate(),
            "augmentation_rng": render_rng.getstate(),
            "curve": curve,
            "registration_sha256": file_identity(run / "registration.json"),
            "training_seconds": elapsed,
            "parameters": sum(p.numel() for p in model.parameters()),
            "training_history_tokens": training_history_tokens,
            "training_recurrent_padded_positions": recurrent_positions,
            "training_routing_embedding_padded_positions": routing_positions,
            "data_sha256": file_identity(study.q.OLD / "data/manifest.json"),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        torch.save(record, output)
    summary = {
        k: record[k]
        for k in (
            "format",
            "training_recipe",
            "config",
            "seed",
            "next_step",
            "tokenizer",
            "curve",
            "registration_sha256",
            "training_seconds",
            "parameters",
            "data_sha256",
            "training_history_tokens",
            "training_recurrent_padded_positions",
            "training_routing_embedding_padded_positions",
        )
    }
    summary.update(
        sha256=file_identity(output),
        sampled_peak_rss=max(memory.samples),
        process_high_water_bytes=peak_bytes(),
        steps=registration["config"]["steps"],
    )
    study.q.dump(output.with_suffix(".json"), summary)


def seal(run: Path) -> None:
    verify(run)
    study.q.dump(
        run / "models.json",
        {
            "utc": datetime.now(UTC).isoformat(),
            "registration_sha256": file_identity(run / "registration.json"),
            "files": {
                f"train/augmented-{s}.pt": file_identity(run / "train" / f"augmented-{s}.pt")
                for s in (31, 47)
            },
        },
    )
    print("Sealed both new checkpoints before development inference")


def evaluate(run: Path, method: str, seed: int) -> None:
    verify(run, models=True)
    output = run / "raw" / f"{method}-{seed}.json"
    if output.exists():
        raise ValueError("development output already exists")
    torch.set_num_threads(1)
    started = time.perf_counter()
    diagnostic_seconds = 0.0
    checkpoint = (
        run / "train" / f"augmented-{seed}.pt"
        if method in ("augmented", "zero")
        else OLD / "train" / f"new-{seed}.pt"
        if method == "old"
        else study.q.checkpoint_for("recent", seed)
    )
    with study.MemorySample() as memory:
        model, saved = (
            load_integrated(checkpoint)
            if method in ("recent", "lexical")
            else load_pooled(checkpoint)
        )
        if method in ("augmented", "zero") and saved.get("training_recipe") != RECIPE:
            raise ValueError("wrong augmented checkpoint recipe")
        mode = method if method in ("recent", "lexical", "zero") else "integrated"
        checkpoint_hash = file_identity(checkpoint)
        dataset = json.loads((run / "development.json").read_text())
        if dataset["role"] != "development-only":
            raise ValueError("development-only dataset required")
        predictions: list[Row] = []
        for row in dataset["worlds"]:
            texts = [e["text"] for e in row["events"]]
            answers = []
            for question in row["questions"]:
                answer = study.q.infer(model, None, texts, question["query"], mode, checkpoint_hash)
                answer.update(question)
                answer["correct"] = answer["answer"] == question["expected"]
                answer["unsupported"] = question["expected"] == "?" and answer["answer"] != "?"
                answer["evidence_ingested"] = all(
                    i in answer["selected_record_ids"] for i in question["evidence"]
                )
                answer["evidence_suffix_exposed"] = all(
                    i in answer["suffix_record_ids"] for i in question["evidence"]
                )
                answer["extra_routing_embedding_positions"] = (
                    answer["update_tokens"] + len(question["query"].encode())
                    if method not in ("recent", "lexical")
                    else 0
                )
                diag = time.perf_counter()
                if method not in ("recent", "lexical"):
                    writes, read = study.routes(model, texts, question["query"])
                    answer.update(
                        read_predicted=read,
                        read_correct=read == question["key"],
                        write_predictions=writes,
                        write_records=len(writes),
                        write_correct=sum(
                            p == e["address"] for p, e in zip(writes, row["events"], strict=True)
                        ),
                    )
                diagnostic_seconds += time.perf_counter() - diag
                answers.append(answer)
            predictions.append(
                {k: row[k] for k in ("id", "category", "eval_seed", "load")}
                | {"answers": answers, "correct": all(a["correct"] for a in answers)}
            )
    study.q.dump(
        output,
        {
            "role": "development-only",
            "method": method,
            "seed": seed,
            "checkpoint_sha256": file_identity(checkpoint),
            "development_sha256": file_identity(run / "development.json"),
            "model_seal_sha256": file_identity(run / "models.json"),
            "predictions": predictions,
            "seconds": time.perf_counter() - started,
            "diagnostic_seconds": diagnostic_seconds,
            "sampled_peak_rss": max(memory.samples),
            "rss_samples": len(memory.samples),
            "process_high_water_bytes": peak_bytes(),
            "totals": study.q.summarize(predictions),
        },
    )
    print(
        method,
        seed,
        "development exact",
        sum(p["correct"] for p in predictions),
        "/",
        len(predictions),
    )


def gate(cell: Row, zero: Row) -> Row:
    known = cell["known_correct"] / cell["known_worlds"]
    drop = known - zero["known_correct"] / zero["known_worlds"]
    checks = {
        "overall_at_least_80": cell["accuracy"] >= 0.8,
        "known_at_least_80": known >= 0.8,
        "correction_at_least_80": cell["categories"]["correction"]["correct"]
        / cell["categories"]["correction"]["worlds"]
        >= 0.8,
        "preservation_at_least_80": cell["categories"]["preservation"]["correct"]
        / cell["categories"]["preservation"]["worlds"]
        >= 0.8,
        "unsupported_at_most_5": cell["unsupported"] / cell["unknown_queries"] <= 0.05,
        "memory_zero_known_drop_at_least_50pp": drop >= 0.5,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "known_accuracy": known,
        "known_accuracy_drop_zero": drop,
    }


def analyze(run: Path) -> None:
    verify(run, models=True)
    methods: Row = {}
    clusters: Row = {}
    examples: Row = {}
    for method in METHODS:
        methods[method] = {}
        clusters[method] = defaultdict(list)
        for seed in (31, 47):
            raw = json.loads((run / "raw" / f"{method}-{seed}.json").read_text())
            if (
                raw["role"] != "development-only"
                or raw["model_seal_sha256"] != file_identity(run / "models.json")
                or raw["development_sha256"] != file_identity(run / "development.json")
            ):
                raise ValueError("scored output belongs to a different development comparison")
            totals = raw["totals"]
            answers = [a for p in raw["predictions"] for a in p["answers"]]
            known = [a for a in answers if a["evidence"]]
            totals["known_generated_distribution"] = dict(Counter(a["answer"] for a in known))
            totals.update(
                sampled_peak_rss=raw["sampled_peak_rss"],
                process_seconds=raw["seconds"],
                evidence_queries=len(known),
                evidence_ingested=sum(a["evidence_ingested"] for a in known),
                evidence_suffix_exposed=sum(a["evidence_suffix_exposed"] for a in known),
                extra_routing_embedding_positions=sum(
                    a["extra_routing_embedding_positions"] for a in answers
                ),
            )
            if method not in ("recent", "lexical"):
                totals.update(
                    read_correct=sum(a["read_correct"] for a in answers),
                    read_queries=len(answers),
                    write_correct=sum(a["write_correct"] for a in answers),
                    write_records=sum(a["write_records"] for a in answers),
                )
            totals["per_evaluation_seed"] = {
                str(s): study.q.summarize([p for p in raw["predictions"] if p["eval_seed"] == s])
                for s in (9101, 9102, 9103)
            }
            methods[method][str(seed)] = totals
            for prediction in raw["predictions"]:
                clusters[method][prediction["id"]].append(int(prediction["correct"]))
    uncertainty = {}
    for method in METHODS:
        values = {i: sum(v) / 2 for i, v in clusters[method].items()}
        uncertainty[method] = {
            "accuracy_95": study.q.bootstrap(values),
            "difference_vs_old_95": study.q.bootstrap(
                {i: v - sum(clusters["old"][i]) / 2 for i, v in values.items()}
            ),
        }
    for seed in (31, 47):
        old = {
            p["id"]: p
            for p in json.loads((run / "raw" / f"old-{seed}.json").read_text())["predictions"]
        }
        new = json.loads((run / "raw" / f"augmented-{seed}.json").read_text())["predictions"]
        examples[str(seed)] = {
            label: [{"old": old[p["id"]], "augmented": p} for p in new if test(p, old[p["id"]])][:5]
            for label, test in {
                "gains": lambda n, o: n["correct"] and not o["correct"],
                "regressions": lambda n, o: not n["correct"] and o["correct"],
                "known_failures": lambda n, o: (
                    not n["correct"] and all(a["expected"] != "?" for a in n["answers"])
                ),
                "unsupported": lambda n, o: any(a["unsupported"] for a in n["answers"]),
            }.items()
        }
    gates = {s: gate(methods["augmented"][s], methods["zero"][s]) for s in ("31", "47")}
    status = "PASS" if all(g["status"] == "PASS" for g in gates.values()) else "FAIL"
    study.q.dump(
        run / "summary.json",
        {
            "milestone_status": status,
            "role": "development-only",
            "final_evaluation": "NOT_STARTED",
            "methods": methods,
            "gates": gates,
            "uncertainty": uncertainty,
        },
    )
    study.q.dump(run / "examples.json", examples)
    lines = [
        "| Method | Exact /168 seed31/47 | Known /120 | Unsupported /48 | Selected tokens "
        "| Forward positions | Extra routing positions | Latency ms | Peak RSS MiB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        parts = [method]
        for key in (
            "correct",
            "known_correct",
            "unsupported",
            "selected_tokens",
            "forward_positions",
            "extra_routing_embedding_positions",
            "response_ms",
        ):
            parts.append(" / ".join(f"{seeds[s][key]:.1f}" for s in ("31", "47")))
        parts.append(
            " / ".join(f"{seeds[s]['sampled_peak_rss'] / 1024**2:.1f}" for s in ("31", "47"))
        )
        lines.append("| " + " | ".join(parts) + " |")
    (run / "table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(status, json.dumps(gates), flush=True)
    print("\n".join(lines))


def checked(run: Path, label: str, argv: list[str], timeout: int = 180) -> None:
    command = [
        sys.executable,
        "scripts/check.py",
        "--timeout",
        str(timeout),
        "--output-dir",
        str(run / "checks"),
        label,
        "--",
        sys.executable,
        __file__,
        *argv,
        "--run",
        str(run),
    ]
    if subprocess.run(command, timeout=timeout + 15).returncode:
        raise RuntimeError(f"failed {label}; retain failure, no automatic retry")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("register", "train", "seal", "evaluate", "analyze", "run")
    )
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--seed", type=int, choices=(31, 47))
    parser.add_argument("--method", choices=METHODS)
    args = parser.parse_args()
    if args.command == "register":
        register(args.run)
    elif args.command == "seal":
        seal(args.run)
    elif args.command == "analyze":
        analyze(args.run)
    elif args.command in ("train", "evaluate"):
        if args.seed is None:
            parser.error("--seed required")
        if args.command == "train":
            train(args.run, args.seed)
        else:
            if args.method is None:
                parser.error("--method required")
            evaluate(args.run, args.method, args.seed)
    else:
        for seed in (31, 47):
            checked(args.run, f"train-{seed}", ["train", "--seed", str(seed)])
        checked(args.run, "model-seal", ["seal"])
        for index, seed in enumerate((31, 47)):
            for method in METHODS[index:] + METHODS[:index]:
                checked(
                    args.run,
                    f"development-{method}-{seed}",
                    ["evaluate", "--seed", str(seed), "--method", method],
                )
        checked(args.run, "analysis", ["analyze"])


if __name__ == "__main__":
    main()
