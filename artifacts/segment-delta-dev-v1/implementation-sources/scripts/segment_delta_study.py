"""Single-use, offline CPU development run; never trains or calls production chat."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

STARTED = time.perf_counter()
ROOT = Path(__file__).resolve().parents[1]

from segment_delta_data import CATEGORIES, gates, save, score, sha  # noqa: E402
from segment_delta_watch import watch, worker_receipt  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def runtime():
    return dict(
        python=platform.python_version(),
        torch=importlib.metadata.version("torch"),
        psutil=importlib.metadata.version("psutil"),
        platform=platform.platform(),
    )


def verify(root, *, full_data=True, locked=True):
    registration = read(root / "registration.json")
    if runtime() != registration["runtime"]:
        raise ValueError("registered runtime mismatch")
    for name, digest in registration["source_files"].items():
        if sha(ROOT / name) != digest:
            raise ValueError(f"registered source mismatch: {name}")
    if full_data:
        for name, digest in registration["data"].items():
            if sha(root / name) != digest:
                raise ValueError(f"registered data mismatch: {name}")
    if locked:
        lock = read(root / "implementation-lock.json")
        if lock["registration_sha256"] != sha(root / "registration.json"):
            raise ValueError("registration lock mismatch")
        for name, digest in lock["sources"].items():
            if sha(ROOT / name) != digest:
                raise ValueError(f"implementation source mismatch: {name}")
    return registration


def identity(root):
    reg = read(root / "registration.json")
    return dict(
        registration=sha(root / "registration.json"),
        implementation=sha(root / "implementation-lock.json"),
        train=reg["data"]["train.json"],
        runtime=json.dumps(runtime(), sort_keys=True),
    )


def checkpoint(root, seed, variant):
    return root / "stages" / f"train-{seed}-{variant}" / "checkpoint.pt"


def checked_checkpoint(root, seed, variant):
    path = checkpoint(root, seed, variant)
    if sha(path) != read(path.with_name("checkpoint-meta.json"))["sha256"]:
        raise ValueError("checkpoint hash mismatch")
    return path


def timed_limit(started, cpu_started, cap):
    wall, cpu = time.perf_counter() - started, time.process_time() - cpu_started
    if max(wall, cpu) > cap:
        raise TimeoutError("registered per-document/request cap")
    return dict(wall=wall, cpu=cpu)


def lexical(prefix):
    """Declared grammar-only retrieval/copy control, not a learned LM."""
    import re

    history, question = prefix.rsplit("\n", 1)
    query = set(re.findall(r"[a-z0-9]+", question.casefold()))
    records = history.splitlines()
    ranked = sorted(
        enumerate(records),
        key=lambda row: (len(query & set(re.findall(r"[a-z0-9]+", row[1].casefold()))), row[0]),
        reverse=True,
    )
    output = "?"
    selected = None
    if ranked:
        index, text = ranked[0]
        overlap = query & set(re.findall(r"[a-z0-9]+", text.casefold()))
        if len(overlap) == 2 and "=" in text:
            output, selected = text.split("=", 1)[1], index
    return dict(
        generated_ids=[*(b + 3 for b in output.encode()), 2],
        history_bytes=len(history.encode()),
        input_ids=[1, *(b + 3 for b in prefix.encode())],
        scanned_bytes=len(prefix.encode()),
        selected_line=selected,
        model_parameters=0,
    )


def worker(root, directory, stage, seed, variant, ablation):
    verify(root, full_data=False, locked=stage not in {"contracts", "seal"})
    reg = read(root / "registration.json")
    if stage == "contracts":
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/test_segment_delta.py",
                "--basetemp",
                str(directory / "tmp"),
            ],
            cwd=ROOT,
            timeout=50,
        )
        worker_receipt(directory, STARTED, 0.0)
        return completed.returncode
    if stage == "lexical":
        generate(root, directory, None, True, True, reg["caps"]["request_seconds"])
        worker_receipt(directory, STARTED, 0.0)
        return 0
    from toruk_lm.engine import setup
    from toruk_lm.segment_delta import DeltaConfig, build_model
    from toruk_lm.segment_delta_training import FitConfig, fit, load

    setup(seed, 1)
    config = DeltaConfig(**reg["config"])
    if stage == "seal":
        contracts = read(root / "contracts/cost.json")
        if contracts["status"] != "PASS":
            raise ValueError("contract tests did not pass")
        names = list(reg["source_files"]) + [
            "src/toruk_lm/segment_delta.py",
            "src/toruk_lm/segment_delta_training.py",
            "scripts/segment_delta_study.py",
            "tests/test_segment_delta.py",
        ]
        sources = {n: sha(ROOT / n) for n in names}
        counts = {
            v: sum(p.numel() for p in build_model(v, config).parameters())
            for v in ("ordinary", "recurrent", "delta")
        }
        if counts != reg["parameters"] or max(counts.values()) / min(counts.values()) > 1.03:
            raise ValueError("registered parameter budget mismatch")
        snapshot = root / "implementation-sources"
        snapshot.mkdir()
        for name in names:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        save(
            root / "implementation-lock.json",
            dict(
                registration_sha256=sha(root / "registration.json"),
                sources=sources,
                parameters=counts,
                case_sha256={
                    row["id"]: hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
                    for row in read(root / "inputs.json")
                },
                contracts_sha256=sha(root / "contracts/cost.json"),
                status="SEALED_BEFORE_STUDY_TRAINING_AND_ANSWERS",
            ),
        )
        print("implementation_sha256", sha(root / "implementation-lock.json"))
        worker_receipt(directory, STARTED, time.perf_counter() - STARTED)
        return 0
    if stage == "train":
        path = root / "train.json"
        if sha(path) != reg["data"]["train.json"]:
            raise ValueError("training data identity mismatch")
        setup_wall = time.perf_counter() - STARTED
        result = fit(
            variant,
            config,
            FitConfig(seed=seed),
            read(path),
            directory / "checkpoint.pt",
            identity(root),
            steps=reg["train"]["steps"],
        )
        if result["parameters"] != reg["parameters"][variant]:
            raise ValueError("fitted parameter budget mismatch")
        save(directory / "training.json", result)
        save(
            directory / "checkpoint-meta.json",
            dict(
                sha256=sha(directory / "checkpoint.pt"),
                bytes=(directory / "checkpoint.pt").stat().st_size,
            ),
        )
        worker_receipt(directory, STARTED, setup_wall)
        return 0
    model, _, saved = load(checked_checkpoint(root, seed, variant), identity(root))
    if saved["next_step"] != 128 or saved["variant"] != variant or saved["fit"]["seed"] != seed:
        raise ValueError("checkpoint progress/variant/seed mismatch")
    model.eval()
    setup_wall = time.perf_counter() - STARTED
    read_memory, write_memory = ablation != "no-read", ablation != "no-write"
    if stage == "generate":
        generate(root, directory, model, read_memory, write_memory, reg["caps"]["request_seconds"])
    elif stage == "score":
        evaluate_losses(
            root, directory, model, seed, variant, ablation, reg["caps"]["request_seconds"]
        )
    else:
        raise ValueError("unknown stage")
    worker_receipt(directory, STARTED, setup_wall)
    return 0


def generate(root, directory, model, read_memory, write_memory, cap):
    # Explicitly no evaluator labels are opened in this function or its callers.
    from toruk_lm.segment_delta import ResearchSession

    reg = read(root / "registration.json")
    if sha(root / "inputs.json") != reg["data"]["inputs.json"]:
        raise ValueError("generation input identity mismatch")
    cases = read(root / "inputs.json")
    first = None
    with (directory / "predictions.jsonl").open("x", encoding="utf-8") as stream:
        for i, case in enumerate([*cases, cases[0]]):
            started, cpu = time.perf_counter(), time.process_time()
            if model is None:
                result = lexical(case["prefix"])
            else:
                result = ResearchSession(model, read=read_memory, write=write_memory).generate(
                    case["prefix"]
                )
            cost = timed_limit(started, cpu, cap)
            if i == 0:
                first = result
            if i == len(cases) and result != first:
                raise ValueError("deterministic prediction/work/state replay failure")
            stream.write(
                json.dumps(
                    dict(
                        id=case["id"],
                        prefix=case["prefix"],
                        replay=i == len(cases),
                        result=result,
                        cost=cost,
                    )
                )
                + "\n"
            )
            stream.flush()
    save(
        directory / "generation-seal.json",
        dict(sha256=sha(directory / "predictions.jsonl"), requests=len(cases) + 1, replay=True),
    )


def evaluation_name(seed, variant, ablation):
    return f"{seed}-{variant}-{ablation}"


def evaluate_losses(root, directory, model, seed, variant, ablation, cap):
    import torch

    from toruk_lm.segment_delta import document_loss

    name = evaluation_name(seed, variant, ablation)
    generation = root / "stages" / f"generate-{name}"
    if sha(generation / "predictions.jsonl") != read(generation / "generation-seal.json")["sha256"]:
        raise ValueError("raw generation seal mismatch")
    labels = read(root / "labels-evaluator-only.json")
    predictions = rows(generation / "predictions.jsonl")[:-1]
    prose = read(root / "dev-prose.json")
    reg = read(root / "registration.json")
    for filename in ("labels-evaluator-only.json", "dev-prose.json"):
        if sha(root / filename) != reg["data"][filename]:
            raise ValueError("evaluator data identity mismatch")
    totals = dict(
        factual_loss=0.0,
        factual_targets=0,
        answer_loss=0.0,
        answer_targets=0,
        prose_loss=0.0,
        prose_targets=0,
    )
    with torch.no_grad(), (directory / "losses.jsonl").open("x", encoding="utf-8") as stream:
        for prediction, label in zip(predictions, labels, strict=True):
            if prediction["id"] != label["id"]:
                raise ValueError("case/label order mismatch")
            started, cpu = time.perf_counter(), time.process_time()
            prefix = prediction["prefix"]
            loss, count, answer, n_answer = document_loss(
                model,
                prefix + label["gold"],
                read=ablation != "no-read",
                write=ablation != "no-write",
                answer_start=len(prefix.encode()),
            )
            cost = timed_limit(started, cpu, cap)
            row = dict(
                id=label["id"],
                category=label["category"],
                gold=label["gold"],
                correct=score(prediction["result"]["generated_ids"], label["gold"]),
                distance=label["distance"],
                gap_segments=label["gap_segments"],
                loss=float(loss),
                targets=count,
                answer_loss=float(answer),
                answer_targets=n_answer,
                cost=cost,
            )
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            totals["factual_loss"] += float(loss)
            totals["factual_targets"] += count
            totals["answer_loss"] += float(answer)
            totals["answer_targets"] += n_answer
        for case in prose:
            started, cpu = time.perf_counter(), time.process_time()
            loss, count, _, _ = document_loss(
                model, case["text"], read=ablation != "no-read", write=ablation != "no-write"
            )
            cost = timed_limit(started, cpu, cap)
            stream.write(
                json.dumps(
                    dict(id=case["id"], prose=True, loss=float(loss), targets=count, cost=cost)
                )
                + "\n"
            )
            stream.flush()
            totals["prose_loss"] += float(loss)
            totals["prose_targets"] += count
    save(directory / "loss-summary.json", totals)


def summarize(root, costs, shared):
    reg = read(root / "registration.json")
    labels = read(root / "labels-evaluator-only.json")
    summaries = {}
    for seed, variant in reg["fit_order"]:
        for ablation in ("full", "no-read", "no-write") if variant == "delta" else ("full",):
            name = evaluation_name(seed, variant, ablation)
            generated = rows(root / "stages" / f"generate-{name}" / "predictions.jsonl")
            evaluated = rows(root / "stages" / f"score-{name}" / "losses.jsonl")[:24]
            losses = read(root / "stages" / f"score-{name}" / "loss-summary.json")
            training = costs[f"train-{seed}-{variant}"]
            total = {
                key: sum(costs[f"{stage}-{name}"][key] for stage in ("generate", "score"))
                for key in ("cpu", "wall")
            }
            categories = {
                c: sum(row["correct"] for row in evaluated if row["category"] == c)
                for c in CATEGORIES
            }
            correct = sum(categories.values())
            distant = [
                r
                for r in evaluated
                if r["category"] in {"distant", "correction", "related_field", "exact_copy"}
            ]
            bins = {
                tag: dict(
                    correct=sum(r["correct"] for r in distant if low <= r["distance"] <= high),
                    count=sum(low <= r["distance"] <= high for r in distant),
                )
                for tag, low, high in (
                    ("25..64", 25, 64),
                    ("65..96", 65, 96),
                    ("97..128", 97, 128),
                    ("129+", 129, 10000),
                )
            }
            summaries[name] = dict(
                seed=seed,
                variant=variant,
                ablation=ablation,
                correct=correct,
                categories=categories,
                long_correct=sum(r["correct"] for r in distant),
                distance_bins=bins,
                prose_nll=losses["prose_loss"] / losses["prose_targets"],
                factual_nll=losses["factual_loss"] / losses["factual_targets"],
                answer_nll=losses["answer_loss"] / losses["answer_targets"],
                eval_cpu=total["cpu"] + shared["cpu"] / 10,
                eval_wall=total["wall"] + shared["wall"] / 10,
                eval_unallocated=total,
                train_cpu=training["cpu"],
                train_wall=training["wall"],
                checkpoint=read(checkpoint(root, seed, variant).with_name("checkpoint-meta.json")),
                training=read(checkpoint(root, seed, variant).with_name("training.json")),
                peak_private=max(
                    costs[f"{stage}-{name}"]["peak_private"] for stage in ("generate", "score")
                ),
                worker_setup={
                    stage: read(root / "stages" / f"{stage}-{name}" / "worker.json")[
                        "cold_setup_wall"
                    ]
                    for stage in ("generate", "score")
                },
                work={
                    key: sum(row["result"][key] for row in generated)
                    for key in (
                        "tokens_read",
                        "forward_positions",
                        "recomputed_positions",
                        "commits",
                        "read_positions",
                        "write_positions",
                    )
                },
                input_ids=sum(len(row["result"]["input_ids"]) for row in generated),
                output_ids=sum(len(row["result"]["generated_ids"]) for row in generated),
                teacher_forced_positions=losses["factual_targets"] + losses["prose_targets"],
                unsupported_unknowns=4 - categories["unknown"],
                failures=[
                    dict(
                        id=r["id"],
                        category=r["category"],
                        gold=r["gold"],
                        generated_ids=p["result"]["generated_ids"],
                    )
                    for r, p in zip(evaluated, generated[:24], strict=True)
                    if not r["correct"]
                ],
            )
    decisions = {}
    for seed in (113, 227):
        decisions[str(seed)] = gates(
            *[
                summaries[evaluation_name(seed, variant, ablation)]
                for variant, ablation in (
                    ("delta", "full"),
                    ("ordinary", "full"),
                    ("recurrent", "full"),
                    ("delta", "no-read"),
                    ("delta", "no-write"),
                )
            ]
        )
    lex = rows(root / "stages/lexical/predictions.jsonl")
    lexical_results = dict(
        correct=sum(
            score(p["result"]["generated_ids"], label["gold"])
            for p, label in zip(lex[:24], labels, strict=True)
        ),
        categories={
            c: sum(
                score(p["result"]["generated_ids"], label["gold"])
                for p, label in zip(lex[:24], labels, strict=True)
                if label["category"] == c
            )
            for c in CATEGORIES
        },
        cost=costs["lexical"],
        input_ids=sum(len(r["result"]["input_ids"]) for r in lex),
        output_ids=sum(len(r["result"]["generated_ids"]) for r in lex),
        scanned_bytes=sum(r["result"]["scanned_bytes"] for r in lex),
        peak_history_bytes=max(r["result"]["history_bytes"] for r in lex),
    )
    save(
        root / "summary.json",
        dict(
            cells=summaries,
            gates=decisions,
            lexical=lexical_results,
            shared=shared,
            advance=all(all(g.values()) for g in decisions.values()),
            registration_sha256=sha(root / "registration.json"),
            implementation_sha256=sha(root / "implementation-lock.json"),
        ),
    )


def run(root):
    registration = verify(root)
    save(
        root / "run-start.json",
        dict(registration_sha256=sha(root / "registration.json"), single_use=True),
    )
    start, cpu_start = time.perf_counter(), time.process_time()
    caps = registration["caps"]
    prep = [read(root / name / "cost.json") for name in ("prepare", "contracts", "seal")]
    if any(r["status"] != "PASS" for r in prep):
        raise ValueError("pre-training gate failed")
    prior = {k: sum(r[k] for r in prep) for k in ("wall", "cpu")}
    costs = {}
    stages = [
        (f"train-{seed}-{v}", "train", seed, v, "full", caps["fit_seconds"])
        for seed, v in registration["fit_order"]
    ]
    for seed, variant in registration["fit_order"]:
        for ablation in ("full", "no-read", "no-write") if variant == "delta" else ("full",):
            name = evaluation_name(seed, variant, ablation)
            stages.append(
                (f"generate-{name}", "generate", seed, variant, ablation, caps["eval_seconds"])
            )
            stages.append(
                (f"score-{name}", "score", seed, variant, ablation, caps["score_seconds"])
            )
    stages.append(("lexical", "lexical", 113, "ordinary", "full", caps["eval_seconds"]))
    failure = None
    try:
        for name, stage, seed, variant, ablation, cap in stages:
            verify(root)
            elapsed = time.perf_counter() - start + prior["wall"]
            used_cpu = (
                sum(r["cpu"] for r in costs.values())
                + time.process_time()
                - cpu_start
                - sum(r["controller_cpu"] for r in costs.values())
                + prior["cpu"]
            )
            remaining = min(caps["total_seconds"] - elapsed, caps["total_seconds"] - used_cpu)
            if remaining <= 0:
                raise TimeoutError("registered overall cap")
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "worker",
                "--root",
                str(root),
                "--directory",
                str(root / "stages" / name),
                "--stage",
                stage,
                "--seed",
                str(seed),
                "--variant",
                variant,
                "--ablation",
                ablation,
            ]
            result = watch(
                command,
                root / "stages" / name,
                root,
                min(cap, remaining),
                caps["private_bytes"],
                caps["disk_bytes"],
            )
            costs[name] = result
            print(json.dumps(dict(stage=name, **result)), flush=True)
            if result["status"] != "PASS":
                raise RuntimeError(f"stage stopped: {name}")
        shared = {
            "wall": prior["wall"]
            + time.perf_counter()
            - start
            - sum(r["wall"] for r in costs.values()),
            "cpu": prior["cpu"]
            + time.process_time()
            - cpu_start
            - sum(r["controller_cpu"] for r in costs.values()),
        }
        summarize(root, costs, shared)
        verify(root)
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    disjoint_cpu = (
        time.process_time() - cpu_start - sum(r["controller_cpu"] for r in costs.values())
    )
    wall = time.perf_counter() - start + prior["wall"]
    cpu = sum(r["cpu"] for r in costs.values()) + disjoint_cpu + prior["cpu"]
    if (
        wall > caps["total_seconds"]
        or cpu > caps["total_seconds"]
        or disjoint_cpu > caps["controller_seconds"]
    ):
        failure = failure or "overall/controller cap"
    save(
        root / "run-cost.json",
        dict(
            status="STOP" if failure else "COMPLETED",
            failure=failure,
            wall=wall,
            cpu=cpu,
            disjoint_controller_cpu=disjoint_cpu,
            stage_count=len(costs),
            stages=costs,
            prior_cost=prior,
            quality_advance=read(root / "summary.json")["advance"]
            if (root / "summary.json").exists()
            else False,
        ),
    )
    if failure:
        raise RuntimeError(failure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("contracts", "seal", "run", "worker"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--stage")
    parser.add_argument("--seed", type=int, default=113)
    parser.add_argument("--variant", default="ordinary")
    parser.add_argument("--ablation", default="full", choices=("full", "no-read", "no-write"))
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_relative_to(ROOT / "artifacts"):
        parser.error("run root must be within repository artifacts")
    if args.command == "run":
        run(root)
    elif args.command == "worker":
        if args.directory is None or not args.directory.resolve().is_relative_to(root):
            parser.error("worker directory must be within run")
        sys.exit(worker(root, args.directory, args.stage, args.seed, args.variant, args.ablation))
    else:
        reg = verify(root, locked=False)
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "worker",
            "--root",
            str(root),
            "--directory",
            str(root / args.command),
            "--stage",
            args.command,
        ]
        result = watch(
            command,
            root / args.command,
            root,
            reg["caps"][args.command + "_seconds"]
            if args.command == "seal"
            else reg["caps"]["tests_seconds"],
            reg["caps"]["private_bytes"],
            reg["caps"]["disk_bytes"],
        )
        print(json.dumps(result))
        sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
