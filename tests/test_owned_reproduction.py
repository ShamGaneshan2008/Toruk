"""Fail closed on relocated evidence, altered inputs, outputs and model identity."""

import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def owned_run(tmp_path_factory):
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from study_owned_lm import study

    run = tmp_path_factory.mktemp("owned reproduction") / "run with spaces"
    study(ROOT / "configs/owned-lm-smoke-v1.json", run)
    return run


def validate(run):
    from validate_owned_reproduction import validate as check

    return check(
        run, ROOT / "configs/owned-lm-smoke-v1.json", ROOT / "configs/owned-reproduction-v1.json"
    )


def test_smoke_validates_after_relocation_without_original_checkpoint_paths(owned_run, tmp_path):
    relocated = tmp_path / "relocated run with spaces"
    shutil.copytree(owned_run, relocated)
    assert validate(relocated)["answers"] == 48
    assert validate(relocated)["reference_compared"] is False


@pytest.mark.parametrize("change", ["tokens", "dataset", "identity", "config", "missing", "metric"])
def test_validator_rejects_altered_evidence(owned_run, tmp_path, change):
    run = tmp_path / "run"
    shutil.copytree(owned_run, run)
    if change == "dataset":
        path = run / "data/heldout.json"
        value = json.loads(path.read_text())
        value[0]["prefix"] += "changed"
    elif change == "identity":
        path = run / "registration.json"
        value = json.loads(path.read_text())
        value["runtime"]["owned_lm.py"] = "changed"
    elif change == "config":
        path = run / "registration.json"
        value = json.loads(path.read_text())
        value["config"]["steps"] += 1
    else:
        path = run / "heldout/23-memory_on-full.json"
        if change == "missing":
            path.unlink()
            with pytest.raises(ValueError, match="missing/extra"):
                validate(run)
            return
        value = json.loads(path.read_text())
        if change == "tokens":
            value["rows"][0]["generation"]["generated_ids"] = [66]
        else:
            value["nll"] += 0.1
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        validate(run)


def test_declared_numerical_tolerance_rejects_nonfinite_and_large_changes(owned_run):
    from validate_owned_reproduction import close

    tolerance = dict(rel_tol=1e-5, abs_tol=1e-5)
    close(0.5 + 1e-6, 0.5, tolerance, "hardware rounding")
    for value in (float("nan"), float("inf"), 0.51):
        with pytest.raises(ValueError, match="numeric mismatch"):
            close(value, 0.5, tolerance, "changed loss")


def test_config_line_endings_do_not_break_relocated_validation(owned_run, tmp_path):
    from validate_owned_reproduction import validate as check

    config = tmp_path / "config with spaces.json"
    content = (ROOT / "configs/owned-lm-smoke-v1.json").read_bytes().replace(b"\r\n", b"\n")
    for data in (content, content.replace(b"\n", b"\r\n")):
        config.write_bytes(data)
        assert (
            check(owned_run, config, ROOT / "configs/owned-reproduction-v1.json")["status"]
            == "PASS"
        )


@pytest.mark.parametrize("field,value", [("schema", "v2"), ("steps", 3), ("seeds", [47])])
def test_changed_protocol_is_rejected_before_model_loading(owned_run, tmp_path, field, value):
    from validate_owned_reproduction import validate as check

    config = json.loads((ROOT / "configs/owned-lm-smoke-v1.json").read_text())
    config[field] = value
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="config/protocol identity mismatch"):
        check(owned_run, path, ROOT / "configs/owned-reproduction-v1.json")
