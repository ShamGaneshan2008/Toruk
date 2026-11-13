"""Fresh development-only grammar, frozen byte scorer and gates. Never loads old cases."""

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


CATEGORIES = ("distant", "correction", "related_field", "unknown", "exact_copy", "local")
NAMES = ("uvo", "pex", "zim", "nax")
VALUES = ("la", "mi", "so", "tu")
CODES = ("R-7", "Q_2", "V:4", "Z!6")


def factual(split: str, count: int, seed: int) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    inputs, labels = [], []
    for i in range(count):
        category = CATEGORIES[i % 6]
        group = i // 6
        name = rng.choice(NAMES)
        other = next(n for n in NAMES if n != name)
        value = rng.choice(VALUES)
        old = next(v for v in VALUES if v != value)
        field = "code" if category == "exact_copy" else "city"
        if field == "code":
            value = CODES[group % 4]
        gap = (32, 64, 96, 128)[group % 4]
        # A split-specific nonce makes full train/dev texts disjoint; shared
        # entities/grammar/value inventory are an explicitly IID limitation.
        filler = ((f"wind {split[0]}{i:03d} hums. " + "rain falls. " * 12)[:gap]) + "\n"
        evidence = f"{name} {field}={value}\n"
        if category == "unknown":
            history = f"{name} role={old}\n" + filler
            value = "?"
        elif category == "local":
            history = filler + evidence
        elif category == "correction":
            history = f"{name} city={old}\n" + "rain falls.\n" + evidence + filler
        elif category == "related_field":
            history = evidence + f"{name} role={old}\n{other} city={old}\n" + filler
        else:
            history = evidence + filler
        question = f"{name} {field}?="
        prefix = history + question
        source_end = history.rfind(evidence) + len(evidence) if category != "unknown" else None
        labels.append(
            dict(
                id=f"{split}-f{i:03d}",
                category=category,
                gold=value,
                distance=len(prefix.encode()) - source_end if source_end is not None else None,
                gap_segments=(len(prefix.encode()) - source_end) // 24 if source_end else None,
            )
        )
        inputs.append(dict(id=f"{split}-f{i:03d}", prefix=prefix))
    return inputs, labels


def prose(split: str, count: int) -> list[dict]:
    return [
        dict(
            id=f"{split}-p{i:03d}",
            text=f"The {('quiet', 'small', 'warm', 'blue')[i % 4]} room has a lamp. "
            f"Rain falls and the wind hums. Note {split[0]}{i:03d}.\n",
        )
        for i in range(count)
    ]


def validate(
    train: list[dict], inputs: list[dict], labels: list[dict], dev_prose: list[dict]
) -> None:
    if {r["id"] for r in inputs} != {r["id"] for r in labels}:
        raise ValueError("input/label identities differ")
    ids = [r["id"] for r in [*train, *inputs, *dev_prose]]
    if len(ids) != len(set(ids)):
        raise ValueError("document IDs overlap")
    development = {r["prefix"] + label["gold"] for r, label in zip(inputs, labels, strict=True)}
    development |= {r["text"] for r in dev_prose}
    if development & {r["text"] for r in train}:
        raise ValueError("train/dev texts overlap")
    if any(len(r["text"].encode()) + 1 > 192 or r["split"] != "train" for r in train):
        raise ValueError("training split or BPTT bound")
    for row, label in zip(inputs, labels, strict=True):
        history, query = row["prefix"].rsplit("\n", 1)
        name, field = query[:-2].split()
        records = [
            line.split("=", 1)[1]
            for line in history.splitlines()
            if line.startswith(f"{name} {field}=")
        ]
        independent = records[-1] if records else "?"
        if independent != label["gold"]:
            raise ValueError("label/source mismatch")
        if len(row["prefix"].encode()) + len(label["gold"].encode()) + 1 > 192:
            raise ValueError("development BPTT bound")
        if label["category"] in {"distant", "correction", "related_field", "exact_copy"}:
            if label["distance"] <= 24:
                raise ValueError("distant evidence is local")


def score(ids: list[int], gold: str) -> bool:
    # No stripping, Unicode replacement, casefold, substring or alternate answer.
    return ids == [*(b + 3 for b in gold.encode("utf-8")), 2]


def gates(delta: dict, ordinary: dict, recurrent: dict, no_read: dict, no_write: dict) -> dict:
    controls = (ordinary, recurrent)
    return dict(
        exact_floor_and_gain=delta["correct"] >= 18
        and all(delta["correct"] >= c["correct"] + 4 for c in controls),
        distant_gain=delta["long_correct"] >= 12
        and all(delta["long_correct"] >= c["long_correct"] + 4 for c in controls),
        category_no_regression=all(
            delta["categories"][k] >= c["categories"][k] for k in CATEGORIES for c in controls
        ),
        unknown_safety=delta["categories"]["unknown"] == 4,
        memory_dependence=all(
            delta["long_correct"] >= a["long_correct"] + 2 for a in (no_read, no_write)
        ),
        ordinary_nll=delta["prose_nll"] <= 1.05 * ordinary["prose_nll"],
        inference_cpu=delta["eval_cpu"] <= 0.9 * recurrent["eval_cpu"],
        inference_wall=delta["eval_wall"] <= 0.9 * recurrent["eval_wall"],
        training_cpu=delta["train_cpu"] <= 1.5 * recurrent["train_cpu"],
        training_wall=delta["train_wall"] <= 1.5 * recurrent["train_wall"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    train_inputs, train_labels = factual("train", 128, 831107)
    train = [
        dict(id=r["id"], split="train", text=r["prefix"] + label["gold"])
        for r, label in zip(train_inputs, train_labels, strict=True)
    ]
    train += [dict(**r, split="train") for r in prose("train", 32)]
    inputs, labels = factual("dev", 24, 831109)
    dev_prose = prose("dev", 8)
    validate(train, inputs, labels, dev_prose)
    for name, rows in (
        ("train", train),
        ("inputs", inputs),
        ("labels-evaluator-only", labels),
        ("dev-prose", dev_prose),
    ):
        save(root / f"{name}.json", rows)
    save(
        root / "data-manifest.json",
        dict(
            version="segment-delta-development-v1",
            split_counts=dict(train=160, dev_facts=24, dev_prose=8),
            seeds=dict(train=831107, dev=831109),
            held_out_created=False,
            files={
                n: sha(root / n)
                for n in (
                    "train.json",
                    "inputs.json",
                    "labels-evaluator-only.json",
                    "dev-prose.json",
                )
            },
            train_targets=sum(len(r["text"].encode()) + 1 for r in train),
            train_max_targets=max(len(r["text"].encode()) + 1 for r in train),
            categories={c: sum(label["category"] == c for label in labels) for c in CATEGORIES},
        ),
    )


if __name__ == "__main__":
    main()
