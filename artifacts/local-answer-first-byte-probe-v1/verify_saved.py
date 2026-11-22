"""Read-only, standard-library audit; never imports a model or executes a forward."""

import argparse
import hashlib
import json
import math
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
OLD = ROOT / "artifacts/local-answer-dev-v1"
REG_SHA = "b244089a172bf7933fe53ee1558b2e8ac1c393c03e837e22e884dee052863213"
CELLS = ("601-ordinary", "601-recurrent", "947-recurrent", "947-ordinary")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def native(text, eos=False):
    return [1, *(b + 3 for b in text.encode("utf-8")), *([2] if eos else [])]


def metrics(vector, gold):
    # Independent recomputation, no import of the registered implementation.
    order = sorted(range(2, 259), key=lambda token: (-vector[token], token))
    pred = order[0]
    margin = vector[pred] - vector[gold]
    full_max = max(vector)
    full_z = sum(math.exp(v - full_max) for v in vector)
    eligible_z = sum(math.exp(vector[i] - vector[pred]) for i in range(2, 259))
    return dict(
        expected_first_id=gold,
        predicted_first_id=pred,
        expected_rank=order.index(gold) + 1,
        expected_logit=vector[gold],
        predicted_logit=vector[pred],
        expected_minus_predicted_margin=-margin,
        predicted_minus_expected_margin=margin,
        expected_probability_full=math.exp(vector[gold] - full_max) / full_z,
        predicted_probability_full=math.exp(vector[pred] - full_max) / full_z,
        expected_probability_eligible=math.exp(vector[gold] - vector[pred]) / eligible_z,
        predicted_probability_eligible=1 / eligible_z,
        winner_minus_runner_up=vector[pred] - vector[order[1]],
        tied_winners=sum(vector[i] == vector[pred] for i in range(2, 259)),
        near_tied_gold=gold != pred and margin <= 1e-4,
        near_tied_decision=vector[pred] - vector[order[1]] <= 1e-4,
    )


def close(actual, expected):
    if isinstance(expected, float):
        return math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    return actual == expected


def lifetime(directory, seconds, reg):
    cost = read(directory / "cost.json")
    check(cost["status"] == "PASS" and cost["returncode"] == 0, "process status")
    check(cost["complete_process_lifetimes"] and cost["active_processes"] == 0, "complete lifetime")
    check(cost["error"] is None and cost["failure"] is None, "process error")
    check(cost["terminated_processes"] == 0, "terminated process")
    check(cost["cpu"] == cost["user_cpu"] + cost["kernel_cpu"], "kernel CPU sum")
    check(0 <= cost["cpu"] <= seconds and 0 < cost["wall"] <= seconds, "time cap")
    check(
        cost["peak_private"] <= reg["caps"]["memory"] and cost["peak_disk"] <= reg["caps"]["disk"],
        "memory/disk caps",
    )
    check(cost["max_monitor_gap"] <= 5, "observation gap")
    samples = lines(directory / "resources.jsonl")
    check(
        samples and all(a["elapsed"] <= b["elapsed"] for a, b in zip(samples, samples[1:])),
        "sample order",
    )
    return cost


def audit():
    reg = read(RUN / "registration.json")
    check(sha(RUN / "registration.json") == REG_SHA, "registration identity")
    check(read(RUN / "run-start.json")["registration_sha256"] == REG_SHA, "start seal")
    check(reg["order"] == list(CELLS) and reg["records"] == 260, "registered plan")
    for name, digest in reg["sources"].items():
        check(sha(ROOT / name) == sha(RUN / "sources" / name) == digest, "source: " + name)
    for name, digest in reg["data"].items():
        check(sha(RUN / name) == digest, "data: " + name)
    for name, digest in reg["original_evidence"].items():
        check(sha(OLD / name) == digest, "original: " + name)
    for meta in reg["checkpoints"].values():
        path = ROOT / meta["path"]
        check(
            sha(path) == meta["sha256"] and path.stat().st_size == meta["bytes"],
            "saved checkpoint bytes",
        )
    diagnosis = read(ROOT / "artifacts/local-answer-first-byte-v1/inventory.json")
    for name, item in diagnosis["files"].items():
        check(
            sha(ROOT / name) == item["sha256"] and (ROOT / name).stat().st_size == item["bytes"],
            "preserved diagnosis: " + name,
        )

    prefixes = read(RUN / "prefix-inputs.json")
    labels = read(RUN / "gold-evaluator.json")
    label_map = {r["id"]: r for r in labels}
    inputs = {r["id"]: r for r in read(OLD / "train-inputs.json")}
    old_labels = {r["id"]: r for r in read(OLD / "train-labels.json")}
    docs = {r["id"]: r for r in read(OLD / "train-documents.json")}
    check(len(prefixes) == len(labels) == 32, "city count")
    selected_ids = [r["id"] for r in old_labels.values() if r["category"] == "city"]
    check([r["id"] for r in prefixes] == selected_ids, "training city order")
    for case, label in zip(prefixes, labels, strict=True):
        identity = case["id"]
        check(label["id"] == identity and case["prefix"] == inputs[identity]["prefix"], "prefix")
        check(
            case["input_ids"] == native(case["prefix"]) and len(case["input_ids"]) == 54,
            "native prefix bytes",
        )
        check(case["delimiter_ids"] == case["input_ids"][-2:] == [66, 64], "delimiter")
        check(case["target_y"] == 53 and case["local_logit"] == 21, "causal target position")
        check(
            label["text"]
            == docs[identity]["text"]
            == case["prefix"] + old_labels[identity]["gold"],
            "full document bytes",
        )
        check(label["full_document_ids"] == native(label["text"], eos=True), "full native IDs")
        check(label["mask_positions"] == [53, 54, 55], "mask")
        targets = [*(b + 3 for b in old_labels[identity]["gold"].encode()), 2]
        check(label["answer_target_ids"] == label["full_document_ids"][54:] == targets, "targets")
        check(
            label["expected_first_id"] == targets[0] == label["expected_first_byte"] + 3,
            "gold first byte/token",
        )

    phase_seal = read(RUN / "prefix-phase-seal.json")
    check(phase_seal["records"] == 132, "prefix seal count")
    for name, digest in phase_seal["files"].items():
        check(sha(RUN / name) == digest, "prefix phase seal")
    original_ids = read(RUN / "original-first-ids.json")
    actual_plan = []
    vectors = {}
    costs = {}
    max_request = dict(cpu=0.0, wall=0.0)
    max_ce_difference = 0.0
    max_saved_suffix_difference = 0.0
    for phase in ("prefix", "teacher"):
        for cell in CELLS:
            directory = RUN / "stages" / f"{phase}-{cell}"
            costs[f"{phase}-{cell}"] = lifetime(directory, 20, reg)
            check(read(directory / "controller-final.json")["status"] == "PASS", "worker finally")
            inv = read(directory / "invariants.json")
            check(
                inv["unchanged"]
                and inv["before"] == inv["after"]
                and inv["before"]["gradient_fields_none"],
                "model/RNG/gradient invariants",
            )
            raw = lines(directory / "vectors.jsonl")
            count = 33 if phase == "prefix" else 32
            check(len(raw) == count, "vector count")
            seal = read(directory / "seal.json")
            check(
                seal["records"] == count and seal["vectors"] == sha(directory / "vectors.jsonl"),
                "vector seal",
            )
            request_costs = lines(directory / "request-costs.jsonl")
            check(len(request_costs) == count, "request cost count")
            old_predictions = {
                r["id"]: r
                for r in lines(OLD / "stages" / f"generate-train-{cell}" / "predictions.jsonl")
                if not r["replay"]
            }
            old_losses = {
                r["id"]: r for r in lines(OLD / "stages" / f"loss-train-{cell}" / "losses.jsonl")
            }
            selections = lines(directory / "selection.jsonl") if phase == "prefix" else None
            if selections is not None:
                check(
                    len(selections) == count
                    and seal["selection"] == sha(directory / "selection.jsonl"),
                    "selection seal",
                )
            cases = [*prefixes, prefixes[0]] if phase == "prefix" else prefixes
            for index, (row, case, cost) in enumerate(zip(raw, cases, request_costs, strict=True)):
                label = label_map[case["id"]]
                record_id = f"{phase}-{cell}-{index:03d}"
                expected_plan = dict(
                    record_id=record_id,
                    phase=phase,
                    cell=cell,
                    id=case["id"],
                    replay=phase == "prefix" and index == 32,
                    index=index,
                )
                actual_plan.append(expected_plan)
                check(
                    all(row[k] == v for k, v in expected_plan.items() if k != "index"), "row plan"
                )
                check(row["target_y"] == 53 and row["local_logit"] == 21, "raw target position")
                check(
                    row["suppressed_ids"] == [0, 1] and row["nonfinite_indices"] == [],
                    "suppression",
                )
                check(
                    len(row["logits"]) == 259 and all(math.isfinite(v) for v in row["logits"]),
                    "finite full-vocabulary vector",
                )
                check(
                    cost["record_id"] == record_id
                    and all(0 <= cost[k] <= 2 for k in ("cpu", "wall")),
                    "request cap",
                )
                for key in max_request:
                    max_request[key] = max(max_request[key], cost[key])
                expected_prefix = old_predictions[row["id"]]
                check(
                    expected_prefix["prefix"] == case["prefix"]
                    and expected_prefix["input_ids"] == case["input_ids"],
                    "original evaluation bytes",
                )
                metric = metrics(row["logits"], label["expected_first_id"])
                if phase == "prefix":
                    check(row["input_ids"] == case["input_ids"], "raw prefix IDs")
                    pred = metric["predicted_first_id"]
                    check(
                        pred
                        == expected_prefix["result"]["generated_ids"][0]
                        == original_ids[cell][row["id"]],
                        "reproduction",
                    )
                    check(
                        selections[index]
                        == dict(
                            record_id=record_id, predicted_first_id=pred, original_first_id=pred
                        ),
                        "selection sidecar",
                    )
                    if row["replay"]:
                        check(
                            row["logits"] == raw[0]["logits"]
                            and row["input_ids"] == raw[0]["input_ids"],
                            "exact replay",
                        )
                else:
                    check(
                        row["input_ids"] == label["full_document_ids"][:-1]
                        and row["prefix_input_ids"] == case["input_ids"]
                        and row["mask_positions"] == [53, 54, 55]
                        and row["answer_target_ids"] == label["answer_target_ids"],
                        "teacher mask/IDs",
                    )
                    ce = row["answer_ce"]
                    check(len(ce) == 3 and all(math.isfinite(v) for v in ce), "finite suffix CE")
                    log_z = max(row["logits"]) + math.log(
                        sum(math.exp(v - max(row["logits"])) for v in row["logits"])
                    )
                    delta = abs(ce[0] - (log_z - row["logits"][label["expected_first_id"]]))
                    max_ce_difference = max(max_ce_difference, delta)
                    check(delta <= 1e-5, "raw first-token CE consistency")
                    # Descriptive consistency check against saved v1 loss, no rescoring.
                    max_saved_suffix_difference = max(
                        max_saved_suffix_difference,
                        abs(sum(ce) - old_losses[row["id"]]["answer_loss"]),
                    )
                vectors[record_id] = (row, metric)
    check(actual_plan == read(RUN / "plan.json"), "exact 260-record order")
    measured = lines(RUN / "measurements.jsonl")
    check(len(measured) == 260, "annotation count")
    for annotation, (record_id, (row, metric)) in zip(measured, vectors.items(), strict=True):
        check(
            annotation["record_id"] == record_id
            and all(annotation[k] == row[k] for k in ("phase", "cell", "id", "replay")),
            "annotation identity",
        )
        check(
            annotation["expected_first_byte"] == label_map[row["id"]]["expected_first_byte"], "byte"
        )
        check(all(close(annotation[k], v) for k, v in metric.items()), "rank/margin/probability")
    parity = read(RUN / "parity.json")
    check(len(parity) == 128, "parity count")
    for index, row in enumerate(parity):
        cell = CELLS[index // 32]
        case_index = index % 32
        p, pm = vectors[f"prefix-{cell}-{case_index:03d}"]
        t, tm = vectors[f"teacher-{cell}-{case_index:03d}"]
        diff = max(abs(a - b) for a, b in zip(p["logits"], t["logits"], strict=True))
        check(
            row == dict(cell=cell, id=p["id"], max_abs_difference=diff, pass_parity=True)
            and diff <= 1e-5
            and pm["predicted_first_id"] == tm["predicted_first_id"],
            "numerical parity",
        )

    summary = read(RUN / "summary.json")
    check(
        summary["records"] == 260
        and summary["prefix_records"] == 132
        and summary["teacher_records"] == summary["parity_records"] == 128,
        "summary counts",
    )
    check(summary["training_updates"] == summary["generated_answers"] == 0, "forbidden work")
    check(
        summary["registration_sha256"] == REG_SHA
        and summary["measurements_sha256"] == sha(RUN / "measurements.jsonl"),
        "summary seals",
    )
    check(summary["decision"] == "REPRODUCIBLE_FIRST_TOKEN_MARGINS_WITH_PARITY", "decision")
    check(summary["stages"] == costs, "stage cost identities")
    contracts = lifetime(RUN / "contracts", 20, reg)
    check(sha(RUN / "contracts/cost.json") == reg["contracts_sha256"], "contract receipt")
    outer = lifetime(RUN / "execution", 200, reg)
    check(read(RUN / "execution/controller-final.json")["status"] == "PASS", "controller finally")
    residual = {
        key: outer[key] - sum(cost[key] for cost in costs.values()) for key in ("cpu", "wall")
    }
    check(
        all(0 <= value <= 40 for value in residual.values()), "complete preparation/controller cap"
    )
    check(not (RUN / "failure.json").exists(), "retained failure marker")
    old_summary = read(OLD / "summary.json")
    check(
        old_summary["decision"] == "STOP_TRAINING_FAILURE"
        and not read(OLD / "training-gate.json")["pass_gate"],
        "unchanged original failed gate",
    )
    check(not list((OLD / "stages").glob("*dev*")), "development absent")

    cell_stats = {}
    failures = []
    for cell in CELLS:
        main = [
            m for m in measured if m["phase"] == "prefix" and not m["replay"] and m["cell"] == cell
        ]
        wrong = [m for m in main if m["expected_first_id"] != m["predicted_first_id"]]
        check(summary["cells"][cell]["wrong"] == len(wrong), "summary failures")
        signed = []
        for index in range(32):
            row, m = vectors[f"prefix-{cell}-{index:03d}"]
            gold = m["expected_first_id"]
            signed.append(
                row["logits"][gold] - max(row["logits"][i] for i in range(2, 259) if i != gold)
            )
        cell_stats[cell] = dict(
            records=32,
            first_matches=32 - len(wrong),
            wrong=len(wrong),
            expected_ranks=sorted({m["expected_rank"] for m in main}),
            signed_gold_vs_best_other_min=min(signed),
            signed_gold_vs_best_other_max=max(signed),
            near_tied_decisions=sum(m["near_tied_decision"] for m in main),
            wrong_gold_prob_min=min(
                (m["expected_probability_eligible"] for m in wrong), default=None
            ),
            wrong_gold_prob_max=max(
                (m["expected_probability_eligible"] for m in wrong), default=None
            ),
        )
        if cell == "947-ordinary":
            for index, m in enumerate(main):
                if m["expected_first_id"] == m["predicted_first_id"]:
                    continue
                controls = {}
                for passing in CELLS[:3]:
                    _, other = vectors[f"prefix-{passing}-{index:03d}"]
                    check(other["expected_rank"] == 1, "passing checkpoint comparison")
                    controls[passing] = dict(
                        rank=other["expected_rank"],
                        signed_gold_vs_best_other=other["winner_minus_runner_up"],
                        expected_probability_eligible=other["expected_probability_eligible"],
                    )
                failures.append(
                    dict(
                        id=m["id"],
                        expected_id=m["expected_first_id"],
                        predicted_id=m["predicted_first_id"],
                        rank=m["expected_rank"],
                        signed_gold_vs_best_other=signed[index],
                        expected_probability_eligible=m["expected_probability_eligible"],
                        predicted_probability_eligible=m["predicted_probability_eligible"],
                        controls=controls,
                    )
                )
    check(len(failures) == 16, "16 saved failures")
    return dict(
        status="PASS",
        registration_sha256=REG_SHA,
        records=260,
        prefix_records=132,
        teacher_records=128,
        replay_checks=4,
        parity_checks=128,
        max_parity_difference=max(r["max_abs_difference"] for r in parity),
        max_first_ce_reconstruction_difference=max_ce_difference,
        max_old_suffix_loss_sum_difference=max_saved_suffix_difference,
        cells=cell_stats,
        failures=failures,
        complete_execution_cost=outer,
        complete_preparation_controller_cost=residual,
        contracts_cost=contracts,
        max_request_cost=max_request,
        stage_costs=costs,
        auditor_training_or_forward_or_generation=False,
        original_training_gate=False,
        development_evaluated=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        print(json.dumps({k: result[k] for k in ("status", "records", "parity_checks")}))
    else:
        print(json.dumps(result, sort_keys=True, allow_nan=False))
