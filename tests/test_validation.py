import json
import subprocess
import sys

import pytest
import torch

from toruk_lm.data import read_documents
from toruk_lm.engine import load_checkpoint, load_model
from toruk_lm.tokenizer import ByteTokenizer


@pytest.mark.parametrize("content", ["[]\n", "null\n", '"text"\n', "{broken\n"])
def test_invalid_jsonl_reports_path_and_line(tmp_path, content):
    path = tmp_path / "invalid.jsonl"
    path.write_text("\n" + content, encoding="utf-8")
    with pytest.raises(ValueError, match="invalid.jsonl:2:"):
        read_documents(path)


@pytest.mark.parametrize(
    "saved, message",
    [
        ([], "dictionary"),
        ({"format": "wrong"}, "unsupported checkpoint"),
        ({"format": "toruk-ordinary-v1", "tokenizer": "wrong"}, "tokenizer identity"),
        ({"format": "toruk-ordinary-v1", "tokenizer": ByteTokenizer.fingerprint}, "missing fields"),
    ],
)
def test_checkpoint_structure_errors(tmp_path, saved, message):
    path = tmp_path / "invalid.pt"
    torch.save(saved, path)
    with pytest.raises(ValueError, match=message):
        load_checkpoint(path)


def test_corrupt_checkpoint_is_rejected_without_unsafe_fallback(tmp_path):
    path = tmp_path / "invalid.pt"
    path.write_bytes(b"not a torch checkpoint")
    with pytest.raises(ValueError, match="cannot read checkpoint"):
        load_checkpoint(path)


def test_checkpoint_state_mismatch_is_actionable(tmp_path):
    # Complete container, with incompatible model weights.
    saved = {
        "format": "toruk-ordinary-v1",
        "tokenizer": ByteTokenizer.fingerprint,
        "model_config": {"context": 8, "width": 16, "heads": 2, "layers": 1},
        "train_config": {},
        "model": {},
        "optimizer": {},
        "scheduler": None,
        "python_rng": (),
        "torch_rng": torch.get_rng_state(),
        "datasets": {},
        "next_step": 0,
        "data_progress": {},
    }
    path = tmp_path / "mismatch.pt"
    torch.save(saved, path)
    with pytest.raises(ValueError, match="model state mismatch"):
        load_model(path)


def test_cli_checkpoint_and_path_errors(tmp_path):
    path = tmp_path / "incomplete.pt"
    torch.save({"format": "toruk-ordinary-v1", "tokenizer": ByteTokenizer.fingerprint}, path)
    for checkpoint, message in ((path, "missing fields"), (tmp_path, "Permission denied")):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "toruk_lm",
                "generate",
                "--checkpoint",
                str(checkpoint),
                "--prompt",
                "Hello",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 2
        assert "error:" in result.stderr
        assert "Traceback" not in result.stderr
        if checkpoint == path:
            assert message in result.stderr
        assert not result.stdout


def test_valid_jsonl_still_loads(tmp_path):
    path = tmp_path / "valid.jsonl"
    row = {"id": "one", "text": "hello"}
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert read_documents(path) == [row]
