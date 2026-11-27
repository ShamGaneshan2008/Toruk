"""Checkpoint integrity, exact continuation and CLI checks on disposable CPU data."""

import copy
import json
import random
import subprocess
import sys
from dataclasses import asdict

import pytest
import torch

from toruk_lm import owned_resume as safe
from toruk_lm import owned_training as legacy
from toruk_lm.owned_data import digest
from toruk_lm.owned_lm import VARIANTS, OwnedConfig


@pytest.fixture
def config():
    return OwnedConfig(context=8, width=8, heads=2, layers=1, slots=2, max_document_tokens=64)


def documents(short=False):
    prefix = "Q=" if short else "Evidence: tag=red. Tag?="
    return [dict(id="disposable-0", split="train", prefix=prefix, answer="a", text=prefix + "a\n")]


@pytest.fixture
def checkpoint(tmp_path, config):
    path = tmp_path / "legacy.pt"
    legacy.train(config, "ordinary", documents(), path, steps=2, seed=23, batch=1)
    return path


def corrupt(payload, change):
    raw = payload["optimizer"]
    index = next(iter(raw["state"]))
    moments = raw["state"][index]
    if change == "missing_all":
        raw["state"] = {}
    elif change == "missing_one":
        del raw["state"][index]
    elif change == "extra_state":
        raw["state"][9999] = copy.deepcopy(moments)
    elif change == "duplicate_parameter":
        raw["param_groups"][0]["params"][1] = index
    elif change == "reordered_parameters":
        raw["param_groups"][0]["params"].reverse()
    elif change.startswith("setting_"):
        field = change.removeprefix("setting_")
        raw["param_groups"][0][field] = {
            "lr": 0.1,
            "betas": (0.5, 0.9),
            "eps": 0.01,
            "weight_decay": 0.5,
            "amsgrad": True,
        }[field]
    elif change == "missing_moment_field":
        del moments["exp_avg"]
    elif change == "moment_shape":
        moments["exp_avg"] = torch.zeros(1)
    elif change == "moment_dtype":
        moments["exp_avg"] = moments["exp_avg"].double()
    elif change == "nonfinite_moment":
        moments["exp_avg"].fill_(torch.nan)
    elif change == "negative_second_moment":
        moments["exp_avg_sq"].fill_(-1)
    elif change == "model_dtype":
        name = next(iter(payload["model"]))
        payload["model"][name] = payload["model"][name].double()
    elif change == "step_shape":
        moments["step"] = torch.tensor([2.0])
    elif change == "step_value":
        moments["step"] = torch.tensor(1.0)
    elif change == "step_integer":
        moments["step"] = torch.tensor(2)
    elif change == "targets":
        payload["targets"] += 1
    elif change == "bool_targets":
        payload["targets"] = True
    elif change == "zero_steps":
        payload["next_step"] = 0
    elif change == "python_rng":
        payload["python_rng"] = (1, 2, 3)
    elif change == "torch_rng":
        payload["torch_rng"] = torch.zeros(3, dtype=torch.uint8)
    elif change == "runtime":
        payload["runtime"] = {}
    elif change == "tokenizer":
        payload["tokenizer"] = "different"
    elif change == "float_seed":
        payload["options"]["seed"] = 23.0
    elif change == "bool_batch":
        payload["options"]["batch"] = True
    else:
        raise AssertionError(change)


@pytest.mark.parametrize(
    "change",
    [
        "missing_all",
        "missing_one",
        "extra_state",
        "duplicate_parameter",
        "reordered_parameters",
        "setting_lr",
        "setting_betas",
        "setting_eps",
        "setting_weight_decay",
        "setting_amsgrad",
        "missing_moment_field",
        "moment_shape",
        "moment_dtype",
        "nonfinite_moment",
        "negative_second_moment",
        "model_dtype",
        "step_shape",
        "step_value",
        "step_integer",
        "targets",
        "bool_targets",
        "zero_steps",
        "python_rng",
        "torch_rng",
        "runtime",
        "tokenizer",
        "float_seed",
        "bool_batch",
    ],
)
def test_corrupt_checkpoint_rejected_before_training(
    checkpoint, tmp_path, config, monkeypatch, change
):
    payload = torch.load(checkpoint, weights_only=True)
    corrupt(payload, change)
    bad = tmp_path / "bad.pt"
    torch.save(payload, bad)
    output = tmp_path / "must not exist" / "new.pt"

    def forbidden(*args, **kwargs):
        pytest.fail("corrupt checkpoint reached training")

    monkeypatch.setattr(legacy, "train", forbidden)
    with pytest.raises(ValueError):
        safe.train(config, "ordinary", documents(), output, steps=3, seed=23, batch=1, resume=bad)
    assert not output.parent.exists()


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("short", [False, True])
def test_exact_resume_and_legacy_checkpoint_compatibility(tmp_path, config, variant, short):
    docs = documents(short)
    full, first, resumed = [tmp_path / f"{name}.pt" for name in ("full", "first", "resumed")]
    legacy.train(config, variant, docs, full, steps=3, seed=23, batch=1)
    legacy.train(config, variant, docs, first, steps=1, seed=23, batch=1)
    assert not first.with_suffix(".resume.json").exists()
    result = safe.train(config, variant, docs, resumed, steps=3, seed=23, batch=1, resume=first)
    a = torch.load(full, weights_only=True)
    b = torch.load(resumed, weights_only=True)
    for name in a["model"]:
        assert torch.equal(a["model"][name], b["model"][name]), name
    assert a["optimizer"]["param_groups"] == b["optimizer"]["param_groups"]
    assert set(a["optimizer"]["state"]) == set(b["optimizer"]["state"])
    for index, moments in a["optimizer"]["state"].items():
        for field, value in moments.items():
            assert torch.equal(value, b["optimizer"]["state"][index][field])
    assert torch.equal(a["torch_rng"], b["torch_rng"])
    assert a["python_rng"] == b["python_rng"] and a["targets"] == b["targets"]
    assert result["resumed_from"] == 1
    assert result["resume_validation"]["dataset"] == digest(docs)
    receipt = json.loads(resumed.with_suffix(".resume.json").read_text())
    assert receipt["contract"] == safe.CONTRACT and receipt["status"] == "PASS"
    assert receipt["training_updates_this_run"] == 2
    assert receipt["options"]["seed"] == 23 and receipt["environment"]["device"] == "cpu"
    # A pre-adapter v1 file does not need a fabricated receipt or waived source identity.
    assert safe.validate_resume(full, docs)["next_step"] == 3


def test_validator_preserves_rng_and_rejects_changed_data(checkpoint):
    before = checkpoint.read_bytes()
    torch_rng, python_rng = torch.get_rng_state().clone(), random.getstate()
    report = safe.validate_resume(checkpoint, documents())
    assert report["model_forwards"] == report["optimizer_updates"] == 0
    assert torch.equal(torch_rng, torch.get_rng_state()) and python_rng == random.getstate()
    assert checkpoint.read_bytes() == before
    changed = documents()
    changed[0]["text"] += "changed"
    with pytest.raises(ValueError, match="dataset"):
        safe.validate_resume(checkpoint, changed)


@pytest.mark.parametrize("content", [b"", b"not a weights archive"])
def test_unreadable_checkpoint_is_a_validation_failure(tmp_path, content):
    path = tmp_path / "bad.pt"
    path.write_bytes(content)
    with pytest.raises(ValueError, match="checkpoint"):
        safe.validate_resume(path, documents())


@pytest.mark.parametrize("field,value", [("seed", 24), ("steps", 2), ("batch", 2)])
def test_resume_options_must_match(checkpoint, config, tmp_path, field, value):
    options = dict(steps=3, seed=23, batch=1)
    options[field] = value
    with pytest.raises(ValueError, match="mismatch"):
        safe.train(
            config, "ordinary", documents(), tmp_path / "new.pt", resume=checkpoint, **options
        )


@pytest.mark.parametrize("suffix", [".pt", ".json", ".partial", ".resume.json"])
def test_output_and_companions_never_overwritten(tmp_path, config, suffix):
    output = tmp_path / "new.pt"
    occupied = output.with_suffix(suffix)
    occupied.write_bytes(b"existing work")
    with pytest.raises(ValueError, match="overwrite"):
        safe.train(config, "ordinary", documents(), output, steps=1, seed=23, batch=1)
    assert occupied.read_bytes() == b"existing work"


@pytest.mark.parametrize("variant", ["memory_on", "memory_off"])
@pytest.mark.parametrize("short", [False, True])
def test_required_moments_follow_recurrent_participation(tmp_path, config, variant, short):
    path = tmp_path / "new.pt"
    safe.train(config, variant, documents(short), path, steps=1, seed=23, batch=1)
    payload = torch.load(path, weights_only=True)
    # Remove an actual participating parameter, including a writer for long
    # memory-on documents. Inactive parameters are already absent in valid files.
    del payload["optimizer"]["state"][max(payload["optimizer"]["state"])]
    bad = tmp_path / "missing.pt"
    torch.save(payload, bad)
    with pytest.raises(ValueError, match="moments"):
        safe.validate_resume(bad, documents(short))


def test_intermittent_writer_schedule_rejected_before_training(tmp_path, config, monkeypatch):
    docs = documents(False) + documents(True)
    docs[1]["id"] = "disposable-1"

    def forbidden(*args, **kwargs):
        pytest.fail("unsupported schedule reached training")

    monkeypatch.setattr(legacy, "train", forbidden)
    output = tmp_path / "absent" / "new.pt"
    with pytest.raises(ValueError, match="intermittent"):
        safe.train(config, "memory_on", docs, output, steps=2, seed=23, batch=1)
    assert not output.parent.exists()


@pytest.mark.parametrize("invalid", ["split", "over_budget", "empty"])
def test_invalid_training_documents_rejected_before_output(tmp_path, config, invalid):
    docs = documents()
    if invalid == "split":
        docs[0]["split"] = "dev"
    elif invalid == "over_budget":
        docs[0]["text"] = "a" * 65
    else:
        docs = []
    output = tmp_path / "absent" / "new.pt"
    with pytest.raises(ValueError):
        safe.train(config, "ordinary", docs, output, steps=1, seed=23, batch=1)
    assert not output.parent.exists()


@pytest.mark.parametrize("invalid", ["missing", "empty", "blank", "number", "duplicate"])
def test_document_ids_are_checked_before_training(tmp_path, config, monkeypatch, invalid):
    docs = documents()
    if invalid == "missing":
        del docs[0]["id"]
    elif invalid == "duplicate":
        docs.append(dict(docs[0], text="another independent document"))
    else:
        docs[0]["id"] = {"empty": "", "blank": " \t", "number": 42}[invalid]

    def forbidden(*args, **kwargs):
        pytest.fail("invalid document IDs reached the numerical trainer")

    monkeypatch.setattr(legacy, "train", forbidden)
    output = tmp_path / "absent" / "new.pt"
    with pytest.raises(ValueError, match="document.*ID"):
        safe.train(config, "ordinary", docs, output, steps=1, seed=23, batch=1)
    assert not output.parent.exists()


def test_non_float32_default_is_rejected_before_training(tmp_path, config, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unsupported dtype reached the numerical trainer")

    monkeypatch.setattr(legacy, "train", forbidden)
    previous = torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.float64)
        with pytest.raises(ValueError, match="float32"):
            safe.train(config, "ordinary", documents(), tmp_path / "new.pt", steps=1, seed=23)
    finally:
        torch.set_default_dtype(previous)


def test_cli_train_resume_validate_and_failure(tmp_path, config):
    data, settings = tmp_path / "train.json", tmp_path / "config.json"
    data.write_text(json.dumps(documents()))
    settings.write_text(
        json.dumps(dict(model=asdict(config), batch_documents=1, learning_rate=0.003))
    )
    first, resumed = tmp_path / "first.pt", tmp_path / "resumed.pt"
    base = [sys.executable, "-m", "toruk_lm.owned_resume"]
    for checkpoint, steps, resume in ((first, "1", []), (resumed, "2", ["--resume", str(first)])):
        result = subprocess.run(
            [
                *base,
                "train",
                "--checkpoint",
                str(checkpoint),
                "--config",
                str(settings),
                "--data",
                str(data),
                "--variant",
                "ordinary",
                "--steps",
                steps,
                *resume,
            ],
            capture_output=True,
            text=True,
            timeout=45,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["resume_validation"]["status"] == "PASS"
    result = subprocess.run(
        [*base, "validate", "--checkpoint", str(resumed), "--data", str(data)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["next_step"] == 2
    payload = torch.load(resumed, weights_only=True)
    payload["optimizer"]["state"] = {}
    bad = tmp_path / "bad.pt"
    torch.save(payload, bad)
    result = subprocess.run(
        [*base, "validate", "--checkpoint", str(bad), "--data", str(data)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 2 and "validation failed" in result.stderr
    data.write_text("[null]")
    result = subprocess.run(
        [*base, "validate", "--checkpoint", str(resumed), "--data", str(data)],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 2 and "Traceback" not in result.stderr
