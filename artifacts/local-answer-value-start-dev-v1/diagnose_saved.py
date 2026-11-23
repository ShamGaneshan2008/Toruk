"""Inspect saved training evidence and weights only; no model construction or inference."""
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import torch

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
OLD = ROOT / "artifacts/local-answer-paired-batch-dev-v1"

def read(path):
    return json.loads(path.read_text())

def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    cells = {}
    for seed in (601, 947):
        for variant in ("ordinary", "recurrent"):
            for arm in ("original", "city-shuffled", "city-paired"):
                identity = f"{seed}-{variant}-{arm}"
                fit = OLD / "stages" / ("fit-" + identity)
                analysis = OLD / "stages" / ("analyze-" + identity)
                path = fit / "checkpoint.pt"
                meta = read(fit / "checkpoint-meta.json")
                assert digest(path) == meta["sha256"] and path.stat().st_size == meta["bytes"]
                checkpoint = torch.load(path, weights_only=True, map_location="cpu")
                assert checkpoint["format"] == "toruk-local-answer-paired-batch-dev-v1"
                assert (checkpoint["seed"], checkpoint["variant"], checkpoint["arm"]) == (seed, variant, arm)
                assert checkpoint["steps"] == 1536
                assert all(float(s["step"]) == 1536 for s in checkpoint["optimizer"]["state"].values())
                h = hashlib.sha256()
                squared = 0.
                parameters = 0
                for name, value in checkpoint["model"].items():
                    assert value.dtype == torch.float32 and torch.isfinite(value).all()
                    h.update(name.encode())
                    h.update(value.numpy().tobytes())
                    squared += float(value.double().square().sum())
                    parameters += value.numel()
                training = read(fit / "training-summary.json")
                assert h.hexdigest() == training["final_model_sha256"]
                trace = lines(fit / "training.jsonl")
                assert len(trace) == 1536 and sum(t["forward_positions"] for t in trace) == 786432
                assert sum(t["history_targets"] + t["answer_targets"] for t in trace) == 692224
                vectors = lines(analysis / "city-first-token.jsonl")
                wrong = [r for r in vectors if r["expected_rank"] != 1]
                by_gold = {}
                for char in ("l", "m", "s", "t"):
                    selected = [r for r in vectors if r["expected_first_id"] == ord(char) + 3]
                    by_gold[char] = dict(count=len(selected),
                        errors=sum(r["expected_rank"] != 1 for r in selected))
                m = read(analysis / "metrics.json")
                cells[identity] = dict(
                    exact=m["exact"], eos=m["eos"], malformed=m["malformed"],
                    wrong_first=len(wrong), expected_city_first=by_gold,
                    wrong_margin_range=[min(r["expected_minus_predicted_margin"] for r in wrong),
                                        max(r["expected_minus_predicted_margin"] for r in wrong)] if wrong else None,
                    mean_city_first_ce=sum(-math.log(r["expected_probability_full"]) for r in vectors)/32,
                    wrong_ids=[r["id"] for r in wrong],
                    initial_hash=training["initial_sha256"],final_tensor_hash=h.hexdigest(),
                    parameter_count=parameters,parameter_l2=math.sqrt(squared),
                    checkpoint_sha256=meta["sha256"],checkpoint_bytes=meta["bytes"],
                    late_answer_nll=sum(r["answer_loss"]/r["answer_targets"] for r in trace[-32:])/32,
                    total_targets=692224,total_dense_positions=786432)
    for seed in (601,947):
        for variant in ("ordinary","recurrent"):
            assert len({cells[f"{seed}-{variant}-{a}"]["initial_hash"]
                        for a in ("original","city-shuffled","city-paired")}) == 1
    old = read(OLD / "independent-audit.json")
    result=dict(
        status="SAVED_TRAINING_EVIDENCE_VERIFIED",
        cells=cells,prior_comparisons=old["comparisons"],
        established=["Shared initialization within each seed/model and matched total exposure/work.",
                     "All old ordinary947 failures corrected by both city schedules, with four/six new t-byte regressions.",
                     "Saved failures are rank-two non-near-tied preferences, not proof of absent context or EOS failure.",
                     "All final tensors finite; optimizer progress matches 1536; no stale checkpoint identity."],
        unknown=["Initialization versus shuffle contribution across seeds.",
                 "Why optimization selected one competing byte rather than another.",
                 "Whether additional first-answer supervision repairs all values without suffix/EOS regression.",
                 "Development generalization, which prior paired-batch training gates never opened."],
        hypothesis="On the strongest city-shuffled schedule, first-answer-token weight16 may improve answer-value discrimination versus uniform CE.",
        rationale_limit="Saved correlations and tensor norms do not establish a training cause.",
        model_construction=False,new_forward_passes=0,new_generated_answers=0,
        checkpoint_bytes_modified=False,heldout_inputs_accessed=False)
    with (RUN/"saved-diagnosis.json").open("x",encoding="utf-8",newline="\n") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("cells","prior_comparisons")},indent=2))

if __name__=="__main__":
    main()
