"""Audit saved Qwen development evidence only; no model loading or generation."""

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from verify_portable_research_evidence import Evidence, digest, frozen_functions, portable_path

ROOT = Path(__file__).resolve().parents[1]
RUN = "artifacts/qwen-long-history-v3/attempt-001"
SUPPORT = "artifacts/research-evidence-portable-v1"
COSTS = (
    "prompt_tokens",
    "output_tokens",
    "selector_cpu_seconds",
    "selector_wall_seconds",
    "generation_cpu_seconds",
    "generation_wall_seconds",
    "request_cpu_seconds",
    "request_wall_seconds",
)


def validate_development(cases: list[dict]) -> None:
    ids = [c["id"] for c in cases]
    if (
        not cases
        or len(set(ids)) != len(ids)
        or any(c.get("split") != "development" or "-development-" not in c["id"] for c in cases)
    ):
        raise ValueError("unique development cases only")


class Inputs:
    """Read only named, hash-bound inputs; reject held-out paths before opening."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.manifest = json.loads((root / SUPPORT / "manifest.json").read_bytes())
        self.consumed: dict[str, str] = {}

    def read(self, name: str, expected: str | None = None) -> bytes:
        relative = portable_path(name)
        if "heldout" in relative.casefold() or "held-out" in relative.casefold():
            raise ValueError("held-out inputs prohibited")
        expected = expected or self.manifest["files"][relative]
        raw = (self.root / relative).read_bytes()
        if digest(raw) != expected:
            raise ValueError("frozen input changed: " + relative)
        self.consumed[relative] = expected
        return raw

    def json(self, name: str) -> Any:
        return json.loads(self.read(name))

    def rows(self, name: str) -> list[dict]:
        return [json.loads(line) for line in self.read(name).splitlines()]


def frozen_api(inputs: Inputs) -> dict:
    """Extract only the registered scorer/envelope functions, never data generators."""
    files = {}
    registrations = (
        (
            "artifacts/backbone-qualification-v1/registration.json",
            "scripts/qualify_answer_backbone.py",
        ),
        (
            "artifacts/qwen-long-history-v1/execution-v2/registration.json",
            "scripts/qwen_long_history.py",
        ),
    )
    for registration, source in registrations:
        files[registration] = inputs.read(registration)
        reg = json.loads(files[registration])
        expected = next(h for n, h in reg["bindings"].items() if portable_path(n) == source)
        raw = inputs.read(source, expected)
        if digest(raw) != expected:
            raise ValueError("registered function source drift: " + source)
        files[source] = raw
    evidence = Evidence(inputs.root, files)
    base: dict[str, Any] = {"Any": Any, "re": re}
    frozen_functions(evidence, *registrations[0], {"normalized", "phrase", "score"}, base)
    system_node = next(
        n.value
        for n in ast.parse(files[registrations[0][1]]).body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "SYSTEM" for t in n.targets)
    )
    api = {
        **base,
        "base_score": base["score"],
        "SYSTEM": ast.literal_eval(system_node),
        "SCHEMA": "qwen-long-history-v1",
    }
    frozen_functions(
        evidence, *registrations[1], {"inference_turns", "envelope", "score", "failure"}, api
    )
    return api


def audit_row(case: dict, row: dict, tokenizer: Any, api: dict) -> dict:
    turns = api["inference_turns"](case)
    chosen = row["selected_indices"]
    proposed = row["proposed_indices"]
    if chosen != sorted(set(chosen)) or not set(chosen) <= set(proposed):
        raise ValueError("selection order or fitting mismatch")
    if any(i < 0 or i >= len(turns) for i in proposed):
        raise ValueError("source index outside history")
    sources = [{"id": f"m{i}", **turns[i]} for i in chosen]
    prompt = api["envelope"](turns, chosen)
    if sources != row["selected_sources"] or prompt != row["prompt_messages"]:
        raise ValueError("source text or rendered prompt mismatch")
    ids = tokenizer.apply_chat_template(
        prompt, tokenize=True, add_generation_prompt=True, return_dict=False
    )
    decoded = tokenizer.decode(row["generated_ids"], skip_special_tokens=True).strip()
    if ids != row["prompt_ids"] or decoded != row["answer"]:
        raise ValueError("native prompt or generated answer mismatch")
    if (
        len(ids) != row["prompt_tokens"]
        or len(ids) > 512
        or len(row["generated_ids"]) != row["output_tokens"]
        or row["output_tokens"] > 64
        or row["total_tokens"] != row["prompt_tokens"] + row["output_tokens"]
    ):
        raise ValueError("token accounting mismatch")
    score = api["score"](row["answer"], case)
    if score != row["score"] or api["failure"](score, case, chosen) != row["failure"]:
        raise ValueError("saved scorer disagreement")
    missing = sorted(set(case["required"]) - set(chosen))
    if row["required_evidence_retained"] != (not missing):
        raise ValueError("evidence retention mismatch")
    classification = "correct" if score["correct"] else "selection" if missing else "generation"
    return {
        "classification": classification,
        "required_omitted_indices": missing,
        "fit_evicted_indices": sorted(set(proposed) - set(chosen)),
        "omitted_indices": sorted(set(range(len(turns))) - set(chosen)),
        "native_rendered_prompt": tokenizer.decode(ids, skip_special_tokens=False),
        "saved_row": row,
    }


def verify_preservation(root: Path, baseline: dict) -> int:
    for name, expected in baseline["sha256"].items():
        # Hashing frozen files is permitted; their held-out records are never parsed.
        with (root / name).open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError("frozen evidence changed: " + name)
    return len(baseline["sha256"])


def audit(root: Path, baseline: dict) -> dict:
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    inputs = Inputs(root)
    cases = inputs.json(RUN + "/development.json")
    validate_development(cases)
    gold = {case["id"]: case for case in cases}
    api = frozen_api(inputs)
    from transformers import AutoTokenizer

    tokenizer_dir = root / SUPPORT / "tokenizers/qwen"
    for path in tokenizer_dir.iterdir():
        if path.is_file():
            inputs.read(path.relative_to(root).as_posix())
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir, local_files_only=True, trust_remote_code=False
    )
    from toruk_lm.context_selection import LexicalContextSelector, terms

    published = inputs.json(RUN + "/results.json")
    arms, details = {}, {}
    for arm in ("before", "lexical", "after"):
        internal = "lexical" if arm == "lexical" else "toruk"
        folder = f"{RUN}/arms/{arm}/rehearsal"
        rows = inputs.rows(f"{folder}/development-{internal}-answers.jsonl")
        traces = inputs.rows(f"{folder}/selection-traces.jsonl")
        ordinary = [row for row in rows if not row["is_replay"]]
        if len(ordinary) != len(gold) or {r["id"] for r in ordinary} != set(gold):
            raise ValueError("development answer membership mismatch")
        if len(rows) != len(gold) + 1 or len(traces) != len(rows):
            raise ValueError("development replay count mismatch")
        details[arm] = {}
        for row, trace in zip(rows, traces, strict=True):
            case = gold[row["id"].removesuffix("-replay")]
            detail = audit_row(case, row, tokenizer, api)
            if trace["selected_indices"] != row["proposed_indices"]:
                raise ValueError("selection trace mismatch")
            if arm == "after":
                messages = case["messages"]
                query = terms(messages[-1]["content"])
                candidates = trace["gate"]["candidates"]
                if [c["index"] for c in candidates] != list(range(len(messages) - 3)):
                    raise ValueError("gate candidate coverage mismatch")
                ranked = []
                for candidate in candidates:
                    message = messages[candidate["index"]]
                    overlap = (
                        query & terms(message["content"]) if message["role"] == "user" else set()
                    )
                    admitted = bool(overlap)
                    if candidate["overlap"] != sorted(overlap) or candidate["admitted"] != admitted:
                        raise ValueError("gate admission mismatch")
                    if admitted:
                        ranked.append((candidate["cosine"], candidate["index"]))
                expected = sorted(
                    [i for _, i in sorted(ranked, reverse=True)[:2]]
                    + list(range(len(messages) - 3, len(messages)))
                )
                if expected != row["proposed_indices"]:
                    raise ValueError("gate ranking mismatch")
            elif arm == "lexical":
                if LexicalContextSelector().select(case["messages"])[0] != row["proposed_indices"]:
                    raise ValueError("lexical selection mismatch")
            if not row["is_replay"]:
                details[arm][case["id"]] = detail
        replay_keys = ("answer", "score", "selected_indices", "prompt_ids", "generated_ids", "work")
        if not rows[-1]["is_replay"] or rows[-1]["id"] != rows[0]["id"] + "-replay":
            raise ValueError("replay identity mismatch")
        if any(rows[0][key] != rows[-1][key] for key in replay_keys):
            raise ValueError("saved replay differs")
        summary = published["arms"][arm]
        for label, subset in (("seven_case_costs", ordinary), ("including_replay_costs", rows)):
            for field in COSTS:
                if not math.isclose(
                    sum(r[field] for r in subset), summary[label][field], abs_tol=1e-8
                ):
                    raise ValueError("published cost mismatch: " + field)
        if sum(r["score"]["correct"] for r in ordinary) != summary["correct"]:
            raise ValueError("published accuracy mismatch")
        arms[arm] = {
            "correct": summary["correct"],
            "cases": len(gold),
            **{
                key: summary[key]
                for key in (
                    "seven_case_costs",
                    "including_replay_costs",
                    "stage_cpu_seconds",
                    "stage_wall_seconds",
                )
            },
        }
    failures = []
    for case in cases:
        key = case["id"]
        current, lexical = details["after"][key], details["lexical"][key]
        if (
            not current["saved_row"]["score"]["correct"]
            and lexical["saved_row"]["score"]["correct"]
        ):
            different = sorted(
                set(lexical["saved_row"]["selected_indices"])
                - set(current["saved_row"]["selected_indices"])
            )
            failures.append(
                {
                    "case": case,
                    "v3_toruk": current,
                    "lexical": lexical,
                    "lexical_only_sources": [
                        {"index": i, **case["messages"][i]} for i in different
                    ],
                    "causal_limit": (
                        "Extra context differs; no causal selector improvement established."
                    ),
                }
            )
    wins = sum(
        details["after"][key]["saved_row"]["score"]["correct"]
        and not details["lexical"][key]["saved_row"]["score"]["correct"]
        for key in gold
    )
    return {
        "schema": "qwen-long-history-dev-v4",
        "mode": "offline development audit; no selector intervention",
        "baseline_head": baseline["head"],
        "selector_changed": False,
        "new_generations": 0,
        "heldout_records_parsed": 0,
        "arms_historical_v3": arms,
        "development_details": details,
        "lexical_wins_over_v3": failures,
        "paired_v3_versus_lexical": {
            "wins": wins,
            "losses": len(failures),
            "ties": len(gold) - wins - len(failures),
        },
        "after_this_audit": "Identical to saved v3; no new inference or cost measurement.",
        "preserved_files": verify_preservation(root, baseline),
        "consumed_development_inputs": inputs.consumed,
        "audit_cpu_seconds": time.process_time() - start_cpu,
        "audit_wall_seconds": time.perf_counter() - start_wall,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; preserve previous audit evidence")
    baseline = json.loads(args.baseline.read_bytes())
    if (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        != baseline["head"]
    ):
        raise ValueError("baseline commit changed")
    result = audit(ROOT, baseline)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "preserved_files": result["preserved_files"],
                "new_generations": 0,
                "failures": [
                    x["v3_toruk"]["classification"] for x in result["lexical_wins_over_v3"]
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
