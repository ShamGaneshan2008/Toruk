"""Fail-closed archival accounting and label isolation, without loading chat weights."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_chat_advantage import (  # noqa: E402
    audit,
    audit_latest_launch,
    frozen_fixture_bytes,
    model_messages,
    replay_baseline,
)

FIXTURE = ROOT / "configs/chat-release-eval-v2.json"
RAW = ROOT / "artifacts/chat-release-v2/raw.json"


def test_archived_result_is_rescored_and_cost_scope_is_explicit():
    result = audit(FIXTURE, RAW)
    assert [result["summary"][mode]["quality"] for mode in ("BASELINE", "TORUK")] == [6, 6]
    assert result["selected_token_reduction_pct"] == 14.96
    assert len(result["rows"]) == 40
    assert result["full_system_efficiency"] == "UNESTABLISHED"
    assert "selector forward/token work" in result["missing_historical_costs"]
    key = next(r for r in result["rows"] if r["id"] == "long_key" and r["mode"] == "TORUK")
    assert "CEDAR-19" in key["selected_sources"][0]["content"]


@pytest.mark.parametrize("corruption", ["score", "cost", "duplicate", "source", "identity"])
def test_audit_rejects_inconsistent_saved_evidence(tmp_path, corruption):
    raw = json.loads(RAW.read_bytes())
    row = raw["rows"][0]
    if corruption == "score":
        row["score"]["quality"] = False
    elif corruption == "cost":
        row["metrics"]["total_tokens"] += 1
    elif corruption == "duplicate":
        raw["rows"][-1] = copy.deepcopy(row)
    elif corruption == "source":
        row["metrics"]["selected_message_ids"] = ["m999"]
    else:
        raw["selector_sha256"] = "0" * 64
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        audit(FIXTURE, path)


def test_frozen_question_edit_is_rejected(tmp_path):
    fixture = json.loads(FIXTURE.read_bytes())
    fixture["cases"][0]["messages"][0]["content"] += " edited"
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(fixture))
    with pytest.raises(ValueError, match="fixture identity"):
        audit(path, RAW)


def test_only_hash_verified_checkout_line_endings_are_recoverable(tmp_path):
    frozen = frozen_fixture_bytes(FIXTURE)
    crlf = tmp_path / "crlf.json"
    crlf.write_bytes(frozen.replace(b"\n", b"\r\n"))
    assert frozen_fixture_bytes(crlf) == frozen
    crlf.write_bytes(crlf.read_bytes().replace(b"HELLO", b"BYE"))
    with pytest.raises(ValueError, match="fixture identity"):
        frozen_fixture_bytes(crlf)


def test_latest_archive_counts_intermediate_generation_and_matched_static_histories():
    result = audit_latest_launch(ROOT / "artifacts/chat-launch-gate-20261107")
    assert result["matched_static_histories"] == 26
    for method in result["methods"].values():
        summary = method["summary"]
        assert len(method["rows"]) == 41
        assert summary["cases"] == 37
        assert (
            summary["all_request_metric_totals"]["output_tokens"]
            > summary["summed_metrics"]["output_tokens"]
        )


def test_generator_only_receives_history_and_matched_decoding():
    fixture = json.loads(FIXTURE.read_bytes())
    case = fixture["cases"][0]
    projected = model_messages(case)
    assert all(set(message) == {"role", "content"} for message in projected)
    assert "accepted" not in str(projected)
    projected[0]["content"] = "mutation"
    assert case["messages"][0]["content"] != "mutation"
    raw = json.loads(RAW.read_bytes())
    calls = []

    class Backend:
        def reply_with_metrics(self, messages, budget, **settings):
            calls.append((messages, budget, settings))
            # A deliberately wrong reply demonstrates labels are only used for scoring.
            old = next(r for r in raw["rows"] if r["id"] == case["id"] and r["mode"] == "BASELINE")
            return {"answer": "wrong", "metrics": old["metrics"]}

    result = replay_baseline({**fixture, "cases": [case]}, Backend(), raw["rows"])
    assert calls == [(model_messages(case), 32, {"mode": "BASELINE", "temperature": 0, "top_p": 1})]
    assert result["all_answers_match"] is False
    assert result["summary"]["quality"] == 0
