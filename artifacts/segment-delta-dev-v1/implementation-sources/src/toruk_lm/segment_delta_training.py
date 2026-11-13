"""Strict optimizer-boundary training for the isolated development prototype."""

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch

from toruk_lm.engine import setup
from toruk_lm.owned_lm import OwnedMemoryLM
from toruk_lm.owned_training import finite_tensors, train_indices
from toruk_lm.segment_delta import DeltaConfig, ResearchModel, build_model, document_loss
from toruk_lm.tokenizer import ByteTokenizer

FORMAT = "toruk-segment-delta-dev-v1"


@dataclass(frozen=True)
class FitConfig:
    seed: int = 113
    batch: int = 2
    learning_rate: float = 0.003

    def __post_init__(self) -> None:
        if type(self.seed) is not int or type(self.batch) is not int or not 1 <= self.batch <= 2:
            raise ValueError("invalid fit seed/batch")
        if self.learning_rate != 0.003:
            raise ValueError("only fixed development learning rate supported")


def data_digest(documents: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json.dumps(documents, sort_keys=True).encode()).hexdigest()


def optimizer_for(model: ResearchModel, config: FitConfig) -> torch.optim.AdamW:
    return torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0.01,
        foreach=False,
        fused=False,
    )


def load(
    path: Path, identity: dict[str, str]
) -> tuple[ResearchModel, torch.optim.AdamW, dict[str, Any]]:
    saved = torch.load(path, weights_only=True, map_location="cpu")
    required = {
        "format",
        "boundary",
        "config",
        "fit",
        "variant",
        "identity",
        "tokenizer",
        "model",
        "optimizer",
        "torch_rng",
        "python_rng",
        "next_step",
        "next_document_cursor",
        "data_digest",
        "targets",
        "parameters",
    }
    if not isinstance(saved, dict) or set(saved) != required or saved.get("format") != FORMAT:
        raise ValueError("incompatible segment delta checkpoint")
    if (
        saved["boundary"] != "drained-document-optimizer"
        or saved["tokenizer"] != ByteTokenizer.fingerprint
        or saved["identity"] != identity
    ):
        raise ValueError("checkpoint boundary/tokenizer/source/data/runtime identity mismatch")
    if type(saved["next_step"]) is not int or not 1 <= saved["next_step"] <= 128:
        raise ValueError("invalid checkpoint step")
    if type(saved["targets"]) is not int or saved["targets"] < 1 or not finite_tensors(saved):
        raise ValueError("invalid checkpoint targets/values")
    try:
        config, fit = DeltaConfig(**saved["config"]), FitConfig(**saved["fit"])
        if saved["next_document_cursor"] != saved["next_step"] * fit.batch:
            raise ValueError("checkpoint document cursor mismatch")
        model = build_model(saved["variant"], config)
        if saved["parameters"] != sum(p.numel() for p in model.parameters()):
            raise ValueError("checkpoint parameter mismatch")
        model.load_state_dict(saved["model"], strict=True)
        optimizer = optimizer_for(model, fit)
        raw = saved["optimizer"]
        if len(raw["param_groups"]) != 1:
            raise ValueError("invalid optimizer parameter groups")
        expected = optimizer.state_dict()["param_groups"][0]
        if raw["param_groups"][0] != expected:
            raise ValueError("optimizer settings/parameter identities mismatch")
        optimizer.load_state_dict(raw)
        if len(optimizer.state) != len(list(model.parameters())):
            raise ValueError("missing optimizer moments")
        for parameter, moments in optimizer.state.items():
            if set(moments) != {"step", "exp_avg", "exp_avg_sq"} or (
                moments["exp_avg"].shape != parameter.shape
                or moments["exp_avg_sq"].shape != parameter.shape
                or moments["step"].numel() != 1
                or float(moments["step"]) != saved["next_step"]
            ):
                raise ValueError("optimizer moments/progress mismatch")
        torch.Generator().set_state(saved["torch_rng"])
        random.Random().setstate(saved["python_rng"])
    except (KeyError, TypeError, RuntimeError) as error:
        raise ValueError("invalid segment delta checkpoint payload") from error
    return model, optimizer, saved


def fit(
    variant: str,
    config: DeltaConfig,
    options: FitConfig,
    documents: list[dict[str, Any]],
    output: Path,
    identity: dict[str, str],
    *,
    steps: int = 128,
    resume: Path | None = None,
    trace_path: Path | None = None,
) -> dict[str, Any]:
    if type(steps) is not int or not 1 <= steps <= 128 or output.exists():
        raise ValueError("bounded steps and fresh checkpoint output required")
    if not documents or any(d.get("split") != "train" for d in documents):
        raise ValueError("training accepts training documents only")
    if len({d["id"] for d in documents}) != len(documents):
        raise ValueError("duplicate training document IDs")
    setup(options.seed, 1)
    model = build_model(variant, config)
    # Same-shaped backbone tensors share initial values across variants. No
    # training data or evaluation outcome influences initialization.
    own_rng = torch.get_rng_state()
    torch.manual_seed(options.seed)
    reference = build_model("recurrent", config)
    assert isinstance(reference, OwnedMemoryLM)
    torch.set_rng_state(own_rng)
    own = model.state_dict()
    for key, value in reference.backbone.state_dict().items():
        target = key if variant == "ordinary" else "backbone." + key
        if target in own and own[target].shape == value.shape:
            own[target] = value.clone()
    model.load_state_dict(own)
    optimizer = optimizer_for(model, options)
    first = targets = 0
    if resume is not None:
        model, optimizer, saved = load(resume, identity)
        if (
            saved["config"] != asdict(config)
            or saved["fit"] != asdict(options)
            or saved["variant"] != variant
            or saved["data_digest"] != data_digest(documents)
        ):
            raise ValueError("resume config/fit/data/variant mismatch")
        first, targets = saved["next_step"], saved["targets"]
        if first >= steps:
            raise ValueError("resume must extend optimizer boundary")
        torch.set_rng_state(saved["torch_rng"])
        random.setstate(saved["python_rng"])
    model.train()
    trace = []
    output.parent.mkdir(parents=True, exist_ok=True)
    # Incremental trace survives interruption; one receipt per completed update.
    with (trace_path or output.with_suffix(".trace.jsonl")).open("x", encoding="utf-8") as stream:
        for step in range(first, steps):
            optimizer.zero_grad(set_to_none=True)
            indices = train_indices(len(documents), step, options.batch, options.seed)
            losses, count = [], 0
            for index in indices:
                loss, n, _, _ = document_loss(
                    model, documents[index]["text"], maximum=config.maximum
                )
                losses.append(loss)
                count += n
            objective = torch.stack(losses).sum() / count
            if not torch.isfinite(objective):
                raise ValueError("nonfinite training objective")
            objective.backward()
            if any(p.grad is None or not torch.isfinite(p.grad).all() for p in model.parameters()):
                raise ValueError("missing/nonfinite parameter gradient")
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            if not finite_tensors(model.state_dict()):
                raise ValueError("nonfinite fitted weights")
            targets += count
            row = dict(
                step=step + 1,
                nll=float(objective.detach()),
                targets=count,
                ids=[documents[i]["id"] for i in indices],
                forward_positions=count,
            )
            trace.append(row)
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
    payload = dict(
        format=FORMAT,
        boundary="drained-document-optimizer",
        config=asdict(config),
        fit=asdict(options),
        variant=variant,
        identity=identity,
        tokenizer=ByteTokenizer.fingerprint,
        model=model.state_dict(),
        optimizer=optimizer.state_dict(),
        torch_rng=torch.get_rng_state(),
        python_rng=random.getstate(),
        next_step=steps,
        next_document_cursor=steps * options.batch,
        data_digest=data_digest(documents),
        targets=targets,
        parameters=sum(p.numel() for p in model.parameters()),
    )
    temporary = output.with_suffix(".partial")
    if temporary.exists():
        raise ValueError("partial checkpoint already exists")
    torch.save(payload, temporary)
    temporary.replace(output)
    return dict(
        parameters=payload["parameters"],
        targets=targets,
        next_step=steps,
        forward_positions=sum(r["forward_positions"] for r in trace),
        checkpoint_bytes=output.stat().st_size,
        trace=trace,
        gradient_parameters=sum(p.numel() for p in model.parameters() if p.grad is not None),
    )
