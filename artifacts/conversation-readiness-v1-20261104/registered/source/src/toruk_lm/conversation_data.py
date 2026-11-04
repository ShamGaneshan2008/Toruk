"""Original synthetic conversation contract and strict, cross-stage leakage audit.

No third-party corpus or private transcript is downloaded. The task authorizes
creation of these synthetic examples. The reported refusal diagnostic is held
out only, using repository scenario text explicitly requested by the user.
"""

import json
import random
import re
from pathlib import Path
from typing import Any

from toruk_lm.owned_data import digest
from toruk_lm.owned_training import write_json

CATEGORIES = (
    "instruction",
    "factual",
    "uncertainty",
    "correction",
    "distant",
    "exact",
    "math",
    "refusal",
)
SPLIT_NAMES = ("train", "development", "test")
FORMAT = "toruk-json-role-lines-v1"


def format_messages(messages: list[dict[str, str]], *, prompt: bool = False) -> str:
    """Role plus JSON string per line; content cannot inject a role delimiter."""
    if not messages:
        raise ValueError("conversation must be nonempty")
    expected = "user"
    lines = []
    for index, message in enumerate(messages):
        if set(message) != {"role", "content"}:
            raise ValueError("message requires exactly role and content")
        role, content = message["role"], message["content"]
        if role == "system" and index == 0:
            pass
        elif role != expected:
            raise ValueError("roles must alternate user/assistant")
        else:
            expected = "assistant" if role == "user" else "user"
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty or invalid message content")
        lines.append(role + ":" + json.dumps(content, ensure_ascii=True) + "\n")
    if prompt:
        if messages[-1]["role"] != "user":
            raise ValueError("generation prompt must end in user turn")
        lines.append("assistant:")
    return "".join(lines)


def overlap(answer: str, text: str) -> bool:
    """Standalone complete answer, not substrings of unrelated identifiers."""
    return re.search(r"(?<!\w)" + re.escape(answer) + r"(?!\w)", text, re.I) is not None


def make_cases(split: str, count: int, seed: int) -> list[dict[str, Any]]:
    if split not in SPLIT_NAMES or not 1 <= count <= 16:
        raise ValueError("invalid conversation split/size")
    rng = random.Random(seed + SPLIT_NAMES.index(split) * 1000)
    prefix = {"train": "T", "development": "D", "test": "E"}[split]
    result = []
    for category in CATEGORIES:
        for index in range(count):
            name = f"{prefix}person{category}{index}"
            value = f"{prefix}value{category}{index}"
            old = f"{prefix}old{category}{index}"
            messages: list[dict[str, str]] = []
            if category == "instruction":
                question = f"Reply only {value}."
            elif category == "factual":
                question = (
                    f"The label for {name} is {value}. What is its label? Reply only the label."
                )
            elif category == "uncertainty":
                value = {
                    "train": "Not provided.",
                    "development": "Not stated.",
                    "test": "Unknown.",
                }[split]
                question = f"What is {name}'s unseen label? If missing, reply only {value}"
            elif category in ("correction", "distant", "exact"):
                if category == "exact":
                    value = f"{prefix}/Q-{index}_x!"
                messages.extend(
                    [
                        {
                            "role": "user",
                            "content": f"{name}'s label is "
                            + (old if category == "correction" else value)
                            + ".",
                        },
                        {"role": "assistant", "content": "Recorded."},
                    ]
                )
                if category == "correction":
                    messages.extend(
                        [
                            {"role": "user", "content": f"Correction: the label is now {value}."},
                            {"role": "assistant", "content": "Updated."},
                        ]
                    )
                elif category == "distant":
                    messages.extend(
                        [
                            {
                                "role": "user",
                                "content": "Unrelated note: "
                                + rng.choice(("wind ", "rain ", "cloud ")) * 15,
                            },
                            {"role": "assistant", "content": "Noted."},
                        ]
                    )
                question = f"What is {name}'s label? Reply only the exact label."
            elif category == "math":
                operand = {"train": 2, "development": 7, "test": 5}[split]
                value = str(operand + operand)
                question = f"For {name}, what is {operand}+{operand}? Reply only the number."
            else:
                operand = {"train": 3, "development": 8, "test": 5}[split]
                value = str(operand + operand)
                messages.extend(
                    [
                        {"role": "user", "content": "open YouTube"},
                        {"role": "assistant", "content": "I cannot access online content."},
                    ]
                )
                question = (
                    "what is 5+5"
                    if split == "test" and index == 0
                    else f"For {name}, what is {operand}+{operand}? Reply only the number."
                )
            messages.append({"role": "user", "content": question})
            completed = [*messages, {"role": "assistant", "content": value}]
            result.append(
                {
                    "id": f"{split}-{category}-{index}",
                    "split": split,
                    "category": category,
                    "messages": messages,
                    "answer": value,
                    "prefix": format_messages(messages, prompt=True),
                    "text": format_messages(completed),
                    "obsolete": old if category == "correction" else "",
                }
            )
    return result


def audit_splits(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    seen_ids: set[str] = set()
    seen_messages: set[str] = set()
    for split, rows in splits.items():
        for row in rows:
            identity = digest(row["messages"])
            if row["split"] != split or row["id"] in seen_ids or identity in seen_messages:
                raise ValueError("duplicate conversation or split/ID mismatch")
            seen_ids.add(row["id"])
            seen_messages.add(identity)
            if row["prefix"] != format_messages(row["messages"], prompt=True):
                raise ValueError("conversation formatting mismatch")
            if row["text"] != format_messages(
                [*row["messages"], {"role": "assistant", "content": row["answer"]}]
            ):
                raise ValueError("target formatting mismatch")
    answer_matches = []
    for split in ("development", "test"):
        for evaluation in splits[split]:
            for training in splits["train"]:
                if overlap(evaluation["answer"], training["text"]):
                    answer_matches.append(
                        {
                            "evaluation": evaluation["id"],
                            "training": training["id"],
                            "answer": evaluation["answer"],
                        }
                    )
    if answer_matches:
        raise ValueError(f"held-out answer in conversation training: {answer_matches[:3]}")
    return {
        "status": "PASS",
        "format": FORMAT,
        "answer_matches": 0,
        "counts": {key: len(rows) for key, rows in splits.items()},
        "digests": {key: digest(rows) for key, rows in splits.items()},
    }


def prepare(
    config: dict[str, Any],
    inherited: list[dict[str, Any]],
    output: Path,
    diagnostic: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    splits = {
        split: make_cases(split, config[f"{split}_per_category"], config["seed"])
        for split in SPLIT_NAMES
    }
    if diagnostic is not None:
        splits["test"].append(
            {
                "id": "test-observed-full-refusal",
                "split": "test",
                "category": "refusal",
                "messages": diagnostic,
                "answer": "10",
                "prefix": format_messages(diagnostic, prompt=True),
                "text": format_messages([*diagnostic, {"role": "assistant", "content": "10"}]),
                "obsolete": "",
            }
        )
    for split, rows in splits.items():
        for row in rows:
            if len(row["prefix"].encode()) > config["max_prompt_bytes"]:
                raise ValueError("conversation exceeds registered prompt budget")
            if split == "train" and len(row["text"].encode()) + 1 > config["max_document_targets"]:
                raise ValueError("conversation exceeds inherited document training limit")
    audit = audit_splits(splits)
    reserved = sorted({row["answer"] for split in ("development", "test") for row in splits[split]})
    matches = [
        {
            "training_id": row["id"],
            "answers": [answer for answer in reserved if overlap(answer, row["text"])],
        }
        for row in inherited
    ]
    matches = [row for row in matches if row["answers"]]
    excluded = {row["training_id"] for row in matches}
    clean = [row for row in inherited if row["id"] not in excluded]
    for split, rows in splits.items():
        write_json(output / f"{split}.json", rows)
    write_json(output / "clean-pretraining-train.json", clean)
    result = {
        "schema": "toruk-conversation-data-manifest-v1",
        "format": FORMAT,
        "audit": audit,
        "source": {
            "kind": "original task-generated synthetic examples",
            "permission": "User explicitly requested creation of small conversation examples",
            "third_party_corpus": False,
            "private_transcript_downloads": False,
            "diagnostic": "Repository probe_refusal_carryover.py prior_refusal scenario; test only",
        },
        "filtering": "Nonempty alternating roles; exact canonical message deduplication; "
        "split IDs; standalone held-out answer exclusion",
        "inherited_training_digest": digest(inherited),
        "inherited_matches": matches,
        "clean_pretraining_digest": digest(clean),
        "clean_pretraining_documents": len(clean),
        "clean_pretraining_targets": sum(len(row["text"].encode()) + 1 for row in clean),
        "starting_checkpoint_eligible": not matches,
        "interpretation": "Literal overlap is not proof of semantic leakage. This strict "
        "user-requested gate makes no exception for incidental note IDs. "
        "Filtering does not remove exposure from inherited weights.",
    }
    write_json(output / "manifest.json", result)
    return result


def require_training_ready(manifest: dict[str, Any], checkpoint_dataset: str) -> None:
    if checkpoint_dataset != manifest["inherited_training_digest"]:
        raise ValueError("checkpoint is not bound to the audited training corpus")
    if not manifest["starting_checkpoint_eligible"]:
        raise ValueError(
            "training blocked: inherited checkpoint saw reserved answer text; "
            "clean data alone cannot clean its weights"
        )
