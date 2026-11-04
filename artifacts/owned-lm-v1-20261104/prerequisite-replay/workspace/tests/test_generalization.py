import copy
import json
import subprocess
import sys

import pytest

from toruk_lm.controlled import package_fingerprint, train_controlled
from toruk_lm.data import sha256_file, write_json
from toruk_lm.generalization import (
    CELLS,
    build_data,
    check_holdout,
    checked_data,
    describe,
    kernel_identity,
    shift_world,
    verify_binding,
)
from toruk_lm.model import ModelConfig
from toruk_lm.worlds import dataset_identity, load_worlds, make_world, make_worlds, observed


def protocol(path, cells, binding=None):
    data = dict(
        cells={name: CELLS[name] for name in cells},
        anchors=[[117, 40], [118, 50]],
        kernel=kernel_identity(),
        package_sha256=package_fingerprint(),
        methods={"ordinary-write": binding} if binding else {},
    )
    write_json(path, data)
    return data


def test_heldout_pairing_new_templates_length_matched_density_and_stable_hashes(tmp_path):
    p = tmp_path / "protocol.json"
    config = protocol(
        p, ["control", "template4", "template5", "claims4", "facts4", "claims12", "facts12"]
    )
    forbidden = [make_world(17, "train", i) for i in range(4)] + [
        make_world(17, "validation", i) for i in range(4)
    ]
    left = build_data(config, p, tmp_path / "left", forbidden)
    right = build_data(config, p, tmp_path / "right", forbidden)
    for cell in left:
        assert dataset_identity(left[cell]) == dataset_identity(right[cell])
        assert checked_data(left[cell], p) == checked_data(right[cell], p)
        assert not (left[cell].parent / "train.jsonl").exists()
    control = checked_data(left["control"], p)
    for cell in ("template4", "template5"):
        changed = checked_data(left[cell], p)
        assert [r["events"] for r in changed] == [r["events"] for r in control]
        assert [r["probes"] for r in changed] == [r["probes"] for r in control]
        assert all(r["template"] not in (0, 1, 2, 3) for r in changed)
    for n in (4, 12):
        claims = checked_data(left[f"claims{n}"], p)
        facts = checked_data(left[f"facts{n}"], p)
        assert [len(r["history"]) for r in claims] == [len(r["history"]) for r in facts]
        assert [r["probes"] for r in claims] == [r["probes"] for r in facts]
        assert [r["anchor_id"] for r in claims] == [r["anchor_id"] for r in facts]
    with pytest.raises(ValueError, match="evaluation-only"):
        load_worlds(left["control"], "train")
    with pytest.raises(ValueError, match="overlap"):
        check_holdout(control[0], [control[0]])
    near = copy.deepcopy(control[0])
    near["id"] = "different"
    for e in near["events"]:
        e["entity"] = "new-" + e["entity"]
    with pytest.raises(ValueError, match="near-duplicate"):
        check_holdout(near, [control[0]])


def test_reject_stale_protocol_manifest_data_and_explicit_shift_mismatch(tmp_path):
    p = tmp_path / "protocol.json"
    config = protocol(p, ["control"])
    path = build_data(config, p, tmp_path / "data", [])["control"]
    before = path.read_bytes()
    path.write_bytes(before + b"\n")
    with pytest.raises(ValueError, match="fingerprint"):
        checked_data(path, p)
    path.write_bytes(before)
    manifest = path.parent / "manifest.json"
    original = manifest.read_text()
    changed = json.loads(original)
    changed["shift"]["extra"] = 12
    write_json(manifest, changed)
    with pytest.raises(ValueError, match="shift"):
        checked_data(path, p)
    manifest.write_text(original)
    config["package_sha256"] = "stale"
    write_json(p, config)
    with pytest.raises(ValueError, match="stale"):
        checked_data(path, p)


def test_seed_strata_floor_data_labels_and_duplicate_detection():
    rows = [
        shift_world(seed, index, "control", CELLS["control"])
        for seed, index in ((117, 40), (118, 50))
    ]
    predictions = []
    for row in rows:
        for probe in row["probes"]:
            predictions.append(
                dict(
                    world_id=row["id"],
                    question=probe["question"],
                    group=probe["group"],
                    answer="?",
                    gold=probe["answer"],
                    correct=probe["answer"] == "?",
                    history_tokens=len(row["history"]) + 1,
                )
            )
    metrics = describe(predictions, rows)
    assert metrics["primary"] == 0 and metrics["exact_accuracy"] == 1 / 3
    assert metrics["data_seed_sample_sd"] == 0 and metrics["training_seed_sd"] is None
    assert sum(v["examples"] for v in metrics["strata"]["history_tokens"].values()) == 12
    assert set(metrics["per_data_seed"]) == {"117", "118"}
    corrupt = copy.deepcopy(predictions)
    corrupt[-1] = corrupt[0]
    with pytest.raises(ValueError, match="duplicate"):
        describe(corrupt, rows)
    corrupt = copy.deepcopy(predictions)
    corrupt[0]["group"] = "unknown"
    with pytest.raises(ValueError, match="scoring/label"):
        describe(corrupt, rows)
    projected = observed(rows[0], rows[0]["probes"][0])
    rows[0]["shift"] = {"oracle": "secret", "future_question": "secret"}
    assert observed(rows[0], rows[0]["probes"][0]) == projected


def test_real_protocol_bound_heldout_cli_and_checkpoint_rejection(tmp_path):
    data = tmp_path / "train-data"
    make_worlds(data, worlds_per_split=2)
    parent = tmp_path / "parent"
    training = train_controlled(
        data / "train.jsonl",
        data / "validation.jsonl",
        parent / "ordinary",
        "ordinary",
        steps=1,
        config=ModelConfig(width=8, heads=2, layers=1),
    )
    binding = dict(
        checkpoint="ordinary/checkpoint.pt",
        checkpoint_sha256=sha256_file(parent / "ordinary/checkpoint.pt"),
        predictor=None,
        predictor_sha256=None,
        policy="write",
        training=training,
    )
    p = tmp_path / "protocol.json"
    config = protocol(p, ["template4"], binding)
    shifted = build_data(config, p, tmp_path / "heldout", [])["template4"]
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "toruk_lm",
            "evaluate-heldout",
            "--parent",
            str(parent),
            "--protocol",
            str(p),
            "--method",
            "ordinary-write",
            "--data",
            str(shifted),
            "--output",
            str(tmp_path / "evaluation"),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    metrics = json.loads(run.stdout)
    assert metrics["examples"] == 12
    assert (tmp_path / "evaluation/predictions.json").is_file()
    wrong = dict(binding, checkpoint_sha256="stale")
    with pytest.raises(ValueError, match="checkpoint"):
        verify_binding(parent, wrong)
