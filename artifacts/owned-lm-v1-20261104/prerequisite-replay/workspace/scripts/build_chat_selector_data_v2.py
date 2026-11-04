"""Build split-disjoint conversational evidence cases for protocol v2."""

import argparse
import hashlib
import json
import random
from pathlib import Path

SEEDS = {"train": 711, "dev": 991, "final": 1423}
SIZES = {"train": 24, "dev": 8, "final": 4}  # per category
CATEGORIES = ("correction", "preservation", "conflict", "irrelevant", "long_recall", "multi_fact", "unknown")
NOUNS = {
    "train": ("city", "archive key", "hobby"),
    "dev": ("town", "locker pin", "craft"),
    "final": ("port", "vault code", "instrument"),
}
FRAMES = {
    "train": ("{name}'s {slot} is {value}.", "What is {name}'s {slot}?"),
    "dev": ("For {name}, record {slot}: {value}.", "Tell me the {slot} for {name}."),
    "final": ("Please remember this entry: {name} has {value} as the {slot}.", "Which {slot} belongs to {name}?"),
}
VALUES = {
    "train": ("Pune", "Jaipur", "Kochi", "Bhopal", "Sitar", "Flute"),
    "dev": ("Surat", "Indore", "Patna", "Agra", "Violin", "Oboe"),
    "final": ("Mysuru", "Nashik", "Udaipur", "Ranchi", "Cello", "Harp"),
}


def make_case(split: str, category: str, number: int, rng: random.Random) -> dict:
    name = f"{split.capitalize()}member{number:02d}"
    slot, code_slot, other_slot = NOUNS[split]
    old, new = rng.sample(VALUES[split][:4], 2)
    code = f"{split.upper()}CODE{number:02d}"
    frame, question = FRAMES[split]
    long = number % 2 == 1
    messages = [{"role": "user", "content": frame.format(name=name, slot=slot, value=old)}]
    evidence = [0]
    expected = [old]
    forbidden = []
    if category == "long_recall":
        messages[0]["content"] = frame.format(name=name, slot=code_slot, value=code)
        expected = [code]
    if category == "multi_fact":
        messages.append({"role": "user", "content": frame.format(name=name, slot=code_slot, value=code)})
        evidence.append(1)
        expected.append(code)
    if category == "unknown":
        evidence = []
        expected = []
    messages.append({"role": "assistant", "content": "Recorded."})
    pairs = 7 if long else 1
    for pair in range(pairs):
        other = f"{split.capitalize()}visitor{number:02d}{pair}"
        distraction = frame.format(name=other, slot=slot, value=rng.choice(VALUES[split][:4]))
        distraction += " The lighthouse log describes a bridge, a market, and a rainy evening. " * (2 if long else 1)
        if pair == (3 if long else 0) and category in ("correction", "conflict"):
            marker = "Correction: " if category == "correction" else "The later entry replaces the old one: "
            distraction = marker + frame.format(name=name, slot=slot, value=new)
            evidence = [len(messages)]
            expected = [new]
            forbidden = [old]
        if pair == (3 if long else 0) and category == "preservation":
            distraction = "Correction: " + frame.format(name=name, slot=other_slot, value="Cello")
        if pair == (3 if long else 0) and category == "irrelevant":
            distraction = frame.format(name=name, slot=other_slot, value="Harp")
        messages.extend([{"role": "user", "content": distraction}, {"role": "assistant", "content": "Noted."}])
    if category == "multi_fact":
        query = f"Give both the {slot} and {code_slot} for {name}."
    elif category == "unknown":
        query = f"Which {code_slot} belongs to {name}? If never supplied, say you do not know."
    else:
        query = question.format(name=name, slot=code_slot if category == "long_recall" else slot)
    messages.append({"role": "user", "content": query})
    return {"id": f"{split}-{category}-{number:02d}", "split": split, "category": category,
            "world": f"{split}-{name}", "template_family": split, "messages": messages,
            "evidence_ids": evidence, "expected": expected, "forbidden": forbidden,
            "history_length": "long" if long else "short"}


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
        cases = [make_case(split, category, n, rng) for category in CATEGORIES for n in range(SIZES[split])]
        raw = "".join(json.dumps(case, sort_keys=True) + "\n" for case in cases).encode()
        (args.output_dir / f"{split}.jsonl").write_bytes(raw)
        hashes[split] = hashlib.sha256(raw).hexdigest()
    manifest = {"format": "toruk-chat-selector-data-v2", "seeds": SEEDS,
                "sizes_per_category": SIZES, "categories": CATEGORIES,
                "template_families": {split: FRAMES[split] for split in SEEDS},
                "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "split_sha256": hashes}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
