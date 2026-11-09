"""Successor contracts without pretrained weights or historical selector substitution."""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from m6_successor import (  # noqa: E402
    aggregate,
    cases,
    inference_messages,
    leakage_audit,
    score,
    sha,
    tree_memory,
    verify,
    write,
)


def test_deterministic_data_and_disjoint_values_templates():
    dev = cases("development", 8051, 1)
    held = cases("heldout", 8061, 4)
    assert cases("heldout", 8061, 4) == held
    assert len(dev) == 6 and len(held) == 24
    assert all(len(case["messages"]) > 20 for case in held)
    leakage_audit(dev, held, "independent controlled-world training text")
    bad = copy.deepcopy(held)
    bad[0]["value"] = dev[0]["value"]
    with pytest.raises(ValueError, match="values"):
        leakage_audit(dev, bad, "")
    with pytest.raises(ValueError, match="training text"):
        leakage_audit(dev, held, held[0]["value"])


def test_scoring_corrections_exact_spacing_and_abstention():
    examples = {c["kind"]: c for c in cases("heldout", 8061, 1)}
    corrected = examples["correction"]
    assert score(corrected["value"], corrected)["correct"]
    assert not score(corrected["obsolete"], corrected)["correct"]
    assert score(corrected["obsolete"], corrected)["stale_assertion_proxy"]
    exact = examples["exact"]
    assert score(exact["value"], exact)["correct"]
    assert not score(exact["value"].replace("  ", " "), exact)["correct"]
    assert score("I don't know.", examples["missing"])["correct"]
    assert score("The locker key is invented.", examples["missing"])["unsupported_abstention_proxy"]


def test_registration_identity_and_no_overwrite(tmp_path):
    file = tmp_path / "file.json"
    write(file, {"value": 1})
    with pytest.raises(FileExistsError):
        write(file, {"value": 2})
    write(tmp_path / "registration.json", {"bindings": {str(file): sha(file)}, "dependencies": {}})
    verify(tmp_path)
    file.write_text(json.dumps({"value": 2}))
    with pytest.raises(ValueError, match="drift"):
        verify(tmp_path)


def test_cost_accounting_keeps_token_units_and_full_history_separate():
    row = {
        "kind": "exact",
        "score": {
            "correct": True,
            "unsupported_abstention_proxy": False,
            "stale_assertion_proxy": False,
        },
        "metrics": {"selected_context_tokens": 100, "output_tokens": 4},
        "request_wall_seconds": 2.0,
        "request_cpu_seconds": 3.0,
        "required_evidence_retained": True,
        "work": {
            "history_token_positions": 900,
            "fit_token_positions": 100,
            "backbone_forward_positions": 103,
            "selector_byte_positions": 2000,
            "selector_byte_positions_calls": 32,
        },
    }
    result = aggregate([row, copy.deepcopy(row)])
    assert result["prompt_tokens"] == 200
    assert result["work"]["history_token_positions"] == 1800
    assert result["work"]["selector_byte_positions"] == 4000
    assert result["request_cpu_seconds"] == 6
    assert "total_tokens" not in result  # No false equivalence of byte and BPE positions.


def test_generator_projection_excludes_gold_and_does_not_mutate_case():
    case = cases("heldout", 8061, 1)[0]
    messages = inference_messages(case)
    assert all(set(m) == {"role", "content"} for m in messages)
    assert messages[-1]["content"] == case["messages"][-1]["content"]
    messages[0]["content"] = "changed"
    assert case["messages"][0]["content"] != "changed"


def test_windows_launcher_memory_includes_actual_model_child():
    from types import SimpleNamespace

    class Process:
        def __init__(self, memory, children):
            self.memory = memory
            self.descendants = children

        def children(self, recursive):
            assert recursive
            return self.descendants

        def is_running(self):
            return True

        def memory_info(self):
            return SimpleNamespace(rss=self.memory, private=self.memory * 2)

    model = Process(100_000_000, [])
    launcher = Process(1_000_000, [model])
    assert tree_memory(launcher) == (101_000_000, 202_000_000)
