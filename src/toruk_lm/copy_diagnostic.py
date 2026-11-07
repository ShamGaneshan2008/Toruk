"""Matched-position exact-copy diagnostic; separate from all existing chat paths."""

import hashlib
import json
import random
import time
from typing import Any

import torch
from torch import nn

from toruk_lm.owned_lm import OwnedMemoryLM, OwnedModel, OwnedSession
from toruk_lm.owned_training import memory_bytes
from toruk_lm.tokenizer import ByteTokenizer

KINDS = ("value", "exact", "unknown")


def make_cases(
    split: str, seed: int, worlds: int, gaps: list[int], prefix_bytes: int
) -> list[dict[str, Any]]:
    if not 1 <= worlds <= 16 or not gaps or min(gaps) < 0 or prefix_bytes > 367:
        raise ValueError("copy probe bounds exceeded")
    rng = random.Random(seed)
    rows = []
    for kind in KINDS:
        for index in range(worlds):
            entity = rng.choice(("Ada", "Bo", "Cy", "Dee"))
            expected = (
                rng.choice(("red", "blue", "gold", "lime"))
                if kind == "value"
                else "?"
                if kind == "unknown"
                else "".join(rng.choice("aKpQz0279-/_+!") for _ in range(6))
            )
            evidence = (
                f"{entity} visited the park.\n"
                if kind == "unknown"
                else f"{entity}'s tag is {expected}.\n"
            )
            instruction = "If unknown answer ?.\n"
            question = f"Answer {entity}'s tag? "
            padding_size = prefix_bytes - len((instruction + evidence + question).encode())
            if padding_size < max(gaps):
                raise ValueError("gap does not fit fixed total prefix")
            padding = ""
            while len(padding) < padding_size:
                padding += f"Note {rng.randrange(1000)}: {rng.choice(('rain', 'wind', 'sun'))}.\n"
            padding = padding[:padding_size]
            for gap in gaps:
                cut = padding_size - gap
                history = instruction + padding[:cut] + evidence + padding[cut:]
                rows.append(
                    dict(
                        id=f"{split}-{kind}-{index}-g{gap}",
                        world_id=f"{split}-{kind}-{index}",
                        split=split,
                        kind=kind,
                        gap=gap,
                        history=history,
                        question=question,
                        expected=expected,
                        evidence=evidence,
                        prefix_bytes=prefix_bytes,
                    )
                )
    return rows


@torch.no_grad()
def generate(
    model: OwnedModel, history: str, question: str, budget: int, *, query_read_off: bool = False
) -> dict[str, Any]:
    if not history or not question or len((history + question).encode()) + 1 + budget > 384:
        raise ValueError("probe requires nonempty phases and <=384 total token positions")
    if not 1 <= budget <= 16:
        raise ValueError("probe output budget must be 1..16")
    if query_read_off and not isinstance(model, OwnedMemoryLM):
        raise ValueError("query read gate requires an owned memory model")
    timings = {"reader_ms": 0.0, "writer_linears_ms": 0.0}
    counts = {"reader_calls": 0, "writer_linear_calls": 0}
    hooks: list[Any] = []
    starts: dict[str, float] = {}

    def hook_pair(name: str, metric: str, counter: str) -> tuple[Any, Any]:
        def before(module: nn.Module, args: tuple[Any, ...]) -> None:
            starts[name] = time.perf_counter()

        def after(module: nn.Module, args: tuple[Any, ...], output: Any) -> None:
            timings[metric] += (time.perf_counter() - starts[name]) * 1000
            counts[counter] += 1

        return before, after

    if isinstance(model, OwnedMemoryLM):
        modules = [
            (f"reader-{i}", module, "reader_ms", "reader_calls")
            for i, module in enumerate(model.readers)
        ]
        modules += [
            ("proposal", model.proposal, "writer_linears_ms", "writer_linear_calls"),
            ("gate", model.gate, "writer_linears_ms", "writer_linear_calls"),
        ]
        for name, module, metric, counter in modules:
            pre, post = hook_pair(name, metric, counter)
            hooks += [module.register_forward_pre_hook(pre), module.register_forward_hook(post)]
    started, cpu_started = time.perf_counter(), time.process_time()
    before_memory = memory_bytes()
    try:
        token_start = time.perf_counter()
        history_ids = [1, *ByteTokenizer().encode(history)]
        question_ids = ByteTokenizer().encode(question)
        tokenize_ms = (time.perf_counter() - token_start) * 1000
        session = OwnedSession(model)
        history_start = time.perf_counter()
        session.consume(history_ids)
        history_ms = (time.perf_counter() - history_start) * 1000
        state_hash = (
            hashlib.sha256(json.dumps(session.state.tolist()).encode()).hexdigest()
            if session.state is not None
            else None
        )
        history_reader_calls = counts["reader_calls"]
        session.read = not query_read_off
        query_start = time.perf_counter()
        logits = session.consume(question_ids)
        query_ms = (time.perf_counter() - query_start) * 1000
        decode_start = time.perf_counter()
        generated = []
        for _ in range(budget):
            scores = logits.clone()
            scores[:2] = -torch.inf
            token = int(scores.argmax().item())
            generated.append(token)
            if token == 2:
                break
            logits = session.consume([token])
        decode_ms = (time.perf_counter() - decode_start) * 1000
        result: dict[str, Any] = dict(
            answer=ByteTokenizer().decode(generated),
            generated_ids=generated,
            input_tokens=len(history_ids) + len(question_ids),
            output_tokens=len(generated),
            forward_positions=session.forward_positions,
            memory_commits=session.commits,
            state_bytes=session.state.numel() * session.state.element_size()
            if session.state is not None
            else 0,
            history_state_sha256=state_hash,
            history_reader_calls=history_reader_calls,
            query_answer_reader_calls=counts["reader_calls"] - history_reader_calls,
            selector_work=0,
            tokenization_ms=tokenize_ms,
            history_ms=history_ms,
            query_ms=query_ms,
            decode_ms=decode_ms,
            **timings,
            **counts,
        )
    finally:
        for hook in hooks:
            hook.remove()
    result.update(
        seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu_started,
        memory_before=before_memory,
        memory_after=memory_bytes(),
        memory_timing_scope=(
            "Reader and writer linear modules only; excludes norms/nonlinearities/hook overhead. "
            "Total phase timings include all operations."
        ),
    )
    return result
