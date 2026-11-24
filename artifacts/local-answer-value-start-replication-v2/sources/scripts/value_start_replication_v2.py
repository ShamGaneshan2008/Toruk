"""One registered custom-LM intervention: first-answer-token weight16 versus uniform CE."""

from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import local_answer_dev as local
import value_start_replication_data as data
from answer_trainability_dev import (
    CONFIG,
    PARAMETERS,
    forward_batch,
    initial_hash,
    make_batch,
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
sys.path.insert(0, str(ROOT / "src"))
RUN = ROOT / "artifacts/local-answer-value-start-replication-v2"
EXEC = RUN / "registered" / "execution"
OLD = ROOT / "artifacts/local-answer-dev-v1"
PAIRED = ROOT / "artifacts/local-answer-paired-batch-dev-v1"
FORMAT = "toruk-local-answer-value-start-replication-v2"
PROTOCOL = "docs/research/local-answer-value-start-replication-v2-protocol.md"
WEIGHTS = {"uniform": 0, "first16": 15}
CROSSED = data.CROSSED
ORDER = [
    (seed, variant, arm)
    for index, seed in enumerate(CROSSED)
    for model_index, variant in enumerate(("ordinary", "recurrent"))
    for arm in (
        ("uniform", "first16") if (index + model_index) % 2 == 0 else ("first16", "uniform")
    )
]

STEPS = 1536
SOURCES = [
    PROTOCOL,
    "scripts/value_start_replication_data.py",
    "scripts/audit_value_start_replication_v2.py",
    "scripts/value_start_replication_v2.py",
    "tests/test_value_start_replication_v2.py",
    "tests/test_lifetime_job_v2.py",
    "tests/test_lifetime_job.py",
    "scripts/lifetime_job_v2.py",
    "scripts/lifetime_job.py",
    "scripts/local_answer_dev.py",
    "scripts/answer_trainability_dev.py",
    "scripts/segment_delta_watch.py",
    "scripts/first_byte_probe.py",
    "src/toruk_lm/owned_lm.py",
    "src/toruk_lm/model.py",
    "src/toruk_lm/recurrent.py",
    "src/toruk_lm/tokenizer.py",
    "src/toruk_lm/engine.py",
    "src/toruk_lm/data.py",
    "pyproject.toml",
    ".gitattributes",
]


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def append(stream: Any, value: Any) -> None:
    stream.write(json.dumps(value, allow_nan=False, sort_keys=True) + "\n")
    stream.flush()


def identity(seed: str, variant: str, arm: str) -> str:
    return f"{seed}-{variant}-{arm}"


def check_plan() -> dict[str, Any]:
    plan = read(RUN / "plan.json")
    require(plan["runtime"] == runtime(), "runtime changed")
    for name, expected in plan["sources"].items():
        require(sha(ROOT / name) == sha(RUN / "sources" / name) == expected, "source: " + name)
    for name, expected in plan["data"].items():
        require(sha(RUN / name) == expected, "data: " + name)
    return dict(plan)


def check_registration() -> dict[str, Any]:
    check_plan()
    reg = read(RUN / "registration.json")
    require(reg["plan_sha256"] == sha(RUN / "plan.json"), "registration/plan")
    for name, expected in reg["prerequisite_files"].items():
        require(sha(RUN / name) == expected, "prerequisite bytes")
    for receipt in reg["prerequisite_seals"]:
        verify_seal(RUN / receipt["path"], expected_seal_sha256=receipt["sha256"])
    return dict(reg)


def checked_data(name: str, *, training: bool = False) -> Any:
    if training:
        require(name == "train-documents.json", "training loader rejects non-training files")
    plan = read(RUN / "plan.json")
    require(name in plan["data"] and sha(RUN / name) == plan["data"][name], "data seal")
    value = read(RUN / name)
    if training:
        require(
            len(value) == 96 and all(d["split"] == "train" for d in value), "train-only documents"
        )
    return value


def prepare() -> None:
    precondition = read(RUN / "precondition.json")
    require(
        precondition["measurement_integrity"] == "PASS"
        and precondition["decision"] == "STOP_DEVELOPMENT_FAILURE",
        "committed v1 precondition",
    )
    files = data.datasets()
    prior = read(OLD / "train-labels.json") + read(OLD / "dev-labels.json")
    prior += read(ROOT / "artifacts/local-answer-value-start-dev-v1/dev-labels.json")
    overlap = data.validate(files, prior)
    save(RUN / "overlap.json", overlap)
    for name, value in files.items():
        save(RUN / name, value)
    schedules = {key: data.schedule(files, axes["shuffle"]) for key, axes in CROSSED.items()}
    save(RUN / "schedules.json", schedules)
    protected = read(ROOT / "artifacts/local-answer-value-start-dev-v1/review-inventory.json")[
        "files"
    ]
    for name, meta in protected.items():
        require(
            (ROOT / name).stat().st_size == meta["bytes"] and sha(ROOT / name) == meta["sha256"],
            "v1 preserved",
        )
    save(RUN / "preservation-before.json", dict(files=protected))
    hashes = {}
    for name in SOURCES:
        target = RUN / "sources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write((ROOT / name).read_bytes())
        hashes[name] = sha(target)
    oldreg = read(OLD / "registration.json")
    initial = {
        f"{key}-{variant}": read(
            OLD / "stages" / f"train-{axes['initialization']}-{variant}" / "training-summary.json"
        )["initial_sha256"]
        for key, axes in CROSSED.items()
        for variant in PARAMETERS
    }
    save(
        RUN / "plan.json",
        dict(
            format=FORMAT,
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            sources=hashes,
            data={name: sha(RUN / name) for name in (*files, "schedules.json")},
            runtime=runtime(),
            config=CONFIG,
            parameters=PARAMETERS,
            initial_hashes=initial,
            tokenizer=oldreg["tokenizer"],
            crossed_seeds=CROSSED,
            order=ORDER,
            weights=WEIGHTS,
            steps=1536,
            batch=8,
            optimizer=dict(
                lr=0.003,
                betas=[0.9, 0.999],
                eps=1e-8,
                weight_decay=0.01,
                clip=1.0,
                foreach=False,
                fused=False,
            ),
            preservation_sha256=sha(RUN / "preservation-before.json"),
            precondition_sha256=sha(RUN / "precondition.json"),
            overlap_sha256=sha(RUN / "overlap.json"),
            resource_rule=(
                "fit_cap=max(60,ceil(max(2*max(last-two CPU/wall)*1536+20)/10)*10); <=120"
            ),
            max_caps=dict(
                fit=120,
                evaluate=30,
                development=30,
                request=2,
                overall=1800,
                rehearsal=45,
                contracts=60,
                preparation=150,
                memory=2147483648,
                disk=134217728,
            ),
            training_gate=(
                "ALL eight first16 cells exact96/EOS96/zero first errors,malformed,repetition; "
                "ALL eight controls exact>=90/EOS96/zero malformed,repetition"
            ),
            development_gate=(
                "ALL eight candidates exact>=22,city>=7,code>=7,unknown8,EOS24,"
                "zero malformed/repetition,known_context_gain>=8; ALL eight pairs "
                "positive exact gain and no city/code/EOS regression"
            ),
            status="DESIGN_FROZEN_BEFORE_REHEARSAL_AND_RESEARCH_FITS",
        ),
    )
    print(json.dumps(dict(plan_sha256=sha(RUN / "plan.json"), maximum_fits=16)), flush=True)


def batch_tensors(documents: list[dict[str, Any]]) -> tuple[Any, Any, Any, Any]:
    import torch
    from torch.nn import functional as F

    x, y, answer = make_batch(documents)
    require(x.shape[1] <= 64, "document budget")
    x = F.pad(x, (0, 64 - x.shape[1]), value=0)
    y = F.pad(y, (0, 64 - y.shape[1]), value=-100)
    answer = F.pad(answer, (0, 64 - answer.shape[1]), value=False)
    first = torch.zeros_like(answer)
    for index, doc in enumerate(documents):
        first[index, len(doc["prefix"].encode())] = True
    require(first.sum() == len(documents) and not (first & ~answer).any(), "first answer alignment")
    return x, y, answer, first


def loss_from_logits(
    logits: Any, y: Any, answer: Any, first: Any, extra: int
) -> tuple[Any, dict[str, Any]]:
    from torch.nn import functional as F

    require(extra in (0, 15), "registered objective only")
    losses = F.cross_entropy(logits.transpose(1, 2), y, ignore_index=-100, reduction="none")
    valid = y.ne(-100)
    h, a, f = losses[valid & ~answer].sum(), losses[valid & answer].sum(), losses[first].sum()
    nh, na, nf = int((valid & ~answer).sum()), int((valid & answer).sum()), int(first.sum())
    require(nh > 0 and na > 0 and nf > 0, "loss partitions")
    denominator = nh + na + extra * nf
    return (h + a + extra * f) / denominator, dict(
        history_loss=float(h.detach()),
        answer_loss=float(a.detach()),
        first_loss=float(f.detach()),
        history_targets=nh,
        answer_targets=na,
        first_targets=nf,
        weighted_denominator=denominator,
    )


def objective(
    model: Any, documents: list[dict[str, Any]], extra: int
) -> tuple[Any, dict[str, Any]]:
    x, y, answer, first = batch_tensors(documents)
    value, stats = loss_from_logits(forward_batch(model, x), y, answer, first, extra)
    stats["forward_positions"] = x.numel()
    return value, stats


VALUES = ("la", "mi", "so", "tu", "R-7", "Q_2", "V:4", "Z!6", "?")


def outcome(ids: list[int], gold: str) -> dict[str, Any]:
    expected = [b + 3 for b in gold.encode()]
    eos = bool(ids and ids[-1] == 2)
    body = ids[:-1] if eos else ids
    return dict(
        exact=ids == [*expected, 2],
        value_exact=body == expected,
        eos=eos,
        wrong_first=not ids or ids[0] != expected[0],
        malformed=tuple(body) not in {tuple(b + 3 for b in v.encode()) for v in VALUES},
        repetition=any(
            ids[i : i + w] * 3 == ids[i : i + 3 * w]
            for w in (1, 2)
            for i in range(len(ids) - 3 * w + 1)
        ),
    )


def score_predictions(
    predictions: list[dict[str, Any]], labels: list[dict[str, Any]]
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    cases = []
    for p, label in zip(predictions, labels, strict=True):
        require(p["id"] == label["id"], "scoring order")
        flags = outcome(p["result"]["generated_ids"], label["gold"])
        counts.update({k: int(v) for k, v in flags.items()})
        categories[label["category"]] += int(flags["exact"])
        cases.append(dict(id=label["id"], gold=label["gold"], category=label["category"], **flags))
    return dict(count=len(labels), **counts, categories=dict(categories), cases=cases)


def mastery(m: dict[str, Any]) -> bool:
    return (
        m["exact"] == 96
        and m["eos"] == 96
        and m["wrong_first"] == 0
        and m["malformed"] == 0
        and m["repetition"] == 0
    )


def eligible(training: dict[str, Any]) -> bool:
    if set(training) != {identity(*cell) for cell in ORDER}:
        return False
    for key, m in training.items():
        if key.endswith("-first16"):
            if not mastery(m):
                return False
        elif not (
            m["exact"] >= 90 and m["eos"] == 96 and m["malformed"] == 0 and m["repetition"] == 0
        ):
            return False
    return len(training) == len(ORDER)


def development_floor(m: dict[str, Any]) -> bool:
    return (
        m["exact"] >= 22
        and m["categories"]["city"] >= 7
        and m["categories"]["code"] >= 7
        and m["categories"]["unknown"] == 8
        and m["eos"] == 24
        and m["malformed"] == 0
        and m["repetition"] == 0
        and m["known_context_gain"] >= 8
    )


def rehearsal(directory: Path) -> None:
    check_plan()
    import torch

    from toruk_lm.engine import setup

    records: dict[str, Any] = {}
    for variant in PARAMETERS:
        for arm, extra in WEIGHTS.items():
            setup(902407, 1)
            model = make_model(variant)
            optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, foreach=False, fused=False)
            before = initial_hash(model)
            dummy = [dict(prefix="X" * 62, text="X" * 63) for _ in range(8)]
            iterations = []
            for _ in range(3):
                x, y, answer, first = batch_tensors(dummy)
                x = torch.randint(3, 259, x.shape)
                y = torch.randint(3, 259, y.shape)
                x[:, 0] = 1
                y[:, -1] = 2
                optimizer.zero_grad(set_to_none=True)
                began, cpu = time.perf_counter(), time.process_time()
                loss, _ = loss_from_logits(forward_batch(model, x), y, answer, first, extra)
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
                    dict(
                        cpu=time.process_time() - cpu,
                        wall=time.perf_counter() - began,
                        loss=float(loss.detach()),
                    )
                )
            require(initial_hash(model) == before and not optimizer.state, "zero-update rehearsal")
            bound = 2 * max(max(i["cpu"], i["wall"]) for i in iterations[1:]) * 1536 + 20
            records[f"{variant}-{arm}"] = dict(iterations=iterations, projected_fit=bound)
    fit_cap = max(60, 10 * math.ceil(max(r["projected_fit"] for r in records.values()) / 10))
    result = dict(
        seed=902407,
        records=records,
        optimizer_updates=0,
        study_examples_used=False,
        selected_fit_cap=fit_cap,
        pass_rehearsal=fit_cap <= 120,
    )
    save(directory / "rehearsal.json", result)
    require(result["pass_rehearsal"], "rehearsal exceeds prospective ceiling; stop without retry")


def prepare_resources() -> None:
    check_plan()
    with controller_record(RUN / "preparation" / "budget"):
        receipts = []
        contracts = RUN / "preparation/contracts"
        command = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_value_start_replication_v2.py",
            "tests/test_lifetime_job_v2.py",
            "tests/test_lifetime_job.py",
            "--basetemp",
            str(RUN / "preparation/pytest-tmp"),
        ]
        result = watch_and_seal(command, contracts, RUN / "preparation", 60)
        receipts.append(dict(path=contracts.relative_to(RUN).as_posix(), sha256=result.seal_sha256))
        require(result.cost["status"] == "PASS", "new contracts failed")
        directory = RUN / "preparation/rehearsal"
        result = watch_and_seal(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts/value_start_replication_v2.py"),
                "worker",
                "--kind",
                "rehearsal",
                "--directory",
                str(directory),
            ],
            directory,
            RUN / "preparation",
            45,
        )
        receipts.append(dict(path=directory.relative_to(RUN).as_posix(), sha256=result.seal_sha256))
        require(result.cost["status"] == "PASS", "rehearsal failed; no retry")
        save(RUN / "preparation-summary.json", dict(status="PASS", seals=receipts))


def register() -> None:
    plan = check_plan()
    prep = read(RUN / "preparation-summary.json")
    require(prep["status"] == "PASS", "preparation failed")
    receipt = read(RUN / "preparation-budget-receipt.json")
    seals = [*prep["seals"], dict(path="preparation/budget", sha256=receipt["sha256"])]
    for seal in seals:
        verify_seal(RUN / seal["path"], expected_seal_sha256=seal["sha256"])
        require(read(RUN / seal["path"] / "cost.json")["status"] == "PASS", "prerequisite STOP")
    fitcap = read(RUN / "preparation/rehearsal/rehearsal.json")["selected_fit_cap"]
    require(fitcap <= 120, "fit ceiling")
    caps = dict(
        fit=fitcap,
        evaluate=30,
        development=30,
        request=2,
        overall=1800,
        memory=2147483648,
        disk=134217728,
    )
    names = (
        "precondition.json",
        "overlap.json",
        "starting-state.json",
        "preservation-before.json",
        "preparation-summary.json",
        "preparation-budget-receipt.json",
        "preparation/rehearsal/rehearsal.json",
    )
    save(
        RUN / "registration.json",
        dict(
            format=FORMAT,
            plan_sha256=sha(RUN / "plan.json"),
            caps=caps,
            order=plan["order"],
            prerequisite_files={name: sha(RUN / name) for name in names},
            prerequisite_seals=seals,
            status="FROZEN_BEFORE_ANY_RESEARCH_FIT_OR_ANSWER",
        ),
    )
    print(
        json.dumps(dict(registration_sha256=sha(RUN / "registration.json"), caps=caps)), flush=True
    )


def fit(directory: Path, seed: str, variant: str, arm: str) -> None:
    reg = check_registration()
    require(
        read(RUN / "attempt-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
        "registered attempt marker",
    )
    import torch

    from toruk_lm.engine import setup

    setup(CROSSED[seed]["initialization"], 1)
    model = make_model(variant)
    require(
        torch.get_num_threads() == 1
        and torch.are_deterministic_algorithms_enabled()
        and all(p.device.type == "cpu" and p.dtype == torch.float32 for p in model.parameters()),
        "deterministic single-thread float32 CPU runtime",
    )
    initial = initial_hash(model)
    require(
        initial == read(RUN / "plan.json")["initial_hashes"][f"{seed}-{variant}"], "initialization"
    )
    require(sum(p.numel() for p in model.parameters()) == PARAMETERS[variant], "parameter budget")
    docs = {d["id"]: d for d in checked_data("train-documents.json", training=True)}
    batches = checked_data("schedules.json")[str(seed)]
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=0.003,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
        foreach=False,
        fused=False,
    )
    targets = positions = completed = 0
    began, cpu = time.perf_counter(), time.process_time()
    try:
        with (directory / "training.jsonl").open("x", encoding="utf-8") as stream:
            for batch in batches:
                optimizer.zero_grad(set_to_none=True)
                loss, stats = objective(model, [docs[i] for i in batch["ids"]], WEIGHTS[arm])
                require(torch.isfinite(loss), "nonfinite objective")
                loss.backward()
                require(
                    all(
                        p.grad is not None and torch.isfinite(p.grad).all()
                        for p in model.parameters()
                    ),
                    "missing/nonfinite gradients",
                )
                norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
                optimizer.step()
                require(
                    all(torch.isfinite(p).all() for p in model.parameters()), "nonfinite parameters"
                )
                completed += 1
                targets += stats["history_targets"] + stats["answer_targets"]
                positions += stats["forward_positions"]
                append(
                    stream,
                    dict(**batch, objective=float(loss.detach()), gradient_norm=norm, **stats),
                )
        require(completed == 1536 and targets == 692224 and positions == 786432, "matched work")
        checkpoint = dict(
            format=FORMAT,
            registration=sha(RUN / "registration.json"),
            seed=seed,
            initialization_seed=CROSSED[seed]["initialization"],
            shuffle_seed=CROSSED[seed]["shuffle"],
            variant=variant,
            arm=arm,
            config=CONFIG,
            steps=completed,
            model=model.state_dict(),
            optimizer=optimizer.state_dict(),
            torch_rng=torch.get_rng_state(),
            python_rng=random.getstate(),
            initial_sha256=initial,
        )
        path = directory / "checkpoint.pt"
        with path.open("xb") as stream:
            torch.save(checkpoint, stream)
        save(directory / "checkpoint-meta.json", dict(bytes=path.stat().st_size, sha256=sha(path)))
        save(
            directory / "training-summary.json",
            dict(
                steps=completed,
                targets=targets,
                forward_positions=positions,
                initial_sha256=initial,
                final_model_sha256=initial_hash(model),
                loop_cpu=time.process_time() - cpu,
                loop_wall=time.perf_counter() - began,
                fit_cap=reg["caps"]["fit"],
            ),
        )
    except BaseException as error:
        save(directory / "fit-failure.json", dict(error=repr(error), completed_steps=completed))
        with (directory / "checkpoint-partial.pt").open("xb") as stream:
            torch.save(
                dict(
                    format=FORMAT,
                    partial=True,
                    completed_steps=completed,
                    model=model.state_dict(),
                    optimizer=optimizer.state_dict(),
                ),
                stream,
            )
        raise


def load(seed: str, variant: str, arm: str) -> Any:
    check_registration()
    import torch

    from toruk_lm.engine import setup

    setup(CROSSED[seed]["initialization"], 1)
    directory = EXEC / "stages" / ("fit-" + identity(seed, variant, arm))
    path = directory / "checkpoint.pt"
    meta = read(directory / "checkpoint-meta.json")
    require(sha(path) == meta["sha256"] and path.stat().st_size == meta["bytes"], "checkpoint hash")
    saved = torch.load(path, weights_only=True, map_location="cpu")
    require(
        saved["format"] == FORMAT
        and saved["registration"] == sha(RUN / "registration.json")
        and (saved["seed"], saved["variant"], saved["arm"]) == (seed, variant, arm)
        and saved["steps"] == 1536
        and saved["config"] == CONFIG,
        "checkpoint identity",
    )
    require(all(float(s["step"]) == 1536 for s in saved["optimizer"]["state"].values()), "progress")
    require(all(torch.isfinite(v).all() for v in saved["model"].values()), "finite checkpoint")
    model = make_model(variant)
    model.load_state_dict(saved["model"], strict=True)
    model.eval()
    return model


def request_cost(began: float, cpu: float) -> dict[str, float]:
    return dict(cpu=time.process_time() - cpu, wall=time.perf_counter() - began)


def generate(directory: Path, model: Any, split: str, mode: str = "main") -> list[dict[str, Any]]:
    from toruk_lm.owned_lm import OwnedSession

    inputs = checked_data(f"{split}-inputs.json")
    first = None
    with (directory / f"predictions-{mode}.jsonl").open("x", encoding="utf-8") as stream:
        for index, case in enumerate([*inputs, inputs[0]]):
            prefix = (
                local.question_only(case["prefix"]) if mode == "question-only" else case["prefix"]
            )
            began, cpu = time.perf_counter(), time.process_time()
            result = OwnedSession(model).generate(prefix, budget=8)
            cost = request_cost(began, cpu)
            append(
                stream,
                dict(
                    id=case["id"],
                    prefix=prefix,
                    input_ids=[1, *(b + 3 for b in prefix.encode())],
                    result=result,
                    cost=cost,
                    replay=index == len(inputs),
                ),
            )
            require(max(cost.values()) <= 2, "generation request cap")
            if index == 0:
                first = result
            require(index != len(inputs) or result == first, "generation replay")
    # This marker covers only a closed prediction stream, never parent monitor logs.
    save(
        directory / f"generation-complete-{mode}.json",
        dict(
            predictions_sha256=sha(directory / f"predictions-{mode}.jsonl"),
            requests=len(inputs) + 1,
            labels_opened_by_generator=False,
        ),
    )
    return list(rows(directory / f"predictions-{mode}.jsonl")[:-1])


def evaluate(directory: Path, seed: str, variant: str, arm: str, split: str) -> None:
    if split == "dev":
        require(read(EXEC / "training-gate.json")["pass_gate"], "development gate closed")
    model = load(seed, variant, arm)
    before = initial_hash(model)
    predictions = generate(directory, model, split)
    labels = checked_data(f"{split}-labels.json")
    metrics = score_predictions(predictions, labels)
    import torch
    from first_byte_probe import measurement, vector_record

    from toruk_lm.owned_lm import OwnedSession

    with (
        torch.no_grad(),
        (directory / "first-vectors.jsonl").open("x", encoding="utf-8") as vectors,
        (directory / "first-measurements.jsonl").open("x", encoding="utf-8") as measurements,
    ):
        inputs = checked_data(f"{split}-inputs.json")
        first = None
        for index, (case, label) in enumerate(
            zip([*inputs, inputs[0]], [*labels, labels[0]], strict=True)
        ):
            began, cpu = time.perf_counter(), time.process_time()
            ids = [1, *(b + 3 for b in case["prefix"].encode())]
            tensor = OwnedSession(model).consume(ids)
            raw = vector_record(
                vectors, dict(id=case["id"], input_ids=ids, replay=index == len(inputs)), tensor
            )
            m = measurement(raw["logits"], label["gold"].encode()[0] + 3)
            pred = predictions[0] if index == len(inputs) else predictions[index]
            require(
                m["predicted_first_id"] == pred["result"]["generated_ids"][0], "first argmax parity"
            )
            cost = request_cost(began, cpu)
            append(measurements, dict(id=case["id"], cost=cost, replay=index == len(inputs), **m))
            require(max(cost.values()) <= 2, "vector request cap")
            if index == 0:
                first = raw["logits"]
            require(index != len(inputs) or raw["logits"] == first, "vector replay")
    totals: Counter[str] = Counter()
    with (
        torch.no_grad(),
        (directory / "teacher-losses.jsonl").open("x", encoding="utf-8") as stream,
    ):
        for p, label in zip(predictions, labels, strict=True):
            began, cpu = time.perf_counter(), time.process_time()
            _, stats = objective(
                model, [dict(prefix=p["prefix"], text=p["prefix"] + label["gold"])], 0
            )
            cost = request_cost(began, cpu)
            append(stream, dict(id=p["id"], cost=cost, **stats))
            require(max(cost.values()) <= 2, "teacher loss cap")
            totals.update(stats)
    metrics["full_nll"] = (totals["history_loss"] + totals["answer_loss"]) / (
        totals["history_targets"] + totals["answer_targets"]
    )
    metrics["answer_nll"] = totals["answer_loss"] / totals["answer_targets"]
    metrics["first_nll"] = totals["first_loss"] / totals["first_targets"]
    if split == "dev":
        question = score_predictions(generate(directory, model, split, "question-only"), labels)
        save(directory / "question-only-metrics.json", question)
        metrics["known_context_gain"] = sum(
            metrics["categories"][k] - question["categories"][k] for k in ("city", "code")
        )
        metrics["development_floor"] = development_floor(metrics)
    require(initial_hash(model) == before, "evaluation mutated weights")
    save(directory / "metrics.json", metrics)


def compare_development(dev: dict[str, Any]) -> dict[str, Any]:
    if not dev:
        return dict(evaluated=False, improved=False, memory_study_justified=False)
    gains = {}
    no_regression = True
    for seed in CROSSED:
        for variant in PARAMETERS:
            candidate, control = (
                dev[identity(seed, variant, arm)] for arm in ("first16", "uniform")
            )
            gains[f"{seed}-{variant}"] = candidate["exact"] - control["exact"]
            no_regression &= candidate["eos"] >= control["eos"] and all(
                candidate["categories"][k] >= control["categories"][k]
                for k in ("city", "code", "unknown")
            )
    floors = all(
        development_floor(dev[identity(s, v, "first16")]) for s in CROSSED for v in PARAMETERS
    )
    improved = floors and no_regression and all(gain > 0 for gain in gains.values())
    return dict(
        evaluated=True,
        candidate_floors=floors,
        no_regression=no_regression,
        pair_exact_gains=gains,
        improved=improved,
        memory_study_justified=False,
        scope="Objective replication only; no architecture/memory attribution.",
    )


def stage(kind: str, seed: str, variant: str, arm: str, ledger: Any) -> Path:
    reg = check_registration()
    name = f"{kind}-{identity(seed, variant, arm)}"
    directory = EXEC / "stages" / name
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts/value_start_replication_v2.py"),
        "worker",
        "--kind",
        kind,
        "--directory",
        str(directory),
        "--seed",
        str(seed),
        "--variant",
        variant,
        "--arm",
        arm,
    ]
    result = watch_and_seal(command, directory, EXEC.parent, reg["caps"][kind])
    append(
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
    verify_seal(directory, expected_seal_sha256=result.seal_sha256)
    require(result.cost["status"] == "PASS", "stage failed: " + name)
    print(
        json.dumps(dict(stage=name, cpu=result.cost["cpu"], wall=result.cost["wall"])), flush=True
    )
    return directory


def controller() -> None:
    reg = check_registration()
    training: dict[str, Any] = {}
    development: dict[str, Any] = {}
    with controller_record(EXEC), (EXEC / "stages.jsonl").open("x", encoding="utf-8") as ledger:
        try:
            for seed, variant, arm in ORDER:
                stage("fit", seed, variant, arm, ledger)
                directory = stage("evaluate", seed, variant, arm, ledger)
                training[identity(seed, variant, arm)] = read(directory / "metrics.json")
            gate = eligible(training)
            save(
                EXEC / "training-gate.json",
                dict(
                    pass_gate=gate,
                    candidate_mastery={
                        k: mastery(m) for k, m in training.items() if k.endswith("-first16")
                    },
                    control_mastery={
                        k: mastery(m) for k, m in training.items() if k.endswith("-uniform")
                    },
                    controls_eligible=all(
                        m["exact"] >= 90
                        and m["eos"] == 96
                        and m["malformed"] == 0
                        and m["repetition"] == 0
                        for k, m in training.items()
                        if k.endswith("-uniform")
                    ),
                ),
            )
            if gate:
                for seed, variant, arm in ORDER:
                    directory = stage("development", seed, variant, arm, ledger)
                    development[identity(seed, variant, arm)] = read(directory / "metrics.json")
            comparison = compare_development(development)
            target_gain = sum(
                training[identity(s, v, "first16")]["exact"]
                - training[identity(s, v, "uniform")]["exact"]
                for s in CROSSED
                for v in PARAMETERS
            )
            no_training_regression = all(
                training[identity(s, v, "first16")]["exact"]
                >= training[identity(s, v, "uniform")]["exact"]
                for s in CROSSED
                for v in PARAMETERS
            )
            training_improvement = (
                all(mastery(m) for k, m in training.items() if k.endswith("-first16"))
                and target_gain > 0
                and no_training_regression
            )
            save(
                EXEC / "summary.json",
                dict(
                    registration_sha256=sha(RUN / "registration.json"),
                    training=training,
                    development=development,
                    training_gate=gate,
                    training_improvement=training_improvement,
                    target_training_gain=target_gain,
                    development_evaluated=bool(development),
                    comparison=comparison,
                    decision="STOP_TRAINING_FAILURE"
                    if not gate
                    else "REPLICATION_GATES_PASS"
                    if comparison["improved"]
                    else "STOP_DEVELOPMENT_FAILURE",
                    caps=reg["caps"],
                    answer_provider="fresh Toruk CausalLM or OwnedMemoryLM weights only",
                ),
            )
            print(
                json.dumps(
                    dict(
                        training_gate=gate,
                        training_improvement=training_improvement,
                        development_evaluated=bool(development),
                        comparison=comparison,
                    )
                ),
                flush=True,
            )
        except BaseException as error:
            save(
                EXEC / "failure.json",
                dict(error=repr(error), training=training, development=development),
            )
            raise


def run_study() -> None:
    reg = check_registration()
    result = watch_and_seal(
        [sys.executable, "-B", str(ROOT / "scripts/value_start_replication_v2.py"), "controller"],
        EXEC,
        EXEC.parent,
        reg["caps"]["overall"],
    )
    save(
        RUN / "execution-receipt.json",
        dict(
            path="registered/execution",
            sha256=result.seal_sha256,
            workload_status=result.cost["status"],
        ),
    )
    require(result.cost["status"] == "PASS", "registered workload STOP")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "prepare",
            "resources",
            "preparation-controller",
            "register",
            "launch",
            "run-study",
            "controller",
            "worker",
        ),
    )
    parser.add_argument("--kind", choices=("rehearsal", "fit", "evaluate", "development"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--seed", choices=tuple(CROSSED), default=next(iter(CROSSED)))
    parser.add_argument("--variant", choices=PARAMETERS, default="ordinary")
    parser.add_argument("--arm", choices=WEIGHTS, default="uniform")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "resources":
        check_plan()
        result = watch_and_seal(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts/value_start_replication_v2.py"),
                "preparation-controller",
            ],
            RUN / "preparation" / "budget",
            RUN / "preparation",
            150,
        )
        save(
            RUN / "preparation-budget-receipt.json",
            dict(sha256=result.seal_sha256, status=result.cost["status"]),
        )
        require(result.cost["status"] == "PASS", "preparation STOP; no study fits")
    elif args.command == "preparation-controller":
        prepare_resources()
    elif args.command == "register":
        register()
    elif args.command == "launch":
        reg = check_registration()
        save(
            RUN / "attempt-start.json",
            dict(
                registration_sha256=sha(RUN / "registration.json"),
                max_fits=16,
                max_updates=24576,
                no_retries=True,
            ),
        )
        result = watch_and_seal(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts/value_start_replication_v2.py"),
                "run-study",
            ],
            RUN / "registered" / "budget",
            EXEC.parent,
            reg["caps"]["overall"],
        )
        save(
            RUN / "registered-budget-receipt.json",
            dict(path="registered/budget", sha256=result.seal_sha256, status=result.cost["status"]),
        )
        print(
            json.dumps(
                dict(
                    status=result.cost["status"],
                    cpu=result.cost["cpu"],
                    wall=result.cost["wall"],
                    seal_sha256=result.seal_sha256,
                )
            ),
            flush=True,
        )
        require(result.cost["status"] == "PASS", "registered budget STOP")
    elif args.command == "run-study":
        run_study()
    elif args.command == "controller":
        controller()
    else:
        require(
            args.directory and args.directory.resolve().is_relative_to(RUN), "new study directory"
        )
        with controller_record(args.directory):
            if args.kind == "rehearsal":
                rehearsal(args.directory)
            elif args.kind == "fit":
                fit(args.directory, args.seed, args.variant, args.arm)
            else:
                check_registration()
                evaluate(
                    args.directory,
                    args.seed,
                    args.variant,
                    args.arm,
                    "dev" if args.kind == "development" else "train",
                )


if __name__ == "__main__":
    main()
