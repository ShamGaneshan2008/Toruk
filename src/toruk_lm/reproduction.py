"""Bounded ordinary-LM reproduction and checked result regeneration."""

import csv
import json
import math
import platform
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from toruk_lm.data import (
    make_fixture,
    read_documents,
    sha256_file,
    training_batch,
    windows,
    write_json,
)
from toruk_lm.engine import (
    TrainConfig,
    evaluate,
    evaluate_loss,
    load_checkpoint,
    load_model,
    setup,
    train,
)
from toruk_lm.model import ModelConfig, generate
from toruk_lm.tokenizer import ByteTokenizer
from toruk_lm.validation import read_config, read_object, validate


def package_sources() -> dict[str, str]:
    return {path.name: sha256_file(path) for path in sorted(Path(__file__).parent.glob("*.py"))}


def fresh_output(path: Path) -> None:
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError("use a fresh output directory to preserve existing results")


def verify_training_metrics(
    run: Path, fitted: dict[str, Any], saved: dict[str, Any]
) -> tuple[int, float]:
    """Derive target accounting; validate stored observations without re-timing them."""
    steps = fitted.get("steps_this_invocation")
    if type(steps) is not int or not 0 < steps <= saved["next_step"]:
        raise ValueError("invalid training invocation step count")
    start = saved["next_step"] - steps
    examples = windows(read_documents(run / "data/train.jsonl"), saved["model_config"]["context"])
    config = saved["train_config"]
    expected_targets = 0
    for step in range(start, saved["next_step"]):
        _, targets = training_batch(examples, step, config["batch_size"], config["seed"])
        expected_targets += int(targets.ne(-100).sum().item())
    if (
        type(fitted.get("train_valid_tokens_this_invocation")) is not int
        or fitted["train_valid_tokens_this_invocation"] != expected_targets
    ):
        raise ValueError("training target count disagrees with data and deterministic schedule")

    def positive_observation(value: Any, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"invalid training metric {name}: expected finite positive number")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"invalid training metric {name}: expected finite positive number")
        return float(value)

    seconds = positive_observation(fitted.get("training_seconds"), "training_seconds")
    throughput = positive_observation(
        fitted.get("train_tokens_per_second"), "train_tokens_per_second"
    )
    if not math.isclose(throughput, expected_targets / seconds, rel_tol=1e-9):
        raise ValueError("training throughput disagrees with targets and saved duration")
    losses = fitted.get("losses")
    if not isinstance(losses, list) or len(losses) != steps:
        raise ValueError("training loss records disagree with invocation step count")
    for step, row in enumerate(losses, start=start + 1):
        if not isinstance(row, dict) or row.get("step") != step:
            raise ValueError("training loss record step mismatch")
        for key in ("loss", "gradient_norm"):
            value = row.get(key)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"invalid training loss record: {key}")
    return expected_targets, seconds


def reproduce(
    output: Path,
    config: Path | None = None,
    steps: int = 2,
    documents: int = 10,
    data_seed: int = 17,
    max_new_tokens: int = 8,
) -> dict[str, Any]:
    fresh_output(output)
    if steps <= 0 or max_new_tokens <= 0:
        raise ValueError("steps and max_new_tokens must be positive")
    model, training = read_config(config) if config else (ModelConfig(), TrainConfig())
    make_fixture(output / "data", data_seed, documents)
    write_json(output / "config.json", {"model": asdict(model), "training": asdict(training)})
    manifest = output / "data/manifest.json"
    validate(manifest, output / "config.json")
    train(
        output / "data/train.jsonl",
        output / "data/validation.jsonl",
        output / "train",
        model,
        training,
        steps,
    )
    checkpoint = output / "train/checkpoint.pt"
    validate(manifest, output / "config.json", checkpoint)
    evaluate(checkpoint, output / "data/validation.jsonl", output / "eval", max_new_tokens)
    reloaded = load_model(checkpoint)
    tokens = generate(reloaded, [1, *ByteTokenizer().encode("Field journal")], max_new_tokens)
    write_json(
        output / "generation.json",
        {"prompt": "Field journal", "ids": tokens, "generated": ByteTokenizer().decode(tokens)},
    )
    record = {
        "format": "toruk-foundation-run-v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "package_version": version("toruk-lm"),
        "package_sources": package_sources(),
        "environment": {
            "python": platform.python_version(),
            "torch": version("torch"),
            "platform": platform.platform(),
        },
        "parameters": {
            "steps": steps,
            "documents": documents,
            "data_seed": data_seed,
            "max_new_tokens": max_new_tokens,
        },
        "test_split": "integrity checked only; not model scored or used for tuning",
        "artifacts": {
            path.relative_to(output).as_posix(): sha256_file(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    write_json(output / "manifest.json", record)
    return summarize(output, output / "summary")


def summarize(run: Path, output: Path) -> dict[str, Any]:
    fresh_output(output)
    setup(23, 1)
    manifest = read_object(run / "manifest.json")
    if manifest.get("format") != "toruk-foundation-run-v1":
        raise ValueError("unsupported run manifest format")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, dict) or any(
        type(parameters.get(key)) is not int or parameters[key] <= 0
        for key in ("steps", "documents", "max_new_tokens")
    ):
        raise ValueError(
            "run parameters require positive integer steps, documents and max_new_tokens"
        )
    artifacts = manifest.get("artifacts")
    required = {
        "config.json",
        "data/manifest.json",
        "data/train.jsonl",
        "data/validation.jsonl",
        "data/test.jsonl",
        "train/checkpoint.pt",
        "train/config.json",
        "train/metrics.json",
        "eval/metrics.json",
        "eval/predictions.json",
        "generation.json",
    }
    if not isinstance(artifacts, dict) or not required <= artifacts.keys():
        raise ValueError("run manifest is missing required artifacts")
    for name, expected in artifacts.items():
        path = run / name
        if not path.resolve().is_relative_to(run.resolve()):
            raise ValueError("run artifact path must remain inside run directory")
        if sha256_file(path) != expected:
            raise ValueError(f"stale run manifest: artifact checksum mismatch: {name}")
    if manifest.get("package_sources") != package_sources():
        raise ValueError("run package source mismatch; use the recorded source or wheel")
    checkpoint = run / "train/checkpoint.pt"
    validate(run / "data/manifest.json", run / "config.json", checkpoint)
    saved = load_checkpoint(checkpoint)
    data_manifest = read_object(run / "data/manifest.json")
    if (
        parameters["steps"] != saved["next_step"]
        or parameters.get("data_seed") != data_manifest.get("seed")
        or parameters["documents"]
        != sum(spec["documents"] for spec in data_manifest["splits"].values())
    ):
        raise ValueError("run parameters disagree with checkpoint or dataset manifest")
    fitted, scored = read_object(run / "train/metrics.json"), read_object(run / "eval/metrics.json")
    for key in ("model_config", "train_config", "datasets"):
        if fitted.get(key) != saved[key]:
            raise ValueError(f"training metrics {key} disagree with checkpoint")
    if fitted.get("steps_completed") != saved["next_step"]:
        raise ValueError("training metrics steps disagree with checkpoint")
    training_targets, training_seconds = verify_training_metrics(run, fitted, saved)
    if read_object(run / "train/config.json") != read_object(run / "config.json"):
        raise ValueError("run and training configs disagree")
    if scored.get("checkpoint_sha256") != sha256_file(checkpoint):
        raise ValueError("evaluation checkpoint identity mismatch")
    if scored.get("dataset_sha256") != saved["datasets"]["validation"]:
        raise ValueError("evaluation split identity mismatch")
    rescored = evaluate_loss(load_model(checkpoint), run / "data/validation.jsonl")
    if scored.get("valid_tokens") != rescored["valid_tokens"] or not math.isclose(
        scored["loss_nats_per_byte_or_eos"],
        rescored["loss_nats_per_byte_or_eos"],
        rel_tol=1e-6,
        abs_tol=1e-6,
    ):
        raise ValueError("saved evaluation loss disagrees with checkpoint rescore")
    predictions = json.loads((run / "eval/predictions.json").read_text(encoding="utf-8"))
    rows = read_documents(run / "data/validation.jsonl")
    if not isinstance(predictions, list) or len(predictions) != len(rows):
        raise ValueError("prediction count disagrees with validation split")
    tokens, seconds = 0, 0.0
    model = load_model(checkpoint)
    tokenizer = ByteTokenizer()
    parameter_count = sum(p.numel() for p in model.parameters())
    if fitted.get("parameters") != parameter_count or fitted.get("recurrent_state_bytes") != 0:
        raise ValueError("training model resource counts disagree with checkpoint")
    for prediction, row in zip(predictions, rows, strict=True):
        prefix = row["text"][: len(row["text"]) // 2]
        if not isinstance(prediction, dict) or (
            prediction.get("id") != row["id"]
            or prediction.get("prefix") != prefix
            or prediction.get("reference_suffix") != row["text"][len(prefix) :]
        ):
            raise ValueError("prediction identity/prefix/reference mismatch")
        generated = generate(
            model, [1, *tokenizer.encode(prefix)], manifest["parameters"]["max_new_tokens"]
        )
        history_tokens = len(tokenizer.encode(prefix)) + 1
        if prediction.get("observed_history_tokens") != history_tokens or prediction.get(
            "retained_context_tokens"
        ) != min(history_tokens, model.config.context):
            raise ValueError("prediction context accounting mismatch")
        if prediction.get("generated_ids") != generated or prediction.get(
            "generated"
        ) != tokenizer.decode(generated):
            raise ValueError("prediction disagrees with checkpoint generation")
        duration = prediction.get("end_to_end_seconds")
        if (
            isinstance(duration, bool)
            or not isinstance(duration, (float, int))
            or not math.isfinite(duration)
            or duration <= 0
        ):
            raise ValueError("invalid saved prediction timing")
        tokens += len(generated)
        seconds += duration
    if (
        scored["generation"]["generated_tokens"] != tokens
        or scored["generation"]["examples"] != len(rows)
        or scored["generation"]["end_to_end_seconds"] != seconds
    ):
        raise ValueError("generation aggregates disagree with raw predictions")
    summary = {
        "scope": "ordinary-LM smoke fixture; no factual or memory claim",
        "parameters": parameter_count,
        "steps": saved["next_step"],
        "training_targets": training_targets,
        "validation_loss_nats_per_byte_or_eos": rescored["loss_nats_per_byte_or_eos"],
        "validation_targets": rescored["valid_tokens"],
        "generated_tokens": tokens,
        "saved_generation_seconds": seconds,
        "saved_mean_generation_ms": seconds * 1000 / len(rows),
        "saved_generation_tokens_per_second": tokens / seconds,
        "saved_training_seconds": training_seconds,
        "saved_training_tokens_per_second": training_targets / training_seconds,
        "checkpoint_sha256": sha256_file(checkpoint),
        "run_manifest_sha256": sha256_file(run / "manifest.json"),
        "uncertainty": "NOT_TESTED; one seed and synthetic fixture",
        "recurrent_state_bytes": 0,
        "peak_memory_bytes": None,
        "timing_note": (
            "stored run timings; rescore/generation verify outputs but do not replace timings"
        ),
    }
    write_json(output / "metrics.json", summary)
    with (output / "table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["measurement", "value"])
        writer.writerows(summary.items())
    (output / "table.md").write_text(
        "| Measurement | Value |\n| --- | --- |\n"
        + "".join(f"| {key} | {value} |\n" for key, value in summary.items()),
        encoding="utf-8",
    )
    return summary
