"""Development attribution must follow supplied evidence and immutable scorer bytes."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_qwen_development_v4 as audit  # noqa: E402


class Tokenizer:
    def __init__(self, answer):
        self.answer = answer

    def apply_chat_template(self, *args, **kwargs):
        return [11, 12]

    def decode(self, ids, skip_special_tokens):
        return self.answer if skip_special_tokens else "native prompt"


@pytest.fixture(scope="module")
def api():
    return audit.frozen_api(audit.Inputs(ROOT))


def example(api, *, omitted=False, unknown=False, answer="record number"):
    case = {
        "schema": "qwen-long-history-v1",
        "id": "fixture-development-example",
        "split": "development",
        "kind": "missing" if unknown else "distant",
        "expected": "UNKNOWN" if unknown else "violet harbor",
        "alternatives": [],
        "required": [] if unknown else [0],
        "messages": [
            {"role": "user", "content": "Record assigns violet harbor."},
            {"role": "assistant", "content": "Noted."},
            {"role": "user", "content": "Which destination?"},
        ],
    }
    chosen = [1, 2] if omitted else [0, 1, 2]
    score = api["score"](answer, case)
    row = {
        "answer": answer,
        "selected_indices": chosen,
        "proposed_indices": chosen,
        "selected_sources": [{"id": f"m{i}", **case["messages"][i]} for i in chosen],
        "prompt_messages": api["envelope"](case["messages"], chosen),
        "prompt_ids": [11, 12],
        "generated_ids": [21],
        "prompt_tokens": 2,
        "output_tokens": 1,
        "total_tokens": 3,
        "score": score,
        "failure": api["failure"](score, case, chosen),
        "required_evidence_retained": not omitted,
    }
    return case, row, Tokenizer(answer)


@pytest.mark.parametrize("omitted,expected", [(True, "selection"), (False, "generation")])
def test_attribution_changes_when_required_source_is_omitted(api, omitted, expected):
    case, row, tokenizer = example(api, omitted=omitted)
    assert audit.audit_row(case, row, tokenizer, api)["classification"] == expected


def test_empty_required_set_does_not_make_a_wrong_unknown_answer_correct(api):
    case, row, tokenizer = example(api, unknown=True, answer="unrelated field")
    result = audit.audit_row(case, row, tokenizer, api)
    assert result["classification"] == "generation"
    assert result["required_omitted_indices"] == []
    assert row["score"]["unsupported_response_proxy"]


def test_correct_answer_uses_frozen_rubric_and_preserves_raw_row(api):
    case, row, tokenizer = example(api, answer="violet harbor")
    original = copy.deepcopy(row)
    assert audit.audit_row(case, row, tokenizer, api)["classification"] == "correct"
    assert row == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("selected_sources", []),
        ("prompt_messages", []),
        ("prompt_tokens", 513),
        ("output_tokens", 2),
        ("total_tokens", 99),
        ("required_evidence_retained", False),
        ("score", {"correct": True}),
        ("prompt_ids", [99]),
        ("answer", "altered answer"),
    ],
)
def test_corruption_is_rejected_instead_of_reclassified(api, field, value):
    case, row, tokenizer = example(api)
    row[field] = value
    with pytest.raises(ValueError):
        audit.audit_row(case, row, tokenizer, api)


def test_heldout_path_is_rejected_before_file_open():
    inputs = audit.Inputs(ROOT)
    with pytest.raises(ValueError, match="held-out inputs prohibited"):
        inputs.read("artifacts/nonexistent/heldout-answers.jsonl")


def test_split_and_duplicate_guards_run_before_answer_audit():
    case = {"id": "fixture-development-example", "split": "development"}
    for cases in ([], [case, case], [{**case, "split": "heldout"}]):
        with pytest.raises(ValueError, match="unique development"):
            audit.validate_development(cases)


def test_preservation_detects_drift_without_rewriting(tmp_path):
    path = tmp_path / "frozen.json"
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="frozen evidence changed"):
        audit.verify_preservation(tmp_path, {"sha256": {"frozen.json": "0" * 64}})
    assert path.read_bytes() == b"changed"


def test_saved_development_audit_has_no_candidate_or_heldout_input():
    baseline = json.loads((ROOT / "artifacts/qwen-long-history-dev-v4/baseline.json").read_bytes())
    result = audit.audit(ROOT, baseline)
    assert not result["selector_changed"] and result["new_generations"] == 0
    assert result["heldout_records_parsed"] == 0
    assert result["preserved_files"] == len(baseline["sha256"])
    assert all("heldout" not in p.casefold() for p in result["consumed_development_inputs"])
    assert all(
        failure["v3_toruk"]["classification"] == "generation"
        and failure["v3_toruk"]["required_omitted_indices"] == []
        for failure in result["lexical_wins_over_v3"]
    )
