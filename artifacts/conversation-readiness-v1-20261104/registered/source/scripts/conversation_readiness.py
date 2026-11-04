"""Prepare/audit conversation data; diagnose existing models without pilot training."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from toruk_lm.conversation_data import FORMAT, prepare, require_training_ready
from toruk_lm.engine import setup
from toruk_lm.owned_data import digest, load_data
from toruk_lm.owned_lm import OwnedSession
from toruk_lm.owned_training import load, memory_bytes, write_json


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_run(args: argparse.Namespace) -> None:
    run = args.output
    run.mkdir(parents=True, exist_ok=False)
    config = read(args.config)
    if config["conversational_training_enabled"] or config["training_targets_cap"] != 0:
        raise ValueError("this readiness path does not authorize conversational training")
    source = read(args.refusal_reference)
    diagnostic = next(
        row["history"] for row in source["rows"] if row["scenario"] == "full_history_matched"
    )
    model, saved = load(args.checkpoint)
    inherited = load_data(args.inherited_train, "train")
    if digest(inherited) != saved["dataset"]:
        raise ValueError("starting checkpoint data fingerprint mismatch")
    manifest = prepare(config, inherited, run / "data", diagnostic)
    blocker = None
    try:
        require_training_ready(manifest, saved["dataset"])
    except ValueError as error:
        blocker = str(error)
    registration = {
        "schema": "toruk-conversation-readiness-registration-v1",
        "config": config,
        "checkpoint": str(args.checkpoint),
        "checkpoint_sha256": sha(args.checkpoint),
        "checkpoint_dataset": saved["dataset"],
        "parameters": sum(p.numel() for p in model.parameters()),
        "training_targets_inherited": saved["targets"],
        "format": FORMAT,
        "data_manifest_sha256": sha(run / "data/manifest.json"),
        "refusal_source": str(args.refusal_reference),
        "refusal_source_sha256": sha(args.refusal_reference),
        "source": {
            path: sha(Path(path))
            for path in (
                "src/toruk_lm/conversation_data.py",
                "scripts/conversation_readiness.py",
                str(args.config),
            )
        },
        "readiness": "BLOCKED" if blocker else "REQUIRES_WARMSTART_PROTOCOL",
        "blocker": blocker,
        "new_training_targets": 0,
        "pilot": "NOT_RUN",
        "product_integration": "BLOCKED",
    }
    write_json(run / "registration.json", registration)
    print(
        json.dumps(
            {
                "readiness": registration["readiness"],
                "blocker": blocker,
                "new_conversation_data": manifest["audit"],
                "inherited_matches": manifest["inherited_matches"],
            }
        )
    )


def score(answer: str, row: dict[str, Any]) -> dict[str, Any]:
    answer = answer.strip()
    words = answer.lower().split()
    triples = [tuple(words[i : i + 3]) for i in range(max(0, len(words) - 2))]
    return {
        "exact": answer == row["answer"],
        "false_assertion_proxy": row["category"] == "uncertainty"
        and bool(answer)
        and answer != row["answer"],
        "wrong_nonempty": bool(answer) and answer != row["answer"],
        "repeated_trigrams": len(triples) - len(set(triples)),
        "invalid_utf8": "\ufffd" in answer,
        "refusal_carryover_error": row["category"] == "refusal" and answer != row["answer"],
    }


def evaluate_run(args: argparse.Namespace) -> None:
    run = args.output
    if (run / "diagnostics.json").exists():
        raise ValueError("refusing duplicate evaluation")
    registration = read(run / "registration.json")
    for path, expected in registration["source"].items():
        if sha(Path(path)) != expected:
            raise ValueError("registered readiness sources changed")
    if sha(run / "data/manifest.json") != registration["data_manifest_sha256"]:
        raise ValueError("registered dataset manifest changed")
    config = registration["config"]
    rows = read(run / "data/test.json")
    if digest(rows) != read(run / "data/manifest.json")["audit"]["digests"]["test"]:
        raise ValueError("test data changed")
    setup(0, config["cpu_threads"])
    checkpoint = Path(registration["checkpoint"])
    if sha(checkpoint) != registration["checkpoint_sha256"]:
        raise ValueError("starting weights changed")
    model, _ = load(checkpoint)
    outputs = []
    start = time.perf_counter()
    deadline = start + config["max_evaluation_seconds"]

    def limit(cap: int) -> None:
        if time.perf_counter() > deadline or memory_bytes()["rss"] > cap:
            raise RuntimeError("registered evaluation time/RSS cap exceeded")
        if (
            sum(path.stat().st_size for path in run.rglob("*") if path.is_file())
            > config["max_run_disk_bytes"]
        ):
            raise RuntimeError("registered disk cap exceeded")

    for row in rows:
        limit(config["owned_max_rss_bytes"])
        t, cpu = time.perf_counter(), time.process_time()
        try:
            generated = OwnedSession(model).generate(row["prefix"], config["max_new_tokens"])
            answer, error = str(generated["answer"]), None
        except ValueError as exception:
            generated, answer, error = {}, "", str(exception)
        outputs.append(
            {
                "case": row["id"],
                "category": row["category"],
                "expected": row["answer"],
                "origin": "toruk_owned",
                "model_id": "toruk-owned-next-token-v1@" + registration["checkpoint_sha256"][:12],
                "training_stage": "before_conversational_training",
                "raw_answer": answer,
                "generation": generated,
                "error": error,
                "scores": score(answer, row),
                "seconds": time.perf_counter() - t,
                "cpu_seconds": time.process_time() - cpu,
                "memory": memory_bytes(),
            }
        )
        limit(config["owned_max_rss_bytes"])
    if args.backbone_dir is not None:
        from toruk_lm.chat_foundation import PretrainedChatBackend

        backend = PretrainedChatBackend(args.backbone_dir)
        # Preserve the existing backbone implementation's declared two-thread path.
        for row in rows:
            limit(config["external_max_rss_bytes"])
            t, cpu = time.perf_counter(), time.process_time()
            response = backend.reply_with_metrics(
                row["messages"], config["max_new_tokens"], mode="BASELINE", temperature=0, top_p=1
            )
            outputs.append(
                {
                    "case": row["id"],
                    "category": row["category"],
                    "expected": row["answer"],
                    "origin": "external_pretrained",
                    "model_id": backend.model_id,
                    "raw_answer": response["answer"],
                    "response": response,
                    "scores": score(response["answer"], row),
                    "seconds": time.perf_counter() - t,
                    "cpu_seconds": time.process_time() - cpu,
                    "memory": memory_bytes(),
                }
            )
            limit(config["external_max_rss_bytes"])
    write_json(
        run / "diagnostics.json",
        {
            "schema": "toruk-conversation-diagnostic-v1",
            "rows": outputs,
            "seconds": time.perf_counter() - start,
            "pilot": "NOT_RUN",
            "product_gate": "FAIL: no eligible starting checkpoint and no trained pilot",
            "decoding": {
                "temperature": 0,
                "max_new_tokens": config["max_new_tokens"],
                "owned_tokenizer": "UTF8 bytes",
                "external_tokenizer": "native BPE",
                "prompt_format_owned": FORMAT,
                "external_threads": 2,
            },
            "resource_enforcement": "Time, disk and RSS checks at request boundaries; "
            "outer check.py timeout. Not an OS memory hard limit.",
        },
    )
    print(
        json.dumps({"diagnostic_answers": len(outputs), "pilot": "NOT_RUN", "product_gate": "FAIL"})
    )


def validate(output: Path) -> None:
    config = read(Path("configs/conversation-readiness-v1.json"))
    manifest = prepare(
        config, [{"id": "fixture", "text": "Note 10: rain.", "split": "train"}], output
    )
    try:
        require_training_ready(manifest, manifest["inherited_training_digest"])
    except ValueError:
        print("PASS: chat formatting/splits checked; inherited-exposure gate blocks training")
    else:
        raise AssertionError("exposure guard failed open")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "evaluate", "validate"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/conversation-readiness-v1.json")
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("artifacts/owned-lm-v1-20261104/primary/models/31-memory_on/checkpoint.pt"),
    )
    parser.add_argument(
        "--inherited-train",
        type=Path,
        default=Path("artifacts/owned-lm-v1-20261104/primary/data/train.json"),
    )
    parser.add_argument(
        "--refusal-reference",
        type=Path,
        default=Path("artifacts/current-state-audit-20261103/refusal-replay.json"),
    )
    parser.add_argument("--backbone-dir", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare_run(args)
    elif args.action == "evaluate":
        evaluate_run(args)
    else:
        validate(args.output)
