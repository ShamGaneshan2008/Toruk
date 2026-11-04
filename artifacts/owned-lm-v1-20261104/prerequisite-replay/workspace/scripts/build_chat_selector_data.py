"""Generate disjoint synthetic chat-evidence splits from fixed seeds."""

import argparse
import hashlib
import json
import random
from pathlib import Path

SEEDS = {"train": 1701, "dev": 2301, "final": 4701}
SIZES = {"train": 40, "dev": 12, "final": 12}  # cases per category
CATEGORIES = ("correction", "preservation", "distraction", "long_recall", "unknown")
CITIES = {
    "train": ("Pune", "Jaipur", "Kochi", "Bhopal"),
    "dev": ("Surat", "Indore", "Patna", "Agra"),
    "final": ("Mysuru", "Nashik", "Udaipur", "Ranchi"),
}
FILLER = (
    "A separate travel note describes the station, a market, a bridge, and a rainy evening. "
    "It does not change any personal details in the earlier note. "
)


def make_case(split: str, category: str, number: int, rng: random.Random) -> dict:
    name = f"{split.capitalize()}person{number:03d}"
    city, newer = rng.sample(CITIES[split], 2)
    key = f"{split.upper()}KEY{number:03d}"
    original = (
        f"{name}'s archive key is {key}. Keep this exact archive key for later."
        if category == "long_recall"
        else f"{name}'s city is {city}. Keep this city for later."
    )
    if category == "unknown":
        original = f"{name}'s city is {city}. Keep this city for later."
    messages = [
        {"role": "user", "content": original},
        {"role": "assistant", "content": "I noted that information."},
    ]
    for pair in range(1, 9):
        other = f"{split.capitalize()}other{number:03d}{pair}"
        distractor = f"{other}'s hobby is chess. {FILLER * 3}"
        if pair == 4 and category == "correction":
            distractor = (
                f"Correction: {name}'s city changed to {newer}. "
                f"The earlier city is outdated. {FILLER * 2}"
            )
        elif pair == 4 and category == "preservation":
            distractor = (
                f"Correction: {name}'s hobby changed to painting. "
                f"The city remains unchanged. {FILLER * 2}"
            )
        elif pair == 6 and category in ("distraction", "unknown"):
            distractor = f"{name}'s hobby is walking. {FILLER * 3}"
        messages.extend(
            [
                {"role": "user", "content": distractor},
                {"role": "assistant", "content": "Noted; continuing the conversation."},
            ]
        )
    question = {
        "correction": f"What is {name}'s city now?",
        "preservation": f"What is {name}'s city?",
        "distraction": f"What is {name}'s city?",
        "long_recall": f"What is {name}'s archive key?",
        "unknown": f"What is {name}'s secret code? If it was not supplied, say you do not know.",
    }[category]
    messages.append({"role": "user", "content": question})
    evidence = [8] if category == "correction" else ([] if category == "unknown" else [0])
    expected = (
        None
        if category == "unknown"
        else (key if category == "long_recall" else newer if category == "correction" else city)
    )
    return {
        "id": f"{split}-{category}-{number:03d}",
        "split": split,
        "category": category,
        "messages": messages,
        "evidence_ids": evidence,
        "expected": expected,
        "forbidden": city if category == "correction" else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("use a fresh output directory")
    args.output_dir.mkdir(parents=True)
    hashes = {}
    for split, seed in SEEDS.items():
        rng = random.Random(seed)
        cases = [
            make_case(split, category, n, rng)
            for category in CATEGORIES
            for n in range(SIZES[split])
        ]
        content = "".join(json.dumps(case, sort_keys=True) + "\n" for case in cases)
        path = args.output_dir / f"{split}.jsonl"
        path.write_bytes(content.encode("utf-8"))
        hashes[split] = hashlib.sha256(content.encode()).hexdigest()
    manifest = {
        "format": "toruk-chat-selector-data-v1",
        "seeds": SEEDS,
        "cases_per_category": SIZES,
        "categories": CATEGORIES,
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "split_sha256": hashes,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
