"""Contracts for the fresh frozen-Qwen four-arm study, without model inference."""

import copy
import json
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from qualify_answer_backbone import sha, verify, write  # noqa: E402
from qwen_long_history import (  # noqa: E402
    ARMS,
    KINDS,
    SYSTEM,
    aggregate,
    check_overlap,
    criteria,
    envelope,
    failure,
    fit_context,
    inference_turns,
    make_cases,
    score,
)


def data():
    return make_cases("development", 82811, 1, 20), make_cases("heldout", 82831, 4, 20)


def test_data_deterministic_and_separated():
    dev, held = data()
    assert len(dev) == 7 and len(held) == 28
    assert held == make_cases("heldout", 82831, 4, 20)
    assert sum(c["expected"] != "UNKNOWN" for c in held) == 22
    legacy = []
    for p in (
        "artifacts/m6-successor-v1/execution/heldout.json",
        "artifacts/backbone-qualification-v1/heldout.json",
        "artifacts/backbone-qualification-v1/development.json",
    ):
        legacy.extend(json.loads((ROOT / p).read_bytes()))
    assert check_overlap(dev, held, legacy)["status"] == "PASS"
    bad = copy.deepcopy(held)
    bad[0]["expected"] = dev[0]["expected"]
    with pytest.raises(ValueError, match="overlap"):
        check_overlap(dev, bad, legacy)


def test_projection_does_not_expose_labels_and_has_same_format():
    case = data()[1][0]
    turns = inference_turns(case)
    before = envelope(turns, list(range(len(turns))))
    assert before[0]["content"] == SYSTEM
    assert before[1]["content"].startswith("Reference:\nUser: ")
    assert before[1]["content"].endswith(case["question"] + "\n\nAnswer:")
    case["expected"] = "SECRET_GOLD_CANARY"
    case["required"] = [999]
    assert inference_turns(case) == turns
    assert envelope(inference_turns(case), list(range(len(turns)))) == before
    with pytest.raises(ValueError):
        inference_turns({"schema": "old"})


def test_whole_turn_budget_preserves_question_and_chronology():
    turns = [{"role": "user", "content": str(i)} for i in range(5)]

    def encode(messages):
        length = messages[1]["content"].count("User:") * 10 + 10
        return torch.zeros((1, length), dtype=torch.long)

    chosen, tokens, work = fit_context(turns, list(range(5)), encode, 30)
    assert chosen == [2, 3, 4] and tokens.numel() == 30
    assert work == 50 + 40 + 30
    assert turns == [{"role": "user", "content": str(i)} for i in range(5)]
    with pytest.raises(ValueError):
        envelope(turns, [3, 1, 4])
    with pytest.raises(ValueError):
        fit_context(turns, [4], lambda _: torch.zeros((1, 100)), 30)


def test_scoring_correction_literal_and_abstention():
    held = data()[1]
    correction = next(c for c in held if c["kind"] == "correction")
    assert score(correction["expected"], correction)["correct"]
    assert score("retired locker", correction)["stale_assertion_proxy"]
    assert not score(correction["expected"] + " or retired locker", correction)["correct"]
    literal = next(c for c in held if c["kind"] == "literal")
    assert score(literal["expected"], literal)["exact_match"]
    assert not score(literal["expected"].replace("  ", " "), literal)["correct"]
    unknown = next(c for c in held if c["expected"] == "UNKNOWN")
    assert score("It is not known.", unknown)["correct"]
    assert not score("Unknown; the code is FAKE.", unknown)["correct"]
    vague = next(c for c in held if c["kind"] == "reference" and c["expected"] == "UNKNOWN")
    assert score("UNKNOWN", vague)["correct"]


def test_failure_attribution_distinguishes_omission_and_generator():
    case = data()[1][0]
    bad = score("UNKNOWN", case)
    assert failure(bad, case, []) == "required evidence omitted"
    assert failure(bad, case, case["required"]) == "unnecessary abstention with evidence present"
    assert (
        failure(score("other", case), case, case["required"])
        == "generator failed with required evidence present"
    )


def test_quality_regression_and_complete_cost_gates():
    config = json.loads((ROOT / "configs/qwen-long-history-v1.json").read_bytes())
    base = {
        "complete": True,
        "cases": 28,
        "known_cases": 22,
        "correct": 20,
        "known_correct": 17,
        "unsupported_proxy": 0,
        "stale_proxy": 0,
        "categories": {k: {"correct": 3} for k in KINDS},
        "charged_total": {"cpu_seconds": 100, "wall_seconds": 100},
    }
    results = {a: copy.deepcopy(base) for a in ARMS}
    results["toruk"]["charged_total"] = {"cpu_seconds": 80, "wall_seconds": 80}
    assert all(criteria(results, config, 28, 22).values())
    results["toruk"]["charged_total"]["cpu_seconds"] = 95
    assert not criteria(results, config, 28, 22)["cpu_seconds_vs_lexical"]
    results["toruk"]["correct"] = 16
    assert not criteria(results, config, 28, 22)["toruk_quality_floor"]
    results["full"]["complete"] = False
    assert not criteria(results, config, 28, 22)["all_complete_and_caps"]


def test_replay_counts_cost_but_not_accuracy():
    case = data()[1][0]
    row = {
        "id": case["id"],
        "kind": case["kind"],
        "score": score(case["expected"], case),
        "required_evidence_retained": True,
        "failure": "correct",
        "work": {"selector_byte_positions": 64},
    }
    for k in (
        "prompt_tokens",
        "output_tokens",
        "total_tokens",
        "request_cpu_seconds",
        "request_wall_seconds",
        "selector_cpu_seconds",
        "selector_wall_seconds",
        "fit_cpu_seconds",
        "fit_wall_seconds",
        "generation_cpu_seconds",
        "generation_wall_seconds",
        "history_bytes",
        "selector_history_bytes",
    ):
        row[k] = 2
    result = aggregate([row, {**row, "id": "replay", "is_replay": True}], [case])
    assert result["cases"] == 1 and result["correct"] == 1
    assert result["request_cpu_seconds"] == 4 and result["work"]["selector_byte_positions"] == 128


def test_identity_and_exclusive_outputs(tmp_path):
    model = tmp_path / "weights"
    model.write_bytes(b"original")
    write(
        tmp_path / "registration.json", {"bindings": {str(model): sha(model)}, "dependencies": {}}
    )
    verify(tmp_path)
    model.write_bytes(b"replacement")
    with pytest.raises(ValueError, match="drift"):
        verify(tmp_path)
    with pytest.raises(FileExistsError):
        write(tmp_path / "registration.json", {})


def test_full_context_overflow_is_an_error_not_truncation():
    from qwen_long_history import validate_full_context

    validate_full_context(32704, 32768, 64)
    with pytest.raises(ValueError, match="overflow"):
        validate_full_context(32705, 32768, 64)


def test_frozen_qwen_and_successor_identity_and_decoding():
    cfg = json.loads((ROOT / "configs/qwen-long-history-v1.json").read_bytes())
    qualified = json.loads((ROOT / cfg["backbone_freeze"]).read_bytes())
    assert qualified["generation_policy"] == cfg["generation_policy"]
    assert qualified["system_instructions"] == SYSTEM
    assert sha(ROOT / cfg["selector_checkpoint"]) == cfg["selector_sha256"]
    assert (
        qualified["model_sha256"]
        == "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"
    )


def test_progress_read_retries_only_filesystem_failure(monkeypatch, tmp_path):
    import qwen_long_history as q

    p = tmp_path / "progress.json"
    p.write_text("{}")
    calls = []

    def transient(path):
        calls.append(path)
        if len(calls) < 3:
            raise PermissionError("atomic rename contention")
        return {"active": True}

    monkeypatch.setattr(q, "read", transient)
    monkeypatch.setattr(q.time, "sleep", lambda _: None)
    assert q.read_progress(p) == {"active": True} and len(calls) == 3

    def persistent(path):
        raise PermissionError("persistent")

    monkeypatch.setattr(q, "read", persistent)
    with pytest.raises(PermissionError):
        q.read_progress(p)


def test_monitor_cleanup_terminates_descendants():
    from types import SimpleNamespace

    from qwen_long_history import terminate_tree

    killed = []
    descendant = SimpleNamespace(kill=lambda: killed.append("descendant"))
    process = SimpleNamespace(children=lambda recursive: [descendant])
    child = SimpleNamespace(poll=lambda: None, kill=lambda: killed.append("worker"))
    terminate_tree(process, child)
    assert killed == ["descendant", "worker"]
