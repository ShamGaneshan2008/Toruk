import json
import shutil
import subprocess
import sys

import pytest
import torch

from toruk_lm.data import sha256_file, write_json
from toruk_lm.engine import load_checkpoint, load_model
from toruk_lm.reproduction import reproduce, summarize


@pytest.fixture(scope="module")
def accounting_run(tmp_path_factory):
    path = tmp_path_factory.mktemp("accounting") / "run"
    reproduce(path)
    return path


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("train_valid_tokens_this_invocation", 999999, "target count"),
        ("training_seconds", 0, "training_seconds"),
        ("training_seconds", -1, "training_seconds"),
        ("training_seconds", float("nan"), "training_seconds"),
        ("train_tokens_per_second", 999999, "throughput disagrees"),
        ("steps_this_invocation", 0, "invocation step"),
        ("losses", [], "loss records"),
    ],
)
def test_rehashed_training_metrics_must_be_consistent(
    accounting_run, tmp_path, field, value, message
):
    path = tmp_path / "copy"
    shutil.copytree(accounting_run, path)
    metrics = path / "train/metrics.json"
    record = json.loads(metrics.read_text())
    record[field] = value
    write_json(metrics, record)
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["artifacts"]["train/metrics.json"] = sha256_file(metrics)
    write_json(path / "manifest.json", manifest)
    with pytest.raises(ValueError, match=message):
        summarize(path, tmp_path / "tables")


def test_cli_invalid_training_time_is_actionable(accounting_run, tmp_path):
    path = tmp_path / "copy"
    shutil.copytree(accounting_run, path)
    metrics = path / "train/metrics.json"
    record = json.loads(metrics.read_text())
    record["training_seconds"] = 0
    write_json(metrics, record)
    manifest = json.loads((path / "manifest.json").read_text())
    manifest["artifacts"]["train/metrics.json"] = sha256_file(metrics)
    write_json(path / "manifest.json", manifest)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "toruk_lm",
            "summarize",
            "--run",
            str(path),
            "--output",
            str(tmp_path / "tables"),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 2
    assert "training_seconds" in result.stderr and "Traceback" not in result.stderr
    assert not (tmp_path / "tables").exists()


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_checkpoint_cannot_generate_successfully(accounting_run, tmp_path, value):
    saved = load_checkpoint(accounting_run / "train/checkpoint.pt")
    saved["model"]["output.weight"].fill_(value)
    path = tmp_path / "invalid.pt"
    torch.save(saved, path)
    with pytest.raises(ValueError, match="nonfinite model weights"):
        load_model(path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "toruk_lm",
            "generate",
            "--checkpoint",
            str(path),
            "--prompt",
            "Field journal",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 2
    assert "nonfinite model weights" in result.stderr and "Traceback" not in result.stderr
    assert not result.stdout
