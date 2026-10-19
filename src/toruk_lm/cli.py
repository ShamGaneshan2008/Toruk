"""Real CLI entry points for Toruk-LM foundation experiments."""

import argparse
import json
import os
import platform
from pathlib import Path
from typing import Any

import torch

from toruk_lm.data import make_fixture
from toruk_lm.engine import TrainConfig, evaluate, load_model, setup, train
from toruk_lm.model import ModelConfig, generate
from toruk_lm.tokenizer import ByteTokenizer


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="toruk", description="Toruk-LM research foundation")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("diagnose", help="report actual runtime and CUDA availability")
    data = sub.add_parser("make-fixture", help="generate document-separated smoke-test text")
    data.add_argument("--output", type=Path, required=True)
    data.add_argument("--seed", type=int, default=17)
    data.add_argument("--documents", type=int, default=60)
    fit = sub.add_parser("train", help="train ordinary LM; CPU; fixed learning rate")
    fit.add_argument("--train", type=Path, required=True)
    fit.add_argument("--validation", type=Path, required=True)
    fit.add_argument("--output", type=Path, required=True)
    fit.add_argument("--steps", type=int, default=20, help="absolute total optimizer steps")
    fit.add_argument("--resume", type=Path)
    for name, default in (
        ("context", 64),
        ("width", 32),
        ("heads", 4),
        ("layers", 2),
        ("seed", 23),
        ("batch-size", 4),
        ("threads", 1),
    ):
        fit.add_argument(f"--{name}", type=int, default=default)
    fit.add_argument("--learning-rate", type=float, default=0.003)
    score = sub.add_parser("evaluate", help="local-context loss and autoregressive continuations")
    score.add_argument("--checkpoint", type=Path, required=True)
    score.add_argument("--data", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--max-new-tokens", type=int, default=32)
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
        elif args.command == "train":
            result = train(
                args.train,
                args.validation,
                args.output,
                ModelConfig(args.context, args.width, args.heads, args.layers),
                TrainConfig(args.seed, args.batch_size, args.learning_rate, args.threads),
                args.steps,
                args.resume,
            )
        elif args.command == "evaluate":
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
    except (ValueError, FloatingPointError, FileNotFoundError) as error:
        root.error(str(error))
    print(json.dumps(result, indent=2))
