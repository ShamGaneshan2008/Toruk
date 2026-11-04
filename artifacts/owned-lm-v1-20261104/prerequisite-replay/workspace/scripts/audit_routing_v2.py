"""Offline independent raw-text oracle and saved-output integrity checks."""

import argparse
import hashlib
import json
import re
import tarfile
import zipfile
from pathlib import Path

from toruk_lm.tokenizer import ByteTokenizer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    run = args.run
    worlds = {(w["id"], w["load"]): w for w in json.loads((run / "final.json").read_text())}
    independent = {}
    for identity, world in worlds.items():
        truth, evidence, addresses = {}, {}, []
        for i, event in enumerate(world["events"]):
            match = re.fullmatch(
                r"(Ada|Ben|Cyd) (red|blue|green|cat|dog|owl) (color|pet) (Set|Change|Claim)\.",
                event["text"],
            )
            assert match, event["text"]
            name, value, field, operation = match.groups()
            key = (name, field)
            address = ("Ada", "Ben", "Cyd").index(name) * 2 + ("color", "pet").index(field)
            addresses.append(6 if operation == "Claim" else address)
            if operation != "Claim":
                truth[key], evidence[key] = value, i
        questions = []
        for question in world["questions"]:
            match = re.fullmatch(r"(color|pet)\? (Ada|Ben|Cyd)'s is What", question["query"])
            assert match
            field, name = match.groups()
            key = (name, field)
            expected = truth.get(key, "?")
            assert expected == question["expected"]
            relevant = [evidence[key]] if key in evidence else []
            assert relevant == question["evidence"]
            questions.append((expected, relevant))
        independent[identity] = questions, addresses
    world_count = answer_count = 0
    files = sorted((run / "raw").glob("*.json"))
    assert len(files) == 12
    for path in files:
        raw = json.loads(path.read_text())
        predictions = raw["predictions"]
        assert len(predictions) == len(worlds)
        assert len({(p["id"], p["load"]) for p in predictions}) == len(worlds)
        for prediction in predictions:
            identity = prediction["id"], prediction["load"]
            world = worlds[identity]
            oracle, addresses = independent[identity]
            assert len(prediction["answers"]) == len(oracle)
            for answer, (expected, relevant) in zip(prediction["answers"], oracle, strict=True):
                assert ByteTokenizer().decode(answer["generated_ids"]) == answer["answer"]
                assert answer["correct"] == (answer["answer"] == expected)
                assert answer["unsupported"] == (expected == "?" and answer["answer"] != "?")
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
                answer_count += 1
            assert prediction["correct"] == all(a["correct"] for a in prediction["answers"])
            world_count += 1
    for archive in (run / "package").glob("*"):
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
        else:
            with tarfile.open(archive) as bundle:
                names = bundle.getnames()
        assert not any("/internal/" in n or n.endswith((".pt", ".safetensors")) for n in names)
    verified = 0
    if args.manifest:
        manifest = json.loads((run / "manifest.json").read_text())
        for name, digest in manifest["files"].items():
            assert hashlib.sha256((run / name).read_bytes()).hexdigest() == digest, name
            verified += 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "world_predictions": world_count,
                "answers": answer_count,
                "raw_text_oracle_mismatches": 0,
                "manifest_files_verified": verified,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
