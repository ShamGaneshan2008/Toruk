"""Instruction comparisons must cover the full development set symmetrically."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import qwen_development_v5 as study  # noqa: E402
from test_qwen_development_v4 import Tokenizer, example  # noqa: E402


@pytest.fixture(scope="module")
def api():
    return study.frozen_api(study.Inputs(ROOT))


@pytest.fixture(scope="module")
def cases():
    return study.Inputs(ROOT).json(study.OLD + "/development.json")


def test_registration_has_symmetric_complete_conditions_and_fixed_limits(api):
    config = study.read(study.CONFIG)
    assert set(config["order"]) == {
        c + "-" + a for c in config["candidates"] for a in ("toruk", "lexical")
    }
    assert len(config["order"]) == 6
    assert config["candidates"]["original"] == api["SYSTEM"]
    assert config["limits"]["rehearsal_stage_wall_seconds"] == 180
    assert config["limits"]["rehearsal_total_wall_seconds"] == 6 * 180
    assert config["generation_retries"] == 0
    assert not config["heldout_authorized"] and not config["production_change"]


def test_candidate_instructions_contain_no_development_answers_ids_or_specific_fields(cases):
    for text in study.read(study.CONFIG)["candidates"].values():
        for case in cases:
            if case["expected"] != "UNKNOWN":
                assert case["expected"].casefold() not in text.casefold()
        assert "LHD-" not in text
        for field in ("password", "seal", "ledger", "meeting", "flower", "plate", "crate"):
            assert field not in text.casefold()


def test_instruction_is_identical_for_both_arms_and_changes_only_system(api, cases):
    turns = api["inference_turns"](cases[0])
    chosen = [0, len(turns) - 1]
    old = api["envelope"](turns, chosen)
    for instruction in study.read(study.CONFIG)["candidates"].values():
        toruk = study.prompt(api, turns, chosen, instruction)
        lexical = study.prompt(api, turns, chosen, instruction)
        assert toruk == lexical
        assert toruk[0] == {"role": "system", "content": instruction}
        assert toruk[1:] == old[1:]
    assert study.prompt(api, turns, chosen, api["SYSTEM"]) == old


@pytest.mark.parametrize("mutation", ["subset", "duplicate", "heldout", "answer", "order"])
def test_rejects_nonsealed_or_incomplete_development(cases, mutation):
    changed = copy.deepcopy(cases)
    if mutation == "subset":
        changed.pop()
    elif mutation == "duplicate":
        changed[-1] = changed[0]
    elif mutation == "heldout":
        changed[0]["split"] = "heldout"
    elif mutation == "answer":
        changed[0]["expected"] = "injected"
    else:
        changed.reverse()
    with pytest.raises(ValueError, match="seven sealed"):
        study.validate_cases(changed, cases)


def test_accepts_exact_development_set(cases):
    study.validate_cases(copy.deepcopy(cases), cases)


def group(correct):
    return {"correct": correct, "known_retained": 6, "exact_copy": True, "preservation": True}


def test_full_set_improvement_supports_only_development():
    baseline = {
        "toruk": group([False, True, True, True, True, True, False]),
        "lexical": group([True] * 7),
    }
    candidate = {a: group([True] * 7) for a in baseline}
    assert study.decision(baseline, candidate, True)["development_support"]
    assert not study.decision(baseline, candidate, False)["development_support"]


@pytest.mark.parametrize("arm,index", [(a, i) for a in ("toruk", "lexical") for i in range(7)])
def test_improvements_on_motivating_failures_cannot_hide_any_other_loss(arm, index):
    baseline = {
        "toruk": group([False, True, True, True, True, True, False]),
        "lexical": group([True] * 7),
    }
    candidate = {a: group([True] * 7) for a in baseline}
    candidate[arm]["correct"][index] = False
    assert not study.decision(baseline, candidate, True)["development_support"]


@pytest.mark.parametrize(
    "metric,value", [("known_retained", 5), ("exact_copy", False), ("preservation", False)]
)
def test_evidence_and_fidelity_are_required_for_both_arms(metric, value):
    baseline = {"toruk": group([False] * 7), "lexical": group([True] * 7)}
    candidate = {a: group([True] * 7) for a in baseline}
    candidate["lexical"][metric] = value
    assert not study.decision(baseline, candidate, True)["development_support"]


def test_partial_run_is_reportable_and_never_supported():
    baseline = {a: group([]) for a in ("toruk", "lexical")}
    assert not study.decision(baseline, baseline, False)["development_support"]


def test_registered_file_drift_and_output_reuse_are_rejected(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("registered", encoding="utf-8")
    bindings = {str(source): study.sha(source)}
    study.verify_map(bindings)
    source.write_text("drift", encoding="utf-8")
    with pytest.raises(ValueError, match="identity drift"):
        study.verify_map(bindings)
    receipt = tmp_path / "started.json"
    study.write(receipt, {"first": True})
    with pytest.raises(FileExistsError):
        study.write(receipt, {"first": False})
    assert json.loads(receipt.read_bytes()) == {"first": True}


def test_frozen_scoring_and_raw_answer_validation_with_new_instruction(api):
    case, row, _ = example(api, answer="violet harbor")
    instruction = "Only answer using the reference."
    row["prompt_messages"][0]["content"] = instruction
    original = copy.deepcopy(row)
    study.audit_row(case, row, Tokenizer(row["answer"]), api, instruction)
    assert row == original
    row["score"]["correct"] = False
    with pytest.raises(ValueError, match="scorer disagreement"):
        study.audit_row(case, row, Tokenizer(row["answer"]), api, instruction)


@pytest.mark.parametrize(
    "field,value",
    [
        ("answer", "fabricated"),
        ("prompt_ids", [99]),
        ("output_tokens", 42),
        ("selected_sources", []),
    ],
)
def test_new_instruction_does_not_bypass_token_source_or_answer_integrity(api, field, value):
    case, row, _ = example(api, answer="violet harbor")
    row[field] = value
    with pytest.raises(ValueError):
        study.audit_row(case, row, Tokenizer("violet harbor"), api, api["SYSTEM"])
