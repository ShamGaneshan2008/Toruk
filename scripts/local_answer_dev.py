"""Single-use local-answer development study with complete Windows Job lifetimes."""

import argparse
import json
import math
import random
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

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
    score,
    sha,
)
from lifetime_job import controller_record, watch

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-dev-v1"
PREP = ROOT / "artifacts/local-answer-dev-v1-preparation"
PROTOCOL = "docs/research/local-answer-dev-v1-protocol.md"
NAMES = ("uvo", "pex", "zim", "nax")
CITIES = ("la", "mi", "so", "tu")
CODES = ("R-7", "Q_2", "V:4", "Z!6")
INVENTORY = (*CITIES, *CODES, "?")
ORDER = ((601, "ordinary"), (601, "recurrent"), (947, "recurrent"), (947, "ordinary"))
STEPS = 1536
FORMAT = "toruk-local-answer-dev-v1"
SOURCES = [
    PROTOCOL,
    "scripts/local_answer_dev.py",
    "scripts/lifetime_job.py",
    "scripts/answer_trainability_dev.py",
    "scripts/segment_delta_watch.py",
    "tests/test_local_answer_dev.py",
    "tests/test_lifetime_job.py",
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


def parser_answer(prefix):
    history, question = prefix.rsplit("\n", 1)
    lhs = question[:-2]
    matches = [
        line.split("=", 1)[1]
        for line in history.splitlines()
        if "=" in line and line.split("=", 1)[0] == lhs
    ]
    return matches[-1] if matches else "?"


def question_only(prefix):
    lines = prefix.splitlines(keepends=True)
    require(len(lines) == 3, "exactly prelude/assignment/query required")
    return lines[0] + "." * (len(lines[1].encode()) - 1) + "\n" + lines[2]


def classify(ids):
    closed = any(score(ids, value) for value in INVENTORY)
    repetitive = any(
        ids[i : i + w] * 3 == ids[i : i + 3 * w]
        for w in (1, 2)
        for i in range(len(ids) - 3 * w + 1)
    )
    return dict(eos=bool(ids and ids[-1] == 2), malformed=not closed, repetitive=repetitive)


def datasets():
    files = {}
    for split in ("train", "dev"):
        inputs, labels, documents = [], [], []
        for entity, name in enumerate(NAMES):
            for category in ("city", "code", "unknown"):
                field = "role" if category == "unknown" else category
                query_field = "city" if category == "unknown" else field
                values = CODES if field == "code" else CITIES
                for pair in (0, 1):
                    value = values[(entity + pair + (0 if split == "train" else 2)) % 4]
                    templates = ("A", "B") if split == "train" else (("A", "B")[pair],)
                    for template in templates:
                        for _nonce in range(2 if split == "train" else 1):
                            index = len(inputs)
                            prelude = (f"note {split[0]}{index:03d}; " + "rain. " * 8)[:30] + "\n"
                            lhs = f"{name} {field}" if template == "A" else f"{field} {name}"
                            query = (
                                f"{name} {query_field}"
                                if template == "A"
                                else f"{query_field} {name}"
                            )
                            prefix = prelude + lhs + "=" + value + "\n" + query + "?="
                            gold = "?" if category == "unknown" else value
                            identity = f"{split}-{index:03d}"
                            inputs.append(dict(id=identity, prefix=prefix))
                            labels.append(
                                dict(
                                    id=identity,
                                    gold=gold,
                                    category=category,
                                    template=template,
                                    canonical=[name, field, value, query_field],
                                )
                            )
                            if split == "train":
                                documents.append(
                                    dict(
                                        id=identity,
                                        split="train",
                                        prefix=prefix,
                                        gold=gold,
                                        text=prefix + gold,
                                    )
                                )
        files[f"{split}-inputs.json"] = inputs
        files[f"{split}-labels.json"] = labels
        if split == "train":
            files["train-documents.json"] = documents
    return files


def validate(files):
    ids = set()
    texts = set()
    canonical = {}
    for split, size in (("train", 96), ("dev", 24)):
        inputs, labels = files[f"{split}-inputs.json"], files[f"{split}-labels.json"]
        require(len(inputs) == len(labels) == size, "split size")
        require(
            Counter(label["category"] for label in labels)
            == dict(city=size // 3, code=size // 3, unknown=size // 3),
            "category balance",
        )
        require(
            Counter(label["template"] for label in labels) == dict(A=size // 2, B=size // 2),
            "template balance",
        )
        canonical[split] = set()
        for case, label in zip(inputs, labels, strict=True):
            require(case["id"] == label["id"] and case["id"] not in ids, "ID overlap")
            ids.add(case["id"])
            prefix, gold = case["prefix"], label["gold"]
            require(prefix + gold not in texts, "text overlap")
            texts.add(prefix + gold)
            prelude, assignment, question = prefix.splitlines()
            require(len(prelude.encode()) + 1 == 31, "prelude placement")
            require(
                len((assignment + "\n" + question + gold).encode()) + 1 <= 32,
                "local answer exceeds segment",
            )
            require(len((prefix + gold).encode()) + 1 <= 64, "document bound")
            source_words, value = assignment.split("=", 1)
            query_words = question[:-2]
            a, b = source_words.split()
            q, r = query_words.split()
            source_name = a if a in NAMES else b
            source_field = b if a in NAMES else a
            query_name = q if q in NAMES else r
            query_field = r if q in NAMES else q
            inferred = value if (source_name, source_field) == (query_name, query_field) else "?"
            require(inferred == gold, "independent label/source check")
            key = (source_name, source_field, value, query_field)
            require(list(key) == label["canonical"], "canonical identity")
            canonical[split].add(key)
    require(not canonical["train"] & canonical["dev"], "canonical train/dev overlap")
    require(
        {label["gold"] for label in files["train-labels.json"]} == set(INVENTORY), "answer coverage"
    )
    for name in NAMES:
        for field in ("city", "code"):
            require(
                len({k[2] for k in canonical["train"] if k[0] == name and k[1] == field}) == 2,
                "multiple values per entity",
            )
    for document, case, label in zip(
        files["train-documents.json"],
        files["train-inputs.json"],
        files["train-labels.json"],
        strict=True,
    ):
        require(
            document
            == dict(**case, split="train", gold=label["gold"], text=case["prefix"] + label["gold"]),
            "training documents mismatch",
        )


def batch_objective(model, documents):
    from torch.nn import functional as F

    x, y, answer = make_batch(documents)
    logits = forward_batch(model, x)
    loss = F.cross_entropy(logits.transpose(1, 2), y, ignore_index=-100, reduction="none")
    valid = y.ne(-100)
    history = valid & ~answer
    h, a = loss[history].sum(), loss[answer].sum()
    nh, na = int(history.sum()), int(answer.sum())
    require(nh > 0 and na > 0, "nonempty loss partitions")
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
        # Valid synthetic two-segment texts: no study strings, questions, labels or answers.
        numeric = [dict(prefix="X" * 62, text="X" * 63) for _ in range(8)]
        times = []
        for _iteration in range(3):
            x, y, mask = make_batch(numeric)
            x = torch.randint(3, 259, x.shape)
            x[:, 0] = 1
            y = torch.randint(3, 259, y.shape)
            y[:, -1] = 2
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
                "rehearsal finite gradients",
            )
            times.append(
                dict(
                    cpu=time.process_time() - cpu,
                    wall=time.perf_counter() - began,
                    loss=float(loss.detach()),
                )
            )
        bound = 2 * max(max(t["cpu"], t["wall"]) for t in times[1:]) * STEPS + 10
        records[variant] = dict(
            iterations=times, projected_fit_seconds=bound, within_fit_cap=bound <= 120
        )
    save(
        directory / "rehearsal.json",
        dict(
            seed=900301,
            optimizer_steps=0,
            study_documents_used=False,
            records=records,
            pass_projection=all(r["within_fit_cap"] for r in records.values()),
        ),
    )
    require(
        all(r["within_fit_cap"] for r in records.values()),
        "fixed resource rehearsal projection failed",
    )


def freeze():
    from toruk_lm.tokenizer import ByteTokenizer

    contracts = read(PREP / "contracts-001/cost.json")
    numeric = read(PREP / "rehearsal-001/cost.json")
    rehearsal_summary = read(PREP / "rehearsal-001/rehearsal.json")
    require(
        all(
            c["status"] == "PASS" and c["complete_process_lifetimes"] for c in (contracts, numeric)
        ),
        "prerequisite accounting/caps failed",
    )
    require(rehearsal_summary["pass_projection"], "rehearsal failed")
    RUN.mkdir(parents=True, exist_ok=False)
    files = datasets()
    validate(files)
    for name, value in files.items():
        save(RUN / name, value)
    sources = {}
    for name in SOURCES:
        target = RUN / "sources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
        sources[name] = sha(target)
    counts = {v: sum(p.numel() for p in make_model(v).parameters()) for v in PARAMETERS}
    require(counts == PARAMETERS, "parameter budget")
    prerequisites = {
        str(p.relative_to(ROOT)): sha(p)
        for p in (
            PREP / "contracts-001/cost.json",
            PREP / "rehearsal-001/cost.json",
            PREP / "rehearsal-001/rehearsal.json",
        )
    }
    save(
        RUN / "registration.json",
        dict(
            version=FORMAT,
            protocol=PROTOCOL,
            sources=sources,
            data={n: sha(RUN / n) for n in files},
            runtime=runtime(),
            config=CONFIG,
            parameters=PARAMETERS,
            tokenizer=dict(identity=ByteTokenizer.identity, fingerprint=ByteTokenizer.fingerprint),
            order=ORDER,
            steps=STEPS,
            batch=8,
            objective="uniform CE including EOS",
            prerequisites=prerequisites,
            caps=dict(
                fit=120,
                generate=20,
                loss=20,
                controls=10,
                overall=1000,
                memory=2 * 1024**3,
                disk=128 * 1024**2,
                request=2,
            ),
            gates=dict(
                train_exact=90,
                train_eos=96,
                dev_exact=22,
                dev_eos=24,
                city=7,
                code=7,
                unknown=8,
                known_context_gain=8,
            ),
            base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            status="FROZEN_BEFORE_STUDY_TRAINING_AND_ANSWERS",
        ),
    )
    print(json.dumps(dict(registration_sha256=sha(RUN / "registration.json"), parameters=counts)))


def verify(data=True):
    reg = read(RUN / "registration.json")
    require(reg["runtime"] == runtime(), "runtime changed")
    for name, digest in reg["sources"].items():
        require(
            sha(ROOT / name) == sha(RUN / "sources" / name) == digest, f"source changed: {name}"
        )
    for name, digest in reg["prerequisites"].items():
        require(sha(ROOT / name) == digest, "prerequisite changed")
    if data:
        for name, digest in reg["data"].items():
            require(sha(RUN / name) == digest, f"data changed: {name}")
    return reg


def checked_data(filename):
    require(
        sha(RUN / filename) == read(RUN / "registration.json")["data"][filename], "data identity"
    )
    return read(RUN / filename)


def train(directory, seed, variant):
    import torch

    from toruk_lm.engine import setup

    setup(seed, 1)
    model = make_model(variant)
    initial = initial_hash(model)
    documents = checked_data("train-documents.json")
    require(
        all(d["split"] == "train" for d in documents) and len(documents) == 96,
        "training-only input",
    )
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
        for step in range(STEPS):
            indices = []
            for offset in range(8):
                epoch, index = divmod(step * 8 + offset, len(documents))
                order = list(range(len(documents)))
                random.Random(seed + epoch).shuffle(order)
                indices.append(order[index])
            selected = [documents[i] for i in indices]
            optimizer.zero_grad(set_to_none=True)
            objective, stats = batch_objective(model, selected)
            require(torch.isfinite(objective), "nonfinite loss")
            objective.backward()
            require(
                all(
                    p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()
                ),
                "missing/nonfinite gradient",
            )
            norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            optimizer.step()
            require(all(torch.isfinite(p).all() for p in model.parameters()), "nonfinite weights")
            targets += stats["history_targets"] + stats["answer_targets"]
            positions += stats["forward_positions"]
            stream.write(
                json.dumps(
                    dict(
                        step=step + 1,
                        ids=[d["id"] for d in selected],
                        objective=float(objective.detach()),
                        gradient_norm=norm,
                        **stats,
                    ),
                    allow_nan=False,
                )
                + "\n"
            )
            stream.flush()
    payload = dict(
        format=FORMAT,
        registration=sha(RUN / "registration.json"),
        config=CONFIG,
        seed=seed,
        variant=variant,
        steps=STEPS,
        model=model.state_dict(),
        optimizer=optimizer.state_dict(),
        torch_rng=torch.get_rng_state(),
        python_rng=random.getstate(),
        targets=targets,
        initial_sha256=initial,
    )
    path = directory / "checkpoint.pt"
    torch.save(payload, path)
    save(directory / "checkpoint-meta.json", dict(sha256=sha(path), bytes=path.stat().st_size))
    save(
        directory / "training-summary.json",
        dict(
            targets=targets,
            forward_positions=positions,
            steps=STEPS,
            presentations=STEPS * 8,
            initial_sha256=initial,
            loop_cpu=time.process_time() - cpu,
            loop_wall=time.perf_counter() - began,
        ),
    )


def load(seed, variant):
    import torch

    from toruk_lm.engine import setup

    setup(seed, 1)
    directory = RUN / "stages" / f"train-{seed}-{variant}"
    path = directory / "checkpoint.pt"
    meta = read(directory / "checkpoint-meta.json")
    require(
        sha(path) == meta["sha256"] and path.stat().st_size == meta["bytes"], "checkpoint hash/size"
    )
    saved = torch.load(path, weights_only=True, map_location="cpu")
    require(
        saved["format"] == FORMAT
        and saved["registration"] == sha(RUN / "registration.json")
        and saved["config"] == CONFIG,
        "checkpoint identity",
    )
    require(
        saved["seed"] == seed and saved["variant"] == variant and saved["steps"] == STEPS,
        "checkpoint cell/progress",
    )
    require(all(torch.isfinite(v).all() for v in saved["model"].values()), "nonfinite checkpoint")
    require(
        all(float(s["step"]) == STEPS for s in saved["optimizer"]["state"].values()),
        "optimizer progress",
    )
    model = make_model(variant)
    model.load_state_dict(saved["model"], strict=True)
    model.eval()
    return model


def generate(directory, model, split, mode):
    from toruk_lm.owned_lm import OwnedSession

    inputs = checked_data(f"{split}-inputs.json")
    first = None
    with (directory / "predictions.jsonl").open("x", encoding="utf-8") as stream:
        for index, case in enumerate([*inputs, inputs[0]]):
            prefix = question_only(case["prefix"]) if mode == "question-only" else case["prefix"]
            began, cpu = time.perf_counter(), time.process_time()
            result = OwnedSession(model).generate(prefix, budget=8)
            cost = dict(cpu=time.process_time() - cpu, wall=time.perf_counter() - began)
            require(max(cost.values()) <= 2, "request cap")
            require(index != len(inputs) or result == first, "deterministic replay mismatch")
            if index == 0:
                first = result
            stream.write(
                json.dumps(
                    dict(
                        id=case["id"],
                        prefix=prefix,
                        original_prefix=case["prefix"],
                        input_ids=[1, *(b + 3 for b in prefix.encode())],
                        result=result,
                        cost=cost,
                        replay=index == len(inputs),
                    )
                )
                + "\n"
            )
            stream.flush()
    save(
        directory / "seal.json",
        dict(sha256=sha(directory / "predictions.jsonl"), requests=len(inputs) + 1),
    )


def metrics(predictions, labels):
    counts = Counter()
    categories = Counter()
    templates = Counter()
    case_rows = []
    for p, label in zip(predictions, labels, strict=True):
        require(p["id"] == label["id"], "label order")
        ids = p["result"]["generated_ids"]
        flags = classify(ids)
        correct = score(ids, label["gold"])
        counts.update({k: int(v) for k, v in dict(exact=correct, **flags).items()})
        categories[label["category"]] += int(correct)
        templates[label["template"]] += int(correct)
        case_rows.append(
            dict(
                id=label["id"],
                gold=label["gold"],
                category=label["category"],
                template=label["template"],
                correct=correct,
                **flags,
            )
        )
    return dict(
        count=len(labels),
        **counts,
        categories=dict(categories),
        templates=dict(templates),
        cases=case_rows,
    )


def evaluate(directory, model, seed, variant, split):
    import torch

    pred = RUN / "stages" / f"generate-{split}-{seed}-{variant}" / "predictions.jsonl"
    require(sha(pred) == read(pred.parent / "seal.json")["sha256"], "prediction seal")
    predictions = rows(pred)[:-1]
    labels = checked_data(f"{split}-labels.json")
    result = metrics(predictions, labels)
    totals = Counter()
    with torch.no_grad(), (directory / "losses.jsonl").open("x", encoding="utf-8") as stream:
        for p, label in zip(predictions, labels, strict=True):
            began, cpu = time.perf_counter(), time.process_time()
            objective, stats = batch_objective(
                model, [dict(prefix=p["prefix"], text=p["prefix"] + label["gold"])]
            )
            require(
                max(time.perf_counter() - began, time.process_time() - cpu) <= 2, "loss request cap"
            )
            totals.update(
                {
                    k: stats[k]
                    for k in ("history_loss", "answer_loss", "history_targets", "answer_targets")
                }
            )
            stream.write(json.dumps(dict(id=p["id"], **stats)) + "\n")
    result.update(
        full_nll=(totals["history_loss"] + totals["answer_loss"])
        / (totals["history_targets"] + totals["answer_targets"]),
        history_nll=totals["history_loss"] / totals["history_targets"],
        answer_nll=totals["answer_loss"] / totals["answer_targets"],
    )
    save(directory / "metrics.json", result)


def controls(directory):
    inputs = checked_data("dev-inputs.json")
    documents = checked_data("train-documents.json")
    prior = defaultdict(Counter)
    for doc in documents:
        prior[doc["prefix"].splitlines()[-1]][doc["gold"]] += 1
    for kind in ("source-parser", "question-prior"):
        predictions = []
        with (directory / f"{kind}.jsonl").open("x", encoding="utf-8") as stream:
            for case in inputs:
                value = (
                    parser_answer(case["prefix"])
                    if kind == "source-parser"
                    else sorted(
                        prior[case["prefix"].splitlines()[-1]],
                        key=lambda v: (-prior[case["prefix"].splitlines()[-1]][v], v),
                    )[0]
                )
                row = dict(
                    id=case["id"],
                    prefix=case["prefix"],
                    result=dict(generated_ids=[*(b + 3 for b in value.encode()), 2]),
                )
                stream.write(json.dumps(row) + "\n")
                predictions.append(row)
        # Open labels only after all raw continuations for this control are saved.
        save(
            directory / f"{kind}-metrics.json",
            metrics(predictions, checked_data("dev-labels.json")),
        )


def worker(args):
    with controller_record(args.directory):
        if args.stage == "rehearsal":
            rehearsal(args.directory)
            return
        if args.stage == "freeze":
            freeze()
            return
        verify(data=False)
        if args.stage == "train":
            train(args.directory, args.seed, args.variant)
            return
        if args.stage == "controls":
            controls(args.directory)
            return
        model = load(args.seed, args.variant)
        if args.stage == "generate":
            generate(args.directory, model, args.split, args.mode)
        elif args.stage == "loss":
            evaluate(args.directory, model, args.seed, args.variant, args.split)


def run():
    reg = verify()
    save(
        RUN / "run-start.json",
        dict(registration_sha256=sha(RUN / "registration.json"), order=ORDER),
    )
    costs = {}
    results = {}

    def stage(kind, seed=601, variant="ordinary", split="train", mode="main"):
        tag = (
            f"train-{seed}-{variant}"
            if kind == "train"
            else "controls"
            if kind == "controls"
            else (
                f"{kind}-{split}-{seed}-{variant}"
                + ("-question-only" if mode == "question-only" else "")
            )
        )
        directory = RUN / "stages" / tag
        command = [
            sys.executable,
            "-B",
            str(ROOT / "scripts/local_answer_dev.py"),
            "worker",
            "--stage",
            kind,
            "--directory",
            str(directory),
            "--seed",
            str(seed),
            "--variant",
            variant,
            "--split",
            split,
            "--mode",
            mode,
        ]
        cost = watch(
            command,
            directory,
            RUN,
            reg["caps"]["fit" if kind == "train" else kind],
            reg["caps"]["memory"],
            reg["caps"]["disk"],
        )
        costs[tag] = cost
        require(
            cost["status"] == "PASS" and cost["complete_process_lifetimes"], f"stage STOP: {tag}"
        )
        print(
            json.dumps(dict(stage=tag, cpu=cost["cpu"], wall=cost["wall"], status=cost["status"])),
            flush=True,
        )
        return directory

    try:
        for seed, variant in ORDER:
            stage("train", seed, variant)
            stage("generate", seed, variant)
            directory = stage("loss", seed, variant)
            results[f"train-{seed}-{variant}"] = read(directory / "metrics.json")
        train_pass = all(
            m["exact"] >= 90 and m["eos"] == 96 and m["malformed"] == 0 for m in results.values()
        )
        save(RUN / "training-gate.json", dict(pass_gate=train_pass, metrics=results))
        gates = {}
        if train_pass:
            control_dir = stage("controls")
            parser = read(control_dir / "source-parser-metrics.json")
            require(parser["exact"] == 24, "source parser/control integrity failed")
            for seed, variant in ORDER:
                stage("generate", seed, variant, split="dev")
                directory = stage("loss", seed, variant, split="dev")
                main = read(directory / "metrics.json")
                qdir = stage("generate", seed, variant, split="dev", mode="question-only")
                raw = rows(qdir / "predictions.jsonl")[:-1]
                diagnostic = metrics(raw, checked_data("dev-labels.json"))
                save(qdir / "metrics.json", diagnostic)
                results[f"dev-{seed}-{variant}"] = main
                results[f"question-only-{seed}-{variant}"] = diagnostic
                gain = sum(
                    main["categories"][k] - diagnostic["categories"][k] for k in ("city", "code")
                )
                gates[f"{seed}-{variant}"] = dict(
                    exact=main["exact"] >= 22,
                    city=main["categories"]["city"] >= 7,
                    code=main["categories"]["code"] >= 7,
                    unknown=main["categories"]["unknown"] == 8,
                    eos=main["eos"] == 24,
                    format=main["malformed"] == 0,
                    context_gain=gain >= 8,
                    known_gain=gain,
                )
        passed = train_pass and all(
            all(value for key, value in gate.items() if key != "known_gain")
            for gate in gates.values()
        )
        decision = (
            "READY_FOR_SEPARATELY_REGISTERED_MEMORY_COMPARISON"
            if passed
            else "STOP_GENERALIZATION_FAILURE"
            if train_pass
            else "STOP_TRAINING_FAILURE"
        )
        save(
            RUN / "summary.json",
            dict(
                registration_sha256=sha(RUN / "registration.json"),
                decision=decision,
                training_gate=train_pass,
                gates=gates,
                results=results,
                stages=costs,
            ),
        )
        print(json.dumps(dict(decision=decision, gates=gates)), flush=True)
    except BaseException as error:
        save(RUN / "failure.json", dict(error=repr(error), stages=costs, results=results))
        raise


def audit():
    verify()
    summary = read(RUN / "summary.json")
    refs = {}
    for seed, variant in ORDER:
        directory = RUN / "stages" / f"train-{seed}-{variant}"
        trace = rows(directory / "training.jsonl")
        require(
            len(trace) == STEPS and [r["step"] for r in trace] == list(range(1, STEPS + 1)),
            "training trace steps",
        )
        signature = [
            (r["ids"], r["history_targets"], r["answer_targets"], r["forward_positions"])
            for r in trace
        ]
        require(signature == refs.setdefault(seed, signature), "unmatched data/compute")
        require(
            all(
                math.isclose(
                    r["objective"],
                    (r["history_loss"] + r["answer_loss"])
                    / (r["history_targets"] + r["answer_targets"]),
                    rel_tol=1e-6,
                )
                for r in trace
            ),
            "uniform objective",
        )
        counts = Counter(i for row in trace for i in row["ids"])
        require(set(counts.values()) == {128} and len(counts) == 96, "exposure")
        load(seed, variant)
    for name, cost in summary["stages"].items():
        require(
            cost["status"] == "PASS"
            and cost["complete_process_lifetimes"]
            and cost["active_processes"] == 0,
            "stage accounting",
        )
        require(
            read(RUN / "stages" / name / "controller-final.json")["status"] == "PASS",
            "controller finally receipt",
        )
        path = RUN / "stages" / name / "predictions.jsonl"
        if path.exists():
            require(sha(path) == read(path.parent / "seal.json")["sha256"], "prediction seal")
            predictions = rows(path)
            require(predictions[0]["result"] == predictions[-1]["result"], "replay")
            split = "train" if name.startswith("generate-train-") else "dev"
            actual = metrics(predictions[:-1], checked_data(f"{split}-labels.json"))
            stored = (
                read(path.parent / "metrics.json")
                if "question-only" in name
                else read(RUN / "stages" / name.replace("generate-", "loss-", 1) / "metrics.json")
            )
            require(
                all(
                    actual[k] == stored[k]
                    for k in ("exact", "eos", "malformed", "repetitive", "categories", "templates")
                ),
                "raw scores",
            )
    outer = read(RUN / "execution/cost.json")
    require(
        outer["status"] == "PASS"
        and outer["complete_process_lifetimes"]
        and outer["active_processes"] == 0,
        "complete enclosing accounting",
    )
    require(
        read(RUN / "execution/controller-final.json")["status"] == "PASS",
        "root controller final receipt",
    )
    return dict(
        status="PASS",
        decision=summary["decision"],
        registration_sha256=sha(RUN / "registration.json"),
        complete_job_cpu=outer["cpu"],
        job_wall=outer["wall"],
        training_or_generation_executed=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("worker", "run", "audit"))
    parser.add_argument(
        "--stage", choices=("rehearsal", "freeze", "train", "generate", "loss", "controls")
    )
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--seed", type=int, choices=(601, 947), default=601)
    parser.add_argument("--variant", choices=PARAMETERS, default="ordinary")
    parser.add_argument("--split", choices=("train", "dev"), default="train")
    parser.add_argument("--mode", choices=("main", "question-only"), default="main")
    args = parser.parse_args()
    if args.command == "run":
        with controller_record(RUN / "execution"):
            run()
    elif args.command == "audit":
        print(json.dumps(audit(), sort_keys=True))
    else:
        require(
            args.directory and args.directory.resolve().is_relative_to(ROOT),
            "workspace output required",
        )
        worker(args)


if __name__ == "__main__":
    main()
