"""Controlled worlds v1. Oracle/labels are offline; ObservedPrompt is the runtime API."""

import hashlib
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from toruk_lm.data import sha256_file, write_json
from toruk_lm.engine import load_model, setup
from toruk_lm.model import generate
from toruk_lm.tokenizer import ByteTokenizer

SCHEMA = "toruk-worlds-v1"
KINDS = {"SET", "FIX", "CLAIM", "QUOTE", "IF", "DENY", "CONFLICT"}
AUTHORITATIVE = {"SET", "FIX"}
SPLITS = ("train", "validation", "test")
LEGEND = (
    "SET/FIX are verified records. CLAIM/QUOTE/IF/DENY do not update records. "
    "CONFLICT makes that attribute uncertain. Unknown or uncertain answer: ?.\n"
)
TEMPLATES = (
    "{kind} {entity}.{attribute}={value}.\n",
    "{kind}|{entity}|{attribute}|{value}\n",
    "{kind}: {attribute} of {entity} is {value}.\n",
    "[{kind}] {entity}/{attribute}/{value}\n",
    "{kind} (entity={entity}; attribute={attribute}; value={value})\n",
    "{kind} entry: {entity} -> {attribute} -> {value}\n",
)


@dataclass(frozen=True)
class ObservedPrompt:
    """No oracle, answer, world table, future observations or other questions."""

    history: str
    question: str

    def text(self) -> str:
        return self.history + self.question


def oracle(events: list[dict[str, str]], entity: str, attribute: str) -> str:
    """Independent backwards event query; never consult generator's forward table."""
    for event in reversed(events):
        if event["entity"] == entity and event["attribute"] == attribute:
            if event["kind"] == "CONFLICT":
                return "?"
            if event["kind"] == "SET" or event["kind"] == "FIX":
                return event["value"]
    return "?"


def question(entity: str, attribute: str) -> str:
    return f"Q:{entity}.{attribute}?\nA:"


def render(events: list[dict[str, str]], template: int) -> str:
    return LEGEND + "".join(TEMPLATES[template].format(**event) for event in events)


def make_world(seed: int, split: str, index: int) -> dict[str, Any]:
    if split not in SPLITS or index < 0:
        raise ValueError("invalid world split/index")
    split_index = SPLITS.index(split)
    rng = random.Random(f"{SCHEMA}/{seed}/{split}/{index}")
    # Assign split/world identity BEFORE generating events, questions or labels.
    identity = f"{split}-{seed}-{index:04d}"
    entity = f"e{split_index}{index:03d}"
    other = f"f{split_index}{index:03d}"
    template = index % 2 if split == "train" else split_index + 1
    corrections = 1 + index % 2 if split == "train" else split_index + 2
    events: list[dict[str, str]] = []
    truth: dict[tuple[str, str], str] = {}

    def add(kind: str, who: str, attribute: str, value: str) -> None:
        events.append(dict(kind=kind, entity=who, attribute=attribute, value=value))
        # Forward simulator deliberately differs from backwards-query oracle.
        if kind in AUTHORITATIVE:
            truth[who, attribute] = value
        elif kind == "CONFLICT":
            truth.pop((who, attribute), None)

    colors = rng.sample(["red", "blue", "green", "gold", "pink", "black"], 5)
    add("SET", entity, "color", colors[0])
    add("SET", entity, "name", rng.choice(["Ada", "Bo", "Cy", "Di"]))
    add("SET", other, "date", f"2026-10-{rng.randint(1, 28):02d}")
    add("SET", other, "count", str(rng.randint(10, 99)))
    add("SET", other, "color", colors[0])
    for i in range(corrections):
        add("FIX", entity, "color", colors[i + 1])
        add("CLAIM", entity, "name", "Wrong")
    add("CONFLICT", other, "color", colors[-1])
    # A visible kind is the sole authority cue; no hidden source credentials.
    for kind in ("QUOTE", "IF", "DENY"):
        add(kind, entity, "color", colors[0])
    distractors = 2 + index % 3
    for i in range(distractors):
        add("SET", f"d{split_index}{index:03d}{i}", "count", str(rng.randint(0, 9)))
    probes = []
    for who, attribute, group in (
        (entity, "color", "corrected"),
        (entity, "name", "unchanged_entity"),
        (other, "date", "unrelated_date"),
        (other, "count", "unrelated_number"),
        (entity, "missing", "unknown"),
        (other, "color", "ambiguous"),
    ):
        expected = truth.get((who, attribute), "?")
        if oracle(events, who, attribute) != expected:
            raise AssertionError("independent oracle disagrees with simulator")
        probes.append(
            dict(
                entity=who,
                attribute=attribute,
                group=group,
                answer=expected,
                question=question(who, attribute),
            )
        )
    return dict(
        schema=SCHEMA,
        id=identity,
        split=split,
        template=template,
        corrections=corrections,
        distractors=distractors,
        events=events,
        history=render(events, template),
        probes=probes,
    )


def make_worlds(output: Path, seed: int = 17, worlds_per_split: int = 8) -> dict[str, Any]:
    if worlds_per_split < 2:
        raise ValueError("at least two worlds per split")
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite a nonempty world dataset")
    output.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = dict(schema=SCHEMA, seed=seed, splits={})
    manifest["generator_sha256"] = sha256_file(Path(__file__))
    for split in SPLITS:
        rows = [make_world(seed, split, i) for i in range(worlds_per_split)]
        path = output / f"{split}.jsonl"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8"
        )
        # Ordinary LM training export; test answers are never exported for fitting.
        lm = output / f"{split}_lm.jsonl"
        if split != "test":
            examples = [
                dict(
                    id=f"{row['id']}-q{i}", text=row["history"] + p["question"] + p["answer"] + "\n"
                )
                for row in rows
                for i, p in enumerate(row["probes"])
            ]
            lm.write_text("".join(json.dumps(e) + "\n" for e in examples), encoding="utf-8")
        manifest["splits"][split] = dict(
            worlds=worlds_per_split,
            ids=[r["id"] for r in rows],
            templates=sorted({r["template"] for r in rows}),
            correction_counts=sorted({r["corrections"] for r in rows}),
            sha256=sha256_file(path),
            lm_sha256=sha256_file(lm) if split != "test" else None,
        )
    write_json(output / "manifest.json", manifest)
    return manifest


def load_worlds(path: Path, allowed_split: str) -> list[dict[str, Any]]:
    """Fail closed on stale bytes, forged labels, duplicates and split misuse."""
    if allowed_split not in SPLITS:
        raise ValueError("invalid allowed split")
    manifest = json.loads((path.parent / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("evaluation_only") and allowed_split != "validation":
        raise ValueError("held-out evaluation-only dataset cannot be used for training")
    if manifest.get("schema") != SCHEMA:
        raise ValueError("world schema mismatch")
    entry = manifest["splits"][allowed_split]
    if sha256_file(path) != entry["sha256"]:
        raise ValueError("world dataset fingerprint mismatch")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if not rows or [r["id"] for r in rows] != entry["ids"]:
        raise ValueError("world IDs mismatch/duplicates")
    all_ids = [identity for s in SPLITS for identity in manifest["splits"][s]["ids"]]
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("split world overlap")
    for row in rows:
        if row["schema"] != SCHEMA or row["split"] != allowed_split:
            raise ValueError("world split mismatch")
        if any(e["kind"] not in KINDS for e in row["events"]):
            raise ValueError("unsupported event kind")
        if row["history"] != render(row["events"], row["template"]):
            raise ValueError("rendered evidence mismatch")
        groups = [p["group"] for p in row["probes"]]
        if len(groups) != 6 or set(groups) != {
            "corrected",
            "unchanged_entity",
            "unrelated_date",
            "unrelated_number",
            "unknown",
            "ambiguous",
        }:
            raise ValueError("missing/duplicate probe groups")
        for probe in row["probes"]:
            if probe["answer"] != oracle(row["events"], probe["entity"], probe["attribute"]):
                raise ValueError("oracle label mismatch")
            if probe["question"] != question(probe["entity"], probe["attribute"]):
                raise ValueError("question mismatch")
    return rows


def observed(row: dict[str, Any], probe: dict[str, str]) -> ObservedPrompt:
    return ObservedPrompt(row["history"], probe["question"])


def summarize(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, Any] = {}
    for group in sorted({p["group"] for p in predictions}):
        subset = [p for p in predictions if p["group"] == group]
        groups[group] = dict(
            examples=len(subset),
            correct=sum(p["correct"] for p in subset),
            accuracy=sum(p["correct"] for p in subset) / len(subset),
        )
    return dict(
        examples=len(predictions),
        groups=groups,
        exact_accuracy=sum(p["correct"] for p in predictions) / len(predictions),
        answer_coverage=sum(p["answer"] not in ("", "?") for p in predictions) / len(predictions),
    )


def evaluate_worlds(
    checkpoint: Path, data: Path, output: Path, split: str = "validation", max_new_tokens: int = 16
) -> dict[str, Any]:
    if split == "test":
        raise ValueError("test access requires a separately frozen protocol; not enabled")
    if max_new_tokens <= 0:
        raise ValueError("positive generation budget required")
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a fresh evaluation directory")
    rows = load_worlds(data, split)
    setup(23, 1)
    started = time.perf_counter()
    model = load_model(checkpoint)
    model_load_seconds = time.perf_counter() - started
    tokenizer = ByteTokenizer()
    predictions = []
    for row in rows:
        for probe in row["probes"]:
            runtime = observed(row, probe)
            started = time.perf_counter()
            prefix = [tokenizer.bos_id, *tokenizer.encode(runtime.text())]
            tokens = generate(model, prefix, max_new_tokens)
            raw = tokenizer.decode(tokens)
            answer = raw.split("\n", 1)[0]
            elapsed = time.perf_counter() - started
            predictions.append(
                dict(
                    world_id=row["id"],
                    group=probe["group"],
                    question=runtime.question,
                    answer=answer,
                    generated=raw,
                    generated_ids=tokens,
                    gold=probe["answer"],
                    correct=answer == probe["answer"],
                    history_tokens=len(tokenizer.encode(runtime.history)),
                    input_tokens_read=len(prefix),
                    retained_context_tokens=min(len(prefix), model.config.context),
                    corrections=row["corrections"],
                    distractors=row["distractors"],
                    seconds=elapsed,
                )
            )
    metrics = summarize(predictions)
    elapsed = sum(p["seconds"] for p in predictions)
    metrics.update(
        schema=SCHEMA,
        variant="ordinary-local-context",
        split=split,
        model_load_seconds=model_load_seconds,
        end_to_end_seconds=elapsed,
        mean_answer_seconds=elapsed / len(predictions),
        input_tokens_read=sum(p["input_tokens_read"] for p in predictions),
        generated_tokens=sum(len(p["generated_ids"]) for p in predictions),
        checkpoint_sha256=sha256_file(checkpoint),
        data_sha256=sha256_file(data),
        tokenizer=ByteTokenizer.fingerprint,
        protocol="greedy first-line exact value; gold enters scoring only",
        peak_memory_bytes=None,
        uncertainty="one-seed pilot; no statistical claim",
    )
    write_json(output / "predictions.json", predictions)
    write_json(output / "metrics.json", metrics)
    write_json(
        output / "config.json",
        dict(
            checkpoint=str(checkpoint),
            data=str(data),
            split=split,
            max_new_tokens=max_new_tokens,
            runtime_fields=["history", "question"],
        ),
    )
    return metrics


def dataset_identity(path: Path) -> str:
    """Combined world/manifest identity for future experiment caches."""
    return hashlib.sha256(
        (sha256_file(path) + sha256_file(path.parent / "manifest.json")).encode()
    ).hexdigest()
