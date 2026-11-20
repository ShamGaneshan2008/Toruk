"""Independent saved-evidence accounting; no model execution or study mutation."""

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(ids, value):
    return ids == [*(b + 3 for b in value.encode()), 2]


def audit():
    reg = read(RUN / "registration.json")
    summary = read(RUN / "summary.json")
    outer = read(RUN / "execution/cost.json")
    gate = read(RUN / "training-gate.json")
    require(sha(RUN / "registration.json") == summary["registration_sha256"], "registration identity")
    require(gate["eligible"] == summary["eligible"], "training gate changed")
    # Preserve the enclosing monitor's failure. It is not a failed quality score
    # or permission to replace/repair the original cost receipt.
    require(outer["returncode"] == 0, "study controller did not finish")
    for name, expected in reg["sources"].items():
        require(sha(RUN / "sources" / name) == sha(ROOT / name) == expected, f"source: {name}")
    for name, expected in reg["data"].items():
        require(sha(RUN / name) == expected, f"data: {name}")
    documents = read(RUN / "train-documents.json")
    lookup = {d["id"]: d for d in documents}
    total_tokens = sum(len(d["text"].encode()) + 1 for d in documents)
    answer_tokens = sum(len(d["gold"].encode()) + 1 for d in documents)
    cells, order_refs, initial_refs = {}, {}, {}
    for seed, objective, variant in reg["order"]:
        name = f"{seed}-{objective}-{variant}"
        directory = RUN / "stages" / f"train-{name}"
        stats = read(directory / "training-summary.json")
        trace = rows(directory / "training.jsonl")
        require(len(trace) == 512, "step count")
        order = [r["ids"] for r in trace]
        require(order == order_refs.setdefault(seed, order), "unmatched order")
        require(stats["initial_sha256"] == initial_refs.setdefault((seed, variant), stats["initial_sha256"]), "unmatched initial weights")
        require(Counter(i for r in trace for i in r["ids"]) == Counter({d["id"]: 256 for d in documents}), "exposure")
        require(stats["targets"] == total_tokens * 256 and stats["answer_targets"] == answer_tokens * 256, "target totals")
        w = reg["objectives"][objective]
        sums = Counter()
        for step, row in enumerate(trace, 1):
            require(row["step"] == step, "step order")
            nh = na = 0
            raw_history = raw_answer = weighted_history = weighted_answer = 0.0
            logit_history_sq = logit_answer_sq = 0.0
            for doc_index, identity in enumerate(row["ids"]):
                doc = lookup[identity]
                ids = [*(b + 3 for b in doc["text"].encode()), 2]
                offset = len(doc["prefix"].encode())
                require(row["target_ids"][doc_index] == ids and row["answer_start"][doc_index] == offset, "target IDs/offset")
                values = zip(ids, row["token_ce"][doc_index], row["token_weighted_loss"][doc_index], row["token_logit_gradient_l2"][doc_index], strict=True)
                for index, (token, ce, weighted, norm) in enumerate(values):
                    require(all(math.isfinite(v) and v >= 0 for v in (ce, weighted, norm)), "nonfinite token evidence")
                    factor = (w if index >= offset else 1) / row["denominator"]
                    require(math.isclose(weighted, ce * factor, rel_tol=2e-6, abs_tol=1e-9), "per-token weighted loss")
                    # CE specifies p_gold. Other probabilities are not saved, so
                    # only bounds on their squared norm can be independently checked.
                    residual = 1 - math.exp(-ce)
                    require(norm >= factor * residual - 2e-7 and norm <= math.sqrt(2) * factor * residual + 2e-7, "logit gradient bound")
                    if index >= offset:
                        na += 1
                        raw_answer += ce
                        weighted_answer += weighted
                        logit_answer_sq += norm * norm
                        if token == 2:
                            sums["eos_weighted_loss"] += weighted
                    else:
                        nh += 1
                        raw_history += ce
                        weighted_history += weighted
                        logit_history_sq += norm * norm
            require(nh == row["history_targets"] and na == row["answer_targets"] and nh + w * na == row["denominator"], "partition counts")
            for actual, expected in ((raw_history, row["history_loss_sum"]), (raw_answer, row["answer_loss_sum"]), (weighted_history, row["history_contribution"]), (weighted_answer, row["answer_contribution"])):
                require(math.isclose(actual, expected, rel_tol=2e-6, abs_tol=1e-7), "partition loss sum")
            h, a, dot, combined = (row[k] for k in ("history_gradient_l2", "answer_gradient_l2", "gradient_dot", "combined_gradient_l2"))
            require(abs(dot) <= h * a + 1e-10, "gradient Cauchy bound")
            require(math.isclose(combined**2, h*h+a*a+2*dot, rel_tol=1e-5, abs_tol=1e-10), "gradient sum")
            require(math.isclose(row["answer_projection_on_total"] + row["history_projection_on_total"], 1, abs_tol=2e-6), "gradient projections")
            sums.update(dict(history_weighted_loss=weighted_history, answer_weighted_loss=weighted_answer, history_logit_gradient_sq=logit_history_sq, answer_logit_gradient_sq=logit_answer_sq))
        gradient = dict(
            raw_answer_target_fraction=answer_tokens / total_tokens,
            weighted_answer_target_fraction=w * answer_tokens / (total_tokens - answer_tokens + w * answer_tokens),
            summed_weighted_answer_loss_fraction=sums["answer_weighted_loss"] / (sums["answer_weighted_loss"] + sums["history_weighted_loss"]),
            summed_eos_loss_fraction=sums["eos_weighted_loss"] / (sums["answer_weighted_loss"] + sums["history_weighted_loss"]),
            logit_gradient_answer_squared_norm_fraction=sums["answer_logit_gradient_sq"] / (sums["answer_logit_gradient_sq"] + sums["history_logit_gradient_sq"]),
            mean_history_parameter_gradient_l2=statistics.fmean(r["history_gradient_l2"] for r in trace),
            mean_answer_parameter_gradient_l2=statistics.fmean(r["answer_gradient_l2"] for r in trace),
            mean_answer_projection=statistics.fmean(r["answer_projection_on_total"] for r in trace),
            initial_objective=trace[0]["history_contribution"] + trace[0]["answer_contribution"],
            final_objective=trace[-1]["history_contribution"] + trace[-1]["answer_contribution"],
        )
        cell = dict(training=stats, contributions=gradient, evaluations={})
        for split in ("train", "dev"):
            tag = f"{split}-{name}"
            if tag not in summary["metrics"]:
                require(split == "dev" and not summary["eligible"][objective], "skipped evaluation")
                require(not (RUN / "stages" / f"generate-dev-{name}").exists(), "gate bypass")
                continue
            path = RUN / "stages" / f"generate-{split}-{name}" / "predictions.jsonl"
            predictions = rows(path)
            inputs = read(RUN / f"{split}-inputs.json")
            labels = read(RUN / f"{split}-labels.json")
            require(sha(path) == read(path.parent / "generation-seal.json")["sha256"], "raw seal")
            require(len(predictions) == len(inputs) + 1 and predictions[-1]["result"] == predictions[0]["result"], "replay")
            count = Counter()
            for p, case, label in zip(predictions[:-1], inputs, labels, strict=True):
                require(p["id"] == case["id"] == label["id"] and p["prefix"] == case["prefix"], "case/prefix")
                require(p["input_ids"] == [1, *(b + 3 for b in case["prefix"].encode())], "native prompt IDs")
                ids = p["result"]["generated_ids"]
                require(1 <= len(ids) <= 8 and all(2 <= t < 259 for t in ids), "output IDs")
                count["exact"] += exact(ids, label["gold"])
                count["eos"] += ids[-1] == 2
                count["malformed"] += not any(exact(ids, v) for v in ("la", "mi", "so", "tu", "R-7", "Q_2", "?"))
                count["repetitive"] += any(ids[i:i+k]*3 == ids[i:i+3*k] for k in (1,2) for i in range(len(ids)-3*k+1))
            metrics = summary["metrics"][tag]
            require(all(metrics[k] == count[k] for k in count), "metrics disagree")
            generation_cost = read(path.parent / "cost.json")
            loss_cost = read(RUN / "stages" / f"loss-{split}-{name}" / "cost.json")
            cell["evaluations"][split] = dict(
                metrics=metrics,
                cold_generation=generation_cost,
                cold_scoring=loss_cost,
                warm_requests={k: sum(p["cost"][k] for p in predictions) for k in ("cpu", "wall")},
                requests=len(predictions),
            )
        cell["cold_training"] = read(directory / "cost.json")
        cells[name] = cell
    require(all(s["status"] == "PASS" for s in summary["stages"].values()), "stage failure")
    return dict(status="SAVED_EVIDENCE_VERIFIED", envelope_valid=outer["status"] == "PASS",
                registration_sha256=sha(RUN / "registration.json"), cells=cells,
                unique_training_targets=total_tokens, unique_answer_targets=answer_tokens,
                eligible=summary["eligible"], development_pass=summary["development_pass"],
                decision=summary["decision"], execution=outer,
                training_or_generation_executed=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    result = audit()
    if options.output:
        require(options.output.resolve().is_relative_to(RUN), "output must stay in study directory")
        with options.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        print(json.dumps(dict(status=result["status"], output=str(options.output), decision=result["decision"])))
    else:
        print(json.dumps(result, sort_keys=True))
