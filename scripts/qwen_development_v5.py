"""Registered development-only instruction study; reuse frozen workers and monitor."""

import argparse
import ctypes
import importlib.metadata
import json
import subprocess
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from audit_qwen_development_v4 import Inputs, frozen_api
from qwen_long_history_v3 import load, read, rows, sha, write

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/qwen-development-v5.json"
PROTOCOL = ROOT / "docs/research/qwen-development-v5-protocol.md"
TESTS = ROOT / "tests/test_qwen_development_v5.py"
OLD = "artifacts/qwen-long-history-v3/attempt-001"
NAMESPACE = ROOT / "artifacts/qwen-development-v5"
KINDS = ("distant", "correction", "distractor", "literal", "preservation", "reference", "missing")
COSTS = (
    "prompt_tokens",
    "output_tokens",
    "selector_cpu_seconds",
    "selector_wall_seconds",
    "fit_cpu_seconds",
    "fit_wall_seconds",
    "generation_cpu_seconds",
    "generation_wall_seconds",
    "request_cpu_seconds",
    "request_wall_seconds",
)


def validate_cases(cases: list[dict], expected: list[dict]) -> None:
    if cases != expected or len(cases) != 7 or tuple(c["kind"] for c in cases) != KINDS:
        raise ValueError("only the complete seven sealed development cases are permitted")
    if any(c.get("split") != "development" for c in cases):
        raise ValueError("development only")


def prompt(api: dict, turns: list[dict], chosen: list[int], instruction: str) -> list[dict]:
    original = api["envelope"](turns, chosen)
    return [{"role": "system", "content": instruction}, original[1]]


def verify_map(bindings: dict[str, str]) -> None:
    for name, expected in bindings.items():
        if sha(ROOT / name) != expected:
            raise ValueError("registered identity drift: " + name)


def verify_registration(run: Path) -> dict:
    reg = read(run / "registration.json")
    verify_map(reg["bindings"])
    verify_map(reg["frozen_baseline"])
    for name, expected in reg["dependencies"].items():
        if importlib.metadata.version(name) != expected:
            raise ValueError("dependency drift: " + name)
    return reg


def frozen_inventory() -> dict[str, str]:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    prefixes = (
        "artifacts/qwen-long-history-v",
        "artifacts/qwen-long-history-dev-v4/",
        "artifacts/research-evidence-portable-v1/",
        "docs/research/qwen-long-history-",
        "scripts/qwen_long_history",
        "scripts/audit_qwen_development_v4.py",
        "scripts/report_qwen_long_history",
        "scripts/verify_portable_research_evidence.py",
        "tests/test_qwen_",
        "configs/qwen-long-history-",
        "src/toruk_lm/",
        "artifacts/backbone-qualification-v1/registration.json",
        "scripts/qualify_answer_backbone.py",
        "pyproject.toml",
        ".gitattributes",
    )
    return {n: sha(ROOT / n) for n in names if n and n.startswith(prefixes)}


def prepare(run: Path) -> None:
    start, used = time.perf_counter(), time.process_time()
    config = read(CONFIG)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != config["base_commit"]:
        raise ValueError("study requires the registered base commit")
    inputs = Inputs(ROOT)
    cases = inputs.json(OLD + "/development.json")
    validate_cases(cases, cases)
    api = frozen_api(inputs)
    if config["candidates"]["original"] != api["SYSTEM"]:
        raise ValueError("original instruction drift")
    oldreg = inputs.json(OLD + "/arms/after/rehearsal/registration.json")
    assets = [Path(config["backbone_directory"]) / Path(n).name for n in oldreg["model_files"][:-1]]
    assets.append(Path(config["selector_checkpoint"]))
    asset_bindings = {}
    for path, original in zip(assets, oldreg["model_files"], strict=True):
        expected = oldreg["bindings"][original]
        if sha(path) != expected:
            raise ValueError("runtime asset identity mismatch: " + str(path))
        asset_bindings[str(path)] = expected
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        config["backbone_directory"], local_files_only=True, trust_remote_code=False
    )
    run.mkdir(parents=True, exist_ok=False)
    baseline = frozen_inventory()
    write(run / "baseline.json", {"head": head, "sha256": baseline})
    write(
        run / "starting-state.json",
        {
            "head": head,
            "cwd": str(ROOT),
            "git_root": subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True
            ).strip(),
            "status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
            "registered_utc": datetime.now(UTC).isoformat(),
            "heldout_records_parsed": 0,
        },
    )
    shim = run / "worker-source/scripts/qwen_long_history.py"
    shim.parent.mkdir(parents=True)
    shim.write_text(
        "import sys\n"
        + f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
        + "from qwen_development_v5 import worker_main\nworker_main()\n",
        encoding="utf-8",
    )
    source_paths = [Path(__file__), CONFIG, PROTOCOL, TESTS, shim]
    with zipfile.ZipFile(run / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source_paths:
            archive.writestr(path.relative_to(ROOT).as_posix(), path.read_bytes())
        for name in baseline:
            if name.startswith(("src/", "scripts/")):
                archive.writestr(name, (ROOT / name).read_bytes())
    bindings = {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths}
    bindings[(run / "source.zip").relative_to(ROOT).as_posix()] = sha(run / "source.zip")
    dependencies = {n: importlib.metadata.version(n) for n in oldreg["dependencies"]}
    registrations = {}
    for label in config["order"]:
        candidate, arm = label.split("-")
        instruction = config["candidates"][candidate]
        folder = run / "arms" / label / "rehearsal"
        folder.mkdir(parents=True)
        write(folder / "development.json", cases)
        full_ids = {
            c["id"]: tokenizer.apply_chat_template(
                prompt(
                    api, api["inference_turns"](c), list(range(len(c["messages"]))), instruction
                ),
                tokenize=True,
                add_generation_prompt=True,
                return_dict=False,
            )
            for c in cases
        }
        write(folder / "full-prompt-ids.json", full_ids)
        per_arm = {
            p.relative_to(ROOT).as_posix(): sha(p)
            for p in (folder / "development.json", folder / "full-prompt-ids.json")
        }
        write(
            folder / "registration.json",
            {
                "schema": "qwen-development-v5",
                "v5_root": str(run),
                "candidate": candidate,
                "arm": arm,
                "instruction": instruction,
                "dependencies": dependencies,
                "config": {
                    **oldreg["config"],
                    "backbone_directory": config["backbone_directory"],
                    "selector_checkpoint": config["selector_checkpoint"],
                },
                "context_limit": oldreg["context_limit"],
                "model_files": list(asset_bindings),
                "bindings": {**bindings, **asset_bindings, **per_arm},
                "v2_config": {
                    **config["limits"],
                    "runtime_python": sys.executable,
                    "source_checkout": str(run / "worker-source"),
                },
                "heldout_authorized": False,
            },
        )
        registrations[(folder / "registration.json").relative_to(ROOT).as_posix()] = sha(
            folder / "registration.json"
        )
    write(
        run / "registration.json",
        {
            "schema": "qwen-development-v5",
            "registered_utc": datetime.now(UTC).isoformat(),
            "config": config,
            "bindings": {**bindings, **asset_bindings, **registrations},
            "frozen_baseline": baseline,
            "dependencies": dependencies,
            "consumed_development_inputs": inputs.consumed,
            "new_training": False,
            "heldout_authorized": False,
            "python": sys.version,
        },
    )
    write(
        run / "preparation-cost.json",
        {
            "wall_seconds": time.perf_counter() - start,
            "controller_cpu_seconds": time.process_time() - used,
            "new_generations": 0,
        },
    )
    print(json.dumps({"registered": str(run), "conditions": 6, "generations_planned": 48}))


def worker_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("worker",))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--split", choices=("development",), required=True)
    parser.add_argument("--arm", choices=("toruk", "lexical"), required=True)
    args = parser.parse_args()
    local = read(args.run / "registration.json")
    reg = verify_registration(Path(local["v5_root"]))
    verify_map(local["bindings"])
    if args.arm != local["arm"]:
        raise ValueError("registered arm mismatch")
    inputs = Inputs(ROOT)
    api = frozen_api(inputs)
    validate_cases(read(args.run / "development.json"), inputs.json(OLD + "/development.json"))
    sys.path.insert(0, str(ROOT / "src"))
    import qwen_long_history as legacy

    from toruk_lm import chat_foundation
    from toruk_lm.relevance_gate import LexicalAdmissionSelector

    original_selector = chat_foundation.TorukContextSelector
    # Adapt only the research worker; no package or production source is modified.
    cast(Any, chat_foundation).TorukContextSelector = lambda p: LexicalAdmissionSelector(
        original_selector(p)
    )
    cast(Any, legacy).envelope = lambda turns, chosen: prompt(
        api, turns, chosen, local["instruction"]
    )
    cast(Any, legacy).verify = lambda path: local
    if local["instruction"] != reg["config"]["candidates"][local["candidate"]]:
        raise ValueError("instruction mismatch")
    legacy.worker(args.run, "development", args.arm)


def evaluate(run: Path) -> None:
    monitor = load(ROOT / "scripts/qwen_long_history_v2.py", "v5_frozen_monitor")
    started, used = monitor.clocks(), monitor.cpu()
    reg = verify_registration(run)
    write(
        run / "development-started.json",
        {
            "clocks": started,
            "registration_sha256": sha(run / "registration.json"),
        },
    )
    acquired = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    stages = []
    totals = {"wall_seconds": 0.0, "cpu_seconds": 0.0}
    try:
        if not acquired:
            raise RuntimeError("idle-sleep prevention failed")
        for label in reg["config"]["order"]:
            _, arm = label.split("-")
            stage = monitor.stage(run / "arms" / label, arm, totals)
            stage["condition"] = label
            stages.append(stage)
            for key in totals:
                totals[key] += stage[key]
            if stage["failure"]:
                break
    finally:
        restored = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        write(
            run / "development-cost.json",
            {
                "stages": stages,
                "totals": totals,
                "power_acquired": bool(acquired),
                "power_restored": bool(restored),
                "heldout_completed": 0,
                "lifecycle_wall_seconds": monitor.elapsed(started, monitor.clocks()),
                "controller_lifecycle_cpu_seconds": monitor.cpu() - used,
                "complete": len(stages) == 6 and all(s["failure"] is None for s in stages),
            },
        )
    verify_registration(run)


def decision(baselines: dict, candidate: dict, technical: bool) -> dict:
    if any(
        len(group[a]["correct"]) != 7
        for group in (baselines, candidate)
        for a in ("toruk", "lexical")
    ):
        return {"checks": {"complete_seven_case_comparison": False}, "development_support": False}
    checks = {"technical_validity": technical}
    toruk, lexical = candidate["toruk"], candidate["lexical"]
    checks["toruk_improves"] = sum(toruk["correct"]) > sum(baselines["toruk"]["correct"])
    checks["no_new_case_losses"] = all(
        all(
            not old or new
            for old, new in zip(baselines[a]["correct"], candidate[a]["correct"], strict=True)
        )
        for a in ("toruk", "lexical")
    )
    checks["no_loss_versus_matched_lexical"] = all(
        not lex or tor for tor, lex in zip(toruk["correct"], lexical["correct"], strict=True)
    )
    checks["evidence_exact_copy_preservation"] = all(
        candidate[a]["known_retained"] == 6
        and candidate[a]["exact_copy"]
        and candidate[a]["preservation"]
        for a in ("toruk", "lexical")
    )
    return {"checks": checks, "development_support": all(checks.values())}


def audit_row(case: dict, row: dict, tokenizer: Any, api: dict, instruction: str) -> None:
    from audit_qwen_development_v4 import audit_row as frozen_audit_row

    changed_api = {**api, "envelope": lambda turns, chosen: prompt(api, turns, chosen, instruction)}
    frozen_audit_row(case, row, tokenizer, changed_api)


def summarize(run: Path) -> dict:
    tick, used = time.perf_counter(), time.process_time()
    reg = verify_registration(run)
    inputs = Inputs(ROOT)
    cases = inputs.json(OLD + "/development.json")
    api = frozen_api(inputs)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        ROOT / "artifacts/research-evidence-portable-v1/tokenizers/qwen",
        local_files_only=True,
        trust_remote_code=False,
    )
    costs = read(run / "development-cost.json")
    conditions = {}
    technical = costs["complete"] and costs["power_acquired"] and costs["power_restored"]
    original_matches = True
    for label in reg["config"]["order"]:
        candidate, arm = label.split("-")
        folder = run / "arms" / label / "rehearsal"
        path = folder / f"development-{arm}-answers.jsonl"
        data = rows(path) if path.exists() else []
        ordinary = [r for r in data if not r["is_replay"]]
        complete = len(data) == 8 and [r["id"] for r in ordinary] == [c["id"] for c in cases]
        instruction = reg["config"]["candidates"][candidate]
        for case, row in zip(cases, ordinary, strict=False):
            audit_row(case, row, tokenizer, api, instruction)
        replay_match = (
            complete
            and data[-1]["id"] == data[0]["id"] + "-replay"
            and all(
                data[0][k] == data[-1][k]
                for k in (
                    "answer",
                    "score",
                    "prompt_ids",
                    "generated_ids",
                    "selected_indices",
                    "work",
                )
            )
        )
        if complete:
            audit_row(cases[0], data[-1], tokenizer, api, instruction)
        historical_arm = "after" if arm == "toruk" else "lexical"
        historical = inputs.rows(
            OLD + f"/arms/{historical_arm}/rehearsal/development-{arm}-answers.jsonl"
        )
        selection_match = complete and all(
            row[k] == old[k]
            for row, old in zip(data, historical, strict=True)
            for k in ("selected_indices", "proposed_indices", "selected_sources")
        )
        if candidate == "original":
            original_matches &= complete and all(
                row[k] == old[k]
                for row, old in zip(data, historical, strict=True)
                for k in ("prompt_ids", "generated_ids", "answer", "score")
            )
        technical &= bool(complete and replay_match and selection_match)
        by_kind = {r["kind"]: r for r in ordinary}
        conditions[label] = {
            "complete": complete,
            "replay_matches": replay_match,
            "selection_matches_v3": selection_match,
            "correct": [r["score"]["correct"] for r in ordinary],
            "accuracy": sum(r["score"]["correct"] for r in ordinary) / 7,
            "known_retained": sum(
                r["required_evidence_retained"] for r in ordinary if r["kind"] != "missing"
            ),
            "exact_copy": by_kind.get("literal", {}).get("score", {}).get("exact_match", False),
            "preservation": by_kind.get("preservation", {}).get("score", {}).get("correct", False),
            "seven_case_costs": {k: sum(r[k] for r in ordinary) for k in COSTS},
            "including_replay_costs": {k: sum(r[k] for r in data) for k in COSTS},
            "answers": [
                {
                    k: r[k]
                    for k in (
                        "id",
                        "kind",
                        "answer",
                        "score",
                        "failure",
                        "prompt_tokens",
                        "output_tokens",
                        "request_wall_seconds",
                    )
                }
                for r in ordinary
            ],
        }
    technical &= original_matches
    baselines = {a: conditions["original-" + a] for a in ("toruk", "lexical")}
    result = {
        "schema": "qwen-development-v5",
        "technical_validity": bool(technical),
        "original_controls_match_v3": original_matches,
        "conditions": conditions,
        "decisions": {
            c: decision(
                baselines,
                {a: conditions[c + "-" + a] for a in ("toruk", "lexical")},
                bool(technical),
            )
            for c in ("field", "check")
        },
        "frozen_files_unchanged": len(reg["frozen_baseline"]),
        "new_training": False,
        "production_change": False,
        "heldout_records_parsed": 0,
        "audit_wall_seconds": time.perf_counter() - tick,
        "audit_controller_cpu_seconds": time.process_time() - used,
    }
    write(run / "results.json", result)
    print(
        json.dumps(
            {k: result[k] for k in ("technical_validity", "decisions", "frozen_files_unchanged")}
        )
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "development", "summarize"))
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to(NAMESPACE) or run == NAMESPACE:
        raise ValueError("fresh v5 output namespace required")
    {"prepare": prepare, "development": evaluate, "summarize": summarize}[args.action](run)


if __name__ == "__main__":
    main()
