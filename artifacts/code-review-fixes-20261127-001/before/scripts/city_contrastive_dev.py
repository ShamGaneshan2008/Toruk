"""Single-use city contrastive objective study; isolated adapters preserve v2 bytes."""

from __future__ import annotations

import argparse
import contextlib
import functools
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import value_start_replication_v2 as v2
from answer_trainability_dev import (
    forward_batch,
    initial_hash,
    make_model,
    read,
    rows,
    runtime,
    save,
    sha,
)
from lifetime_job import controller_record
from lifetime_job_v2 import verify_seal, watch_and_seal

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-city-contrastive-dev-v1"
OLD = ROOT / "artifacts/local-answer-value-start-replication-v2"
DIAG = ROOT / "artifacts/value-start-v2-diagnosis-20261127-001"
EXEC = RUN / "registered/execution"
SCRIPT = ROOT / "scripts/city_contrastive_dev.py"
PROTOCOL = "docs/research/local-answer-city-contrastive-dev-v1-protocol.md"
FORMAT = "toruk-local-answer-city-contrastive-dev-v1"
CAPS = dict(
    fit=90, evaluate=30, development=30, overall=1800, request=2, memory=2147483648, disk=134217728
)
ORDER = [(s, v, "control" if a == "uniform" else "contrast") for s, v, a in v2.ORDER]
SOURCES = list(
    dict.fromkeys(
        [
            *v2.SOURCES,
            PROTOCOL,
            "scripts/city_contrastive_dev.py",
            "scripts/audit_city_contrastive_dev.py",
            "tests/test_city_contrastive_dev.py",
        ]
    )
)
BASE_OBJECTIVE = v2.objective


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def confuser_map(labels: list[dict[str, Any]]) -> dict[str, int]:
    """Training labels only; never derive a confuser from development errors."""
    require(labels and all(r["id"].startswith("v2-train-") for r in labels), "training labels only")
    values: dict[str, set[str]] = {}
    for label in labels:
        if label["category"] == "city":
            values.setdefault(label["canonical"][0], set()).add(label["gold"])
    require(all(len(v) == 2 for v in values.values()), "two training city values per entity")
    result = {}
    for label in labels:
        if label["category"] == "city":
            other = next(iter(values[label["canonical"][0]] - {label["gold"]}))
            require(other.encode()[0] != label["gold"].encode()[0], "distinct first bytes")
            result[label["id"]] = other.encode()[0] + 3
    return result


def contrastive_loss(
    logits: Any, y: Any, first: Any, documents: list[dict[str, Any]], confusers: dict[str, int]
) -> tuple[Any, list[dict[str, Any]]]:
    import torch
    from torch.nn import functional as F

    selected = [i for i, doc in enumerate(documents) if doc["id"] in confusers]
    if not selected:
        return logits.new_zeros(()), []
    positions = first.long().argmax(1)
    gold_ids = [int(y[i, positions[i]]) for i in selected]
    other_ids = [confusers[documents[i]["id"]] for i in selected]
    gold = torch.stack(
        [logits[i, positions[i], g] for i, g in zip(selected, gold_ids, strict=True)]
    )
    other = torch.stack(
        [logits[i, positions[i], c] for i, c in zip(selected, other_ids, strict=True)]
    )
    loss = F.softplus(2 + other - gold).mean()
    records = [
        dict(
            id=documents[i]["id"],
            gold_id=g,
            confuser_id=c,
            gold_logit=float(zg),
            confuser_logit=float(zc),
        )
        for i, g, c, zg, zc in zip(
            selected,
            gold_ids,
            other_ids,
            gold.detach().tolist(),
            other.detach().tolist(),
            strict=True,
        )
    ]
    return loss, records


def objective(
    model: Any, documents: list[dict[str, Any]], extra: int, *, arm: str, confusers: dict[str, int]
) -> tuple[Any, dict[str, Any]]:
    if extra == 0:  # Evaluation must retain the unweighted teacher-loss path, without training IDs.
        return BASE_OBJECTIVE(model, documents, 0)
    require(extra == 15 and arm in ("control", "contrast"), "frozen objective")
    x, y, answer, first = v2.batch_tensors(documents)
    logits = forward_batch(model, x)
    ce, stats = v2.loss_from_logits(logits, y, answer, first, 15)
    auxiliary, records = contrastive_loss(logits, y, first, documents, confusers)
    stats.update(
        forward_positions=x.numel(),
        ce_objective=float(ce.detach()),
        city_loss=float(auxiliary.detach()),
        city_records=records,
        city_contributions=len(records),
    )
    return (ce + 0.1 * auxiliary if arm == "contrast" else ce), stats


def check_plan() -> dict[str, Any]:
    plan = read(RUN / "plan-final.json")
    require(runtime() == plan["runtime"], "runtime drift")
    for name, digest in plan["sources"].items():
        require(sha(ROOT / name) == sha(RUN / "sources" / name) == digest, "source drift: " + name)
    for name, digest in plan["data"].items():
        require(sha(RUN / name) == digest, "data drift: " + name)
    return dict(plan)


def checked_data(name: str, training: bool = False) -> Any:
    if training:
        require(name == "train-documents.json", "training documents only")
    plan = check_plan()
    require(name in plan["data"], "registered input only")
    return read(RUN / name)


def check_registration() -> dict[str, Any]:
    check_plan()
    reg = read(RUN / "registration.json")
    require(reg["plan_sha256"] == sha(RUN / "plan-final.json"), "registration binding")
    require(reg["caps"] == CAPS and reg["order"] == [list(x) for x in ORDER], "caps/order drift")
    for item in reg["prerequisite_seals"]:
        verify_seal(RUN / item["path"], expected_seal_sha256=item["sha256"])
        require(read(RUN / item["path"] / "cost.json")["status"] == "PASS", "prerequisite STOP")
    return dict(reg)


@contextlib.contextmanager
def adapter(arm: str) -> Iterator[None]:
    """Process-local paths/objective only; restore globals even if a worker fails."""
    mapping = read(RUN / "confusers.json")
    changes = dict(
        RUN=RUN,
        EXEC=EXEC,
        FORMAT=FORMAT,
        WEIGHTS=dict(control=15, contrast=15),
        check_plan=check_plan,
        check_registration=check_registration,
        checked_data=checked_data,
        objective=functools.partial(objective, arm=arm, confusers=mapping),
    )
    prior = {name: getattr(v2, name) for name in changes}
    try:
        for name, value in changes.items():
            setattr(v2, name, value)
        yield
    finally:
        for name, value in prior.items():
            setattr(v2, name, value)


def preservation() -> int:
    inventory = read(OLD / "review-inventory.json")["files"]
    for name, meta in inventory.items():
        require(
            (ROOT / name).stat().st_size == meta["bytes"] and sha(ROOT / name) == meta["sha256"],
            "historical preservation: " + name,
        )
    for name, digest in read(RUN / "starting-state.json")["files"].items():
        require(sha(ROOT / name) == digest, "existing edits changed: " + name)
    return len(inventory)


def prepare() -> None:
    import audit_value_start_replication_v2 as audit

    require(not (RUN / "plan-final.json").exists(), "plan exists; overwrite refused")
    diagnosis = read(DIAG / "diagnosis.json")
    require(diagnosis["summary"]["all_begin_at_first_answer_token"], "testable hypothesis absent")
    require(diagnosis["integrity"]["decision"] == "STOP_DEVELOPMENT_FAILURE", "diagnosis")
    prior = read(OLD / "plan-final.json")
    require(runtime() == prior["runtime"], "original runtime required")
    save(RUN / "precondition.json", audit.audit())
    protected = preservation()
    for name, digest in prior["data"].items():
        require(sha(OLD / name) == digest, "v2 data hash")
        with (RUN / name).open("xb") as stream:
            stream.write((OLD / name).read_bytes())
    labels = read(RUN / "train-labels.json")
    save(RUN / "confusers.json", confuser_map(labels))
    require(
        not {tuple(r["canonical"]) for r in labels}
        & {tuple(r["canonical"]) for r in read(RUN / "dev-labels.json")},
        "canonical overlap",
    )
    sources = {}
    for name in SOURCES:
        target = RUN / "sources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write((ROOT / name).read_bytes())
        sources[name] = sha(target)
    save(
        RUN / "plan-final.json",
        dict(
            format=FORMAT,
            sources=sources,
            data={name: sha(RUN / name) for name in (*prior["data"], "confusers.json")},
            runtime=runtime(),
            caps=CAPS,
            order=ORDER,
            initial_hashes=prior["initial_hashes"],
            config=v2.CONFIG,
            parameters=v2.PARAMETERS,
            crossed_seeds=v2.CROSSED,
            tokenizer=prior["tokenizer"],
            steps=1536,
            batch=8,
            coefficient=0.1,
            margin=2,
            rehearsal_seed=927113,
            source_commit=read(RUN / "starting-state.json")["head"],
            protected_v2_files=protected,
            diagnosis_sha256=sha(DIAG / "diagnosis.json"),
            proposal_sha256=sha(DIAG / "proposal.md"),
            precondition_sha256=sha(RUN / "precondition.json"),
            status="FROZEN_BEFORE_REHEARSAL_OR_STUDY_FORWARD",
        ),
    )


def command(*args: str) -> list[str]:
    return [sys.executable, "-B", str(SCRIPT), *args]


def receipt(directory: Path, result: Any) -> dict[str, Any]:
    return dict(
        path=directory.relative_to(RUN).as_posix(),
        sha256=result.seal_sha256,
        status=result.cost["status"],
        cpu=result.cost["cpu"],
        wall=result.cost["wall"],
    )


def rehearsal(directory: Path) -> None:
    check_plan()
    import torch

    from toruk_lm.engine import setup

    records: dict[str, Any] = {}
    dummy = [dict(id=f"dummy-{i}", prefix="X" * 62, text="X" * 63) for i in range(8)]
    confusers = {d["id"]: 4 for d in dummy}
    for variant in v2.PARAMETERS:
        for arm in ("control", "contrast"):
            setup(927113, 1)
            model = make_model(variant)
            optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, foreach=False, fused=False)
            before = initial_hash(model)
            iterations = []
            for _ in range(3):
                x, y, answer, first = v2.batch_tensors(dummy)
                x, y = torch.randint(3, 259, x.shape), torch.randint(5, 259, y.shape)
                x[:, 0], y[:, -1] = 1, 2
                optimizer.zero_grad(set_to_none=True)
                began, cpu = time.perf_counter(), time.process_time()
                logits = forward_batch(model, x)
                ce, _stats = v2.loss_from_logits(logits, y, answer, first, 15)
                aux, _records = contrastive_loss(logits, y, first, dummy, confusers)
                loss = ce + 0.1 * aux if arm == "contrast" else ce
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                require(
                    torch.isfinite(loss)
                    and all(
                        p.grad is not None and torch.isfinite(p.grad).all()
                        for p in model.parameters()
                    ),
                    "rehearsal finite",
                )
                iterations.append(
                    dict(cpu=time.process_time() - cpu, wall=time.perf_counter() - began)
                )
            require(initial_hash(model) == before and not optimizer.state, "zero-update rehearsal")
            bound = 2 * max(max(r.values()) for r in iterations[1:]) * 1536 + 20
            records[f"{variant}-{arm}"] = dict(iterations=iterations, projected_fit=bound)
    passed = all(r["projected_fit"] <= 90 for r in records.values())
    save(
        directory / "rehearsal.json",
        dict(
            seed=927113,
            records=records,
            optimizer_updates=0,
            study_examples_used=False,
            pass_rehearsal=passed,
        ),
    )
    require(passed, "rehearsal STOP_RESOURCE; no retry")


def resources_controller(directory: Path) -> None:
    with controller_record(directory):
        testdir = RUN / "preparation/contracts"
        result = watch_and_seal(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "tests/test_city_contrastive_dev.py",
                "tests/test_lifetime_job.py",
                "tests/test_lifetime_job_v2.py",
                "--basetemp",
                str(RUN / "preparation/pytest-temp"),
            ],
            testdir,
            RUN / "preparation",
            60,
        )
        items = [receipt(testdir, result)]
        require(result.cost["status"] == "PASS", "contracts failed; no rehearsal or fit")
        target = RUN / "preparation/rehearsal"
        result = watch_and_seal(
            command("worker", "--kind", "rehearsal", "--directory", str(target)),
            target,
            RUN / "preparation",
            45,
        )
        items.append(receipt(target, result))
        require(result.cost["status"] == "PASS", "rehearsal STOP; no retry")
        save(RUN / "preparation-summary.json", dict(status="PASS", seals=items))


def fit(directory: Path, seed: str, variant: str, arm: str) -> None:
    require(
        read(RUN / "attempt-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
        "registered single attempt",
    )
    with adapter(arm):
        v2.fit(directory, seed, variant, arm)
    if arm == "control":
        old = OLD / "registered/execution/stages" / f"fit-{seed}-{variant}-first16"
        matched = (
            read(directory / "training-summary.json")["final_model_sha256"]
            == read(old / "training-summary.json")["final_model_sha256"]
        )
        save(directory / "control-parity.json", dict(final_tensors=matched))
        require(matched, "STOP_CONTROL_REPRODUCTION: final tensors")


def evaluate(directory: Path, seed: str, variant: str, arm: str, split: str) -> None:
    if split == "dev" and arm == "contrast":
        require(read(EXEC / "control-development-gate.json")["pass_gate"], "control dev barrier")
    with adapter(arm):
        v2.evaluate(directory, seed, variant, arm, split)
    if arm == "control":
        old = (
            OLD
            / "registered/execution/stages"
            / (("development" if split == "dev" else "evaluate") + f"-{seed}-{variant}-first16")
        )
        parity = {}
        for mode in ("main", "question-only") if split == "dev" else ("main",):
            current, prior = (rows(p / f"predictions-{mode}.jsonl") for p in (directory, old))
            parity[mode] = all(
                a["input_ids"] == b["input_ids"] and a["result"] == b["result"]
                for a, b in zip(current, prior, strict=True)
            )
        save(directory / "control-parity.json", parity)
        require(all(parity.values()), "STOP_CONTROL_REPRODUCTION: native predictions")
    costs = {}
    for mode in ("main", "question-only") if split == "dev" else ("main",):
        raw = rows(directory / f"predictions-{mode}.jsonl")
        costs[mode] = dict(
            requests=len(raw),
            input_tokens=sum(len(r["input_ids"]) for r in raw),
            generated_tokens=sum(len(r["result"]["generated_ids"]) for r in raw),
            forward_positions=sum(r["result"]["forward_positions"] for r in raw),
            cpu=sum(r["cost"]["cpu"] for r in raw),
            wall=sum(r["cost"]["wall"] for r in raw),
        )
    vectors, teacher = (
        rows(directory / "first-vectors.jsonl"),
        rows(directory / "teacher-losses.jsonl"),
    )
    costs["vectors"] = dict(
        requests=len(vectors),
        input_tokens=sum(len(r["input_ids"]) for r in vectors),
        forward_positions=sum(len(r["input_ids"]) for r in vectors),
    )
    costs["teacher"] = dict(
        requests=len(teacher),
        targets=sum(r["history_targets"] + r["answer_targets"] for r in teacher),
        forward_positions=64 * len(teacher),
    )
    save(directory / "token-costs.json", costs)


def pair_gate(control: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    old, new = ({r["id"]: r["exact"] for r in m["cases"]} for m in (control, candidate))
    require(set(old) == set(new), "matched cases")
    introduced = [i for i in old if old[i] and not new[i]]
    fixed = [i for i in old if not old[i] and new[i]]
    gain = candidate["exact"] - control["exact"]
    passed = not introduced and (gain > 0 if control["exact"] < 24 else candidate["exact"] == 24)
    passed &= candidate["eos"] >= control["eos"] and all(
        candidate["categories"][k] >= control["categories"][k] for k in ("city", "code", "unknown")
    )
    return dict(
        pass_pair=bool(passed),
        gain=gain,
        introduced=introduced,
        fixed=fixed,
        ceiling=control["exact"] == 24,
    )


def comparison(development: dict[str, Any]) -> dict[str, Any]:
    pairs, nll = {}, {}
    for seed in v2.CROSSED:
        for variant in v2.PARAMETERS:
            key = f"{seed}-{variant}"
            pairs[key] = pair_gate(development[key + "-control"], development[key + "-contrast"])
        if seed.startswith("i601-"):
            city = {r["id"] for r in read(RUN / "dev-labels.json") if r["category"] == "city"}
            means = {
                a: sum(
                    r["first_loss"]
                    for r in rows(
                        EXEC / "stages" / f"development-{seed}-recurrent-{a}/teacher-losses.jsonl"
                    )
                    if r["id"] in city
                )
                / 8
                for a in ("control", "contrast")
            }
            nll[seed] = dict(**means, improved=means["contrast"] < means["control"])
    gains = {
        v: sum(p["gain"] for k, p in pairs.items() if k.endswith("-" + v)) for v in v2.PARAMETERS
    }
    floors = {k: v2.development_floor(m) for k, m in development.items() if k.endswith("-contrast")}
    passed = (
        all(p["pass_pair"] for p in pairs.values())
        and all(floors.values())
        and all(v > 0 for v in gains.values())
        and all(v["improved"] for v in nll.values())
    )
    return dict(
        pass_gate=passed,
        pairs=pairs,
        candidate_floors=floors,
        model_gains=gains,
        recurrent601_city_first_nll=nll,
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
    v2.append(
        ledger,
        dict(
            stage=name,
            path=directory.relative_to(EXEC).as_posix(),
            seal_sha256=result.seal_sha256,
            status=result.cost["status"],
            cpu=result.cost["cpu"],
            wall=result.cost["wall"],
        ),
    )
    require(result.cost["status"] == "PASS", "stage STOP: " + name)
    print(
        json.dumps(dict(stage=name, cpu=result.cost["cpu"], wall=result.cost["wall"])), flush=True
    )
    return directory


def controller() -> None:
    check_registration()
    training: dict[str, Any] = {}
    development: dict[str, Any] = {}
    with controller_record(EXEC), (EXEC / "stages.jsonl").open("x", encoding="utf-8") as ledger:
        try:
            for seed, variant, arm in ORDER:
                stage("fit", seed, variant, arm, ledger)
                directory = stage("evaluate", seed, variant, arm, ledger)
                training[f"{seed}-{variant}-{arm}"] = read(directory / "metrics.json")
            gate = all(v2.mastery(m) for m in training.values())
            save(
                EXEC / "training-gate.json",
                dict(pass_gate=gate, cells={k: v2.mastery(m) for k, m in training.items()}),
            )
            if gate:
                for arm in ("control", "contrast"):
                    for seed in v2.CROSSED:
                        for variant in v2.PARAMETERS:
                            d = stage("development", seed, variant, arm, ledger)
                            development[f"{seed}-{variant}-{arm}"] = read(d / "metrics.json")
                    if arm == "control":
                        save(EXEC / "control-development-gate.json", dict(pass_gate=True))
            result = comparison(development) if gate else dict(pass_gate=False)
            save(
                EXEC / "summary.json",
                dict(
                    training=training,
                    development=development,
                    training_gate=gate,
                    comparison=result,
                    decision="STOP_TRAINING_FAILURE"
                    if not gate
                    else "DEVELOPMENT_GATES_PASS"
                    if result["pass_gate"]
                    else "STOP_DEVELOPMENT_FAILURE",
                ),
            )
        except BaseException as error:
            save(
                EXEC / "failure.json",
                dict(error=repr(error), training=training, development=development),
            )
            raise


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
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
    p.add_argument("--directory", type=Path)
    p.add_argument("--kind", choices=("rehearsal", "fit", "evaluate", "development"))
    p.add_argument("--seed", choices=tuple(v2.CROSSED))
    p.add_argument("--variant", choices=tuple(v2.PARAMETERS))
    p.add_argument("--arm", choices=("control", "contrast"))
    a = p.parse_args()
    if a.action == "prepare":
        prepare()
    elif a.action == "resources":
        check_plan()
        target = RUN / "preparation/budget"
        result = watch_and_seal(
            command("resources-controller", "--directory", str(target)),
            target,
            RUN / "preparation",
            150,
        )
        save(RUN / "preparation-budget-receipt.json", receipt(target, result))
        require(result.cost["status"] == "PASS", "preparation STOP; no retry")
    elif a.action == "resources-controller":
        resources_controller(a.directory)
    elif a.action == "register":
        check_plan()
        preservation()
        items = [
            *read(RUN / "preparation-summary.json")["seals"],
            read(RUN / "preparation-budget-receipt.json"),
        ]
        for item in items:
            verify_seal(RUN / item["path"], expected_seal_sha256=item["sha256"])
            require(item["status"] == "PASS", "prerequisite STOP")
        save(
            RUN / "registration.json",
            dict(
                plan_sha256=sha(RUN / "plan-final.json"),
                caps=CAPS,
                order=ORDER,
                prerequisite_seals=items,
                status="FROZEN_BEFORE_FIT_1",
            ),
        )
    elif a.action == "launch":
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
        target = RUN / "registered/budget"
        result = watch_and_seal(
            command("budget", "--directory", str(target)), target, RUN / "registered", 1800
        )
        save(RUN / "registered-budget-receipt.json", receipt(target, result))
        require(result.cost["status"] == "PASS", "registered STOP; no retry")
    elif a.action == "budget":
        with controller_record(a.directory):
            result = watch_and_seal(command("controller"), EXEC, RUN / "registered", 1800)
            save(RUN / "execution-receipt.json", receipt(EXEC, result))
            require(result.cost["status"] == "PASS", "execution STOP; no retry")
    elif a.action == "controller":
        controller()
    else:
        require(a.directory and a.directory.resolve().is_relative_to(RUN), "new output only")
        with controller_record(a.directory):
            if a.kind == "rehearsal":
                rehearsal(a.directory)
            elif a.kind == "fit":
                fit(a.directory, a.seed, a.variant, a.arm)
            else:
                evaluate(
                    a.directory,
                    a.seed,
                    a.variant,
                    a.arm,
                    "dev" if a.kind == "development" else "train",
                )


if __name__ == "__main__":
    main()
