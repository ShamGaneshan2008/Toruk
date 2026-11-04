"""Registered bounded CPU next-token study; held-out scoring occurs once after freeze."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import torch

from toruk_lm.owned_data import CATEGORIES, load_data, write_data
from toruk_lm.owned_lm import VARIANTS, OwnedConfig
from toruk_lm.owned_training import evaluate, load, runtime_identity, train, write_json

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def success(results: dict[str, Any], seeds: list[int]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    for seed in seeds:
        c = results[f"{seed}-memory_on-full"]
        for variant in ("ordinary", "ordinary_matched", "memory_off"):
            a = results[f"{seed}-{variant}-full"]
            prefix = f"{seed}-{variant}"
            checks[prefix + "-loss"] = c["nll"] <= a["nll"] - 0.05

            def distant(row: dict[str, Any]) -> float:
                categories = row["categories"]
                return sum(categories[k]["correct"] for k in ("distant", "correction")) / sum(
                    categories[k]["n"] for k in ("distant", "correction")
                )

            checks[prefix + "-recall"] = distant(c) >= distant(a) + 0.1
            checks[prefix + "-correction-preservation"] = all(
                c["categories"][k]["correct"] >= a["categories"][k]["correct"]
                for k in ("correction", "preservation")
            )
            checks[prefix + "-unsupported"] = c["unsupported"] <= a["unsupported"]
    for ablation in ("no_read", "no_update"):
        delta = sum(
            results[f"{seed}-memory_on-{ablation}"]["nll"]
            - results[f"{seed}-memory_on-full"]["nll"]
            for seed in seeds
        ) / len(seeds)
        checks[ablation + "-loss"] = delta >= 0.01
    return {"passed": all(checks.values()), "checks": checks}


def study(config_path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError("fresh output required: never overwrite held-out results")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["schema"] != "toruk-owned-lm-study-v1":
        raise ValueError("unsupported study config")
    if not 1 <= config["max_seconds"] <= 600:
        raise ValueError("study requires CPU budget <=600 seconds")
    output.mkdir(parents=True)
    model = OwnedConfig(**config["model"])
    manifest = write_data(
        output / "data",
        {split: config[f"{split}_per_category"] for split in ("train", "dev", "heldout")},
        model.max_document_tokens,
    )
    registration = {
        "schema": "toruk-owned-study-registration-v1",
        "config": config,
        "config_sha256": sha(config_path),
        "runtime": runtime_identity(),
        "driver_sha256": sha(Path(__file__)),
        "design_sha256": sha(ROOT / "docs/research/owned-lm-v1-design.md"),
        "manifest": manifest,
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version,
        "torch": torch.__version__,
        "platform": platform.platform(),
        "heldout_policy": "single scoring pass after checkpoint freeze; no tuning from heldout",
        "success_criterion": "design section Numerical criterion; all gates required",
    }
    write_json(output / "registration.json", registration)
    start, cpu_start = time.perf_counter(), time.process_time()
    deadline = start + config["max_seconds"]
    train_rows = load_data(output / "data/train.json", "train")
    dev_rows = load_data(output / "data/dev.json", "dev")
    # Profile uses training data only; it cannot choose model thresholds or view heldout.
    profile = train(
        model,
        "memory_on",
        train_rows,
        output / "profile/checkpoint.pt",
        steps=2,
        seed=config["seeds"][0],
        batch=config["batch_documents"],
        learning_rate=config["learning_rate"],
        deadline=deadline,
    )
    train_results = {}
    development = {}
    for seed in config["seeds"]:
        for variant in VARIANTS:
            name = f"{seed}-{variant}"
            checkpoint = output / "models" / name / "checkpoint.pt"
            train_results[name] = train(
                model,
                variant,
                train_rows,
                checkpoint,
                steps=config["steps"],
                seed=seed,
                batch=config["batch_documents"],
                learning_rate=config["learning_rate"],
                deadline=deadline,
            )
            if runtime_identity() != registration["runtime"]:
                raise ValueError("runtime changed during registered experiment")
            development[name] = evaluate(
                checkpoint,
                dev_rows,
                output / "dev" / f"{name}.json",
                budget=config["max_new_tokens"],
            )
    # Exercise resume independently of main fit. No heldout feedback enters here.
    partial = output / "resume/partial.pt"
    seed = config["seeds"][0]
    train(
        model,
        "memory_on",
        train_rows,
        partial,
        steps=1,
        seed=seed,
        batch=config["batch_documents"],
        learning_rate=config["learning_rate"],
        deadline=deadline,
    )
    resumed = output / "resume/resumed.pt"
    train(
        model,
        "memory_on",
        train_rows,
        resumed,
        steps=2,
        seed=seed,
        batch=config["batch_documents"],
        learning_rate=config["learning_rate"],
        resume=partial,
        deadline=deadline,
    )
    _, continuous = load(output / "profile/checkpoint.pt")
    _, resumed_payload = load(resumed)
    resume_equal = all(
        torch.equal(value, resumed_payload["model"][key])
        for key, value in continuous["model"].items()
    )
    if not resume_equal:
        raise ValueError("deterministic checkpoint resume failed")
    freeze = {
        "runtime": runtime_identity(),
        "driver_sha256": sha(Path(__file__)),
        "checkpoints": {
            name: sha(output / "models" / name / "checkpoint.pt") for name in train_results
        },
        "development_inspected_without_changes": True,
        "resume_equal": resume_equal,
    }
    write_json(output / "freeze.json", freeze)
    heldout_rows = load_data(output / "data/heldout.json", "heldout")
    results = {}
    for seed in config["seeds"]:
        for variant in VARIANTS:
            checkpoint = output / "models" / f"{seed}-{variant}" / "checkpoint.pt"
            for ablation in (
                ("full", "no_read", "no_update") if variant == "memory_on" else ("full",)
            ):
                if time.perf_counter() > deadline:
                    raise TimeoutError(
                        "bounded study budget exhausted before evaluation completion"
                    )
                key = f"{seed}-{variant}-{ablation}"
                results[key] = evaluate(
                    checkpoint,
                    heldout_rows,
                    output / "heldout" / f"{key}.json",
                    budget=config["max_new_tokens"],
                    ablation=ablation,
                )
            if variant.startswith("ordinary"):
                key = f"{seed}-{variant}-rolling"
                results[key] = evaluate(
                    checkpoint,
                    heldout_rows,
                    output / "heldout" / f"{key}.json",
                    budget=config["max_new_tokens"],
                    rolling=True,
                )
    if runtime_identity() != freeze["runtime"] or sha(Path(__file__)) != freeze["driver_sha256"]:
        raise ValueError("frozen evaluation source changed")
    summary = {
        "schema": "toruk-owned-study-results-v1",
        "profile": profile,
        "training": {
            key: {k: v for k, v in value.items() if k != "trace"}
            for key, value in train_results.items()
        },
        "heldout": {
            key: {k: v for k, v in value.items() if k != "rows"} for key, value in results.items()
        },
        "criterion": success(results, config["seeds"]),
        "resume_equal": resume_equal,
        "seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu_start,
        "categories": CATEGORIES,
        "scope": config["scope"],
    }
    write_json(output / "summary.json", summary)
    print(
        json.dumps(
            {
                "status": "complete",
                "criterion": summary["criterion"]["passed"],
                "seconds": summary["seconds"],
                "output": str(output),
            }
        )
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    study(options.config, options.output)


if __name__ == "__main__":
    main()
