"""Post-study byte/hash/accounting audit. No model import, fitting or generation."""
import json
import math
import statistics
import sys
import time
from pathlib import Path

started = time.perf_counter()
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[1] / "scripts"))
from segment_delta_data import CATEGORIES, gates, save, score, sha
from segment_delta_study import evaluation_name, read, rows, verify
from segment_delta_watch import worker_receipt

reg = verify(root)
summary, costs = read(root / "summary.json"), read(root / "run-cost.json")
assert costs["status"] == "COMPLETED" and costs["stage_count"] == 27
inputs, labels = read(root / "inputs.json"), read(root / "labels-evaluator-only.json")
per_cell = {}
for name, cell in summary["cells"].items():
    generation = root / "stages" / f"generate-{name}"
    raw = rows(generation / "predictions.jsonl")
    assert len(raw) == 25 and raw[-1]["replay"] and raw[0]["result"] == raw[-1]["result"]
    assert sha(generation/"predictions.jsonl") == read(generation/"generation-seal.json")["sha256"]
    counts = {c:0 for c in CATEGORIES}
    for row, case, label in zip(raw[:24], inputs, labels, strict=True):
        assert row["prefix"] == case["prefix"] and row["id"] == case["id"] == label["id"]
        assert row["result"]["input_ids"] == [1, *(b+3 for b in case["prefix"].encode())]
        assert all(type(t) is int and 2 <= t < 259 for t in row["result"]["generated_ids"])
        counts[label["category"]] += score(row["result"]["generated_ids"], label["gold"])
    assert counts == cell["categories"] and sum(counts.values()) == cell["correct"]
    samples = [row["cost"]["wall"] for row in raw]
    per_cell[name] = dict(
        requests=25, scored=24, unclosed=sum(r["result"]["budget_exhausted"] for r in raw[:24]),
        request_wall_median=statistics.median(samples), request_wall_p95=sorted(samples)[math.ceil(.95*len(samples))-1],
        request_cpu=sum(r["cost"]["cpu"] for r in raw), request_wall=sum(samples),
        request_cpu_max=max(r["cost"]["cpu"] for r in raw),
        raw_first_bytes=bytes(t-3 for t in raw[0]["result"]["generated_ids"] if t>=3).hex(),
    )
for seed in (113,227):
    traces = []
    for variant in ("ordinary","recurrent","delta"):
        directory = root/"stages"/f"train-{seed}-{variant}"
        stats = read(directory/"training.json")
        trace = rows(directory/"checkpoint.trace.jsonl")
        assert len(trace) == 128 and stats["next_step"] == 128
        assert sum(r["targets"] for r in trace) == stats["targets"]
        assert stats["parameters"] == stats["gradient_parameters"] == reg["parameters"][variant]
        assert sha(directory/"checkpoint.pt") == read(directory/"checkpoint-meta.json")["sha256"]
        traces.append([(r["ids"],r["targets"]) for r in trace])
    assert traces[0] == traces[1] == traces[2]
    expected = gates(*[summary["cells"][evaluation_name(seed,v,a)] for v,a in (
        ("delta","full"),("ordinary","full"),("recurrent","full"),("delta","no-read"),("delta","no-write"))])
    assert expected == summary["gates"][str(seed)]
max_gap = max(max(r["gap"] for r in rows(root/"stages"/name/"resources.jsonl")) for name in costs["stages"])
assert max_gap <= 5
assert max(r["peak_private"] for r in costs["stages"].values()) < reg["caps"]["private_bytes"]
assert all(r["status"] == "PASS" for r in costs["stages"].values())
assert costs["wall"] < 1500 and costs["cpu"] < 1500
assert not summary["advance"]
save(root/"poststudy-audit.json", dict(
    status="PASS", checks="raw exact scorer, sealed bytes, replay, shared training order/targets, checkpoints, frozen gates/caps/source identities",
    requests=275, scored_answers=264, unique_questions=24, cells=per_cell, max_monitor_gap=max_gap,
    training_targets=sum(read(root/"stages"/name/"training.json")["targets"] for name in costs["stages"] if name.startswith("train-")),
    train_cost={k:sum(r[k] for name,r in costs["stages"].items() if name.startswith("train-")) for k in ("cpu","wall")},
    warm_generation_cost={k:sum(r[f"request_{k}"] for r in per_cell.values()) for k in ("cpu","wall")},
    peak_stage_private=max(r["peak_private"] for r in costs["stages"].values()),
    failed_rehearsal_lower_bound={k:max(rows(root/"rehearsal/resources.jsonl")[-1][field],read(root/"rehearsal/worker.json")[workerfield]) for k,field,workerfield in (
        ("wall","elapsed","worker_wall"),("cpu","cpu","lifetime_cpu"))},
))
worker_receipt(root/"poststudy-audit-cost", started, 0.)
