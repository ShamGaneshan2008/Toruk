"""Bounded next-token training/checkpoints/evaluation, separate from chat backbones."""

import argparse
import hashlib
import json
import math
import random
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from toruk_lm.engine import setup
from toruk_lm.model import CausalLM, generate
from toruk_lm.owned_data import digest, load_data
from toruk_lm.owned_lm import (
    FORMAT,
    VARIANTS,
    OwnedConfig,
    OwnedModel,
    OwnedSession,
    build_model,
    document_loss,
)
from toruk_lm.tokenizer import ByteTokenizer


def runtime_identity() -> dict[str, str]:
    root = Path(__file__).parent
    names = (
        "owned_lm.py",
        "owned_data.py",
        "owned_training.py",
        "model.py",
        "recurrent.py",
        "engine.py",
        "tokenizer.py",
    )
    return {
        name: hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for name in names
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def memory_bytes() -> dict[str, int]:
    # Optional measurement dependency is part of the development environment.
    try:
        import psutil  # type: ignore[import-untyped]
    except ImportError:
        return {"rss": 0, "process_lifetime_peak_rss": 0}
    info = psutil.Process().memory_info()
    return {"rss": info.rss, "process_lifetime_peak_rss": getattr(info, "peak_wset", 0)}


def flags(variant: str, ablation: str = "full") -> tuple[bool, bool]:
    if ablation not in ("full", "no_read", "no_update"):
        raise ValueError("unsupported ablation")
    return variant == "memory_on" and ablation != "no_read", (
        variant == "memory_on" and ablation != "no_update"
    )


def train_indices(count: int, step: int, batch: int, seed: int) -> list[int]:
    indices = []
    for offset in range(batch):
        epoch, position = divmod(step * batch + offset, count)
        order = list(range(count))
        random.Random(seed + epoch).shuffle(order)
        indices.append(order[position])
    return indices


def finite_tensors(value: Any) -> bool:
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(finite_tensors(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tensors(item) for item in value)
    return True


def load(path: Path) -> tuple[OwnedModel, dict[str, Any]]:
    payload = torch.load(path, weights_only=True, map_location="cpu")
    if not isinstance(payload, dict) or payload.get("format") != FORMAT:
        raise ValueError("unsupported checkpoint: requires toruk-owned-next-token-v1")
    required = {
        "config",
        "variant",
        "tokenizer",
        "runtime",
        "model",
        "optimizer",
        "options",
        "dataset",
        "next_step",
        "torch_rng",
        "python_rng",
        "targets",
    }
    if required - payload.keys():
        raise ValueError("incomplete owned LM checkpoint")
    if (
        payload["tokenizer"] != ByteTokenizer.fingerprint
        or payload["runtime"] != runtime_identity()
    ):
        raise ValueError("owned LM tokenizer/runtime identity mismatch")
    if type(payload["next_step"]) is not int or not 0 <= payload["next_step"] <= 512:
        raise ValueError("invalid optimizer-boundary progress")
    if not finite_tensors(payload):
        raise ValueError("nonfinite owned LM checkpoint")
    model = build_model(OwnedConfig(**payload["config"]), payload["variant"])
    model.load_state_dict(payload["model"], strict=True)
    options = payload["options"]
    if (
        not isinstance(options, dict)
        or set(options) != {"seed", "batch", "learning_rate", "threads"}
        or options["threads"] != 1
        or not 1 <= options["batch"] <= 4
        or not 0 < options["learning_rate"] <= 0.1
    ):
        raise ValueError("unsupported owned LM training options")
    try:
        random.Random().setstate(payload["python_rng"])
        torch.Generator().set_state(payload["torch_rng"])
        optimizer = torch.optim.AdamW(model.parameters(), lr=options["learning_rate"])
        optimizer.load_state_dict(payload["optimizer"])
        valid_parameters = set(model.parameters())
        for parameter, moments in optimizer.state.items():
            if parameter not in valid_parameters or set(moments) != {
                "step",
                "exp_avg",
                "exp_avg_sq",
            }:
                raise ValueError("unknown optimizer parameter or moments")
            if (
                moments["exp_avg"].shape != parameter.shape
                or moments["exp_avg_sq"].shape != parameter.shape
                or float(moments["step"]) != payload["next_step"]
            ):
                raise ValueError("optimizer shapes/progress mismatch")
    except (TypeError, KeyError, RuntimeError) as error:
        raise ValueError("invalid owned LM optimizer/RNG checkpoint") from error
    return model, payload


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
    if not 1 <= steps <= 512 or not 1 <= batch <= 4:
        raise ValueError("bounded training requires steps 1..512 and batch 1..4")
    if not math.isfinite(learning_rate) or not 0 < learning_rate <= 0.1:
        raise ValueError("invalid learning rate")
    if not documents or any(row.get("split") != "train" for row in documents):
        raise ValueError("only training documents may be optimized")
    if output.exists():
        raise ValueError("refusing to overwrite owned LM checkpoint")
    options = {"seed": seed, "batch": batch, "learning_rate": learning_rate, "threads": 1}
    setup(seed, 1)
    model = build_model(config, variant)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    first = targets = 0
    if resume is not None:
        model, saved = load(resume)
        if (
            saved["config"] != asdict(config)
            or saved["variant"] != variant
            or saved["options"] != options
            or saved["dataset"] != digest(documents)
        ):
            raise ValueError("resume config/data/variant mismatch")
        first, targets = saved["next_step"], saved["targets"]
        if first >= steps:
            raise ValueError("resume must extend an optimizer boundary")
        optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
        optimizer.load_state_dict(saved["optimizer"])
        # AdamW state is present only for parameters that received gradients.
        for parameter, state in optimizer.state.items():
            if state and (
                state["exp_avg"].shape != parameter.shape
                or state["exp_avg_sq"].shape != parameter.shape
                or float(state["step"]) != first
            ):
                raise ValueError("incompatible optimizer moments/progress")
        torch.set_rng_state(saved["torch_rng"])
        random.setstate(saved["python_rng"])
    read, write = flags(variant)
    model.train()
    start, cpu_start = time.perf_counter(), time.process_time()
    trace = []
    positions = 0
    for step in range(first, steps):
        if deadline is not None and time.perf_counter() > deadline:
            raise TimeoutError("bounded owned LM training budget exhausted")
        optimizer.zero_grad(set_to_none=True)
        losses = []
        count = 0
        ids = train_indices(len(documents), step, batch, seed)
        for index in ids:
            loss, n, work = document_loss(
                model,
                documents[index]["text"],
                read=read,
                write=write,
                maximum=config.max_document_tokens,
            )
            losses.append(loss)
            count += n
            positions += work
        loss = torch.stack(losses).sum() / count
        if not torch.isfinite(loss):
            raise ValueError("nonfinite training loss")
        loss.backward()
        if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in model.parameters()):
            raise ValueError("nonfinite gradient")
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        targets += count
        trace.append(
            {
                "step": step + 1,
                "nll": float(loss.detach()),
                "targets": count,
                "document_ids": [documents[i]["id"] for i in ids],
            }
        )
    payload = {
        "format": FORMAT,
        "config": asdict(config),
        "variant": variant,
        "tokenizer": ByteTokenizer.fingerprint,
        "runtime": runtime_identity(),
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "options": options,
        "dataset": digest(documents),
        "next_step": steps,
        "targets": targets,
        "torch_rng": torch.get_rng_state(),
        "python_rng": random.getstate(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".partial")
    torch.save(payload, temporary)
    temporary.replace(output)
    result = {
        "variant": variant,
        "seed": seed,
        "steps": steps,
        "resumed_from": first,
        "training_targets_total": targets,
        "forward_positions_this_run": positions,
        "seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu_start,
        "parameters": sum(p.numel() for p in model.parameters()),
        "active_gradient_parameters": sum(
            p.numel() for p in model.parameters() if p.grad is not None
        ),
        "memory": memory_bytes(),
        "trace": trace,
    }
    write_json(output.with_suffix(".json"), result)
    return result


@torch.no_grad()
def evaluate(
    checkpoint: Path,
    documents: list[dict[str, Any]],
    output: Path,
    *,
    budget: int = 16,
    ablation: str = "full",
    rolling: bool = False,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError("refusing to overwrite an evaluation")
    setup(0, 1)
    model, payload = load(checkpoint)
    model.eval()
    read, write = flags(payload["variant"], ablation)
    if rolling and not isinstance(model, CausalLM):
        raise ValueError("rolling diagnostic requires ordinary LM")
    rows = []
    start, cpu_start = time.perf_counter(), time.process_time()
    for row in documents:
        loss_start = time.perf_counter()
        loss, n, work = document_loss(
            model,
            row["text"],
            read=read,
            write=write,
            maximum=payload["config"]["max_document_tokens"],
        )
        nll_seconds = time.perf_counter() - loss_start
        generated_start = time.perf_counter()
        if rolling:
            assert isinstance(model, CausalLM)
            prefix_ids = [1, *ByteTokenizer().encode(row["prefix"])]
            generated_ids = generate(model, prefix_ids, budget)
            generated: dict[str, Any] = {
                "answer": ByteTokenizer().decode(generated_ids),
                "generated_ids": generated_ids,
                "input_tokens": len(prefix_ids),
                "forward_positions": sum(
                    min(model.config.context, len(prefix_ids) + i)
                    for i in range(len(generated_ids))
                ),
                "commits": 0,
                "allocated_state_bytes": 0,
                "budget_exhausted": bool(generated_ids and generated_ids[-1] != 2),
            }
        else:
            generated = dict(
                OwnedSession(model, read=read, write=write).generate(row["prefix"], budget)
            )
        generation_seconds = time.perf_counter() - generated_start
        answer = str(generated["answer"]).strip()
        expected = row["answer"]
        rows.append(
            {
                "id": row["id"],
                "category": row["category"],
                "expected": expected,
                "obsolete": row["obsolete"],
                "evidence": row["evidence"],
                "prefix_sha256": digest(row["prefix"]),
                "generation": generated,
                "correct": answer == expected,
                "unsupported": expected == "?" and answer not in ("?", ""),
                "wrong_nonempty": bool(answer) and answer != expected,
                "stale": bool(row["obsolete"]) and answer == row["obsolete"],
                "empty": not answer,
                "invalid_utf8": "\ufffd" in answer,
                "loss_sum": float(loss),
                "targets": n,
                "nll_forward_positions": work,
                "nll_seconds": nll_seconds,
                "generation_seconds": generation_seconds,
            }
        )
    nll = sum(r["loss_sum"] for r in rows) / sum(r["targets"] for r in rows)
    result = {
        "schema": "toruk-owned-evaluation-v1",
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        "variant": payload["variant"],
        "seed": payload["options"]["seed"],
        "ablation": ablation,
        "rolling_diagnostic": rolling,
        "dataset": digest(documents),
        "nll": nll,
        "byte_perplexity": math.exp(nll),
        "questions": len(rows),
        "correct": sum(r["correct"] for r in rows),
        "unsupported": sum(r["unsupported"] for r in rows),
        "wrong_nonempty": sum(r["wrong_nonempty"] for r in rows),
        "categories": {
            c: {
                "n": sum(r["category"] == c for r in rows),
                "correct": sum(r["category"] == c and r["correct"] for r in rows),
            }
            for c in sorted({r["category"] for r in rows})
        },
        "seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu_start,
        "memory": memory_bytes(),
        "rows": rows,
    }
    write_json(output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EXPERIMENTAL Toruk-owned byte LM; not chat qualified"
    )
    parser.add_argument("action", choices=("train", "evaluate", "generate"))
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--variant", choices=VARIANTS, default="memory_on")
    parser.add_argument("--split", choices=("train", "dev", "heldout"), default="dev")
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--prompt", default="Hello")
    parser.add_argument("--max-new-tokens", type=int, default=16)
    args = parser.parse_args()
    if args.action == "train":
        if args.config is None or args.data is None:
            parser.error("train requires --config and --data")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        result = train(
            OwnedConfig(**config["model"]),
            args.variant,
            load_data(args.data, "train"),
            args.checkpoint,
            steps=args.steps,
            seed=args.seed,
            batch=config["batch_documents"],
            learning_rate=config["learning_rate"],
            resume=args.resume,
        )
        print(json.dumps({k: v for k, v in result.items() if k != "trace"}))
    elif args.action == "evaluate":
        if args.data is None or args.output is None:
            parser.error("evaluate requires --data and --output")
        result = evaluate(
            args.checkpoint,
            load_data(args.data, args.split),
            args.output,
            budget=args.max_new_tokens,
        )
        print(json.dumps({k: v for k, v in result.items() if k != "rows"}))
    else:
        setup(0, 1)
        model, saved = load(args.checkpoint)
        read, write = flags(saved["variant"])
        print(
            json.dumps(
                {
                    "experimental": True,
                    "conversationally_qualified": False,
                    "model": FORMAT,
                    "variant": saved["variant"],
                    **OwnedSession(model, read=read, write=write).generate(
                        args.prompt, args.max_new_tokens
                    ),
                }
            )
        )


if __name__ == "__main__":
    main()
