"""Single-use paired city-batch development study with complete Windows Job accounting."""

import argparse
import json
import math
import random
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import local_answer_dev as original
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
from lifetime_job import controller_record, watch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RUN = ROOT / "artifacts/local-answer-paired-batch-dev-v1"
OLD = ROOT / "artifacts/local-answer-dev-v1"
PROTOCOL = "docs/research/local-answer-paired-batch-dev-v1-protocol.md"
FORMAT = "toruk-local-answer-paired-batch-dev-v1"
ARMS = ("original", "city-shuffled", "city-paired")
SEEDS = (601, 947)
STEPS = 1536
CAPS = dict(
    contracts=30,
    rehearsal=30,
    fit=60,
    analyze=20,
    development=20,
    request=2,
    overall=1500,
    memory=2147483648,
    disk=134217728,
)
ORDER = [
    (601, "ordinary", "original"),
    (601, "ordinary", "city-shuffled"),
    (601, "ordinary", "city-paired"),
    (601, "recurrent", "city-paired"),
    (601, "recurrent", "city-shuffled"),
    (601, "recurrent", "original"),
    (947, "recurrent", "original"),
    (947, "recurrent", "city-shuffled"),
    (947, "recurrent", "city-paired"),
    (947, "ordinary", "city-paired"),
    (947, "ordinary", "city-shuffled"),
    (947, "ordinary", "original"),
]
SOURCES = [
    PROTOCOL,
    "scripts/paired_batch_dev.py",
    "tests/test_paired_batch_dev.py",
    "scripts/local_answer_dev.py",
    "scripts/answer_trainability_dev.py",
    "scripts/first_byte_probe.py",
    "scripts/lifetime_job.py",
    "scripts/segment_delta_watch.py",
    "tests/test_lifetime_job.py",
    "tests/test_local_answer_dev.py",
    "src/toruk_lm/model.py",
    "src/toruk_lm/recurrent.py",
    "src/toruk_lm/owned_lm.py",
    "src/toruk_lm/tokenizer.py",
    "src/toruk_lm/engine.py",
    "src/toruk_lm/data.py",
    ".gitattributes",
    "pyproject.toml",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def append(stream, value):
    stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
    stream.flush()


def cell(seed, variant, arm):
    return f"{seed}-{variant}-{arm}"


def schedule(documents, labels, seed, arm):
    require(seed in SEEDS and arm in ARMS, "registered seed/arm")
    ids = [d["id"] for d in documents]
    lookup = {r["id"]: r for r in labels}
    city = sorted(i for i in ids if lookup[i]["category"] == "city")
    noncity = sorted(set(ids) - set(city))
    groups = defaultdict(list)
    for identity in city:
        groups[lookup[identity]["canonical"][0]].append(identity)
    require(len(ids) == 96 and len(city) == 32 and len(noncity) == 64, "schedule population")
    require(len(groups) == 4 and all(len(g) == 8 for g in groups.values()), "entity groups")
    result = []
    for epoch in range(128):
        if arm == "original":
            ordered = list(ids)
            random.Random(seed + epoch).shuffle(ordered)
            batches = [ordered[i : i + 8] for i in range(0, 96, 8)]
        else:
            nc = list(noncity)
            random.Random(seed + 200000 + epoch).shuffle(nc)
            other = iter([nc[i : i + 8] for i in range(0, 64, 8)])
            if arm == "city-shuffled":
                ordered = list(city)
                random.Random(seed + 100000 + epoch).shuffle(ordered)
                cities = [ordered[i : i + 8] for i in range(0, 32, 8)]
            else:
                entities = sorted(groups)
                random.Random(seed + 100000 + epoch).shuffle(entities)
                cities = [sorted(groups[e]) for e in entities]
            ci = iter(cities)
            batches = []
            for offset in range(12):
                if offset in (0, 3, 6, 9):
                    batch = list(next(ci))
                    random.Random(seed + 300000 + 12 * epoch + offset).shuffle(batch)
                else:
                    batch = next(other)
                batches.append(batch)
        for offset, batch in enumerate(batches):
            result.append(
                dict(
                    step=12 * epoch + offset + 1,
                    epoch=epoch,
                    offset=offset,
                    ids=batch,
                    padded_forward_positions=512,
                )
            )
    require(len(result) == STEPS, "schedule length")
    return result


def validate_schedules(documents, labels, schedules):
    lookup = {d["id"]: d for d in documents}
    labelmap = {d["id"]: d for d in labels}
    for seed in SEEDS:
        for arm in ARMS:
            plan = schedules[f"{seed}-{arm}"]
            require(len(plan) == STEPS, "schedule steps")
            exposure = Counter(i for b in plan for i in b["ids"])
            require(exposure == Counter({i: 128 for i in lookup}), "matched per-document exposure")
            require(
                all(len(b["ids"]) == len(set(b["ids"])) == 8 for b in plan), "batch unique size"
            )
            require(
                all(
                    b["step"] == n + 1 and b["padded_forward_positions"] == 512
                    for n, b in enumerate(plan)
                ),
                "step/work identity",
            )
            targets = sum(len(lookup[i]["text"].encode()) + 1 for b in plan for i in b["ids"])
            require(targets == 692224, "matched target total")
            if arm == "city-paired":
                for b in plan:
                    if b["offset"] in (0, 3, 6, 9):
                        chosen = [labelmap[i] for i in b["ids"]]
                        require(
                            len({r["canonical"][0] for r in chosen}) == 1, "same entity pairing"
                        )
                        for template in ("A", "B"):
                            values = Counter(r["gold"] for r in chosen if r["template"] == template)
                            require(
                                len(values) == 2 and set(values.values()) == {2},
                                "both values/templates/nonces paired",
                            )
        for a, b in zip(
            schedules[f"{seed}-city-paired"], schedules[f"{seed}-city-shuffled"], strict=True
        ):
            if a["offset"] not in (0, 3, 6, 9):
                require(a["ids"] == b["ids"], "matched noncity schedule")
            require(
                sum(len(lookup[i]["text"].encode()) + 1 for i in a["ids"])
                == sum(len(lookup[i]["text"].encode()) + 1 for i in b["ids"]),
                "city control per-step target counts",
            )


def prepare():
    require(
        Path(
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT)
            .decode()
            .strip()
        ).resolve()
        == ROOT,
        "Git root",
    )
    RUN.mkdir(exist_ok=False)
    reg = read(OLD / "registration.json")
    require(
        sha(OLD / "registration.json")
        == "c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4",
        "old registration",
    )
    documents = {}
    for name, digest in reg["data"].items():
        require(sha(OLD / name) == digest, "frozen local data identity")
        (RUN / name).write_bytes((OLD / name).read_bytes())
        documents[name] = read(RUN / name)
    original.validate(documents)
    schedules = {
        f"{s}-{a}": schedule(
            documents["train-documents.json"], documents["train-labels.json"], s, a
        )
        for s in SEEDS
        for a in ARMS
    }
    validate_schedules(documents["train-documents.json"], documents["train-labels.json"], schedules)
    save(RUN / "batch-schedules.json", schedules)
    initial = {}
    protected = set()
    for seed in SEEDS:
        for variant in PARAMETERS:
            base = OLD / "stages" / f"train-{seed}-{variant}"
            initial[f"{seed}-{variant}"] = read(base / "training-summary.json")["initial_sha256"]
            protected.update(
                (base / n)
                for n in ("checkpoint.pt", "checkpoint-meta.json", "training-summary.json")
            )
    for relative in (
        "artifacts/local-answer-first-byte-v1/inventory.json",
        "artifacts/local-answer-first-byte-probe-v1/inventory.json",
        "artifacts/local-answer-first-token-review-v1/inventory.json",
    ):
        path = ROOT / relative
        protected.add(path)
        protected.update(ROOT / n for n in read(path)["files"])
    handoff = ROOT / "artifacts/checkpoint-handoff-v1-20261123"
    protected.update(p for p in handoff.rglob("*") if p.is_file())
    protected.update(
        OLD / n
        for n in (
            *reg["data"],
            "registration.json",
            "artifact-inventory.json",
            "summary.json",
            "training-gate.json",
        )
    )
    preserve = {
        p.relative_to(ROOT).as_posix(): dict(bytes=p.stat().st_size, sha256=sha(p))
        for p in sorted(protected)
    }
    save(
        RUN / "preservation-before.json",
        dict(files=preserve, scope="handoff and consumed frozen evidence"),
    )
    sources = {}
    for name in SOURCES:
        target = RUN / "sources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
        sources[name] = sha(target)
    save(
        RUN / "plan.json",
        dict(
            format=FORMAT,
            protocol=PROTOCOL,
            sources=sources,
            data={n: sha(RUN / n) for n in (*reg["data"], "batch-schedules.json")},
            runtime=runtime(),
            source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            initial_hashes=initial,
            order=ORDER,
            caps=CAPS,
            config=CONFIG,
            parameters=PARAMETERS,
            seeds=SEEDS,
            arms=ARMS,
            steps=STEPS,
            batch=8,
            pad_targets_to=64,
            tokenizer=reg["tokenizer"],
            optimizer=dict(
                lr=0.003,
                betas=[0.9, 0.999],
                eps=1e-8,
                weight_decay=0.01,
                clip=1.0,
                foreach=False,
                fused=False,
            ),
            decoding=dict(greedy=True, budget=8, suppress=[0, 1], stop=2),
            gates=dict(
                training_exact=96,
                training_eos=96,
                training_malformed=0,
                training_repetitive=0,
                city_first_errors=0,
                min_city_winner_margin=1e-4,
                global_training_gate="all twelve cells before ANY development generation",
                dev_exact=22,
                dev_city=7,
                dev_code=7,
                dev_unknown=8,
                dev_eos=24,
                dev_malformed=0,
                dev_known_context_gain=8,
            ),
            old_registration_sha256=sha(OLD / "registration.json"),
            preservation_sha256=sha(RUN / "preservation-before.json"),
            status="PLAN_FROZEN_BEFORE_REHEARSAL_AND_FITTING",
        ),
    )
    print(json.dumps(dict(plan_sha256=sha(RUN / "plan.json"), cells=len(ORDER))), flush=True)


def verify_plan():
    plan = read(RUN / "plan.json")
    require(plan["runtime"] == runtime(), "runtime changed")
    for name, expected in plan["sources"].items():
        require(
            sha(ROOT / name) == sha(RUN / "sources" / name) == expected,
            "frozen source changed: " + name,
        )
    for name, expected in plan["data"].items():
        require(sha(RUN / name) == expected, "frozen data changed: " + name)
    require(
        sha(RUN / "preservation-before.json") == plan["preservation_sha256"], "preservation seal"
    )
    return plan


def verify_registration():
    plan = verify_plan()
    reg = read(RUN / "registration.json")
    require(reg["plan_sha256"] == sha(RUN / "plan.json"), "registration/plan binding")
    for name, expected in reg["prerequisites"].items():
        require(sha(RUN / name) == expected, "prerequisite changed")
    require(
        read(RUN / "run-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
        "single run registration seal",
    )
    return plan


def batch_objective(model, documents):
    from torch.nn import functional as F

    x, y, answer = make_batch(documents)
    require(x.shape[1] <= 64, "document budget")
    x = F.pad(x, (0, 64 - x.shape[1]), value=0)
    y = F.pad(y, (0, 64 - y.shape[1]), value=-100)
    answer = F.pad(answer, (0, 64 - answer.shape[1]), value=False)
    logits = forward_batch(model, x)
    losses = F.cross_entropy(logits.transpose(1, 2), y, ignore_index=-100, reduction="none")
    valid = y.ne(-100)
    h, a = losses[valid & ~answer].sum(), losses[valid & answer].sum()
    nh, na = int((valid & ~answer).sum()), int((valid & answer).sum())
    require(nh > 0 and na > 0, "nonempty uniform objective partitions")
    return (h + a) / (nh + na), dict(
        history_loss=float(h.detach()),
        answer_loss=float(a.detach()),
        history_targets=nh,
        answer_targets=na,
        forward_positions=x.numel(),
    )


def rehearsal(directory):
    import torch

    from toruk_lm.engine import setup

    records = {}
    for variant in PARAMETERS:
        setup(900301, 1)
        model = make_model(variant)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, foreach=False, fused=False)
        before = initial_hash(model)
        numeric = [dict(prefix="X" * 62, text="X" * 63) for _ in range(8)]
        times = []
        for _ in range(3):
            x, y, _mask = make_batch(numeric)
            x, y = torch.randint(3, 259, x.shape), torch.randint(3, 259, y.shape)
            x[:, 0], y[:, -1] = 1, 2
            optimizer.zero_grad(set_to_none=True)
            began, cpu = time.perf_counter(), time.process_time()
            logits = forward_batch(model, x)
            loss = torch.nn.functional.cross_entropy(logits.transpose(1, 2), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            require(
                torch.isfinite(loss)
                and all(
                    p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()
                ),
                "rehearsal finite",
            )
            times.append(
                dict(
                    cpu=time.process_time() - cpu,
                    wall=time.perf_counter() - began,
                    loss=float(loss.detach()),
                )
            )
        bound = 2 * max(max(t["cpu"], t["wall"]) for t in times[1:]) * STEPS + 10
        require(initial_hash(model) == before and not optimizer.state, "zero optimizer updates")
        records[variant] = dict(
            iterations=times, projected_fit_seconds=bound, within_fit_cap=bound <= CAPS["fit"]
        )
    projected = 6 * sum(r["projected_fit_seconds"] for r in records.values()) + 24 * 20 + 80
    summary = dict(
        seed=900301,
        optimizer_steps=0,
        study_documents_used=False,
        records=records,
        projected_total_seconds=projected,
        pass_projection=all(r["within_fit_cap"] for r in records.values())
        and projected <= CAPS["overall"],
    )
    save(directory / "rehearsal.json", summary)
    require(summary["pass_projection"], "fixed rehearsal projection failed; no retry")


def freeze_registration():
    plan = verify_plan()
    prerequisites = {}
    for name in ("preparation/contracts/cost.json", "preparation/rehearsal/cost.json"):
        cost = read(RUN / name)
        require(
            cost["status"] == "PASS"
            and cost["complete_process_lifetimes"]
            and cost["active_processes"] == 0,
            "preparation cost STOP",
        )
        prerequisites[name] = sha(RUN / name)
    require(read(RUN / "preparation/rehearsal/rehearsal.json")["pass_projection"], "rehearsal STOP")
    for name in (
        "preparation/rehearsal/rehearsal.json",
        "preparation/contracts/contracts-result.json",
        "preparation/rehearsal/controller-final.json",
    ):
        prerequisites[name] = sha(RUN / name)
    save(
        RUN / "registration.json",
        dict(
            format=FORMAT,
            plan_sha256=sha(RUN / "plan.json"),
            prerequisites=prerequisites,
            caps=plan["caps"],
            order=plan["order"],
            status="FROZEN_BEFORE_ANY_STUDY_UPDATE_OR_ANSWER",
        ),
    )
    save(
        RUN / "run-start.json",
        dict(
            registration_sha256=sha(RUN / "registration.json"),
            maximum_fits=12,
            maximum_optimizer_updates=18432,
        ),
    )
    print(json.dumps(dict(registration_sha256=sha(RUN / "registration.json"))), flush=True)


def fit(directory, seed, variant, arm):
    verify_registration()
    import torch

    from toruk_lm.engine import setup

    setup(seed, 1)
    model = make_model(variant)
    initial = initial_hash(model)
    plan = read(RUN / "plan.json")
    require(initial == plan["initial_hashes"][f"{seed}-{variant}"], "registered initialization")
    require(sum(p.numel() for p in model.parameters()) == PARAMETERS[variant], "parameter count")
    documents = {d["id"]: d for d in read(RUN / "train-documents.json")}
    require(
        len(documents) == 96 and all(d["split"] == "train" for d in documents.values()),
        "train-only fitting",
    )
    batches = read(RUN / "batch-schedules.json")[f"{seed}-{arm}"]
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=0.003,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
        foreach=False,
        fused=False,
    )
    targets = positions = 0
    began, cpu = time.perf_counter(), time.process_time()
    with (directory / "training.jsonl").open("x", encoding="utf-8") as stream:
        for batch in batches:
            optimizer.zero_grad(set_to_none=True)
            objective, stats = batch_objective(model, [documents[i] for i in batch["ids"]])
            require(torch.isfinite(objective), "nonfinite training loss")
            objective.backward()
            require(
                all(
                    p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()
                ),
                "nonfinite/missing gradients",
            )
            norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            optimizer.step()
            require(all(torch.isfinite(p).all() for p in model.parameters()), "nonfinite weights")
            targets += stats["history_targets"] + stats["answer_targets"]
            positions += stats["forward_positions"]
            append(
                stream,
                dict(**batch, objective=float(objective.detach()), gradient_norm=norm, **stats),
            )
    require(targets == 692224 and positions == 786432, "matched target/dense work")
    payload = dict(
        format=FORMAT,
        registration=sha(RUN / "registration.json"),
        config=CONFIG,
        seed=seed,
        variant=variant,
        arm=arm,
        steps=STEPS,
        model=model.state_dict(),
        optimizer=optimizer.state_dict(),
        torch_rng=torch.get_rng_state(),
        python_rng=random.getstate(),
        targets=targets,
        forward_positions=positions,
        initial_sha256=initial,
    )
    path = directory / "checkpoint.pt"
    require(not path.exists(), "checkpoint overwrite refused")
    torch.save(payload, path)
    save(directory / "checkpoint-meta.json", dict(sha256=sha(path), bytes=path.stat().st_size))
    save(
        directory / "training-summary.json",
        dict(
            targets=targets,
            forward_positions=positions,
            steps=STEPS,
            presentations=12288,
            initial_sha256=initial,
            final_model_sha256=initial_hash(model),
            loop_cpu=time.process_time() - cpu,
            loop_wall=time.perf_counter() - began,
        ),
    )


def load(seed, variant, arm):
    verify_registration()
    import torch

    from toruk_lm.engine import setup

    setup(seed, 1)
    base = RUN / "stages" / f"fit-{cell(seed, variant, arm)}"
    path = base / "checkpoint.pt"
    meta = read(base / "checkpoint-meta.json")
    require(sha(path) == meta["sha256"] and path.stat().st_size == meta["bytes"], "checkpoint hash")
    saved = torch.load(path, weights_only=True, map_location="cpu")
    require(
        saved["format"] == FORMAT
        and saved["registration"] == sha(RUN / "registration.json")
        and saved["config"] == CONFIG
        and (saved["seed"], saved["variant"], saved["arm"]) == (seed, variant, arm)
        and saved["steps"] == STEPS,
        "checkpoint identity",
    )
    require(
        all(float(s["step"]) == STEPS for s in saved["optimizer"]["state"].values()),
        "optimizer progress",
    )
    require(all(torch.isfinite(v).all() for v in saved["model"].values()), "finite checkpoint")
    model = make_model(variant)
    model.load_state_dict(saved["model"], strict=True)
    model.eval()
    return model


def request_cost(began, cpu):
    cost = dict(cpu=time.process_time() - cpu, wall=time.perf_counter() - began)
    return cost


def generate(directory, model, split, mode="main"):
    from toruk_lm.owned_lm import OwnedSession

    inputs = read(RUN / f"{split}-inputs.json")
    first = None
    name = f"predictions-{mode}.jsonl"
    with (directory / name).open("x", encoding="utf-8") as stream:
        for index, case in enumerate([*inputs, inputs[0]]):
            prefix = (
                original.question_only(case["prefix"])
                if mode == "question-only"
                else case["prefix"]
            )
            began, cpu = time.perf_counter(), time.process_time()
            result = OwnedSession(model).generate(prefix, budget=8)
            cost = request_cost(began, cpu)
            append(
                stream,
                dict(
                    id=case["id"],
                    prefix=prefix,
                    result=result,
                    cost=cost,
                    input_ids=[1, *(b + 3 for b in prefix.encode())],
                    replay=index == len(inputs),
                ),
            )
            require(max(cost.values()) <= CAPS["request"], "request CPU/wall cap")
            if index == 0:
                first = result
            require(index != len(inputs) or result == first, "generation replay")
    save(
        directory / f"seal-{mode}.json",
        dict(file=name, sha256=sha(directory / name), requests=len(inputs) + 1),
    )
    return rows(directory / name)[:-1]


def observations(directory, seed, variant, arm, split):
    import torch
    from first_byte_probe import measurement, vector_record

    from toruk_lm.owned_lm import OwnedSession

    model = load(seed, variant, arm)
    before = initial_hash(model)
    prediction = generate(directory, model, split)
    labels = read(RUN / f"{split}-labels.json")
    metrics = original.metrics(prediction, labels)
    metrics["first_token_errors_all"] = sum(
        p["result"]["generated_ids"][0] != label["gold"].encode()[0] + 3
        for p, label in zip(prediction, labels, strict=True)
    )
    metrics["first_token_errors_by_category"] = {
        category: sum(
            p["result"]["generated_ids"][0] != label["gold"].encode()[0] + 3
            for p, label in zip(prediction, labels, strict=True)
            if label["category"] == category
        )
        for category in ("city", "code", "unknown")
    }
    totals = Counter()
    with (
        torch.no_grad(),
        (directory / "teacher-losses.jsonl").open("x", encoding="utf-8") as stream,
    ):
        for p, label in zip(prediction, labels, strict=True):
            began, cpu = time.perf_counter(), time.process_time()
            _, stats = batch_objective(
                model, [dict(prefix=p["prefix"], text=p["prefix"] + label["gold"])]
            )
            cost = request_cost(began, cpu)
            totals.update(
                {
                    k: stats[k]
                    for k in ("history_loss", "answer_loss", "history_targets", "answer_targets")
                }
            )
            append(stream, dict(id=p["id"], cost=cost, **stats))
            require(max(cost.values()) <= CAPS["request"], "loss request CPU/wall cap")
    metrics["full_nll"] = (totals["history_loss"] + totals["answer_loss"]) / (
        totals["history_targets"] + totals["answer_targets"]
    )
    metrics["answer_nll"] = totals["answer_loss"] / totals["answer_targets"]
    city_rows = []
    with (
        torch.no_grad(),
        (directory / "city-first-token.jsonl").open("x", encoding="utf-8") as stream,
        (directory / "city-raw-vectors.jsonl").open("x", encoding="utf-8") as vectors,
    ):
        for p, label in zip(prediction, labels, strict=True):
            if label["category"] != "city":
                continue
            began, cpu = time.perf_counter(), time.process_time()
            ids = [1, *(b + 3 for b in p["prefix"].encode())]
            tensor = OwnedSession(model).consume(ids)
            saved_vector = vector_record(vectors, dict(id=p["id"], input_ids=ids), tensor)
            logits = saved_vector["logits"]
            m = measurement(logits, label["gold"].encode()[0] + 3)
            require(m["predicted_first_id"] == p["result"]["generated_ids"][0], "first-byte parity")
            row = dict(
                id=p["id"],
                canonical=label["canonical"],
                template=label["template"],
                input_ids=ids,
                logits=logits,
                cost=request_cost(began, cpu),
                **m,
            )
            append(stream, row)
            city_rows.append(row)
            require(max(row["cost"].values()) <= CAPS["request"], "vector request CPU/wall cap")
    metrics["city_first_errors"] = sum(r["expected_rank"] != 1 for r in city_rows)
    metrics["city_near_ties"] = sum(r["winner_minus_runner_up"] <= 1e-4 for r in city_rows)
    metrics["city_min_winner_margin"] = min(r["winner_minus_runner_up"] for r in city_rows)
    if split == "dev":
        raw = generate(directory, model, split, mode="question-only")
        question = original.metrics(raw, labels)
        save(directory / "question-only-metrics.json", question)
        metrics["known_context_gain"] = sum(
            metrics["categories"][k] - question["categories"][k] for k in ("city", "code")
        )
        metrics["development_gate"] = development_mastery(metrics)
    require(initial_hash(model) == before, "inference mutated weights")
    save(directory / "metrics.json", metrics)
    save(
        directory / "observation-seal.json",
        {p.name: sha(p) for p in directory.iterdir() if p.suffix in (".json", ".jsonl")},
    )
    return metrics


def training_mastery(m):
    return (
        m["exact"] == 96
        and m["eos"] == 96
        and m["malformed"] == 0
        and m["repetitive"] == 0
        and m["city_first_errors"] == 0
        and m["city_near_ties"] == 0
    )


def development_mastery(m):
    return (
        m["exact"] >= 22
        and m["categories"]["city"] >= 7
        and m["categories"]["code"] >= 7
        and m["categories"]["unknown"] == 8
        and m["eos"] == 24
        and m["malformed"] == 0
        and m["known_context_gain"] >= 8
    )


def primary_verdict(results):
    target = {a: results[cell(947, "ordinary", a)] for a in ARMS}
    paired = target["city-paired"]
    if not training_mastery(paired):
        return "REJECT_PAIRED_SUFFICIENCY_AT_ORDINARY947"
    for seed in SEEDS:
        for variant in PARAMETERS:
            p = results[cell(seed, variant, "city-paired")]
            for arm in ("original", "city-shuffled"):
                c = results[cell(seed, variant, arm)]
                if p["exact"] < c["exact"] or p["city_first_errors"] > c["city_first_errors"]:
                    return "REJECT_NO_REGRESSION_REQUIREMENT"
    if any(
        target[a]["city_first_errors"] <= paired["city_first_errors"]
        for a in ("original", "city-shuffled")
    ):
        return "NO_PAIRING_SPECIFIC_SUPPORT_COMPARATOR_MATCHES"
    return "SUPPORT_TARGETED_PAIRING_DISCRIMINATION_ONLY"


def development_comparison(results):
    if not results:
        return dict(evaluated=False, supported=False)
    gates = {}
    for seed in SEEDS:
        for variant in PARAMETERS:
            paired = results[cell(seed, variant, "city-paired")]
            gates[f"{seed}-{variant}"] = development_mastery(paired) and all(
                paired["exact"] >= results[cell(seed, variant, a)]["exact"]
                and paired["eos"] >= results[cell(seed, variant, a)]["eos"]
                for a in ("original", "city-shuffled")
            )
    city_totals = {
        a: sum(results[cell(s, v, a)]["categories"]["city"] for s in SEEDS for v in PARAMETERS)
        for a in ARMS
    }
    supported = all(gates.values()) and all(
        city_totals["city-paired"] > city_totals[a] for a in ("original", "city-shuffled")
    )
    return dict(evaluated=True, supported=supported, per_cell_gates=gates, city_totals=city_totals)


def stage(kind, seed=601, variant="ordinary", arm="original", costs=None):
    tag = f"{kind}-{cell(seed, variant, arm)}"
    directory = RUN / "stages" / tag
    command = [
        sys.executable,
        "-B",
        str(ROOT / "scripts/paired_batch_dev.py"),
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
    cost = watch(command, directory, RUN, CAPS[kind])
    if costs is not None:
        costs[tag] = cost
    require(
        cost["status"] == "PASS"
        and cost["complete_process_lifetimes"]
        and cost["active_processes"] == 0,
        "stage STOP: " + tag,
    )
    print(json.dumps(dict(stage=tag, cpu=cost["cpu"], wall=cost["wall"])), flush=True)
    return directory


def execute():
    verify_plan()
    save(
        RUN / "execution-start.json",
        dict(plan_sha256=sha(RUN / "plan.json"), maximum_fits=12, no_retry=True),
    )
    costs, results, development = {}, {}, {}
    try:
        contract = RUN / "preparation/contracts"
        test_command = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_paired_batch_dev.py",
            "tests/test_local_answer_dev.py",
            "tests/test_lifetime_job.py",
            "--basetemp",
            str(RUN / "preparation/pytest-tmp"),
        ]
        cost = watch(test_command, contract, RUN, CAPS["contracts"])
        costs["contracts"] = cost
        require(cost["status"] == "PASS" and cost["complete_process_lifetimes"], "contracts STOP")
        save(
            contract / "contracts-result.json",
            dict(
                status="PASS",
                pytest_returncode=cost["returncode"],
                complete_lifetime_source="parent Job",
                note="Result observed by controller after pytest exit; not a pytest self-receipt",
            ),
        )
        rehearsal_dir = RUN / "preparation/rehearsal"
        cost = watch(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts/paired_batch_dev.py"),
                "worker",
                "--kind",
                "rehearsal",
                "--directory",
                str(rehearsal_dir),
            ],
            rehearsal_dir,
            RUN,
            CAPS["rehearsal"],
        )
        costs["rehearsal"] = cost
        require(cost["status"] == "PASS" and cost["complete_process_lifetimes"], "rehearsal STOP")
        freeze_registration()
        for seed, variant, arm in ORDER:
            stage("fit", seed, variant, arm, costs)
            directory = stage("analyze", seed, variant, arm, costs)
            results[cell(seed, variant, arm)] = read(directory / "metrics.json")
        gates = {name: training_mastery(m) for name, m in results.items()}
        train_pass = all(gates.values())
        save(RUN / "training-gate.json", dict(pass_gate=train_pass, cells=gates))
        verdict = primary_verdict(results)
        if train_pass:
            for seed, variant, arm in ORDER:
                directory = stage("development", seed, variant, arm, costs)
                development[cell(seed, variant, arm)] = read(directory / "metrics.json")
        save(
            RUN / "summary.json",
            dict(
                registration_sha256=sha(RUN / "registration.json"),
                training_gate=train_pass,
                training_gates=gates,
                primary_verdict=verdict,
                development_evaluated=bool(development),
                development_comparison=development_comparison(development),
                development_gate=bool(development)
                and all(m["development_gate"] for m in development.values()),
                decision="STOP_TRAINING_FAILURE"
                if not train_pass
                else "DEVELOPMENT_GATES_PASS"
                if all(m["development_gate"] for m in development.values())
                else "STOP_DEVELOPMENT_FAILURE",
                results=results,
                development=development,
                stages=costs,
            ),
        )
        print(
            json.dumps(
                dict(
                    training_gate=train_pass,
                    primary_verdict=verdict,
                    development_evaluated=bool(development),
                )
            ),
            flush=True,
        )
    except BaseException as error:
        save(
            RUN / "failure.json",
            dict(error=repr(error), stages=costs, results=results, development=development),
        )
        raise


def audit():
    plan = verify_plan()
    preservation = read(RUN / "preservation-before.json")
    for name, meta in preservation["files"].items():
        path = ROOT / name
        require(
            path.stat().st_size == meta["bytes"] and sha(path) == meta["sha256"],
            "preserved input changed: " + name,
        )
    costs = {}
    for path in (RUN / "execution").glob("cost.json"):
        costs[path.relative_to(RUN).as_posix()] = read(path)
    for path in (RUN / "preparation").rglob("cost.json"):
        if "pytest-tmp" not in path.parts:
            costs[path.relative_to(RUN).as_posix()] = read(path)
    for path in (RUN / "stages").glob("*/cost.json"):
        costs[path.relative_to(RUN).as_posix()] = read(path)
    for name, c in costs.items():
        require(
            c["complete_process_lifetimes"] and c["active_processes"] == 0,
            "incomplete Job: " + name,
        )
        require(c["cpu"] == c["user_cpu"] + c["kernel_cpu"], "kernel CPU arithmetic")
    outer = costs["execution/cost.json"]
    if not (RUN / "summary.json").exists():
        return dict(
            status="STOP_PRESERVED",
            failure=read(RUN / "failure.json"),
            complete_outer_cost=outer,
            preserved_files=len(preservation["files"]),
            model_execution=False,
        )
    verify_registration()
    summary = read(RUN / "summary.json")
    schedules = read(RUN / "batch-schedules.json")
    labels = read(RUN / "train-labels.json")
    documentmap = {d["id"]: d for d in read(RUN / "train-documents.json")}
    from first_byte_probe import measurement

    actual = {}
    for seed, variant, arm in ORDER:
        identity = cell(seed, variant, arm)
        base = RUN / "stages" / f"fit-{identity}"
        trace = rows(base / "training.jsonl")
        schedule_rows = schedules[f"{seed}-{arm}"]
        require(len(trace) == STEPS, "trace length")
        for t, expected in zip(trace, schedule_rows, strict=True):
            require(all(t[k] == expected[k] for k in expected), "schedule/trace")
            require(t["forward_positions"] == 512, "dense work")
            require(
                t["history_targets"] + t["answer_targets"]
                == sum(len(documentmap[i]["text"].encode()) + 1 for i in t["ids"]),
                "trace targets",
            )
            require(
                math.isclose(
                    t["objective"],
                    (t["history_loss"] + t["answer_loss"])
                    / (t["history_targets"] + t["answer_targets"]),
                    rel_tol=1e-6,
                ),
                "uniform CE",
            )
        fitmeta = read(base / "checkpoint-meta.json")
        require(
            sha(base / "checkpoint.pt") == fitmeta["sha256"]
            and (base / "checkpoint.pt").stat().st_size == fitmeta["bytes"],
            "final checkpoint",
        )
        require(
            read(base / "training-summary.json")["initial_sha256"]
            == plan["initial_hashes"][f"{seed}-{variant}"],
            "same initialization",
        )
        directory = RUN / "stages" / f"analyze-{identity}"
        for name, expected in read(directory / "observation-seal.json").items():
            require(sha(directory / name) == expected, "observation seal")
        raw = rows(directory / "predictions-main.jsonl")
        require(raw[0]["result"] == raw[-1]["result"], "replay")
        rescored = original.metrics(raw[:-1], labels)
        m = read(directory / "metrics.json")
        require(all(rescored[k] == m[k] for k in rescored), "raw training scores")
        city = rows(directory / "city-first-token.jsonl")
        require(len(city) == 32, "city vectors")
        for r in city:
            derived = measurement(r["logits"], r["expected_first_id"])
            require(all(r[k] == v for k, v in derived.items()), "saved-vector margins")
        require(
            m["city_first_errors"] == sum(r["expected_rank"] != 1 for r in city), "first errors"
        )
        actual[identity] = m
    require(actual == summary["results"], "summary metrics")
    require(primary_verdict(actual) == summary["primary_verdict"], "primary verdict")
    gate = all(training_mastery(m) for m in actual.values())
    require(gate == summary["training_gate"], "global gate")
    require(gate or not summary["development_evaluated"], "development prohibition")
    require(not any(c["status"] != "PASS" for c in costs.values()), "Job STOP")
    return dict(
        status="PASS",
        primary_verdict=summary["primary_verdict"],
        decision=summary["decision"],
        training_gate=gate,
        development_evaluated=summary["development_evaluated"],
        fits=len(ORDER),
        saved_training_answers=12 * 96,
        city_vectors=12 * 32,
        complete_outer_cost=outer,
        preserved_files=len(preservation["files"]),
        model_execution=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "launch", "execute", "worker", "audit"))
    parser.add_argument("--kind", choices=("rehearsal", "fit", "analyze", "development"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--seed", type=int, default=601, choices=SEEDS)
    parser.add_argument("--variant", default="ordinary", choices=PARAMETERS)
    parser.add_argument("--arm", default="original", choices=ARMS)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "launch":
        verify_plan()
        require(not (RUN / "execution-start.json").exists(), "single registered attempt consumed")
        result = watch(
            [sys.executable, "-B", str(ROOT / "scripts/paired_batch_dev.py"), "execute"],
            RUN / "execution",
            RUN,
            CAPS["overall"],
        )
        print(json.dumps(result), flush=True)
        raise SystemExit(0 if result["status"] == "PASS" else 1)
    elif args.command == "execute":
        with controller_record(RUN / "execution"):
            execute()
    elif args.command == "audit":
        print(json.dumps(audit(), indent=2))
    else:
        require(
            args.directory and args.directory.resolve().is_relative_to(RUN), "new study path only"
        )
        with controller_record(args.directory):
            if args.kind == "rehearsal":
                verify_plan()
                rehearsal(args.directory)
            elif args.kind == "fit":
                fit(args.directory, args.seed, args.variant, args.arm)
            else:
                verify_registration()
                if args.kind == "development":
                    require(
                        read(RUN / "training-gate.json")["pass_gate"], "development gate closed"
                    )
                observations(
                    args.directory,
                    args.seed,
                    args.variant,
                    args.arm,
                    "dev" if args.kind == "development" else "train",
                )


if __name__ == "__main__":
    main()
