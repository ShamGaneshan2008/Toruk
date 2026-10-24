"""Frozen-checkpoint exploratory failure studies; no fitting or final M6 test access."""

import ast
import copy
import json
import math
import os
import platform
import statistics
import time
import zipfile
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

import torch

from toruk_lm.comparisons import EXPECTED_RESULTS, process_peak_bytes
from toruk_lm.controlled import evaluate_controlled, package_fingerprint
from toruk_lm.data import sha256_file, write_json
from toruk_lm.tokenizer import ByteTokenizer
from toruk_lm.worlds import (
    SCHEMA,
    SPLITS,
    TEMPLATES,
    dataset_identity,
    load_worlds,
    make_world,
    oracle,
    render,
    summarize,
)

KNOWN_GROUPS = ("corrected", "unchanged_entity", "unrelated_date", "unrelated_number")
KERNEL_FILES = (
    "controlled.py",
    "model.py",
    "recurrent.py",
    "tokenizer.py",
    "effect_predictor.py",
    "engine.py",
)
METHODS = {
    "templates": (
        "ordinary-write",
        "recurrent-write",
        "revision-write",
        "revision-predictor",
        "revision-heuristic",
    ),
    "load": (
        "ordinary-write",
        "recurrent-write",
        "slots2-write",
        "slots8-write",
        "revision-write",
        "revision-predictor",
    ),
}
CELLS = {
    "control": dict(template=2, extra=0, density="none"),
    "template4": dict(template=4, extra=0, density="none"),
    "template5": dict(template=5, extra=0, density="none"),
    "claims4": dict(template=2, extra=4, density="claims"),
    "claims12": dict(template=2, extra=12, density="claims"),
    "facts4": dict(template=2, extra=4, density="facts"),
    "facts12": dict(template=2, extra=12, density="facts"),
}


def kernel_identity() -> dict[str, str]:
    return {name: sha256_file(Path(__file__).parent / name) for name in KERNEL_FILES}


class Journal:
    def __init__(self, output: Path, seconds: float) -> None:
        self.output, self.seconds = output, seconds
        self.started = time.perf_counter()
        self.records: list[dict[str, Any]] = []

    def run(self, label: str, call: Callable[[], Any]) -> Any:
        record: dict[str, Any] = dict(stage=label, status="RUNNING")
        self.records.append(record)
        if time.perf_counter() - self.started >= self.seconds:
            record.update(status="BLOCKED", reason="elapsed study budget")
            write_json(self.output / "stages.json", self.records)
            raise TimeoutError("study budget exhausted")
        write_json(self.output / "stages.json", self.records)
        start = time.perf_counter()
        try:
            value = call()
        except Exception as error:
            record.update(status="FAIL", error=repr(error), seconds=time.perf_counter() - start)
            write_json(self.output / "stages.json", self.records)
            raise
        record.update(
            status="PASS",
            seconds=time.perf_counter() - start,
            cumulative_process_peak_bytes=process_peak_bytes(),
        )
        write_json(self.output / "stages.json", self.records)
        return value


def fresh(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh study directory")
    output.mkdir(parents=True, exist_ok=True)


def check_kernel(expected: dict[str, str]) -> None:
    if expected != kernel_identity():
        raise ValueError("frozen model/scoring kernel mismatch")


def parent_integrity(parent: Path, handoff: Path) -> dict[str, Any]:
    snapshot = json.loads((handoff / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in kernel_identity().items():
        if snapshot["source_files"]["src/toruk_lm/" + name] != digest:
            raise ValueError("M6 inference/scoring source mismatch")
    archive = handoff / "source.zip"
    stored = [
        h for p, h in snapshot["evidence_sha256"].items() if p.endswith("m6-handoff/source.zip")
    ]
    if stored != [sha256_file(archive)]:
        raise ValueError("M6 source archive mismatch")
    with zipfile.ZipFile(archive) as source:
        old = ast.parse(source.read("src/toruk_lm/worlds.py").decode("utf-8"))
    current = ast.parse((Path(__file__).parent / "worlds.py").read_text(encoding="utf-8"))
    for name in (
        "oracle",
        "question",
        "render",
        "make_world",
        "observed",
        "summarize",
        "ObservedPrompt",
    ):
        left = next(node for node in old.body if getattr(node, "name", None) == name)
        right = next(node for node in current.body if getattr(node, "name", None) == name)
        if ast.dump(left) != ast.dump(right):
            raise ValueError("M6 world/scoring semantics changed")
    original_templates = next(
        ast.literal_eval(node.value)
        for node in old.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "TEMPLATES" for t in node.targets)
    )
    if tuple(TEMPLATES[: len(original_templates)]) != original_templates:
        raise ValueError("original rendering templates changed")
    manifest = json.loads((parent / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        if sha256_file(parent / name) != digest:
            raise ValueError("stale/corrupt M6 artifact: " + name)
    summary = json.loads((parent / "summary.json").read_text(encoding="utf-8"))
    if set(summary["results"]) != EXPECTED_RESULTS:
        raise ValueError("incomplete M6 comparison")
    protocol = json.loads((parent / "protocol.json").read_text(encoding="utf-8"))
    if protocol["final_test"] != "closed" or protocol["seed"] != 23:
        raise ValueError("unsupported M6 protocol/test access")
    return summary


def model_bindings(parent: Path, summary: dict[str, Any]) -> dict[str, Any]:
    bindings = {}
    for name in sorted(summary["results"]):
        model_name, policy = name.rsplit("-", 1)
        checkpoint = f"{model_name}/checkpoint.pt"
        predictor = (
            f"{model_name}-effect-model/predictor.pt"
            if policy in ("predictor", "heuristic")
            else None
        )
        bindings[name] = dict(
            checkpoint=checkpoint,
            checkpoint_sha256=sha256_file(parent / checkpoint),
            predictor=predictor,
            predictor_sha256=sha256_file(parent / predictor) if predictor else None,
            policy=policy,
            training=summary["training"][model_name],
        )
    return bindings


def verify_binding(parent: Path, binding: dict[str, Any]) -> None:
    if sha256_file(parent / binding["checkpoint"]) != binding["checkpoint_sha256"]:
        raise ValueError("checkpoint identity mismatch")
    if (
        binding["predictor"]
        and sha256_file(parent / binding["predictor"]) != binding["predictor_sha256"]
    ):
        raise ValueError("predictor identity mismatch")


def replay_one(parent: Path, output: Path, name: str, binding: dict[str, Any]) -> dict[str, Any]:
    verify_binding(parent, binding)
    before = json.loads((parent / name / "predictions.json").read_text(encoding="utf-8"))
    old_metrics = json.loads((parent / name / "metrics.json").read_text(encoding="utf-8"))
    metrics = evaluate_controlled(
        parent / binding["checkpoint"],
        parent / "data/validation.jsonl",
        output / name,
        16,
        binding["policy"],
        parent / binding["predictor"] if binding["predictor"] else None,
    )
    after = json.loads((output / name / "predictions.json").read_text(encoding="utf-8"))
    keys = ("world_id", "group", "question", "generated_ids", "answer", "gold", "correct")
    if [{k: p[k] for k in keys} for p in before] != [
        {k: p[k] for k in keys} for p in after
    ] or metrics["groups"] != old_metrics["groups"]:
        raise ValueError("M6 generated-answer reproduction mismatch")
    return dict(
        status="PASS",
        answers=len(after),
        inference_seconds=metrics["inference_seconds"],
        inference_forward_tokens=metrics["inference_forward_tokens"],
        scoring_forward_tokens=metrics["scoring_forward_tokens"],
    )


def verify_m6(parent: Path, handoff: Path, output: Path, seconds: float = 110) -> dict[str, Any]:
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("invalid replay budget")
    fresh(output)
    journal = Journal(output, seconds)
    summary = journal.run("parent-integrity", partial(parent_integrity, parent, handoff))
    bindings = model_bindings(parent, summary)
    write_json(
        output / "protocol.json",
        dict(
            parent_manifest_sha256=sha256_file(parent / "manifest.json"),
            kernel=kernel_identity(),
            models=bindings,
            package_sha256=package_fingerprint(),
            seconds=seconds,
        ),
    )
    results = {}
    for name, binding in bindings.items():
        results[name] = journal.run(name, partial(replay_one, parent, output, name, binding))
    record = dict(
        status="PASS",
        comparisons=len(results),
        results=results,
        parent_manifest_sha256=sha256_file(parent / "manifest.json"),
        parent_protocol_sha256=sha256_file(parent / "protocol.json"),
        parent_data={
            s: dataset_identity(parent / f"data/{s}.jsonl") for s in ("train", "validation")
        },
        kernel=kernel_identity(),
        bindings=bindings,
        original_world_semantics="PASS",
        package_sha256=package_fingerprint(),
        elapsed_seconds=time.perf_counter() - journal.started,
        inherited_cost=summary["cost"],
        M6_status=summary["status"],
        final_test="NOT_RUN; hashes only, no final-test scoring",
    )
    write_json(output / "verification.json", record)
    return dict(
        status="PASS",
        comparisons=len(results),
        answers=sum(r["answers"] for r in results.values()),
        elapsed_seconds=record["elapsed_seconds"],
        evidence=str(output),
    )


def known_values(row: dict[str, Any]) -> tuple[str, ...]:
    values = {p["group"]: p["answer"] for p in row["probes"]}
    return tuple(values[g] for g in KNOWN_GROUPS)


def check_holdout(row: dict[str, Any], forbidden: list[dict[str, Any]]) -> None:
    entities = {e["entity"] for e in row["events"]}
    for old in forbidden:
        if row["id"] == old["id"] or entities & {e["entity"] for e in old["events"]}:
            raise ValueError("held-out entity/world overlap")
        differences = sum(a != b for a, b in zip(known_values(row), known_values(old), strict=True))
        if differences < 2:
            raise ValueError("near-duplicate held-out answer combination")


def shift_world(seed: int, index: int, cell: str, spec: dict[str, Any]) -> dict[str, Any]:
    row = copy.deepcopy(make_world(seed, "validation", index))
    row.update(
        id=f"m7-{seed}-{index}-{cell}",
        anchor_id=f"m7-{seed}-{index}",
        data_seed=seed,
        anchor_index=index,
        evaluation_partition="m7-held-out",
        template=spec["template"],
        shift=dict(cell=cell, **spec),
    )
    for i in range(spec["extra"]):
        entity = f"g{seed}{index}{i}"
        row["events"].append(
            dict(
                kind="SET" if spec["density"] == "facts" else "CLAIM",
                entity="fx" + entity if spec["density"] == "facts" else entity,
                attribute="count",
                value=str((seed + i) % 10),
            )
        )
    row["distractors"] += spec["extra"]
    row["history"] = render(row["events"], row["template"])
    if any(
        p["answer"] != oracle(row["events"], p["entity"], p["attribute"]) for p in row["probes"]
    ):
        raise ValueError("shift changed a probe truth")
    if 1 + len(ByteTokenizer().encode(row["history"])) > 2048:
        raise ValueError("held-out history exceeds frozen segment budget")
    return row


def build_data(
    protocol: dict[str, Any], protocol_path: Path, output: Path, forbidden: list[dict[str, Any]]
) -> dict[str, Path]:
    paths = {}
    for cell, spec in protocol["cells"].items():
        rows = []
        for seed, index in protocol["anchors"]:
            row = shift_world(seed, index, cell, spec)
            check_holdout(row, forbidden)
            rows.append(row)
        directory = output / cell
        fresh(directory)
        data = directory / "validation.jsonl"
        data.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
        )
        manifest = dict(
            schema=SCHEMA,
            purpose="M7-held-out",
            evaluation_only=True,
            protocol_sha256=sha256_file(protocol_path),
            cell=cell,
            shift=spec,
            package_sha256=package_fingerprint(),
            splits={},
        )
        for split in SPLITS:
            manifest["splits"][split] = dict(
                ids=[r["id"] for r in rows] if split == "validation" else [],
                worlds=len(rows) if split == "validation" else 0,
                sha256=sha256_file(data) if split == "validation" else None,
            )
        write_json(directory / "manifest.json", manifest)
        paths[cell] = data
    for level in (4, 12):
        if f"facts{level}" in paths:
            facts = load_worlds(paths[f"facts{level}"], "validation")
            claims = load_worlds(paths[f"claims{level}"], "validation")
            if [len(ByteTokenizer().encode(r["history"])) for r in facts] != [
                len(ByteTokenizer().encode(r["history"])) for r in claims
            ]:
                raise ValueError("density contrast is not byte-length matched")
    return paths


def checked_data(data: Path, protocol_path: Path) -> list[dict[str, Any]]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    check_kernel(protocol["kernel"])
    manifest = json.loads((data.parent / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("purpose") != "M7-held-out"
        or not manifest.get("evaluation_only")
        or manifest["protocol_sha256"] != sha256_file(protocol_path)
        or manifest["package_sha256"] != package_fingerprint()
        or protocol["package_sha256"] != package_fingerprint()
    ):
        raise ValueError("stale/mismatched study protocol or dataset manifest")
    cell = manifest["cell"]
    spec = protocol["cells"][cell]
    if manifest["shift"] != spec:
        raise ValueError("shift configuration mismatch")
    rows = load_worlds(data, "validation")
    expected = [shift_world(seed, index, cell, spec) for seed, index in protocol["anchors"]]
    if rows != expected:
        raise ValueError("held-out transformation/anchor mismatch")
    return rows


def quality(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    result = summarize(predictions)
    result["primary"] = sum(result["groups"][g]["accuracy"] for g in KNOWN_GROUPS) / 4
    return result


def describe(predictions: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(predictions) != 6 * len(rows):
        raise ValueError("missing held-out predictions")
    lookup = {r["id"]: r for r in rows}
    seen = set()
    per_seed: dict[int, list[dict[str, Any]]] = {}
    strata: dict[str, dict[str, list[dict[str, Any]]]] = {}
    stale, uncertain_errors = 0, 0
    examples: list[dict[str, Any]] = []
    for p in predictions:
        key = p["world_id"], p["question"]
        if key in seen:
            raise ValueError("duplicate held-out world/question prediction")
        seen.add(key)
        row = lookup[p["world_id"]]
        probe = next(q for q in row["probes"] if q["question"] == p["question"])
        if (
            p["group"] != probe["group"]
            or p["gold"] != probe["answer"]
            or p["correct"] != (p["answer"] == p["gold"])
            or p["history_tokens"] != len(ByteTokenizer().encode(row["history"])) + 1
        ):
            raise ValueError("held-out scoring/label mismatch")
        per_seed.setdefault(row["data_seed"], []).append(p)
        relevant = [
            (i, e)
            for i, e in enumerate(row["events"])
            if e["entity"] == probe["entity"]
            and e["attribute"] == probe["attribute"]
            and e["kind"] in ("SET", "FIX", "CONFLICT")
        ]
        distance = (
            None
            if not relevant
            else len(
                ByteTokenizer().encode(
                    "".join(
                        TEMPLATES[row["template"]].format(**e)
                        for e in row["events"][relevant[-1][0] + 1 :]
                    )
                )
            )
        )
        keys = {(e["entity"], e["attribute"]) for e in row["events"] if e["kind"] in ("SET", "FIX")}
        count = sum(oracle(row["events"], *key) != "?" for key in keys)
        dimensions = dict(
            history_tokens=p["history_tokens"],
            known_facts=count,
            evidence_distance_tokens=distance,
            distractors=row["distractors"],
            corrections=row["corrections"],
        )
        for dimension, value in dimensions.items():
            strata.setdefault(dimension, {}).setdefault(str(value), []).append(p)
        obsolete = {
            e["value"]
            for _, e in relevant
            if e["kind"] in ("SET", "FIX") and e["value"] != probe["answer"]
        }
        stale += int(not p["correct"] and p["answer"] in obsolete)
        uncertain_errors += int(
            probe["group"] in ("unknown", "ambiguous")
            and p["answer"] not in ("", "?")
            and not p["correct"]
        )
        if not p["correct"] and len(examples) < 6:
            examples.append(
                dict(
                    world_id=row["id"],
                    group=p["group"],
                    answer=p["answer"],
                    gold=p["gold"],
                    evidence_distance_tokens=distance,
                )
            )
    seed_results = {str(seed): quality(values) for seed, values in per_seed.items()}
    primary = [r["primary"] for r in seed_results.values()]

    def stratum(values: list[dict[str, Any]]) -> dict[str, Any]:
        known = [p for p in values if p["group"] in KNOWN_GROUPS]
        return dict(
            examples=len(values),
            correct=sum(p["correct"] for p in values),
            known_examples=len(known),
            known_correct=sum(p["correct"] for p in known),
        )

    return dict(
        **quality(predictions),
        per_data_seed=seed_results,
        data_seed_mean=statistics.mean(primary),
        data_seed_sample_sd=statistics.stdev(primary) if len(primary) > 1 else None,
        training_seed_sd=None,
        strata={
            dim: {v: stratum(items) for v, items in bins.items()} for dim, bins in strata.items()
        },
        matches_superseded_value=stale,
        nonabstaining_uncertain_errors=uncertain_errors,
        failure_examples=examples,
    )


def evaluate_cell(
    parent: Path, binding: dict[str, Any], data: Path, protocol: Path, output: Path
) -> dict[str, Any]:
    rows = checked_data(data, protocol)
    verify_binding(parent, binding)
    metrics = evaluate_controlled(
        parent / binding["checkpoint"],
        data,
        output,
        16,
        binding["policy"],
        parent / binding["predictor"] if binding["predictor"] else None,
    )
    if metrics["config"] != binding["training"]["config"]:
        raise ValueError("checkpoint configuration mismatch")
    predictions = json.loads((output / "predictions.json").read_text(encoding="utf-8"))
    analysis = describe(predictions, rows)
    if analysis["groups"] != metrics["groups"]:
        raise ValueError("metric aggregation mismatch")
    context = metrics["config"]["model"]["context"]
    recurrent = metrics["config"]["variant"] == "recurrent"
    history_calls = sum(math.ceil((len(r["history"].encode()) + 1) / context) for r in rows)
    generation_calls = sum(
        math.ceil(len(p["question"].encode()) / context)
        + len(p["generated_ids"])
        - int(p["generated_ids"][-1] == 2)
        if recurrent
        else len(p["generated_ids"])
        for p in predictions
    )
    scoring_calls = sum(
        math.ceil((len((p["question"] + p["gold"] + "\n").encode()) - 1) / context)
        if recurrent
        else len((p["gold"] + "\n").encode())
        for p in predictions
    )
    analysis["resources"] = dict(
        derived_inference_forward_calls=history_calls + generation_calls,
        derived_offline_scoring_forward_calls=scoring_calls,
        derived_memory_proposals=(history_calls + generation_calls + scoring_calls)
        if recurrent
        else 0,
        inference_seconds=metrics["inference_seconds"],
        model_load_seconds=metrics["model_load_seconds"],
        history_tokens_including_bos=metrics["observed_history_tokens"],
        question_tokens=metrics["question_tokens"],
        generated_tokens=metrics["generated_tokens"],
        inference_forward_tokens=metrics["inference_forward_tokens"],
        offline_answer_forward_tokens=metrics["scoring_forward_tokens"],
        forwarded_positions_per_second=metrics["inference_forward_tokens"]
        / metrics["inference_seconds"],
        model_parameters=binding["training"]["parameters"],
        memory_state_bytes=binding["training"]["memory_state_bytes"],
        active_predictor_parameters=metrics["active_predictor_parameters"],
        predictor_fallbacks=metrics["predictor_fallbacks"],
        final_boundaries=metrics["final_boundaries"],
        final_boundary_writes=metrics["final_boundary_writes"],
        history_lm_loss=metrics["history_lm_loss"],
        teacher_forced_answer_loss=metrics["teacher_forced_answer_loss"],
    )
    write_json(output / "analysis.json", analysis)
    write_json(
        output / "bindings.json",
        dict(
            protocol_sha256=sha256_file(protocol),
            data=dataset_identity(data),
            model=binding,
            package_sha256=package_fingerprint(),
        ),
    )
    return analysis


def run_study(
    parent: Path,
    verification: Path,
    output: Path,
    study: str,
    worlds_per_seed: int = 2,
    seconds: float = 110,
) -> dict[str, Any]:
    if (
        study not in METHODS
        or not 1 <= worlds_per_seed <= 2
        or not math.isfinite(seconds)
        or seconds <= 0
    ):
        raise ValueError("invalid bounded study configuration")
    verified = json.loads(verification.read_text(encoding="utf-8"))
    if (
        verified["status"] != "PASS"
        or verified["comparisons"] != 14
        or set(verified["results"]) != EXPECTED_RESULTS
        or any(r["status"] != "PASS" for r in verified["results"].values())
        or verified["parent_manifest_sha256"] != sha256_file(parent / "manifest.json")
        or verified["parent_protocol_sha256"] != sha256_file(parent / "protocol.json")
        or verified["parent_data"]
        != {s: dataset_identity(parent / f"data/{s}.jsonl") for s in ("train", "validation")}
    ):
        raise ValueError("stale/unverified M6 prerequisite")
    check_kernel(verified["kernel"])
    fresh(output)
    cells = (
        ("control", "template4", "template5")
        if study == "templates"
        else ("control", "claims4", "claims12", "facts4", "facts12")
    )
    methods = METHODS[study]
    protocol = dict(
        schema="m7-failures-v1",
        study=study,
        cells={c: CELLS[c] for c in cells},
        methods={m: verified["bindings"][m] for m in methods},
        anchors=[
            (seed, 40 + 10 * i + j)
            for i, seed in enumerate((117, 118))
            for j in range(worlds_per_seed)
        ],
        data_seeds=[117, 118],
        training_seeds=[23],
        answer_budget=16,
        kernel=kernel_identity(),
        package_sha256=package_fingerprint(),
        verification_sha256=sha256_file(verification),
        parent_manifest_sha256=sha256_file(parent / "manifest.json"),
        final_test="closed",
        new_training_steps=0,
        seconds=seconds,
        primary="M6 four-group macro exact accuracy; paired change vs control",
        boundary_gate="control primary >=0.5; otherwise onset/capacity unidentifiable",
        inherited_M6_cost=verified["inherited_cost"],
    )
    protocol_path = output / "protocol.json"
    write_json(protocol_path, protocol)
    write_json(
        output / "hardware.json",
        dict(
            python=platform.python_version(),
            platform=platform.platform(),
            processor=platform.processor(),
            logical_cpus=os.cpu_count(),
            torch=str(torch.__version__),
            cuda_available=torch.cuda.is_available(),
            training_device="cpu",
            threads=1,
        ),
    )
    journal = Journal(output, seconds)
    forbidden = load_worlds(parent / "data/train.jsonl", "train") + load_worlds(
        parent / "data/validation.jsonl", "validation"
    )
    paths = journal.run(
        "frozen-data", partial(build_data, protocol, protocol_path, output / "data", forbidden)
    )
    results: dict[str, dict[str, Any]] = {}
    for cell, data in paths.items():
        results[cell] = {}
        for method in methods:
            results[cell][method] = journal.run(
                cell + "/" + method,
                partial(
                    evaluate_cell,
                    parent,
                    protocol["methods"][method],
                    data,
                    protocol_path,
                    output / cell / method,
                ),
            )
    comparisons: dict[str, dict[str, Any]] = {}
    for cell in cells:
        if cell == "control":
            continue
        comparisons[cell] = {}
        for method in methods:
            before, after = results["control"][method], results[cell][method]
            comparisons[cell][method] = dict(
                delta_primary=after["primary"] - before["primary"],
                control_primary=before["primary"],
                shifted_primary=after["primary"],
                per_data_seed_delta={
                    seed: after["per_data_seed"][seed]["primary"] - value["primary"]
                    for seed, value in before["per_data_seed"].items()
                },
                boundary_status="UNIDENTIFIABLE_AT_FLOOR"
                if before["primary"] < 0.5
                else "EXPLORATORY",
                generalization_claim="UNSUPPORTED; M6 positive quality prerequisite absent",
            )
    summary = dict(
        status="PARTIAL; exploratory failure study only",
        study=study,
        results=results,
        comparisons=comparisons,
        elapsed_seconds=time.perf_counter() - journal.started,
        cumulative_process_peak_bytes=process_peak_bytes(),
        new_training_steps=0,
        final_test="NOT_RUN",
        training_seed_uncertainty=None,
        protocol_sha256=sha256_file(protocol_path),
        package_sha256=package_fingerprint(),
    )
    write_json(output / "summary.json", summary)
    hashes = {
        p.relative_to(output).as_posix(): sha256_file(p)
        for p in sorted(output.rglob("*"))
        if p.is_file() and p != output / "manifest.json"
    }
    write_json(
        output / "manifest.json",
        dict(
            files=hashes,
            protocol_sha256=sha256_file(protocol_path),
            package_sha256=package_fingerprint(),
        ),
    )
    return dict(
        status=summary["status"],
        study=study,
        evaluations=len(cells) * len(methods),
        answers=sum(r["examples"] for values in results.values() for r in values.values()),
        elapsed_seconds=summary["elapsed_seconds"],
        evidence=str(output),
    )
