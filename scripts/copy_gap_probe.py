"""One frozen-checkpoint query-read-gate experiment; no fitting or chat changes."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import torch
from validate_owned_reproduction import validate

from toruk_lm.copy_diagnostic import generate, make_cases
from toruk_lm.engine import setup
from toruk_lm.owned_training import load, memory_bytes, runtime_identity, write_json
from toruk_lm.tokenizer import ByteTokenizer

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/copy-gap-probe-v1.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(package):
    registration = read(package / "registration.json")
    for name, expected in registration["inputs"].items():
        require(sha(ROOT / name) == expected, f"frozen input changed: {name}")
    for phase in ("dev", "heldout"):
        require(sha(package / f"{phase}.json") == registration["data"][phase], "dataset changed")
    return registration


def freeze(package, parent):
    require(not package.exists(), "fresh package directory required")
    parent = parent.resolve()
    require(parent.is_relative_to(ROOT), "parent must be inside the checkout")
    config = read(CONFIG)
    require(config["schema"] == "toruk-copy-gap-probe-v1", "unsupported probe protocol")
    require(
        0 < config["phase_seconds"] <= 180
        and config["max_new_tokens"] == 16
        and config["prefix_bytes"] == 351
        and config["gaps"] == [0, 32, 64, 128, 256]
        and config["seeds"] == [31, 47]
        and config["dev"]["worlds_per_kind"] <= 4
        and config["heldout"]["worlds_per_kind"] <= 12,
        "v1 probe requires the registered finite bounds",
    )
    result = validate(
        parent,
        ROOT / config["parent_config"],
        ROOT / "configs/owned-reproduction-v1.json",
        ROOT / config["parent_reference"],
    )
    require(result["research_gate"] is False, "prior negative verdict not confirmed")
    datasets = {
        phase: make_cases(
            phase,
            config[phase]["seed"],
            config[phase]["worlds_per_kind"],
            config["gaps"],
            config["prefix_bytes"],
        )
        for phase in ("dev", "heldout")
    }
    require(
        not (
            {r["expected"] for r in datasets["dev"] if r["kind"] == "exact"}
            & {r["expected"] for r in datasets["heldout"] if r["kind"] == "exact"}
        ),
        "exact-string values overlap between development and heldout",
    )
    package.mkdir(parents=True)
    for phase, rows in datasets.items():
        write_json(package / f"{phase}.json", rows)
    files = [
        CONFIG,
        Path(__file__),
        ROOT / "src/toruk_lm/copy_diagnostic.py",
        ROOT / config["parent_config"],
        ROOT / "configs/owned-reproduction-v1.json",
        ROOT / "scripts/validate_owned_reproduction.py",
        ROOT / "docs/research/copy-gap-v1-protocol.md",
    ]
    files += [ROOT / "src/toruk_lm" / n for n in runtime_identity()]
    models = {}
    for seed in config["seeds"]:
        for variant in ("memory_on", "ordinary", "ordinary_matched"):
            path = parent / "models" / f"{seed}-{variant}" / "checkpoint.pt"
            files.append(path)
            models[f"{seed}-{variant}"] = path.relative_to(ROOT).as_posix()
    write_json(
        package / "registration.json",
        dict(
            schema="toruk-copy-gap-registration-v1",
            frozen_utc=datetime.now(UTC).isoformat(),
            config=config,
            inputs={p.relative_to(ROOT).as_posix(): sha(p) for p in files},
            models=models,
            parent_validation=result,
            data={p: sha(package / f"{p}.json") for p in datasets},
            head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            git_status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
            python=sys.version,
            torch=torch.__version__,
            tokenizer=ByteTokenizer.fingerprint,
            state="Frozen before development and heldout inference; all thresholds fixed",
        ),
    )
    print(
        json.dumps(
            dict(
                status="FROZEN",
                dev_cases=len(datasets["dev"]),
                heldout_cases=len(datasets["heldout"]),
            )
        )
    )


def worker(package, phase, method, seed):
    registration = verify(package)
    config = registration["config"]
    variant = "memory_on" if method == "query_read_off" else method
    checkpoint = ROOT / registration["models"][f"{seed}-{variant}"]
    setup(0, 1)
    start = time.perf_counter()
    model, payload = load(checkpoint)
    checkpoint_hash = sha(checkpoint)
    require(
        payload["variant"] == variant and payload["options"]["seed"] == seed,
        "checkpoint variant/seed mismatch",
    )
    load_seconds = time.perf_counter() - start
    directory = package / phase
    raw_path = directory / f"{seed}-{method}.jsonl"
    require(not raw_path.exists(), "refusing to overwrite raw answers")
    with raw_path.open("x", encoding="utf-8") as stream:
        for case in read(package / f"{phase}.json"):
            if time.perf_counter() - start > config["phase_seconds"]:
                raise TimeoutError("bounded worker budget exhausted")
            generated = generate(
                model,
                case["history"],
                case["question"],
                config["max_new_tokens"],
                query_read_off=method == "query_read_off",
            )
            answer = generated["answer"].strip()
            row = dict(
                case_id=case["id"],
                world_id=case["world_id"],
                phase=phase,
                kind=case["kind"],
                gap=case["gap"],
                method=method,
                seed=seed,
                expected=case["expected"],
                correct=answer == case["expected"],
                wrong_nonempty=bool(answer) and answer != case["expected"],
                unknown_assertion=case["kind"] == "unknown" and answer not in ("?", ""),
                first_token_correct=generated["generated_ids"][0]
                == ByteTokenizer().encode(case["expected"])[0],
                generation=generated,
                checkpoint_sha256=checkpoint_hash,
            )
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
    write_json(
        directory / f"{seed}-{method}-worker.json",
        dict(
            status="PASS",
            model_load_seconds=load_seconds,
            seconds=time.perf_counter() - start,
            memory=memory_bytes(),
            peak_scope="One fresh process per method/seed/phase; includes loading",
        ),
    )


def run_phase(package, phase):
    registration = verify(package)
    config = registration["config"]
    if phase == "heldout":
        require(
            (package / "dev/complete.json").is_file(), "development execution must finish first"
        )
    directory = package / phase
    require(not directory.exists(), "phase already started; no quality-driven retries")
    directory.mkdir()
    started = time.perf_counter()
    commands = []
    for i, seed in enumerate(config["seeds"]):
        methods = config["methods"][i:] + config["methods"][:i]
        for method in methods:
            command = [
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
            remaining = config["phase_seconds"] - (time.perf_counter() - started)
            require(remaining > 0, "phase resource cap exhausted")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=remaining,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            (directory / f"{seed}-{method}.log").write_text(
                result.stdout + result.stderr, encoding="utf-8"
            )
            commands.append(dict(command=command, returncode=result.returncode))
            write_json(directory / "commands.json", commands)
            require(result.returncode == 0, f"worker failed: {seed}/{method}; inspect retained log")
    audit = audit_phase(package, phase)
    write_json(
        directory / "complete.json",
        dict(
            status="PASS",
            seconds=time.perf_counter() - started,
            outputs=audit["outputs"],
            quality_gate=audit["passed"],
        ),
    )
    print(
        json.dumps(
            dict(
                phase=phase,
                outputs=audit["outputs"],
                quality_gate=audit["passed"],
                seconds=time.perf_counter() - started,
            )
        )
    )


def audit_phase(package, phase):
    registration = verify(package)
    config = registration["config"]
    cases = {r["id"]: r for r in read(package / f"{phase}.json")}
    rows = []
    for seed in config["seeds"]:
        paired = {}
        for method in config["methods"]:
            path = package / phase / f"{seed}-{method}.jsonl"
            outputs = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            require(
                len(outputs) == len(cases) and {r["case_id"] for r in outputs} == set(cases),
                "duplicate or missing raw cases",
            )
            for row in outputs:
                case = cases[row["case_id"]]
                g = row["generation"]
                answer = ByteTokenizer().decode(g["generated_ids"]).strip()
                require(row["method"] == method and row["seed"] == seed, "raw mode/seed mismatch")
                require(
                    row["expected"] == case["expected"]
                    and row["correct"] == (answer == case["expected"]),
                    "raw score mismatch",
                )
                require(
                    g["answer"].strip() == answer and 0 < len(g["generated_ids"]) <= 16,
                    "raw generation mismatch",
                )
                require(g["input_tokens"] == config["prefix_bytes"] + 1, "unequal prefix budget")
                require(
                    row["unknown_assertion"]
                    == (case["kind"] == "unknown" and answer not in ("?", "")),
                    "false assertion score mismatch",
                )
                if method == "query_read_off":
                    require(g["query_answer_reader_calls"] == 0, "query read gate did not execute")
                paired[method, row["case_id"]] = g
            rows += outputs
        for case_id in cases:
            base, changed = (paired[m, case_id] for m in ("memory_on", "query_read_off"))
            require(
                base["history_state_sha256"] == changed["history_state_sha256"]
                and base["history_reader_calls"] == changed["history_reader_calls"],
                "intervention changed history processing",
            )
    aggregates = {}
    for seed in config["seeds"]:
        for method in config["methods"]:
            selected = [r for r in rows if r["seed"] == seed and r["method"] == method]
            cells = {}
            for kind in ("value", "exact", "unknown"):
                for gap in config["gaps"]:
                    cell = [r for r in selected if r["kind"] == kind and r["gap"] == gap]
                    cells[f"{kind}/{gap}"] = dict(
                        n=len(cell),
                        correct=sum(r["correct"] for r in cell),
                        first_token_correct=sum(r["first_token_correct"] for r in cell),
                    )
            aggregates[f"{seed}-{method}"] = dict(
                cells=cells,
                n=len(selected),
                correct=sum(r["correct"] for r in selected),
                unknown_assertions=sum(r["unknown_assertion"] for r in selected),
                wrong_nonempty=sum(r["wrong_nonempty"] for r in selected),
                **{
                    k: sum(r["generation"][k] for r in selected)
                    for k in (
                        "input_tokens",
                        "output_tokens",
                        "forward_positions",
                        "memory_commits",
                        "reader_ms",
                        "writer_linears_ms",
                        "reader_calls",
                        "writer_linear_calls",
                        "seconds",
                        "cpu_seconds",
                    )
                },
                worker=read(package / phase / f"{seed}-{method}-worker.json"),
            )
    checks = {}
    thresholds = config["criteria"]
    for seed in config["seeds"]:
        base, changed = (aggregates[f"{seed}-{m}"] for m in ("memory_on", "query_read_off"))

        def accuracy(row, kind, gaps):
            cells = [row["cells"][f"{kind}/{gap}"] for gap in gaps]
            return sum(c["correct"] for c in cells) / sum(c["n"] for c in cells)

        local = accuracy(changed, "exact", [0])
        checks[f"{seed}-local-exact-gain"] = (
            local >= accuracy(base, "exact", [0]) + thresholds["local_exact_min_gain"]
        )
        checks[f"{seed}-local-exact-floor"] = local >= thresholds["local_exact_min_accuracy"]
        for kind in ("value", "exact"):
            checks[f"{seed}-distant-{kind}"] = (
                accuracy(changed, kind, [32, 64, 128, 256])
                >= accuracy(base, kind, [32, 64, 128, 256])
                - thresholds["distant_known_max_accuracy_drop"]
            )
        checks[f"{seed}-local-value"] = (
            accuracy(changed, "value", [0])
            >= accuracy(base, "value", [0]) - thresholds["local_value_max_accuracy_drop"]
        )
        checks[f"{seed}-unknown"] = (
            changed["unknown_assertions"]
            <= base["unknown_assertions"] + thresholds["unknown_max_extra_false_assertions"]
        )
        checks[f"{seed}-work"] = (
            changed["forward_positions"]
            <= base["forward_positions"] * thresholds["max_forward_position_ratio"]
        )
    result = dict(
        schema="toruk-copy-gap-results-v1",
        phase=phase,
        outputs=len(rows),
        passed=all(checks.values()),
        checks=checks,
        aggregates=aggregates,
        scope="Frozen seeds; repeated gaps are paired within world, not independent questions",
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
    args = parser.parse_args()
    try:
        if args.action == "freeze":
            require(args.parent is not None, "freeze requires --parent")
            freeze(args.package, args.parent)
        elif args.action == "run":
            run_phase(args.package, args.phase)
        elif args.action == "audit":
            print(json.dumps(dict(passed=audit_phase(args.package, args.phase)["passed"])))
        else:
            worker(args.package, args.phase, args.method, args.seed)
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Copy-gap probe failed: {error}\n")


if __name__ == "__main__":
    main()
