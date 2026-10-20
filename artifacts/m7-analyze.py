"""Recompute integrity/resource summaries from retained M7 outputs; no inference."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = {"studies": {}, "final_test": "NOT_RUN", "new_study_training_steps": 0}
additive = (
    "history_tokens_including_bos",
    "question_tokens",
    "generated_tokens",
    "inference_forward_tokens",
    "offline_answer_forward_tokens",
    "inference_seconds",
    "model_load_seconds",
    "derived_inference_forward_calls",
    "derived_offline_scoring_forward_calls",
    "derived_memory_proposals",
    "final_boundaries",
    "final_boundary_writes",
    "predictor_fallbacks",
)
for study, evaluations in (("templates", 15), ("load", 30)):
    directory = ROOT / f"artifacts/m7-{study}-001"
    summary = read(directory / "summary.json")
    manifest = read(directory / "manifest.json")
    protocol = read(directory / "protocol.json")
    assert digest(directory / "protocol.json") == manifest["protocol_sha256"]
    for name, expected in manifest["files"].items():
        assert digest(directory / name) == expected, name
    results = summary["results"]
    assert set(results) == set(protocol["cells"])
    resources = []
    grid = {}
    all_lengths, all_distances, all_facts = [], [], []
    for cell, methods in results.items():
        assert set(methods) == set(protocol["methods"])
        grid[cell] = {}
        for method, value in methods.items():
            assert value["examples"] == 24
            assert set(value["per_data_seed"]) == {"117", "118"}
            assert all(x["examples"] == 12 for x in value["per_data_seed"].values())
            assert all(
                sum(x["examples"] for x in bins.values()) == 24 for bins in value["strata"].values()
            )
            raw = read(directory / cell / method / "predictions.json")
            assert len(raw) == len({(p["world_id"], p["question"]) for p in raw}) == 24
            for group, score in value["groups"].items():
                items = [p for p in raw if p["group"] == group]
                assert len(items) == score["examples"] == 4
                assert sum(p["correct"] for p in items) == score["correct"]
            resources.append(value["resources"])
            all_lengths += [int(v) for v in value["strata"]["history_tokens"]]
            all_distances += [
                int(v) for v in value["strata"]["evidence_distance_tokens"] if v != "None"
            ]
            all_facts += [int(v) for v in value["strata"]["known_facts"]]
            grid[cell][method] = {
                k: value[k]
                for k in (
                    "primary",
                    "exact_accuracy",
                    "per_data_seed",
                    "data_seed_sample_sd",
                    "matches_superseded_value",
                    "nonabstaining_uncertain_errors",
                )
            }
    assert len(resources) == evaluations
    assert all(s["status"] == "PASS" for s in read(directory / "stages.json"))
    report["studies"][study] = dict(
        status="PASS execution; PARTIAL research",
        evaluations=evaluations,
        answers=evaluations * 24,
        manifest_files_verified=len(manifest["files"]),
        protocol_sha256=manifest["protocol_sha256"],
        package_sha256=summary["package_sha256"],
        driver_seconds=summary["elapsed_seconds"],
        full_command_seconds=read(f"artifacts/checks/m7-{study}.json")["seconds"],
        process_peak_bytes=summary["cumulative_process_peak_bytes"],
        resources={k: sum(r[k] for r in resources) for k in additive},
        history_token_range=[min(all_lengths), max(all_lengths)],
        evidence_distance_token_range=[min(all_distances), max(all_distances)],
        known_fact_range=[min(all_facts), max(all_facts)],
        quality=grid,
    )
verification = read("artifacts/m7-m6-replay/verification.json")
assert verification["status"] == "PASS" and verification["comparisons"] == 14
report["replay"] = dict(
    comparisons=14,
    answers=sum(r["answers"] for r in verification["results"].values()),
    driver_seconds=verification["elapsed_seconds"],
    full_command_seconds=read("artifacts/checks/m7-replay.json")["seconds"],
    inference_forward_tokens=sum(
        r["inference_forward_tokens"] for r in verification["results"].values()
    ),
    offline_answer_forward_tokens=sum(
        r["scoring_forward_tokens"] for r in verification["results"].values()
    ),
    inherited_M6_cost=verification["inherited_cost"],
)
records = {p.stem: read(p) for p in (ROOT / "artifacts/checks").glob("m7-*.json")}
report["checks"] = {
    name: {k: r[k] for k in ("status", "seconds", "evidence_path")} for name, r in records.items()
}
report["recorded_check_wall_seconds"] = sum(r["seconds"] for r in records.values())
report["accounting_limit"] = (
    "Wall times can overlap and are not CPU time. Test training/forward totals are "
    "uninstrumented. Proposal/call counts are derived from frozen kernel control flow. "
    "Predictor support/fallback work is included in stage/inference wall time; all "
    "32 deployed M7 predictor decisions fell back before the MLP. Historical M6 "
    "training/label/fitting costs are inherited separately, not charged repeatedly."
)
(ROOT / "artifacts/m7-analysis.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    json.dumps(
        {
            "status": "PASS",
            "evaluations": 45,
            "new_answers": 1080,
            "manifest_files_verified": sum(
                v["manifest_files_verified"] for v in report["studies"].values()
            ),
        }
    )
)
