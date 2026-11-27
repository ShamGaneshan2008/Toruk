"""Independent saved-only value-start replication v2 auditor; never imports torch."""

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-value-start-replication-v2"
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job_v2 import verify_seal  # noqa: E402

VALUES = ("la", "mi", "so", "tu", "R-7", "Q_2", "V:4", "Z!6", "?")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flags(ids, gold):
    expected = [b + 3 for b in gold.encode()]
    eos = bool(ids and ids[-1] == 2)
    body = ids[:-1] if eos else ids
    allowed = {tuple(b + 3 for b in value.encode()) for value in VALUES}
    return dict(
        exact=ids == expected + [2],
        value_exact=body == expected,
        eos=eos,
        wrong_first=not ids or ids[0] != expected[0],
        malformed=tuple(body) not in allowed,
        repetition=any(
            ids[i : i + w] * 3 == ids[i : i + 3 * w]
            for w in (1, 2)
            for i in range(len(ids) - 3 * w + 1)
        ),
    )


def mastery(m):
    return (
        m["exact"] == 96
        and m["eos"] == 96
        and m["wrong_first"] == 0
        and m["malformed"] == 0
        and m["repetition"] == 0
    )


def floor(m):
    return (
        m["exact"] >= 22
        and m["categories"]["city"] >= 7
        and m["categories"]["code"] >= 7
        and m["categories"]["unknown"] == 8
        and m["eos"] == 24
        and m["malformed"] == 0
        and m["repetition"] == 0
        and m["known_context_gain"] >= 8
    )


def scores(raw, inputs, labels, question=False):
    require(len(raw) == len(labels) + 1 and raw[-1]["replay"], "prediction row count/replay")
    require(raw[0]["result"] == raw[-1]["result"], "generation replay")
    counts: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    cases = []
    for p, case, label in zip(raw[:-1], inputs, labels, strict=True):
        require(p["id"] == case["id"] == label["id"], "case identity")
        prefix = case["prefix"]
        if question:
            lines = prefix.splitlines(keepends=True)
            prefix = lines[0] + "." * (len(lines[1].encode()) - 1) + "\n" + lines[2]
        require(
            p["prefix"] == prefix and p["input_ids"] == [1, *(b + 3 for b in prefix.encode())],
            "native prefix",
        )
        ids = p["result"]["generated_ids"]
        require(1 <= len(ids) <= 8 and all(2 <= i < 259 for i in ids), "native generation budget")
        require(max(p["cost"].values()) <= 2, "generation request cap")
        f = flags(ids, label["gold"])
        counts.update({k: int(v) for k, v in f.items()})
        categories[label["category"]] += int(f["exact"])
        cases.append(dict(id=label["id"], gold=label["gold"], category=label["category"], **f))
    return dict(count=len(labels), **counts, categories=dict(categories), cases=cases)


def verify_observation(directory, split):
    labels = read(RUN / f"{split}-labels.json")
    inputs = read(RUN / f"{split}-inputs.json")
    raw = rows(directory / "predictions-main.jsonl")
    require(
        sha(directory / "predictions-main.jsonl")
        == read(directory / "generation-complete-main.json")["predictions_sha256"],
        "closed raw stream",
    )
    actual = scores(raw, inputs, labels)
    stored = read(directory / "metrics.json")
    require(all(stored[k] == v for k, v in actual.items()), "independent outcomes")
    vectors = rows(directory / "first-vectors.jsonl")
    measures = rows(directory / "first-measurements.jsonl")
    require(len(vectors) == len(measures) == len(inputs) + 1, "vector count")
    require(vectors[0]["logits"] == vectors[-1]["logits"], "vector replay")
    first_ces = []
    examples = []
    for i, (vector, m) in enumerate(zip(vectors, measures, strict=True)):
        position = 0 if i == len(inputs) else i
        label = labels[position]
        require(vector["id"] == m["id"] == label["id"], "vector join")
        require(vector["input_ids"] == raw[position]["input_ids"], "vector native IDs")
        logits = vector["logits"]
        require(len(logits) == 259 and all(math.isfinite(v) for v in logits), "finite logits")
        gold = label["gold"].encode()[0] + 3
        order = sorted(range(2, 259), key=lambda j: (-logits[j], j))
        top, runner = order[:2]
        require(
            m["expected_first_id"] == gold and m["expected_rank"] == order.index(gold) + 1,
            "gold rank",
        )
        require(
            m["predicted_first_id"] == top == raw[position]["result"]["generated_ids"][0],
            "argmax parity",
        )
        require(
            m["expected_minus_predicted_margin"] == logits[gold] - logits[top]
            and m["winner_minus_runner_up"] == logits[top] - logits[runner],
            "saved margins",
        )
        require(max(m["cost"].values()) <= 2, "vector request cap")
        mx = max(logits)
        ce = math.log(sum(math.exp(v - mx) for v in logits)) + mx - logits[gold]
        if i < len(inputs):
            first_ces.append(ce)
            if top != gold:
                examples.append(
                    dict(
                        id=label["id"],
                        category=label["category"],
                        gold=label["gold"],
                        generated_ids=raw[i]["result"]["generated_ids"],
                        answer=raw[i]["result"]["answer"],
                        gold_rank=m["expected_rank"],
                        expected_first_id=gold,
                        predicted_first_id=top,
                        gold_minus_top=m["expected_minus_predicted_margin"],
                        prefix=inputs[i]["prefix"],
                    )
                )
    teacher = rows(directory / "teacher-losses.jsonl")
    require(len(teacher) == len(inputs), "loss count")
    totals: Counter[str] = Counter()
    for t, case in zip(teacher, inputs, strict=True):
        require(t["id"] == case["id"] and max(t["cost"].values()) <= 2, "teacher loss identity/cap")
        totals.update(
            {
                k: t[k]
                for k in (
                    "history_loss",
                    "answer_loss",
                    "first_loss",
                    "history_targets",
                    "answer_targets",
                    "first_targets",
                )
            }
        )
    full = (totals["history_loss"] + totals["answer_loss"]) / (
        totals["history_targets"] + totals["answer_targets"]
    )
    require(math.isclose(stored["full_nll"], full, rel_tol=1e-12), "full NLL")
    require(
        math.isclose(
            stored["answer_nll"], totals["answer_loss"] / totals["answer_targets"], rel_tol=1e-12
        ),
        "answer NLL",
    )
    require(
        math.isclose(
            stored["first_nll"], totals["first_loss"] / totals["first_targets"], rel_tol=1e-12
        ),
        "first NLL",
    )
    if split == "dev":
        qraw = rows(directory / "predictions-question-only.jsonl")
        q = scores(qraw, inputs, labels, question=True)
        require(q == read(directory / "question-only-metrics.json"), "question-only outcomes")
        gain = sum(actual["categories"][k] - q["categories"][k] for k in ("city", "code"))
        require(
            gain == stored["known_context_gain"] and floor(stored) == stored["development_floor"],
            "development gate",
        )
    return dict(
        metrics=stored,
        wrong_first_examples=examples,
        teacher_prefix_ce_max_difference=max(
            abs(c - t["first_loss"]) for c, t in zip(first_ces, teacher, strict=True)
        ),
        model_generation_positions=sum(p["result"]["forward_positions"] for p in raw),
        requests=len(raw),
        vectors=len(vectors),
    )


def closed_cost(directory, cap, memory, disk):
    cost = read(directory / "cost.json")
    require(
        cost["complete_process_lifetimes"] and cost["active_processes"] == 0,
        "complete Job lifetime",
    )
    require(cost["cpu"] == cost["user_cpu"] + cost["kernel_cpu"], "kernel CPU arithmetic")
    require(
        max(cost["cpu"], cost["wall"]) <= cap
        and cost["peak_private"] <= memory
        and cost["peak_disk"] <= disk
        and cost["max_monitor_gap"] <= 5,
        "resource cap",
    )
    monitor = rows(directory / "resources.jsonl")
    require(
        monitor[-1]["active"] == 0 and max(r["job_cpu"] for r in monitor) <= cost["cpu"],
        "final monitor CPU/process closure",
    )
    require(
        max(r["peak_private"] for r in monitor) <= cost["peak_private"]
        and max(r["elapsed"] for r in monitor) <= cost["wall"],
        "monitor/final receipt bounds",
    )
    require(cost["status"] == "PASS", "workload STOP retained")
    return cost


def audit():
    plan = read(RUN / "plan-final.json")
    reg = read(RUN / "registration.json")
    require(reg["plan_sha256"] == sha(RUN / "plan-final.json"), "plan identity")
    for name, digest in plan["sources"].items():
        require(
            sha(ROOT / name) == sha(RUN / "sources-final" / name) == digest,
            "frozen source: " + name,
        )
    for name, digest in plan["data"].items():
        require(sha(RUN / name) == digest, "frozen data: " + name)
    for name, digest in reg["prerequisite_files"].items():
        require(sha(RUN / name) == digest, "prerequisite: " + name)
    for receipt in reg["prerequisite_seals"]:
        verify_seal(RUN / receipt["path"], expected_seal_sha256=receipt["sha256"])
    before = read(RUN / "preservation-before.json")
    require(sha(RUN / "preservation-before.json") == plan["preservation_sha256"], "baseline")
    for name, meta in before["files"].items():
        require(
            (ROOT / name).stat().st_size == meta["bytes"] and sha(ROOT / name) == meta["sha256"],
            "v1 preservation",
        )
    require(
        read(RUN / "precondition.json")["decision"] == "STOP_DEVELOPMENT_FAILURE",
        "negative v1 preserved",
    )
    overlap = read(RUN / "overlap.json")
    require(
        overlap["pass_overlap"]
        and overlap["dev_overlap_train"] == overlap["dev_overlap_v1_and_known"] == 0,
        "overlap gate",
    )
    require(sha(RUN / "overlap.json") == plan["overlap_sha256"], "frozen overlap receipt")
    execution = RUN / "registered/execution"
    costs = {}
    for path, cap in (
        ("preparation/contracts", 60),
        ("preparation/rehearsal", 45),
        ("preparation/budget", 150),
        ("registered/execution", 1800),
        ("registered/budget", 1800),
    ):
        costs[path] = closed_cost(RUN / path, cap, reg["caps"]["memory"], reg["caps"]["disk"])
    for name in ("execution-receipt.json", "registered-budget-receipt.json"):
        receipt = read(RUN / name)
        verify_seal(RUN / receipt["path"], expected_seal_sha256=receipt["sha256"])
    require(
        read(RUN / "attempt-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
        "attempt",
    )
    axes = plan["crossed_seeds"]
    require(
        {tuple(v.values()) for v in axes.values()}
        == {(601, 1301), (601, 1709), (947, 1301), (947, 1709)},
        "full crossed axes",
    )
    schedules = read(RUN / "schedules.json")
    for left in axes:
        for right in axes:
            require(
                (schedules[left] == schedules[right])
                == (axes[left]["shuffle"] == axes[right]["shuffle"]),
                "shuffle independent of initialization",
            )
    documents = {r["id"]: r for r in read(RUN / "train-documents.json")}
    ledger = rows(execution / "stages.jsonl")
    expected = []
    training, development, cells = {}, {}, {}
    initialization: dict[str, str] = {}
    trace_rows = 0
    for seed, model, arm in plan["order"]:
        key = f"{seed}-{model}-{arm}"
        cells[key] = dict(
            initialization_seed=axes[seed]["initialization"],
            shuffle_seed=axes[seed]["shuffle"],
            model=model,
            objective=arm,
        )
        for kind in ("fit", "evaluate"):
            stage = f"{kind}-{key}"
            expected.append(stage)
            receipt = next(r for r in ledger if r["stage"] == stage)
            directory = execution / receipt["path"]
            verify_seal(directory, expected_seal_sha256=receipt["seal_sha256"])
            cost = closed_cost(
                directory, reg["caps"][kind], reg["caps"]["memory"], reg["caps"]["disk"]
            )
            costs[stage] = cost
            cells[key][kind + "_cost"] = cost
            if kind == "evaluate":
                observation = verify_observation(directory, "train")
                cells[key]["training"] = observation
                training[key] = observation["metrics"]
                continue
            meta = read(directory / "checkpoint-meta.json")
            require(
                sha(directory / "checkpoint.pt") == meta["sha256"]
                and (directory / "checkpoint.pt").stat().st_size == meta["bytes"],
                "checkpoint identity",
            )
            cells[key]["checkpoint"] = meta
            trace = rows(directory / "training.jsonl")
            require(len(trace) == 1536, "fixed updates")
            exposure: Counter[str] = Counter()
            weighted = 0
            for row, batch in zip(trace, schedules[seed], strict=True):
                require(all(row[k] == v for k, v in batch.items()), "exact frozen batch schedule")
                require(
                    row["forward_positions"] == 512 and row["first_targets"] == 8, "matched work"
                )
                nt = sum(len(documents[i]["text"].encode()) + 1 for i in row["ids"])
                na = sum(len(documents[i]["gold"].encode()) + 1 for i in row["ids"])
                require(
                    row["history_targets"] + row["answer_targets"] == nt
                    and row["answer_targets"] == na,
                    "actual target counts",
                )
                extra = 15 if arm == "first16" else 0
                require(row["weighted_denominator"] == nt + extra * 8, "target weights")
                reconstructed = (
                    row["history_loss"] + row["answer_loss"] + extra * row["first_loss"]
                ) / (nt + extra * 8)
                require(
                    math.isclose(reconstructed, row["objective"], rel_tol=1e-6)
                    and math.isfinite(row["gradient_norm"]),
                    "finite weighted objective",
                )
                exposure.update(row["ids"])
                weighted += row["weighted_denominator"]
            require(exposure == Counter({i: 128 for i in documents}), "matched presentations")
            require(weighted == (876544 if extra else 692224), "weighted total")
            stats = read(directory / "training-summary.json")
            require(
                stats["steps"] == 1536
                and stats["targets"] == 692224
                and stats["forward_positions"] == 786432,
                "fit totals",
            )
            initial_key = f"{axes[seed]['initialization']}-{model}"
            require(
                stats["initial_sha256"]
                == plan["initial_hashes"][f"{seed}-{model}"]
                == initialization.setdefault(initial_key, stats["initial_sha256"]),
                "initialization independent of shuffle/objective",
            )
            trace_rows += len(trace)
    require(len(training) == 16, "all sixteen cells")
    candidate_mastery = all(mastery(m) for k, m in training.items() if k.endswith("-first16"))
    controls_floor = all(
        m["exact"] >= 90 and m["eos"] == 96 and not m["malformed"] and not m["repetition"]
        for k, m in training.items()
        if k.endswith("-uniform")
    )
    gate = candidate_mastery and controls_floor
    summary = read(execution / "summary.json")
    require(
        training == summary["training"]
        and gate == summary["training_gate"] == read(execution / "training-gate.json")["pass_gate"],
        "training gate",
    )
    if gate:
        for seed, model, arm in plan["order"]:
            key = f"{seed}-{model}-{arm}"
            stage = "development-" + key
            expected.append(stage)
            receipt = next(r for r in ledger if r["stage"] == stage)
            directory = execution / receipt["path"]
            verify_seal(directory, expected_seal_sha256=receipt["seal_sha256"])
            cost = closed_cost(
                directory, reg["caps"]["development"], reg["caps"]["memory"], reg["caps"]["disk"]
            )
            costs[stage] = cost
            observation = verify_observation(directory, "dev")
            development[key] = observation["metrics"]
            cells[key]["development"] = observation
            cells[key]["development_cost"] = cost
    else:
        require(not list((execution / "stages").glob("development-*")), "closed development gate")
    require([r["stage"] for r in ledger] == expected, "single registered order; no extra attempts")
    require(
        development == summary["development"]
        and bool(development) == summary["development_evaluated"],
        "development occurrence",
    )
    pair_gains = {}
    floors = no_regression = False
    improved = False
    if development:
        floors = all(floor(m) for k, m in development.items() if k.endswith("-first16"))
        no_regression = True
        for seed in axes:
            for model in ("ordinary", "recurrent"):
                c, u = (development[f"{seed}-{model}-{arm}"] for arm in ("first16", "uniform"))
                pair_gains[f"{seed}-{model}"] = c["exact"] - u["exact"]
                no_regression &= c["eos"] >= u["eos"] and all(
                    c["categories"][k] >= u["categories"][k] for k in ("city", "code", "unknown")
                )
        improved = floors and no_regression and all(gain > 0 for gain in pair_gains.values())
        comparison = summary["comparison"]
        require(
            comparison["candidate_floors"] == floors
            and comparison["no_regression"] == no_regression
            and comparison["pair_exact_gains"] == pair_gains
            and comparison["improved"] == improved,
            "independent development gates",
        )
    require(not summary["comparison"]["memory_study_justified"], "no memory attribution")
    decision = (
        "STOP_TRAINING_FAILURE"
        if not gate
        else "REPLICATION_GATES_PASS"
        if improved
        else "STOP_DEVELOPMENT_FAILURE"
    )
    require(summary["decision"] == decision, "negative/positive decision")
    return dict(
        status="PASS",
        measurement_integrity="PASS",
        decision=decision,
        candidate_training_mastery=candidate_mastery,
        controls_eligibility=controls_floor,
        training_gate=gate,
        development_evaluated=bool(development),
        consistent_objective_improvement=improved,
        per_pair_dev_gains=pair_gains,
        cells=cells,
        costs=costs,
        optimizer_steps_verified=trace_rows,
        formal_scientific_stage_seals=len(ledger),
        original_v1_files_unchanged=len(before["files"]),
        registration_sha256=sha(RUN / "registration.json"),
        plan_sha256=sha(RUN / "plan-final.json"),
        new_audit_model_forwards=0,
        heldout_evaluated=False,
        memory_advantage=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit()
    except BaseException as error:
        blocked = RUN / "audit-BLOCKED.json"
        if not blocked.exists():
            with blocked.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(
                    dict(status="BLOCKED", error=repr(error), sealed_evidence_repaired=False),
                    stream,
                    indent=2,
                )
                stream.write("\n")
        raise
    if args.output:
        require(
            args.output.resolve().is_relative_to(RUN)
            and not args.output.resolve().is_relative_to(RUN / "registered"),
            "audit outside sealed execution",
        )
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("cells", "costs")}, indent=2))


if __name__ == "__main__":
    main()
