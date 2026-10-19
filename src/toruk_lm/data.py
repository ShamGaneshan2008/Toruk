"""Document-separated, deterministic ordinary-text fixture and next-token windows."""

import hashlib
import json
import random
from pathlib import Path
from typing import Any

import torch
from torch import Tensor

from toruk_lm.tokenizer import ByteTokenizer


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_fixture(directory: Path, seed: int = 17, documents: int = 60) -> dict[str, Any]:
    if documents < 10:
        raise ValueError("at least ten documents are required")
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("refusing to overwrite a nonempty dataset directory")
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    rows = []
    for i in range(documents):
        animal = rng.choice(["fox", "owl", "otter", "deer"])
        place = rng.choice(["river", "forest", "garden", "hill"])
        text = (
            f"Field journal {i:04d}. The {animal} lives near the {place}. "
            f"In the morning the {animal} visits the {place}. "
            f"At night the {place} is quiet. This ends field journal {i:04d}.\n"
        )
        rows.append({"id": f"fixture-{seed}-{i:04d}", "text": text})
    rng.shuffle(rows)
    train_end, val_end = int(documents * 0.8), int(documents * 0.9)
    manifest: dict[str, Any] = {
        "kind": "ordinary-text-smoke-fixture-v1",
        "seed": seed,
        "note": "Not a controlled-world benchmark; no independent factual scoring oracle.",
        "splits": {},
    }
    for name, subset in (
        ("train", rows[:train_end]),
        ("validation", rows[train_end:val_end]),
        ("test", rows[val_end:]),
    ):
        path = directory / f"{name}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in subset), encoding="utf-8")
        manifest["splits"][name] = {
            "documents": len(subset),
            "sha256": sha256_file(path),
            "ids": [row["id"] for row in subset],
        }
    write_json(directory / "manifest.json", manifest)
    return manifest


def read_documents(path: Path) -> list[dict[str, str]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows or any(
        not isinstance(row.get("id"), str) or not isinstance(row.get("text"), str) for row in rows
    ):
        raise ValueError("expected nonempty JSONL with string id and text")
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("duplicate document id")
    return rows


def check_separation(train: list[dict[str, str]], validation: list[dict[str, str]]) -> None:
    if {r["id"] for r in train} & {r["id"] for r in validation}:
        raise ValueError("train/validation document IDs overlap")
    if {r["text"] for r in train} & {r["text"] for r in validation}:
        raise ValueError("train/validation documents have identical text")


def windows(documents: list[dict[str, str]], context: int) -> list[tuple[list[int], list[int]]]:
    if context <= 0:
        raise ValueError("context must be positive")
    tokenizer = ByteTokenizer()
    result = []
    for document in documents:
        tokens = tokenizer.encode(document["text"], document=True)
        for start in range(0, len(tokens) - 1, context):
            x = tokens[start : min(start + context, len(tokens) - 1)]
            y = tokens[start + 1 : start + 1 + len(x)]
            result.append((x, y))
    return result


def batch(examples: list[tuple[list[int], list[int]]]) -> tuple[Tensor, Tensor]:
    length = max(len(x) for x, _ in examples)
    x = torch.zeros(len(examples), length, dtype=torch.long)
    y = torch.full_like(x, -100)
    for lane, (inputs, targets) in enumerate(examples):
        x[lane, : len(inputs)] = torch.tensor(inputs)
        y[lane, : len(targets)] = torch.tensor(targets)
    return x, y


def training_batch(
    examples: list[tuple[list[int], list[int]]],
    step: int,
    batch_size: int,
    seed: int,
) -> tuple[Tensor, Tensor]:
    chosen = []
    orders: dict[int, list[int]] = {}
    for offset in range(step * batch_size, (step + 1) * batch_size):
        epoch, position = divmod(offset, len(examples))
        if epoch not in orders:
            order = list(range(len(examples)))
            random.Random(seed + epoch).shuffle(order)
            orders[epoch] = order
        chosen.append(examples[orders[epoch][position]])
    return batch(chosen)
