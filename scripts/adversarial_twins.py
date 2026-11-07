"""Challenge answer-prior explanations with frozen models and counterfactual twins."""

import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil
import torch
from copy_gap_probe import read, require, sha
from validate_owned_reproduction import validate

from toruk_lm.copy_diagnostic import generate
from toruk_lm.engine import setup
from toruk_lm.owned_lm import OwnedSession
from toruk_lm.owned_training import load, memory_bytes, runtime_identity, write_json
from toruk_lm.tokenizer import ByteTokenizer

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/adversarial-twins-v1.json"


def cases(split, spec):
    rng = random.Random(spec["seed"])
    rows = []
    for kind in ("value", "exact", "unknown"):
        n = spec["unknown_worlds"] if kind == "unknown" else spec["worlds_per_kind"]
        for i in range(n):
            entity = rng.choice(("Ada", "Bo", "Cy", "Dee"))
            values = (
                rng.sample(("blue", "gold", "lime"), 2)
                if kind == "value"
                else ["".join(rng.choice("aKpQz0279-/_+!") for _ in range(6)) for _ in range(2)]
            )
            if kind == "unknown":
                values = ["?"]
            require(len(values) == len(set(values)), "duplicate counterfactual targets")
            filler = "".join(
                f"Note {rng.randrange(1000)}: {rng.choice(('rain', 'wind', 'sun'))}.\n"
                for _ in range(rng.randrange(4, 9))
            )
            for location in ("local", "distant"):
                for arm, value in enumerate(values):
                    evidence = (
                        f"{entity} visited the park.\n"
                        if kind == "unknown"
                        else f"{entity}'s tag is {value}.\n"
                    )
                    history = "If unknown answer ?.\n" + (
                        filler + evidence if location == "local" else evidence + filler
                    )
                    query = f"Answer {entity}'s tag? "
                    require(
                        len((history + query).encode()) + 17 <= 384, "case exceeds resource cap"
                    )
                    rows.append(
                        dict(
                            id=f"{split}-{kind}-{i}-{location}-{arm}",
                            world=f"{split}-{kind}-{i}",
                            kind=kind,
                            location=location,
                            arm=arm,
                            history=history,
                            query=query,
                            expected=value,
                            alternative=values[1 - arm] if len(values) == 2 else None,
                        )
                    )
    return rows


@torch.no_grad()
def preference(model, history, query, targets, gated):
    started, cpu = time.perf_counter(), time.process_time()
    session = OwnedSession(model)
    session.consume([1, *ByteTokenizer().encode(history)])
    session.read = not gated
    session.consume(ByteTokenizer().encode(query))
    prefix_work, prefix_commits = session.forward_positions, session.commits
    total_work, commits = prefix_work, prefix_commits
    scores = []
    for target in targets:
        clone = session.clone()
        logits = clone.last_logits
        ids = ByteTokenizer().encode(target)
        token_logps = []
        for i, token in enumerate(ids):
            scores_now = logits.clone()
            scores_now[:2] = -torch.inf
            token_logps.append(float(torch.log_softmax(scores_now, dim=-1)[token]))
            if i + 1 < len(ids):
                logits = clone.consume([token])
        total_work += clone.forward_positions - prefix_work
        commits += clone.commits - prefix_commits
        scores.append(dict(target=target, ids=ids, token_logps=token_logps, logp=sum(token_logps)))
    return dict(
        scores=scores,
        forward_positions=total_work,
        memory_commits=commits,
        seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu,
        scope="Offline conditional value-byte likelihood; no EOS score, no answer replacement",
    )


def verify(package):
    reg = read(package / "registration.json")
    for name, digest in reg["inputs"].items():
        require(sha(ROOT / name) == digest, f"frozen input changed: {name}")
    for phase, digest in reg["datasets"].items():
        require(sha(package / f"{phase}.json") == digest, f"dataset changed: {phase}")
    return reg


def freeze(package, parent):
    require(not package.exists(), "fresh package required")
    cfg = read(CONFIG)
    require(
        cfg["schema"] == "toruk-adversarial-twins-v1"
        and 0 < cfg["phase_seconds"] <= 240
        and 0 < cfg["heldout"]["worlds_per_kind"] <= 10
        and 0 < cfg["dev"]["worlds_per_kind"] <= 2
        and 0 < cfg["heldout"]["unknown_worlds"] <= 4
        and 0 < cfg["dev"]["unknown_worlds"] <= 2
        and cfg["max_new_tokens"] == 16
        and cfg["seeds"] == [31, 47]
        and cfg["methods"] == ["memory_on", "query_read_off", "ordinary", "ordinary_matched"]
        and cfg["sample_interval_seconds"] == 0.02,
        "unsupported protocol or unbounded config",
    )
    parent = parent.resolve()
    require(parent.is_relative_to(ROOT), "parent must be inside checkout")
    validation = validate(
        parent,
        ROOT / "configs/owned-lm-primary-v1.json",
        ROOT / "configs/owned-reproduction-v1.json",
        ROOT / "artifacts/owned-lm-v1-20261104/primary",
    )
    data = {p: cases(p, cfg[p]) for p in ("dev", "heldout")}
    require(
        not (
            {r["history"] + r["query"] for r in data["dev"]}
            & {r["history"] + r["query"] for r in data["heldout"]}
        ),
        "split prompt overlap",
    )
    require(
        not (
            {r["expected"] for r in data["dev"] if r["kind"] == "exact"}
            & {r["expected"] for r in data["heldout"] if r["kind"] == "exact"}
        ),
        "exact value overlap",
    )
    train_prefixes = {r["prefix"] for r in read(parent / "data/train.json")}
    require(
        not (train_prefixes & {r["history"] + r["query"] for rows in data.values() for r in rows}),
        "challenge prompt duplicates original training input",
    )
    files = [
        Path(__file__),
        CONFIG,
        ROOT / "scripts/copy_gap_probe.py",
        ROOT / "scripts/validate_owned_reproduction.py",
        ROOT / "src/toruk_lm/copy_diagnostic.py",
        ROOT / "configs/owned-lm-primary-v1.json",
        ROOT / "configs/owned-reproduction-v1.json",
        ROOT / "docs/research/adversarial-twins-v1-protocol.md",
    ]
    files += [ROOT / "src/toruk_lm" / name for name in runtime_identity()]
    models = {}
    for seed in cfg["seeds"]:
        for variant in ("memory_on", "ordinary", "ordinary_matched"):
            path = parent / "models" / f"{seed}-{variant}" / "checkpoint.pt"
            files.append(path)
            models[f"{seed}-{variant}"] = path.relative_to(ROOT).as_posix()
    package.mkdir(parents=True)
    for phase, rows in data.items():
        write_json(package / f"{phase}.json", rows)
    write_json(
        package / "registration.json",
        dict(
            config=cfg,
            models=models,
            parent_validation=validation,
            frozen_utc=datetime.now(UTC).isoformat(),
            inputs={p.relative_to(ROOT).as_posix(): sha(p) for p in files},
            datasets={p: sha(package / f"{p}.json") for p in data},
            tokenizer=ByteTokenizer.fingerprint,
            head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
            python=sys.version,
            torch=torch.__version__,
        ),
    )
    print(json.dumps(dict(frozen=True, cases={p: len(rows) for p, rows in data.items()})))


def worker(package, phase, method, seed):
    reg = verify(package)
    setup(0, 1)
    variant = "memory_on" if method == "query_read_off" else method
    checkpoint = ROOT / reg["models"][f"{seed}-{variant}"]
    model, _ = load(checkpoint)
    start = time.perf_counter()
    with (package / phase / f"{seed}-{method}.jsonl").open("x", encoding="utf-8") as stream:
        for case in read(package / f"{phase}.json"):
            g = generate(
                model, case["history"], case["query"], 16, query_read_off=method == "query_read_off"
            )
            answer = g["answer"].strip()
            score = (
                preference(
                    model,
                    case["history"],
                    case["query"],
                    [case["expected"], case["alternative"]],
                    method == "query_read_off",
                )
                if case["alternative"] is not None
                else None
            )
            stream.write(
                json.dumps(
                    dict(
                        case=case["id"],
                        world=case["world"],
                        kind=case["kind"],
                        location=case["location"],
                        arm=case["arm"],
                        method=method,
                        seed=seed,
                        expected=case["expected"],
                        correct=answer == case["expected"],
                        unknown_assertion=case["kind"] == "unknown" and answer not in ("?", ""),
                        generation=g,
                        preference=score,
                        checkpoint_sha256=reg["inputs"][
                            str(checkpoint.relative_to(ROOT)).replace("\\", "/")
                        ],
                    ),
                    allow_nan=False,
                )
                + "\n"
            )
            stream.flush()
    write_json(
        package / phase / f"{seed}-{method}-worker.json",
        dict(
            pid=os.getpid(),
            seconds=time.perf_counter() - start,
            lifetime_cpu_seconds=time.process_time(),
            memory=memory_bytes(),
        ),
    )


def phase_run(package, phase):
    reg = verify(package)
    cfg = reg["config"]
    require(
        phase != "heldout" or (package / "dev/complete.json").exists(),
        "development must finish first",
    )
    out = package / phase
    require(not out.exists(), "phase already started; no retries")
    out.mkdir()
    started = time.perf_counter()
    commands = []
    for i, seed in enumerate(cfg["seeds"]):
        order = cfg["methods"][i:] + cfg["methods"][:i]
        for method in order:
            cmd = [
                sys.executable,
                str(Path(__file__).resolve()),
                "worker",
                "--package",
                str(package.resolve()),
                "--phase",
                phase,
                "--method",
                method,
                "--seed",
                str(seed),
            ]
            peak = 0
            samples = 0
            child_cpu = {}
            clock = time.perf_counter()
            cpu = time.process_time()
            with (out / f"{seed}-{method}.log").open("w", encoding="utf-8") as log:
                child = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
                while child.poll() is None:
                    if time.perf_counter() - started > cfg["phase_seconds"]:
                        for descendant in psutil.Process(child.pid).children(recursive=True):
                            try:
                                descendant.kill()
                            except psutil.NoSuchProcess:
                                pass
                        child.kill()
                        child.wait()
                        raise TimeoutError("phase cap exhausted")
                    processes = [psutil.Process(os.getpid())]
                    processes += processes[0].children(recursive=True)
                    rss = 0
                    for process in processes:
                        try:
                            rss += process.memory_info().rss
                            if process.pid != os.getpid():
                                times = process.cpu_times()
                                child_cpu[process.pid] = max(
                                    child_cpu.get(process.pid, 0), times.user + times.system
                                )
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    peak = max(peak, rss)
                    samples += 1
                    time.sleep(cfg["sample_interval_seconds"])
            commands.append(
                dict(
                    command=cmd,
                    returncode=child.returncode,
                    wall_seconds=time.perf_counter() - clock,
                    controller_cpu_seconds=time.process_time() - cpu,
                    sampled_controller_and_children_peak_bytes=peak,
                    samples=samples,
                    sampled_child_cpu_seconds=child_cpu,
                    sample_scope="Controller and recursive children; check.py/IDE harness excluded",
                )
            )
            write_json(out / "commands.json", commands)
            require(child.returncode == 0, f"worker failed {seed}/{method}; inspect retained log")
    result = audit(package, phase)
    write_json(
        out / "complete.json",
        dict(
            seconds=time.perf_counter() - started,
            outputs=result["outputs"],
            passed=result["quality_passed"],
            controller_lifetime_cpu_seconds=time.process_time(),
            accounted_worker_and_launcher_cpu_seconds=sum(
                row["full_cpu_seconds"] for row in result["aggregates"].values()
            )
            - sum(command["controller_cpu_seconds"] for command in commands),
        ),
    )
    print(
        json.dumps(
            dict(
                phase=phase,
                outputs=result["outputs"],
                quality=result["quality_passed"],
                seconds=time.perf_counter() - started,
            )
        )
    )


def audit(package, phase):
    reg = verify(package)
    cfg = reg["config"]
    gold = {c["id"]: c for c in read(package / f"{phase}.json")}
    aggregates = {}
    for seed in cfg["seeds"]:
        for method in cfg["methods"]:
            path = package / phase / f"{seed}-{method}.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            require(
                len(rows) == len(gold) and {r["case"] for r in rows} == set(gold),
                "missing/duplicate cases",
            )
            for r in rows:
                c = gold[r["case"]]
                g = r["generation"]
                decoded = ByteTokenizer().decode(g["generated_ids"])
                require(
                    r["method"] == method and r["seed"] == seed and r["expected"] == c["expected"],
                    "identity mismatch",
                )
                require(
                    g["answer"] == decoded and r["correct"] == (decoded.strip() == c["expected"]),
                    "score mismatch",
                )
                require(
                    g["input_tokens"] == len((c["history"] + c["query"]).encode()) + 1,
                    "input token mismatch",
                )
                require(
                    r["unknown_assertion"]
                    == (c["kind"] == "unknown" and decoded.strip() not in ("?", "")),
                    "assertion score mismatch",
                )
                if r["preference"]:
                    for s, target in zip(
                        r["preference"]["scores"], [c["expected"], c["alternative"]], strict=True
                    ):
                        require(
                            s["ids"] == ByteTokenizer().encode(target)
                            and abs(s["logp"] - sum(s["token_logps"])) < 1e-9,
                            "likelihood mismatch",
                        )
            cells = {}
            for kind in ("value", "exact"):
                for location in ("local", "distant"):
                    subset = [r for r in rows if r["kind"] == kind and r["location"] == location]
                    worlds = {r["world"] for r in subset}
                    both = 0
                    flip = 0
                    for world in worlds:
                        pair = [r for r in subset if r["world"] == world]
                        require(
                            len(pair) == 2 and {r["arm"] for r in pair} == {0, 1}, "unpaired twins"
                        )
                        both += all(r["correct"] for r in pair)
                        flip += all(
                            r["preference"]["scores"][0]["logp"]
                            > r["preference"]["scores"][1]["logp"] + cfg["preference_margin"]
                            for r in pair
                        )
                    cells[f"{kind}/{location}"] = dict(
                        pairs=len(worlds), both_correct=both, preference_flip=flip
                    )
            command = next(
                x
                for x in read(package / phase / "commands.json")
                if f"{seed}-{method}.jsonl" == path.name
                and x["command"][-1] == str(seed)
                and x["command"][-3] == method
            )
            w = read(package / phase / f"{seed}-{method}-worker.json")
            cpu_samples = {
                int(pid): seconds for pid, seconds in command["sampled_child_cpu_seconds"].items()
            }
            cpu_samples[w["pid"]] = max(cpu_samples.get(w["pid"], 0), w["lifetime_cpu_seconds"])
            aggregates[f"{seed}-{method}"] = dict(
                cells=cells,
                correct=sum(r["correct"] for r in rows),
                n=len(rows),
                unknown_assertions=sum(r["unknown_assertion"] for r in rows),
                generation={
                    k: sum(r["generation"][k] for r in rows)
                    for k in (
                        "seconds",
                        "cpu_seconds",
                        "input_tokens",
                        "output_tokens",
                        "forward_positions",
                        "memory_commits",
                        "reader_ms",
                        "writer_linears_ms",
                        "reader_calls",
                    )
                },
                scoring={
                    k: sum(r["preference"][k] for r in rows if r["preference"])
                    for k in ("seconds", "cpu_seconds", "forward_positions", "memory_commits")
                },
                full_wall_seconds=command["wall_seconds"],
                full_cpu_seconds=sum(cpu_samples.values()) + command["controller_cpu_seconds"],
                sampled_tree_peak_bytes=command["sampled_controller_and_children_peak_bytes"],
                worker=w,
            )
    checks = {}
    cost_checks = {}
    for seed in cfg["seeds"]:
        c, b = (aggregates[f"{seed}-{m}"] for m in ("memory_on", "ordinary_matched"))

        def acc(row, cell):
            v = row["cells"][cell]
            return v["both_correct"] / v["pairs"]

        checks[f"{seed}-primary"] = (
            acc(c, "value/distant") >= cfg["min_pair_accuracy"]
            and acc(c, "value/distant") >= acc(b, "value/distant") + cfg["min_pair_gain"]
        )
        checks[f"{seed}-local"] = (
            acc(c, "value/local") >= acc(b, "value/local") - cfg["max_local_accuracy_drop"]
        )
        checks[f"{seed}-exact"] = acc(c, "exact/distant") >= acc(b, "exact/distant")
        checks[f"{seed}-unknown"] = (
            c["unknown_assertions"] <= b["unknown_assertions"] + cfg["max_extra_unknown_assertions"]
        )
        cost_checks[f"{seed}-cpu"] = (
            c["full_cpu_seconds"] <= b["full_cpu_seconds"] * cfg["cost_max_cpu_ratio"]
        )
        cost_checks[f"{seed}-wall"] = (
            c["full_wall_seconds"] <= b["full_wall_seconds"] * cfg["cost_max_wall_ratio"]
        )
        cost_checks[f"{seed}-rss"] = (
            c["sampled_tree_peak_bytes"]
            <= b["sampled_tree_peak_bytes"] * cfg["cost_max_sampled_tree_rss_ratio"]
        )
    result = dict(
        outputs=len(gold) * len(cfg["seeds"]) * len(cfg["methods"]),
        quality_passed=all(checks.values()),
        joint_passed=all(checks.values()) and all(cost_checks.values()),
        checks=checks,
        cost_checks=cost_checks,
        aggregates=aggregates,
        cost_scope=(
            "Full evaluation includes offline scoring, startup, logging and controller monitoring; "
            "not an online-only serving benchmark."
        ),
    )
    write_json(package / phase / "results.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run", "audit", "worker"))
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--phase", choices=("dev", "heldout"), default="dev")
    parser.add_argument("--method")
    parser.add_argument("--seed", type=int)
    a = parser.parse_args()
    try:
        if a.action == "freeze":
            require(a.parent is not None, "parent required")
            freeze(a.package, a.parent)
        elif a.action == "run":
            phase_run(a.package, a.phase)
        elif a.action == "audit":
            print(json.dumps(dict(passed=audit(a.package, a.phase)["quality_passed"])))
        else:
            worker(a.package, a.phase, a.method, a.seed)
    except (ValueError, OSError, KeyError, TypeError, TimeoutError) as error:
        parser.exit(1, f"Adversarial challenge failed: {error}\n")


if __name__ == "__main__":
    main()
