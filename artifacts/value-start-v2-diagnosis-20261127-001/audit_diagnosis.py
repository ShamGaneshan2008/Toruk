"""Read-only v2 diagnosis, with complete cases and paired regressions; no model imports.

Recheck with .venv/Scripts/python.exe -I -S -B <this file> --verify-only.
Outputs are exclusive files in this new report directory, never in frozen evidence.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
RUN = ROOT / "artifacts/local-answer-value-start-replication-v2"
READS = set()
VERIFY_ONLY = sys.argv[1:] == ["--verify-only"]
if sys.argv[1:] not in ([], ["--verify-only"]):
    raise SystemExit("usage: audit_diagnosis.py [--verify-only]")


def guard(event, args):
    if event == "import" and args[0].split(".")[0] in {
        "torch",
        "transformers",
        "ollama",
        "toruk_lm",
        "requests",
    }:
        raise RuntimeError("Model/network imports forbidden in saved-only diagnosis")
    if event != "open" or isinstance(args[0], int):
        return
    path = Path(args[0]).resolve()
    if any(term in str(path).lower() for term in ("heldout", "held-out", "held_out")):
        raise RuntimeError("Held-out access forbidden")
    flags = args[2] or 0
    writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
    if writing:
        if not path.is_relative_to(OUT):
            raise RuntimeError("Writes outside new report directory forbidden")
    else:
        READS.add(str(path))


sys.addaudithook(guard)
sys.path.insert(0, str(ROOT / "scripts"))
import diagnose_value_start_v2 as existing  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(name, value):
    if VERIFY_ONLY:
        assert read(OUT / name) == value, name
        return
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def semantics(split):
    inputs, labels = (read(RUN / f"{split}-{kind}.json") for kind in ("inputs", "labels"))
    result = {}
    for case, label in zip(inputs, labels, strict=True):
        lines = case["prefix"].splitlines(keepends=True)
        assert len(lines) == 3 and len(lines[0].encode()) + 1 == 32
        lhs, value = lines[1].strip().split("=")
        left, right = lhs.split()
        template = "A" if left in {"bek", "dov", "ral", "sun"} else "B"
        entity, field = (left, right) if template == "A" else (right, left)
        assert lines[2].endswith("?=")
        left, right = lines[2][:-2].split()
        queried_entity, query = (left, right) if template == "A" else (right, left)
        assert entity == queried_entity
        gold = value if field == query else "?"
        category = field if field == query else "unknown"
        assert case["id"] == label["id"]
        assert [entity, field, value, query] == label["canonical"]
        assert gold == label["gold"] and category == label["category"]
        assert template == label["template"]
        assert len(case["prefix"].encode()) + len(gold.encode()) + 2 <= 64
        result[case["id"]] = dict(
            gold=gold,
            category=category,
            evidence_and_query_in_second_segment=True,
            canonical=label["canonical"],
            template=template,
        )
    return result


def main():
    diagnosis = existing.diagnose()  # Call the read-only function, never its historical writer.
    integrity = diagnosis["integrity"]
    assert integrity == read(RUN / "independent-audit.json")
    prior = read(ROOT / "artifacts/local-answer-entity-dropout-dev-v1/saved-v2-diagnosis.json")
    assert diagnosis["summary"] == prior["summary"]
    assert diagnosis["failures"] == prior["failures"]
    source_checks = {split: semantics(split) for split in ("train", "dev")}
    train_keys = {tuple(row["canonical"]) for row in source_checks["train"].values()}
    dev_keys = {tuple(row["canonical"]) for row in source_checks["dev"].values()}
    assert not train_keys & dev_keys
    vectors_verified = 0
    max_teacher_difference = 0.0
    for cell in integrity["cells"].values():
        assert cell["training"]["metrics"]["exact"] == 96
        for phase, split in (("evaluate", "train"), ("development", "dev")):
            key = (
                f"i{cell['initialization_seed']}-s{cell['shuffle_seed']}"
                f"-{cell['model']}-{cell['objective']}"
            )
            directory = RUN / "registered/execution/stages" / f"{phase}-{key}"
            raw = existing.audit.rows(directory / "predictions-main.jsonl")
            for row in raw[:-1]:
                ids = row["result"]["generated_ids"]
                assert 2 not in ids or ids.index(2) == len(ids) - 1
                answer = bytes(i - 3 for i in ids if 3 <= i < 259).decode("utf-8", "replace")
                assert answer == row["result"]["answer"]
                expected = [b + 3 for b in source_checks[split][row["id"]]["gold"].encode()] + [2]
                assert existing.audit.flags(ids, source_checks[split][row["id"]]["gold"])[
                    "exact"
                ] == (ids == expected)
            observation = cell["training" if split == "train" else "development"]
            vectors_verified += observation["vectors"]
            max_teacher_difference = max(
                max_teacher_difference, observation["teacher_prefix_ce_max_difference"]
            )
    pairs = []
    for crossed in ("i601-s1301", "i601-s1709", "i947-s1301", "i947-s1709"):
        for model in ("ordinary", "recurrent"):
            key = f"{crossed}-{model}"
            u, c = [
                integrity["cells"][f"{key}-{arm}"]["development"]["metrics"]
                for arm in ("uniform", "first16")
            ]
            old = {r["id"]: r["exact"] for r in u["cases"]}
            new = {r["id"]: r["exact"] for r in c["cases"]}
            fixed = [i for i in old if not old[i] and new[i]]
            introduced = [i for i in old if old[i] and not new[i]]
            delta = c["exact"] - u["exact"]
            assert delta == len(fixed) - len(introduced) == integrity["per_pair_dev_gains"][key]
            pairs.append(
                dict(
                    cell=key,
                    uniform=u["exact"],
                    first16=c["exact"],
                    delta=delta,
                    fixed=fixed,
                    introduced=introduced,
                    uniform_categories=u["categories"],
                    first16_categories=c["categories"],
                    uniform_eos=u["eos"],
                    first16_eos=c["eos"],
                    first16_floor=existing.audit.floor(c),
                    uniform_malformed=u["malformed"],
                    first16_malformed=c["malformed"],
                    uniform_context_gain=u["known_context_gain"],
                    first16_context_gain=c["known_context_gain"],
                )
            )
    for f in diagnosis["failures"]:
        assert source_checks["dev"][f["id"]]["gold"] == f["gold"]
        f["classification"] = dict(
            data="verified consistent label and supplied local evidence",
            first_token="verified incorrect allowed argmax; gold rank >1 and negative margin",
            training=(
                "training mastery verified; optimization cause of generalization error unidentified"
            ),
            decoding=(
                "first-token implementation/replay consistent; malformed/EOS flags are additional "
                "symptoms"
            ),
            scoring="verified strict native byte-plus-EOS mismatch",
            integrity="verified original source/data/checkpoint/stage seals and closed accounting",
            entity_shortcut=(
                "hypothesis only; matching a seen entity value does not establish causation"
            ),
        )
    write("diagnosis.json", diagnosis)
    write(
        "comparison.json",
        dict(
            pairs=pairs,
            source_checks=source_checks,
            vectors_verified=vectors_verified,
            max_teacher_prefix_ce_difference=max_teacher_difference,
        ),
    )
    lines = [
        "# Value-start v2 saved-record diagnosis — 27 November 2026",
        "",
        "Decision: **STOP_DEVELOPMENT_FAILURE**. Integrity: **PASS**.",
        "",
        "Recomputed with the unchanged independent auditor. Zero model forwards, training, "
        "or held-out access. Training mastery is 96/96 in all sixteen cells; "
        "48 stage seals and 24,576 recorded updates verify. All 34 development failures "
        "start at the first byte (eight first16; 26 uniform). Five malformed outputs and "
        "one EOS failure are additional symptoms, not evidence of a scorer defect.",
        "",
        "## Every failed primary development prediction",
        "",
        "Crossed IDs encode initialization and shuffle separately. Answers are JSON strings: "
        "`\\n` denotes a literal newline. EOS and format are independently checked. "
        "Every row has consistent data/evidence, wrong allowed argmax, correct mismatch scoring, "
        "and passing integrity. Its specific optimization cause remains unidentified.",
        "",
        "| Cell | Case | Expected | Actual | Gold rank | Gold − top | EOS | Malformed |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for f in diagnosis["failures"]:
        lines.append(
            f"| {f['cell']} | {f['id']} | `{json.dumps(f['gold'])}` | "
            f"`{json.dumps(f['answer'])}` | {f['expected_rank']} | {f['margin']:.6f} | "
            f"{f['flags']['eos']} | {f['flags']['malformed']} |"
        )
    lines += [
        "",
        "## Registered uniform controls",
        "",
        "| Cell | Uniform /24 | First16 /24 | Delta | Fixed cases | Introduced errors |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for p in pairs:
        lines.append(
            f"| {p['cell']} | {p['uniform']} | {p['first16']} | {p['delta']:+d} | "
            f"{', '.join(p['fixed']) or 'none'} | {', '.join(p['introduced']) or 'none'} |"
        )
    lines += [
        "",
        "Five pairs improve, two tie, one regresses. Both recurrent601 candidates "
        "fail the city and format floors; shuffle1301 also loses EOS. Ordinary601/1301 "
        "loses a correct city case. Recurrent947/1301 fixes case000 but loses case012 "
        "despite unchanged net accuracy. The registered strict-positive-all-eight gate "
        "remains failed; no ceiling exception is applied retroactively.",
        "",
        "## Cause boundaries",
        "",
        "All 120 train/development labels independently agree with their assignment/query "
        "text, all needed evidence fits segment2, and canonical train/dev overlap is zero. "
        f"All {vectors_verified} saved first-logit vectors (including replays) match "
        "recorded greedy first IDs; raw decoding and scoring also agree. The largest "
        f"teacher-prefix CE difference is {max_teacher_difference:.12g}.",
        "",
        "Twenty-two failures emit a value seen for the same entity/category during "
        "training. Entity/value shortcuts are plausible, not causally established. "
        "Templates have 21/13 failures but differ in canonical cases, so template effects "
        "are confounded. Three failures share the question-only first byte; this does "
        "not establish complete disregard of evidence. Forcing a correct first byte "
        "was not tested and cannot be assumed to fix suffixes or termination.",
        "",
        "This is a local-combination generalization failure, not a demonstrated distant-"
        "memory bottleneck. The later entity-dropout study also failed its own gate; "
        "it is preserved and is not proposed again. See `proposal.md` for the one "
        "prospective objective intervention. Reused dev cases make that proposal an "
        "adaptive development repair study, not independent generalization evidence.",
        "",
    ]
    report = "\n".join(lines)
    if VERIFY_ONLY:
        assert (OUT / "report.md").read_text(encoding="utf-8") == report
    else:
        with (OUT / "report.md").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(report)
    starting = read(OUT / "starting-state.json")
    for relative, expected in starting["files"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    if not VERIFY_ONLY:
        write(
            "access-record.json",
            dict(
                model_imports_forbidden=True,
                heldout_paths_forbidden=True,
                writes_confined_to_report_directory=True,
                named_inputs_unchanged=len(starting["files"]),
                read_paths=sorted(READS),
            ),
        )
    print(
        json.dumps(
            dict(
                decision=integrity["decision"],
                integrity=integrity["measurement_integrity"],
                failure_count=len(diagnosis["failures"]),
                pairs=pairs,
                vectors_verified=vectors_verified,
                model_forwards=0,
                heldout_opened=False,
                named_inputs_unchanged=len(starting["files"]),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
