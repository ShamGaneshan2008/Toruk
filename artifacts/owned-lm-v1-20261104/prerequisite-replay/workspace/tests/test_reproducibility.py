import json
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from toruk_lm.data import sha256_file
from toruk_lm.reproducibility import compare_replay, rescore, validate_config, verify_files
from toruk_lm.tokenizer import ByteTokenizer
from toruk_lm.worlds import make_world


def test_strict_config_rejects_unknown_unbounded_and_changed_protocol(tmp_path):
    config = json.loads(Path("configs/reproduce-smoke-v1.json").read_text())
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    assert validate_config(path) == config
    for changes in (
        {"steps": 3},
        {"seconds": float("nan")},
        {"seed": True},
        {"typo": 1},
        {"mode": "other"},
    ):
        path.write_text(json.dumps(config | changes))
        with pytest.raises(ValueError):
            validate_config(path)


def test_manifest_rejects_missing_modified_and_escaping_artifacts(tmp_path):
    path = tmp_path / "result.json"
    path.write_text("{}")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": {path.name: sha256_file(path)}}))
    assert verify_files(tmp_path) == 1
    path.write_text("changed")
    with pytest.raises(ValueError, match="checksum"):
        verify_files(tmp_path)
    path.unlink()
    with pytest.raises(ValueError, match="missing artifact"):
        verify_files(tmp_path)
    manifest.write_text(json.dumps({"files": {"../outside": "anything"}}))
    with pytest.raises(ValueError, match="escapes"):
        verify_files(tmp_path)


def test_rescore_detects_forged_gold_decoding_duplicate_and_missing_answers():
    row = make_world(17, "validation", 0)
    predictions = [
        dict(
            world_id=row["id"],
            question=p["question"],
            group=p["group"],
            gold=p["answer"],
            generated="?",
            generated_ids=ByteTokenizer().encode("?"),
            answer="?",
            correct=p["answer"] == "?",
        )
        for p in row["probes"]
    ]
    assert rescore(predictions, [row], 2)["exact_accuracy"] == 1 / 3
    for changes in (
        {"gold": "fake"},
        {"generated": "fake"},
        {"correct": True},
        {"generated_ids": [2, 66]},
    ):
        changed = [p.copy() for p in predictions]
        changed[0].update(changes)
        with pytest.raises(ValueError):
            rescore(changed, [row], 2)
    with pytest.raises(ValueError, match="missing"):
        rescore(predictions[:-1], [row], 2)
    with pytest.raises(ValueError, match="duplicate"):
        rescore([*predictions, predictions[0]], [row], 2)


def test_cli_invalid_config_missing_file_and_unknown_protocol_method(tmp_path):
    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps({"methods": {"ordinary-write": {}}}))
    checkpoint = tmp_path / "unsupported.pt"
    torch.save({"format": "unsupported"}, checkpoint)
    for args, expected in (
        (["validate-config", "--config", str(tmp_path / "missing.json")], "missing.json"),
        (
            [
                "evaluate-heldout",
                "--parent",
                str(tmp_path),
                "--protocol",
                str(protocol),
                "--method",
                "typo",
                "--data",
                "missing",
                "--output",
                str(tmp_path / "out"),
            ],
            "unknown protocol method",
        ),
        (
            ["reproduce", "--config", str(protocol), "--output", str(tmp_path / "out")],
            "reproduction config requires",
        ),
        (["diagnose", "--unsupported"], "unrecognized arguments"),
        (
            ["generate", "--checkpoint", str(checkpoint), "--prompt", "hello"],
            "unsupported checkpoint",
        ),
    ):
        completed = subprocess.run(
            [sys.executable, "-m", "toruk_lm", *args], text=True, capture_output=True, timeout=60
        )
        assert completed.returncode == 2
        assert expected in completed.stderr
        assert "Traceback" not in completed.stderr


def test_replay_comparison_rejects_missing_and_changed_generated_tokens(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    prediction = dict(
        world_id="a",
        group="corrected",
        question="Q",
        generated_ids=[66],
        answer="?",
        gold="red",
        correct=False,
    )
    for directory in (left, right):
        directory.mkdir()
        (directory / "predictions.json").write_text(json.dumps([prediction]))
        (directory / "metrics.json").write_text(
            json.dumps({"groups": {"corrected": {"correct": 0}}})
        )
    assert compare_replay(left, right, tmp_path / "ok")["answers"] == 1
    (right / "predictions.json").write_text(json.dumps([prediction | {"generated_ids": [67]}]))
    with pytest.raises(ValueError, match="generated-answer mismatch"):
        compare_replay(left, right, tmp_path / "changed")
    (right / "predictions.json").unlink()
    with pytest.raises(ValueError, match="missing"):
        compare_replay(left, right, tmp_path / "missing")


def test_real_reproduction_cli_emits_rescored_artifacts_and_rejects_overwrite(tmp_path):
    output = tmp_path / "smoke"
    command = [
        sys.executable,
        "-m",
        "toruk_lm",
        "reproduce",
        "--config",
        "configs/reproduce-smoke-v1.json",
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=True, timeout=90)
    result = json.loads(completed.stdout)
    assert result["status"] == "PASS"
    assert result["results"]["recurrent"]["resume"] == "PASS"
    assert verify_files(output) > 10
    repeated = subprocess.run(command, text=True, capture_output=True, timeout=30)
    assert repeated.returncode == 2 and "fresh" in repeated.stderr
