"""Validation-only bounded protocol. No final-test evaluation or runtime oracle."""

import importlib
import json
import os
import platform
import sys
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

import torch

from toruk_lm.controlled import (
    evaluate_controlled,
    package_fingerprint,
    train_controlled,
)
from toruk_lm.data import sha256_file, write_json
from toruk_lm.effect_training import evaluate_effect, fit_effect, paired_labels
from toruk_lm.model import ModelConfig
from toruk_lm.worlds import make_worlds

EXPECTED_RESULTS = {
    "ordinary-write",
    "ordinary-wide-write",
    "recurrent-write",
    "recurrent-predictor",
    "revision-write",
    "revision-predictor",
    "revision-heuristic",
    "revision-random",
    "revision-retain",
    "revision-reset",
    "no-correction-write",
    "no-preservation-write",
    "slots2-write",
    "slots8-write",
}


def process_peak_bytes() -> int | None:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t)
                for name in (
                    "PeakWorkingSetSize",
                    "WorkingSetSize",
                    "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage",
                    "PagefileUsage",
                    "PeakPagefileUsage",
                )
            ]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        current = ctypes.windll.kernel32.GetCurrentProcess
        current.restype = wintypes.HANDLE
        query = ctypes.windll.psapi.GetProcessMemoryInfo
        query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        query.restype = wintypes.BOOL
        return (
            int(counters.PeakWorkingSetSize)
            if query(current(), ctypes.byref(counters), counters.cb)
            else None
        )
    resource: Any = importlib.import_module("resource")
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * (1 if platform.system() == "Darwin" else 1024))


def aggregate(paths: list[Path], expected: set[str]) -> dict[str, Any]:
    """Reject missing/duplicate/stale/data-mismatched results; never silently exclude failures."""
    results: dict[str, Any] = {}
    data = None
    for path in paths:
        result = json.loads(path.read_text(encoding="utf-8"))
        name = path.parent.name
        if name in results:
            raise ValueError("duplicate comparison result")
        if result["package_sha256"] != package_fingerprint():
            raise ValueError("stale comparison result")
        if result["config"]["seed"] != 23:
            raise ValueError("unexpected comparison seed")
        if data is not None and data != result["data"]:
            raise ValueError("comparison data mismatch")
        data = result["data"]
        groups = result["groups"]
        primary = (
            sum(
                groups[g]["accuracy"]
                for g in ("corrected", "unchanged_entity", "unrelated_date", "unrelated_number")
            )
            / 4
        )
        results[name] = dict(
            primary_correction_preservation_macro=primary,
            exact_accuracy=result["exact_accuracy"],
            groups=groups,
            seed=result["config"]["seed"],
            policy=result["policy"],
            inference_seconds=result["inference_seconds"],
            inference_forward_tokens=result["inference_forward_tokens"],
            metrics_sha256=sha256_file(path),
        )
    if set(results) != expected:
        raise ValueError("missing/unexpected comparison results")
    return dict(
        results=results,
        data=data,
        seeds=[23],
        across_seed_std=None,
        uncertainty="one seed; no across-seed uncertainty estimate",
        final_test="NOT_RUN; validation only",
    )


def run_pilot(
    output: Path, steps: int = 12, worlds: int = 4, answer_budget: int = 16, seconds: float = 110
) -> dict[str, Any]:
    if steps <= 0 or worlds < 2 or answer_budget <= 0 or seconds <= 0:
        raise ValueError("positive bounded pilot configuration required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("fresh pilot directory required")
    output.mkdir(parents=True, exist_ok=True)
    protocol = dict(
        schema="m6-validation-pilot-v1",
        seed=23,
        fixture_seed=17,
        worlds_per_split=worlds,
        steps_per_model=steps,
        profile_steps=2,
        answer_budget=answer_budget,
        predictor_steps=100,
        model=dict(context=64, width=32, heads=4, layers=2),
        memory_slots=[2, 4, 8],
        threads=1,
        cpu_only=True,
        elapsed_cap_seconds=seconds,
        primary="mean corrected/unchanged-entity/unrelated-date/unrelated-number accuracy",
        final_test="closed",
        tuning="none; all coefficients/configs predeclared",
        parameter_match="ordinary width40 sensitivity; approximate only",
        matching="equal world steps/probes; parameters, FLOPs and branch costs not matched",
        falsification=(
            "no joint accuracy improvement over heuristic, or correction/preservation tradeoff"
        ),
        package_sha256=package_fingerprint(),
    )
    protocol["baselines"] = sorted(EXPECTED_RESULTS)
    write_json(output / "protocol.json", protocol)  # Freeze BEFORE world generation/evaluation.
    hardware = dict(
        python=platform.python_version(),
        platform=platform.platform(),
        processor=platform.processor(),
        logical_cpus=os.cpu_count(),
        torch=str(torch.__version__),
        cuda_available=torch.cuda.is_available(),
        training_device="cpu",
    )
    write_json(output / "hardware.json", hardware)
    stages: list[dict[str, Any]] = []
    started = time.perf_counter()

    def stage(name: str, function: Callable[[], Any]) -> Any:
        if time.perf_counter() - started >= seconds:
            stages.append(dict(stage=name, status="BLOCKED", reason="elapsed pilot budget"))
            write_json(output / "stages.json", stages)
            raise TimeoutError("pilot elapsed budget exhausted before stage " + name)
        start = time.perf_counter()
        record: dict[str, Any] = dict(stage=name, status="RUNNING")
        stages.append(record)
        write_json(output / "stages.json", stages)
        try:
            result = function()
        except Exception as error:
            record.update(status="FAIL", error=repr(error), seconds=time.perf_counter() - start)
            write_json(output / "stages.json", stages)
            raise
        record.update(
            status="PASS",
            seconds=time.perf_counter() - start,
            cumulative_process_peak_bytes=process_peak_bytes(),
        )
        write_json(output / "stages.json", stages)
        return result

    data = output / "data"
    stage("worlds", lambda: make_worlds(data, 17, worlds))
    train, validation = data / "train.jsonl", data / "validation.jsonl"
    stage(
        "profile-ordinary",
        lambda: train_controlled(train, validation, output / "profile-ordinary", "ordinary", 2),
    )
    stage(
        "profile-recurrent",
        lambda: train_controlled(train, validation, output / "profile-recurrent", "recurrent", 2),
    )
    configurations = [
        ("ordinary", "ordinary", "qa", 4, 32),
        ("recurrent", "recurrent", "qa", 4, 32),
        ("revision", "recurrent", "revision", 4, 32),
        ("no-correction", "recurrent", "no-correction", 4, 32),
        ("no-preservation", "recurrent", "no-preservation", 4, 32),
        ("slots2", "recurrent", "qa", 2, 32),
        ("slots8", "recurrent", "qa", 8, 32),
        ("ordinary-wide", "ordinary", "qa", 4, 40),
    ]
    training = {}
    result_paths = []
    for name, variant, objective, slots, width in configurations:
        run = output / name
        training[name] = stage(
            "train-" + name,
            partial(
                train_controlled,
                train,
                validation,
                run,
                variant,
                steps,
                slots=slots,
                config=ModelConfig(width=width),
                objective=objective,
            ),
        )
        checkpoint = run / "checkpoint.pt"
        stage(
            "eval-" + name,
            partial(
                evaluate_controlled,
                checkpoint,
                validation,
                output / (name + "-write"),
                answer_budget,
            ),
        )
        result_paths.append(output / (name + "-write") / "metrics.json")
        if name not in ("recurrent", "revision"):
            continue
        for split, path in (("train", train), ("validation", validation)):
            stage(
                name + "-labels-" + split,
                partial(
                    paired_labels,
                    checkpoint,
                    path,
                    output / (name + "-labels-" + split),
                    split,
                    limit=worlds,
                    answer_budget=answer_budget,
                ),
            )
        predictor = output / (name + "-effect-model")
        stage(
            name + "-fit-effect",
            partial(fit_effect, output / (name + "-labels-train/labels.json"), predictor, 100),
        )
        stage(
            name + "-effect-metrics",
            partial(
                evaluate_effect,
                predictor / "predictor.pt",
                output / (name + "-labels-validation/labels.json"),
                output / (name + "-effect-eval"),
            ),
        )
        policies = (
            ("predictor",)
            if name == "recurrent"
            else ("predictor", "heuristic", "random", "retain", "reset")
        )
        for policy in policies:
            destination = output / (name + "-" + policy)
            stage(
                "eval-" + destination.name,
                partial(
                    evaluate_controlled,
                    checkpoint,
                    validation,
                    destination,
                    answer_budget,
                    policy,
                    predictor / "predictor.pt" if policy in ("predictor", "heuristic") else None,
                ),
            )
            result_paths.append(destination / "metrics.json")
    results = aggregate(result_paths, EXPECTED_RESULTS)
    profiles = [
        json.loads((output / ("profile-" + name) / "metrics.json").read_text())
        for name in ("ordinary", "recurrent")
    ]
    label_costs = [json.loads(p.read_text())["cost"] for p in output.glob("*-labels-*/labels.json")]
    predictor_costs = [
        json.loads(p.read_text()) for p in output.glob("*-effect-model/metrics.json")
    ]
    results["cost"] = dict(
        total_lm_optimizer_steps=sum(
            r["steps_this_invocation"] for r in [*training.values(), *profiles]
        ),
        train_forward_tokens=sum(
            r["model_input_token_evaluations"] for r in [*training.values(), *profiles]
        ),
        lm_training_seconds=sum(r["training_seconds"] for r in [*training.values(), *profiles]),
        branch_count=sum(r["branches"] for r in label_costs),
        label_forward_tokens=sum(r["label_forward_tokens"] for r in label_costs),
        branch_generated_forward_tokens=sum(r["generation_forward_tokens"] for r in label_costs),
        label_generation_seconds=sum(r["seconds"] for r in label_costs),
        predictor_steps=sum(r["steps"] for r in predictor_costs),
        predictor_training_seconds=sum(r["training_seconds"] for r in predictor_costs),
        failed_stages=[r for r in stages if r["status"] != "PASS"],
        note=(
            "Includes profiles/labels/predictors in this pilot. Earlier test/failed-check costs "
            "are separate check records; no total CPU-hours claim."
        ),
    )
    results.update(
        protocol_sha256=sha256_file(output / "protocol.json"),
        training={
            name: {k: v for k, v in row.items() if k != "losses"} for name, row in training.items()
        },
        elapsed_seconds=time.perf_counter() - started,
        cumulative_peak_process_bytes=process_peak_bytes(),
        status="PARTIAL; bounded validation study, not final matched-resource M6",
        limitations=[
            "one seed",
            "small synthetic worlds",
            "no final test",
            "unequal parameters/FLOPs",
            "additional label/predictor cost",
            "memory reset is an inference distribution shift",
        ],
    )
    write_json(output / "summary.json", results)
    files = {
        p.relative_to(output).as_posix(): sha256_file(p)
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }
    write_json(
        output / "manifest.json",
        dict(protocol=protocol, files=files, package_sha256=package_fingerprint()),
    )
    return dict(
        status=results["status"],
        results=results["results"],
        elapsed_seconds=results["elapsed_seconds"],
        evidence=str(output),
    )
