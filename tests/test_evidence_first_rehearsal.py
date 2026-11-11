"""Integration/resource tests use fake decoder outputs; no model generations."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evidence_first_rehearsal as study  # noqa: E402
from evidence_first_policy import IntegrityError  # noqa: E402


class Tensor:
    def __init__(self, ids):
        self.ids = ids
        self.shape = (1, len(ids))

    def numel(self):
        return len(self.ids)

    def __getitem__(self, key):
        assert key == 0
        return self

    def tolist(self):
        return self.ids


class Tokenizer:
    def encode(self, text, **kwargs):
        return list(text.encode())


class Backend:
    tokenizer = Tokenizer()
    model_id = "fake-no-decoder-loaded"

    def __init__(self, generated="UNKNOWN"):
        self.generated = generated
        self.calls = 0
        self.prompts = []

    def _tokens(self, prompt):
        self.prompts.append(prompt)
        return Tensor(list(json.dumps(prompt).encode()))

    def generate_once(self, tokens):
        self.calls += 1
        return [1, 2], self.generated


class Selector:
    def __init__(self, indices, name="T"):
        self.indices = indices
        self.sha256 = name

    def select(self, messages):
        return self.indices, True


def messages(question="In turns m1: Copy CopperFern's ribbon."):
    return [
        {"role": "user", "content": "CopperFern's unrelated note is \"" + "x" * 700 + '".'},
        {"role": "user", "content": 'CopperFern\'s ribbon is "  ν\tL  ".'},
        {"role": "user", "content": question},
    ]


def test_controls_and_policy_keep_identical_fit_and_original_control_behavior():
    selected = [0, 1, 2]
    control_backend = Backend("  generated control  ")
    original_messages = messages()
    control = study.execute(original_messages, Selector(selected), control_backend, False)
    proposed_backend = Backend("must never be called")
    proposed = study.execute(original_messages, Selector(selected), proposed_backend, True)
    assert control["payload"] == "generated control"  # historical LM .strip() behavior
    assert proposed["payload"].encode() == "  ν\tL  ".encode()
    assert original_messages == messages()  # no mutation or rewriting
    for key in ("prompt_messages", "prompt_ids", "fitted_sources", "manifest", "fitted_indices"):
        assert control[key] == proposed[key]
    assert control["fitted_indices"] == [1, 2]
    assert proposed["fit_evictions"] == ["m0"]
    assert control_backend.calls == 1 and proposed_backend.calls == 0
    assert control["executed_input_tokens"] > 0 and proposed["executed_input_tokens"] == 0
    assert proposed["cost"]["parsing_policy_validation_wall_seconds"] > 0
    assert proposed["cost"]["tokenization_wall_seconds"] > 0
    assert proposed["history_bytes"] > proposed["fitted_bytes"]


def test_both_selectors_use_the_same_policy_and_never_expose_omitted_bytes(monkeypatch):
    seen = []
    original = study.answer

    def policy(view, **kwargs):
        seen.append(view)
        assert not hasattr(view, "history")
        assert "x" * 700 not in repr(view)
        return original(view, **kwargs)

    monkeypatch.setattr(study, "answer", policy)
    rows = [
        study.execute(messages(), Selector([0, 1, 2], name), Backend(), True) for name in ("T", "L")
    ]
    assert len(seen) == 2 and rows[0]["policy"] == rows[1]["policy"]
    assert all(r["extra_history_lookups"] == 0 for r in rows)


def test_real_lexical_selector_uses_the_same_integration_seam():
    from toruk_lm.context_selection import LexicalContextSelector

    result = study.execute(messages(), LexicalContextSelector("lexical-v1"), Backend(), True)
    assert result["payload"].encode() == "  ν\tL  ".encode()


def test_integration_synthesis_charges_lm_work_even_when_output_is_rejected():
    turns = [
        {"role": "user", "content": 'CopperFern\'s ribbon is "nu".'},
        {"role": "user", "content": 'BronzeMoss\'s ribbon is "xi".'},
        {"role": "user", "content": "Combine CopperFern's ribbon and BronzeMoss's ribbon."},
    ]
    backend = Backend("nu and fabricated")
    result = study.execute(turns, Selector([0, 1, 2]), backend, True)
    assert result["payload"] == "UNKNOWN" and backend.calls == 1
    assert result["policy"]["reason"] == "unsupported synthesis output"
    assert result["lm_calls"] == 1 and result["executed_input_tokens"] > 0
    assert result["executed_output_tokens"] == 2
    assert result["cost"]["lm_wall_seconds"] > 0


def test_failed_lm_call_keeps_cost_and_unknown_token_receipt_without_retry():
    class BrokenBackend(Backend):
        def generate_once(self, tokens):
            self.calls += 1
            raise RuntimeError("synthetic decoder failure")

    backend = BrokenBackend()
    diagnostics = {}
    with pytest.raises(RuntimeError, match="synthetic decoder failure"):
        study.execute(messages(), Selector([0, 1, 2]), backend, False, diagnostics)
    assert backend.calls == 1 and diagnostics["lm_calls"] == 1
    assert diagnostics["executed_input_tokens"] > 0
    assert diagnostics["executed_output_tokens"] is None
    assert diagnostics["cost"]["lm_wall_seconds"] > 0


def test_cap_formula_budgets_49_requests_in_each_of_eight_workers():
    data, stages = [], []
    for n in (1, 2):
        for cell in study.CELLS:
            data.extend(
                {
                    "cell": cell,
                    "pass": n,
                    "cost": {"request_wall_seconds": 2, "request_cpu_seconds": 3},
                }
                for _ in range(5)
            )
            stages.append({"cell": cell, "pass": n, "wall_seconds": 20, "cpu_seconds": 35})
    caps = study.propose_caps(data, stages, 5, 7)
    assert caps["request_wall_seconds"] == 4
    assert caps["request_cpu_seconds"] == 6
    assert caps["cell_pass_wall_seconds"] == 20 + 49 * 4
    assert caps["cell_pass_cpu_seconds"] == 40 + 49 * 6
    assert caps["overall_wall_seconds"] == 8 * 216 + 120
    assert caps["overall_cpu_seconds"] == 8 * 334 + 168


@pytest.mark.parametrize("mutation", ["subset", "duplicate", "gold", "registered"])
def test_rehearsal_rejects_benchmark_cases_and_annotations(mutation):
    cases = [{"id": f"disposable-{i}", "disposable": True, "messages": [{}] * 32} for i in range(4)]
    if mutation == "subset":
        cases.pop()
    elif mutation == "duplicate":
        cases[-1] = cases[0]
    elif mutation == "gold":
        cases[0]["expected"] = "oracle"
    else:
        cases[0]["disposable"] = False
    with pytest.raises(ValueError):
        study.validate_cases(cases)


def test_pair_audit_rejects_source_or_prompt_drift(tmp_path):
    for cell, value in (("T-LM", 1), ("T-P", 2)):
        folder = tmp_path / "pass-1" / cell
        folder.mkdir(parents=True)
        row = {"failure": None, "case": "same", "manifest": value}
        (folder / "requests.jsonl").write_text(json.dumps(row) + "\n")
    with pytest.raises(IntegrityError, match="evidence/prompt drift"):
        study.check_pairs(tmp_path)
