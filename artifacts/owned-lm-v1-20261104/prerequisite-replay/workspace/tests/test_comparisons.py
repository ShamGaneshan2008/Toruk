import json
import subprocess
import sys

import pytest
import torch

from toruk_lm.comparisons import EXPECTED_RESULTS, aggregate
from toruk_lm.controlled import package_fingerprint, revision_objective


def test_revision_preservation_masks_and_separate_objective_ablations():
    values = {
        name: torch.tensor(float(i + 1), requires_grad=True)
        for i, name in enumerate(
            [
                "corrected",
                "unchanged_entity",
                "unrelated_date",
                "unrelated_number",
                "unknown",
                "ambiguous",
            ]
        )
    }
    groups = {name: (value, 1) for name, value in values.items()}
    revision_objective(groups, "revision").backward()
    assert values["corrected"].grad.item() == 1
    for name in ("unchanged_entity", "unrelated_date", "unrelated_number"):
        assert values[name].grad.item() > 0
    for value in values.values():
        value.grad = None
    revision_objective(groups, "no-correction").backward()
    assert values["corrected"].grad.item() == 0
    assert values["unrelated_date"].grad.item() > 0
    for value in values.values():
        value.grad = None
    revision_objective(groups, "no-preservation").backward()
    assert values["corrected"].grad.item() > 0
    assert values["unrelated_date"].grad.item() == 0
    with pytest.raises(ValueError, match="valid targets"):
        revision_objective({"corrected": (torch.tensor(1.0), 0)}, "revision")


def test_aggregation_rejects_missing_duplicate_stale_and_different_data(tmp_path):
    paths = []
    result = dict(
        package_sha256=package_fingerprint(),
        data="same",
        config={"seed": 23},
        policy="write",
        exact_accuracy=0.0,
        inference_seconds=1.0,
        inference_forward_tokens=10,
        groups={
            g: {"accuracy": 0.0}
            for g in ("corrected", "unchanged_entity", "unrelated_date", "unrelated_number")
        },
    )
    for name in ("one", "two"):
        directory = tmp_path / name
        directory.mkdir()
        path = directory / "metrics.json"
        path.write_text(json.dumps(result))
        paths.append(path)
    assert aggregate(paths, {"one", "two"})["across_seed_std"] is None
    with pytest.raises(ValueError, match="missing"):
        aggregate(paths[:1], {"one", "two"})
    with pytest.raises(ValueError, match="duplicate"):
        aggregate([paths[0], paths[0]], {"one"})
    paths[1].write_text(json.dumps(dict(result, package_sha256="old")))
    with pytest.raises(ValueError, match="stale"):
        aggregate(paths, {"one", "two"})
    paths[1].write_text(json.dumps(dict(result, data="different")))
    with pytest.raises(ValueError, match="data mismatch"):
        aggregate(paths, {"one", "two"})


def test_tiny_real_cli_comparison_pipeline_and_generated_outputs(tmp_path):
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "toruk_lm",
            "controlled-pilot",
            "--output",
            str(tmp_path / "pilot"),
            "--steps",
            "1",
            "--worlds",
            "2",
            "--answer-budget",
            "2",
            "--seconds",
            "90",
        ],
        capture_output=True,
        text=True,
        timeout=100,
        check=True,
    )
    result = json.loads(run.stdout)
    assert set(result["results"]) == EXPECTED_RESULTS
    directory = tmp_path / "pilot"
    summary = json.loads((directory / "summary.json").read_text())
    assert summary["cost"]["total_lm_optimizer_steps"] == 12  # 8 runs + two 2-step profiles
    assert summary["cost"]["branch_count"] == 16  # 2 checkpoints x 2 splits x 2 worlds x 2 ops
    assert summary["cost"]["predictor_steps"] == 200
    assert summary["across_seed_std"] is None
    for name in EXPECTED_RESULTS:
        raw = json.loads((directory / name / "predictions.json").read_text())
        assert len(raw) == 12 and all("generated_ids" in row for row in raw)
    assert not (directory / "data/test_lm.jsonl").exists()
    protocol = json.loads((directory / "protocol.json").read_text())
    assert protocol["final_test"] == "closed"
    assert (
        json.loads((directory / "manifest.json").read_text())["package_sha256"]
        == package_fingerprint()
    )
