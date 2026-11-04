"""Independent offline development oracle and saved-output checks; no inference."""

import argparse
import json
from pathlib import Path

import value_fidelity_dev as study

from toruk_lm.tokenizer import ByteTokenizer


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run
    study.verify(run, models=True)
    dataset = json.loads((run / "development.json").read_text())
    assert dataset["role"] == "development-only" and not (run / "final.json").exists()
    oracle = {}
    for world in dataset["worlds"]:
        truth, evidence, addresses = {}, {}, []
        for i, event in enumerate(world["events"]):
            words = event["text"].rstrip(".").split()
            assert len(words) == 4
            (name,) = [w for w in words if w in ("Ada", "Ben", "Cyd")]
            (field,) = [w for w in words if w in ("color", "pet")]
            (value,) = [w for w in words if w in ("red", "blue", "green", "cat", "dog", "owl")]
            (operation,) = [w for w in words if w in ("Set", "Change", "Claim")]
            key = (name, field)
            address = ("Ada", "Ben", "Cyd").index(name) * 2 + ("color", "pet").index(field)
            addresses.append(6 if operation == "Claim" else address)
            if operation != "Claim":
                truth[key], evidence[key] = value, i
        questions = []
        for question in world["questions"]:
            words = question["query"].split()
            (name,) = [w[:-2] for w in words if w.endswith("'s")]
            (field,) = [w[:-1] for w in words if w in ("color?", "pet?")]
            key = (name, field)
            expected = truth.get(key, "?")
            relevant = [evidence[key]] if key in evidence else []
            expected_address = ("Ada", "Ben", "Cyd").index(name) * 2 + ("color", "pet").index(field)
            assert question["key"] == expected_address
            assert question["expected"] == expected and question["evidence"] == relevant
            questions.append((expected, relevant))
        oracle[world["id"]] = questions, addresses, world
    worlds = answers = 0
    correct_by_cell = {}
    files = sorted((run / "raw").glob("*.json"))
    assert len(files) == 10
    for path in files:
        raw = json.loads(path.read_text())
        method, seed = raw["method"], raw["seed"]
        checkpoint = (
            run / "train" / f"augmented-{seed}.pt"
            if method in ("augmented", "zero")
            else study.OLD / "train" / f"new-{seed}.pt"
            if method == "old"
            else study.study.q.checkpoint_for("recent", seed)
        )
        assert raw["checkpoint_sha256"] == study.file_identity(checkpoint)
        assert raw["role"] == "development-only"
        assert raw["development_sha256"] == study.file_identity(run / "development.json")
        assert raw["model_seal_sha256"] == study.file_identity(run / "models.json")
        assert len(raw["predictions"]) == len(oracle)
        assert len({p["id"] for p in raw["predictions"]}) == len(oracle)
        correct = 0
        for prediction in raw["predictions"]:
            labels, addresses, world = oracle[prediction["id"]]
            assert len(prediction["answers"]) == len(labels)
            for answer, (expected, relevant) in zip(prediction["answers"], labels, strict=True):
                assert ByteTokenizer().decode(answer["generated_ids"]) == answer["answer"]
                assert answer["expected"] == expected
                assert answer["correct"] == (answer["answer"] == expected)
                assert answer["unsupported"] == (expected == "?" and answer["answer"] != "?")
                assert answer["evidence_ingested"] == all(
                    i in answer["selected_record_ids"] for i in relevant
                )
                assert answer["evidence_suffix_exposed"] == all(
                    i in answer["suffix_record_ids"] for i in relevant
                )
                assert answer["history_tokens_scanned"] == sum(
                    len(e["text"].encode()) + 1 for e in world["events"]
                )
                assert len(answer["generated_ids"]) <= 12 and answer["selected_tokens"] <= 160
                if "write_predictions" in answer:
                    assert answer["write_correct"] == sum(
                        a == b for a, b in zip(answer["write_predictions"], addresses, strict=True)
                    )
                answers += 1
            assert prediction["correct"] == all(a["correct"] for a in prediction["answers"])
            correct += prediction["correct"]
            worlds += 1
        assert raw["totals"]["correct"] == correct
        correct_by_cell[path.stem] = correct
    print(
        json.dumps(
            {
                "status": "PASS",
                "role": "development-only",
                "world_predictions": worlds,
                "answers": answers,
                "scoring_mismatches": 0,
                "final_set_exists": False,
                "correct_by_cell": correct_by_cell,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
