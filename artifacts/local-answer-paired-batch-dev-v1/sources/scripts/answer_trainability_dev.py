"""Single-use answer-trainability development study; no old data or chat imports."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from segment_delta_watch import watch, worker_receipt

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/answer-trainability-dev-v1"
PROTOCOL = "docs/research/answer-trainability-dev-v1-protocol.md"
CONFIG = dict(context=32, width=16, heads=4, layers=1, slots=4, max_document_tokens=64)
PARAMETERS = dict(ordinary=14058, recurrent=14416)
WEIGHTS = dict(uniform=1, answer16=16)
ORDER = [
    (419, "uniform", "ordinary"),
    (419, "uniform", "recurrent"),
    (419, "answer16", "ordinary"),
    (419, "answer16", "recurrent"),
    (733, "answer16", "recurrent"),
    (733, "answer16", "ordinary"),
    (733, "uniform", "recurrent"),
    (733, "uniform", "ordinary"),
]
INVENTORY = ("la", "mi", "so", "tu", "R-7", "Q_2", "?")
SOURCES = [
    PROTOCOL,
    "scripts/answer_trainability_dev.py",
    "tests/test_answer_trainability_dev.py",
    "scripts/segment_delta_watch.py",
    "src/toruk_lm/owned_lm.py",
    "src/toruk_lm/recurrent.py",
    "src/toruk_lm/model.py",
    "src/toruk_lm/tokenizer.py",
    "src/toruk_lm/engine.py",
    "src/toruk_lm/data.py",
    ".gitattributes",
    "pyproject.toml",
]
FORMAT = "toruk-answer-trainability-dev-v1"
STARTED = time.perf_counter()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime():
    return dict(
        python=platform.python_version(),
        torch=importlib.metadata.version("torch"),
        psutil=importlib.metadata.version("psutil"),
        platform=platform.platform(),
    )


def data_files():
    train_specs = [
        ("uvo", "city", "la", "city"),
        ("pex", "city", "mi", "city"),
        ("zim", "city", "so", "city"),
        ("nax", "city", "tu", "city"),
        ("uvo", "code", "R-7", "code"),
        ("pex", "code", "Q_2", "code"),
        ("zim", "role", "mi", "city"),
        ("nax", "role", "la", "city"),
    ]
    dev_specs = [
        ("uvo", "city", "mi", "city"),
        ("uvo", "city", "so", "city"),
        ("pex", "city", "so", "city"),
        ("pex", "city", "tu", "city"),
        ("zim", "city", "tu", "city"),
        ("zim", "city", "la", "city"),
        ("nax", "city", "la", "city"),
        ("nax", "city", "mi", "city"),
        ("zim", "code", "R-7", "code"),
        ("nax", "code", "R-7", "code"),
        ("uvo", "code", "Q_2", "code"),
        ("zim", "code", "Q_2", "code"),
        ("uvo", "role", "so", "city"),
        ("pex", "role", "tu", "city"),
        ("zim", "role", "la", "city"),
        ("nax", "role", "mi", "city"),
    ]
    files = {}
    for split, specs in (("train", train_specs), ("dev", dev_specs)):
        inputs, labels, documents = [], [], []
        for index, (name, field, value, query_field) in enumerate(specs):
            prelude = (f"note {split[0]}{index:03d}; " + "rain. " * 8)[:30] + "\n"
            core = f"{name} {field}={value}\n{name} {query_field}?="
            prefix = prelude + core
            gold = value if field == query_field else "?"
            identity = f"{split}-{index:03d}"
            inputs.append(dict(id=identity, prefix=prefix))
            labels.append(
                dict(id=identity, gold=gold, category=field if field != "role" else "unknown")
            )
            documents.append(
                dict(id=identity, split=split, prefix=prefix, gold=gold, text=prefix + gold)
            )
        files[f"{split}-inputs.json"] = inputs
        files[f"{split}-labels.json"] = labels
        if split == "train":
            files["train-documents.json"] = documents
    return files


def validate_data(files):
    seen_ids, seen_texts, seen_cores = set(), set(), set()
    for split, count, counts in (
        ("train", 8, dict(city=4, code=2, unknown=2)),
        ("dev", 16, dict(city=8, code=4, unknown=4)),
    ):
        inputs, labels = files[f"{split}-inputs.json"], files[f"{split}-labels.json"]
        require(len(inputs) == len(labels) == count, "split size")
        require(dict(Counter(label["category"] for label in labels)) == counts, "category balance")
        for case, label in zip(inputs, labels, strict=True):
            require(case["id"] == label["id"] and case["id"] not in seen_ids, "IDs overlap")
            seen_ids.add(case["id"])
            prefix, gold = case["prefix"], label["gold"]
            prelude, assignment, query = prefix.splitlines()
            require(len(prelude.encode()) + 1 == 31, "prelude placement")
            entity, field = query[:-2].split()
            source = assignment.split("=", 1)
            inferred = source[1] if source[0] == f"{entity} {field}" else "?"
            require(inferred == gold and gold in INVENTORY, "independent source check")
            core = assignment + "\n" + query
            require(core not in seen_cores and prefix + gold not in seen_texts, "texts overlap")
            seen_cores.add(core)
            seen_texts.add(prefix + gold)
            require(len((core + gold).encode()) + 1 <= 32, "answer crosses local segment")
            require(len((prefix + gold).encode()) + 1 <= 64, "document exceeds bound")
    require({r["gold"] for r in files["train-labels.json"]} == set(INVENTORY), "answer coverage")
    for doc, case, label in zip(
        files["train-documents.json"],
        files["train-inputs.json"],
        files["train-labels.json"],
        strict=True,
    ):
        require(
            doc
            == dict(**case, split="train", gold=label["gold"], text=case["prefix"] + label["gold"]),
            "training mismatch",
        )


def make_model(variant, config=CONFIG):
    from toruk_lm.owned_lm import OwnedConfig, build_model

    return build_model(
        OwnedConfig(**config), "ordinary_matched" if variant == "ordinary" else "memory_on"
    )


def initial_hash(model):
    digest = hashlib.sha256()
    for name, value in model.state_dict().items():
        digest.update(name.encode())
        digest.update(value.detach().numpy().tobytes())
    return digest.hexdigest()


def make_batch(documents, context=32):
    import torch

    from toruk_lm.tokenizer import ByteTokenizer

    encoded = [ByteTokenizer().encode(d["text"], document=True) for d in documents]
    size = max(len(t) - 1 for t in encoded)
    x = torch.zeros(len(documents), size, dtype=torch.long)
    y = torch.full_like(x, -100)
    answer = torch.zeros_like(x, dtype=torch.bool)
    for index, (doc, tokens) in enumerate(zip(documents, encoded, strict=True)):
        length = len(tokens) - 1
        x[index, :length] = torch.tensor(tokens[:-1])
        y[index, :length] = torch.tensor(tokens[1:])
        answer[index, len(doc["prefix"].encode()) : length] = True
    require(not (x[:, ::context] == 0).any(), "empty batch segment")
    return x, y, answer


def forward_batch(model, x):
    import torch

    from toruk_lm.owned_lm import OwnedMemoryLM, segment

    state = model.initial_state(len(x)) if isinstance(model, OwnedMemoryLM) else None
    logits = []
    for start in range(0, x.shape[1], model.config.context):
        value, state = segment(
            model, x[:, start : start + model.config.context], state, read=True, write=True
        )
        logits.append(value)
    return torch.cat(logits, dim=1)


def loss_parts(logits, targets, answer, weight):
    import torch
    from torch.nn import functional as F

    valid = targets.ne(-100)
    answer = answer & valid
    history = valid & ~answer
    losses = F.cross_entropy(logits.transpose(1, 2), targets, ignore_index=-100, reduction="none")
    nh, na = int(history.sum()), int(answer.sum())
    denominator = nh + weight * na
    require(nh > 0 and na > 0 and denominator > 0, "empty objective partition")
    h, a = losses[history].sum(), losses[answer].sum()
    factors = torch.where(answer, weight, 1) * valid / denominator
    with torch.no_grad():
        residual = logits.softmax(-1)
        residual.scatter_add_(-1, targets.clamp_min(0)[..., None], -valid[..., None].float())
        logit_gradient_norm = residual.norm(dim=-1) * factors
    return (
        h / denominator,
        weight * a / denominator,
        dict(
            history_targets=nh,
            answer_targets=na,
            denominator=denominator,
            answer_weight_mass=weight * na / denominator,
            history_loss_sum=float(h.detach()),
            answer_loss_sum=float(a.detach()),
            history_contribution=float(h.detach()) / denominator,
            answer_contribution=weight * float(a.detach()) / denominator,
            token_ce=losses.detach(),
            token_weighted_loss=(losses * factors).detach(),
            token_logit_gradient_l2=logit_gradient_norm,
        ),
    )


def gradient_parts(model, history, answer):
    import torch

    parameters = list(model.parameters())
    gh = torch.autograd.grad(history, parameters, retain_graph=True, allow_unused=True)
    ga = torch.autograd.grad(answer, parameters, allow_unused=True)
    hs = ans = dot = total = 0.0
    for parameter, h, a in zip(parameters, gh, ga, strict=True):
        require(h is not None or a is not None, "parameter has no objective path")
        h = torch.zeros_like(parameter) if h is None else h
        a = torch.zeros_like(parameter) if a is None else a
        parameter.grad = h + a
        require(torch.isfinite(parameter.grad).all(), "nonfinite gradient")
        hs += float(h.double().square().sum())
        ans += float(a.double().square().sum())
        dot += float((h.double() * a.double()).sum())
        total += float(parameter.grad.double().square().sum())
    return dict(
        history_gradient_l2=math.sqrt(hs),
        answer_gradient_l2=math.sqrt(ans),
        gradient_dot=dot,
        combined_gradient_l2=math.sqrt(total),
        answer_projection_on_total=(ans + dot) / total if total else None,
        history_projection_on_total=(hs + dot) / total if total else None,
    )


def score(ids, gold):
    return ids == [*(b + 3 for b in gold.encode("utf-8")), 2]


def classify(ids):
    closed = any(score(ids, answer) for answer in INVENTORY)
    repeated = any(
        ids[start : start + width] * 3 == ids[start : start + 3 * width]
        for width in (1, 2)
        for start in range(len(ids) - 3 * width + 1)
    )
    return dict(eos=bool(ids and ids[-1] == 2), malformed=not closed, repetitive=repeated)


def freeze(contracts):
    from toruk_lm.engine import setup
    from toruk_lm.tokenizer import ByteTokenizer

    require(read(contracts)["status"] == "PASS", "contracts failed")
    RUN.mkdir(parents=True, exist_ok=False)
    files = data_files()
    validate_data(files)
    for name, value in files.items():
        save(RUN / name, value)
    sources = {}
    for name in SOURCES:
        target = RUN / "sources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
        sources[name] = sha(target)
    shutil.copyfile(contracts, RUN / "contracts-cost.json")
    counts = {}
    for variant in PARAMETERS:
        setup(419, 1)
        model = make_model(variant)
        counts[variant] = sum(p.numel() for p in model.parameters())
    require(
        counts == PARAMETERS and max(counts.values()) / min(counts.values()) <= 1.03,
        "parameter budgets",
    )
    save(
        RUN / "registration.json",
        dict(
            version=FORMAT,
            diagnosis_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            git_status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(),
            runtime=runtime(),
            tokenizer=dict(identity=ByteTokenizer.identity, fingerprint=ByteTokenizer.fingerprint),
            config=CONFIG,
            parameters=PARAMETERS,
            objectives=WEIGHTS,
            order=ORDER,
            optimizer=dict(
                steps=512,
                batch=4,
                lr=0.003,
                betas=[0.9, 0.999],
                eps=1e-8,
                weight_decay=0.01,
                clip=1.0,
            ),
            caps=dict(
                fit=180,
                generate=20,
                loss=20,
                request=2,
                controller=60,
                overall=2400,
                memory=2 * 1024**3,
                disk=256 * 1024**2,
            ),
            scorer="exact UTF-8 bytes+3 then EOS2; no repair",
            data={name: sha(RUN / name) for name in files},
            sources=sources,
            contracts_sha256=sha(RUN / "contracts-cost.json"),
            success=dict(
                tiny_exact=8, dev_exact=12, dev_eos=16, dev_malformed=0, city=6, code=3, unknown=3
            ),
            status="FROZEN_BEFORE_STUDY_FITS_AND_ANSWERS",
        ),
    )
    print(json.dumps(dict(registration_sha256=sha(RUN / "registration.json"), parameters=counts)))


def verify(full_data=True):
    reg = read(RUN / "registration.json")
    require(reg["runtime"] == runtime(), "runtime mismatch")
    for name, expected in reg["sources"].items():
        require(
            sha(ROOT / name) == sha(RUN / "sources" / name) == expected, f"source changed: {name}"
        )
    if full_data:
        for name, expected in reg["data"].items():
            require(sha(RUN / name) == expected, f"data changed: {name}")
    require(sha(RUN / "contracts-cost.json") == reg["contracts_sha256"], "test receipt changed")
    return reg


def cell_name(seed, objective, variant):
    return f"{seed}-{objective}-{variant}"


def train(directory, seed, objective, variant):
    import torch

    from toruk_lm.engine import setup

    setup(seed, 1)
    model = make_model(variant)
    before = initial_hash(model)
    require(
        sha(RUN / "train-documents.json")
        == read(RUN / "registration.json")["data"]["train-documents.json"],
        "training data identity",
    )
    documents = read(RUN / "train-documents.json")
    require(
        len(documents) == 8 and all(d["split"] == "train" for d in documents), "training-only bound"
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
    targets = answer_targets = positions = 0
    setup_wall = time.perf_counter() - STARTED
    loop_wall, loop_cpu = time.perf_counter(), time.process_time()
    with (directory / "training.jsonl").open("x", encoding="utf-8") as stream:
        for step in range(512):
            indices = []
            for offset in range(4):
                epoch, position = divmod(step * 4 + offset, len(documents))
                order = list(range(len(documents)))
                random.Random(seed + epoch).shuffle(order)
                indices.append(order[position])
            batch = [documents[i] for i in indices]
            x, y, mask = make_batch(batch)
            optimizer.zero_grad(set_to_none=True)
            logits = forward_batch(model, x)
            history, answer, stats = loss_parts(logits, y, mask, WEIGHTS[objective])
            require(torch.isfinite(history + answer), "nonfinite objective")
            stats.update(gradient_parts(model, history, answer))
            norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            optimizer.step()
            require(all(torch.isfinite(p).all() for p in model.parameters()), "nonfinite weights")
            target_ids, token_ce, token_weighted_loss, token_logit_gradient_l2 = [], [], [], []
            for i in range(len(batch)):
                valid = y[i].ne(-100)
                target_ids.append(y[i, valid].tolist())
                token_ce.append(stats["token_ce"][i, valid].tolist())
                token_weighted_loss.append(stats["token_weighted_loss"][i, valid].tolist())
                token_logit_gradient_l2.append(stats["token_logit_gradient_l2"][i, valid].tolist())
            for key in ("token_ce", "token_weighted_loss", "token_logit_gradient_l2"):
                del stats[key]
            count = int(y.ne(-100).sum())
            targets += count
            answer_targets += int(mask.sum())
            positions += x.numel()
            stream.write(
                json.dumps(
                    dict(
                        step=step + 1,
                        ids=[d["id"] for d in batch],
                        target_ids=target_ids,
                        answer_start=[len(d["prefix"].encode()) for d in batch],
                        token_ce=token_ce,
                        token_weighted_loss=token_weighted_loss,
                        token_logit_gradient_l2=token_logit_gradient_l2,
                        clip_input_norm=norm,
                        forward_positions=x.numel(),
                        **stats,
                    ),
                    allow_nan=False,
                )
                + "\n"
            )
            stream.flush()
    loop_cost = dict(cpu=time.process_time() - loop_cpu, wall=time.perf_counter() - loop_wall)
    payload = dict(
        format=FORMAT,
        registration=sha(RUN / "registration.json"),
        variant=variant,
        seed=seed,
        objective=objective,
        config=CONFIG,
        tokenizer=read(RUN / "registration.json")["tokenizer"],
        model=model.state_dict(),
        optimizer=optimizer.state_dict(),
        next_step=512,
        presentations=2048,
        targets=targets,
        answer_targets=answer_targets,
        initial_sha256=before,
        torch_rng=torch.get_rng_state(),
        python_rng=random.getstate(),
    )
    path = directory / "checkpoint.pt"
    torch.save(payload, path)
    save(directory / "checkpoint-meta.json", dict(sha256=sha(path), bytes=path.stat().st_size))
    save(
        directory / "training-summary.json",
        dict(
            targets=targets,
            answer_targets=answer_targets,
            forward_positions=positions,
            parameters=sum(p.numel() for p in model.parameters()),
            initial_sha256=before,
            steps=512,
            presentations=2048,
            loop=loop_cost,
        ),
    )
    return setup_wall


def load_model(seed, objective, variant):
    import torch

    from toruk_lm.engine import setup

    setup(seed, 1)
    directory = RUN / "stages" / f"train-{cell_name(seed, objective, variant)}"
    path = directory / "checkpoint.pt"
    meta = read(directory / "checkpoint-meta.json")
    require(
        sha(path) == meta["sha256"] and path.stat().st_size == meta["bytes"], "checkpoint bytes"
    )
    saved = torch.load(path, weights_only=True, map_location="cpu")
    require(
        saved["format"] == FORMAT and saved["registration"] == sha(RUN / "registration.json"),
        "checkpoint format/identity",
    )
    require(
        saved["variant"] == variant and saved["seed"] == seed and saved["objective"] == objective,
        "checkpoint cell",
    )
    require(
        saved["next_step"] == 512 and saved["presentations"] == 2048 and saved["config"] == CONFIG,
        "checkpoint progress",
    )
    require(
        saved["tokenizer"] == read(RUN / "registration.json")["tokenizer"], "checkpoint tokenizer"
    )
    require(all(torch.isfinite(t).all() for t in saved["model"].values()), "nonfinite checkpoint")
    model = make_model(variant)
    model.load_state_dict(saved["model"], strict=True)
    model.eval()
    return model


def generate(directory, model, split):
    from toruk_lm.owned_lm import OwnedSession
    from toruk_lm.tokenizer import ByteTokenizer

    path = RUN / f"{split}-inputs.json"
    require(sha(path) == read(RUN / "registration.json")["data"][path.name], "prefix identity")
    cases = read(path)
    first = None
    with (directory / "predictions.jsonl").open("x", encoding="utf-8") as stream:
        for index, case in enumerate([*cases, cases[0]]):
            wall, cpu = time.perf_counter(), time.process_time()
            result = OwnedSession(model).generate(case["prefix"], budget=8)
            cost = dict(cpu=time.process_time() - cpu, wall=time.perf_counter() - wall)
            require(max(cost.values()) <= 2, "request cap")
            require(index != len(cases) or result == first, "replay mismatch")
            if index == 0:
                first = result
            stream.write(
                json.dumps(
                    dict(
                        id=case["id"],
                        prefix=case["prefix"],
                        input_ids=[1, *ByteTokenizer().encode(case["prefix"])],
                        replay=index == len(cases),
                        result=result,
                        cost=cost,
                    )
                )
                + "\n"
            )
            stream.flush()
    save(
        directory / "generation-seal.json",
        dict(sha256=sha(directory / "predictions.jsonl"), requests=len(cases) + 1),
    )


def evaluate(directory, model, seed, objective, variant, split):
    import torch

    name = cell_name(seed, objective, variant)
    generated = RUN / "stages" / f"generate-{split}-{name}"
    require(
        sha(generated / "predictions.jsonl") == read(generated / "generation-seal.json")["sha256"],
        "generation changed",
    )
    predictions = rows(generated / "predictions.jsonl")[:-1]
    label_path = RUN / f"{split}-labels.json"
    require(
        sha(label_path) == read(RUN / "registration.json")["data"][label_path.name],
        "label identity",
    )
    labels = read(label_path)
    totals = Counter()
    by_category = Counter()
    with (directory / "losses.jsonl").open("x", encoding="utf-8") as stream, torch.no_grad():
        for prediction, label in zip(predictions, labels, strict=True):
            require(prediction["id"] == label["id"], "label order")
            wall, cpu = time.perf_counter(), time.process_time()
            doc = dict(prefix=prediction["prefix"], text=prediction["prefix"] + label["gold"])
            x, y, mask = make_batch([doc])
            _, _, stats = loss_parts(forward_batch(model, x), y, mask, 1)
            for key in ("token_ce", "token_weighted_loss", "token_logit_gradient_l2"):
                del stats[key]
            ids = prediction["result"]["generated_ids"]
            output = classify(ids)
            correct = score(ids, label["gold"])
            cost = dict(cpu=time.process_time() - cpu, wall=time.perf_counter() - wall)
            require(max(cost.values()) <= 2, "loss document cap")
            record = dict(
                id=label["id"],
                gold=label["gold"],
                category=label["category"],
                correct=correct,
                **output,
                **stats,
                cost=cost,
            )
            stream.write(json.dumps(record) + "\n")
            stream.flush()
            for key in ("history_targets", "answer_targets", "history_loss_sum", "answer_loss_sum"):
                totals[key] += stats[key]
            for key, value in dict(exact=correct, **output).items():
                totals[key] += int(value)
            by_category[label["category"]] += int(correct)
    save(
        directory / "metrics.json",
        dict(
            count=len(labels),
            **totals,
            categories=dict(by_category),
            full_nll=(totals["history_loss_sum"] + totals["answer_loss_sum"])
            / (totals["history_targets"] + totals["answer_targets"]),
            history_nll=totals["history_loss_sum"] / totals["history_targets"],
            answer_nll=totals["answer_loss_sum"] / totals["answer_targets"],
        ),
    )


def stage_worker(directory, stage, seed, objective, variant, split):
    setup_wall = 0.0
    try:
        if stage == "contracts":
            return subprocess.call(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-q",
                    "tests/test_answer_trainability_dev.py",
                    "-o",
                    f"cache_dir={directory / 'pytest-cache'}",
                    "--basetemp",
                    str(directory / "pytest-tmp"),
                ],
                cwd=ROOT,
            )
        if stage == "freeze":
            freeze(ROOT / "artifacts/answer-trainability-dev-v1-preflight-001/cost.json")
            return 0
        verify(full_data=False)
        if stage == "train":
            setup_wall = train(directory, seed, objective, variant)
        else:
            model = load_model(seed, objective, variant)
            setup_wall = time.perf_counter() - STARTED
            if stage == "generate":
                generate(directory, model, split)
            elif stage == "loss":
                evaluate(directory, model, seed, objective, variant, split)
            else:
                raise ValueError("unknown worker stage")
        return 0
    finally:
        worker_receipt(directory, STARTED, setup_wall)


def dev_pass(metrics):
    return (
        metrics["exact"] >= 12
        and metrics["eos"] == 16
        and metrics["malformed"] == 0
        and all(
            metrics["categories"][key] >= value
            for key, value in dict(city=6, code=3, unknown=3).items()
        )
    )


def run():
    reg = verify()
    save(
        RUN / "run-start.json",
        dict(registration_sha256=sha(RUN / "registration.json"), order=ORDER),
    )
    began, cpu_before = time.perf_counter(), time.process_time()
    costs, metrics = {}, {}

    def stage(kind, seed, objective, variant, split="train"):
        name = cell_name(seed, objective, variant)
        tag = f"train-{name}" if kind == "train" else f"{kind}-{split}-{name}"
        command = [
            sys.executable,
            "-B",
            str(ROOT / "scripts/answer_trainability_dev.py"),
            "worker",
            "--stage",
            kind,
            "--seed",
            str(seed),
            "--objective",
            objective,
            "--variant",
            variant,
            "--split",
            split,
            "--directory",
            str(RUN / "stages" / tag),
        ]
        own_cpu = time.process_time() - cpu_before
        own_wall = time.perf_counter() - began - sum(c["wall"] for c in costs.values())
        require(max(own_cpu, own_wall) <= 60, "controller overhead cap")
        result = watch(
            command,
            RUN / "stages" / tag,
            RUN,
            reg["caps"]["fit" if kind == "train" else kind],
            reg["caps"]["memory"],
            reg["caps"]["disk"],
        )
        costs[tag] = result
        require(result["status"] == "PASS", f"stage failed: {tag}; preserve evidence, no retry")
        print(
            json.dumps(
                dict(stage=tag, cpu=result["cpu"], wall=result["wall"], status=result["status"])
            ),
            flush=True,
        )
        return RUN / "stages" / tag

    try:
        for seed, objective, variant in ORDER:
            stage("train", seed, objective, variant)
            stage("generate", seed, objective, variant)
            directory = stage("loss", seed, objective, variant)
            metrics[f"train-{cell_name(seed, objective, variant)}"] = read(
                directory / "metrics.json"
            )
        eligible = {
            objective: all(
                metrics[f"train-{cell_name(seed, objective, variant)}"]["exact"] == 8
                for seed in (419, 733)
                for variant in PARAMETERS
            )
            for objective in WEIGHTS
        }
        save(
            RUN / "training-gate.json",
            dict(
                eligible=eligible,
                metrics=metrics,
                decision="DEVELOPMENT_ALLOWED_FOR_PASSING_OBJECTIVES"
                if any(eligible.values())
                else "STOP_TINY_OVERFIT_FAILED",
            ),
        )
        for seed, objective, variant in ORDER:
            if eligible[objective]:
                stage("generate", seed, objective, variant, "dev")
                directory = stage("loss", seed, objective, variant, "dev")
                metrics[f"dev-{cell_name(seed, objective, variant)}"] = read(
                    directory / "metrics.json"
                )
        passed = {
            objective: eligible[objective]
            and all(
                dev_pass(metrics[f"dev-{cell_name(seed, objective, variant)}"])
                for seed in (419, 733)
                for variant in PARAMETERS
            )
            for objective in WEIGHTS
        }
        decision = (
            "COMPLETE_ANSWERS_DEMONSTRATED"
            if any(passed.values())
            else (
                "STOP_GENERALIZATION_FAILURE"
                if any(eligible.values())
                else "STOP_TINY_OVERFIT_FAILED"
            )
        )
        save(
            RUN / "summary.json",
            dict(
                registration_sha256=sha(RUN / "registration.json"),
                eligible=eligible,
                development_pass=passed,
                decision=decision,
                metrics=metrics,
                stages=costs,
                controller_cpu=time.process_time() - cpu_before,
                controller_wall_excluding_stages=time.perf_counter()
                - began
                - sum(c["wall"] for c in costs.values()),
            ),
        )
        print(
            json.dumps(dict(decision=decision, eligible=eligible, development_pass=passed)),
            flush=True,
        )
    except BaseException as error:
        save(
            RUN / "failure.json",
            dict(error=repr(error), completed=list(costs), partial_metrics=metrics),
        )
        raise


def audit():
    verify()
    summary = read(RUN / "summary.json")
    reference, initial = {}, {}
    for seed, objective, variant in ORDER:
        name = cell_name(seed, objective, variant)
        directory = RUN / "stages" / f"train-{name}"
        trace = rows(directory / "training.jsonl")
        require(len(trace) == 512 and [r["step"] for r in trace] == list(range(1, 513)), "steps")
        signature = [(r["ids"], r["history_targets"], r["answer_targets"]) for r in trace]
        require(signature == reference.setdefault(seed, signature), "exposure differs")
        stats = read(directory / "training-summary.json")
        key = (seed, variant)
        require(
            stats["initial_sha256"] == initial.setdefault(key, stats["initial_sha256"]),
            "initialization differs",
        )
        for row in trace:
            w = WEIGHTS[objective]
            require(
                row["denominator"] == row["history_targets"] + w * row["answer_targets"],
                "weighted count",
            )
            require(
                math.isclose(
                    row["combined_gradient_l2"] ** 2,
                    row["history_gradient_l2"] ** 2
                    + row["answer_gradient_l2"] ** 2
                    + 2 * row["gradient_dot"],
                    rel_tol=1e-5,
                    abs_tol=1e-10,
                ),
                "gradient decomposition",
            )
            require(
                math.isclose(
                    sum(map(sum, row["token_weighted_loss"])),
                    row["history_contribution"] + row["answer_contribution"],
                    rel_tol=1e-5,
                ),
                "loss decomposition",
            )
            require(
                math.isclose(
                    row["clip_input_norm"], row["combined_gradient_l2"], rel_tol=1e-5, abs_tol=1e-7
                ),
                "update gradient norm",
            )
        for split in ("train", "dev"):
            tag = f"{split}-{name}"
            if tag not in summary["metrics"]:
                require(
                    split == "dev" and not summary["eligible"][objective],
                    "missing permitted evaluation",
                )
                require(
                    not (RUN / "stages" / f"generate-dev-{name}").exists(),
                    "failed objective evaluated",
                )
                continue
            path = RUN / "stages" / f"generate-{split}-{name}" / "predictions.jsonl"
            predictions = rows(path)
            require(sha(path) == read(path.parent / "generation-seal.json")["sha256"], "raw seal")
            require(
                predictions[0]["result"] == predictions[-1]["result"] and predictions[-1]["replay"],
                "replay",
            )
            labels = read(RUN / f"{split}-labels.json")
            exact = sum(
                score(p["result"]["generated_ids"], label["gold"])
                for p, label in zip(predictions[:-1], labels, strict=True)
            )
            require(exact == summary["metrics"][tag]["exact"], "score mismatch")
        load_model(seed, objective, variant)
    return dict(
        status="PASS",
        registration_sha256=sha(RUN / "registration.json"),
        cells=8,
        decision=summary["decision"],
        training_or_generation_executed=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("worker", "run", "audit"))
    parser.add_argument("--stage", choices=("contracts", "freeze", "train", "generate", "loss"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--seed", type=int, choices=(419, 733), default=419)
    parser.add_argument("--objective", choices=WEIGHTS, default="uniform")
    parser.add_argument("--variant", choices=PARAMETERS, default="ordinary")
    parser.add_argument("--split", choices=("train", "dev"), default="train")
    args = parser.parse_args()
    if args.command == "run":
        run()
    elif args.command == "audit":
        print(json.dumps(audit(), sort_keys=True))
    else:
        require(
            args.directory is not None and args.directory.resolve().is_relative_to(ROOT),
            "workspace output required",
        )
        return stage_worker(
            args.directory, args.stage, args.seed, args.objective, args.variant, args.split
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
