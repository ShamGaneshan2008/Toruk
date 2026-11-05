"""One frozen data-only owned-LM experiment; never called by chat inference."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import psutil

from toruk_lm.conversation_data import audit_splits, format_messages, make_cases, overlap
from toruk_lm.engine import setup
from toruk_lm.owned_data import digest
from toruk_lm.owned_lm import OwnedConfig, OwnedSession
from toruk_lm.owned_training import (
    flags,
    load,
    memory_bytes,
    runtime_identity,
    train,
    train_indices,
    write_json,
)

BASE = Path("artifacts/conversation-format-v1-20261105")
SOURCE = Path("artifacts/conversation-readiness-v1-20261104/registered/data")
OLD = Path("artifacts/owned-lm-v1-20261104/primary/models/31-memory_on/checkpoint.pt")
PROTOCOL = Path("docs/research/conversation-format-v1-protocol.md")


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(raw: str, expected: str, *, owned: bool) -> dict[str, Any]:
    content = raw.strip()
    framed = False
    if owned:
        try:
            parsed = json.loads(raw)
            framed = isinstance(parsed, str)
            if framed:
                content = parsed
        except ValueError:
            pass
    words = content.lower().split()
    triples = [tuple(words[i : i + 3]) for i in range(max(0, len(words) - 2))]
    return {
        "content": content,
        "framed": framed if owned else None,
        "raw_exact": raw.strip() == expected,
        "exact": (framed or not owned) and content == expected,
        "invalid_utf8": "\ufffd" in raw,
        "repeated_trigrams": len(triples) - len(set(triples)),
    }


def identities() -> dict[str, str]:
    return {str(path): sha(path) for path in (PROTOCOL, Path(__file__))}


def register(run: Path) -> None:
    if (run / "registration.json").exists():
        raise ValueError("registration already exists")
    splits = {key: read(SOURCE / f"{key}.json") for key in ("train", "development", "test")}
    fresh = make_cases("test", 3, 11301)
    for row in fresh:
        row["id"] = "fresh-" + row["id"]
        for message in row["messages"]:
            content = message["content"]
            for old, new in (
                ("Eperson", "Hperson"),
                ("Evalue", "Hvalue"),
                ("Eold", "Hold"),
                ("E/Q", "H/Q"),
                ("Unknown.", "Unavailable."),
                ("5+5", "9+9"),
            ):
                content = content.replace(old, new)
            message["content"] = content
        for old, new in (
            ("Evalue", "Hvalue"),
            ("Eold", "Hold"),
            ("E/Q", "H/Q"),
            ("Unknown.", "Unavailable."),
        ):
            row["answer"] = row["answer"].replace(old, new)
            row["obsolete"] = row["obsolete"].replace(old, new)
        if row["category"] in ("math", "refusal"):
            row["answer"] = "18"
        row["prefix"] = format_messages(row["messages"], prompt=True)
        row["text"] = format_messages(
            [*row["messages"], {"role": "assistant", "content": row["answer"]}]
        )
    audit = audit_splits({**splits, "test": [*splits["test"], *fresh]})
    reserved = {row["answer"] for row in [*splits["development"], *splits["test"], *fresh]}
    control_source = read(SOURCE / "clean-pretraining-train.json")
    control = [r for r in control_source if not any(overlap(a, r["text"]) for a in reserved)]
    data = {
        "candidate": splits["train"],
        "control": control,
        "development": splits["development"],
        "primary": fresh,
        "regression": splits["test"],
    }
    for key, rows in data.items():
        write_json(run / "data" / f"{key}.json", rows)
    source_manifest = read(SOURCE / "manifest.json")
    registration = {
        "schema": "toruk-conversation-format-v1",
        "sources": identities(),
        "runtime": runtime_identity(),
        "data_audit": audit,
        "starting_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "model": asdict(OwnedConfig()),
        "seed": 31,
        "steps": 512,
        "batch": 2,
        "learning_rate": 0.003,
        "budget": 32,
        "data": {key: digest(rows) for key, rows in data.items()},
        "old_checkpoint": str(OLD),
        "old_sha256": sha(OLD),
        "provenance": {
            "source_manifest": str(SOURCE / "manifest.json"),
            "sha256": sha(SOURCE / "manifest.json"),
            "original": source_manifest["source"],
            "new_training_data": False,
            "license": "Original repository synthetic data; no third-party license added. "
            "Repository specifies no project license.",
            "control_removed_ids": [r["id"] for r in control_source if r not in control],
            "lineage": "Both new fits random initialization; no inherited weights or optimizer.",
        },
    }
    write_json(run / "registration.json", registration)
    print(json.dumps({"registered": True, "data_counts": {k: len(v) for k, v in data.items()}}))


def validate(run: Path) -> dict[str, Any]:
    reg = read(run / "registration.json")
    if reg["sources"] != identities() or reg["runtime"] != runtime_identity():
        raise ValueError("frozen sources changed")
    if sha(OLD) != reg["old_sha256"]:
        raise ValueError("old checkpoint changed")
    for key, expected in reg["data"].items():
        if digest(read(run / "data" / f"{key}.json")) != expected:
            raise ValueError("sealed data changed")
    return reg


def fit(run: Path, condition: str) -> None:
    reg = validate(run)
    documents = read(run / "data" / f"{condition}.json")
    targets = sum(
        len(documents[i]["text"].encode()) + 1
        for step in range(512)
        for i in train_indices(len(documents), step, 2, 31)
    )
    if targets > 393216 or any(len(r["text"].encode()) + 1 > 384 for r in documents):
        raise ValueError("training target budget exceeded")
    deadline = time.perf_counter() + 120
    common = dict(seed=31, batch=2, learning_rate=0.003, deadline=deadline)
    checkpoint = run / "models" / condition / "checkpoint.pt"
    if condition == "candidate":
        partial = checkpoint.with_name("step256.pt")
        train(OwnedConfig(**reg["model"]), "memory_on", documents, partial, steps=256, **common)
        train(
            OwnedConfig(**reg["model"]),
            "memory_on",
            documents,
            checkpoint,
            steps=512,
            resume=partial,
            **common,
        )
    else:
        train(OwnedConfig(**reg["model"]), "memory_on", documents, checkpoint, steps=512, **common)
    if memory_bytes()["rss"] > 512 * 1024**2:
        raise RuntimeError("owned RSS cap exceeded")


def train_run(run: Path) -> None:
    validate(run)
    if (run / "freeze.json").exists():
        raise ValueError("already trained")
    resources = {}
    for condition in ("control", "candidate"):
        command = [
            sys.executable,
            str(Path(__file__)),
            "fit",
            "--run",
            str(run),
            "--condition",
            condition,
        ]
        started = time.perf_counter()
        with (run / f"{condition}-fit.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            peak = 0
            while process.poll() is None:
                try:
                    peak = max(peak, psutil.Process(process.pid).memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                if time.perf_counter() - started > 125 or peak > 512 * 1024**2:
                    process.kill()
                    process.wait()
                    raise RuntimeError("training subprocess exceeded wall/RSS cap")
                time.sleep(0.05)
        resources[condition] = {
            "command": command,
            "exit": process.returncode,
            "seconds": time.perf_counter() - started,
            "sampled_peak_rss": peak,
        }
        write_json(run / "training-processes.json", resources)
        if process.returncode:
            raise RuntimeError(f"{condition} training failed; inspect retained log")
    write_json(
        run / "freeze.json",
        {
            "registration_sha256": sha(run / "registration.json"),
            "checkpoints": {
                c: sha(run / "models" / c / "checkpoint.pt") for c in ("candidate", "control")
            },
        },
    )


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {
        "n": len(rows),
        "exact": sum(r["scores"]["exact"] for r in rows),
        "raw_exact": sum(r["scores"]["raw_exact"] for r in rows),
        "framed": sum(bool(r["scores"]["framed"]) for r in rows),
        "terminated": sum(r.get("terminated") is True for r in rows),
        "errors": sum(bool(r["error"]) for r in rows),
        "invalid_utf8": sum(r["scores"]["invalid_utf8"] for r in rows),
        "unsupported_unknown_proxy": sum(r["unsupported_unknown_proxy"] for r in rows),
        "stale": sum(r["stale"] for r in rows),
        "repeated_trigrams": sum(r["scores"]["repeated_trigrams"] for r in rows),
        "unique_nonempty": len({r["raw_answer"] for r in rows if r["raw_answer"]}),
        "seconds": sum(r["seconds"] for r in rows),
        "cpu_seconds": sum(r["cpu_seconds"] for r in rows),
        "prompt_tokens": sum(r["prompt_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "owned_forward_positions": sum(r["forward_positions"] for r in rows),
        "peak_rss": max(r["memory"]["process_lifetime_peak_rss"] for r in rows),
        "categories": {},
    }
    for category in sorted({r["category"] for r in rows}):
        selected = [r for r in rows if r["category"] == category]
        result["categories"][category] = {
            "n": len(selected),
            "exact": sum(r["scores"]["exact"] for r in selected),
        }
    return result


def gates(summary: dict[str, Any]) -> dict[str, Any]:
    candidate = summary["candidate"]
    comparisons = {}
    for name in ("historical", "control"):
        old = summary[name]
        comparisons[name] = (
            candidate["framed"] - old["framed"] >= 0.5 * candidate["n"]
            and candidate["terminated"] - old["terminated"] >= 0.5 * candidate["n"]
            and candidate["exact"] >= old["exact"] - 1
            and all(
                candidate["categories"][c]["exact"] >= v["exact"] - 1
                for c, v in old["categories"].items()
            )
            and all(
                candidate[k] <= old[k]
                for k in ("unsupported_unknown_proxy", "invalid_utf8", "repeated_trigrams")
            )
        )
    quality = (
        candidate["exact"] >= 0.8 * candidate["n"]
        and all(v["exact"] >= 0.6 * v["n"] for v in candidate["categories"].values())
        and candidate["terminated"] >= 0.95 * candidate["n"]
        and not any(candidate[k] for k in ("errors", "invalid_utf8", "unsupported_unknown_proxy"))
    )
    return {
        "framing_and_regression": comparisons,
        "integration": quality and all(comparisons.values()),
    }


def evaluate_run(run: Path, backbone: Path) -> None:
    reg = validate(run)
    freeze = read(run / "freeze.json")
    if freeze["registration_sha256"] != sha(run / "registration.json"):
        raise ValueError("registration changed after freeze")
    for c, expected in freeze["checkpoints"].items():
        if sha(run / "models" / c / "checkpoint.pt") != expected:
            raise ValueError("trained checkpoint changed")
    # Claim evaluation before inference: failed attempts cannot silently rerun held-out.
    (run / "evaluation-started.json").open("x").write(
        json.dumps({"freeze": sha(run / "freeze.json")})
    )
    started = time.perf_counter()
    conditions = {
        "historical": (OLD, "full"),
        "control": (run / "models/control/checkpoint.pt", "full"),
        "candidate": (run / "models/candidate/checkpoint.pt", "full"),
        "no_read": (run / "models/candidate/checkpoint.pt", "no_read"),
        "no_update": (run / "models/candidate/checkpoint.pt", "no_update"),
    }
    outputs = []

    def limit(external: bool = False) -> None:
        if time.perf_counter() - started > 350:
            raise RuntimeError("evaluation wall cap exceeded")
        if memory_bytes()["rss"] > (4096 if external else 512) * 1024**2:
            raise RuntimeError("evaluation RSS cap exceeded")
        if sum(p.stat().st_size for p in run.rglob("*") if p.is_file()) > 64 * 1024**2:
            raise RuntimeError("experiment disk cap exceeded")

    def append(
        row: dict[str, Any],
        suite: str,
        condition: str,
        raw: str,
        error: str | None,
        generation: dict[str, Any],
        model_id: str,
        tick: float,
        cpu: float,
        external: bool = False,
    ) -> None:
        scores = measure(raw, row["answer"], owned=not external)
        outputs.append(
            {
                "case": row["id"],
                "suite": suite,
                "condition": condition,
                "origin": "external_pretrained" if external else "toruk_owned",
                "model_id": model_id,
                "category": row["category"],
                "expected": row["answer"],
                "raw_answer": raw,
                "scores": scores,
                "error": error,
                "generation": generation,
                "unsupported_unknown_proxy": row["category"] == "uncertainty"
                and bool(raw.strip())
                and not scores["exact"],
                "stale": bool(row["obsolete"]) and scores["content"] == row["obsolete"],
                "terminated": generation.get("terminated")
                if external
                else (not generation["budget_exhausted"] if generation else False),
                "prompt_tokens": generation.get("prompt_tokens", 0)
                if external
                else generation.get("input_tokens", 0),
                "output_tokens": generation.get("output_tokens", 0)
                if external
                else len(generation.get("generated_ids", [])),
                "forward_positions": generation.get("forward_positions", 0),
                "seconds": time.perf_counter() - tick,
                "cpu_seconds": time.process_time() - cpu,
                "memory": memory_bytes(),
                "prefix_sha256": digest(row["prefix"]),
            }
        )

    for condition, (checkpoint, ablation) in conditions.items():
        setup(0, 1)
        model, saved = load(checkpoint)
        read_memory, write = flags(saved["variant"], ablation)
        for suite in ("development", "primary", "regression"):
            for row in read(run / "data" / f"{suite}.json"):
                limit()
                tick, cpu = time.perf_counter(), time.process_time()
                try:
                    gen = dict(
                        OwnedSession(model, read=read_memory, write=write).generate(
                            row["prefix"], reg["budget"]
                        )
                    )
                    raw, error = str(gen["answer"]), None
                except ValueError as exception:
                    gen, raw, error = {}, "", str(exception)
                append(
                    row,
                    suite,
                    condition,
                    raw,
                    error,
                    gen,
                    "toruk-owned-next-token-v1@" + sha(checkpoint)[:12],
                    tick,
                    cpu,
                )
                limit()
        write_json(
            run / f"outputs-{condition}.json", [r for r in outputs if r["condition"] == condition]
        )
    from toruk_lm.chat_foundation import PretrainedChatBackend

    backend = PretrainedChatBackend(backbone)
    for suite in ("primary", "regression"):
        for row in read(run / "data" / f"{suite}.json"):
            limit(True)
            tick, cpu = time.perf_counter(), time.process_time()
            response = backend.reply_with_metrics(
                row["messages"], reg["budget"], mode="BASELINE", temperature=0, top_p=1
            )
            metrics = response["metrics"]
            gen = {
                "response": response,
                "prompt_tokens": metrics["selected_context_tokens"],
                "output_tokens": metrics["output_tokens"],
                "terminated": None,
            }
            append(
                row,
                suite,
                "external_qwen",
                response["answer"],
                None,
                gen,
                backend.model_id,
                tick,
                cpu,
                True,
            )
            limit(True)
    write_json(
        run / "outputs-external_qwen.json",
        [r for r in outputs if r["condition"] == "external_qwen"],
    )
    summaries = {
        suite: {
            c: summarize([r for r in outputs if r["condition"] == c and r["suite"] == suite])
            for c in [*conditions, "external_qwen"]
            if any(r["condition"] == c and r["suite"] == suite for r in outputs)
        }
        for suite in ("development", "primary", "regression")
    }
    write_json(run / "summary.json", summaries)
    write_json(
        run / "decision.json",
        {suite: gates(summaries[suite]) for suite in ("primary", "regression")},
    )
    print(
        json.dumps(
            {
                "answers": len(outputs),
                "seconds": time.perf_counter() - started,
                "decision": read(run / "decision.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "train", "fit", "evaluate"))
    parser.add_argument("--run", type=Path, default=BASE)
    parser.add_argument("--condition", choices=("candidate", "control"))
    parser.add_argument(
        "--backbone-dir", type=Path, default=Path("artifacts/qwen-chat-001/backbone")
    )
    args = parser.parse_args()
    if args.action == "register":
        register(args.run)
    elif args.action == "train":
        train_run(args.run)
    elif args.action == "fit":
        fit(args.run, args.condition)
    else:
        evaluate_run(args.run, args.backbone_dir)
