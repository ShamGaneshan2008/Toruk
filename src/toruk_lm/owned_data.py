"""Versioned synthetic IID documents; labels never enter the model interface."""

import hashlib
import json
import random
from pathlib import Path
from typing import Any

CATEGORIES = ("distant", "correction", "preservation", "exact", "local", "unknown")
SPLITS = {"train": 3201, "dev": 4201, "heldout": 5201}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def cases(split: str, per_category: int) -> list[dict[str, Any]]:
    if split not in SPLITS or not 1 <= per_category <= 64:
        raise ValueError("invalid owned dataset split/size")
    rng = random.Random(SPLITS[split])
    result = []
    for category in CATEGORIES:
        for index in range(per_category):
            entity = rng.choice(("Ada", "Bo", "Cy", "Dee"))
            value, old = rng.sample(("red", "blue", "gold", "lime"), 2)
            filler = "".join(
                f"Note {rng.randrange(1000)}: {rng.choice(('rain', 'wind', 'sun'))}.\n"
                for _ in range(4 + rng.randrange(3))
            )
            evidence = f"{entity}'s tag is {value}.\n"
            obsolete = ""
            if category == "correction":
                obsolete = old
                evidence = f"{entity}'s tag is {old}.\n"
                filler = f"Correction: {entity}'s tag is {value}, replacing {old}.\n" + filler
            elif category == "preservation":
                filler = f"Other person's tag is {old}.\n" + filler
            elif category == "exact":
                value = rng.choice(("K-7/ax", "pQ_02", "V.9!", "z+3=Q"))
                evidence = f"{entity}'s tag is {value}.\n"
            elif category == "unknown":
                evidence = f"{entity} visited the park.\n"
                value = "?"
            question = f"{entity}'s tag? "
            history = filler + evidence if category == "local" else evidence + filler
            prefix = "If unknown answer ?.\n" + history + "Answer " + question
            result.append(
                {
                    "id": f"{split}-{category}-{index}",
                    "split": split,
                    "category": category,
                    "history": history,
                    "prefix": prefix,
                    "answer": value,
                    "obsolete": obsolete,
                    "text": prefix + value + "\n",
                    "evidence": evidence.strip(),
                }
            )
    return result


def write_data(output: Path, sizes: dict[str, int], maximum: int) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    manifest: dict[str, Any] = {"schema": "toruk-owned-documents-v1", "splits": {}}
    for split, size in sizes.items():
        rows = cases(split, size)
        for row in rows:
            if row["text"] in seen or len(row["text"].encode()) + 1 > maximum:
                raise ValueError("duplicate or over-budget document")
            seen.add(row["text"])
        path = output / f"{split}.json"
        path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        manifest["splits"][split] = {
            "seed": SPLITS[split],
            "count": len(rows),
            "sha256": digest(rows),
            "training_targets": sum(len(row["text"].encode()) + 1 for row in rows),
        }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_data(path: Path, split: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    if not rows or any(row.get("split") != split for row in rows):
        raise ValueError("dataset split mismatch")
    if any(row["text"] != row["prefix"] + row["answer"] + "\n" for row in rows):
        raise ValueError("document/answer contract mismatch")
    return rows
