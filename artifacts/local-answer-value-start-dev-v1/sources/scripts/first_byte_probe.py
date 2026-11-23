"""Single-use first-token measurement; no training, generated answer or token feedback."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import pickle
import random
import subprocess
import sys
import time
from pathlib import Path

from lifetime_job import controller_record, watch

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-first-byte-probe-v1"
ORIGINAL = ROOT / "artifacts/local-answer-dev-v1"
ORIGINAL_SHA = "c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4"
CELLS = ("601-ordinary", "601-recurrent", "947-recurrent", "947-ordinary")
PROTOCOL = "docs/research/local-answer-first-byte-probe-v1-protocol.md"
SOURCES = [
    PROTOCOL,
    "scripts/first_byte_probe.py",
    "tests/test_first_byte_probe.py",
    "scripts/lifetime_job.py",
    "scripts/local_answer_dev.py",
    "scripts/answer_trainability_dev.py",
    "scripts/segment_delta_watch.py",
    "src/toruk_lm/model.py",
    "src/toruk_lm/recurrent.py",
    "src/toruk_lm/owned_lm.py",
    "src/toruk_lm/tokenizer.py",
    "src/toruk_lm/engine.py",
    "src/toruk_lm/data.py",
    ".gitattributes",
    "pyproject.toml",
]


class ProbeStop(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProbeStop(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def append(stream, value):
    stream.write(json.dumps(value, allow_nan=False) + "\n")
    stream.flush()


def runtime():
    import platform

    return dict(
        python=platform.python_version(),
        platform=platform.platform(),
        torch=importlib.metadata.version("torch"),
        psutil=importlib.metadata.version("psutil"),
    )


def inputs_from_saved():
    require(sha(ORIGINAL / "registration.json") == ORIGINAL_SHA, "original registration")
    old = read(ORIGINAL / "registration.json")
    for name in ("train-inputs.json", "train-labels.json", "train-documents.json"):
        require(sha(ORIGINAL / name) == old["data"][name], "original training data")
    inputs = read(ORIGINAL / "train-inputs.json")
    labels = read(ORIGINAL / "train-labels.json")
    docs = {d["id"]: d for d in read(ORIGINAL / "train-documents.json")}
    selected = []
    gold = []
    originals = {}
    checkpoints = {}
    for case, label in zip(inputs, labels, strict=True):
        require(case["id"] == label["id"], "original label order")
        if label["category"] != "city":
            continue
        prefix = case["prefix"]
        start = len(prefix.encode())
        identity = case["id"]
        ids = [1, *(b + 3 for b in prefix.encode())]
        target = [*(b + 3 for b in label["gold"].encode()), 2]
        full = [1, *(b + 3 for b in docs[identity]["text"].encode()), 2]
        require(start == 53 and len(ids) == 54 and ids[-2:] == [66, 64], "prefix boundary")
        require(
            docs[identity]["prefix"] == prefix and full[:54] == ids, "saved document construction"
        )
        require(
            docs[identity]["text"] == prefix + label["gold"]
            and docs[identity]["gold"] == label["gold"]
            and full[54:] == target,
            "saved gold byte/token identity",
        )
        selected.append(
            dict(
                id=identity,
                prefix=prefix,
                input_ids=ids,
                target_y=53,
                local_logit=21,
                delimiter_ids=[66, 64],
            )
        )
        gold.append(
            dict(
                id=identity,
                gold=label["gold"],
                expected_first_byte=label["gold"].encode()[0],
                expected_first_id=target[0],
                full_document_ids=full,
                text=docs[identity]["text"],
                mask_positions=[53, 54, 55],
                answer_target_ids=target,
                template=label["template"],
                canonical=label["canonical"],
            )
        )
    require(len(selected) == len(gold) == 32, "city case count")
    wanted = {c["id"]: c for c in selected}
    for cell in CELLS:
        path = ORIGINAL / "stages" / f"generate-train-{cell}" / "predictions.jsonl"
        require(
            sha(path) == read(path.parent / "seal.json")["sha256"], "original predictions changed"
        )
        predictions = {p["id"]: p for p in rows(path) if not p["replay"]}
        originals[cell] = {}
        for identity, case in wanted.items():
            p = predictions[identity]
            require(
                p["prefix"] == case["prefix"] and p["input_ids"] == case["input_ids"],
                "original native prefix",
            )
            originals[cell][identity] = p["result"]["generated_ids"][0]
        checkpoint = ORIGINAL / "stages" / f"train-{cell}" / "checkpoint.pt"
        meta = read(checkpoint.parent / "checkpoint-meta.json")
        require(
            sha(checkpoint) == meta["sha256"] and checkpoint.stat().st_size == meta["bytes"],
            "checkpoint bytes",
        )
        checkpoints[cell] = dict(path=checkpoint.relative_to(ROOT).as_posix(), **meta)
    plan = []
    for phase in ("prefix", "teacher"):
        for cell in CELLS:
            cases = [*selected, selected[0]] if phase == "prefix" else selected
            for index, case in enumerate(cases):
                plan.append(
                    dict(
                        record_id=f"{phase}-{cell}-{index:03d}",
                        phase=phase,
                        cell=cell,
                        id=case["id"],
                        replay=phase == "prefix" and index == 32,
                        index=index,
                    )
                )
    require(len(plan) == 260, "record plan")
    return selected, gold, originals, checkpoints, plan


def measurement(logits, expected):
    require(len(logits) == 259 and all(math.isfinite(v) for v in logits), "STOP_NONFINITE")
    ordered = sorted(range(2, 259), key=lambda i: (-logits[i], i))
    predicted, runner = ordered[:2]
    full_max = max(logits)
    eligible_max = logits[predicted]
    full_z = sum(math.exp(v - full_max) for v in logits)
    eligible_z = sum(math.exp(logits[i] - eligible_max) for i in range(2, 259))
    margin = logits[predicted] - logits[expected]
    return dict(
        expected_first_id=expected,
        predicted_first_id=predicted,
        expected_rank=ordered.index(expected) + 1,
        expected_logit=logits[expected],
        predicted_logit=logits[predicted],
        expected_minus_predicted_margin=-margin,
        predicted_minus_expected_margin=margin,
        expected_probability_full=math.exp(logits[expected] - full_max) / full_z,
        predicted_probability_full=math.exp(logits[predicted] - full_max) / full_z,
        expected_probability_eligible=math.exp(logits[expected] - eligible_max) / eligible_z,
        predicted_probability_eligible=1 / eligible_z,
        winner_minus_runner_up=logits[predicted] - logits[runner],
        tied_winners=sum(logits[i] == logits[predicted] for i in range(2, 259)),
        near_tied_gold=expected != predicted and margin <= 1e-4,
        near_tied_decision=logits[predicted] - logits[runner] <= 1e-4,
    )


def freeze(contracts):
    require(contracts["status"] == "PASS" and contracts["complete_process_lifetimes"], "contracts")
    prefixes, gold, originals, checkpoints, plan = inputs_from_saved()
    data = {
        "prefix-inputs.json": prefixes,
        "gold-evaluator.json": gold,
        "original-first-ids.json": originals,
        "plan.json": plan,
    }
    for name, value in data.items():
        save(RUN / name, value)
    sources = {}
    for name in SOURCES:
        target = RUN / "sources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
        sources[name] = sha(target)
    evidence_names = [
        "registration.json",
        "train-inputs.json",
        "train-labels.json",
        "train-documents.json",
        "summary.json",
        "training-gate.json",
    ]
    for cell in CELLS:
        evidence_names.extend(
            (
                f"stages/generate-train-{cell}/predictions.jsonl",
                f"stages/generate-train-{cell}/seal.json",
                f"stages/train-{cell}/checkpoint-meta.json",
            )
        )
    save(
        RUN / "registration.json",
        dict(
            version="toruk-local-answer-first-byte-probe-v1",
            sources=sources,
            data={n: sha(RUN / n) for n in data},
            checkpoints=checkpoints,
            runtime=runtime(),
            order=list(CELLS),
            original_registration=ORIGINAL_SHA,
            original_evidence={name: sha(ORIGINAL / name) for name in evidence_names},
            original_config=read(ORIGINAL / "registration.json")["config"],
            parameters=read(ORIGINAL / "registration.json")["parameters"],
            tokenizer=read(ORIGINAL / "registration.json")["tokenizer"],
            protocol=PROTOCOL,
            contracts_sha256=sha(RUN / "contracts/cost.json"),
            records=260,
            prefix_records=132,
            teacher_records=128,
            caps=dict(
                worker=20,
                request=2,
                preparation_controller=40,
                overall=200,
                memory=2 * 1024**3,
                disk=128 * 1024**2,
            ),
            parity_max_abs=1e-5,
            near_tie=1e-4,
            seed_configs=list(CELLS),
            base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            status="FROZEN_BEFORE_ANY_FORWARD",
        ),
    )
    print(
        json.dumps(dict(registration_sha256=sha(RUN / "registration.json"), records=260)),
        flush=True,
    )


def verify(data=False):
    require((RUN / "registration.json").is_file(), "registration required before model loading")
    reg = read(RUN / "registration.json")
    if (RUN / "run-start.json").exists():
        require(
            read(RUN / "run-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
            "registration seal changed",
        )
    require(reg["runtime"] == runtime(), "runtime mismatch")
    for name, expected in reg["sources"].items():
        require(
            sha(ROOT / name) == sha(RUN / "sources" / name) == expected, "source changed: " + name
        )
    for meta in reg["checkpoints"].values():
        require(sha(ROOT / meta["path"]) == meta["sha256"], "checkpoint changed")
    if data:
        for name, expected in reg["data"].items():
            require(sha(RUN / name) == expected, "frozen data changed")
    return reg


def checked_data(name):
    reg = read(RUN / "registration.json")
    require(sha(RUN / name) == reg["data"][name], "frozen data mismatch: " + name)
    return read(RUN / name)


def load_saved(cell):
    reg = verify()
    require((RUN / "run-start.json").is_file(), "run marker required before model loading")
    import torch
    from local_answer_dev import load

    from toruk_lm.tokenizer import ByteTokenizer

    seed, variant = cell.split("-")
    model = load(int(seed), variant)
    require(not model.training, "eval mode required")
    require(
        all(p.dtype == torch.float32 and p.device.type == "cpu" for p in model.parameters())
        and torch.get_num_threads() == 1
        and torch.are_deterministic_algorithms_enabled(),
        "frozen dtype/device/runtime settings",
    )
    require(
        sum(p.numel() for p in model.parameters()) == reg["parameters"][variant], "model budget"
    )
    require(ByteTokenizer.fingerprint == reg["tokenizer"]["fingerprint"], "tokenizer identity")
    return model


def invariants(model):
    import torch

    weights = hashlib.sha256()
    for name, tensor in model.state_dict().items():
        weights.update(name.encode())
        weights.update(tensor.detach().numpy().tobytes())
    rng = hashlib.sha256(
        torch.get_rng_state().numpy().tobytes() + pickle.dumps(random.getstate())
    ).hexdigest()
    return dict(
        model_sha256=weights.hexdigest(),
        rng_sha256=rng,
        gradient_fields_none=all(p.grad is None for p in model.parameters()),
    )


def vector_record(stream, record, tensor, **extra):
    values = tensor.detach().tolist()
    bad = [i for i, v in enumerate(values) if not math.isfinite(v)]
    encoded = [v if math.isfinite(v) else v.hex() for v in values]
    row = dict(**record, logits=encoded, suppressed_ids=[0, 1], nonfinite_indices=bad, **extra)
    append(stream, row)  # Preserve the vector before selection or rejection.
    require(not bad, "STOP_NONFINITE")
    return row


def prefix_worker(directory, cell, model):
    import torch

    from toruk_lm.owned_lm import OwnedSession

    cases = checked_data("prefix-inputs.json")
    originals = checked_data("original-first-ids.json")[cell]
    first = None
    with (
        (directory / "vectors.jsonl").open("x", encoding="utf-8") as vectors,
        (directory / "selection.jsonl").open("x", encoding="utf-8") as selections,
        (directory / "request-costs.jsonl").open("x", encoding="utf-8") as costs,
    ):
        with torch.no_grad():
            for index, case in enumerate([*cases, cases[0]]):
                began, cpu = time.perf_counter(), time.process_time()
                ids = [1, *(b + 3 for b in case["prefix"].encode())]
                require(ids == case["input_ids"] and ids[-2:] == [66, 64], "native prefix mismatch")
                session = OwnedSession(model)
                logits = session.consume(ids)
                row = vector_record(
                    vectors,
                    dict(
                        record_id=f"prefix-{cell}-{index:03d}",
                        cell=cell,
                        phase="prefix",
                        id=case["id"],
                        replay=index == 32,
                        input_ids=ids,
                        target_y=53,
                        local_logit=21,
                    ),
                    logits,
                )
                scores = logits.clone()
                scores[:2] = -torch.inf
                predicted = int(scores.argmax())
                append(
                    selections,
                    dict(
                        record_id=row["record_id"],
                        predicted_first_id=predicted,
                        original_first_id=originals[case["id"]],
                    ),
                )
                require(predicted == originals[case["id"]], "STOP_REPRODUCTION_FAILURE")
                value = (row["input_ids"], row["logits"], predicted)
                if index == 0:
                    first = value
                if index == 32:
                    require(value == first, "STOP_REPLAY_FAILURE")
                cost = dict(
                    record_id=row["record_id"],
                    cpu=time.process_time() - cpu,
                    wall=time.perf_counter() - began,
                )
                append(costs, cost)
                require(max(cost["cpu"], cost["wall"]) <= 2, "request cap")
    save(
        directory / "seal.json",
        dict(
            vectors=sha(directory / "vectors.jsonl"),
            selection=sha(directory / "selection.jsonl"),
            records=33,
        ),
    )


def teacher_worker(directory, cell, model):
    import torch
    from answer_trainability_dev import forward_batch, make_batch
    from torch.nn import functional as F

    seal = read(RUN / "prefix-phase-seal.json")
    for name, digest in seal["files"].items():
        require(sha(RUN / name) == digest, "prefix phase changed")
    prefixes = checked_data("prefix-inputs.json")
    labels = checked_data("gold-evaluator.json")
    raw = rows(RUN / "stages" / f"prefix-{cell}" / "vectors.jsonl")[:32]
    with (
        (directory / "vectors.jsonl").open("x", encoding="utf-8") as vectors,
        (directory / "request-costs.jsonl").open("x", encoding="utf-8") as costs,
    ):
        with torch.no_grad():
            for index, (case, label, prefix_vector) in enumerate(
                zip(prefixes, labels, raw, strict=True)
            ):
                began, cpu = time.perf_counter(), time.process_time()
                require(case["id"] == label["id"] == prefix_vector["id"], "teacher case order")
                x, y, mask = make_batch([dict(prefix=case["prefix"], text=label["text"])])
                require(
                    x[0].tolist() == label["full_document_ids"][:-1]
                    and y[0].tolist() == label["full_document_ids"][1:],
                    "native document targets",
                )
                positions = mask[0].nonzero().flatten().tolist()
                require(
                    positions == label["mask_positions"] == [53, 54, 55], "target mask mismatch"
                )
                require(
                    y[0, mask[0]].tolist() == label["answer_target_ids"]
                    and x[0, :54].tolist() == case["input_ids"],
                    "target IDs/prefix mismatch",
                )
                all_logits = forward_batch(model, x)
                ce = F.cross_entropy(
                    all_logits.transpose(1, 2), y, ignore_index=-100, reduction="none"
                )[0, mask[0]].tolist()
                first_logits = all_logits[0, 53]
                row = vector_record(
                    vectors,
                    dict(
                        record_id=f"teacher-{cell}-{index:03d}",
                        cell=cell,
                        phase="teacher",
                        id=case["id"],
                        replay=False,
                        input_ids=x[0].tolist(),
                        prefix_input_ids=case["input_ids"],
                        target_y=53,
                        local_logit=21,
                        mask_positions=positions,
                        answer_target_ids=label["answer_target_ids"],
                    ),
                    first_logits,
                    answer_ce=[v if math.isfinite(v) else v.hex() for v in ce],
                )
                require(all(math.isfinite(v) for v in ce), "STOP_NONFINITE_CE")
                predicted = max(range(2, 259), key=lambda i: (row["logits"][i], -i))
                prefix_predicted = max(
                    range(2, 259), key=lambda i: (prefix_vector["logits"][i], -i)
                )
                difference = max(
                    abs(a - b) for a, b in zip(row["logits"], prefix_vector["logits"], strict=True)
                )
                require(
                    difference <= 1e-5 and predicted == prefix_predicted,
                    "STOP_NUMERICAL_PARITY_FAILURE",
                )
                cost = dict(
                    record_id=row["record_id"],
                    cpu=time.process_time() - cpu,
                    wall=time.perf_counter() - began,
                )
                append(costs, cost)
                require(max(cost["cpu"], cost["wall"]) <= 2, "request cap")
    save(directory / "seal.json", dict(vectors=sha(directory / "vectors.jsonl"), records=32))


def worker(directory, phase, cell):
    with controller_record(directory):
        model = load_saved(cell)
        before = invariants(model)
        try:
            if phase == "prefix":
                prefix_worker(directory, cell, model)
            else:
                teacher_worker(directory, cell, model)
        finally:
            after = invariants(model)
            save(
                directory / "invariants.json",
                dict(before=before, after=after, unchanged=before == after),
            )
            require(before == after, "STOP_MODEL_OR_RNG_MUTATION")


def annotate():
    labels = {c["id"]: c for c in checked_data("gold-evaluator.json")}
    output = []
    comparisons = []
    with (RUN / "measurements.jsonl").open("x", encoding="utf-8") as stream:
        for phase in ("prefix", "teacher"):
            for cell in CELLS:
                for row in rows(RUN / "stages" / f"{phase}-{cell}" / "vectors.jsonl"):
                    metrics = measurement(row["logits"], labels[row["id"]]["expected_first_id"])
                    value = dict(
                        record_id=row["record_id"],
                        phase=phase,
                        cell=cell,
                        id=row["id"],
                        replay=row["replay"],
                        expected_first_byte=labels[row["id"]]["expected_first_byte"],
                        **metrics,
                    )
                    append(stream, value)
                    output.append(value)
    for cell in CELLS:
        p = rows(RUN / "stages" / f"prefix-{cell}" / "vectors.jsonl")[:32]
        t = rows(RUN / "stages" / f"teacher-{cell}" / "vectors.jsonl")
        for prefix, teacher in zip(p, t, strict=True):
            difference = max(
                abs(a - b) for a, b in zip(prefix["logits"], teacher["logits"], strict=True)
            )
            comparisons.append(
                dict(
                    cell=cell,
                    id=prefix["id"],
                    max_abs_difference=difference,
                    pass_parity=difference <= 1e-5,
                )
            )
    save(RUN / "parity.json", comparisons)
    require(len(output) == 260 and len(comparisons) == 128, "record count")
    cell_metrics = {}
    for cell in CELLS:
        main = [
            r for r in output if r["phase"] == "prefix" and not r["replay"] and r["cell"] == cell
        ]
        wrong = [r for r in main if r["expected_first_id"] != r["predicted_first_id"]]
        cell_metrics[cell] = dict(
            records=len(main),
            first_token_matches=sum(
                r["expected_first_id"] == r["predicted_first_id"] for r in main
            ),
            wrong=len(wrong),
            wrong_expected_ranks=[r["expected_rank"] for r in wrong],
            wrong_margins=[r["predicted_minus_expected_margin"] for r in wrong],
            near_tied_gold=sum(r["near_tied_gold"] for r in wrong),
            near_tied_decisions=sum(r["near_tied_decision"] for r in main),
        )
    return dict(
        records=260,
        prefix_records=132,
        teacher_records=128,
        parity_records=128,
        max_parity_difference=max(c["max_abs_difference"] for c in comparisons),
        cells=cell_metrics,
        measurements_sha256=sha(RUN / "measurements.jsonl"),
        decision="REPRODUCIBLE_FIRST_TOKEN_MARGINS_WITH_PARITY",
    )


def run():
    save(
        RUN / "bootstrap-start.json",
        dict(
            base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            date="2026-11-21",
        ),
    )
    began, cpu = time.perf_counter(), time.process_time()
    worker_costs = {}
    contracts = None

    def overhead():
        own_wall = time.perf_counter() - began - sum(c["wall"] for c in worker_costs.values())
        own_cpu = time.process_time() - cpu + (contracts["cpu"] if contracts else 0)
        require(max(own_wall, own_cpu) <= 40, "preparation/controller cap")

    try:
        command = [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "tests/test_first_byte_probe.py",
            "-o",
            f"cache_dir={RUN / 'pytest-cache'}",
            "--basetemp",
            str(RUN / "pytest-tmp"),
        ]
        contracts = watch(command, RUN / "contracts", RUN, 20)
        require(
            contracts["status"] == "PASS" and contracts["complete_process_lifetimes"],
            "zero-forward contracts failed",
        )
        freeze(contracts)
        overhead()
        verify(data=True)
        save(
            RUN / "run-start.json",
            dict(registration_sha256=sha(RUN / "registration.json"), records=260),
        )
        for phase in ("prefix", "teacher"):
            for cell in CELLS:
                overhead()
                directory = RUN / "stages" / f"{phase}-{cell}"
                command = [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts/first_byte_probe.py"),
                    "worker",
                    "--directory",
                    str(directory),
                    "--phase",
                    phase,
                    "--cell",
                    cell,
                ]
                cost = watch(command, directory, RUN, 20)
                worker_costs[f"{phase}-{cell}"] = cost
                require(
                    cost["status"] == "PASS" and cost["complete_process_lifetimes"],
                    f"worker STOP: {phase}-{cell}",
                )
                print(
                    json.dumps(
                        dict(
                            stage=f"{phase}-{cell}",
                            cpu=cost["cpu"],
                            wall=cost["wall"],
                            status=cost["status"],
                        )
                    ),
                    flush=True,
                )
            if phase == "prefix":
                files = {}
                for cell in CELLS:
                    directory = RUN / "stages" / f"prefix-{cell}"
                    require(len(rows(directory / "vectors.jsonl")) == 33, "prefix count")
                    for name in ("vectors.jsonl", "selection.jsonl", "seal.json"):
                        path = directory / name
                        files[path.relative_to(RUN).as_posix()] = sha(path)
                save(RUN / "prefix-phase-seal.json", dict(files=files, records=132))
        result = annotate()
        overhead()
        result.update(
            registration_sha256=sha(RUN / "registration.json"),
            stages=worker_costs,
            preparation_controller_cpu_to_receipt=time.process_time() - cpu + contracts["cpu"],
            preparation_controller_wall=time.perf_counter()
            - began
            - sum(c["wall"] for c in worker_costs.values()),
            training_updates=0,
            generated_answers=0,
        )
        save(RUN / "summary.json", result)
        print(
            json.dumps({k: result[k] for k in ("decision", "records", "max_parity_difference")}),
            flush=True,
        )
    except BaseException as error:
        save(
            RUN / "failure.json",
            dict(
                error=repr(error),
                stages=worker_costs,
                registration_sha256=sha(RUN / "registration.json")
                if (RUN / "registration.json").exists()
                else None,
            ),
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "worker"))
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--phase", choices=("prefix", "teacher"))
    parser.add_argument("--cell", choices=CELLS)
    args = parser.parse_args()
    if args.command == "run":
        with controller_record(RUN / "execution"):
            run()
    else:
        require(
            args.directory and args.directory.resolve().is_relative_to(ROOT), "workspace output"
        )
        worker(args.directory, args.phase, args.cell)


if __name__ == "__main__":
    main()
