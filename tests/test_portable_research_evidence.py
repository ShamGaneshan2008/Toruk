"""Portable evidence checks must preserve bytes and never bless unresolved hashes."""

import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "portable_evidence", ROOT / "scripts/verify_portable_research_evidence.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_path_mapping_without_device_directories():
    assert module.portable_path(r"D:\Toruk\artifacts\run\raw.json") == "artifacts/run/raw.json"
    assert (
        module.portable_path("C:/Users/susee/VS_CODE_PROJECT/Toruk/scripts/a.py") == "scripts/a.py"
    )
    with pytest.raises(ValueError):
        module.portable_path("../../outside")


def test_as_run_source_bytes_resolve_without_normalizing():
    old = b"original\r\nsource\r\n"
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("scripts/a.py", old)
    evidence = module.Evidence(
        Path.cwd(), {"source.zip": stream.getvalue(), "scripts/a.py": old.replace(b"\r\n", b"\n")}
    )
    name, raw = evidence.resolve("scripts/a.py", module.digest(old))
    assert name == "source.zip!scripts/a.py" and raw == old
    assert evidence.resolve("scripts/a.py", "0" * 64) is None


def test_generated_wheels_and_external_weights_excluded():
    assert not module.selected("artifacts/qwen-long-history-v3/verification/package/file.whl")
    assert not module.selected(
        "artifacts/backbone-qualification-v1/backbones/qwen/model.safetensors"
    )
    assert module.selected("artifacts/qwen-long-history-v3/verification/qwen-v3-tests.log")
    assert module.selected("artifacts/m6-successor-v1/selector-bundle.zip")
    assert module.selected(module.PROFILE)


def test_archive_traversal_is_rejected():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("../outside", "x")
    with pytest.raises(ValueError, match="unsafe"):
        module.Evidence(Path.cwd(), {"source.zip": stream.getvalue()})


def test_copy_targets_cannot_overwrite_originals(tmp_path):
    path = tmp_path / "raw.json"
    module.write_new(path, b'{"original":true}\r\n')
    with pytest.raises(FileExistsError):
        module.write_new(path, b"replacement")
    assert path.read_bytes() == b'{"original":true}\r\n'


def test_verifier_rejects_changed_included_bytes(tmp_path):
    module.write_new(tmp_path / "raw.json", b"corrupted")
    module.write_new(
        tmp_path / module.MANIFEST,
        json.dumps({"files": {"raw.json": module.digest(b"original")}, "excluded": {}}).encode(),
    )
    with pytest.raises(ValueError, match="included file hash mismatch"):
        module.verify(tmp_path, native=False)


def test_missing_required_binding_is_not_blessed(tmp_path):
    raw = json.dumps({"bindings": {"missing.json": "0" * 64}}).encode()
    module.write_new(tmp_path / "registration.json", raw)
    module.write_new(
        tmp_path / module.MANIFEST,
        json.dumps({"files": {"registration.json": module.digest(raw)}, "excluded": {}}).encode(),
    )
    with pytest.raises(ValueError, match="unresolved required binding"):
        module.verify(tmp_path, native=False)
