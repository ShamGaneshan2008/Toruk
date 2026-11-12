"""Development study boundaries and independent scoring; no model generations."""

import copy
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import source_faithful_development_v1 as study  # noqa: E402
from evidence_first_policy import IntegrityError, answer, make_view  # noqa: E402


def fixture(*, incomplete=False, correction=False):
    source = 'TestRotor\'s slot is "  Ω\tfixture  ".'
    second = 'Correction: TestRotor\'s slot is "new-fixture".' if correction else "No assertion."
    messages = [
        {"role": "user", "content": source},
        {"role": "user", "content": second},
        {"role": "user", "content": "In turns m0,m1: What is TestRotor's slot?"},
    ]
    fitted = [1, 2] if incomplete else [0, 1, 2]
    view = make_view(messages, [0, 1, 2], fitted)
    result = answer(view, token_count=lambda _: 1)
    row = json.loads(
        json.dumps(
            {
                "payload": result.payload,
                "policy": asdict(result),
                "manifest": asdict(view.manifest),
                "fitted_sources": [
                    {"turn": s.interval.turn, "start": s.interval.start, "end": s.interval.end}
                    for s in view.sources
                ],
            }
        )
    )

    def span(turn, text, value):
        start = text.encode().index(('"' + value + '"').encode()) + 1
        return {"turn": turn, "start": start, "end": start + len(value.encode()), "value": value}

    old = span("m0", source, "  Ω\tfixture  ")
    new = span("m1", second, "new-fixture") if correction else old
    label = {
        "id": "test-only",
        "category": "correction" if correction else "copy",
        "payload": new["value"],
        "covered_state": "supported",
        "scope": ["m0", "m1"],
        "unparsed_turns": [],
        "source": new,
        "corrections": [[old, new]] if correction else [],
    }
    return label, row


def test_authored_labels_have_exact_spans_and_only_four_categories():
    cases, labels = study.authored_cases()
    study.validate_labels(cases, labels)
    assert {c["id"] for c in cases} == {label["id"] for label in labels}
    assert all(set(c) == {"id", "messages"} for c in cases)
    assert {len(c["messages"]) for c in cases} == {32, 48}
    for category in ("copy", "binding", "correction", "coverage"):
        assert sum(label["category"] == category for label in labels) == 3


def test_authored_gold_is_not_derived_from_policy(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("no policy or generation when authoring labels")

    monkeypatch.setattr(study.base, "answer", forbidden)
    cases, labels = study.authored_cases()
    study.validate_labels(cases, labels)


def test_manual_label_corruption_fails():
    cases, labels = study.authored_cases()
    labels[0]["source"]["end"] -= 1
    with pytest.raises(IntegrityError, match="span mismatch"):
        study.validate_labels(cases, labels)


def test_no_synthesis_requests_are_permitted():
    cases, labels = study.authored_cases()
    cases[0]["messages"][-1]["content"] = "Combine TestRotor's slot and OtherRotor's slot."
    with pytest.raises(IntegrityError, match="single-field"):
        study.validate_labels(cases, labels)


@pytest.mark.parametrize("correction", [False, True])
def test_source_linked_exact_copy_and_correction_score(correction):
    label, row = fixture(correction=correction)
    scored = study.score(label, row)
    assert scored["payload_correct"] and scored["support_correct"] and scored["provenance_correct"]


def test_normalization_and_unrelated_field_substitution_lose_accuracy():
    label, row = fixture()
    for payload in (row["payload"].strip(), "related-field-fixture"):
        changed = {**row, "payload": payload}
        assert not study.score(label, changed)["payload_correct"]
        assert not study.score(label, changed)["provenance_correct"]


def test_incomplete_safe_abstention_still_loses_full_scope_accuracy():
    label, row = fixture(incomplete=True)
    result = study.score(label, row)
    assert not result["payload_correct"]
    assert result["support_correct"] and result["provenance_correct"]
    assert result["expected_state"] == "coverage-incomplete"


def test_unknown_payload_never_hides_false_absence():
    label, row = fixture(incomplete=True)
    label["payload"] = "UNKNOWN"
    row["policy"]["state"] = "absent-in-complete-scope"
    result = study.score(label, row)
    assert result["payload_correct"] and not result["support_correct"]


def test_unparsed_annotation_never_certifies_absence():
    label, row = fixture()
    label["unparsed_turns"] = ["m1"]
    label["covered_state"] = "absent-in-complete-scope"
    assert study.expected_state(label, row) == "coverage-incomplete"


def test_missing_correction_link_or_wrong_offsets_fail_provenance():
    label, row = fixture(correction=True)
    bad = copy.deepcopy(row)
    bad["policy"]["corrections"] = []
    assert not study.score(label, bad)["provenance_correct"]
    row["policy"]["sources"][0]["start"] += 1
    assert not study.score(label, row)["provenance_correct"]


def test_lm_control_has_payload_score_without_invented_support_state():
    label, row = fixture()
    row["policy"] = None
    result = study.score(label, row)
    assert result["payload_correct"] and result["support_correct"] is None


def gate_fixture():
    scores, costs = {}, {}
    for number in ("1", "2"):
        scores[number], costs[number] = {}, {}
        for cell in study.base.CELLS:
            proposed = cell.endswith("-P")
            scores[number][cell] = [
                {
                    "payload_correct": proposed or i < 9,
                    "support_correct": True,
                    "provenance_correct": True,
                    "category": ("copy", "binding", "correction", "coverage")[i // 3],
                }
                for i in range(12)
            ]
            costs[number][cell] = {
                "tokens": 0 if proposed else 100,
                "cpu": 50 if proposed else 100,
                "wall": 50 if proposed else 100,
            }
    return scores, costs


def test_equal_policy_gains_do_not_establish_learned_selector_value():
    scores, costs = gate_fixture()
    result = study.decide(scores, costs, True)
    assert all(result["policy_gates"].values())
    assert result["outcome"] == "shared policy only"
    assert not result["learned_selector_gate"]
    assert not study.saving(0, 0, 0.2)


def test_one_failed_pass_cannot_be_hidden_by_pooling():
    scores, costs = gate_fixture()
    costs["2"]["T-P"]["wall"] = 95
    result = study.decide(scores, costs, True)
    assert not result["policy_gates"]["T-P"] and result["policy_gates"]["L-P"]


def test_regression_or_bad_support_defeats_policy_gate():
    for field in ("payload_correct", "support_correct", "provenance_correct"):
        scores, costs = gate_fixture()
        scores["1"]["T-P"][0][field] = False
        assert not study.decide(scores, costs, True)["policy_gates"]["T-P"]


def test_stronger_control_hurdle_and_integrity_cannot_be_dropped():
    scores, costs = gate_fixture()
    scores["1"]["L-LM"][9]["payload_correct"] = True
    scores["1"]["L-LM"][10]["payload_correct"] = True
    assert not study.decide(scores, costs, True)["policy_gates"]["T-P"]
    assert not any(study.decide(scores, costs, False)["policy_gates"].values())


def test_request_arithmetic_and_caps_allow_every_request_to_reach_ceiling():
    assert 12 * 4 * 2 + 8 == 104
    assert study.LIMITS["stage_wall_seconds"] == 22 + 13 * 26
    assert study.LIMITS["stage_cpu_seconds"] == 51 + 13 * 51
    assert study.LIMITS["overall_wall_seconds"] == 8 * 360 + 120
    assert study.LIMITS["overall_cpu_seconds"] == 8 * 714 + 120
    assert study.ORDER[1] == tuple(reversed(study.ORDER[0]))


def test_changed_registration_stops_before_source_or_model_loading(tmp_path, monkeypatch):
    monkeypatch.setattr(study, "RUN", tmp_path)
    study.base.write(tmp_path / "registration.json", {"changed": True})
    study.base.write(tmp_path / "execution-started.json", {"registration_sha256": "wrong"})
    with pytest.raises(IntegrityError, match="registration drift"):
        study.verify_freeze()
