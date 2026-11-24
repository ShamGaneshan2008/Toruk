"""Development-only replication inputs and independently seeded city schedules."""

from __future__ import annotations

import random
from collections import Counter
from typing import Any

NAMES = ("bek", "dov", "ral", "sun")
INITIALIZATION_SEEDS = (601, 947)
SHUFFLE_SEEDS = (1301, 1709)
CROSSED = {
    f"i{i}-s{s}": dict(initialization=i, shuffle=s)
    for i in INITIALIZATION_SEEDS
    for s in SHUFFLE_SEEDS
}


def datasets() -> dict[str, Any]:
    files: dict[str, Any] = {}
    for split in ("train", "dev"):
        inputs: list[dict[str, Any]] = []
        labels: list[dict[str, Any]] = []
        documents: list[dict[str, Any]] = []
        for entity, name in enumerate(NAMES):
            for category in ("city", "code", "unknown"):
                field = "role" if category == "unknown" else category
                query_field = "city" if category == "unknown" else field
                values = (
                    ("R-7", "Q_2", "V:4", "Z!6") if field == "code" else ("la", "mi", "so", "tu")
                )
                for pair in (0, 1):
                    value = values[(entity + pair + (0 if split == "train" else 2)) % 4]
                    templates = ("A", "B") if split == "train" else (("A", "B")[pair],)
                    for template in templates:
                        for _ in range(2 if split == "train" else 1):
                            index = len(inputs)
                            prelude = (f"v2 {split[0]}{index:03d}; " + "rain. " * 8)[:30] + "\n"
                            lhs = f"{name} {field}" if template == "A" else f"{field} {name}"
                            query = (
                                f"{name} {query_field}"
                                if template == "A"
                                else f"{query_field} {name}"
                            )
                            prefix = prelude + lhs + "=" + value + "\n" + query + "?="
                            gold = "?" if category == "unknown" else value
                            identity = f"v2-{split}-{index:03d}"
                            inputs.append(dict(id=identity, prefix=prefix))
                            labels.append(
                                dict(
                                    id=identity,
                                    gold=gold,
                                    category=category,
                                    template=template,
                                    canonical=[name, field, value, query_field],
                                )
                            )
                            if split == "train":
                                documents.append(
                                    dict(
                                        id=identity,
                                        split="train",
                                        prefix=prefix,
                                        gold=gold,
                                        text=prefix + gold,
                                    )
                                )
        files[f"{split}-inputs.json"] = inputs
        files[f"{split}-labels.json"] = labels
        if split == "train":
            files["train-documents.json"] = documents
    return files


def validate(files: dict[str, Any], prior_labels: list[dict[str, Any]]) -> dict[str, Any]:
    train = {tuple(r["canonical"]) for r in files["train-labels.json"]}
    dev = {tuple(r["canonical"]) for r in files["dev-labels.json"]}
    prior = {tuple(r["canonical"]) for r in prior_labels}
    assert len(train) == len(dev) == 24 and not train & dev and not dev & prior
    assert len(files["train-inputs.json"]) == 96 and len(files["dev-inputs.json"]) == 24
    assert not {r["id"] for r in files["train-inputs.json"]} & {
        r["id"] for r in files["dev-inputs.json"]
    }
    for split in ("train", "dev"):
        assert Counter(r["category"] for r in files[f"{split}-labels.json"]) == dict.fromkeys(
            ("city", "code", "unknown"), 32 if split == "train" else 8
        )
        for case, label in zip(
            files[f"{split}-inputs.json"], files[f"{split}-labels.json"], strict=True
        ):
            assert case["id"] == label["id"]
            prelude, assignment, query = case["prefix"].splitlines()
            assert len(prelude.encode()) + 1 == 31
            lhs, value = assignment.split("=")
            expected = value if query[:-2] == lhs else "?"
            assert expected == label["gold"] and query.endswith("?=")
            assert len((assignment + "\n" + query + label["gold"]).encode()) + 1 <= 32
    assert sum(len(d["text"].encode()) + 1 for d in files["train-documents.json"]) == 5408
    return dict(
        pass_overlap=True,
        train_cores=24,
        fresh_development_cores=24,
        dev_overlap_train=0,
        dev_overlap_v1_and_known=0,
        prior_permitted_cores=len(prior),
        new_entities=list(NAMES),
        heldout_opened=False,
    )


def schedule(files: dict[str, Any], shuffle_seed: int) -> list[dict[str, Any]]:
    assert shuffle_seed in SHUFFLE_SEEDS
    labels = files["train-labels.json"]
    city = sorted(r["id"] for r in labels if r["category"] == "city")
    noncity = sorted(r["id"] for r in labels if r["category"] != "city")
    rows: list[dict[str, Any]] = []
    for epoch in range(128):
        cities, others = list(city), list(noncity)
        random.Random(shuffle_seed + 100000 + epoch).shuffle(cities)
        random.Random(shuffle_seed + 200000 + epoch).shuffle(others)
        ci, oi = 0, 0
        for offset in range(12):
            if offset in (0, 3, 6, 9):
                batch = cities[ci : ci + 8]
                ci += 8
                random.Random(shuffle_seed + 300000 + 12 * epoch + offset).shuffle(batch)
            else:
                batch = others[oi : oi + 8]
                oi += 8
            rows.append(
                dict(
                    step=12 * epoch + offset + 1,
                    epoch=epoch,
                    offset=offset,
                    ids=batch,
                    padded_forward_positions=512,
                )
            )
    assert Counter(i for row in rows for i in row["ids"]) == Counter({r["id"]: 128 for r in labels})
    return rows
