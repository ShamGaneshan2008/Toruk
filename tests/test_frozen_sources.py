"""CI's archive exception must reject changed bytes instead of accepting them."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "frozen_sources", Path(__file__).resolve().parents[1] / "scripts/check_frozen_sources.py"
)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def test_actual_frozen_sources() -> None:
    guard.verify()


def test_changed_frozen_source_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    source = tmp_path / "archive.py"
    source.write_bytes(b"frozen\n")
    manifest = {"archive.py": hashlib.sha256(source.read_bytes()).hexdigest()}
    (tmp_path / "configs/frozen-source-sha256.json").write_text(json.dumps(manifest))
    guard.verify(tmp_path)
    source.write_bytes(b"modified\n")
    with pytest.raises(ValueError, match="Frozen experiment source changed"):
        guard.verify(tmp_path)
