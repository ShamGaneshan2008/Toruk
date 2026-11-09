"""Post-run audit/interpretive review; never imported by training or inference."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
RUN = BASE / "execution"
sys.path.insert(0, str(ROOT / "scripts"))
from m6_successor import aggregate, score, verify

verify(RUN)
case_map = {c["id"]: c for c in json.loads((RUN / "heldout.json").read_bytes())}
summary = json.loads((RUN / "results.json").read_bytes())
review, costs, counts = [], {}, {}
wrong_values = {"recent": {"heldout-distant-0", "heldout-distant-1", "heldout-distant-2", "heldout-distant-3", "heldout-correction-1", "heldout-correction-3", "heldout-preservation-0", "heldout-preservation-3"}, "lexical": {"heldout-distant-3"}, "toruk": {"heldout-distant-3", "heldout-correction-1", "heldout-correction-2"}}
for method in ("recent", "lexical", "toruk"):
    rows = [json.loads(line) for line in (RUN / f"heldout-{method}-answers.jsonl").read_text().splitlines()]
    assert len(rows) == 24 and {r["id"] for r in rows} == set(case_map)
    assert len({r["id"] for r in rows}) == len(rows)
    reasons = Counter()
    for row in rows:
        case = case_map[row["id"]]
        assert score(row["answer"], case) == row["score"]
        assert len(row["prompt_ids"]) == row["metrics"]["selected_context_tokens"]
        assert len(row["generated_ids"]) == row["metrics"]["output_tokens"]
        assert row["work"]["backbone_forward_positions"] == len(row["prompt_ids"]) + len(row["generated_ids"]) - 1
        assert row["metrics"]["total_tokens"] == len(row["prompt_ids"]) + len(row["generated_ids"])
        for source in row["selected_sources"]:
            message = case["messages"][int(source["id"][1:])]
            assert message == {k:source[k] for k in ("role", "content")}
        rubric_false_negative = case["kind"] == "missing" and ("not known" in row["answer"] or "not available" in row["answer"])
        cause = "correct" if row["score"]["correct"] else "rubric false negative" if rubric_false_negative else "relevant evidence omitted" if not row["required_evidence_retained"] else "generator failed with task context present"
        reasons[cause] += 1
        review.append({"id": row["id"], "method": method, "primary_score": row["score"],
                       "cause": cause, "wrong_task_value_asserted": row["id"] in wrong_values[method],
                       "unsupported_origin_assertion": method == "recent" and row["id"] == "heldout-correction-0",
                       "rubric_false_negative": rubric_false_negative, "answer": row["answer"],
                       "expected": case["value"], "obsolete": case["obsolete"],
                       "selected_sources": row["selected_sources"]})
    counts[method] = dict(reasons)
    all_rows = rows[:]
    for directory in (BASE, RUN):
        all_rows += [json.loads(line) for line in (directory / f"smoke-{method}-answers.jsonl").read_text().splitlines()]
    costs[method] = {"all_generated_requests": len(all_rows), "all_inference_work": aggregate(all_rows)["work"],
                     "heldout_known_evidence_retained": sum(r["required_evidence_retained"] for r in rows if r["kind"] != "missing"),
                     "heldout_known_evidence_cases": 20,
                     "wrong_task_values_reviewed": len(wrong_values[method]),
                     "unknown_rubric_false_negatives": sum(r["rubric_false_negative"] for r in review if r["method"] == method),
                     "peak_os_worker_private_bytes": json.loads((RUN / f"heldout-{method}-worker.json").read_bytes())["self_memory"]["peak_pagefile"],
                     "published_costs": summary["results"][method]}
training = []
for directory in (BASE, RUN):
    for stage in ("profile", "train"):
        worker = json.loads((directory / f"{stage}-worker.json").read_bytes())
        training.append({"path": str(directory / stage), "steps": worker["result"]["total_steps"],
                         "byte_model_input_positions": worker["result"]["model_input_token_evaluations"],
                         "valid_targets": worker["result"]["valid_targets"],
                         "cpu_seconds": worker["lifecycle_cpu_seconds"],
                         "checkpoint_sha256": worker["checkpoint_sha256"]})
audit = {"status": "PASS: 72/72 scores, exact question parity, source provenance, token IDs and actual cached-forward accounting verified",
         "frozen_primary_verdict": summary["pass"], "cause_counts": counts, "costs": costs,
         "training_attempts": training,
         "manual_review_scope": "Task factual values and the explicit missing-information replies. Generic assistant capability statements and exhaustive semantic assertions are not audited. Review does not replace frozen scoring.",
         "cost_scope_limit": "History, selection, model generation, setup, all profile/train/smoke work and sampled controller CPU are charged. Environment installation, common file copy/data registration and integrity-wrapper bookkeeping before job timers are excluded; no FLOP/energy or production-web-system claim.",
         "rows": review}
(BASE / "results-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
lines = ["# Successor held-out answers and review", "", "Frozen scores are unchanged. This offline review is not training data.", "", "| Case | Method | Primary correct | Cause | Raw answer |", "|---|---|---:|---|---|"]
for r in review:
    cells = [r["id"],r["method"],str(r["primary_score"]["correct"]),r["cause"],r["answer"]]
    lines.append("| " + " | ".join(v.replace("|", "\\|").replace("\n", " ") for v in cells) + " |")
(BASE / "raw-answer-review.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps({"audit":audit["status"],"causes":counts,"training_steps_all_attempts":sum(r["steps"] for r in training),"methods":{m:{k:v for k,v in d.items() if k not in ['published_costs','all_inference_work']} for m,d in costs.items()}},indent=2))
