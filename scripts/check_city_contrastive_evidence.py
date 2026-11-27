"""Read-only review of the frozen study, including fields omitted by its v1 audit.

Run with Python -I -S -B. This adds checks without changing frozen source,
predictions, seals, gates or the original audit receipt. Never runs a model.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def integer(value: Any, name: str) -> int:
    require(type(value) is int and value >= 0, "invalid integer: " + name)
    return int(value)


def native_ids(value: Any, *, generated: bool) -> list[int]:
    require(isinstance(value, list) and value, "nonempty native IDs required")
    require(all(type(i) is int and 0 <= i < 259 for i in value), "native IDs must be integers")
    if generated:
        require(len(value) <= 8 and all(i >= 2 for i in value), "native generation budget/range")
        require(2 not in value or value.index(2) == len(value) - 1, "EOS must terminate generation")
        require(value[-1] == 2 or len(value) == 8, "unfinished generation before budget")
    return list(value)


def request_cost(value: Any) -> tuple[float, float]:
    require(isinstance(value, dict) and set(value) == {"cpu", "wall"}, "request cost schema")
    for v in value.values():
        require(
            type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 2,
            "request cost must be finite, nonnegative and within cap",
        )
    return float(value["cpu"]), float(value["wall"])


def rows(path: Path) -> list[dict[str, Any]]:
    result = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    require(result and all(isinstance(r, dict) for r in result), "nonempty observation rows")
    return result


def match_totals(stored: Any, expected: dict[str, Any]) -> None:
    require(isinstance(stored, dict), "token ledger schema")
    for key, value in expected.items():
        if key in ("cpu", "wall"):
            if key not in stored:  # v1 vector/teacher ledgers omit timing aggregates.
                continue
            actual = stored[key]
            require(
                type(actual) in (int, float)
                and math.isfinite(actual)
                and actual >= 0
                and math.isclose(actual, value, rel_tol=1e-12, abs_tol=1e-12),
                "timing ledger mismatch: " + key,
            )
        else:
            require(integer(stored.get(key), key) == value, "token ledger mismatch: " + key)


def verify_observation(directory: Path, *, padded_length: int = 64) -> dict[str, Any]:
    """Validate native types, decoding, replay and every generation/vector/teacher ledger."""
    require(type(padded_length) is int and padded_length > 0, "invalid padded length")
    ledger = json.loads((directory / "token-costs.json").read_text(encoding="utf-8"))
    require(
        isinstance(ledger, dict)
        and set(ledger)
        in ({"main", "vectors", "teacher"}, {"main", "question-only", "vectors", "teacher"}),
        "token ledger modes",
    )
    totals: dict[str, Any] = {}
    primary = rows(directory / "predictions-main.jsonl")
    for mode in ("main", "question-only") if "question-only" in ledger else ("main",):
        raw = primary if mode == "main" else rows(directory / "predictions-question-only.jsonl")
        require(len(raw) >= 2, "missing replay")
        inputs = outputs = positions = 0
        cpu = wall = 0.0
        for index, row in enumerate(raw):
            require(
                type(row["replay"]) is bool and row["replay"] == (index == len(raw) - 1),
                "invalid replay marker",
            )
            require(isinstance(row["prefix"], str), "prefix must be text")
            ids = native_ids(row["input_ids"], generated=False)
            require(ids == [1, *(b + 3 for b in row["prefix"].encode())], "native prefix mismatch")
            result = row["result"]
            generated = native_ids(result["generated_ids"], generated=True)
            decoded = bytes(i - 3 for i in generated if i >= 3).decode("utf-8", errors="replace")
            require(result["answer"] == decoded, "decoded answer mismatch")
            require(
                type(result["budget_exhausted"]) is bool
                and result["budget_exhausted"] == (generated[-1] != 2),
                "budget marker mismatch",
            )
            require(
                integer(result["input_tokens"], "input_tokens") == len(ids), "input token count"
            )
            work = integer(result["forward_positions"], "forward_positions")
            require(work >= len(ids), "generation forward work smaller than input")
            integer(result["commits"], "commits")
            integer(result["allocated_state_bytes"], "allocated_state_bytes")
            c, w = request_cost(row["cost"])
            inputs += len(ids)
            outputs += len(generated)
            positions += work
            cpu += c
            wall += w
        require(
            raw[0]["id"] == raw[-1]["id"] and raw[0]["result"] == raw[-1]["result"],
            "replay mismatch",
        )
        require(len({r["id"] for r in raw[:-1]}) == len(raw) - 1, "duplicate primary case IDs")
        value = dict(
            requests=len(raw),
            input_tokens=inputs,
            generated_tokens=outputs,
            forward_positions=positions,
            cpu=cpu,
            wall=wall,
        )
        # Generation timing aggregates were mandatory even in the original schema.
        require({"cpu", "wall"} <= set(ledger[mode]), "missing generation timing ledger")
        match_totals(ledger[mode], value)
        totals[mode] = value
    vectors = rows(directory / "first-vectors.jsonl")
    measurements = rows(directory / "first-measurements.jsonl")
    require(len(vectors) == len(measurements) == len(primary), "vector row count")
    tokens = 0
    cpu = wall = 0.0
    for index, (vector, measure, pred) in enumerate(
        zip(vectors, measurements, primary, strict=True)
    ):
        ids = native_ids(vector["input_ids"], generated=False)
        require(
            ids == pred["input_ids"] and vector["id"] == measure["id"] == pred["id"],
            "vector identity",
        )
        for row in (vector, measure):
            require(
                type(row["replay"]) is bool and row["replay"] == (index == len(primary) - 1),
                "vector replay marker",
            )
        c, w = request_cost(measure["cost"])
        tokens += len(ids)
        cpu += c
        wall += w
    totals["vectors"] = dict(
        requests=len(vectors), input_tokens=tokens, forward_positions=tokens, cpu=cpu, wall=wall
    )
    match_totals(ledger["vectors"], totals["vectors"])
    teacher = rows(directory / "teacher-losses.jsonl")
    require(len(teacher) == len(primary) - 1, "teacher row count")
    targets = positions = 0
    cpu = wall = 0.0
    for row, pred in zip(teacher, primary[:-1], strict=True):
        require(row["id"] == pred["id"], "teacher identity")
        targets += integer(row["history_targets"], "history_targets")
        targets += integer(row["answer_targets"], "answer_targets")
        require(integer(row["first_targets"], "first_targets") == 1, "teacher first targets")
        require(
            integer(row["forward_positions"], "teacher positions") == padded_length,
            "teacher padded work mismatch",
        )
        positions += padded_length
        c, w = request_cost(row["cost"])
        cpu += c
        wall += w
    totals["teacher"] = dict(
        requests=len(teacher), targets=targets, forward_positions=positions, cpu=cpu, wall=wall
    )
    match_totals(ledger["teacher"], totals["teacher"])
    return totals


def review_study() -> dict[str, Any]:
    # -I removes the script directory from sys.path; resolve our frozen sibling explicitly.
    sys.path.insert(0, str(ROOT / "scripts"))
    import audit_city_contrastive_dev as frozen

    original = frozen.audit()  # Preserve every original source/seal/gate check.
    plan = frozen.read(frozen.RUN / "plan-final.json")
    ledger = frozen.base.rows(frozen.EXEC / "stages.jsonl")
    observations = {}
    for entry in ledger:
        if entry["stage"].startswith(("evaluate-", "development-")):
            path = (frozen.EXEC / entry["path"]).resolve()
            require(path.is_relative_to(frozen.EXEC), "observation outside registered execution")
            observations[entry["stage"]] = verify_observation(
                path, padded_length=plan["config"]["max_document_tokens"]
            )
    return dict(
        status="PASS",
        decision=original["decision"],
        model_forwards=0,
        observations_checked=len(observations),
        token_and_cost_totals=observations,
        scientific_seals=original["scientific_seals"],
        heldout_opened=False,
    )


def read_only_guard(event: str, args: tuple[Any, ...]) -> None:
    if event == "import" and args[0].split(".")[0] in {
        "torch",
        "transformers",
        "ollama",
        "toruk_lm",
    }:
        raise RuntimeError("Model imports forbidden in offline review")
    if event == "open" and not isinstance(args[0], int):
        require(
            not any(s in str(args[0]).lower() for s in ("heldout", "held-out", "held_out")),
            "held-out access forbidden",
        )
        require(
            not (args[2] or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND),
            "offline review cannot write files",
        )


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    sys.addaudithook(read_only_guard)
    print(json.dumps(review_study(), indent=2, allow_nan=False))
