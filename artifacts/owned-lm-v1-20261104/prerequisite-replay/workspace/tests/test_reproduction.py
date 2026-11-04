import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from toruk_lm.data import make_fixture, sha256_file, write_json
from toruk_lm.engine import TrainConfig, load_checkpoint, train
from toruk_lm.model import ModelConfig
from toruk_lm.reproduction import reproduce, summarize
from toruk_lm.validation import read_config, validate, validate_manifest


@pytest.fixture(scope="module")
def sealed_run(tmp_path_factory):
    path = tmp_path_factory.mktemp("sealed") / "run"
    reproduce(path)
    return path


def test_manifest_detects_stale_data_and_metadata(tmp_path):
    make_fixture(tmp_path / "data", documents=10)
    path = tmp_path / "data/manifest.json"
    manifest = validate_manifest(path)
    manifest["splits"]["train"]["documents"] += 1
    write_json(path, manifest)
    with pytest.raises(ValueError, match="count mismatch"):
        validate_manifest(path)
    manifest["splits"]["train"]["documents"] -= 1
    manifest["splits"]["train"]["ids"][0] = "wrong"
    write_json(path, manifest)
    with pytest.raises(ValueError, match="IDs mismatch"):
        validate_manifest(path)
    data = tmp_path / "data/train.jsonl"
    data.write_bytes(data.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="stale manifest.*checksum"):
        validate_manifest(path)


def test_rehashed_manifest_still_rejects_split_overlap(tmp_path):
    make_fixture(tmp_path / "data", documents=10)
    path = tmp_path / "data/manifest.json"
    manifest = validate_manifest(path)
    row = json.loads((path.parent / "train.jsonl").read_text().splitlines()[0])
    test = path.parent / "test.jsonl"
    test.write_text(json.dumps(row) + "\n", encoding="utf-8")
    manifest["splits"]["test"].update(sha256=sha256_file(test), documents=1, ids=[row["id"]])
    write_json(path, manifest)
    with pytest.raises(ValueError, match="separation.*overlap"):
        validate_manifest(path)


@pytest.mark.parametrize(
    "value",
    [
        {"model": {"width": "bad"}, "training": {}},
        {"model": {"heads": True}, "training": {}},
        {"model": {}, "training": {"batch_size": 1.5}},
        {"model": {}, "training": {"learning_rate": "fast"}},
        {"model": {}, "training": {"seed": 2**64}},
        {"model": {}, "training": {}, "unknown": 1},
    ],
)
def test_config_rejects_invalid_types_and_unknown_fields(tmp_path, value):
    path = tmp_path / "config.json"
    write_json(path, value)
    with pytest.raises(ValueError):
        read_config(path)


def test_summary_replays_outputs_and_preserves_timings(sealed_run, tmp_path):
    result = summarize(sealed_run, tmp_path / "summary")
    initial = json.loads((sealed_run / "summary/metrics.json").read_text())
    assert result == initial
    assert (tmp_path / "summary/table.md").read_bytes() == (
        sealed_run / "summary/table.md"
    ).read_bytes()
    assert result["validation_targets"] > 0
    assert result["peak_memory_bytes"] is None
    with pytest.raises(ValueError, match="fresh output"):
        summarize(sealed_run, tmp_path / "summary")


def test_summary_detects_checksum_and_semantic_metric_tampering(sealed_run, tmp_path):
    path = tmp_path / "copy"
    shutil.copytree(sealed_run, path)
    metrics = path / "eval/metrics.json"
    value = json.loads(metrics.read_text())
    value["loss_nats_per_byte_or_eos"] += 1
    write_json(metrics, value)
    with pytest.raises(ValueError, match="checksum mismatch"):
        summarize(path, tmp_path / "summary")
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["artifacts"]["eval/metrics.json"] = sha256_file(metrics)
    write_json(path / "manifest.json", manifest)
    with pytest.raises(ValueError, match="loss disagrees"):
        summarize(path, tmp_path / "summary")


def test_checkpoint_dataset_identity_against_manifest(sealed_run, tmp_path):
    saved = load_checkpoint(sealed_run / "train/checkpoint.pt")
    saved["datasets"]["validation"] = "wrong"
    path = tmp_path / "wrong.pt"
    torch.save(saved, path)
    with pytest.raises(ValueError, match="datasets.*manifest"):
        validate(sealed_run / "data/manifest.json", checkpoint=path)


def test_summary_rejects_inconsistent_run_metadata(sealed_run, tmp_path):
    path = tmp_path / "copy"
    shutil.copytree(sealed_run, path)
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["parameters"]["steps"] += 1
    write_json(path / "manifest.json", manifest)
    with pytest.raises(ValueError, match="parameters disagree"):
        summarize(path, tmp_path / "summary")


@pytest.mark.parametrize(
    "kind, message",
    [
        ("empty", "optimizer requires"),
        ("shape", "optimizer exp_avg"),
        ("rng", "RNG state"),
        ("lr", "optimizer setting mismatch"),
    ],
)
def test_resume_rejects_malformed_training_state(sealed_run, tmp_path, kind, message):
    saved = copy.deepcopy(load_checkpoint(sealed_run / "train/checkpoint.pt"))
    if kind == "empty":
        saved["optimizer"] = {}
    elif kind == "shape":
        first = next(iter(saved["optimizer"]["state"].values()))
        first["exp_avg"] = torch.zeros(1)
    elif kind == "rng":
        saved["python_rng"] = ()
    else:
        saved["optimizer"]["param_groups"][0]["lr"] = 10.0
    path = tmp_path / "invalid.pt"
    torch.save(saved, path)
    with pytest.raises(ValueError, match=message):
        train(
            sealed_run / "data/train.jsonl",
            sealed_run / "data/validation.jsonl",
            tmp_path / "resumed",
            ModelConfig(),
            TrainConfig(),
            3,
            path,
        )


def test_real_cli_reproduction_validation_and_summary(tmp_path):
    def cli(*args, code=0):
        result = subprocess.run(
            [sys.executable, "-m", "toruk_lm", *map(str, args)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == code, result.stderr
        if code:
            assert "error:" in result.stderr and "Traceback" not in result.stderr
        else:
            return json.loads(result.stdout)

    path = tmp_path / "run"
    assert cli("reproduce", "--output", path)["steps"] == 2
    assert (
        cli(
            "validate",
            "--manifest",
            path / "data/manifest.json",
            "--config",
            path / "config.json",
            "--checkpoint",
            path / "train/checkpoint.pt",
        )["next_step"]
        == 2
    )
    assert (
        cli("summarize", "--run", path, "--output", tmp_path / "tables")["validation_targets"] > 0
    )
    data = path / "data/train.jsonl"
    data.write_bytes(data.read_bytes() + b"\n")
    cli("validate", "--manifest", path / "data/manifest.json", code=2)
    cli(
        "train",
        "--train",
        data,
        "--validation",
        path / "data/validation.jsonl",
        "--manifest",
        path / "data/manifest.json",
        "--output",
        tmp_path / "invalid",
        code=2,
    )


def test_check_record_outside_git_checkout(tmp_path):
    source = Path(__file__).resolve().parents[1] / "scripts/check.py"
    folder = tmp_path / "scripts"
    folder.mkdir()
    shutil.copy(source, folder / "check.py")
    result = subprocess.run(
        [
            sys.executable,
            str(folder / "check.py"),
            "--output-dir",
            str(tmp_path / "checks"),
            "outside",
            "--",
            sys.executable,
            "-c",
            "print('real check')",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    record = json.loads((tmp_path / "checks/outside.json").read_text())
    assert record["base_commit"] is None
    assert record["source_files"]["scripts/check.py"] == sha256_file(source)
