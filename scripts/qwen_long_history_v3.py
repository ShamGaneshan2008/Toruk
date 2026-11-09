"""Versioned development-only admission-gate experiment; no held-out action."""

import argparse
import ctypes
import hashlib
import importlib
import importlib.util
import json
import subprocess
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/qwen-long-history-v3.json"
PROTOCOL = ROOT / "docs/research/qwen-long-history-v3-protocol.md"
GATE = ROOT / "src/toruk_lm/relevance_gate.py"
TESTS = ROOT / "tests/test_qwen_long_history_v3.py"
ARMS = ("before", "lexical", "after")


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("module unavailable: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def monitor_module() -> Any:
    return load(ROOT / "scripts/qwen_long_history_v2.py", "frozen_v2_monitor")


def legacy_module(source: Path) -> Any:
    sys.path.insert(0, str(source / "scripts"))
    return importlib.import_module("qwen_long_history")


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def validate_development(cases: list[dict], allowed: set[str]) -> None:
    if len(cases) != 7 or {c["id"] for c in cases} != allowed:
        raise ValueError("only the seven sealed development IDs are permitted")
    if any("-development-" not in c["id"] for c in cases):
        raise ValueError("development-only boundary")


def prepare(run: Path) -> None:
    config = read(CONFIG)
    source, previous = Path(config["source_checkout"]), ROOT / config["v2_run"]
    if sha(previous / "proposed-freeze.json") != config["v2_proposed_freeze_sha256"]:
        raise ValueError("v2 freeze identity mismatch")
    monitor = monitor_module()
    frozen = read(previous / "proposed-freeze.json")
    for group in ("registered_inputs", "output_bindings"):
        monitor.verify_bindings(frozen[group])
    legacy = legacy_module(source)
    dev_path = previous / "rehearsal/development.json"
    cases = read(dev_path)
    validate_development(cases, {c["id"] for c in cases})
    run.mkdir(parents=True, exist_ok=False)
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    original_preservation = read(previous / "preservation-before.json")
    preservation = dict(original_preservation["bindings"])
    preservation.update(
        {
            str(p): sha(p)
            for p in (ROOT / "artifacts/qwen-long-history-v2").rglob("*")
            if p.is_file()
        }
    )
    preservation.update(
        {
            str(ROOT / p): sha(ROOT / p)
            for p in (
                "configs/qwen-long-history-v2.json",
                "docs/research/qwen-long-history-v2-protocol.md",
                "docs/research/qwen-long-history-v2-results.md",
                "scripts/qwen_long_history_v2.py",
                "tests/test_qwen_long_history_v2.py",
            )
        }
    )
    monitor.verify_bindings(preservation)
    write(
        run / "preservation-before.json",
        {"bindings": preservation, "metadata_only": original_preservation["unreadable"]},
    )
    write(
        run / "starting-state.json",
        {
            "cwd": str(ROOT),
            "git_root": subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            ).strip(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "status": subprocess.check_output(["git", "status", "--short"], text=True),
            "source_status": subprocess.check_output(
                ["git", "-c", "safe.directory=D:/Toruk", "-C", str(source), "status", "--short"],
                text=True,
            ),
            "utc": datetime.now(UTC).isoformat(),
            "no_heldout_answers_opened": True,
        },
    )
    baseline = {
        arm: {
            r["id"]: r
            for r in rows(previous / f"rehearsal/development-{arm}-answers.jsonl")
            if not r["is_replay"]
        }
        for arm in ("toruk", "lexical")
    }
    diagnosis = []
    for case in cases:
        item = {
            "id": case["id"],
            "kind": case["kind"],
            "question": case["messages"][-1]["content"],
            "expected": case["expected"],
            "required_indices": case["required"],
            "required_sources": [{"id": f"m{i}", **case["messages"][i]} for i in case["required"]],
        }
        for arm in ("toruk", "lexical"):
            r = baseline[arm][case["id"]]
            assert r["prompt_messages"] == legacy.envelope(
                legacy.inference_turns(case), r["selected_indices"]
            )
            assert r["selected_indices"] == sorted(set(r["selected_indices"]))
            assert r["selected_sources"] == [
                {"id": f"m{i}", **case["messages"][i]} for i in r["selected_indices"]
            ]
            assert r["score"] == legacy.score(r["answer"], case)
            item[arm] = {
                k: r[k]
                for k in (
                    "answer",
                    "selected_indices",
                    "selected_sources",
                    "prompt_tokens",
                    "score",
                    "required_evidence_retained",
                    "proposed_indices",
                )
            }
        old = baseline["toruk"][case["id"]]
        item["diagnosis"] = (
            "correct abstention"
            if old["score"]["correct"]
            else "missing required evidence; irrelevant replacement turns"
            if not old["required_evidence_retained"]
            else (
                "Qwen generation with required evidence retained; "
                "prompt-composition sensitivity not isolated"
            )
        )
        item["ordering_error_observed"] = False
        item["rendering_error_observed"] = False
        item["fit_evicted_proposed_sources"] = old["selected_indices"] != old["proposed_indices"]
        item["missing_required_indices"] = sorted(
            set(case["required"]) - set(old["selected_indices"])
        )
        diagnosis.append(item)
    write(
        run / "v2-development-diagnosis.json",
        {
            "cases": diagnosis,
            "scope": "Development only; no causal overclaim from evidence presence alone",
        },
    )
    write(
        run / "development-overlap.json",
        {
            "case_ids": [c["id"] for c in cases],
            "source_sha256": sha(dev_path),
            "intentional_reuse": (
                "Exact seven v2 development cases, already observed; adaptive development fitting"
            ),
            "new_cases": 0,
            "new_training_cases": 0,
            "heldout_file_parsed": False,
            "boundary": (
                "Only dev.json and dev-only prompt IDs copied; model worker rejects other IDs"
            ),
        },
    )
    with (run / "development.json").open("xb") as stream:
        stream.write(dev_path.read_bytes())
    ids_path = previous / "rehearsal/full-prompt-ids.json"
    ids = read(ids_path)
    assert set(ids) == {c["id"] for c in cases}
    write(run / "full-prompt-ids.json", ids)
    original_reg = read(previous / "rehearsal/registration.json")
    checkpoint_sha = original_reg["config"]["selector_sha256"]
    write(
        run / "selector-identity.json",
        {
            "format": "toruk-lexical-admission-v3",
            "new_training": False,
            "weights_path": original_reg["config"]["selector_checkpoint"],
            "weights_sha256": checkpoint_sha,
            "gate_source_sha256": sha(GATE),
            "runtime_identity_sha256": hashlib.sha256(
                GATE.read_bytes() + checkpoint_sha.encode()
            ).hexdigest(),
        },
    )
    shim = run / "worker-source/scripts/qwen_long_history.py"
    shim.parent.mkdir(parents=True)
    with shim.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            "import sys\n"
            + f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
            + "from qwen_long_history_v3 import worker_main\nworker_main()\n"
        )
    current = [
        Path(__file__),
        GATE,
        CONFIG,
        PROTOCOL,
        TESTS,
        shim,
        run / "development.json",
        run / "full-prompt-ids.json",
        run / "development-overlap.json",
        run / "v2-development-diagnosis.json",
        run / "selector-identity.json",
    ]
    with zipfile.ZipFile(run / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for p in current:
            archive.writestr(p.relative_to(ROOT).as_posix(), p.read_bytes())
        archive.writestr("inherited-v2-source.zip", (previous / "v2-source.zip").read_bytes())
    bindings = {
        **frozen["registered_inputs"],
        **{str(p): sha(p) for p in current},
        str(run / "source.zip"): sha(run / "source.zip"),
        str(previous / "proposed-freeze.json"): sha(previous / "proposed-freeze.json"),
    }
    arm_registrations = {}
    for name in ARMS:
        rehearsal = run / "arms" / name / "rehearsal"
        rehearsal.mkdir(parents=True)
        for filename in ("development.json", "full-prompt-ids.json"):
            with (rehearsal / filename).open("xb") as stream:
                stream.write((run / filename).read_bytes())
        per_arm_bindings = {
            **bindings,
            **{
                str(rehearsal / n): sha(rehearsal / n)
                for n in ("development.json", "full-prompt-ids.json")
            },
        }
        reg = {
            **original_reg,
            "bindings": per_arm_bindings,
            "v3_arm": name,
            "v3_root": str(run),
            "allowed_development_ids": [c["id"] for c in cases],
            "schema": "qwen-long-history-v3-development-only",
            "model_files": [str(source / n) for n in original_reg["model_files"]],
            "v2_config": {**config, "source_checkout": str(run / "worker-source")},
        }
        write(rehearsal / "registration.json", reg)
        arm_registrations[str(rehearsal / "registration.json")] = sha(
            rehearsal / "registration.json"
        )
    write(
        run / "registration.json",
        {
            "schema": "qwen-long-history-v3-development-only",
            "bindings": {**bindings, **arm_registrations},
            "config": config,
            "new_training": False,
            "heldout_authorized": False,
            "registered_utc": datetime.now(UTC).isoformat(),
        },
    )
    write(
        run / "preparation-cost.json",
        {
            "wall_seconds": time.perf_counter() - start_wall,
            "controller_cpu_seconds": time.process_time() - start_cpu,
            "scope": (
                "Shared offline diagnosis, preservation and registration; "
                "before candidate inference"
            ),
        },
    )
    print(
        json.dumps({"registered": str(run), "development_cases": 7, "heldout_authorized": False}),
        flush=True,
    )


def worker_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("worker",))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--split", choices=("development",), required=True)
    parser.add_argument("--arm", choices=("toruk", "lexical"), required=True)
    args = parser.parse_args()
    reg = read(args.run / "registration.json")
    validate_development(read(args.run / "development.json"), set(reg["allowed_development_ids"]))
    source = Path(read(CONFIG)["source_checkout"])
    sys.path.insert(0, str(source / "src"))
    legacy = legacy_module(source)
    from toruk_lm import chat_foundation, context_selection

    original_toruk = chat_foundation.TorukContextSelector
    original_lexical = context_selection.LexicalContextSelector
    gate_module = load(GATE, "registered_admission_v3")
    trace_path = args.run / "selection-traces.jsonl"
    trace_path.open("x").close()

    class TracedSelector:
        def __init__(self, selector: Any) -> None:
            self.selector = selector

        def __getattr__(self, name: str) -> Any:
            return getattr(self.selector, name)

        def select(self, messages: list[dict]) -> Any:
            result = self.selector.select(messages)
            with trace_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(
                    json.dumps(
                        {
                            "arm": reg["v3_arm"],
                            "question": messages[-1]["content"],
                            "selected_indices": result[0],
                            "gate": getattr(self.selector, "last_trace", None),
                        }
                    )
                    + "\n"
                )
            return result

    def toruk_factory(checkpoint: Path) -> Any:
        ranker = original_toruk(checkpoint)
        return TracedSelector(
            gate_module.LexicalAdmissionSelector(ranker) if reg["v3_arm"] == "after" else ranker
        )

    cast(Any, chat_foundation).TorukContextSelector = toruk_factory
    cast(Any, context_selection).LexicalContextSelector = lambda kind: TracedSelector(
        original_lexical(kind)
    )
    legacy.worker(args.run, "development", args.arm)


def evaluate(run: Path) -> None:
    monitor = monitor_module()
    reg = read(run / "registration.json")
    start, before = monitor.clocks(), monitor.cpu()
    write(
        run / "development-started.json",
        {"clocks": start, "registration_sha256": sha(run / "registration.json")},
    )
    monitor.verify_bindings(reg["bindings"])
    acquired = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    write(run / "power-start.json", {"acquired": bool(acquired)})
    totals, stages = {"wall_seconds": 0.0, "cpu_seconds": 0.0}, []
    try:
        if not acquired:
            raise RuntimeError("idle-sleep prevention failed")
        for name in reg["config"]["order"]:
            stage = monitor.stage(
                run / "arms" / name, "lexical" if name == "lexical" else "toruk", totals
            )
            stage["v3_arm"] = name
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
                "lifecycle_wall_seconds": monitor.elapsed(start, monitor.clocks()),
                "controller_lifecycle_cpu_seconds": monitor.cpu() - before,
                "power_restored": bool(restored),
                "heldout_completed": 0,
                "complete": len(stages) == 3 and all(s["failure"] is None for s in stages),
            },
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "development"))
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to(ROOT / "artifacts/qwen-long-history-v3"):
        raise ValueError("fresh v3 output namespace required")
    {"prepare": prepare, "development": evaluate}[args.action](run)


if __name__ == "__main__":
    main()
