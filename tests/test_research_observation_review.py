"""Malformed saved-record fixtures; no model fitting, inference or study edits."""

import copy
import json

import check_city_contrastive_evidence as review
import pytest


def write_rows(path, values):
    path.write_text("".join(json.dumps(v) + "\n" for v in values), encoding="utf-8")


@pytest.fixture
def observation(tmp_path):
    cost = dict(cpu=0.001, wall=0.002)
    sample = dict(
        id="disposable",
        prefix="a?=",
        input_ids=[1, 100, 66, 64],
        replay=False,
        result=dict(
            answer="la",
            generated_ids=[111, 100, 2],
            budget_exhausted=False,
            input_tokens=4,
            forward_positions=15,
            commits=0,
            allocated_state_bytes=0,
        ),
        cost=cost,
    )
    replay = copy.deepcopy(sample)
    replay["replay"] = True
    write_rows(tmp_path / "predictions-main.jsonl", [sample, replay])
    vectors = [
        dict(id=r["id"], input_ids=r["input_ids"], replay=r["replay"], logits=[0.0] * 259)
        for r in (sample, replay)
    ]
    write_rows(tmp_path / "first-vectors.jsonl", vectors)
    write_rows(
        tmp_path / "first-measurements.jsonl",
        [dict(id=r["id"], replay=r["replay"], cost=cost) for r in (sample, replay)],
    )
    write_rows(
        tmp_path / "teacher-losses.jsonl",
        [
            dict(
                id="disposable",
                cost=cost,
                history_targets=3,
                answer_targets=3,
                first_targets=1,
                forward_positions=64,
            )
        ],
    )
    ledger = dict(
        main=dict(
            requests=2,
            input_tokens=8,
            generated_tokens=6,
            forward_positions=30,
            cpu=0.002,
            wall=0.004,
        ),
        vectors=dict(requests=2, input_tokens=8, forward_positions=8),
        teacher=dict(requests=1, targets=6, forward_positions=64),
    )
    (tmp_path / "token-costs.json").write_text(json.dumps(ledger), encoding="utf-8")
    return tmp_path


def test_complete_ledgers_and_unaggregated_measurement_costs(observation):
    totals = review.verify_observation(observation)
    assert totals["main"]["generated_tokens"] == 6
    assert totals["vectors"]["cpu"] == 0.002
    assert totals["teacher"]["wall"] == 0.002
    assert "cpu" not in json.loads((observation / "token-costs.json").read_text())["vectors"]


@pytest.mark.parametrize(
    "kind",
    [
        "vector_requests",
        "vector_float_count",
        "teacher_targets",
        "teacher_work",
        "generation_cpu",
        "negative_cost",
        "nan_cost",
        "float_ids",
        "bool_ids",
        "early_eos",
        "decoded_text",
        "budget_flag",
        "replay_flag",
        "teacher_identity",
        "negative_vector_cost",
        "input_count",
    ],
)
def test_review_rejects_inconsistent_saved_records(observation, kind):
    path = observation / "token-costs.json"
    data = json.loads(path.read_text())
    if kind in ("vector_requests", "vector_float_count", "teacher_targets", "generation_cpu"):
        if kind == "vector_requests":
            data["vectors"]["requests"] += 1
        elif kind == "vector_float_count":
            data["vectors"]["input_tokens"] = 8.0
        elif kind == "teacher_targets":
            data["teacher"]["targets"] += 1
        else:
            data["main"]["cpu"] += 1
        path.write_text(json.dumps(data), encoding="utf-8")
    else:
        filename = (
            "teacher-losses.jsonl"
            if kind in ("teacher_work", "teacher_identity")
            else "first-measurements.jsonl"
            if kind == "negative_vector_cost"
            else "predictions-main.jsonl"
        )
        path = observation / filename
        raw = [json.loads(s) for s in path.read_text().splitlines()]
        if kind == "teacher_work":
            raw[0]["forward_positions"] = 32
        elif kind == "teacher_identity":
            raw[0]["id"] = "different"
        elif kind in ("negative_cost", "negative_vector_cost", "nan_cost"):
            raw[0]["cost"]["cpu"] = float("nan") if kind == "nan_cost" else -1
        elif kind == "float_ids":
            raw[0]["result"]["generated_ids"][-1] = 2.0
        elif kind == "bool_ids":
            raw[0]["input_ids"][0] = True
        elif kind == "early_eos":
            raw[0]["result"]["generated_ids"] = [111, 2, 100, 2]
        elif kind == "decoded_text":
            raw[0]["result"]["answer"] = "not the native answer"
        elif kind == "budget_flag":
            raw[0]["result"]["budget_exhausted"] = True
        elif kind == "replay_flag":
            raw[-1]["replay"] = "yes"
        elif kind == "input_count":
            raw[0]["result"]["input_tokens"] += 1
        write_rows(path, raw)
    with pytest.raises(ValueError):
        review.verify_observation(observation)


def test_offline_guard_rejects_heldout_reads_and_writes():
    with pytest.raises(ValueError, match="held-out"):
        review.read_only_guard("open", ("artifacts/heldout.json", "r", 0))
    with pytest.raises(ValueError, match="cannot write"):
        review.read_only_guard("open", ("anything.json", "w", review.os.O_WRONLY))


def test_offline_guard_rejects_model_imports():
    with pytest.raises(RuntimeError, match="Model imports"):
        review.read_only_guard("import", ("torch",))
