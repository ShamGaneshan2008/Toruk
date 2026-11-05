"""Output framing must not hide incomplete JSON or trailing model continuations."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "conversation_format_study", Path(__file__).parents[1] / "scripts/conversation_format_study.py"
)
assert SPEC and SPEC.loader
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


@pytest.mark.parametrize("raw", ['"blue', '"blue"\nuser:', "18", '{"answer":"blue"}'])
def test_incomplete_or_wrong_type_response_is_not_framed(raw):
    scores = study.measure(raw, "blue", owned=True)
    assert not scores["framed"]
    assert not scores["exact"]


def test_json_transport_decoding_preserves_exact_content():
    scores = study.measure('"A\\nB\\"!"\n', 'A\nB"!', owned=True)
    assert scores["framed"] and scores["exact"]
    assert not scores["raw_exact"]
    assert not study.measure('" blue "', "blue", owned=True)["exact"]


def test_external_uses_native_content():
    scores = study.measure("blue", "blue", owned=False)
    assert scores["exact"]
    assert scores["framed"] is None


def test_release_audit_rejects_a_single_refusal_error():
    report_spec = importlib.util.spec_from_file_location(
        "report_conversation_format",
        Path(__file__).parents[1] / "scripts/report_conversation_format.py",
    )
    assert report_spec and report_spec.loader
    report = importlib.util.module_from_spec(report_spec)
    report_spec.loader.exec_module(report)
    summary = {"candidate": {"categories": {"refusal": {"exact": 2, "n": 3}}}}
    assert not report.integration_audit(summary, {"integration": True})["pass"]
