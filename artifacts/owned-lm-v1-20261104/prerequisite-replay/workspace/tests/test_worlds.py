import dataclasses
import json
import subprocess
import sys

import pytest

from toruk_lm.data import sha256_file
from toruk_lm.worlds import (
    ObservedPrompt,
    dataset_identity,
    load_worlds,
    make_world,
    make_worlds,
    observed,
    oracle,
    render,
    summarize,
)


def event(kind, value, who="x", attribute="color"):
    return dict(kind=kind, entity=who, attribute=attribute, value=value)


def test_authority_correction_ambiguity_and_independent_oracle():
    events = [
        event("SET", "red"),
        event("SET", "Ada", attribute="name"),
        event("SET", "42", who="y"),
        event("FIX", "blue"),
        event("FIX", "gold"),
    ]
    for kind in ("CLAIM", "QUOTE", "IF", "DENY"):
        events.append(event(kind, "red"))
    assert oracle(events, "x", "color") == "gold"
    assert oracle(events, "x", "name") == "Ada"
    assert oracle(events, "y", "color") == "42"
    assert oracle(events, "missing", "color") == "?"
    events.append(event("CONFLICT", "pink"))
    assert oracle(events, "x", "color") == "?"
    events.append(event("FIX", "green"))
    assert oracle(events, "x", "color") == "green"
    for seed in range(10):
        for split in ("train", "validation", "test"):
            for i in range(5):
                row = make_world(seed, split, i)
                for probe in row["probes"]:
                    assert (
                        oracle(row["events"], probe["entity"], probe["attribute"])
                        == probe["answer"]
                    )


def test_frozen_world_splits_templates_patterns_and_determinism(tmp_path):
    left = make_worlds(tmp_path / "left", worlds_per_split=4)
    right = make_worlds(tmp_path / "right", worlds_per_split=4)
    assert left == right
    split_ids = []
    entities = []
    templates = []
    patterns = []
    for split in ("train", "validation", "test"):
        rows = load_worlds(tmp_path / "left" / f"{split}.jsonl", split)
        split_ids.extend(r["id"] for r in rows)
        entities.append({e["entity"] for r in rows for e in r["events"]})
        templates.append({r["template"] for r in rows})
        patterns.append({r["corrections"] for r in rows})
    assert len(set(split_ids)) == len(split_ids)
    for sets in (entities, templates, patterns):
        assert not sets[0] & sets[1] and not sets[0] & sets[2] and not sets[1] & sets[2]
    assert not (tmp_path / "left/test_lm.jsonl").exists()
    assert dataset_identity(tmp_path / "left/train.jsonl") == dataset_identity(
        tmp_path / "right/train.jsonl"
    )
    with pytest.raises(ValueError, match="overwrite"):
        make_worlds(tmp_path / "left")
    with pytest.raises(ValueError, match="fingerprint"):
        load_worlds(tmp_path / "left/train.jsonl", "validation")


def test_runtime_projection_excludes_gold_oracle_and_other_questions():
    row = make_world(17, "train", 0)
    probe = dict(row["probes"][0])
    before = observed(row, probe)
    probe["answer"] = "LEAKED_GOLD"
    row["oracle"] = {"secret": "LEAKED_STATE"}
    row["future_text"] = "LEAKED_FUTURE"
    row["probes"] = [{"question": "LEAKED_QUESTION"}]
    assert observed(row, probe) == before
    assert {f.name for f in dataclasses.fields(ObservedPrompt)} == {"history", "question"}
    assert "LEAKED" not in before.text()


def test_rejects_stale_data_labels_rendering_and_duplicate_worlds(tmp_path):
    make_worlds(tmp_path, worlds_per_split=2)
    path = tmp_path / "train.jsonl"
    original = path.read_text(encoding="utf-8")
    path.write_text(original + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint"):
        load_worlds(path, "train")
    rows = [json.loads(line) for line in original.splitlines()]

    def install(changed):
        path.write_text("".join(json.dumps(r) + "\n" for r in changed), encoding="utf-8")
        manifest_path = tmp_path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["splits"]["train"]["sha256"] = sha256_file(path)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    rows[0]["probes"][0]["answer"] = "obsolete"
    install(rows)
    with pytest.raises(ValueError, match="oracle"):
        load_worlds(path, "train")
    rows[0]["probes"][0]["answer"] = oracle(
        rows[0]["events"], rows[0]["probes"][0]["entity"], "color"
    )
    rows[0]["history"] += "invented evidence"
    install(rows)
    with pytest.raises(ValueError, match="rendered"):
        load_worlds(path, "train")
    rows[0]["history"] = render(rows[0]["events"], rows[0]["template"])
    rows[1]["id"] = rows[0]["id"]
    install(rows)
    with pytest.raises(ValueError, match="IDs"):
        load_worlds(path, "train")


def test_exact_scoring_and_abstention_coverage():
    result = summarize(
        [
            dict(group="corrected", answer="blue", correct=True),
            dict(group="corrected", answer="red", correct=False),
            dict(group="unknown", answer="?", correct=True),
            dict(group="ambiguous", answer="", correct=False),
        ]
    )
    assert result["exact_accuracy"] == 0.5
    assert result["groups"]["corrected"]["accuracy"] == 0.5
    assert result["answer_coverage"] == 0.5


def test_real_controlled_world_cli_train_reload_and_answer_without_gold(tmp_path):
    def cli(*args):
        run = subprocess.run(
            [sys.executable, "-m", "toruk_lm", *map(str, args)],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        return json.loads(run.stdout)

    data, fit, evaluation = (tmp_path / name for name in ("worlds", "fit", "eval"))
    cli("make-worlds", "--output", data, "--worlds-per-split", 2)
    trained = cli(
        "train",
        "--train",
        data / "train_lm.jsonl",
        "--validation",
        data / "validation_lm.jsonl",
        "--output",
        fit,
        "--steps",
        1,
        "--context",
        32,
        "--width",
        16,
        "--layers",
        1,
    )
    assert trained["steps_completed"] == 1
    result = cli(
        "evaluate-worlds",
        "--checkpoint",
        fit / "checkpoint.pt",
        "--data",
        data / "validation.jsonl",
        "--output",
        evaluation,
        "--max-new-tokens",
        2,
    )
    assert result["examples"] == 12
    predictions = json.loads((evaluation / "predictions.json").read_text(encoding="utf-8"))
    row = load_worlds(data / "validation.jsonl", "validation")[0]
    reference = cli(
        "generate",
        "--checkpoint",
        fit / "checkpoint.pt",
        "--prompt",
        observed(row, row["probes"][0]).text(),
        "--max-new-tokens",
        2,
    )
    assert predictions[0]["generated_ids"] == reference["ids"]
    rerun = cli(
        "evaluate-worlds",
        "--checkpoint",
        fit / "checkpoint.pt",
        "--data",
        data / "validation.jsonl",
        "--output",
        tmp_path / "again",
        "--max-new-tokens",
        2,
    )
    assert result["groups"] == rerun["groups"]
