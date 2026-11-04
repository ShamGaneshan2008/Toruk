"""Independent-case contracts, actual request accounting and drift rejection."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import independent_cases as data  # noqa: E402
import independent_replication as experiment  # noqa: E402
import report_independent_replication as report  # noqa: E402


def test_independent_assembly_is_repeatable_bounded_and_preserves_sources() -> None:
    cards = json.loads(data.CARDS.read_text(encoding="utf-8"))
    cases = data.assemble(cards)
    assert cases == data.assemble(cards)
    changed = data.assemble(cards, seed=912)
    assert cases != changed
    for card, case, other in zip(cards, cases, changed, strict=True):
        assert [case["messages"][i] for i in case["evidence"]] == card["events"]
        assert case["messages"][-1] == other["messages"][-1]
        assert case["groups"] == other["groups"]
        assert case["trailing_gap_pairs"] >= 18
    assert any(case["messages"][case["evidence"][0]]["role"] == "assistant" for case in cases)


def test_validation_rejects_short_gaps_and_duplicate_scenarios() -> None:
    cases = data.build()
    messages = cases[0]["messages"]
    cases[0]["messages"] = messages[: cases[0]["evidence"][-1] + 2] + [messages[-1]]
    with pytest.raises(ValueError, match="18 trailing"):
        data.validate(cases)
    cases = data.build()
    cases[-1]["id"] = cases[0]["id"]
    with pytest.raises(ValueError, match="unique"):
        data.validate(cases)


def test_leakage_audit_rejects_normalized_task_text(tmp_path: Path, monkeypatch: Any) -> None:
    cases = data.build()
    text = cases[0]["messages"][cases[0]["evidence"][0]]["content"].upper()
    path = tmp_path / "old.json"
    path.write_text(json.dumps([{"messages": [{"content": "  " + text + "  "}]}]))
    monkeypatch.setattr(data, "historical_paths", lambda: [path])
    monkeypatch.setattr(data, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="historical text overlap"):
        data.leakage_audit(cases)


def test_registered_data_and_dependencies_cannot_drift(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("original")
    dataset = tmp_path / "cases.json"
    dataset.write_text("[]")
    manifest = {
        "bindings": {source.as_posix(): data.sha(source)},
        "datasets": {"cases.json": data.sha(dataset)},
    }
    (tmp_path / "registration.json").write_text(json.dumps(manifest))
    experiment.verify(tmp_path)
    dataset.write_text("[1]")
    with pytest.raises(ValueError, match="dataset drift"):
        experiment.verify(tmp_path)
    dataset.write_text("[]")
    source.write_text("changed")
    with pytest.raises(ValueError, match="dependency drift"):
        experiment.verify(tmp_path)


def test_existing_evaluation_output_is_rejected_before_model_loading(tmp_path: Path) -> None:
    output = tmp_path / "independent.jsonl"
    output.write_text("original\n")
    with pytest.raises(ValueError, match="existing evaluation"):
        experiment.evaluate(tmp_path, "independent")
    assert output.read_text() == "original\n"


class Tokenizer:
    eos_token_id = 0
    pad_token_id = 0

    def apply_chat_template(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        text = "\n".join(m["role"] + ": " + m["content"] for m in messages)
        return {"input_ids": torch.tensor([[ord(c) for c in text]])}

    def decode(self, ids: list[int], **kwargs: Any) -> str:
        return "".join(chr(i) for i in ids)


class Model:
    def generate(self, **kwargs: Any) -> torch.Tensor:
        assert set(kwargs) == {
            "input_ids",
            "max_new_tokens",
            "do_sample",
            "eos_token_id",
            "pad_token_id",
            "use_cache",
        }
        self.received = kwargs
        return torch.cat((kwargs["input_ids"], torch.tensor([[111, 107]])), dim=1)


def test_actual_request_instrumentation_counts_work_without_gold_inputs() -> None:
    backend = experiment.MeasuredBackend.__new__(experiment.MeasuredBackend)
    backend.tokenizer = Tokenizer()
    backend.model = Model()
    backend.system_prompt = ""
    backend.model_id = backend.backbone_id = "explicit-test-double"
    backend.selector = None
    experiment.instrument(backend, {"recent": None})
    backend.reset_measurements()
    messages = [{"role": "user", "content": "question"}]
    response = backend.reply_with_metrics(messages, 48, mode="BASELINE")
    assert response["answer"] == "ok"
    assert backend.generated_ids == [111, 107]
    assert backend.work["fit_attempts"] == 1
    assert backend.work["history_token_positions"] == backend.work["fit_token_positions"]
    assert backend.work["history_token_positions"] == response["metrics"]["input_tokens"]
    assert backend.prompt_ids == backend.model.received["input_ids"][0].tolist()
    assert backend.chosen == [0] and backend.before == [0]


def test_ablations_keep_capacity_and_only_remove_the_named_choices() -> None:
    selectors = experiment.methods()
    messages = [{"role": "user", "content": f"entry {i}"} for i in range(12)]
    assert selectors["toruk"].select(messages) == selectors["no_envelope"].select(messages)
    assert selectors["no_learned_rank"].select(messages)[0] == [7, 8, 9, 10, 11]
    assert isinstance(selectors["restore_cutoff"].selector, experiment.study.ChatRelevanceSelector)
    assert selectors["restore_cutoff"].selector.threshold == 0.2


def test_paired_intervals_and_wilson_account_for_small_samples() -> None:
    a = [
        {"case": {"id": str(i)}, "correct": True, "metrics": {"response_ms": 10}} for i in range(3)
    ]
    b = [
        {"case": {"id": str(i)}, "correct": False, "metrics": {"response_ms": 20}} for i in range(3)
    ]
    interval = report.paired_interval(a, b)
    assert interval["quality_delta_95"] == [1, 1]
    assert interval["latency_saving_fraction_95"] == [0.5, 0.5]
    low, high = report.wilson(3, 3)
    assert 0 < low < 1 and high == 1
    with pytest.raises(ValueError, match="Unpaired"):
        report.paired_interval(a, b[:2])


def test_ci_validation_cli_does_not_need_backbone_weights(tmp_path: Path) -> None:
    path = tmp_path / "validation"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "independent_replication.py"),
            "validate-cases",
            "--run",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    saved = json.loads((path / "validation.json").read_text())
    assert saved["n"] == 24 and "no backbone inference" in saved["scope"]
