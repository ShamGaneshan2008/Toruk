"""The new study must reject changed consumed data/source files and output reuse."""

import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "recall_seal_study", Path(__file__).resolve().parents[1] / "scripts/recall_study.py"
)
assert SPEC and SPEC.loader
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


def test_source_and_dataset_drift(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    source.write_text("original", encoding="utf-8")
    data = tmp_path / "development.json"
    data.write_text("[]", encoding="utf-8")
    registration = {
        "bindings": {str(source): study.sha(source)},
        "data": {"development": study.sha(data)},
    }
    (tmp_path / "registration.json").write_text(json.dumps(registration), encoding="utf-8")
    study.verify(tmp_path)
    data.write_text('["modified"]', encoding="utf-8")
    with pytest.raises(ValueError, match="dataset drift"):
        study.verify(tmp_path)
    data.write_text("[]", encoding="utf-8")
    source.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="registered input drift"):
        study.verify(tmp_path)


def test_outputs_are_not_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "output.json"
    study.write(path, {"saved": True})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        study.write(path, {"saved": False})
    assert path.read_bytes() == original
