"""Fail-closed owned-LM resume adapter; preserve the hash-bound v1 trainer.

The v1 checkpoint format and numerical training implementation remain unchanged.
Use this module for new training/resume; archived commands remain reproducible.
"""

import argparse
import hashlib
import json
import math
import pickle
import platform
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from toruk_lm import owned_training as legacy
from toruk_lm.owned_data import digest, load_data
from toruk_lm.owned_lm import VARIANTS, OwnedConfig, OwnedMemoryLM, OwnedModel

CONTRACT = "toruk-owned-resume-validation-v1"


def _documents(documents: list[dict[str, Any]], config: OwnedConfig) -> list[int]:
    if not documents or any(
        not isinstance(row, dict)
        or row.get("split") != "train"
        or not isinstance(row.get("text"), str)
        for row in documents
    ):
        raise ValueError("resume requires nonempty training documents")
    lengths = [len(row["text"].encode("utf-8")) + 1 for row in documents]
    if max(lengths) > config.max_document_tokens:
        raise ValueError("training document exceeds owned LM budget")
    return lengths


def _options(options: Any) -> None:
    if (
        not isinstance(options, dict)
        or set(options) != {"seed", "batch", "learning_rate", "threads"}
        or type(options["seed"]) is not int
        or not -(2**63) <= options["seed"] < 2**64
        or type(options["batch"]) is not int
        or not 1 <= options["batch"] <= 4
        or type(options["threads"]) is not int
        or options["threads"] != 1
        or type(options["learning_rate"]) not in (int, float)
        or not math.isfinite(options["learning_rate"])
        or not 0 < options["learning_rate"] <= 0.1
    ):
        raise ValueError("invalid owned resume training options")


def _progress(
    model: OwnedModel, payload: dict[str, Any], lengths: list[int]
) -> tuple[dict[int, int], int]:
    """Derive gradient participation from the v1 segment graph, without forwards.

    Backbone/readers participate in every memory-on update. Writer parameters
    participate only when a selected document has a subsequent segment. Memory-off
    bypasses every recurrent operation. AdamW counts parameter updates, not batches.
    """
    options, steps = payload["options"], payload["next_step"]
    targets = writer_steps = 0
    for step in range(steps):
        selected = legacy.train_indices(len(lengths), step, options["batch"], options["seed"])
        targets += sum(lengths[i] for i in selected)
        writer_steps += int(any(lengths[i] > model.config.context for i in selected))
    counts = dict.fromkeys(range(len(list(model.parameters()))), steps)
    if isinstance(model, OwnedMemoryLM):
        backbone = {id(p) for p in model.backbone.parameters()}
        writers = {
            id(p) for module in (model.proposal, model.gate) for p in module.parameters()
        } | {id(model.slot_gate), id(model.slot_proposal)}
        for index, parameter in enumerate(model.parameters()):
            if payload["variant"] == "memory_off":
                counts[index] = steps if id(parameter) in backbone else 0
            elif id(parameter) in writers:
                counts[index] = writer_steps
    return {index: count for index, count in counts.items() if count}, targets


def validate_resume(path: Path, documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a v1 checkpoint against its actual training data, without updates.

    Retains the original source/tokenizer/RNG checks. Does not waive archived
    identities or claim cross-runtime bitwise reproducibility.
    """
    try:
        # Model construction must not consume the caller's RNG stream.
        with torch.random.fork_rng(devices=[]):
            model, payload = legacy.load(path)
            options = payload["options"]
            _options(options)
            if type(payload["next_step"]) is not int or not 1 <= payload["next_step"] <= 512:
                raise ValueError("invalid completed optimizer progress")
            lengths = _documents(documents, OwnedConfig(**payload["config"]))
            if payload["dataset"] != digest(documents):
                raise ValueError("resume dataset identity mismatch")
            expected_counts, targets = _progress(model, payload, lengths)
            if type(payload["targets"]) is not int or payload["targets"] != targets:
                raise ValueError("resume target progress mismatch")
            expected = torch.optim.AdamW(
                model.parameters(), lr=options["learning_rate"]
            ).state_dict()["param_groups"]
            raw = payload["optimizer"]
            if not isinstance(raw, dict) or set(raw) != {"state", "param_groups"}:
                raise ValueError("invalid optimizer schema")
            if raw["param_groups"] != expected or any(
                type(index) is not int for group in raw["param_groups"] for index in group["params"]
            ):
                raise ValueError("optimizer settings/parameter order mismatch")
            states = raw["state"]
            if (
                not isinstance(states, dict)
                or any(type(index) is not int for index in states)
                or set(states) != set(expected_counts)
            ):
                raise ValueError("missing or unexpected optimizer moments")
            for index, parameter in enumerate(model.parameters()):
                if index not in expected_counts:
                    continue
                moments = states[index]
                if not isinstance(moments, dict) or set(moments) != {
                    "step",
                    "exp_avg",
                    "exp_avg_sq",
                }:
                    raise ValueError("invalid optimizer moments schema")
                for field in ("exp_avg", "exp_avg_sq"):
                    value = moments[field]
                    if (
                        not isinstance(value, torch.Tensor)
                        or value.shape != parameter.shape
                        or value.dtype != parameter.dtype
                        or value.device != parameter.device
                        or not torch.isfinite(value).all()
                    ):
                        raise ValueError("invalid optimizer moment shape/dtype/values")
                value = moments["step"]
                if (
                    not isinstance(value, torch.Tensor)
                    or value.ndim != 0
                    or not value.is_floating_point()
                    or not torch.isfinite(value)
                    or float(value) != expected_counts[index]
                ):
                    raise ValueError("optimizer parameter progress mismatch")
    except (
        KeyError,
        TypeError,
        AttributeError,
        RuntimeError,
        OverflowError,
        EOFError,
        pickle.UnpicklingError,
    ) as error:
        raise ValueError("invalid owned resume checkpoint") from error
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "checkpoint_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "variant": payload["variant"],
        "config": payload["config"],
        "options": options,
        "next_step": payload["next_step"],
        "targets": targets,
        "dataset": payload["dataset"],
        "optimizer_parameters": len(expected_counts),
        "model_forwards": 0,
        "optimizer_updates": 0,
    }


def train(
    config: OwnedConfig,
    variant: str,
    documents: list[dict[str, Any]],
    output: Path,
    *,
    steps: int,
    seed: int,
    batch: int = 2,
    learning_rate: float = 0.003,
    resume: Path | None = None,
    deadline: float | None = None,
) -> dict[str, Any]:
    """Preflight strictly, then use the unchanged v1 numerical training path."""
    options = dict(seed=seed, batch=batch, learning_rate=learning_rate, threads=1)
    _options(options)
    lengths = _documents(documents, config)
    if variant not in VARIANTS or type(steps) is not int or not 1 <= steps <= 512:
        raise ValueError("invalid owned resume variant/steps")
    if variant == "memory_on":
        writer_steps = sum(
            any(
                lengths[i] > config.context
                for i in legacy.train_indices(len(lengths), step, batch, seed)
            )
            for step in range(steps)
        )
        # v1's loader requires each stored AdamW step to equal next_step. Do not
        # create a checkpoint that its unchanged loader cannot subsequently read.
        if writer_steps not in (0, steps):
            raise ValueError("v1 cannot resume intermittent writer updates; use uniform segments")
    outputs = [
        output,
        output.with_suffix(".json"),
        output.with_suffix(".partial"),
        output.with_suffix(".resume.json"),
    ]
    if len(set(outputs)) != len(outputs) or any(p.exists() or p.is_symlink() for p in outputs):
        raise ValueError("refusing to overwrite checkpoint or companion output")
    started = time.perf_counter()
    previous = validate_resume(resume, documents) if resume is not None else None
    if previous is not None and (
        previous["config"] != asdict(config)
        or previous["variant"] != variant
        or previous["options"] != options
        or steps <= previous["next_step"]
    ):
        raise ValueError("resume config/options/variant/progress mismatch")
    result = legacy.train(
        config,
        variant,
        documents,
        output,
        steps=steps,
        seed=seed,
        batch=batch,
        learning_rate=learning_rate,
        resume=resume,
        deadline=deadline,
    )
    verified = validate_resume(output, documents)
    receipt = {
        **verified,
        "resumed_from": previous,
        "training_updates_this_run": result["steps"] - result["resumed_from"],
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_identity": legacy.runtime_identity(),
        "environment": {
            "python": platform.python_version(),
            "torch": str(torch.__version__),
            "platform": sys.platform,
            "device": "cpu",
        },
        "adapter_elapsed_seconds": time.perf_counter() - started,
        "limitations": "Software integrity check; no accuracy or efficiency claim. "
        "Legacy checkpoints do not record the complete creation environment.",
    }
    with output.with_suffix(".resume.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return {**result, "resume_validation": receipt}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "train"))
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--variant", choices=VARIANTS, default="memory_on")
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    try:
        documents = load_data(args.data, "train")
        if args.action == "validate":
            result = validate_resume(args.checkpoint, documents)
        else:
            if args.config is None:
                parser.error("train requires --config")
            config = json.loads(args.config.read_text(encoding="utf-8"))
            result = train(
                OwnedConfig(**config["model"]),
                args.variant,
                documents,
                args.checkpoint,
                steps=args.steps,
                seed=args.seed,
                batch=config["batch_documents"],
                learning_rate=config["learning_rate"],
                resume=args.resume,
            )
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        parser.exit(2, f"owned resume validation failed: {error}\n")
    print(json.dumps({k: v for k, v in result.items() if k != "trace"}, allow_nan=False))


if __name__ == "__main__":
    main()
