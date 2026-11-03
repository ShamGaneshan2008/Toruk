"""Replay sealed routing results while binding the files actually consumed."""

import argparse
import json
import time
from pathlib import Path
from typing import Any

import study_routing_v2 as study
import torch

from toruk_lm.integrated_memory import load_integrated
from toruk_lm.integrated_study import file_identity, peak_bytes
from toruk_lm.pooled_router import load_pooled


def declared_digest(files: dict[str, str], path: Path) -> str:
    matches = [digest for name, digest in files.items() if Path(name).resolve() == path.resolve()]
    if len(matches) != 1:
        raise ValueError(f"file is not uniquely declared by the seal: {path}")
    return matches[0]


def require_digest(actual: Path, expected: str) -> None:
    if not actual.is_file() or file_identity(actual) != expected:
        raise ValueError(f"consumed input differs from seal: {actual}")


def bind_run_files(reference: Path, inputs: Path) -> dict[str, Path]:
    """Return consumed files only after comparing them with reference identities."""
    frozen = json.loads((reference / "freeze.json").read_text())
    names = (
        "registration.json",
        "final.json",
        "development/new-31.json",
        "development/new-47.json",
        "train/new-31.pt",
        "train/new-47.pt",
    )
    bound = {}
    for name in names:
        actual = inputs / name
        require_digest(actual, declared_digest(frozen["files"], reference / name))
        bound[name] = actual
    require_digest(inputs / "freeze.json", file_identity(reference / "freeze.json"))
    return bound


def verify_reference_file(reference: Path, path: Path) -> None:
    manifest = json.loads((reference / "manifest.json").read_text())
    name = path.relative_to(reference).as_posix()
    if name not in manifest["files"]:
        raise ValueError(f"reference output is outside package manifest: {name}")
    require_digest(path, manifest["files"][name])


def replay(reference: Path, inputs: Path, output: Path, loads: list[int]) -> dict[str, Any]:
    if output.exists():
        raise ValueError("output already exists; use a fresh replay output")
    # Preserve the original source/metadata checks, then additionally bind actual inputs.
    study.verify_final(reference)
    verify_reference_file(reference, reference / "freeze.json")
    verify_reference_file(reference, reference / "registration.json")
    bound = bind_run_files(reference, inputs)
    registration = json.loads(bound["registration.json"].read_text())
    rows = [r for r in json.loads(bound["final.json"].read_text()) if r["load"] in loads]
    if not rows:
        raise ValueError("no selected worlds")
    selector_path = study.q.SELECTOR
    require_digest(selector_path, declared_digest(registration["files"], selector_path))
    torch.set_num_threads(1)
    started = time.perf_counter()
    replayed: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    differences: list[dict[str, Any]] = []
    for seed in (31, 47):
        for method in study.METHODS:
            path = reference / "raw" / f"{method}-{seed}.json"
            verify_reference_file(reference, path)
            saved = json.loads(path.read_text())
            expected = {(p["id"], p["load"]): p for p in saved["predictions"]}
            checkpoint = (
                bound[f"train/new-{seed}.pt"]
                if method.startswith("new")
                else study.q.checkpoint_for("integrated" if method == "old" else method, seed)
            )
            if not method.startswith("new"):
                require_digest(checkpoint, declared_digest(registration["files"], checkpoint))
            checkpoint_hash = file_identity(checkpoint)
            if checkpoint_hash != saved["checkpoint_sha256"]:
                raise ValueError("loaded checkpoint differs from scored reference checkpoint")
            model, _ = (
                load_pooled(checkpoint) if method.startswith("new") else load_integrated(checkpoint)
            )
            selector = study.q.ChatRelevanceSelector(selector_path) if method == "learned" else None
            mode = (
                "zero"
                if method == "new_zero"
                else "integrated"
                if method in ("old", "new")
                else method
            )
            predictions: list[dict[str, Any]] = []
            for row in rows:
                previous = expected[row["id"], row["load"]]
                texts = [e["text"] for e in row["events"]]
                if len(previous["answers"]) != len(row["questions"]):
                    raise ValueError("reference query count differs")
                answers = []
                for query, old in zip(row["questions"], previous["answers"], strict=True):
                    generated = study.q.infer(
                        model, selector, texts, query["query"], mode, checkpoint_hash
                    )
                    generated.update(query)
                    generated["correct"] = generated["answer"] == query["expected"]
                    generated["unsupported"] = (
                        query["expected"] == "?" and generated["answer"] != "?"
                    )
                    keys = (
                        "answer",
                        "generated_ids",
                        "query",
                        "expected",
                        "correct",
                        "unsupported",
                        "selected_record_ids",
                        "suffix_record_ids",
                        "history_tokens_scanned",
                        "selected_tokens",
                        "update_tokens",
                        "forward_positions",
                        "update_cells",
                        "allocated_state_bytes",
                        "effective_state_bytes",
                    )
                    changed = [key for key in keys if generated[key] != old[key]]
                    if method in ("old", "new", "new_zero"):
                        writes, read = study.routes(model, texts, query["query"])
                        if writes != old["write_predictions"] or read != old["read_predicted"]:
                            changed.append("diagnostic_routes")
                    if changed:
                        differences.append(
                            {
                                "method": method,
                                "seed": seed,
                                "id": row["id"],
                                "load": row["load"],
                                "query": query["query"],
                                "fields": changed,
                            }
                        )
                    answers.append(generated)
                predictions.append(
                    {k: row[k] for k in ("id", "category", "eval_seed", "load")}
                    | {"answers": answers, "correct": all(a["correct"] for a in answers)}
                )
            totals = {
                str(load): study.q.summarize([p for p in predictions if p["load"] == load])
                for load in loads
            }
            cells.append(
                {
                    "method": method,
                    "seed": seed,
                    "checkpoint_sha256": checkpoint_hash,
                    "worlds": len(predictions),
                    "totals": totals,
                }
            )
            replayed.append({"method": method, "seed": seed, "predictions": predictions})
            print(
                method,
                seed,
                "worlds",
                len(predictions),
                "exact parity so far",
                not differences,
                flush=True,
            )
    result = {
        "status": "PASS" if not differences else "FAIL",
        "reference": str(reference),
        "inputs": str(inputs),
        "loads": loads,
        "reference_freeze_sha256": file_identity(reference / "freeze.json"),
        "actual_dataset_sha256": file_identity(bound["final.json"]),
        "cells": cells,
        "world_predictions": sum(len(r["predictions"]) for r in replayed),
        "answers": sum(len(p["answers"]) for r in replayed for p in r["predictions"]),
        "differences": differences,
        "seconds": time.perf_counter() - started,
        "process_high_water_bytes": peak_bytes(),
        "replayed": replayed,
    }
    study.q.dump(output, result)
    if differences:
        raise ValueError(
            f"replay differs from frozen reference in {len(differences)} answers; output retained"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sealed-run", type=Path, required=True)
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--loads", type=int, choices=(0, 8, 32), nargs="+", default=[0])
    args = parser.parse_args()
    replay(args.sealed_run, args.inputs or args.sealed_run, args.output, sorted(set(args.loads)))


if __name__ == "__main__":
    main()
