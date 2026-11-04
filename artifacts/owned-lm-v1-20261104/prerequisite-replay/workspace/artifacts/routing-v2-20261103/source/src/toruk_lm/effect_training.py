"""Offline paired labels/fit/diagnostics. Future probes/gold never enter runtime features."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import torch
from torch import Tensor

from toruk_lm.controlled import answer_loss, load_controlled, package_fingerprint
from toruk_lm.data import sha256_file, write_json
from toruk_lm.effect_predictor import EffectPredictor, features
from toruk_lm.engine import setup
from toruk_lm.recurrent import RecurrentLM, Session
from toruk_lm.tokenizer import ByteTokenizer
from toruk_lm.worlds import dataset_identity, load_worlds


def tensor_hash(value: Tensor) -> str:
    raw = bytes(value.detach().contiguous().view(torch.uint8).flatten().tolist())
    return hashlib.sha256(raw).hexdigest()


@torch.no_grad()
def paired_labels(
    checkpoint: Path,
    data: Path,
    output: Path,
    split: str = "train",
    limit: int = 8,
    seed: int = 23,
    answer_budget: int = 16,
) -> dict[str, Any]:
    if split not in ("train", "validation") or limit <= 0 or answer_budget <= 0:
        raise ValueError("invalid paired-label split/budget")
    setup(seed, 1)
    rows = load_worlds(data, split)[:limit]
    model, _ = load_controlled(checkpoint)
    if not isinstance(model, RecurrentLM):
        raise ValueError("paired labels require recurrent model")
    identity = dict(
        schema="effect-labels-v1",
        checkpoint_sha256=sha256_file(checkpoint),
        data=dataset_identity(data),
        code=package_fingerprint(),
        split=split,
        limit=limit,
        seed=seed,
        answer_budget=answer_budget,
        operations=["retain", "write"],
        boundary="last observed-history segment",
        width=model.config.width,
        slots=model.slots,
        target="retain NLL minus write NLL; nats/answer byte including newline",
    )
    path = output / "labels.json"
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached["identity"] != identity:
            raise ValueError("stale paired-label cache identity")
        payload = dict(features=cached["features"], labels=cached["labels"])
        if (
            cached["payload_sha256"]
            != hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        ):
            raise ValueError("corrupt paired-label cache")
        return cached
    if output.exists() and any(output.iterdir()):
        raise ValueError("incomplete label directory; use a fresh destination")
    weights = {k: v.clone() for k, v in model.state_dict().items()}
    tokenizer = ByteTokenizer()
    inputs, labels = [], []
    forwarded, scored_targets, generation_forwarded = 0, 0, 0
    started = time.perf_counter()
    for row in rows:
        history = [1, *tokenizer.encode(row["history"])]
        state = model.initial_state()
        previous, proposed, summary = state, state, state.mean(1)
        for start in range(0, len(history), model.config.context):
            segment = history[start : start + model.config.context]
            previous = state.clone()
            _, proposed, summary = model(torch.tensor([segment]), previous)
            state = proposed
            forwarded += len(segment)
        # Capture features BEFORE accessing any question/answer/probe table.
        inputs.append(features(previous, proposed, summary)[0].tolist())
        initial_hash = tensor_hash(previous)
        branches: list[dict[str, Any]] = []
        for operation, candidate in (("retain", previous), ("write", proposed)):
            branch = candidate.clone()
            total_loss, count, correct, raw = 0.0, 0, 0, []
            for probe in row["probes"]:
                prompt = tokenizer.encode(probe["question"])
                target = tokenizer.encode(probe["answer"] + "\n")
                loss, n, work = answer_loss(model, history, branch.clone(), prompt, target)
                total_loss, count = total_loss + float(loss), count + n
                forwarded, scored_targets = forwarded + work, scored_targets + n
                session = Session(model)
                session.memory = branch.clone()
                tokens = session.generate(prompt, answer_budget)
                generation_forwarded += session.forward_tokens
                answer = tokenizer.decode(tokens).split("\n", 1)[0]
                correct += answer == probe["answer"]
                raw.append(
                    dict(
                        question=probe["question"],
                        group=probe["group"],
                        generated_ids=tokens,
                        answer=answer,
                        gold=probe["answer"],
                    )
                )
            branches.append(
                dict(
                    operation=operation,
                    initial_state_sha256=initial_hash,
                    candidate_state_sha256=tensor_hash(branch),
                    nll=total_loss / count,
                    targets=count,
                    correct=correct,
                    probes=raw,
                )
            )
        assert branches[0]["targets"] == branches[1]["targets"]
        assert tensor_hash(previous) == initial_hash
        labels.append(
            dict(
                world_id=row["id"],
                boundary_tokens=len(history),
                branches=branches,
                effect=branches[0]["nll"] - branches[1]["nll"],
            )
        )
    if any(not torch.equal(weights[k], v) for k, v in model.state_dict().items()):
        raise AssertionError("branch evaluation mutated model weights")
    payload = dict(features=inputs, labels=labels)
    result = dict(
        identity=identity,
        **payload,
        payload_sha256=hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        cost=dict(
            seconds=time.perf_counter() - started,
            label_forward_tokens=forwarded,
            scored_targets=scored_targets,
            generation_forward_tokens=generation_forwarded,
            branches=2 * len(rows),
            peak_memory_bytes=None,
        ),
        no_weight_updates=True,
    )
    write_json(path, result)
    return result


def fit_effect(train_path: Path, output: Path, steps: int = 100, seed: int = 23) -> dict[str, Any]:
    if steps <= 0 or (output.exists() and any(output.iterdir())):
        raise ValueError("positive steps and fresh output required")
    data = json.loads(train_path.read_text(encoding="utf-8"))
    if data["identity"]["split"] != "train" or data["identity"]["code"] != package_fingerprint():
        raise ValueError("predictor fit requires current training labels")
    payload = dict(features=data["features"], labels=data["labels"])
    if (
        data["payload_sha256"]
        != hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    ):
        raise ValueError("corrupt training labels")
    setup(seed, 1)
    x = torch.tensor(data["features"], dtype=torch.float32)
    y = torch.tensor([r["effect"] for r in data["labels"]], dtype=torch.float32)
    if len(x) < 2 or not torch.isfinite(x).all() or not torch.isfinite(y).all():
        raise ValueError("need at least two finite training label rows")
    predictor = EffectPredictor(x.shape[1])
    predictor.mean.copy_(x.mean(0))
    predictor.scale.copy_(x.std(0, unbiased=False).clamp_min(1e-4))
    predictor.target_mean.copy_(y.mean())
    predictor.target_scale.copy_(y.std(unbiased=False).clamp_min(1e-6))
    predictor.support.copy_(((x - predictor.mean) / predictor.scale).abs().amax(0) + 1)
    predictor.metadata = {**data["identity"], "training_labels_sha256": sha256_file(train_path)}
    state_size = data["identity"]["width"] * data["identity"]["slots"]
    distances = (x[:, state_size : 2 * state_size] - x[:, :state_size]).square().mean(1).sqrt()
    predictor.metadata["heuristic_threshold"] = float(distances.median())
    optimizer = torch.optim.AdamW(predictor.parameters(), lr=0.01)
    started = time.perf_counter()
    gradients = []
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = (((predictor(x) - y) / predictor.target_scale) ** 2).mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite effect loss")
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(predictor.parameters(), 10.0, error_if_nonfinite=True)
        gradients.append(float(norm))
        optimizer.step()
    elapsed = time.perf_counter() - started
    output.mkdir(parents=True, exist_ok=True)
    predictor.eval()
    torch.save(
        dict(
            format="toruk-effect-v1",
            inputs=x.shape[1],
            hidden=16,
            model=predictor.state_dict(),
            metadata=predictor.metadata,
        ),
        output / "predictor.pt",
    )
    metrics = dict(
        steps=steps,
        seed=seed,
        parameters=sum(p.numel() for p in predictor.parameters()),
        training_seconds=elapsed,
        normalized_mse=float(loss.detach()),
        max_gradient_norm=max(gradients),
        labels=sha256_file(train_path),
        predictor_sha256=sha256_file(output / "predictor.pt"),
    )
    write_json(output / "metrics.json", metrics)
    return metrics


@torch.no_grad()
def evaluate_effect(predictor_path: Path, label_path: Path, output: Path) -> dict[str, Any]:
    if output.exists() and any(output.iterdir()):
        raise ValueError("fresh effect evaluation output required")
    data = json.loads(label_path.read_text(encoding="utf-8"))
    payload = dict(features=data["features"], labels=data["labels"])
    if (
        data["identity"]["code"] != package_fingerprint()
        or data["payload_sha256"]
        != hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    ):
        raise ValueError("stale/corrupt evaluation labels")
    predictor = EffectPredictor.load(predictor_path, data["identity"]["checkpoint_sha256"])
    if data["identity"]["split"] != "validation":
        raise ValueError("effect diagnostics require validation labels")
    x = torch.tensor(data["features"], dtype=torch.float32)
    target = torch.tensor([r["effect"] for r in data["labels"]])
    started = time.perf_counter()
    for _ in range(32):
        prediction = predictor(x)
    latency = (time.perf_counter() - started) / (32 * len(x))
    within = (((x - predictor.mean) / predictor.scale).abs() <= predictor.support).all(1)
    chosen = (prediction > 0) & within
    shuffled = chosen[torch.randperm(len(chosen), generator=torch.Generator().manual_seed(23))]
    # The heuristic uses only the magnitude of the observed final proposal change.
    state_size = predictor.metadata["width"] * predictor.metadata["slots"]
    distance = (x[:, state_size : 2 * state_size] - x[:, :state_size]).square().mean(1).sqrt()
    heuristic = distance > predictor.metadata["heuristic_threshold"]
    policies = {
        "retain": torch.zeros_like(chosen),
        "write": torch.ones_like(chosen),
        "predictor": chosen,
        "heuristic": heuristic,
        "shuffled": shuffled,
        "oracle": target > 0,
    }
    policies_metrics = {}
    for name, decisions in policies.items():
        selected = target * decisions
        policies_metrics[name] = dict(
            mean_regret_nats=float((target.clamp_min(0) - selected).mean()),
            write_rate=float(decisions.float().mean()),
        )
    harmful = target < -1e-6
    predicted_harmful = prediction < -1e-6
    true_positive = int((harmful & predicted_harmful).sum())
    calibration = []
    for indices in torch.tensor_split(prediction.argsort(), min(4, len(x))):
        calibration.append(
            dict(
                count=len(indices),
                predicted=float(prediction[indices].mean()),
                observed=float(target[indices].mean()),
            )
        )
    result = dict(
        rmse_nats=float(((prediction - target) ** 2).mean().sqrt()),
        mae_nats=float((prediction - target).abs().mean()),
        sign_ranking_accuracy=float(((prediction > 0) == (target > 0)).float().mean()),
        harmful_examples=int(harmful.sum()),
        harmful_recall=true_positive / int(harmful.sum()) if harmful.any() else None,
        harmful_precision=true_positive / int(predicted_harmful.sum())
        if predicted_harmful.any()
        else None,
        calibration=calibration,
        policies=policies_metrics,
        inference_seconds_per_example=latency,
        ood_fallbacks=int((~within).sum()),
        raw=[
            dict(world_id=r["world_id"], effect=float(y), prediction=float(p), chosen_write=bool(c))
            for r, y, p, c in zip(data["labels"], target, prediction, chosen, strict=True)
        ],
    )
    write_json(output / "metrics.json", result)
    return result
