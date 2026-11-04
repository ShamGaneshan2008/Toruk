"""CPU training, safe-boundary checkpoints, local-window evaluation."""

import math
import pickle
import platform
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch

from toruk_lm.data import (
    batch,
    check_separation,
    read_documents,
    sha256_file,
    training_batch,
    windows,
    write_json,
)
from toruk_lm.model import CausalLM, ModelConfig, generate, loss_sum
from toruk_lm.tokenizer import ByteTokenizer


@dataclass(frozen=True)
class TrainConfig:
    seed: int = 23
    batch_size: int = 4
    learning_rate: float = 0.003
    threads: int = 1

    def __post_init__(self) -> None:
        if any(type(value) is not int for value in (self.seed, self.batch_size, self.threads)):
            raise ValueError("seed, batch_size and threads must be integers")
        if not -(2**63) <= self.seed < 2**64:
            raise ValueError("seed must be in the supported torch seed range")
        if type(self.learning_rate) not in (int, float):
            raise ValueError("learning_rate must be a finite positive number")
        if (
            self.batch_size <= 0
            or self.threads <= 0
            or not math.isfinite(self.learning_rate)
            or self.learning_rate <= 0
        ):
            raise ValueError("batch_size, threads, and learning_rate must be positive")


def setup(seed: int, threads: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(threads)
    torch.use_deterministic_algorithms(True)


def load_checkpoint(path: Path) -> dict[str, Any]:
    try:
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    except (pickle.UnpicklingError, EOFError, RuntimeError) as error:
        raise ValueError(f"cannot read checkpoint {path}: {error}") from error
    if not isinstance(checkpoint, dict):
        raise ValueError("checkpoint must be a dictionary")
    if checkpoint.get("format") != "toruk-ordinary-v1":
        raise ValueError("unsupported checkpoint format or recurrent/mid-document state")
    if checkpoint.get("tokenizer") != ByteTokenizer.fingerprint:
        raise ValueError("tokenizer identity mismatch")
    required = {
        "model_config",
        "train_config",
        "model",
        "optimizer",
        "scheduler",
        "python_rng",
        "torch_rng",
        "datasets",
        "next_step",
        "data_progress",
    }
    missing = required - checkpoint.keys()
    if missing:
        raise ValueError(f"checkpoint missing fields: {', '.join(sorted(missing))}")
    for key in ("model_config", "train_config", "model", "optimizer", "datasets", "data_progress"):
        if not isinstance(checkpoint[key], dict):
            raise ValueError(f"checkpoint {key} must be a dictionary")
    if type(checkpoint["next_step"]) is not int or checkpoint["next_step"] < 0:
        raise ValueError("checkpoint next_step must be a nonnegative integer")
    if checkpoint["scheduler"] is not None:
        raise ValueError("checkpoint scheduler is unsupported; expected fixed learning rate")
    return checkpoint


def load_model(path: Path) -> CausalLM:
    checkpoint = load_checkpoint(path)
    try:
        config = ModelConfig(**checkpoint["model_config"])
    except TypeError as error:
        raise ValueError(f"invalid checkpoint model_config: {error}") from error
    model = CausalLM(config)
    try:
        model.load_state_dict(checkpoint["model"])
    except RuntimeError as error:
        raise ValueError(f"checkpoint model state mismatch: {error}") from error
    for name, parameter in model.named_parameters():
        if not torch.isfinite(parameter).all():
            raise ValueError(f"checkpoint contains nonfinite model weights: {name}")
    model.eval()
    return model


def restore_training_state(
    saved: dict[str, Any], model: CausalLM, optimizer: torch.optim.AdamW
) -> None:
    """Validate resumable AdamW/RNG state before using it for another update."""
    state = saved["optimizer"]
    groups = state.get("param_groups")
    moments = state.get("state")
    if not isinstance(groups, list) or len(groups) != 1 or not isinstance(moments, dict):
        raise ValueError("checkpoint optimizer requires one param_groups entry and state")
    group = groups[0]
    if not isinstance(group, dict) or not isinstance(group.get("params"), list):
        raise ValueError("invalid checkpoint optimizer parameter group")
    indices = group["params"]
    parameters = list(model.parameters())
    if (
        len(indices) != len(parameters)
        or any(type(index) is not int for index in indices)
        or len(set(indices)) != len(indices)
        or set(moments) != set(indices)
    ):
        raise ValueError("checkpoint optimizer parameter/state identity mismatch")
    for key, value in optimizer.defaults.items():
        if group.get(key) != value:
            raise ValueError(f"checkpoint optimizer setting mismatch: {key}")
    for index, parameter in zip(indices, parameters, strict=True):
        item = moments[index]
        if not isinstance(item, dict):
            raise ValueError("invalid checkpoint optimizer state")
        for field in ("exp_avg", "exp_avg_sq"):
            tensor = item.get(field)
            if (
                not isinstance(tensor, torch.Tensor)
                or tensor.shape != parameter.shape
                or tensor.dtype != parameter.dtype
                or not torch.isfinite(tensor).all()
            ):
                raise ValueError(f"invalid checkpoint optimizer {field}")
        step = item.get("step")
        if not isinstance(step, torch.Tensor) or step.numel() != 1:
            raise ValueError("invalid checkpoint optimizer step")
        if step.item() != saved["next_step"]:
            raise ValueError("checkpoint optimizer step disagrees with next_step")
    if not isinstance(saved["python_rng"], tuple) or len(saved["python_rng"]) != 3:
        raise ValueError("invalid checkpoint Python RNG state")
    try:
        random.Random().setstate(saved["python_rng"])
        torch.Generator().set_state(saved["torch_rng"])
    except (TypeError, ValueError, RuntimeError) as error:
        raise ValueError(f"invalid checkpoint RNG state: {error}") from error
    try:
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(state)
    except (KeyError, TypeError, ValueError, RuntimeError) as error:
        raise ValueError(f"incompatible checkpoint training state: {error}") from error
    random.setstate(saved["python_rng"])
    torch.set_rng_state(saved["torch_rng"])


def evaluate_loss(model: CausalLM, path: Path, batch_size: int = 4) -> dict[str, Any]:
    """Nonoverlapping document windows, exactly one score per non-BOS token."""
    examples = windows(read_documents(path), model.config.context)
    total_loss, valid_tokens = 0.0, 0
    model.eval()
    started = time.perf_counter()
    with torch.no_grad():
        for start in range(0, len(examples), batch_size):
            x, y = batch(examples[start : start + batch_size])
            summed, count = loss_sum(model(x), y)
            if not torch.isfinite(summed):
                raise FloatingPointError("nonfinite evaluation loss")
            total_loss += float(summed.item())
            valid_tokens += count
    elapsed = time.perf_counter() - started
    return {
        "loss_nats_per_byte_or_eos": total_loss / valid_tokens,
        "valid_tokens": valid_tokens,
        "seconds": elapsed,
        "tokens_per_second": valid_tokens / elapsed,
        "context_tokens": model.config.context,
        "protocol": "document windows; no token scored twice; positions restart per window",
        "dataset_sha256": sha256_file(path),
    }


def train(
    train_path: Path,
    validation_path: Path,
    output: Path,
    model_config: ModelConfig,
    config: TrainConfig,
    steps: int,
    resume: Path | None = None,
) -> dict[str, Any]:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh output directory to preserve existing runs")
    setup(config.seed, config.threads)
    documents, validation = read_documents(train_path), read_documents(validation_path)
    check_separation(documents, validation)
    examples = windows(documents, model_config.context)
    fingerprints = {"train": sha256_file(train_path), "validation": sha256_file(validation_path)}
    model = CausalLM(model_config)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    next_step = 0
    if resume:
        saved = load_checkpoint(resume)
        for key, expected in (
            ("model_config", asdict(model_config)),
            ("train_config", asdict(config)),
            ("datasets", fingerprints),
        ):
            if saved[key] != expected:
                raise ValueError(f"resume {key} mismatch")
        if saved["data_progress"] != {
            "next_step": saved["next_step"],
            "examples_consumed": saved["next_step"] * config.batch_size,
            "boundary": "after_optimizer_step; independent ordinary-LM windows",
        }:
            raise ValueError("unsupported data-progress/resume boundary")
        restore_training_state(saved, model, optimizer)
        next_step = saved["next_step"]
        if steps <= next_step:
            raise ValueError("steps must exceed checkpoint next_step")
    output.mkdir(parents=True, exist_ok=True)
    losses = []
    processed = 0
    started = time.perf_counter()
    model.train()
    for step in range(next_step, steps):
        x, y = training_batch(examples, step, config.batch_size, config.seed)
        optimizer.zero_grad(set_to_none=True)
        summed, count = loss_sum(model(x), y)
        loss = summed / count
        if not torch.isfinite(loss):
            raise FloatingPointError(f"nonfinite loss at step {step}")
        loss.backward()
        for name, parameter in model.named_parameters():
            if parameter.grad is None or not torch.isfinite(parameter.grad).all():
                raise FloatingPointError(f"missing/nonfinite gradient: {name}, step {step}")
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        losses.append({"step": step + 1, "loss": loss.item(), "gradient_norm": grad_norm.item()})
        processed += count
    training_seconds = time.perf_counter() - started
    # Fixed learning rate: no scheduler exists. Only completed optimizer boundaries are resumable.
    checkpoint = {
        "format": "toruk-ordinary-v1",
        "model_config": asdict(model_config),
        "train_config": asdict(config),
        "tokenizer": ByteTokenizer.fingerprint,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": None,
        "python_rng": random.getstate(),
        "torch_rng": torch.get_rng_state(),
        "datasets": fingerprints,
        "next_step": steps,
        "data_progress": {
            "next_step": steps,
            "examples_consumed": steps * config.batch_size,
            "boundary": "after_optimizer_step; independent ordinary-LM windows",
        },
    }
    temporary = output / "checkpoint.pt.tmp"
    torch.save(checkpoint, temporary)
    temporary.replace(output / "checkpoint.pt")
    metrics = {
        "model_family": "Toruk-LM",
        "variant": "ordinary",
        "steps_completed": steps,
        "steps_this_invocation": steps - next_step,
        "train_config": asdict(config),
        "model_config": asdict(model_config),
        "tokenizer": ByteTokenizer.fingerprint,
        "datasets": fingerprints,
        "parameters": sum(p.numel() for p in model.parameters()),
        "recurrent_state_bytes": 0,
        "train_valid_tokens_this_invocation": processed,
        "training_seconds": training_seconds,
        "train_tokens_per_second": processed / training_seconds,
        "validation": evaluate_loss(model, validation_path, config.batch_size),
        "losses": losses,
        "python": platform.python_version(),
        "torch": str(torch.__version__),
        "device": "cpu",
        "resume_from": str(resume) if resume else None,
        "peak_allocated_memory_bytes": None,
        "peak_memory_note": "CPU allocator peak not measured; CUDA not used",
    }
    write_json(output / "metrics.json", metrics)
    write_json(output / "config.json", {"model": asdict(model_config), "training": asdict(config)})
    return metrics


def evaluate(
    checkpoint: Path,
    data: Path,
    output: Path,
    max_new_tokens: int = 32,
) -> dict[str, Any]:
    if max_new_tokens <= 0:
        raise ValueError("evaluation max_new_tokens must be positive")
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh evaluation directory to preserve existing runs")
    setup(23, 1)
    model = load_model(checkpoint)
    metrics = evaluate_loss(model, data)
    predictions: list[dict[str, Any]] = []
    for row in read_documents(data):
        # A continuation smoke test, not factual QA. Suffix never enters model.generate.
        text = row["text"]
        prefix = text[: len(text) // 2]
        started = time.perf_counter()
        prefix_tokens = [1, *ByteTokenizer().encode(prefix)]
        generated = generate(model, prefix_tokens, max_new_tokens)
        elapsed = time.perf_counter() - started
        predictions.append(
            {
                "id": row["id"],
                "prefix": prefix,
                "generated_ids": generated,
                "generated": ByteTokenizer().decode(generated),
                "reference_suffix": text[len(prefix) :],
                "end_to_end_seconds": elapsed,
                "observed_history_tokens": len(prefix_tokens),
                "retained_context_tokens": min(len(prefix_tokens), model.config.context),
            }
        )
    metrics["generation"] = {
        "protocol": "greedy text continuation; not controlled-world QA or recall accuracy",
        "examples": len(predictions),
        "generated_tokens": sum(len(row["generated_ids"]) for row in predictions),
        "end_to_end_seconds": sum(row["end_to_end_seconds"] for row in predictions),
        "includes": (
            "prefix tokenization, local-window recomputation, greedy decode; excludes model load"
        ),
    }
    metrics["generation"]["tokens_per_second"] = (
        metrics["generation"]["generated_tokens"] / metrics["generation"]["end_to_end_seconds"]
    )
    metrics["checkpoint_sha256"] = sha256_file(checkpoint)
    write_json(output / "metrics.json", metrics)
    write_json(output / "predictions.json", predictions)
    return metrics
