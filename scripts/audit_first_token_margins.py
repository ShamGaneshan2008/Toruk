"""Derive provenance and observed-error margins from the consumed 260-row probe.

Standard library only. This module cannot load a model or execute inference.
"""

import argparse
import hashlib
import json
import math
import runpy
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "artifacts/local-answer-first-byte-probe-v1"
OUT = ROOT / "artifacts/local-answer-first-token-review-v1"
DIAGNOSIS_COMMIT = "743c29ff1b1dc5c86b81de48888a4753860ef0f8"
PROBE_COMMIT = "56af6eddf1467e52bd6e248b196b81f40d99b183"
PROBE_SHA = "b244089a172bf7933fe53ee1558b2e8ac1c393c03e837e22e884dee052863213"
SOURCES = (
    "scripts/audit_first_token_margins.py",
    "tests/test_first_token_margin_review.py",
    "docs/research/local-answer-first-token-review-v1-protocol.md",
    "docs/research/local-answer-paired-batch-v1-proposal.md",
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def id_hash(ids: list[int]) -> str:
    return hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode("ascii")).hexdigest()


def write(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def inventory(path: Path, commit: str) -> int:
    entries = read(path)["files"]
    for name, meta in entries.items():
        check((ROOT / name).is_file(), "missing evidence: " + name)
        check(digest(ROOT / name) == meta["sha256"], "evidence hash: " + name)
        check((ROOT / name).stat().st_size == meta["bytes"], "evidence size: " + name)
    names = {path.relative_to(ROOT).as_posix(), *entries}
    committed = set(git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines())
    check(committed == names, "scoped preservation commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=True)
    check(not git("diff", commit, "--name-only", "--", *sorted(names)), "preserved tree changed")
    return len(entries)


def margins(logits: list[float], gold: int, observed_error: int | None) -> dict[str, Any]:
    check(len(logits) == 259 and all(math.isfinite(v) for v in logits), "finite 259 logits")
    check(2 <= gold < 259, "eligible expected token")
    check(observed_error is None or 2 <= observed_error < 259, "eligible reference token")
    ordered = sorted(range(2, 259), key=lambda token: (-logits[token], token))
    top = ordered[0]
    full_max = max(logits)
    z_full = sum(math.exp(v - full_max) for v in logits)
    z_eligible = sum(math.exp(logits[i] - logits[top]) for i in range(2, 259))
    return dict(
        expected_first_id=gold,
        top_first_id=top,
        expected_rank=ordered.index(gold) + 1,
        expected_probability_full=math.exp(logits[gold] - full_max) / z_full,
        top_probability_full=math.exp(logits[top] - full_max) / z_full,
        expected_probability_eligible=math.exp(logits[gold] - logits[top]) / z_eligible,
        top_probability_eligible=1 / z_eligible,
        expected_minus_top=logits[gold] - logits[top],
        reference_observed_error_id=observed_error,
        expected_minus_observed_error=(
            None if observed_error is None else logits[gold] - logits[observed_error]
        ),
        expected_minus_best_other=logits[gold] - max(logits[i] for i in range(2, 259) if i != gold),
    )


def frozen_inputs() -> dict[str, str]:
    paths = [PROBE / "inventory.json", PROBE / "registration.json"]
    paths += [ROOT / "artifacts/local-answer-first-byte-v1/inventory.json"]
    paths += [
        ROOT / meta["path"] for meta in read(PROBE / "registration.json")["checkpoints"].values()
    ]
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in paths}


def freeze() -> None:
    check(Path(git("rev-parse", "--show-toplevel")).resolve() == ROOT, "Git root")
    # No frozen artifact is rewritten, and this is not another inference registration.
    inputs = frozen_inputs()
    OUT.mkdir()
    write(
        OUT / "registration.json",
        dict(
            version="local-answer-first-token-review-v1",
            date="2026-11-22",
            kind="post-hoc saved-vector derivation; zero new inference",
            head=git("rev-parse", "HEAD"),
            branch=git("branch", "--show-current"),
            origin_main=git("rev-parse", "origin/main"),
            origin_main_vs_head=git("rev-list", "--left-right", "--count", "origin/main...HEAD"),
            diagnosis_commit=DIAGNOSIS_COMMIT,
            probe_commit=PROBE_COMMIT,
            probe_registration_sha256=PROBE_SHA,
            records=260,
            sources={name: digest(ROOT / name) for name in SOURCES},
            inputs=inputs,
            observed_error_reference="archived ordinary947 first ID, only when different from gold",
            original_probe_caps=dict(cpu=200, wall=200, memory=2147483648),
            new_forward_passes=0,
            new_training_updates=0,
            new_generated_answers=0,
        ),
    )
    print(json.dumps(dict(registration_sha256=digest(OUT / "registration.json"))))


def build() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reg = read(OUT / "registration.json")
    for name, expected in {**reg["sources"], **reg["inputs"]}.items():
        check(digest(ROOT / name) == expected, "review input changed: " + name)
    diagnosis_entries = inventory(
        ROOT / "artifacts/local-answer-first-byte-v1/inventory.json", DIAGNOSIS_COMMIT
    )
    probe_entries = inventory(PROBE / "inventory.json", PROBE_COMMIT)
    check(digest(PROBE / "registration.json") == PROBE_SHA, "original probe registration")
    # The archived auditor is standard-library-only. Its main block is not executed.
    audited = runpy.run_path(str(PROBE / "verify_saved.py"), run_name="saved_vector_auditor")[
        "audit"
    ]()
    checkpoints = read(PROBE / "registration.json")["checkpoints"]
    labels = {case["id"]: case for case in read(PROBE / "gold-evaluator.json")}
    prefixes = {case["id"]: case for case in read(PROBE / "prefix-inputs.json")}
    originals = read(PROBE / "original-first-ids.json")
    saved_metrics = {m["record_id"]: m for m in lines(PROBE / "measurements.jsonl")}
    cache: dict[tuple[str, str], tuple[list[dict[str, Any]], list[dict[str, Any]]]] = {}
    results = []
    for plan in read(PROBE / "plan.json"):
        cell, phase, index, identity = (plan[k] for k in ("cell", "phase", "index", "id"))
        directory = PROBE / "stages" / f"{phase}-{cell}"
        if (phase, cell) not in cache:
            cache[phase, cell] = (
                lines(directory / "vectors.jsonl"),
                lines(directory / "request-costs.jsonl"),
            )
        raw, request = (records[index] for records in cache[phase, cell])
        label = labels[identity]
        gold = label["expected_first_id"]
        bad_id = originals["947-ordinary"][identity]
        reference = bad_id if bad_id != gold else None
        m = margins(raw["logits"], gold, reference)
        saved = saved_metrics[plan["record_id"]]
        check(
            m["expected_rank"] == saved["expected_rank"]
            and m["top_first_id"] == saved["predicted_first_id"],
            "saved metric parity",
        )
        check(m["top_first_id"] == originals[cell][identity], "archived first-token reproduction")
        check(request["record_id"] == raw["record_id"] == plan["record_id"], "raw/cost identity")
        prompt = prefixes[identity]["prefix"]
        results.append(
            dict(
                **{k: v for k, v in plan.items() if k != "index"},
                **m,
                checkpoint_sha256=checkpoints[cell]["sha256"],
                checkpoint_path=checkpoints[cell]["path"],
                prefix_utf8_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                input_ids_sha256=id_hash(raw["input_ids"]),
                prefix_input_ids_sha256=id_hash(prefixes[identity]["input_ids"]),
                input_hash_encoding="compact JSON native integer ID array, ASCII; no newline",
                expected_byte=label["expected_first_byte"],
                expected_char=chr(label["expected_first_byte"]),
                top_char=chr(m["top_first_id"] - 3) if m["top_first_id"] >= 3 else "EOS",
                canonical=label["canonical"],
                template=label["template"],
                target_y=53,
                local_logit=21,
                prefix_bytes=53,
                native_prefix_ids=54,
                archived_first_id=originals[cell][identity],
                reproduces_archived_first=True,
                raw_file=(directory / "vectors.jsonl").relative_to(ROOT).as_posix(),
                raw_file_sha256=digest(directory / "vectors.jsonl"),
                raw_line=index + 1,
                saved_request_interval=request,
                isolated_forward_cpu_wall=None,
                request_interval_scope=(
                    "input checks, consume/forward, I/O, selection/parity; quantized CPU"
                ),
                cold_worker_cost_file=(directory / "cost.json").relative_to(ROOT).as_posix(),
                loading_error=None,
                numerical_error=None,
                new_forward_pass=False,
            )
        )
    check(len(results) == 260, "260 derived records")
    main = [r for r in results if r["phase"] == "prefix" and not r["replay"]]
    cells = {}
    comparisons = []
    for cell in read(PROBE / "registration.json")["order"]:
        records = [r for r in main if r["cell"] == cell]
        groupings = {}
        for name, key in (
            ("expected_byte", lambda r: r["expected_char"]),
            ("predicted_byte", lambda r: r["top_char"]),
            ("entity_value", lambda r: "/".join(r["canonical"][:3])),
        ):
            grouped = {}
            for value in sorted({key(r) for r in records}):
                group = [r for r in records if key(r) == value]
                wrong = [r for r in group if r["top_first_id"] != r["expected_first_id"]]
                grouped[value] = dict(
                    count=len(group),
                    wrong=len(wrong),
                    expected_ranks=sorted({r["expected_rank"] for r in group}),
                    expected_minus_top_range=[
                        min(r["expected_minus_top"] for r in group),
                        max(r["expected_minus_top"] for r in group),
                    ],
                    predicted_counts=dict(Counter(r["top_char"] for r in group)),
                )
            groupings[name] = grouped
        cells[cell] = groupings
    failed = [
        r
        for r in main
        if r["cell"] == "947-ordinary" and r["expected_first_id"] != r["top_first_id"]
    ]
    check(len(failed) == 16, "16 failures")
    for failure in failed:
        comparisons.append(
            dict(
                id=failure["id"],
                canonical=failure["canonical"],
                expected_id=failure["expected_first_id"],
                error_id=failure["top_first_id"],
                cells={
                    r["cell"]: {
                        k: r[k]
                        for k in (
                            "expected_rank",
                            "expected_probability_eligible",
                            "top_probability_eligible",
                            "expected_minus_top",
                            "expected_minus_observed_error",
                            "expected_minus_best_other",
                        )
                    }
                    for r in main
                    if r["id"] == failure["id"]
                },
            )
        )
    return results, dict(
        status="PASS",
        records=260,
        new_forward_passes=0,
        diagnosis_inventory_entries=diagnosis_entries,
        probe_inventory_entries=probe_entries,
        complete_probe_cost=audited["complete_execution_cost"],
        original_probe_registration_sha256=PROBE_SHA,
        review_registration_sha256=digest(OUT / "registration.json"),
        max_parity_difference=audited["max_parity_difference"],
        parity_checks=128,
        prompt_and_target_parity=True,
        cells=cells,
        case_comparisons=comparisons,
        missing_m_reproduced=cells["947-ordinary"]["expected_byte"]["m"]["wrong"] == 8,
    )


def derive() -> None:
    try:
        records, summary = build()
        with (OUT / "records.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for record in records:
                stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
        write(OUT / "summary.json", summary)
        print(json.dumps(dict(status="PASS", records=len(records), new_forward_passes=0)))
    except BaseException as error:
        if not (OUT / "STOP.json").exists():
            write(OUT / "STOP.json", dict(error=repr(error), new_forward_passes=0))
        raise


def audit() -> None:
    records, summary = build()
    check(records == lines(OUT / "records.jsonl"), "derived rows changed")
    check(summary == read(OUT / "summary.json"), "derived summary changed")
    print(json.dumps(dict(status="PASS", records=260, new_forward_passes=0)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "derive", "audit"))
    args = parser.parse_args()
    {"freeze": freeze, "derive": derive, "audit": audit}[args.command]()


if __name__ == "__main__":
    main()
