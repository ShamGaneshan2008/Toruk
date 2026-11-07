"""Freeze and audit a negative owned-LM research claim without changing its protocol."""

import argparse
import csv
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
from pathlib import Path

import torch
from validate_owned_reproduction import validate

from toruk_lm.owned_data import CATEGORIES
from toruk_lm.owned_training import runtime_identity, write_json
from toruk_lm.tokenizer import ByteTokenizer

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/claim-closure-v1.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def paired_interval(left, right, *, resamples, seed):
    """Resample matched question blocks; all fitted seeds remain within each block."""
    require(set(left) == set(right) and bool(left), "paired question identity mismatch")
    differences = []
    for key in sorted(left):
        require(set(left[key]) == set(right[key]), "paired training seed mismatch")
        differences.append(sum(left[key][s] - right[key][s] for s in left[key]) / len(left[key]))
    rng = random.Random(seed)
    n = len(differences)
    draws = sorted(sum(rng.choice(differences) for _ in range(n)) / n for _ in range(resamples))
    return dict(
        delta=sum(differences) / n,
        low=draws[int(0.025 * (resamples - 1))],
        high=draws[int(0.975 * (resamples - 1))],
        questions=n,
        interpretation="posthoc scenario uncertainty conditional on the two fitted seeds",
    )


def leakage(datasets):
    sets = {split: {r["text"] for r in rows} for split, rows in datasets.items()}
    overlaps = {
        f"{a}/{b}": len(sets[a] & sets[b])
        for a, b in (("train", "dev"), ("train", "heldout"), ("dev", "heldout"))
    }
    require(not any(overlaps.values()), "exact document leakage")
    train_answers = {r["answer"] for r in datasets["train"]}
    return dict(
        exact_document_overlaps=overlaps,
        heldout_answers_in_train_inventory=sum(
            r["answer"] in train_answers for r in datasets["heldout"]
        ),
        heldout_questions=len(datasets["heldout"]),
        caveat="Shared grammar, entity and answer inventory; no unseen-template claim",
    )


def freeze(package):
    require(not package.exists(), "fresh package directory required")
    config = read(CONFIG)
    require(config["schema"] == "toruk-claim-closure-v1", "unsupported closure protocol")
    files = [
        CONFIG,
        ROOT / config["study_config"],
        ROOT / config["reproduction_contract"],
        Path(__file__),
        ROOT / "scripts/study_owned_lm.py",
        ROOT / "scripts/validate_owned_reproduction.py",
        ROOT / "docs/research/owned-lm-v1-design.md",
    ]
    files += [ROOT / "src/toruk_lm" / name for name in runtime_identity()]
    reference = ROOT / config["reference"]
    files += sorted((reference / "heldout").glob("*.json"))
    files += [reference / f"{name}.json" for name in ("registration", "freeze", "summary")]
    files += [reference / "data" / f"{split}.json" for split in ("train", "dev", "heldout")]
    registration = dict(
        schema="toruk-claim-closure-registration-v1",
        config=config,
        head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        inputs={p.relative_to(ROOT).as_posix(): sha(p) for p in files},
        tokenizer=ByteTokenizer.fingerprint,
        model_runtime=runtime_identity(),
        python=sys.version,
        torch=torch.__version__,
        platform=platform.platform(),
        logical_cpus=os.cpu_count(),
        processor=platform.processor(),
        study_cpu_threads=1,
        scope="Known published outcomes; freeze binds this audit, not a new preregistered test",
    )
    write_json(package / "registration.json", registration)
    print(json.dumps(dict(status="FROZEN", package=str(package), inputs=len(files))))


def analyze(package, run):
    registration = read(package / "registration.json")
    for name, expected in registration["inputs"].items():
        require(sha(ROOT / name) == expected, f"frozen closure input changed: {name}")
    config = registration["config"]
    reproduction = validate(
        run,
        ROOT / config["study_config"],
        ROOT / config["reproduction_contract"],
        ROOT / config["reference"],
    )
    output = package / "analysis"
    require(not output.exists(), "refusing to overwrite closure analysis")
    datasets = {s: read(run / "data" / f"{s}.json") for s in ("train", "dev", "heldout")}
    leak = leakage(datasets)
    summary = read(run / "summary.json")
    results = {p.stem: read(p) for p in sorted((run / "heldout").glob("*.json"))}
    reference = ROOT / config["reference"]
    max_loss_delta = max(
        abs(r["loss_sum"] - old["loss_sum"])
        for name, result in results.items()
        for r, old in zip(
            result["rows"], read(reference / "heldout" / f"{name}.json")["rows"], strict=True
        )
    )
    groups = {}
    raw = []
    for result in results.values():
        mode = "rolling" if result["rolling_diagnostic"] else result["ablation"]
        key = f"{result['variant']}/{mode}"
        groups.setdefault(key, []).append(result)
        for row in result["rows"]:
            generation = row["generation"]
            prefix_tokens = generation["input_tokens"]
            upper = next(
                (b for b in config["prefix_token_upper_bounds"] if prefix_tokens <= b), None
            )
            raw.append(
                dict(
                    condition=key,
                    seed=result["seed"],
                    id=row["id"],
                    category=row["category"],
                    expected=row["expected"],
                    answer=generation["answer"],
                    correct=row["correct"],
                    unsupported=row["unsupported"],
                    prefix_tokens=prefix_tokens,
                    prefix_bin=str(upper) if upper else "overflow",
                    generated_ids=generation["generated_ids"],
                    output_tokens=len(generation["generated_ids"]),
                    memory_updates=generation["commits"],
                    generation_forward_positions=generation["forward_positions"],
                    nll_forward_positions=row["nll_forward_positions"],
                    generation_seconds=row["generation_seconds"],
                    nll_seconds=row["nll_seconds"],
                    loss_sum=row["loss_sum"],
                    targets=row["targets"],
                    stale=row["stale"],
                    allocated_state_bytes=generation["allocated_state_bytes"],
                )
            )
    aggregates = {}
    for key, values in groups.items():
        rows = [r for r in raw if r["condition"] == key]
        variant = values[0]["variant"]
        training = [v for name, v in summary["training"].items() if name.endswith("-" + variant)]
        aggregates[key] = dict(
            n=len(rows),
            correct=sum(r["correct"] for r in rows),
            unsupported=sum(r["unsupported"] for r in rows),
            stale=sum(r["stale"] for r in rows),
            nll={str(v["seed"]): v["nll"] for v in values},
            categories={
                c: dict(
                    n=sum(r["category"] == c for r in rows),
                    correct=sum(r["correct"] for r in rows if r["category"] == c),
                )
                for c in CATEGORIES
            },
            exploratory_prefix_bins={
                b: dict(
                    n=sum(r["prefix_bin"] == b for r in rows),
                    correct=sum(r["correct"] for r in rows if r["prefix_bin"] == b),
                )
                for b in sorted({r["prefix_bin"] for r in rows})
            },
            training_seconds=sum(v["seconds"] for v in training),
            training_cpu_seconds=sum(v["cpu_seconds"] for v in training),
            training_targets=sum(v["training_targets_total"] for v in training),
            allocated_parameters=training[0]["parameters"],
            active_gradient_parameters=training[0]["active_gradient_parameters"],
            generation_seconds=sum(r["generation_seconds"] for r in rows),
            nll_seconds=sum(r["nll_seconds"] for r in rows),
            evaluation_wall_seconds=sum(v["seconds"] for v in values),
            evaluation_cpu_seconds=sum(v["cpu_seconds"] for v in values),
            prefix_tokens=sum(r["prefix_tokens"] for r in rows),
            output_tokens=sum(r["output_tokens"] for r in rows),
            generation_forward_positions=sum(r["generation_forward_positions"] for r in rows),
            nll_forward_positions=sum(r["nll_forward_positions"] for r in rows),
            memory_updates=sum(r["memory_updates"] for r in rows),
            selector_work=0,
            state_bytes=max(r["allocated_state_bytes"] for r in rows),
            process_lifetime_peak_rss=max(v["memory"]["process_lifetime_peak_rss"] for v in values),
            rss_caveat="Cumulative process peak, fixed order; not isolated per-method memory",
        )
    paired = {}

    def outcomes(condition):
        answers = {}
        for row in raw:
            if row["condition"] == condition:
                answers.setdefault(row["id"], {})[row["seed"]] = int(row["correct"])
        return answers

    for baseline in ("ordinary/full", "ordinary_matched/full"):
        paired[baseline] = paired_interval(
            outcomes("memory_on/full"),
            outcomes(baseline),
            resamples=config["bootstrap_resamples"],
            seed=config["bootstrap_seed"],
        )
    # No posthoc analysis is allowed to rescue failure of the original all-required gate.
    require(
        not summary["criterion"]["passed"], "expected negative candidate changed: manual review"
    )
    report = dict(
        schema="toruk-claim-closure-results-v1",
        verdict="CLAIM NOT SUPPORTED",
        reproduction=reproduction,
        max_loss_delta=max_loss_delta,
        leakage=leak,
        original_criterion=summary["criterion"],
        aggregates=aggregates,
        posthoc_paired_intervals=paired,
        untested=config["untested_categories"],
        length_sweep="NOT_RUN: original protocol has no controlled length grid",
        checkpoint_hashes=read(run / "freeze.json")["checkpoints"],
        historical_checkpoint_hashes=read(reference / "freeze.json")["checkpoints"],
        historical_commit=read(reference / "registration.json")["head"],
        tokenizer=registration["tokenizer"],
        registration=registration,
        total_study_seconds=summary["seconds"],
        total_study_cpu_seconds=summary["cpu_seconds"],
    )
    write_json(output / "results.json", report)
    with (output / "per-case.jsonl").open("w", encoding="utf-8") as stream:
        for row in raw:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    with (output / "per-case.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(raw[0]))
        writer.writeheader()
        writer.writerows(raw)
    print(
        json.dumps(
            dict(
                verdict=report["verdict"],
                answers=len(raw),
                max_loss_delta=max_loss_delta,
                paired_intervals=paired,
            ),
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "analyze"))
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "freeze":
            freeze(args.package)
        else:
            require(args.run is not None, "analyze requires --run")
            analyze(args.package, args.run)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Claim closure failed: {error}\n")


if __name__ == "__main__":
    main()
