"""Independent saved-only verification of the value-start study. No model imports/forwards."""

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job_v2 import verify_seal

VALUES = ("la", "mi", "so", "tu", "R-7", "Q_2", "V:4", "Z!6", "?")
ARMS = ("uniform", "first16")


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
    counts = Counter()
    categories = Counter()
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
    totals = Counter()
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
    plan = read(RUN / "plan.json")
    reg = read(RUN / "registration.json")
    require(reg["plan_sha256"] == sha(RUN / "plan.json"), "plan binding")
    for name, h in plan["sources"].items():
        require(sha(ROOT / name) == sha(RUN / "sources" / name) == h, "frozen source: " + name)
    for name, h in plan["data"].items():
        require(sha(RUN / name) == h, "frozen data: " + name)
    for name, h in reg["prerequisite_files"].items():
        require(sha(RUN / name) == h, "prerequisite bytes")
    for receipt in reg["prerequisite_seals"]:
        verify_seal(RUN / receipt["path"], expected_seal_sha256=receipt["sha256"])
    supplement_hash = "202428c1772e614c9bc5a5656ebea065a472dc65236060e8a1052c6f1060a52c"
    verify_seal(RUN / "diagnosis-supplement-execution", expected_seal_sha256=supplement_hash)
    before = read(RUN / "preservation-before.json")
    require(
        sha(RUN / "preservation-before.json") == plan["preservation_sha256"],
        "preservation baseline",
    )
    for name, m in before["files"].items():
        p = ROOT / name
        require(
            p.stat().st_size == m["bytes"] and sha(p) == m["sha256"],
            "original file changed: " + name,
        )
    original = read(ROOT / "artifacts/local-answer-paired-batch-dev-v1/artifact-inventory.json")
    for name, m in original["files"].items():
        require(
            sha(ROOT / name) == m["sha256"] and (ROOT / name).stat().st_size == m["bytes"],
            "v1 changed",
        )
    budget_receipt = read(RUN / "registered-budget-receipt.json")
    verify_seal(RUN / "registered/budget", expected_seal_sha256=budget_receipt["sha256"])
    execution_receipt = read(RUN / "execution-receipt.json")
    execution = RUN / "registered/execution"
    rootseal = verify_seal(execution, expected_seal_sha256=execution_receipt["sha256"])
    require(
        read(RUN / "attempt-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
        "one attempt",
    )
    caps = reg["caps"]
    all_costs = {}
    for path, cap in (
        ("phase1-tests", 60),
        ("diagnosis-execution", 45),
        ("diagnosis-supplement-execution", 30),
        ("preparation/contracts", 60),
        ("preparation/rehearsal", 45),
        ("preparation/budget", 150),
        ("registered/execution", caps["overall"]),
        ("registered/budget", caps["overall"]),
    ):
        all_costs[path] = closed_cost(RUN / path, cap, caps["memory"], caps["disk"])
    require(
        read(RUN / "preparation/rehearsal/rehearsal.json")["optimizer_updates"] == 0,
        "zero-update rehearsal",
    )
    ledger = rows(execution / "stages.jsonl")
    expected = [
        (kind, seed, variant, arm)
        for seed, variant, arm in plan["order"]
        for kind in ("fit", "evaluate")
    ]
    datasets = read(RUN / "train-documents.json")
    docs = {d["id"]: d for d in datasets}
    schedules = read(RUN / "schedules.json")
    training = {}
    development = {}
    cells = {}
    trace_rows = 0
    for kind, seed, variant, arm in expected:
        name = f"{kind}-{seed}-{variant}-{arm}"
        receipt = next(r for r in ledger if r["stage"] == name)
        directory = execution / receipt["path"]
        verify_seal(directory, expected_seal_sha256=receipt["seal_sha256"])
        cost = closed_cost(directory, caps[kind], caps["memory"], caps["disk"])
        all_costs["registered/execution/" + receipt["path"]] = cost
        key = f"{seed}-{variant}-{arm}"
        if kind == "fit":
            meta = read(directory / "checkpoint-meta.json")
            require(
                sha(directory / "checkpoint.pt") == meta["sha256"]
                and (directory / "checkpoint.pt").stat().st_size == meta["bytes"],
                "checkpoint hash/bytes",
            )
            trace = rows(directory / "training.jsonl")
            batches = schedules[str(seed)]
            require(len(trace) == 1536, "fixed optimizer steps")
            exposures = Counter()
            weighted_total = 0
            for t, b in zip(trace, batches, strict=True):
                require(all(t[k] == v for k, v in b.items()), "frozen schedule row")
                require(t["forward_positions"] == 512, "matched dense work")
                nt = sum(len(docs[i]["text"].encode()) + 1 for i in t["ids"])
                na = sum(len(docs[i]["gold"].encode()) + 1 for i in t["ids"])
                require(
                    t["history_targets"] + t["answer_targets"] == nt
                    and t["answer_targets"] == na
                    and t["first_targets"] == 8,
                    "target partitions",
                )
                extra = 0 if arm == "uniform" else 15
                require(t["weighted_denominator"] == nt + extra * 8, "objective mass")
                reconstructed = (t["history_loss"] + t["answer_loss"] + extra * t["first_loss"]) / (
                    nt + extra * 8
                )
                require(math.isclose(t["objective"], reconstructed, rel_tol=1e-6), "weighted CE")
                require(math.isfinite(t["gradient_norm"]), "finite gradient")
                exposures.update(t["ids"])
                weighted_total += t["weighted_denominator"]
            require(exposures == Counter({i: 128 for i in docs}), "matched exposure")
            require(
                weighted_total == (692224 if arm == "uniform" else 876544), "weighted target total"
            )
            stats = read(directory / "training-summary.json")
            require(
                stats["steps"] == 1536
                and stats["targets"] == 692224
                and stats["forward_positions"] == 786432,
                "fit totals",
            )
            require(
                stats["initial_sha256"] == plan["initial_hashes"][f"{seed}-{variant}"],
                "fresh initialization",
            )
            cells[key] = dict(
                seed=seed,
                model=variant,
                arm=arm,
                fit_cpu=cost["cpu"],
                fit_wall=cost["wall"],
                checkpoint=meta,
                weighted_target_mass=weighted_total,
            )
            trace_rows += len(trace)
        else:
            observed = verify_observation(directory, "train")
            cells[key]["training"] = observed
            cells[key]["training_cpu"] = cost["cpu"]
            cells[key]["training_wall"] = cost["wall"]
            training[key] = observed["metrics"]

    expected_keys = {f"{s}-{v}-{a}" for s, v, a in plan["order"]}
    require(set(training) == expected_keys, "complete training cells")
    candidate_mastery = all(mastery(m) for k, m in training.items() if k.endswith("-first16"))
    controls_floor = all(
        m["exact"] >= 90 and m["eos"] == 96 and not m["malformed"] and not m["repetition"]
        for k, m in training.items()
        if k.endswith("-uniform")
    )
    gate = candidate_mastery and controls_floor
    summary = read(execution / "summary.json")
    require(
        training == summary["training"] and gate == summary["training_gate"],
        "training gate decision",
    )
    require(read(execution / "training-gate.json")["pass_gate"] == gate, "gate file")
    if gate:
        for seed, variant, arm in plan["order"]:
            key = f"{seed}-{variant}-{arm}"
            name = "development-" + key
            receipt = next(r for r in ledger if r["stage"] == name)
            directory = execution / receipt["path"]
            verify_seal(directory, expected_seal_sha256=receipt["seal_sha256"])
            cost = closed_cost(directory, caps["development"], caps["memory"], caps["disk"])
            all_costs["registered/execution/" + receipt["path"]] = cost
            observed = verify_observation(directory, "dev")
            development[key] = observed["metrics"]
            cells[key]["development"] = observed
            cells[key]["development_cpu"] = cost["cpu"]
            cells[key]["development_wall"] = cost["wall"]
    else:
        require(not list((execution / "stages").glob("development-*")), "development forbidden")
    require(
        development == summary["development"]
        and bool(development) == summary["development_evaluated"],
        "development occurrence",
    )
    expected_names = [f"{kind}-{s}-{v}-{a}" for kind, s, v, a in expected]
    if gate:
        expected_names += [f"development-{s}-{v}-{a}" for s, v, a in plan["order"]]
    require(
        [r["stage"] for r in ledger] == expected_names, "single fixed stage order; no extra fits"
    )
    target_gain = (
        training["947-ordinary-first16"]["exact"] - training["947-ordinary-uniform"]["exact"]
    )
    no_train_regression = all(
        training[f"{s}-{v}-first16"]["exact"] >= training[f"{s}-{v}-uniform"]["exact"]
        for s in (601, 947)
        for v in ("ordinary", "recurrent")
    )
    require(
        summary["training_improvement"]
        == (candidate_mastery and target_gain > 0 and no_train_regression),
        "training improvement decision",
    )
    dev_floors = False
    no_regression = False
    known_gains = {}
    memory_ready = False
    if development:
        dev_floors = all(floor(m) for k, m in development.items() if k.endswith("-first16"))
        no_regression = all(
            development[f"{s}-{v}-first16"]["exact"] >= development[f"{s}-{v}-uniform"]["exact"]
            and development[f"{s}-{v}-first16"]["eos"] >= development[f"{s}-{v}-uniform"]["eos"]
            for s in (601, 947)
            for v in ("ordinary", "recurrent")
        )
        known_gains = {
            c: sum(
                development[f"{s}-{v}-first16"]["categories"][c]
                - development[f"{s}-{v}-uniform"]["categories"][c]
                for s in (601, 947)
                for v in ("ordinary", "recurrent")
            )
            for c in ("city", "code")
        }
        comp = summary["comparison"]
        require(
            comp["candidate_floors"] == dev_floors
            and comp["no_regression"] == no_regression
            and comp["known_category_gains"] == known_gains,
            "development comparison",
        )
        memory_ready = dev_floors and no_regression
        require(
            comp["memory_study_justified"] == memory_ready
            and comp["improved"] == (memory_ready and sum(known_gains.values()) > 0),
            "development gates",
        )
    decision = (
        "STOP_TRAINING_FAILURE"
        if not gate
        else "LOCAL_ANSWER_DEVELOPMENT_GATES_PASS"
        if memory_ready
        else "STOP_DEVELOPMENT_FAILURE"
    )
    require(summary["decision"] == decision, "finite stop decision")
    independent_scopes = (
        "phase1-tests",
        "diagnosis-execution",
        "diagnosis-supplement-execution",
        "preparation/budget",
        "registered/budget",
    )
    aggregate_cpu = sum(all_costs[k]["cpu"] for k in independent_scopes)
    aggregate_wall = sum(all_costs[k]["wall"] for k in independent_scopes)
    require(
        all_costs["registered/budget"]["cpu"] >= all_costs["registered/execution"]["cpu"],
        "outer complete cost includes root observer and sealing",
    )
    return dict(
        status="PASS_SEALED_EXECUTION_AND_INDEPENDENT_RESCORING",
        measurement_integrity="PASS",
        decision=decision,
        training_gate=gate,
        candidate_training_mastery=candidate_mastery,
        controls_eligibility=controls_floor,
        training_improved=summary["training_improvement"],
        target_training_gain=target_gain,
        development_evaluated=bool(development),
        candidate_development_floors=dev_floors,
        no_development_regression=no_regression,
        development_known_gains=known_gains,
        generalizable_improvement=bool(development)
        and memory_ready
        and sum(known_gains.values()) > 0,
        memory_study_justified=memory_ready,
        cells=cells,
        costs=all_costs,
        nonoverlapping_cost_scopes=list(independent_scopes),
        measured_nonoverlapping_cpu=aggregate_cpu,
        measured_nonoverlapping_wall=aggregate_wall,
        cost_limit="Named complete worker Jobs only; outermost observers and editing/typing/reporting outside Jobs are not complete project cost.",
        saved_training_answers=8 * 96,
        saved_development_answers=8 * 24 if gate else 0,
        saved_question_only_answers=8 * 24 if gate else 0,
        optimizer_updates_verified=trace_rows,
        formal_scientific_stage_seals=len(ledger),
        root_execution_seal_verified=True,
        preserved_files=len(before["files"]),
        preserved_ignored_checkpoints=before["ignored_checkpoints"],
        original_paired_batch_files_unchanged=len(original["files"]),
        v1_registered_integrity="FAIL unchanged",
        phase1_v2_ready=True,
        registration_sha256=sha(RUN / "registration.json"),
        plan_sha256=sha(RUN / "plan.json"),
        source_commit=plan["source_commit"],
        scope_exception=read(RUN / "search-scope-incident.json"),
        unrelated_artifact_reads_cannot_be_certified_zero=True,
        experimental_heldout_inputs_used=False,
        heldout_evaluation_run=False,
        external_answer_provider_used=False,
        new_model_forwards=0,
        new_generated_answers=0,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        require(args.output.resolve().is_relative_to(RUN), "new artifact output only")
        require(
            not args.output.resolve().is_relative_to(RUN / "registered"),
            "never write inside sealed science",
        )
        with args.output.open("x", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
            f.write("\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("cells", "costs", "scope_exception")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
