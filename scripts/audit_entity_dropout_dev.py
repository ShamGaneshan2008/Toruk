"""Saved-only independent scoring/accounting audit. No torch import or model work."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import audit_value_start_replication_v2 as independent
import local_answer_entity_dropout as study
from answer_trainability_dev import read, rows, save, sha
from lifetime_job_v2 import verify_seal

ROOT, RUN, EXEC = study.ROOT, study.RUN, study.EXEC


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit() -> dict[str, Any]:
    old_integrity = independent.audit()
    plan, reg = study.check_plan(), study.check_registration()
    protected = study.preservation()
    require(
        sha(study.OLD / "registration.json") == plan["v2_registration_sha256"], "v2 registration"
    )
    require(
        sha(study.OLD / "review-inventory.json") == plan["preservation_inventory_sha256"],
        "v2 inventory",
    )
    independent.RUN = RUN  # Saved-only observation checker, explicit new evidence paths.
    costs = {}
    for receipt_name, cap in (
        ("preparation-budget-receipt.json", 180),
        ("execution-receipt.json", 1800),
        ("registered-budget-receipt.json", 1800),
    ):
        receipt = read(RUN / receipt_name)
        directory = RUN / receipt["path"]
        verify_seal(directory, expected_seal_sha256=receipt["sha256"])
        costs[receipt["path"]] = independent.closed_cost(directory, cap, 2147483648, 134217728)
    for item in reg["prerequisite_seals"]:
        directory = RUN / item["path"]
        verify_seal(directory, expected_seal_sha256=item["sha256"])
    summary, gate = read(EXEC / "summary.json"), read(EXEC / "training-gate.json")
    views = read(RUN / "training-views.json")
    schedules = read(RUN / "schedules.json")
    labels = read(RUN / "train-labels.json")
    for i, label in enumerate(labels):
        item = views[label["id"]]
        require(item["index"] == i, "original index")
        original, anonymous = item["original"], item["anonymous"]
        name = label["canonical"][0]
        require(
            anonymous["prefix"] == original["prefix"].replace(name, "ref")
            and anonymous["text"] == anonymous["prefix"] + label["gold"]
            and len(anonymous["prefix"].encode()) == len(original["prefix"].encode()),
            "view bytes",
        )
    stages = rows(EXEC / "stages.jsonl")
    expected = [(kind, s, v, a) for s, v, a in study.ORDER for kind in ("fit", "evaluate")]
    if gate["pass_gate"]:
        expected += [("development", s, v, a) for s, v, a in study.ORDER]
    require(
        [s["stage"] for s in stages] == [f"{kind}-{s}-{v}-{a}" for kind, s, v, a in expected],
        "stage order and once-only work",
    )
    cells: dict[str, Any] = {}
    failed = []
    for (kind, seed, variant, arm), item in zip(expected, stages, strict=True):
        directory = RUN / item["path"]
        verify_seal(directory, expected_seal_sha256=item["sha256"])
        cost = independent.closed_cost(directory, study.CAPS[kind], 2147483648, 134217728)
        costs[item["path"]] = cost
        key = f"{seed}-{variant}-{arm}"
        cell = cells.setdefault(key, {})
        if kind == "fit":
            trace, meta = (
                rows(directory / "training.jsonl"),
                read(directory / "training-summary.json"),
            )
            require(len(trace) == 1536, "fixed update count")
            exposure: Counter[Any] = Counter()
            targets = positions = 0
            for actual, batch in zip(trace, schedules[seed], strict=True):
                require(all(actual[k] == v for k, v in batch.items()), "matched schedule")
                wanted = [
                    "anonymous"
                    if arm == "drop50" and (batch["epoch"] + views[i]["index"]) % 2 == 0
                    else "original"
                    for i in batch["ids"]
                ]
                require(actual["views"] == wanted, "dropout schedule")
                exposure.update(zip(batch["ids"], wanted, strict=True))
                n = actual["history_targets"] + actual["answer_targets"]
                require(actual["weighted_denominator"] == n, "uniform target weighting")
                require(
                    math.isclose(
                        actual["objective"],
                        (actual["history_loss"] + actual["answer_loss"]) / n,
                        rel_tol=2e-6,
                        abs_tol=2e-6,
                    ),
                    "objective partition",
                )
                targets += n
                positions += actual["forward_positions"]
            require(targets == 692224 and positions == 786432, "target/forward work")
            for identity in views:
                require(
                    exposure[identity, "original"] == (64 if arm == "drop50" else 128)
                    and exposure[identity, "anonymous"] == (64 if arm == "drop50" else 0),
                    "per-document exposure",
                )
            checkpoint = directory / "checkpoint.pt"
            checkpoint_meta = read(directory / "checkpoint-meta.json")
            require(
                sha(checkpoint) == checkpoint_meta["sha256"]
                and checkpoint.stat().st_size == checkpoint_meta["bytes"],
                "checkpoint bytes",
            )
            require(
                meta["initial_sha256"] == plan["initial_hashes"][f"{seed}-{variant}"],
                "initial parity",
            )
            if arm == "uniform":
                prior = read(
                    study.OLD / "registered/execution/stages" / f"fit-{key}/training-summary.json"
                )
                require(
                    meta["final_model_sha256"] == prior["final_model_sha256"],
                    "final control parity",
                )
            cell["fit"] = meta
        else:
            split = "train" if kind == "evaluate" else "dev"
            metrics = independent.verify_observation(directory, split)["metrics"]
            require(
                all(
                    summary["training" if split == "train" else "development"][key][k] == v
                    for k, v in metrics.items()
                ),
                "summary independently rescored",
            )
            cell[split] = read(directory / "metrics.json")
            raw = rows(directory / "predictions-main.jsonl")
            for p, label in zip(raw[:-1], read(RUN / f"{split}-labels.json"), strict=True):
                flags = independent.flags(p["result"]["generated_ids"], label["gold"])
                if not flags["exact"]:
                    failed.append(
                        dict(
                            cell=key,
                            split=split,
                            id=p["id"],
                            gold=label["gold"],
                            prefix=p["prefix"],
                            result=p["result"],
                            flags=flags,
                        )
                    )
            token_costs = read(directory / "token-costs.json")
            for mode in ("main", "question-only") if split == "dev" else ("main",):
                predictions = rows(directory / f"predictions-{mode}.jsonl")
                require(
                    token_costs[mode]["generated_tokens"]
                    == sum(len(p["result"]["generated_ids"]) for p in predictions),
                    "generated token count",
                )
                require(
                    token_costs[mode]["input_tokens"]
                    == sum(len(p["input_ids"]) for p in predictions),
                    "input token count",
                )
                if arm == "uniform":
                    old = study.OLD / "registered/execution/stages" / f"{kind}-{key}"
                    old_predictions = rows(old / f"predictions-{mode}.jsonl")
                    require(
                        all(
                            p["input_ids"] == q["input_ids"] and p["result"] == q["result"]
                            for p, q in zip(predictions, old_predictions, strict=True)
                        ),
                        "control native parity",
                    )
            cell[split + "_token_costs"] = token_costs
    actual_training = len(cells) == 16 and all(
        independent.mastery(c["train"]) for c in cells.values()
    )
    require(
        actual_training == gate["pass_gate"] == summary["training_gate"], "global training gate"
    )
    if actual_training:
        gains, pairs, floors, nll = {}, {}, {}, {}
        for seed in study.v2.CROSSED:
            for variant in study.v2.PARAMETERS:
                key = f"{seed}-{variant}"
                c, t = cells[key + "-uniform"]["dev"], cells[key + "-drop50"]["dev"]
                gains[key] = t["exact"] - c["exact"]
                pairs[key] = (
                    gains[key] >= 0
                    and (c["exact"] == 24 or gains[key] > 0)
                    and t["eos"] >= c["eos"]
                    and all(
                        t["categories"][k] >= c["categories"][k]
                        for k in ("city", "code", "unknown")
                    )
                )
                floors[key] = independent.floor(t)
            if seed.startswith("i601-"):
                ids = {
                    label["id"]
                    for label in read(RUN / "dev-labels.json")
                    if label["category"] == "city"
                }
                values = {
                    arm: sum(
                        r["first_loss"]
                        for r in rows(
                            EXEC
                            / "stages"
                            / f"development-{seed}-recurrent-{arm}/teacher-losses.jsonl"
                        )
                        if r["id"] in ids
                    )
                    / 8
                    for arm in ("uniform", "drop50")
                }
                nll[seed] = values["drop50"] < values["uniform"]
        model_gains = {
            v: sum(g for key, g in gains.items() if key.endswith("-" + v))
            for v in study.v2.PARAMETERS
        }
        passed = (
            all(pairs.values())
            and all(floors.values())
            and all(nll.values())
            and all(g > 0 for g in model_gains.values())
        )
        require(passed == summary["comparison"]["pass_gate"], "independent development gate")
        decision = "DEVELOPMENT_GATES_PASS" if passed else "STOP_DEVELOPMENT_FAILURE"
    else:
        require(
            not summary["development"] and not list((EXEC / "stages").glob("development-*")),
            "dev NOT_RUN",
        )
        gains, pairs, floors, nll, model_gains = {}, {}, {}, {}, {}
        decision = "STOP_TRAINING_FAILURE"
    require(decision == summary["decision"], "decision")
    independent.RUN = study.OLD
    return dict(
        status="PASS",
        decision=decision,
        training_gate=actual_training,
        development_evaluated=actual_training,
        pair_gains=gains,
        pair_gates=pairs,
        candidate_floors=floors,
        city_first_nll_gates=nll,
        model_gains=model_gains,
        cells=cells,
        failures=failed,
        costs=costs,
        protected_v2_files=protected,
        historical_decision=old_integrity["decision"],
        model_forwards=0,
        heldout_opened=False,
        memory_advantage=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        require(
            args.output.resolve().is_relative_to(RUN)
            and not args.output.resolve().is_relative_to(RUN / "registered"),
            "outside sealed science",
        )
        save(args.output, result)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("cells", "failures", "costs")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
