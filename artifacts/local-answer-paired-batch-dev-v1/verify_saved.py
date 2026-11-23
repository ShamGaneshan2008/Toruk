"""Independent saved-output verification. Reports the frozen live-monitor seal defect explicitly."""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
ARMS = ("original", "city-shuffled", "city-paired")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mastery(m):
    return (
        m["exact"] == 96
        and m["eos"] == 96
        and m["malformed"] == 0
        and m["repetitive"] == 0
        and m["city_first_errors"] == 0
        and m["city_near_ties"] == 0
    )


def audit():
    plan = read(RUN / "plan.json")
    registration = read(RUN / "registration.json")
    require(registration["plan_sha256"] == sha(RUN / "plan.json"), "plan binding")
    require(
        read(RUN / "run-start.json")["registration_sha256"] == sha(RUN / "registration.json"),
        "registration binding",
    )
    for name, expected in plan["sources"].items():
        require(sha(ROOT / name) == sha(RUN / "sources" / name) == expected, "source: " + name)
    for name, expected in plan["data"].items():
        require(sha(RUN / name) == expected, "data: " + name)
    for name, expected in registration["prerequisites"].items():
        require(sha(RUN / name) == expected, "prerequisite: " + name)
    preservation = read(RUN / "preservation-before.json")
    require(
        sha(RUN / "preservation-before.json") == plan["preservation_sha256"], "preservation seal"
    )
    for name, meta in preservation["files"].items():
        require(
            (ROOT / name).stat().st_size == meta["bytes"] and sha(ROOT / name) == meta["sha256"],
            "old evidence/handoff changed: " + name,
        )
    summary = read(RUN / "summary.json")
    schedules = read(RUN / "batch-schedules.json")
    documents = {d["id"]: d for d in read(RUN / "train-documents.json")}
    inputs = read(RUN / "train-inputs.json")
    labels = read(RUN / "train-labels.json")
    known = ("la", "mi", "so", "tu", "R-7", "Q_2", "V:4", "Z!6", "?")
    closed = {tuple([*(b + 3 for b in s.encode()), 2]) for s in known}
    defects, costs, cells = [], {}, {}
    scientific_bindings = 0
    for base in [
        RUN / "execution",
        RUN / "preparation/contracts",
        RUN / "preparation/rehearsal",
        *sorted((RUN / "stages").iterdir()),
    ]:
        c = read(base / "cost.json")
        require(
            c["status"] == "PASS"
            and c["complete_process_lifetimes"]
            and c["active_processes"] == 0,
            "Job closure: " + str(base),
        )
        require(c["cpu"] == c["user_cpu"] + c["kernel_cpu"], "CPU accounting")
        cap = (
            plan["caps"]["overall"]
            if base.name == "execution"
            else plan["caps"]["contracts"]
            if base.name == "contracts"
            else plan["caps"]["rehearsal"]
            if base.name == "rehearsal"
            else plan["caps"]["fit"]
            if base.name.startswith("fit-")
            else plan["caps"]["analyze"]
        )
        require(
            max(c["cpu"], c["wall"]) <= cap
            and c["peak_private"] <= plan["caps"]["memory"]
            and c["peak_disk"] <= plan["caps"]["disk"]
            and c["max_monitor_gap"] <= 5,
            "resource cap: " + str(base),
        )
        monitor = rows(base / "resources.jsonl")
        require(
            monitor[-1]["active"] == 0 and max(r["job_cpu"] for r in monitor) <= c["cpu"],
            "final monitored CPU/exit",
        )
        final = read(
            base
            / ("contracts-result.json" if base.name == "contracts" else "controller-final.json")
        )
        require(final["status"] == "PASS", "controller diagnostic result")
        costs[base.relative_to(RUN).as_posix()] = c

    for seed, variant, arm in plan["order"]:
        identity = f"{seed}-{variant}-{arm}"
        fit = RUN / "stages" / f"fit-{identity}"
        analysis = RUN / "stages" / f"analyze-{identity}"
        trace = rows(fit / "training.jsonl")
        batches = schedules[f"{seed}-{arm}"]
        require(len(trace) == len(batches) == 1536, "training steps")
        exposure = Counter()
        for t, b in zip(trace, batches, strict=True):
            require(all(t[k] == b[k] for k in b), "exact frozen schedule")
            exposure.update(t["ids"])
            require(t["forward_positions"] == t["padded_forward_positions"] == 512, "dense work")
            require(
                t["history_targets"] + t["answer_targets"]
                == sum(len(documents[i]["text"].encode()) + 1 for i in t["ids"]),
                "target work",
            )
            require(
                math.isfinite(t["gradient_norm"])
                and math.isclose(
                    t["objective"],
                    (t["history_loss"] + t["answer_loss"])
                    / (t["history_targets"] + t["answer_targets"]),
                    rel_tol=1e-6,
                ),
                "uniform finite CE",
            )
        require(exposure == Counter({i: 128 for i in documents}), "all exposures")
        train = read(fit / "training-summary.json")
        require(
            train["initial_sha256"] == plan["initial_hashes"][f"{seed}-{variant}"],
            "initialization identity",
        )
        require(train["targets"] == 692224 and train["forward_positions"] == 786432, "fit totals")
        meta = read(fit / "checkpoint-meta.json")
        require(
            (fit / "checkpoint.pt").stat().st_size == meta["bytes"]
            and sha(fit / "checkpoint.pt") == meta["sha256"],
            "checkpoint identity",
        )

        for name, expected in read(analysis / "observation-seal.json").items():
            actual = sha(analysis / name)
            if actual == expected:
                scientific_bindings += 1
                continue
            require(name == "resources.jsonl", "unexpected scientific payload mismatch: " + name)
            raw = (analysis / name).read_bytes()
            digest = hashlib.sha256()
            prefix = None
            for number, line in enumerate(raw.splitlines(keepends=True), 1):
                digest.update(line)
                if digest.hexdigest() == expected:
                    prefix = number
                    break
            require(
                prefix is not None and prefix < len(raw.splitlines()),
                "monitor drift is not proved as append-only continuation",
            )
            defects.append(
                dict(
                    cell=identity,
                    file=name,
                    recorded_sha256=expected,
                    final_sha256=actual,
                    matching_prefix_lines=prefix,
                    final_lines=len(raw.splitlines()),
                    diagnosis="sealed exact line prefix; observer appended after worker seal",
                )
            )

        raw = rows(analysis / "predictions-main.jsonl")
        require(
            len(raw) == 97 and raw[-1]["replay"] and raw[0]["result"] == raw[-1]["result"],
            "raw generation count/replay",
        )
        require(
            sha(analysis / "predictions-main.jsonl") == read(analysis / "seal-main.json")["sha256"],
            "generation seal",
        )
        totals = Counter()
        by_category = Counter()
        by_template = Counter()
        cases = []
        for p, case, label in zip(raw[:-1], inputs, labels, strict=True):
            require(
                p["id"] == case["id"] == label["id"] and p["prefix"] == case["prefix"],
                "native case identity",
            )
            require(p["input_ids"] == [1, *(b + 3 for b in case["prefix"].encode())], "native IDs")
            ids = p["result"]["generated_ids"]
            gold = [*(b + 3 for b in label["gold"].encode()), 2]
            correct = ids == gold
            eos = bool(ids and ids[-1] == 2)
            malformed = tuple(ids) not in closed
            repetitive = any(
                ids[i : i + w] * 3 == ids[i : i + 3 * w]
                for w in (1, 2)
                for i in range(len(ids) - 3 * w + 1)
            )
            first_error = ids[0] != gold[0]
            totals.update(
                dict(
                    exact=int(correct),
                    eos=int(eos),
                    malformed=int(malformed),
                    repetitive=int(repetitive),
                    first_token_errors_all=int(first_error),
                )
            )
            by_category[label["category"]] += int(correct)
            by_template[label["template"]] += int(correct)
            require(max(p["cost"].values()) <= 2 and len(ids) <= 8, "generation cap")
            cases.append(
                dict(
                    id=case["id"],
                    correct=correct,
                    first_error=first_error,
                    expected_first_id=gold[0],
                    actual_first_id=ids[0],
                    answer=p["result"]["answer"],
                    gold=label["gold"],
                )
            )
        m = read(analysis / "metrics.json")
        require(all(m[k] == v for k, v in totals.items()), "independent exact/EOS/raw scores")
        require(
            m["categories"] == dict(by_category) and m["templates"] == dict(by_template),
            "category/template scores",
        )
        require(m == summary["results"][identity], "summary metric binding")
        teacher = rows(analysis / "teacher-losses.jsonl")
        require(len(teacher) == 96, "teacher-loss count")
        losses = Counter()
        for t, case in zip(teacher, inputs, strict=True):
            require(t["id"] == case["id"] and max(t["cost"].values()) <= 2, "loss identity/cap")
            losses.update(
                {
                    k: t[k]
                    for k in ("history_loss", "answer_loss", "history_targets", "answer_targets")
                }
            )
        require(
            math.isclose(
                m["full_nll"],
                (losses["history_loss"] + losses["answer_loss"])
                / (losses["history_targets"] + losses["answer_targets"]),
                rel_tol=1e-12,
            ),
            "NLL arithmetic",
        )
        city = rows(analysis / "city-first-token.jsonl")
        vector_raw = rows(analysis / "city-raw-vectors.jsonl")
        require(len(city) == len(vector_raw) == 32, "city vector count")
        first_errors = 0
        near_ties = 0
        labelmap = {l["id"]: l for l in labels}
        by_id = {c["id"]: c for c in cases}
        for r, v in zip(city, vector_raw, strict=True):
            require(
                r["id"] == v["id"]
                and r["input_ids"] == v["input_ids"]
                and r["logits"] == v["logits"],
                "raw/derived city vectors",
            )
            logits = r["logits"]
            require(len(logits) == 259 and all(math.isfinite(x) for x in logits), "finite logits")
            gold = labelmap[r["id"]]["gold"].encode()[0] + 3
            order = sorted(range(2, 259), key=lambda i: (-logits[i], i))
            top, runner = order[:2]
            require(
                r["expected_first_id"] == gold
                and r["expected_rank"] == order.index(gold) + 1
                and r["predicted_first_id"] == top == by_id[r["id"]]["actual_first_id"],
                "rank/argmax parity",
            )
            require(
                r["expected_minus_predicted_margin"] == logits[gold] - logits[top]
                and r["winner_minus_runner_up"] == logits[top] - logits[runner],
                "margins",
            )
            require(max(r["cost"].values()) <= 2, "vector cap")
            first_errors += top != gold
            near_ties += logits[top] - logits[runner] <= 1e-4
        require(
            m["city_first_errors"] == first_errors and m["city_near_ties"] == near_ties,
            "city counts",
        )
        fitcost, analysiscost = costs[f"stages/fit-{identity}"], costs[f"stages/analyze-{identity}"]
        cells[identity] = dict(
            seed=seed,
            model=variant,
            arm=arm,
            metrics=m,
            cases=cases,
            wrong_first=[r for r in city if r["expected_rank"] != 1],
            complete_fit_cpu=fitcost["cpu"],
            complete_fit_wall=fitcost["wall"],
            complete_analysis_cpu=analysiscost["cpu"],
            complete_analysis_wall=analysiscost["wall"],
            checkpoint=meta,
            training_mastery=mastery(m),
        )
    gates = {name: c["training_mastery"] for name, c in cells.items()}
    require(
        gates == summary["training_gates"] and all(gates.values()) == summary["training_gate"],
        "training gate",
    )
    require(
        not summary["training_gate"]
        and not summary["development_evaluated"]
        and not summary["development"],
        "registered development STOP",
    )
    require(not list((RUN / "stages").glob("development-*")), "no development outputs")
    require(
        summary["primary_verdict"] == "REJECT_PAIRED_SUFFICIENCY_AT_ORDINARY947"
        and not gates["947-ordinary-city-paired"],
        "prespecified target rejection",
    )
    require(len(defects) == 12, "all seal defects declared")
    comparisons = {}
    for arm in ("city-shuffled", "city-paired"):
        baseline = {c["id"]: c for c in cells["947-ordinary-original"]["cases"]}
        candidate = {c["id"]: c for c in cells[f"947-ordinary-{arm}"]["cases"]}
        fixed = [i for i in baseline if not baseline[i]["correct"] and candidate[i]["correct"]]
        regressed = [i for i in baseline if baseline[i]["correct"] and not candidate[i]["correct"]]
        comparisons[arm] = dict(
            fixed_original_failures=fixed,
            regressed_original_correct=regressed,
            net_exact_gain=len(fixed) - len(regressed),
        )
    outer = costs["execution"]
    return dict(
        status="OBSERVATIONS_VERIFIED_WITH_REGISTERED_SEAL_FAILURE",
        registered_integrity_gate="FAIL: frozen auditor rejects live-monitor final hashes",
        as_run_training_decision=summary["decision"],
        primary_verdict=summary["primary_verdict"],
        scientific_payload_hashes_verified=scientific_bindings,
        declared_seal_defects=defects,
        saved_answers_rescored=1152,
        replays_verified=12,
        city_vectors_verified=384,
        fits_verified=12,
        completed_optimizer_updates=18432,
        per_fit_targets=692224,
        per_fit_dense_positions=786432,
        development_evaluated=False,
        preserved_files=len(preservation["files"]),
        source_commit=plan["source_commit"],
        registration_sha256=sha(RUN / "registration.json"),
        plan_sha256=sha(RUN / "plan.json"),
        cells=cells,
        comparisons=comparisons,
        complete_execution_cost=outer,
        cpu_residual_including_preparation_and_controllers=outer["cpu"]
        - sum(c["complete_fit_cpu"] + c["complete_analysis_cpu"] for c in cells.values()),
        model_deserialization=False,
        new_forward_passes=0,
        new_answers=0,
        no_frozen_file_modified=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        require(args.output.resolve().is_relative_to(RUN), "new study output only")
        with args.output.open("x", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
            f.write("\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("cells", "declared_seal_defects", "comparisons")
            },
            indent=2,
        )
    )
    # This is deliberately not a full registered-integrity PASS.
    raise SystemExit(2)


if __name__ == "__main__":
    main()
