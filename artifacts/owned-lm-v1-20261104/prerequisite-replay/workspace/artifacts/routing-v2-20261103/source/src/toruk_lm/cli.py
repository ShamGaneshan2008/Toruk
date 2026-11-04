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
    valid = sub.add_parser("validate-config", help="validate a versioned reproduction config")
    valid.add_argument("--config", type=Path, required=True)
    audit = sub.add_parser(
        "audit-evidence", help="validate sealed evidence and rescore raw answers"
    )
    audit.add_argument("--parent", type=Path, required=True)
    audit.add_argument("--handoff", type=Path, required=True)
    audit.add_argument("--studies", type=Path, nargs="*", default=[])
    audit.add_argument("--output", type=Path, required=True)
    compare = sub.add_parser(
        "compare-replay", help="require exact generated answers and score parity"
    )
    compare.add_argument("--reference", type=Path, required=True)
    compare.add_argument("--reproduction", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
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
    repeat = sub.add_parser(
        "reproduce", help="run a bounded foundation or versioned research config"
    )
    repeat.add_argument("--output", type=Path, required=True)
    repeat.add_argument("--config", type=Path)
    repeat.add_argument("--steps", type=int)
    repeat.add_argument("--documents", type=int)
    repeat.add_argument("--data-seed", type=int)
    repeat.add_argument("--max-new-tokens", type=int)
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
    worlds = sub.add_parser("make-worlds", help="create frozen controlled worlds and LM exports")
    worlds.add_argument("--output", type=Path, required=True)
    worlds.add_argument("--seed", type=int, default=17)
    worlds.add_argument("--worlds-per-split", type=int, default=8)
    world_score = sub.add_parser(
        "evaluate-worlds", help="validation-only generated factual answers"
    )
    world_score.add_argument("--checkpoint", type=Path, required=True)
    world_score.add_argument("--data", type=Path, required=True)
    world_score.add_argument("--output", type=Path, required=True)
    world_score.add_argument("--max-new-tokens", type=int, default=16)
    controlled = sub.add_parser(
        "train-controlled", help="bounded ordinary/recurrent world training"
    )
    controlled.add_argument("--train", type=Path, required=True)
    controlled.add_argument("--validation", type=Path, required=True)
    controlled.add_argument("--output", type=Path, required=True)
    controlled.add_argument("--variant", choices=["ordinary", "recurrent"], required=True)
    controlled.add_argument("--steps", type=int, default=12)
    controlled.add_argument("--seed", type=int, default=23)
    controlled.add_argument("--slots", type=int, default=4)
    controlled.add_argument("--context", type=int, default=64)
    controlled.add_argument("--width", type=int, default=32)
    controlled.add_argument("--heads", type=int, default=4)
    controlled.add_argument("--layers", type=int, default=2)
    controlled.add_argument("--max-segments", type=int, default=32)
    controlled.add_argument("--resume", type=Path)
    controlled.add_argument(
        "--objective", choices=["qa", "revision", "no-correction", "no-preservation"], default="qa"
    )
    controlled_score = sub.add_parser("evaluate-controlled", help="validation-only world answers")
    controlled_score.add_argument("--checkpoint", type=Path, required=True)
    controlled_score.add_argument("--data", type=Path, required=True)
    controlled_score.add_argument("--output", type=Path, required=True)
    controlled_score.add_argument("--max-new-tokens", type=int, default=16)
    controlled_score.add_argument(
        "--policy",
        choices=["write", "retain", "predictor", "heuristic", "random", "reset"],
        default="write",
    )
    controlled_score.add_argument("--predictor", type=Path)
    labels = sub.add_parser("effect-labels", help="offline bounded paired supervision")
    labels.add_argument("--checkpoint", type=Path, required=True)
    labels.add_argument("--data", type=Path, required=True)
    labels.add_argument("--output", type=Path, required=True)
    labels.add_argument("--split", choices=["train", "validation"], default="train")
    labels.add_argument("--limit", type=int, default=8)
    labels.add_argument("--answer-budget", type=int, default=16)
    effect_fit = sub.add_parser("fit-effect", help="fit effect predictor on training labels only")
    effect_fit.add_argument("--labels", type=Path, required=True)
    effect_fit.add_argument("--output", type=Path, required=True)
    effect_fit.add_argument("--steps", type=int, default=100)
    effect_score = sub.add_parser("evaluate-effect", help="offline validation effect diagnostics")
    effect_score.add_argument("--predictor", type=Path, required=True)
    effect_score.add_argument("--labels", type=Path, required=True)
    effect_score.add_argument("--output", type=Path, required=True)
    pilot = sub.add_parser(
        "controlled-pilot", help="bounded validation prerequisite/comparison pipeline"
    )
    pilot.add_argument("--output", type=Path, required=True)
    pilot.add_argument("--steps", type=int, default=12)
    pilot.add_argument("--worlds", type=int, default=4)
    pilot.add_argument("--answer-budget", type=int, default=16)
    pilot.add_argument("--seconds", type=float, default=110)
    replay = sub.add_parser("verify-m6", help="reproduce frozen M6 answers without retraining")
    replay.add_argument("--parent", type=Path, required=True)
    replay.add_argument("--handoff", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--seconds", type=float, default=110)
    study = sub.add_parser("generalization", help="bounded exploratory M7 held-out failure study")
    study.add_argument("--parent", type=Path, required=True)
    study.add_argument("--verification", type=Path, required=True)
    study.add_argument("--study", choices=["templates", "load"], required=True)
    study.add_argument("--output", type=Path, required=True)
    study.add_argument("--worlds-per-seed", type=int, default=2)
    study.add_argument("--seconds", type=float, default=110)
    heldout = sub.add_parser("evaluate-heldout", help="one protocol-bound M7 cell/checkpoint")
    heldout.add_argument("--parent", type=Path, required=True)
    heldout.add_argument("--protocol", type=Path, required=True)
    heldout.add_argument("--method", required=True)
    heldout.add_argument("--data", type=Path, required=True)
    heldout.add_argument("--output", type=Path, required=True)
    return root


def main() -> None:
    root = parser()
    args = root.parse_args()
    result: dict[str, Any]
    try:
        if args.command == "compare-replay":
            from toruk_lm.reproducibility import compare_replay

            result = compare_replay(args.reference, args.reproduction, args.output)
        elif args.command == "validate-config":
            from toruk_lm.reproducibility import validate_config

            result = {"status": "PASS", "config": validate_config(args.config)}
        elif args.command == "reproduce":
            config = json.loads(args.config.read_text(encoding="utf-8")) if args.config else None
            if config is None or isinstance(config, dict) and set(config) == {"model", "training"}:
                result = reproduce(
                    args.output,
                    args.config,
                    args.steps if args.steps is not None else 2,
                    args.documents if args.documents is not None else 10,
                    args.data_seed if args.data_seed is not None else 17,
                    args.max_new_tokens if args.max_new_tokens is not None else 8,
                )
            else:
                if any(
                    value is not None
                    for value in (args.steps, args.documents, args.data_seed, args.max_new_tokens)
                ):
                    raise ValueError("versioned research configs do not accept protocol overrides")
                from toruk_lm.reproducibility import reproduce as reproduce_research

                result = reproduce_research(args.config, args.output)
        elif args.command == "audit-evidence":
            from toruk_lm.reproducibility import audit_evidence

            result = audit_evidence(args.parent, args.handoff, args.studies, args.output)
        elif args.command == "diagnose":
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
        elif args.command == "verify-m6":
            from toruk_lm.generalization import verify_m6

            result = verify_m6(args.parent, args.handoff, args.output, args.seconds)
        elif args.command == "generalization":
            from toruk_lm.generalization import run_study

            result = run_study(
                args.parent,
                args.verification,
                args.output,
                args.study,
                args.worlds_per_seed,
                args.seconds,
            )
        elif args.command == "evaluate-heldout":
            from toruk_lm.generalization import evaluate_cell

            protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
            if args.method not in protocol.get("methods", {}):
                raise ValueError(
                    f"unknown protocol method {args.method!r}; choose from "
                    + ", ".join(sorted(protocol.get("methods", {})))
                )
            result = evaluate_cell(
                args.parent, protocol["methods"][args.method], args.data, args.protocol, args.output
            )
        elif args.command == "controlled-pilot":
            from toruk_lm.comparisons import run_pilot

            result = run_pilot(
                args.output, args.steps, args.worlds, args.answer_budget, args.seconds
            )
        elif args.command == "effect-labels":
            from toruk_lm.effect_training import paired_labels

            result = paired_labels(
                args.checkpoint,
                args.data,
                args.output,
                args.split,
                args.limit,
                answer_budget=args.answer_budget,
            )
        elif args.command == "fit-effect":
            from toruk_lm.effect_training import fit_effect

            result = fit_effect(args.labels, args.output, args.steps)
        elif args.command == "evaluate-effect":
            from toruk_lm.effect_training import evaluate_effect

            result = evaluate_effect(args.predictor, args.labels, args.output)
        elif args.command == "train-controlled":
            from toruk_lm.controlled import train_controlled

            result = train_controlled(
                args.train,
                args.validation,
                args.output,
                args.variant,
                args.steps,
                args.seed,
                args.slots,
                ModelConfig(
                    context=args.context, width=args.width, heads=args.heads, layers=args.layers
                ),
                args.resume,
                args.max_segments,
                args.objective,
            )
        elif args.command == "evaluate-controlled":
            from toruk_lm.controlled import evaluate_controlled

            result = evaluate_controlled(
                args.checkpoint,
                args.data,
                args.output,
                args.max_new_tokens,
                args.policy,
                args.predictor,
            )
        elif args.command == "make-worlds":
            from toruk_lm.worlds import make_worlds

            result = make_worlds(args.output, args.seed, args.worlds_per_split)
        elif args.command == "evaluate-worlds":
            from toruk_lm.worlds import evaluate_worlds

            result = evaluate_worlds(
                args.checkpoint, args.data, args.output, max_new_tokens=args.max_new_tokens
            )
        elif args.command == "make-fixture":
            result = make_fixture(args.output, args.seed, args.documents)
        elif args.command == "validate":
            result = validate(args.manifest, args.config, args.checkpoint)
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
    except KeyError as error:
        root.error(f"malformed configuration/artifact: missing required field {error}")
    except (ValueError, FloatingPointError, OSError, TimeoutError) as error:
        root.error(str(error))
    print(json.dumps(result, indent=2))
