"""Recalculate retained inference totals and parity without model inference."""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
summary = json.loads((root / "evaluation/summary.json").read_text(encoding="utf-8"))
phase1_summary = json.loads((root / "phase1/summary.json").read_text(encoding="utf-8"))
keys = ("prompt_tokens", "output_tokens", "request_ms")
phase1 = {k: sum(m[k] for stage in phase1_summary.values() for m in stage.values()) for k in keys}
phase1.update(rows=96, request_cpu_ms="NOT_MEASURED by historical driver")
phase1["subprocess_wall_seconds"] = sum(
    json.loads((root / "checks" / f"phase1-{stage}.json").read_text(encoding="utf-8"))["seconds"]
    for stage in ("development", "heldout")
)
phase2 = {}
for suite, block in summary["suites"].items():
    methods = block["methods"]
    values = {k: sum(m[k] for m in methods.values()) for k in (
        *keys, "request_cpu_ms", "history_token_positions", "fit_token_positions", "logical_scan_bytes"
    )}
    check = "independent-inference.json" if suite == "independent" else "controlled-ablations.json"
    values.update(
        rows=sum(m["n"] for m in methods.values()), stage_cost=block["stage_cost"],
        subprocess_wall_seconds=json.loads((root / "checks" / check).read_text(encoding="utf-8"))["seconds"],
    )
    phase2[suite] = values
result = {
    "phase1": phase1, "phase2": phase2, "total_model_answers": 312,
    "total_model_prompt_tokens": phase1["prompt_tokens"] + sum(x["prompt_tokens"] for x in phase2.values()),
    "total_model_output_tokens": phase1["output_tokens"] + sum(x["output_tokens"] for x in phase2.values()),
    "total_inference_subprocess_wall_seconds": phase1["subprocess_wall_seconds"] + sum(x["subprocess_wall_seconds"] for x in phase2.values()),
    "phase2_request_cpu_ms": sum(x["request_cpu_ms"] for x in phase2.values()),
    "new_research_training_steps": 0,
    "verification_training": "Separate bounded CLI/unit smokes; see verification logs, excluded from research inference totals",
    "paid_api_calls": 0,
    "energy_electricity_flops_historical_training_cost": "NOT_MEASURED",
    "controlled_main_prompt_answer_parity": 36,
    "restored_cutoff_previous_envelope_parity": 12,
}
old = [json.loads(s) for s in (root / "phase1/heldout.jsonl").read_text(encoding="utf-8").splitlines()]
new = [json.loads(s) for s in (root / "evaluation/controlled.jsonl").read_text(encoding="utf-8").splitlines()]
lookup = {(r["case"]["id"],r["method"]):r for r in old}
for row in new:
    if row["method"] in ("recent", "lexical", "toruk"):
        previous = lookup[row["case"]["id"], "new" if row["method"] == "toruk" else row["method"]]
        assert row["answer"] == previous["answer"] and row["prompt_ids"] == previous["prompt_ids"]
old_envelope = root.parent / "blocker-replay-20261104/heldout.jsonl"
lookup = {r["case"]["id"]:r for line in old_envelope.read_text(encoding="utf-8").splitlines()
          if (r := json.loads(line))["method"] == "new"}
for row in new:
    if row["method"] == "restore_cutoff":
        previous = lookup[row["case"]["id"]]
        assert row["answer"] == previous["answer"] and row["prompt_ids"] == previous["prompt_ids"]
assert result == json.loads((root / "total-cost-accounting.json").read_text(encoding="utf-8"))
with args.output.open("x",encoding="utf-8") as stream:
    json.dump({"status":"PASS", "recalculated":result},stream,indent=2)
print("PASS: exact total-cost recalculation and 48 controlled prompt/answer parity checks.")
