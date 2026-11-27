"""Independent saved-only audit: no torch, model runner or answer generation imports."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import audit_value_start_replication_v2 as base
from lifetime_job_v2 import verify_seal

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-city-contrastive-dev-v1"
OLD = ROOT / "artifacts/local-answer-value-start-replication-v2"
EXEC = RUN / "registered/execution"


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read(path: Path) -> Any:
    return base.read(path)


def softplus(value: float) -> float:
    return max(value, 0) + math.log1p(math.exp(-abs(value)))


def pair(control: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    old, new = ({c["id"]: c["exact"] for c in m["cases"]} for m in (control, candidate))
    require(set(old) == set(new), "paired identities")
    lost = [i for i in old if old[i] and not new[i]]
    fixed = [i for i in old if not old[i] and new[i]]
    gain = candidate["exact"] - control["exact"]
    passed = (
        not lost
        and gain >= 0
        and (control["exact"] == 24 or gain > 0)
        and candidate["eos"] >= control["eos"]
        and all(
            candidate["categories"][c] >= control["categories"][c]
            for c in ("city", "code", "unknown")
        )
    )
    return dict(
        pass_pair=bool(passed),
        gain=gain,
        introduced=lost,
        fixed=fixed,
        ceiling=control["exact"] == 24,
    )


def audit() -> dict[str, Any]:
    historical = base.audit()
    plan, reg = read(RUN / "plan-final.json"), read(RUN / "registration.json")
    require(reg["plan_sha256"] == base.sha(RUN / "plan-final.json"), "plan binding")
    for name, digest in plan["sources"].items():
        require(base.sha(ROOT / name) == base.sha(RUN / "sources" / name) == digest, name)
    for name, digest in plan["data"].items():
        require(base.sha(RUN / name) == digest, name)
    require(plan["coefficient"] == 0.1 and plan["margin"] == 2, "frozen intervention")
    require(
        read(RUN / "attempt-start.json")["registration_sha256"]
        == base.sha(RUN / "registration.json"),
        "attempt binding",
    )
    require(
        plan["data"]
        == {
            **read(OLD / "plan-final.json")["data"],
            "confusers.json": base.sha(RUN / "confusers.json"),
        },
        "unchanged data",
    )
    labels = read(RUN / "train-labels.json")
    mapping = read(RUN / "confusers.json")
    for r in labels:
        if r["category"] == "city":
            others = {
                p["gold"]
                for p in labels
                if p["category"] == "city" and p["canonical"][0] == r["canonical"][0]
            } - {r["gold"]}
            require(
                len(others) == 1 and mapping[r["id"]] == next(iter(others)).encode()[0] + 3,
                "training-only confuser",
            )
    costs = {}
    for item in [
        *reg["prerequisite_seals"],
        read(RUN / "execution-receipt.json"),
        read(RUN / "registered-budget-receipt.json"),
    ]:
        directory = RUN / item["path"]
        verify_seal(directory, expected_seal_sha256=item["sha256"])
        cap = (
            60
            if item["path"].endswith("contracts")
            else 45
            if item["path"].endswith("rehearsal")
            else 150
            if item["path"].startswith("preparation")
            else 1800
        )
        costs[item["path"]] = base.closed_cost(directory, cap, 2147483648, 134217728)
    ledger = base.rows(EXEC / "stages.jsonl")
    expected = [f"{kind}-{s}-{v}-{a}" for s, v, a in plan["order"] for kind in ("fit", "evaluate")]
    docs = {d["id"]: d for d in read(RUN / "train-documents.json")}
    schedules = read(RUN / "schedules.json")
    training: dict[str, Any] = {}
    development: dict[str, Any] = {}
    cells: dict[str, Any] = {}
    initializations: dict[str, str] = {}
    verified_steps = 0
    original = base.RUN
    try:
        base.RUN = RUN
        for entry in ledger:
            name = entry["stage"]
            directory = EXEC / entry["path"]
            verify_seal(directory, expected_seal_sha256=entry["seal_sha256"])
            kind = name.split("-", 1)[0]
            costs[name] = base.closed_cost(directory, reg["caps"][kind], 2147483648, 134217728)
            key = name.removeprefix(kind + "-")
            crossed, model, arm = key.rsplit("-", 2)
            cell = cells.setdefault(key, {})
            if kind == "fit":
                meta, stats = (
                    read(directory / "checkpoint-meta.json"),
                    read(directory / "training-summary.json"),
                )
                require(
                    base.sha(directory / "checkpoint.pt") == meta["sha256"]
                    and (directory / "checkpoint.pt").stat().st_size == meta["bytes"],
                    "checkpoint",
                )
                cell["checkpoint"] = meta
                trace = base.rows(directory / "training.jsonl")
                require(len(trace) == 1536, "fixed steps")
                exposure: Counter[str] = Counter()
                targets = mass = contributions = 0
                for r, batch in zip(trace, schedules[crossed], strict=True):
                    require(all(r[k] == v for k, v in batch.items()), "exact schedule")
                    require(r["forward_positions"] == 512 and r["first_targets"] == 8, "dense work")
                    nt = sum(len(docs[i]["text"].encode()) + 1 for i in batch["ids"])
                    require(
                        r["history_targets"] + r["answer_targets"] == nt
                        and r["weighted_denominator"] == nt + 120,
                        "target accounting",
                    )
                    records = r["city_records"]
                    require(
                        [c["id"] for c in records] == [i for i in batch["ids"] if i in mapping],
                        "city contribution order",
                    )
                    values = []
                    for c in records:
                        require(
                            c["gold_id"] == docs[c["id"]]["gold"].encode()[0] + 3
                            and c["confuser_id"] == mapping[c["id"]],
                            "native auxiliary targets",
                        )
                        require(
                            math.isfinite(c["gold_logit"]) and math.isfinite(c["confuser_logit"]),
                            "finite logits",
                        )
                        values.append(softplus(2 + c["confuser_logit"] - c["gold_logit"]))
                    auxiliary = sum(values) / len(values) if values else 0
                    require(
                        r["city_contributions"] == len(values)
                        and math.isclose(r["city_loss"], auxiliary, rel_tol=2e-6, abs_tol=2e-6),
                        "auxiliary arithmetic",
                    )
                    ce = (r["history_loss"] + r["answer_loss"] + 15 * r["first_loss"]) / (nt + 120)
                    require(
                        math.isclose(ce, r["ce_objective"], rel_tol=2e-6, abs_tol=2e-6),
                        "CE arithmetic",
                    )
                    obj = ce + (0.1 * auxiliary if arm == "contrast" else 0)
                    require(
                        math.isclose(obj, r["objective"], rel_tol=2e-6, abs_tol=2e-6)
                        and math.isfinite(r["gradient_norm"]),
                        "objective arithmetic",
                    )
                    targets += nt
                    mass += nt + 120
                    contributions += len(values)
                    exposure.update(batch["ids"])
                require(
                    targets == 692224
                    and mass == 876544
                    and contributions == 4096
                    and exposure == Counter({i: 128 for i in docs}),
                    "total work",
                )
                require(
                    stats["steps"] == 1536
                    and stats["targets"] == 692224
                    and stats["forward_positions"] == 786432,
                    "fit summary",
                )
                initial_key = crossed.split("-")[0] + "-" + model
                require(
                    stats["initial_sha256"]
                    == plan["initial_hashes"][crossed + "-" + model]
                    == initializations.setdefault(initial_key, stats["initial_sha256"]),
                    "initialization",
                )
                if arm == "control":
                    prior = OLD / "registered/execution/stages" / f"fit-{crossed}-{model}-first16"
                    require(
                        stats["final_model_sha256"]
                        == read(prior / "training-summary.json")["final_model_sha256"]
                        and read(directory / "control-parity.json")["final_tensors"],
                        "control tensors",
                    )
                verified_steps += 1536
            else:
                split = "dev" if kind == "development" else "train"
                observation = base.verify_observation(directory, split)
                cell[split] = observation
                destination = development if split == "dev" else training
                destination[key] = observation["metrics"]
                if arm == "control":
                    prior = (
                        OLD / "registered/execution/stages" / f"{kind}-{crossed}-{model}-first16"
                    )
                    for mode in ("main", "question-only") if split == "dev" else ("main",):
                        a, b = (
                            base.rows(p / f"predictions-{mode}.jsonl") for p in (directory, prior)
                        )
                        require(
                            all(
                                x["input_ids"] == y["input_ids"] and x["result"] == y["result"]
                                for x, y in zip(a, b, strict=True)
                            ),
                            "control native parity",
                        )
                token = read(directory / "token-costs.json")
                for mode in ("main", "question-only") if split == "dev" else ("main",):
                    raw = base.rows(directory / f"predictions-{mode}.jsonl")
                    require(
                        token[mode]["requests"] == len(raw)
                        and token[mode]["input_tokens"] == sum(len(r["input_ids"]) for r in raw)
                        and token[mode]["generated_tokens"]
                        == sum(len(r["result"]["generated_ids"]) for r in raw)
                        and token[mode]["forward_positions"]
                        == sum(r["result"]["forward_positions"] for r in raw),
                        "token ledger",
                    )
        require(len(training) == 16, "all training cells")
        eligible = all(base.mastery(m) for m in training.values())
        require(read(EXEC / "training-gate.json")["pass_gate"] == eligible, "training gate")
        pairs, floors, nll, gains = {}, {}, {}, {}
        passed = False
        if eligible:
            require(read(EXEC / "control-development-gate.json")["pass_gate"], "control barrier")
            for arm in ("control", "contrast"):
                expected += [
                    f"development-{s}-{v}-{arm}"
                    for s in plan["crossed_seeds"]
                    for v in plan["parameters"]
                ]
            for seed in plan["crossed_seeds"]:
                for model in plan["parameters"]:
                    key = seed + "-" + model
                    pairs[key] = pair(development[key + "-control"], development[key + "-contrast"])
                    floors[key + "-contrast"] = base.floor(development[key + "-contrast"])
                if seed.startswith("i601-"):
                    city = {
                        r["id"] for r in read(RUN / "dev-labels.json") if r["category"] == "city"
                    }
                    means = {
                        a: sum(
                            r["first_loss"]
                            for r in base.rows(
                                EXEC
                                / "stages"
                                / f"development-{seed}-recurrent-{a}/teacher-losses.jsonl"
                            )
                            if r["id"] in city
                        )
                        / 8
                        for a in ("control", "contrast")
                    }
                    nll[seed] = dict(**means, improved=means["contrast"] < means["control"])
            gains = {
                v: sum(p["gain"] for k, p in pairs.items() if k.endswith("-" + v))
                for v in plan["parameters"]
            }
            passed = (
                all(p["pass_pair"] for p in pairs.values())
                and all(floors.values())
                and all(g > 0 for g in gains.values())
                and all(v["improved"] for v in nll.values())
            )
        require([r["stage"] for r in ledger] == expected, "once-only order and dev barrier")
        decision = (
            "STOP_TRAINING_FAILURE"
            if not eligible
            else "DEVELOPMENT_GATES_PASS"
            if passed
            else "STOP_DEVELOPMENT_FAILURE"
        )
        summary = read(EXEC / "summary.json")
        require(
            summary["decision"] == decision
            and summary["training"] == training
            and summary["development"] == development,
            "independent decision/metrics",
        )
        if eligible:
            require(
                summary["comparison"]
                == dict(
                    pass_gate=passed,
                    pairs=pairs,
                    candidate_floors=floors,
                    model_gains=gains,
                    recurrent601_city_first_nll=nll,
                ),
                "independent comparison",
            )
        return dict(
            status="PASS",
            measurement_integrity="PASS",
            decision=decision,
            training_gate=eligible,
            development_evaluated=eligible,
            cells=cells,
            pairs=pairs,
            floors=floors,
            city_first_nll=nll,
            model_gains=gains,
            costs=costs,
            scientific_seals=len(ledger),
            optimizer_steps_verified=verified_steps,
            historical_decision=historical["decision"],
            model_forwards=0,
            heldout_opened=False,
        )
    finally:
        base.RUN = original


def partial_audit(error: Exception) -> dict[str, Any]:
    """Retain independent scoring of completed observations after a terminal STOP.

    Missing outputs are NOT_RUN, never zeros. A partial audit never certifies the
    complete experiment's measurement integrity or changes a failed gate.
    """
    cells: dict[str, Any] = {}
    costs: dict[str, Any] = {}
    failures: dict[str, str] = {}
    control_failure = False
    original = base.RUN
    try:
        base.RUN = RUN
        for directory in sorted((EXEC / "stages").glob("*")):
            if not directory.is_dir():
                continue
            name = directory.name
            try:
                verify_seal(directory)
                costs[name] = read(directory / "cost.json")
                if (directory / "control-parity.json").exists():
                    control_failure |= not all(read(directory / "control-parity.json").values())
                if (
                    name.startswith(("evaluate-", "development-"))
                    and (directory / "metrics.json").exists()
                ):
                    split = "dev" if name.startswith("development-") else "train"
                    cells[name] = base.verify_observation(directory, split)
            except Exception as problem:
                failures[name] = repr(problem)
        for relative in (
            "preparation/contracts",
            "preparation/rehearsal",
            "preparation/budget",
            "registered/execution",
            "registered/budget",
        ):
            path = RUN / relative / "cost.json"
            if path.exists():
                costs[relative] = read(path)
        resource = any(c.get("failure") for c in costs.values())
        return dict(
            status="PARTIAL",
            measurement_integrity="INCOMPLETE",
            audit_error=repr(error),
            decision="STOP_CONTROL_REPRODUCTION"
            if control_failure
            else "STOP_RESOURCE"
            if resource
            else "BLOCKED",
            cells=cells,
            costs=costs,
            seal_failures=failures,
            missing_outputs="NOT_RUN",
            model_forwards=0,
            heldout_opened=False,
        )
    finally:
        base.RUN = original


if __name__ == "__main__":
    try:
        result = audit()
    except Exception as error:
        result = partial_audit(error)
    with (RUN / "independent-audit.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("cells", "costs")}, indent=2))
