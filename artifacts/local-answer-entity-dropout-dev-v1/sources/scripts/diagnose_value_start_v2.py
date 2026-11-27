"""Reconstruct crossed v2 failures using saved development evidence only."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import audit_value_start_replication_v2 as audit

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-entity-dropout-dev-v1"


def diagnose() -> dict[str, Any]:
    integrity = audit.audit()
    labels = audit.read(audit.RUN / "dev-labels.json")
    train = audit.read(audit.RUN / "train-labels.json")
    cells, failures = {}, []
    for directory in sorted((audit.RUN / "registered/execution/stages").glob("development-*")):
        key = directory.name.removeprefix("development-")
        inputs = audit.read(audit.RUN / "dev-inputs.json")
        raw = audit.rows(directory / "predictions-main.jsonl")
        question = audit.rows(directory / "predictions-question-only.jsonl")
        measured = audit.rows(directory / "first-measurements.jsonl")
        score = audit.scores(raw, inputs, labels)
        causes: Counter[str] = Counter()
        for p, q, m, label in zip(raw[:-1], question[:-1], measured[:-1], labels, strict=True):
            ids = p["result"]["generated_ids"]
            f = audit.flags(ids, label["gold"])
            if f["exact"]:
                continue
            entity, field, value, query = label["canonical"]
            seen_values = sorted(
                {
                    t["gold"]
                    for t in train
                    if t["canonical"][0] == entity and t["category"] == label["category"]
                }
            )
            answer = p["result"]["answer"]
            cause = "wrong-valid-value" if not f["malformed"] else "malformed-first-token"
            causes[cause] += 1
            failures.append(
                dict(
                    cell=key,
                    id=label["id"],
                    category=label["category"],
                    template=label["template"],
                    canonical=label["canonical"],
                    prefix=p["prefix"],
                    gold=label["gold"],
                    generated_ids=ids,
                    answer=answer,
                    flags=f,
                    expected_first_id=m["expected_first_id"],
                    predicted_first_id=m["predicted_first_id"],
                    expected_rank=m["expected_rank"],
                    margin=m["expected_minus_predicted_margin"],
                    original_entity_training_values=seen_values,
                    chose_entity_training_value=answer in seen_values,
                    question_only_same_first=q["result"]["generated_ids"][0] == ids[0],
                    primary_cause=cause,
                )
            )
        cells[key] = dict(
            exact=score["exact"],
            categories=score["categories"],
            eos=score["eos"],
            malformed=score["malformed"],
            wrong_first=score["wrong_first"],
            repetition=score["repetition"],
            primary_causes=dict(causes),
        )
    assert len(cells) == 16 and len(failures) == 34
    assert all(
        f["flags"]["wrong_first"] and f["expected_rank"] > 1 and f["margin"] < 0 for f in failures
    )
    summary = dict(
        failures=len(failures),
        all_begin_at_first_answer_token=True,
        chose_entity_training_value=sum(f["chose_entity_training_value"] for f in failures),
        question_only_same_first=sum(f["question_only_same_first"] for f in failures),
        eos_failures=sum(not f["flags"]["eos"] for f in failures),
        malformed=sum(f["flags"]["malformed"] for f in failures),
        by_template=dict(Counter(f["template"] for f in failures)),
        by_case=dict(Counter(f["id"] for f in failures)),
        scorer_rejected_correct_complete_answers=0,
        training_mastery_all_16=True,
    )
    return dict(
        integrity=integrity,
        cells=cells,
        failures=failures,
        summary=summary,
        measured_cause="Wrong first-token preferences; some suffix/termination failures follow",
        hypothesis="Entity/value training correlations may encourage shortcuts over local copying",
        causal_identification=False,
        model_forwards=0,
        heldout_opened=False,
    )


def main() -> None:
    RUN.mkdir(exist_ok=True)
    result = diagnose()
    with (RUN / "saved-v2-diagnosis.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    lines = [
        "| Cell | Case | Gold | Raw IDs | Rank | Gold-top | Seen entity value | EOS |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    lines += [
        f"| {f['cell']} | {f['id']} | {f['gold']} | `{f['generated_ids']}` | "
        f"{f['expected_rank']} | {f['margin']:.6f} | {f['chose_entity_training_value']} | "
        f"{f['flags']['eos']} |"
        for f in result["failures"]
    ]
    with (RUN / "saved-v2-failures.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines) + "\n")
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
