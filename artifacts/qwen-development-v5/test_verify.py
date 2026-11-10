"""Publication checks must reject drift without loading weights or generating."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("portable_v5", Path(__file__).with_name("verify.py"))
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.mark.parametrize("name", ["../outside", "C:/Users/outside", "/outside", "a\\b"])
def test_repository_bindings_cannot_escape(name):
    with pytest.raises(ValueError, match="unsafe"):
        module.relative(name)


def test_only_explicit_external_assets_can_be_skipped(tmp_path):
    external = {"C:/original/model.safetensors": "a" * 64}
    assert module.verify_bindings(tmp_path, external, external) == 0
    with pytest.raises(ValueError, match="asset identity drift"):
        module.verify_bindings(tmp_path, {next(iter(external)): "b" * 64}, external)
    with pytest.raises(ValueError, match="unsafe"):
        module.verify_bindings(tmp_path, {"C:/other/file": "a" * 64}, external)


def test_local_payload_corruption_is_rejected_without_repair(tmp_path):
    path = tmp_path / "raw.json"
    path.write_bytes(b"preserved")
    bindings = {"raw.json": module.digest(path.read_bytes())}
    assert module.verify_bindings(tmp_path, bindings, {}) == 1
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="bytes changed"):
        module.verify_bindings(tmp_path, bindings, {})
    assert path.read_bytes() == b"changed"


def test_replay_ignores_only_new_audit_timing():
    saved = {
        "audit_wall_seconds": 1,
        "audit_controller_cpu_seconds": 2,
        "accuracy": 0.5,
        "decisions": {"support": False},
    }
    replay = {**saved, "audit_wall_seconds": 3, "audit_controller_cpu_seconds": 4}
    assert module.substantive(saved) == module.substantive(replay)
    replay["decisions"] = {"support": True}
    assert module.substantive(saved) != module.substantive(replay)


def test_newline_variants_require_the_complete_historical_hash(tmp_path):
    path = tmp_path / "source.py"
    path.write_bytes(b"preserved\nsource\n")
    substitutions = []
    expected = module.digest(b"preserved\r\nsource\r\n")
    assert module.verify_bindings(tmp_path, {"source.py": expected}, {}, substitutions) == 1
    assert substitutions[0]["expected_sha256"] == expected
    assert path.read_bytes() == b"preserved\nsource\n"
    with pytest.raises(ValueError, match="bytes changed"):
        module.verify_bindings(tmp_path, {"source.py": "0" * 64}, {})
