"""Real CLI entry points for Toruk-LM foundation experiments."""

import argparse
import json
import os
import platform
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from toruk_lm.data import make_fixture
from toruk_lm.engine import TrainConfig, evaluate, load_model, setup, train
from toruk_lm.model import ModelConfig, generate
from toruk_lm.reproduction import reproduce, summarize
from toruk_lm.tokenizer import ByteTokenizer
from toruk_lm.validation import read_config, require_split, validate


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="toruk", description="Toruk-LM research foundation")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("diagnose", help="report actual runtime and CUDA availability")
    data = sub.add_parser("make-fixture", help="generate document-separated smoke-test text")
    data.add_argument("--output", type=Path, required=True)
    data.add_argument("--seed", type=int, default=17)
    data.add_argument("--documents", type=int, default=60)
    check = sub.add_parser(
        "validate", help="verify split checksums, config and checkpoint identity"
    )
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--config", type=Path)
    check.add_argument("--checkpoint", type=Path)
    repeat = sub.add_parser("reproduce", help="run and seal a bounded ordinary-LM CPU fixture")
    repeat.add_argument("--output", type=Path, required=True)
    repeat.add_argument("--config", type=Path)
    repeat.add_argument("--steps", type=int, default=2)
    repeat.add_argument("--documents", type=int, default=10)
    repeat.add_argument("--data-seed", type=int, default=17)
    repeat.add_argument("--max-new-tokens", type=int, default=8)
    table = sub.add_parser("summarize", help="verify a sealed run and regenerate result tables")
    table.add_argument("--run", type=Path, required=True)
    table.add_argument("--output", type=Path, required=True)
    fit = sub.add_parser("train", help="train ordinary LM; CPU; fixed learning rate")
    fit.add_argument("--train", type=Path, required=True)
    fit.add_argument("--validation", type=Path, required=True)
    fit.add_argument("--output", type=Path, required=True)
    fit.add_argument("--steps", type=int, default=20, help="absolute total optimizer steps")
    fit.add_argument("--resume", type=Path)
    fit.add_argument("--manifest", type=Path)
    fit.add_argument("--config", type=Path)
    for name, default in (
        ("context", 64),
        ("width", 32),
        ("heads", 4),
        ("layers", 2),
        ("seed", 23),
        ("batch-size", 4),
        ("threads", 1),
    ):
        fit.add_argument(f"--{name}", type=int, default=None, help=f"default: {default}")
    fit.add_argument("--learning-rate", type=float, default=None, help="default: 0.003")
    score = sub.add_parser("evaluate", help="local-context loss and autoregressive continuations")
    score.add_argument("--checkpoint", type=Path, required=True)
    score.add_argument("--data", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--max-new-tokens", type=int, default=32)
    score.add_argument("--manifest", type=Path)
    score.add_argument("--split", choices=("train", "validation", "test"), default="validation")
    sample = sub.add_parser("generate", help="greedy local-context inference")
    sample.add_argument("--checkpoint", type=Path, required=True)
    sample.add_argument("--prompt", required=True)
    sample.add_argument("--max-new-tokens", type=int, default=32)
    return root


def main() -> None:
    root = parser()
    args = root.parse_args()
    result: dict[str, Any]
    try:
        if args.command == "diagnose":
            result = {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "logical_cpus": os.cpu_count(),
                "torch": str(torch.__version__),
                "cuda_available": torch.cuda.is_available(),
                "cuda_devices": [
                    torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
                ],
                "training_device": "cpu",
                "tokenizer": ByteTokenizer.fingerprint,
            }
        elif args.command == "make-fixture":
            result = make_fixture(args.output, args.seed, args.documents)
        elif args.command == "validate":
            result = validate(args.manifest, args.config, args.checkpoint)
        elif args.command == "reproduce":
            result = reproduce(
                args.output,
                args.config,
                args.steps,
                args.documents,
                args.data_seed,
                args.max_new_tokens,
            )
        elif args.command == "summarize":
            result = summarize(args.run, args.output)
        elif args.command == "train":
            model_config, train_config = (
                read_config(args.config) if args.config else (ModelConfig(), TrainConfig())
            )
            model_values, train_values = asdict(model_config), asdict(train_config)
            for key in model_values:
                if getattr(args, key, None) is not None:
                    model_values[key] = getattr(args, key)
            for key in train_values:
                if getattr(args, key) is not None:
                    train_values[key] = getattr(args, key)
            if args.manifest:
                require_split(args.manifest, args.train, "train")
                require_split(args.manifest, args.validation, "validation")
            result = train(
                args.train,
                args.validation,
                args.output,
                ModelConfig(**model_values),
                TrainConfig(**train_values),
                args.steps,
                args.resume,
            )
        elif args.command == "evaluate":
            if args.manifest:
                require_split(args.manifest, args.data, args.split)
                validate(args.manifest, checkpoint=args.checkpoint)
            result = evaluate(
                args.checkpoint,
                args.data,
                args.output,
                args.max_new_tokens,
            )
        else:
            setup(23, 1)
            model = load_model(args.checkpoint)
            generated = generate(
                model,
                [1, *ByteTokenizer().encode(args.prompt)],
                args.max_new_tokens,
            )
            result = {"generated": ByteTokenizer().decode(generated), "ids": generated}
    except (ValueError, FloatingPointError, OSError) as error:
        root.error(str(error))
    print(json.dumps(result, indent=2))
