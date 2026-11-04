"""Independent authored scenario cards with seeded heterogeneous dialogue assembly."""

import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "configs/independent-chat-cards-v1.json"
SEED = 20261104
FILLERS = (
    "The print-room queue contains {n} sheets awaiting binding.",
    "A separate pottery class counted {n} unused wooden tools.",
    "The café noticeboard lists {n} donated paperback books.",
    "An unrelated walking group packed {n} reusable cups.",
    "The museum audio guide contains {n} short recordings.",
    "The bicycle workshop received {n} new wheel reflectors.",
    "An inventory note lists {n} empty shipping envelopes.",
    "The community kitchen washed {n} small serving bowls.",
    "A theatre volunteer counted {n} plain stage cushions.",
    "The reading room has {n} spare bookmarks in a basket.",
    "A separate delivery ledger records {n} returned cardboard tubes.",
    "The music-room notice mentions {n} replacement chair feet.",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble(cards: list[dict[str, Any]], seed: int = SEED) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    result = []
    for card in cards:
        messages: list[dict[str, str]] = []
        total_gaps = rng.randint(22, 25)
        gaps_used = 0

        def gap(target: list[dict[str, str]] = messages) -> None:
            nonlocal gaps_used
            text = rng.choice(FILLERS).format(n=rng.randint(31, 97))
            target.extend(
                [
                    {"role": "user", "content": f"Side note {gaps_used + 1}: {text}"},
                    {"role": "assistant", "content": "Added to the separate notes."},
                ]
            )
            gaps_used += 1

        for _ in range(rng.randint(0, 2)):
            gap()
        evidence = []
        for index, event in enumerate(card["events"]):
            evidence.append(len(messages))
            messages.append(dict(event))
            messages.append(
                {
                    "role": "assistant" if event["role"] == "user" else "user",
                    "content": "Recorded for later.",
                }
            )
            if index + 1 < len(card["events"]):
                gap()
        while gaps_used < total_gaps:
            gap()
        messages.append({"role": "user", "content": card["question"]})
        result.append(
            {
                "id": "ind-" + card["id"],
                "split": "independent-evaluation-only",
                "category": card["category"],
                "task": card["task"],
                "messages": messages,
                "evidence": evidence,
                "groups": card["groups"],
                "forbidden": card["forbidden"],
                "distractor_pairs": total_gaps,
                "trailing_gap_pairs": total_gaps - (max(evidence) // 2 - len(evidence) + 1),
            }
        )
    validate(result)
    return result


def validate(cases: list[dict[str, Any]]) -> None:
    if len(cases) != 24 or len({case["id"] for case in cases}) != 24:
        raise ValueError("Expected 24 unique independent scenarios")
    expected = dict.fromkeys(
        ("distant", "correction", "preservation", "exact", "vague", "missing"), 4
    )
    if dict(Counter(case["category"] for case in cases)) != expected:
        raise ValueError("Independent scenario category counts changed")
    for case in cases:
        messages = case["messages"]
        if len(messages) > 64 or sum(len(m["content"].encode()) for m in messages) > 16384:
            raise ValueError("Input budget exceeded")
        if messages[-1]["role"] != "user" or not case["evidence"]:
            raise ValueError("Missing question or source ledger")
        if len(messages) - 1 - max(case["evidence"]) < 37:
            raise ValueError("Fewer than 18 trailing distraction pairs")
        if any(m["role"] not in ("user", "assistant") for m in messages):
            raise ValueError("Unsupported source role")
        if case["task"] in ("exact", "vague_clear") and not case["groups"]:
            raise ValueError("Known question lacks oracle value")


def historical_paths() -> list[Path]:
    paths = [
        ROOT / f"artifacts/chat-selector-v2-20261101/data/{name}.jsonl"
        for name in ("train", "dev", "final")
    ]
    paths.extend(
        ROOT / f"artifacts/recall-v{version}-20261104/{name}.json"
        for version in (1, 2)
        for name in ("training", "development", "heldout")
    )
    return paths


def leakage_audit(cases: list[dict[str, Any]]) -> dict[str, Any]:
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.casefold()).strip()

    old_texts: set[str] = set()
    bindings = {}
    for path in historical_paths():
        bindings[str(path.relative_to(ROOT))] = sha(path)
        text = path.read_text(encoding="utf-8")
        rows = (
            [json.loads(line) for line in text.splitlines()]
            if path.suffix == ".jsonl"
            else json.loads(text)
        )
        for row in rows:
            old_texts.update(normalize(message["content"]) for message in row["messages"])
    overlaps = []
    for case in cases:
        for index in [*case["evidence"], len(case["messages"]) - 1]:
            if normalize(case["messages"][index]["content"]) in old_texts:
                overlaps.append({"id": case["id"], "turn": index})
    if overlaps:
        raise ValueError(f"Task-bearing historical text overlap: {overlaps}")
    return {
        "procedure": "independently authored cards; seeded heterogeneous filler assembly",
        "seed": SEED,
        "historical_bindings": bindings,
        "exact_normalized_task_text_overlaps": overlaps,
        "limitation": "Not a semantic-template or pretrained-corpus contamination proof",
    }


def build() -> list[dict[str, Any]]:
    return assemble(json.loads(CARDS.read_text(encoding="utf-8")))
