"""Classify every saved v1 development output; never generate or revise a score."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/answer-trainability-dev-v1"
VALUES = {"la", "mi", "so", "tu", "R-7", "Q_2", "?"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def diagnose():
    train = read(RUN / "train-documents.json")
    inputs, labels = read(RUN / "dev-inputs.json"), read(RUN / "dev-labels.json")
    prior = defaultdict(set)
    for doc in train:
        if doc["gold"] != "?":
            prior[doc["prefix"].splitlines()[-1]].add(doc["gold"])
    cells = {}
    for path in sorted((RUN / "stages").glob("generate-dev-*/predictions.jsonl")):
        predictions = [json.loads(s) for s in path.read_text().splitlines()]
        cases = []
        for line, (prediction, case, label) in enumerate(
            zip(predictions[:-1], inputs, labels, strict=True), 1
        ):
            assert prediction["id"] == case["id"] == label["id"]
            ids = prediction["result"]["generated_ids"]
            raw = bytes(t - 3 for t in ids if t >= 3).decode("utf-8", errors="strict")
            exact = ids == [*(b + 3 for b in label["gold"].encode()), 2]
            eos = bool(ids and ids[-1] == 2)
            closed = eos and raw in VALUES and ids == [*(b + 3 for b in raw.encode()), 2]
            primary = (
                "correct"
                if exact
                else "eos_failure"
                if not eos
                else "wrong_value"
                if closed
                else "malformed_closed"
            )
            history, query = case["prefix"].rsplit("\n", 1)
            assignment = history.splitlines()[-1]
            source_value = assignment.split("=", 1)[1]
            cases.append(
                dict(
                    id=case["id"],
                    category=label["category"],
                    gold=label["gold"],
                    generated_ids=ids,
                    raw=raw,
                    primary=primary,
                    eos=eos,
                    malformed=not closed,
                    known_source_missing=label["gold"] != "?"
                    and assignment.split("=", 1)[0] != query[:-2],
                    verified_other_entity_confusion=(
                        not exact
                        and closed
                        and assignment.split()[0] != query.split()[0]
                        and raw == source_value
                    ),
                    verified_other_attribute_copy=not exact
                    and label["gold"] == "?"
                    and closed
                    and raw == source_value,
                    unsupported_unknown=not exact and label["gold"] == "?",
                    training_query_value_match=not exact and closed and raw in prior[query],
                    query_seen_in_training=query in {d["prefix"].splitlines()[-1] for d in train},
                    source=f"{path.relative_to(ROOT).as_posix()}:{line}",
                )
            )
        counts = dict(Counter(c["primary"] for c in cases))
        cells[path.parent.name.removeprefix("generate-dev-")] = dict(
            counts=counts,
            cases=cases,
            prior_matches=sum(c["training_query_value_match"] for c in cases),
            unknown_failures=sum(c["unsupported_unknown"] for c in cases),
        )

    def core(prefix):
        return "\n".join(prefix.splitlines()[-2:])

    overlap = dict(
        ids=len({d["id"] for d in train} & {c["id"] for c in inputs}),
        complete_texts=len(
            {d["text"] for d in train}
            & {c["prefix"] + label["gold"] for c, label in zip(inputs, labels, strict=True)}
        ),
        assignment_query_cores=len(
            {core(d["prefix"]) for d in train} & {core(c["prefix"]) for c in inputs}
        ),
        development_cases_with_seen_question=sum(
            c["prefix"].splitlines()[-1] in {d["prefix"].splitlines()[-1] for d in train}
            for c in inputs
        ),
        single_question_template_in_both_splits=True,
    )
    totals = Counter()
    for cell in cells.values():
        totals.update(cell["counts"])
    assert totals == dict(correct=49, wrong_value=68, malformed_closed=4, eos_failure=7)
    return dict(
        scope="16 development cases x 8 cells = 128 saved predictions; 79 failures",
        counts=dict(totals),
        overlap=overlap,
        cells=cells,
        training_or_generation_executed=False,
        attribution_limit=(
            "One source entity; closed wrong values do not establish entity/field confusion"
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = diagnose()
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(
        json.dumps({key: value for key, value in result.items() if key != "cells"}, sort_keys=True)
    )
    for name, cell in result["cells"].items():
        print(name, cell["counts"], "prior matches", cell["prior_matches"])
