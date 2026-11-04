"""One-document CPU training and generated-answer evaluation for the M3 prerequisite."""

import hashlib
import json
import random
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch
from torch import Tensor

from toruk_lm.data import sha256_file, write_json
from toruk_lm.effect_predictor import EffectPredictor
from toruk_lm.engine import setup
from toruk_lm.model import CausalLM, ModelConfig, generate, loss_sum
from toruk_lm.recurrent import Decision, RecurrentLM, Session
from toruk_lm.tokenizer import ByteTokenizer
from toruk_lm.worlds import dataset_identity, load_worlds, summarize

ControlledModel = CausalLM | RecurrentLM


def package_fingerprint() -> str:
    files = {p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def history_pass(
    model: ControlledModel,
    tokens: list[int],
    max_segments: int = 32,
    decision: Decision | None = None,
    reset_memory: bool = False,
) -> tuple[Tensor | None, Tensor, int]:
    if len(tokens) > max_segments * model.config.context:
        raise ValueError("document exceeds bounded unroll budget")
    memory = model.initial_state() if isinstance(model, RecurrentLM) else None
    total = next(model.parameters()).sum() * 0
    count = 0
    for start in range(0, len(tokens), model.config.context):
        inputs = tokens[start : start + model.config.context]
        x = torch.tensor([inputs])
        targets = tokens[start + 1 : start + len(inputs) + 1]
        targets += [-100] * (len(inputs) - len(targets))
        if isinstance(model, RecurrentLM):
            assert memory is not None
            old = memory
            logits, memory, summary = model(x, old)
            if reset_memory:
                memory = model.initial_state()
            elif start + model.config.context >= len(tokens) and decision is not None:
                if not decision(old, memory, summary):
                    memory = old
        else:
            logits = model(x)
        if any(t != -100 for t in targets):
            summed, n = loss_sum(logits, torch.tensor([targets]))
            total, count = total + summed, count + n
    return memory, total, count


def revision_objective(groups: dict[str, tuple[Tensor, int]], objective: str) -> Tensor:
    """Offline supervised loss only; no gold values are exported to runtime state."""
    if objective not in ("qa", "revision", "no-correction", "no-preservation"):
        raise ValueError("unknown controlled objective")
    if not groups or any(count <= 0 for _, count in groups.values()):
        raise ValueError("revision groups require valid targets")
    if objective == "qa":
        return torch.stack([total for total, _ in groups.values()]).sum() / sum(
            n for _, n in groups.values()
        )
    correction = groups["corrected"][0] / groups["corrected"][1]
    preservation = torch.stack(
        [
            total / n
            for name, (total, n) in groups.items()
            if name.startswith(("unrelated", "unchanged"))
        ]
    ).mean()
    uncertain = torch.stack(
        [groups[name][0] / groups[name][1] for name in ("unknown", "ambiguous")]
    ).mean()
    return (
        correction * (objective != "no-correction")
        + preservation * (objective != "no-preservation")
        + 0.1 * uncertain
    )


def answer_loss(
    model: ControlledModel,
    history: list[int],
    memory: Tensor | None,
    prompt: list[int],
    answer: list[int],
) -> tuple[Tensor, int, int]:
    """Teacher-forced training/scoring only. Runtime generation has a separate API."""
    if not prompt or not answer:
        raise ValueError("nonempty prompt and answer required")
    total = next(model.parameters()).sum() * 0
    forwarded = 0
    if isinstance(model, RecurrentLM):
        assert memory is not None
        state = memory.clone()
        sequence = prompt + answer
        for start in range(0, len(sequence) - 1, model.config.context):
            inputs = sequence[start : min(start + model.config.context, len(sequence) - 1)]
            targets = [
                sequence[t + 1] if t >= len(prompt) - 1 else -100
                for t in range(start, start + len(inputs))
            ]
            logits, state, _ = model(torch.tensor([inputs]), state)
            forwarded += len(inputs)
            if any(t != -100 for t in targets):
                summed, _ = loss_sum(logits, torch.tensor([targets]))
                total = total + summed
    else:
        prefix = history + prompt
        for token in answer:
            x = torch.tensor([prefix[-model.config.context :]])
            logits = model(x)[:, -1:]
            summed, _ = loss_sum(logits, torch.tensor([[token]]))
            total = total + summed
            forwarded += x.numel()
            prefix.append(token)
    return total, len(answer), forwarded


def load_controlled(path: Path) -> tuple[ControlledModel, dict[str, Any]]:
    saved: dict[str, Any] = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(saved, dict):
        raise ValueError("controlled checkpoint must be a dictionary")
    if saved.get("format") != "toruk-controlled-v1" or saved.get("boundary") != "drained-document":
        raise ValueError("unsupported controlled checkpoint/resume boundary")
    if saved.get("tokenizer") != ByteTokenizer.fingerprint:
        raise ValueError("tokenizer mismatch")
    config = ModelConfig(**saved["config"]["model"])
    model: ControlledModel
    if saved["config"]["variant"] == "recurrent":
        model = RecurrentLM(config, saved["config"]["slots"])
    elif saved["config"]["variant"] == "ordinary":
        model = CausalLM(config)
    else:
        raise ValueError("unknown model variant")
    try:
        model.load_state_dict(saved["model"])
    except (RuntimeError, TypeError) as error:
        raise ValueError(f"controlled checkpoint model state mismatch: {error}") from error
    for name, parameter in model.named_parameters():
        if not torch.isfinite(parameter).all():
            raise ValueError(f"controlled checkpoint contains nonfinite model weights: {name}")
    model.eval()
    return model, saved


def train_controlled(
    train_data: Path,
    validation: Path,
    output: Path,
    variant: str,
    steps: int = 12,
    seed: int = 23,
    slots: int = 4,
    config: ModelConfig | None = None,
    resume: Path | None = None,
    max_segments: int = 32,
    objective: str = "qa",
) -> dict[str, Any]:
    if variant not in ("ordinary", "recurrent") or steps <= 0 or max_segments < 2:
        raise ValueError("invalid variant/step/unroll budget")
    if objective not in ("qa", "revision", "no-correction", "no-preservation"):
        raise ValueError("unknown objective")
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh training directory")
    rows = load_worlds(train_data, "train")
    load_worlds(validation, "validation")
    setup(seed, 1)
    model_config = config or ModelConfig()
    settings = dict(
        model=asdict(model_config),
        variant=variant,
        seed=seed,
        slots=slots,
        max_segments=max_segments,
        lm_weight=0.1,
        answer_weight=1.0,
        lr=0.003,
        batch_worlds=1,
        unroll="whole bounded document; no live-graph steps",
        objective=objective,
    )
    identities = dict(train=dataset_identity(train_data), validation=dataset_identity(validation))
    model: ControlledModel = (
        RecurrentLM(model_config, slots) if variant == "recurrent" else CausalLM(model_config)
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003)
    first = 0
    if resume:
        model, saved = load_controlled(resume)
        if (
            saved["config"] != settings
            or saved["data"] != identities
            or saved["package_sha256"] != package_fingerprint()
        ):
            raise ValueError("resume configuration/data/code mismatch")
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.003)
        optimizer.load_state_dict(saved["optimizer"])
        random.setstate(saved["python_rng"])
        torch.set_rng_state(saved["torch_rng"])
        first = saved["next_step"]
        if first >= steps:
            raise ValueError("resume steps must exceed saved total")
    tokenizer = ByteTokenizer()
    losses = []
    input_tokens, valid_targets = 0, 0
    started = time.perf_counter()
    model.train()
    for step in range(first, steps):
        epoch, offset = divmod(step, len(rows))
        order = list(range(len(rows)))
        random.Random(seed + epoch).shuffle(order)
        row = rows[order[offset]]
        history = [1, *tokenizer.encode(row["history"])]
        optimizer.zero_grad(set_to_none=True)
        memory, lm_sum, lm_count = history_pass(model, history, max_segments)
        groups: dict[str, tuple[Tensor, int]] = {}
        qa_count, forwarded = 0, 0
        for probe in row["probes"]:
            summed, count, work = answer_loss(
                model,
                history,
                memory,
                tokenizer.encode(probe["question"]),
                tokenizer.encode(probe["answer"] + "\n"),
            )
            groups[probe["group"]] = (summed, count)
            qa_count, forwarded = qa_count + count, forwarded + work
        loss = revision_objective(groups, objective) + 0.1 * lm_sum / lm_count
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite controlled loss")
        loss.backward()
        for name, parameter in model.named_parameters():
            if parameter.grad is None or not torch.isfinite(parameter.grad).all():
                raise FloatingPointError(f"missing/nonfinite gradient: {name}")
        writer_norm = None
        if isinstance(model, RecurrentLM):
            writer_gradient = model.proposal.weight.grad
            assert writer_gradient is not None
            writer_norm = float(writer_gradient.norm())
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
        optimizer.step()
        input_tokens += len(history) + forwarded
        valid_targets += lm_count + qa_count
        losses.append(
            dict(
                step=step + 1,
                world_id=row["id"],
                loss=float(loss.detach()),
                writer_gradient_norm=writer_norm,
                gradient_norm=float(norm),
            )
        )
    elapsed = time.perf_counter() - started
    output.mkdir(parents=True, exist_ok=True)
    saved = dict(
        format="toruk-controlled-v1",
        boundary="drained-document",
        config=settings,
        model=model.state_dict(),
        optimizer=optimizer.state_dict(),
        next_step=steps,
        python_rng=random.getstate(),
        torch_rng=torch.get_rng_state(),
        tokenizer=ByteTokenizer.fingerprint,
        data=identities,
        package_sha256=package_fingerprint(),
    )
    temporary = output / "checkpoint.pt.tmp"
    torch.save(saved, temporary)
    temporary.replace(output / "checkpoint.pt")
    metrics = dict(
        variant=variant,
        steps_this_invocation=steps - first,
        total_steps=steps,
        model_input_token_evaluations=input_tokens,
        valid_targets=valid_targets,
        training_seconds=elapsed,
        tokens_per_second=input_tokens / elapsed,
        parameters=sum(p.numel() for p in model.parameters()),
        memory_state_bytes=slots * model_config.width * 4 if variant == "recurrent" else 0,
        seed=seed,
        losses=losses,
        config=settings,
        data=identities,
        peak_memory_bytes=None,
        checkpoint_sha256=sha256_file(output / "checkpoint.pt"),
        package_sha256=package_fingerprint(),
    )
    write_json(output / "metrics.json", metrics)
    write_json(output / "config.json", settings)
    return metrics


@torch.no_grad()
def evaluate_controlled(
    checkpoint: Path,
    data: Path,
    output: Path,
    budget: int = 16,
    policy: str = "write",
    predictor_path: Path | None = None,
) -> dict[str, Any]:
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh evaluation directory")
    if budget <= 0:
        raise ValueError("positive answer budget required")
    rows = load_worlds(data, "validation")
    setup(23, 1)
    started = time.perf_counter()
    model, saved = load_controlled(checkpoint)
    if policy not in ("write", "retain", "predictor", "heuristic", "random", "reset"):
        raise ValueError("unknown runtime policy")
    if policy != "write" and not isinstance(model, RecurrentLM):
        raise ValueError("memory policy requires recurrent model")
    predictor = None
    if policy in ("predictor", "heuristic"):
        if predictor_path is None:
            raise ValueError("predictor artifact required for policy")
        predictor = EffectPredictor.load(predictor_path, sha256_file(checkpoint))
    decisions: list[bool] = []
    rng = random.Random(23)

    def decide(previous: Tensor, proposed: Tensor, summary: Tensor) -> bool:
        if policy == "predictor":
            assert predictor is not None
            accept = predictor.recommend(previous, proposed, summary)
        elif policy == "heuristic":
            assert predictor is not None
            accept = (
                float((proposed - previous).square().mean().sqrt())
                > predictor.metadata["heuristic_threshold"]
            )
        elif policy == "random":
            accept = bool(rng.getrandbits(1))
        else:
            accept = policy == "write"
        decisions.append(accept)
        return accept

    load_seconds = time.perf_counter() - started
    tokenizer = ByteTokenizer()
    predictions = []
    total_seconds, history_tokens, forwarded, qa_sum, qa_count, lm_sum, lm_count = (
        0.0,
        0,
        0,
        0.0,
        0,
        0.0,
        0,
    )
    for row in rows:
        started = time.perf_counter()
        history = [1, *tokenizer.encode(row["history"])]
        memory, summed, count = history_pass(
            model,
            history,
            saved["config"]["max_segments"],
            decide if isinstance(model, RecurrentLM) else None,
            policy == "reset",
        )
        lm_sum, lm_count = lm_sum + float(summed), lm_count + count
        history_tokens += len(history)
        forwarded += len(history)
        total_seconds += time.perf_counter() - started
        for probe in row["probes"]:
            started = time.perf_counter()
            prompt = tokenizer.encode(probe["question"])
            if isinstance(model, RecurrentLM):
                session = Session(model)
                assert memory is not None
                session.memory = memory.clone()
                if policy == "reset":
                    session.decide = lambda previous, proposed, summary: False
                tokens = session.generate(prompt, budget)
                work = session.forward_tokens
            else:
                tokens = generate(model, history + prompt, budget)
                work = sum(
                    min(len(history) + len(prompt) + i, model.config.context)
                    for i in range(len(tokens))
                )
            generated = tokenizer.decode(tokens)
            answer = generated.split("\n", 1)[0]
            seconds = time.perf_counter() - started
            total_seconds += seconds
            forwarded += work
            # Future/gold scoring is separate from generation and its timing/work.
            scored, n, scoring_work = answer_loss(
                model, history, memory, prompt, tokenizer.encode(probe["answer"] + "\n")
            )
            qa_sum, qa_count = qa_sum + float(scored), qa_count + n
            predictions.append(
                dict(
                    world_id=row["id"],
                    group=probe["group"],
                    question=probe["question"],
                    generated=generated,
                    generated_ids=tokens,
                    answer=answer,
                    gold=probe["answer"],
                    correct=answer == probe["answer"],
                    seconds=seconds,
                    history_tokens=len(history),
                    corrections=row["corrections"],
                    distractors=row["distractors"],
                    forward_tokens=work,
                    teacher_forced_forward_tokens=scoring_work,
                )
            )
    metrics = summarize(predictions)
    metrics.update(
        config=saved["config"],
        checkpoint_sha256=sha256_file(checkpoint),
        data=dataset_identity(data),
        package_sha256=package_fingerprint(),
        history_lm_loss=lm_sum / lm_count,
        teacher_forced_answer_loss=qa_sum / qa_count,
        model_load_seconds=load_seconds,
        inference_seconds=total_seconds,
        observed_history_tokens=history_tokens,
        question_tokens=sum(len(tokenizer.encode(p["question"])) for p in predictions),
        generated_tokens=sum(len(p["generated_ids"]) for p in predictions),
        inference_forward_tokens=forwarded,
        scoring_forward_tokens=sum(p["teacher_forced_forward_tokens"] for p in predictions),
        peak_memory_bytes=None,
        uncertainty="single-seed tiny validation pilot",
        policy=policy,
        decision_point="last observed-history boundary only",
        final_boundary_writes=sum(decisions),
        final_boundaries=len(decisions),
        predictor_fallbacks=predictor.fallbacks if predictor else 0,
        active_predictor_parameters=sum(p.numel() for p in predictor.parameters())
        if predictor is not None and policy == "predictor"
        else 0,
        predictor_sha256=sha256_file(predictor_path) if predictor_path else None,
    )
    write_json(output / "predictions.json", predictions)
    write_json(output / "metrics.json", metrics)
    return metrics
