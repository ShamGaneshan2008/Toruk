"""One registered training-only entity-dropout experiment; historical files stay immutable."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import value_start_replication_v2 as v2
from answer_trainability_dev import initial_hash, make_model, read, rows, runtime, save, sha
from lifetime_job import controller_record
from lifetime_job_v2 import verify_seal, watch_and_seal

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-entity-dropout-dev-v1"
OLD = ROOT / "artifacts/local-answer-value-start-replication-v2"
EXEC = RUN / "registered/execution"
SCRIPT = ROOT / "scripts/local_answer_entity_dropout.py"
PROTOCOL = "docs/research/local-answer-entity-dropout-dev-v1-protocol.md"
FORMAT = "toruk-local-answer-entity-dropout-dev-v1"
ORDER = [(s, v, "drop50" if a == "first16" else "uniform") for s, v, a in v2.ORDER]
CAPS = dict(
    fit=90, evaluate=40, development=40, overall=1800, request=2, memory=2147483648, disk=134217728
)
SOURCES = list(
    dict.fromkeys(
        [
            *v2.SOURCES,
            PROTOCOL,
            "scripts/local_answer_entity_dropout.py",
            "scripts/diagnose_value_start_v2.py",
            "scripts/audit_entity_dropout_dev.py",
            "tests/test_entity_dropout_dev.py",
        ]
    )
)


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def anonymize(doc: dict[str, Any], name: str) -> dict[str, Any]:
    prefix = doc["prefix"]
    require(len(name) == 3 and name in ("bek", "dov", "ral", "sun"), "known training entity")
    require(prefix.count(name) == 2 and "ref" not in prefix, "exactly two original mentions")
    result = dict(doc, prefix=prefix.replace(name, "ref"), text=doc["text"].replace(name, "ref"))
    require(len(result["prefix"].encode()) == len(prefix.encode()), "byte length")
    require(result["text"] == result["prefix"] + doc["gold"], "answer unchanged")
    return result


def chosen_view(arm: str, epoch: int, index: int) -> str:
    require(arm in ("uniform", "drop50"), "registered arm")
    return "anonymous" if arm == "drop50" and (epoch + index) % 2 == 0 else "original"


def preservation() -> int:
    inventory = read(OLD / "review-inventory.json")["files"]
    for name, meta in inventory.items():
        path = ROOT / name
        require(path.stat().st_size == meta["bytes"] and sha(path) == meta["sha256"], name)
    return len(inventory)


def prepare() -> None:
    diagnosis = read(RUN / "saved-v2-diagnosis.json")
    require(diagnosis["integrity"]["measurement_integrity"] == "PASS", "saved diagnosis")
    preserved = preservation()
    names = (
        "train-inputs.json",
        "train-labels.json",
        "train-documents.json",
        "dev-inputs.json",
        "dev-labels.json",
        "schedules.json",
    )
    prior = read(OLD / "plan-final.json")
    for name in names:
        require(sha(OLD / name) == prior["data"][name], "v2 frozen data")
        with (RUN / name).open("xb") as stream:
            stream.write((OLD / name).read_bytes())
    docs, labels = read(RUN / "train-documents.json"), read(RUN / "train-labels.json")
    views = {
        d["id"]: dict(index=i, original=d, anonymous=anonymize(d, labels[i]["canonical"][0]))
        for i, d in enumerate(docs)
    }
    dev_cores = {tuple(d["canonical"]) for d in read(RUN / "dev-labels.json")}
    train_cores = {tuple(d["canonical"]) for d in labels}
    anonymous_cores = {("ref", *d["canonical"][1:]) for d in labels}
    require(not dev_cores & (train_cores | anonymous_cores), "canonical separation")
    save(RUN / "training-views.json", views)
    save(
        RUN / "overlap.json",
        dict(
            original_overlap=0, anonymous_overlap=0, reused_development=True, heldout_opened=False
        ),
    )
    sources = {}
    for name in SOURCES:
        path = RUN / "sources" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write((ROOT / name).read_bytes())
        sources[name] = sha(path)
    save(
        RUN / "plan.json",
        dict(
            format=FORMAT,
            sources=sources,
            runtime=runtime(),
            caps=CAPS,
            order=ORDER,
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            data={
                name: sha(RUN / name) for name in (*names, "training-views.json", "overlap.json")
            },
            diagnosis_sha256=sha(RUN / "saved-v2-diagnosis.json"),
            v2_registration_sha256=sha(OLD / "registration.json"),
            preservation_inventory_sha256=sha(OLD / "review-inventory.json"),
            preserved_files=preserved,
            initial_hashes=prior["initial_hashes"],
            config=v2.CONFIG,
            parameters=v2.PARAMETERS,
            tokenizer=prior["tokenizer"],
            steps=1536,
            valid_targets=692224,
            forward_positions=786432,
            anonymity_rule="(epoch+original-document-index)%2==0; training only",
            objective="uniform unweighted valid-token CE in both arms",
            status="DESIGN_FROZEN_BEFORE_REHEARSAL_OR_RESEARCH_FORWARD",
        ),
    )
    print(json.dumps(dict(plan_sha256=sha(RUN / "plan.json"), caps=CAPS)))


def check_plan() -> dict[str, Any]:
    plan = read(RUN / "plan.json")
    require(plan["runtime"] == runtime(), "runtime drift")
    for name, digest in plan["sources"].items():
        require(sha(ROOT / name) == sha(RUN / "sources" / name) == digest, "source drift: " + name)
    for name, digest in plan["data"].items():
        require(sha(RUN / name) == digest, "data drift: " + name)
    require(sha(RUN / "saved-v2-diagnosis.json") == plan["diagnosis_sha256"], "diagnosis drift")
    return dict(plan)


def check_registration() -> dict[str, Any]:
    check_plan()
    reg = read(RUN / "registration.json")
    require(reg["plan_sha256"] == sha(RUN / "plan.json"), "plan binding")
    for item in reg["prerequisite_seals"]:
        verify_seal(RUN / item["path"], expected_seal_sha256=item["sha256"])
    return dict(reg)


def checked_data(name: str, *, training: bool = False) -> Any:
    require(not training or name == "train-documents.json", "training loader")
    if name.startswith("dev-"):
        require(read(EXEC / "training-gate.json")["pass_gate"], "development gate closed")
    plan = read(RUN / "plan.json")
    require(name in plan["data"] and sha(RUN / name) == plan["data"][name], "frozen data")
    return read(RUN / name)


def rehearsal(directory: Path) -> None:
    check_plan()
    import torch

    from toruk_lm.engine import setup

    records: dict[str, Any] = {}
    for variant in v2.PARAMETERS:
        setup(918733, 1)
        model = make_model(variant)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, foreach=False, fused=False)
        before = initial_hash(model)
        dummy = [dict(prefix="X" * 62, text="X" * 63) for _ in range(8)]
        timings = []
        for _ in range(3):
            x, y, answer, first = v2.batch_tensors(dummy)
            x, y = torch.randint(3, 259, x.shape), torch.randint(3, 259, y.shape)
            optimizer.zero_grad(set_to_none=True)
            began, cpu = time.perf_counter(), time.process_time()
            loss, _ = v2.loss_from_logits(v2.forward_batch(model, x), y, answer, first, 0)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            require(torch.isfinite(loss), "rehearsal finite")
            timings.append(dict(cpu=time.process_time() - cpu, wall=time.perf_counter() - began))
        bound = 2 * max(max(t.values()) for t in timings[1:]) * 1536 + 20
        require(initial_hash(model) == before and not optimizer.state, "no rehearsal updates")
        records[variant] = dict(timings=timings, projected_fit=bound)
    result = dict(
        records=records,
        updates=0,
        study_examples_used=False,
        pass_gate=all(r["projected_fit"] <= 90 for r in records.values()),
    )
    save(directory / "rehearsal.json", result)
    require(result["pass_gate"], "fixed fit cap cannot accommodate rehearsal; no retry")


def command(action: str, *args: str) -> list[str]:
    return [sys.executable, "-B", str(SCRIPT), action, *args]


def receipt(path: Path, result: Any) -> dict[str, Any]:
    return dict(
        path=path.relative_to(RUN).as_posix(),
        sha256=result.seal_sha256,
        status=result.cost["status"],
        cpu=result.cost["cpu"],
        wall=result.cost["wall"],
    )


def resources_controller(directory: Path) -> None:
    with controller_record(directory):
        contracts = RUN / "preparation/contracts"
        argv = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_entity_dropout_dev.py",
            "tests/test_lifetime_job.py",
            "tests/test_lifetime_job_v2.py",
            "--basetemp",
            str(RUN / "pytest-tmp-preparation"),
        ]
        result = watch_and_seal(argv, contracts, RUN / "preparation", 60)
        require(result.cost["status"] == "PASS", "contracts STOP")
        trial = RUN / "preparation/rehearsal"
        rehearse = watch_and_seal(
            command("worker", "--kind", "rehearsal", "--directory", str(trial)),
            trial,
            RUN / "preparation",
            45,
        )
        save(
            RUN / "preparation-summary.json",
            dict(seals=[receipt(contracts, result), receipt(trial, rehearse)]),
        )
        require(rehearse.cost["status"] == "PASS", "rehearsal STOP")


def fit(directory: Path, seed: str, variant: str, arm: str) -> None:
    plan = check_plan()
    check_registration()
    require(
        read(RUN / "attempt-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
        "attempt marker",
    )
    import torch

    from toruk_lm.engine import setup

    setup(v2.CROSSED[seed]["initialization"], 1)
    model = make_model(variant)
    initial = initial_hash(model)
    require(initial == plan["initial_hashes"][f"{seed}-{variant}"], "initial hash parity")
    require(sum(p.numel() for p in model.parameters()) == v2.PARAMETERS[variant], "parameters")
    views = checked_data("training-views.json")
    batches = checked_data("schedules.json")[seed]
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=0.003,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
        foreach=False,
        fused=False,
    )
    began, cpu = time.perf_counter(), time.process_time()
    totals: Counter[str] = Counter()
    completed = 0
    try:
        with (directory / "training.jsonl").open("x", encoding="utf-8") as stream:
            for batch in batches:
                names = [chosen_view(arm, batch["epoch"], views[i]["index"]) for i in batch["ids"]]
                documents = [views[i][name] for i, name in zip(batch["ids"], names, strict=True)]
                optimizer.zero_grad(set_to_none=True)
                loss, stats = v2.objective(model, documents, 0)
                require(torch.isfinite(loss), "nonfinite loss")
                loss.backward()
                require(
                    all(
                        p.grad is not None and torch.isfinite(p.grad).all()
                        for p in model.parameters()
                    ),
                    "nonfinite/missing gradient",
                )
                norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
                optimizer.step()
                require(
                    all(torch.isfinite(p).all() for p in model.parameters()), "nonfinite parameters"
                )
                completed += 1
                totals.update(stats)
                v2.append(
                    stream,
                    dict(
                        **batch,
                        views=names,
                        objective=float(loss.detach()),
                        gradient_norm=norm,
                        **stats,
                    ),
                )
        require(
            completed == 1536
            and totals["forward_positions"] == 786432
            and totals["history_targets"] + totals["answer_targets"] == 692224,
            "matched token work",
        )
        final = initial_hash(model)
        if arm == "uniform":
            prior = read(
                OLD
                / "registered/execution/stages"
                / f"fit-{seed}-{variant}-uniform/training-summary.json"
            )
            require(final == prior["final_model_sha256"], "matched v2 control tensor parity")
        checkpoint = dict(
            format=FORMAT,
            registration=sha(RUN / "registration.json"),
            seed=seed,
            variant=variant,
            arm=arm,
            steps=completed,
            config=v2.CONFIG,
            model=model.state_dict(),
            optimizer=optimizer.state_dict(),
        )
        path = directory / "checkpoint.pt"
        with path.open("xb") as output:
            torch.save(checkpoint, output)
        save(directory / "checkpoint-meta.json", dict(sha256=sha(path), bytes=path.stat().st_size))
        save(
            directory / "training-summary.json",
            dict(
                initial_sha256=initial,
                final_model_sha256=final,
                steps=completed,
                totals=dict(totals),
                loop_cpu=time.process_time() - cpu,
                loop_wall=time.perf_counter() - began,
                target_tokens=692224,
                padded_forward_positions=786432,
                document_presentations=12288,
                v2_control_tensor_parity=arm == "uniform",
            ),
        )
    except BaseException as error:
        save(directory / "fit-failure.json", dict(error=repr(error), completed_steps=completed))
        with (directory / "checkpoint-partial.pt").open("xb") as output:
            torch.save(
                dict(
                    model=model.state_dict(),
                    optimizer=optimizer.state_dict(),
                    completed_steps=completed,
                    partial=True,
                ),
                output,
            )
        raise


def load(seed: str, variant: str, arm: str) -> Any:
    import torch

    from toruk_lm.engine import setup

    setup(v2.CROSSED[seed]["initialization"], 1)
    directory = EXEC / "stages" / f"fit-{seed}-{variant}-{arm}"
    path, meta = directory / "checkpoint.pt", read(directory / "checkpoint-meta.json")
    require(
        sha(path) == meta["sha256"] and path.stat().st_size == meta["bytes"], "checkpoint bytes"
    )
    saved = torch.load(path, weights_only=True, map_location="cpu")
    require(
        saved["format"] == FORMAT
        and saved["registration"] == sha(RUN / "registration.json")
        and (saved["seed"], saved["variant"], saved["arm"]) == (seed, variant, arm)
        and saved["steps"] == 1536
        and saved["config"] == v2.CONFIG,
        "checkpoint identity",
    )
    require(
        all(float(s["step"]) == 1536 for s in saved["optimizer"]["state"].values()),
        "optimizer steps",
    )
    model = make_model(variant)
    model.load_state_dict(saved["model"], strict=True)
    model.eval()
    return model


def evaluate(directory: Path, seed: str, variant: str, arm: str, split: str) -> None:
    check_registration()
    # Isolated worker adapters select new paths only; frozen source bytes are never edited.
    v2.RUN, v2.EXEC = RUN, EXEC
    v2.checked_data, v2.load = checked_data, load
    v2.evaluate(directory, seed, variant, arm, split)
    if arm == "uniform":
        old = (
            OLD
            / "registered/execution/stages"
            / (("development" if split == "dev" else "evaluate") + f"-{seed}-{variant}-uniform")
        )
        for mode in ("main", "question-only") if split == "dev" else ("main",):
            current, prior = (
                rows(directory / f"predictions-{mode}.jsonl"),
                rows(old / f"predictions-{mode}.jsonl"),
            )
            require(
                all(
                    a["input_ids"] == b["input_ids"] and a["result"] == b["result"]
                    for a, b in zip(current, prior, strict=True)
                ),
                "v2 control native prediction parity",
            )
    costs: dict[str, Any] = {}
    for mode in ("main", "question-only") if split == "dev" else ("main",):
        raw = rows(directory / f"predictions-{mode}.jsonl")
        costs[mode] = dict(
            requests=len(raw),
            input_tokens=sum(len(p["input_ids"]) for p in raw),
            generated_tokens=sum(len(p["result"]["generated_ids"]) for p in raw),
            forward_positions=sum(p["result"]["forward_positions"] for p in raw),
            cpu=sum(p["cost"]["cpu"] for p in raw),
            wall=sum(p["cost"]["wall"] for p in raw),
        )
    vectors, teacher = (
        rows(directory / "first-vectors.jsonl"),
        rows(directory / "teacher-losses.jsonl"),
    )
    measurement_costs = rows(directory / "first-measurements.jsonl")
    costs["first_vectors"] = dict(
        requests=len(vectors),
        input_tokens=sum(len(v["input_ids"]) for v in vectors),
        forward_positions=sum(len(v["input_ids"]) for v in vectors),
        cpu=sum(m["cost"]["cpu"] for m in measurement_costs),
        wall=sum(m["cost"]["wall"] for m in measurement_costs),
    )
    costs["teacher"] = dict(
        requests=len(teacher),
        target_tokens=sum(t["history_targets"] + t["answer_targets"] for t in teacher),
        forward_positions=64 * len(teacher),
        cpu=sum(t["cost"]["cpu"] for t in teacher),
        wall=sum(t["cost"]["wall"] for t in teacher),
    )
    save(directory / "token-costs.json", costs)


def pair_gate(control: dict[str, Any], candidate: dict[str, Any]) -> bool:
    gain = candidate["exact"] - control["exact"]
    return bool(
        gain >= 0
        and (control["exact"] == 24 or gain > 0)
        and candidate["eos"] >= control["eos"]
        and all(
            candidate["categories"][c] >= control["categories"][c]
            for c in ("city", "code", "unknown")
        )
    )


def compare(development: dict[str, Any]) -> dict[str, Any]:
    pairs, city_nll = {}, {}
    for seed in v2.CROSSED:
        for variant in v2.PARAMETERS:
            control, candidate = (
                development[f"{seed}-{variant}-{a}"] for a in ("uniform", "drop50")
            )
            gain = candidate["exact"] - control["exact"]
            pairs[f"{seed}-{variant}"] = dict(
                gain=gain,
                ceiling=control["exact"] == 24,
                pass_pair=pair_gate(control, candidate),
            )
        if seed.startswith("i601-"):
            means = {}
            city_ids = {r["id"] for r in read(RUN / "dev-labels.json") if r["category"] == "city"}
            for arm in ("uniform", "drop50"):
                directory = EXEC / "stages" / f"development-{seed}-recurrent-{arm}"
                teacher = rows(directory / "teacher-losses.jsonl")
                means[arm] = sum(r["first_loss"] for r in teacher if r["id"] in city_ids) / 8
            city_nll[seed] = dict(**means, improved=means["drop50"] < means["uniform"])
    floors = all(v2.development_floor(m) for k, m in development.items() if k.endswith("-drop50"))
    model_gains = {
        v: sum(p["gain"] for key, p in pairs.items() if key.endswith("-" + v))
        for v in v2.PARAMETERS
    }
    passed = (
        floors
        and all(p["pass_pair"] for p in pairs.values())
        and all(g > 0 for g in model_gains.values())
    )
    passed &= all(m["improved"] for m in city_nll.values())
    return dict(
        pass_gate=passed,
        candidate_floors=floors,
        pairs=pairs,
        model_gains=model_gains,
        recurrent601_city_first_nll=city_nll,
    )


def stage(kind: str, seed: str, variant: str, arm: str, ledger: Any) -> Path:
    name = f"{kind}-{seed}-{variant}-{arm}"
    directory = EXEC / "stages" / name
    result = watch_and_seal(
        command(
            "worker",
            "--kind",
            kind,
            "--seed",
            seed,
            "--variant",
            variant,
            "--arm",
            arm,
            "--directory",
            str(directory),
        ),
        directory,
        RUN / "registered",
        CAPS[kind],
    )
    v2.append(ledger, dict(stage=name, **receipt(directory, result)))
    require(result.cost["status"] == "PASS", "stage STOP: " + name)
    print(
        json.dumps(dict(stage=name, cpu=result.cost["cpu"], wall=result.cost["wall"])), flush=True
    )
    return directory


def controller() -> None:
    check_registration()
    training, development = {}, {}
    with controller_record(EXEC), (EXEC / "stages.jsonl").open("x", encoding="utf-8") as ledger:
        try:
            for seed, variant, arm in ORDER:
                stage("fit", seed, variant, arm, ledger)
                directory = stage("evaluate", seed, variant, arm, ledger)
                training[f"{seed}-{variant}-{arm}"] = read(directory / "metrics.json")
            gate = all(v2.mastery(m) for m in training.values()) and len(training) == 16
            save(
                EXEC / "training-gate.json",
                dict(pass_gate=gate, mastery={k: v2.mastery(m) for k, m in training.items()}),
            )
            if gate:
                for seed, variant, arm in ORDER:
                    directory = stage("development", seed, variant, arm, ledger)
                    development[f"{seed}-{variant}-{arm}"] = read(directory / "metrics.json")
            comparison = compare(development) if gate else dict(pass_gate=False, evaluated=False)
            save(
                EXEC / "summary.json",
                dict(
                    training=training,
                    development=development,
                    training_gate=gate,
                    comparison=comparison,
                    decision="STOP_TRAINING_FAILURE"
                    if not gate
                    else "DEVELOPMENT_GATES_PASS"
                    if comparison["pass_gate"]
                    else "STOP_DEVELOPMENT_FAILURE",
                ),
            )
        except BaseException as error:
            save(
                EXEC / "failure.json",
                dict(
                    error=repr(error),
                    decision="BLOCKED",
                    training=training,
                    development=development,
                ),
            )
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=(
            "prepare",
            "resources",
            "resources-controller",
            "register",
            "launch",
            "budget",
            "controller",
            "worker",
        ),
    )
    parser.add_argument("--kind", choices=("rehearsal", "fit", "evaluate", "development"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--seed", choices=tuple(v2.CROSSED), default=next(iter(v2.CROSSED)))
    parser.add_argument("--variant", choices=tuple(v2.PARAMETERS), default="ordinary")
    parser.add_argument("--arm", choices=("uniform", "drop50"), default="uniform")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "resources":
        check_plan()
        directory = RUN / "preparation/budget"
        result = watch_and_seal(
            command("resources-controller", "--directory", str(directory)),
            directory,
            RUN / "preparation",
            180,
        )
        save(RUN / "preparation-budget-receipt.json", receipt(directory, result))
        require(result.cost["status"] == "PASS", "preparation STOP")
    elif args.action == "resources-controller":
        resources_controller(args.directory)
    elif args.action == "register":
        check_plan()
        preservation()
        seals = [
            *read(RUN / "preparation-summary.json")["seals"],
            read(RUN / "preparation-budget-receipt.json"),
        ]
        require(all(r["status"] == "PASS" for r in seals), "prerequisite STOP")
        for r in seals:
            verify_seal(RUN / r["path"], expected_seal_sha256=r["sha256"])
        save(
            RUN / "registration.json",
            dict(
                plan_sha256=sha(RUN / "plan.json"),
                caps=CAPS,
                order=ORDER,
                prerequisite_seals=seals,
                status="FROZEN_BEFORE_FIT_1",
            ),
        )
        print(json.dumps(dict(registration_sha256=sha(RUN / "registration.json"))))
    elif args.action == "launch":
        check_registration()
        save(
            RUN / "attempt-start.json",
            dict(
                registration_sha256=sha(RUN / "registration.json"),
                max_fits=16,
                max_updates=24576,
                no_retries=True,
            ),
        )
        directory = RUN / "registered/budget"
        result = watch_and_seal(
            command("budget", "--directory", str(directory)), directory, RUN / "registered", 1800
        )
        save(RUN / "registered-budget-receipt.json", receipt(directory, result))
        print(json.dumps(receipt(directory, result)), flush=True)
        require(result.cost["status"] == "PASS", "registered budget STOP")
    elif args.action == "budget":
        with controller_record(args.directory):
            result = watch_and_seal(command("controller"), EXEC, RUN / "registered", 1800)
            save(RUN / "execution-receipt.json", receipt(EXEC, result))
            require(result.cost["status"] == "PASS", "execution STOP")
    elif args.action == "controller":
        controller()
    else:
        require(
            args.directory and args.directory.resolve().is_relative_to(RUN), "new study output only"
        )
        with controller_record(args.directory):
            if args.kind == "rehearsal":
                rehearsal(args.directory)
            elif args.kind == "fit":
                fit(args.directory, args.seed, args.variant, args.arm)
            else:
                evaluate(
                    args.directory,
                    args.seed,
                    args.variant,
                    args.arm,
                    "dev" if args.kind == "development" else "train",
                )


if __name__ == "__main__":
    main()
