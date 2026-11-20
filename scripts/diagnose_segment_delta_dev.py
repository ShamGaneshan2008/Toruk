"""Read saved segment-delta-v1 evidence; never fit, forward, decode anew, or write files."""

import argparse
import hashlib
import json
import math
import runpy
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/segment-delta-dev-v1"
REGISTRATION = "bb828757efe6f4073d7d1c74405aa7c73120e11fcfdfff6c09b8a95812e1d2dd"
LOCK = "8711afee882f4e4837e4048a878447c1d1706220ca72faa7ed5270c07e878984"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def classify(ids, gold, score, inventory):
    """Conservative surface labels; malformed text does not establish a memory error."""
    if score(ids, gold):
        return "correct"
    if not ids or ids == [2]:
        return "empty"
    expected = [b + 3 for b in gold.encode()]
    tail = ids[len(expected) :]
    # A whole leading answer followed by whitespace/termination is distinguishable
    # from accidental interior bytes (e.g. 'la' in 'ralai'). This is not a new score.
    if ids[: len(expected)] == expected and (not tail or tail[0] in (2, 12, 13, 16, 35)):
        return "answer_present_rejected"
    if any(ids == [*(b + 3 for b in value.encode()), 2] for value in inventory):
        return "wrong_value"
    return "malformed"


def audit(checkpoints=False, include_cases=False):
    require(sha(RUN / "registration.json") == REGISTRATION, "registration changed")
    require(sha(RUN / "implementation-lock.json") == LOCK, "implementation lock changed")
    reg, lock = read(RUN / "registration.json"), read(RUN / "implementation-lock.json")
    for filename, expected in reg["data"].items():
        require(sha(RUN / filename) == expected, f"data changed: {filename}")
    for snapshot, mapping in (
        ("protocol-sources", reg["source_files"]),
        ("implementation-sources", lock["sources"]),
    ):
        for filename, expected in mapping.items():
            require(sha(RUN / snapshot / filename) == expected, f"snapshot changed: {filename}")
    # Import only the sealed, stdlib-only scorer/validator, without invoking main.
    data = runpy.run_path(str(RUN / "implementation-sources/scripts/segment_delta_data.py"))
    score = data["score"]
    train, inputs, labels, prose = [
        read(RUN / name)
        for name in ("train.json", "inputs.json", "labels-evaluator-only.json", "dev-prose.json")
    ]
    data["validate"](train, inputs, labels, prose)
    require(score([111, 100, 2], "la"), "scorer positive control")
    require(not score([111, 100], "la"), "scorer requires EOS")
    require(not score([35, 111, 100, 2], "la"), "scorer preserves whitespace")
    require(not score([111, 100, 35, 2], "la"), "scorer rejects extra output")
    by_id = {d["id"]: d for d in train}
    inventory = set(data["VALUES"]) | set(data["CODES"]) | {"?"}
    result = dict(
        seals="PASS",
        split_validation="PASS (IDs, complete texts, last-assignment labels, bounds)",
        training={},
        cells={},
        data=dict(
            train_documents=len(train),
            train_targets=sum(len(d["text"].encode()) + 1 for d in train),
            train_answer_targets_including_eos=sum(
                len(d["text"].rsplit("?=", 1)[1].encode()) + 1 for d in train if "?=" in d["text"]
            ),
            development_gold_lengths_with_eos=dict(
                Counter(len(label["gold"].encode()) + 1 for label in labels)
            ),
        ),
    )
    for seed in (113, 227):
        reference = None
        for variant in ("ordinary", "recurrent", "delta"):
            directory = RUN / "stages" / f"train-{seed}-{variant}"
            trace, stats = (
                rows(directory / "checkpoint.trace.jsonl"),
                read(directory / "training.json"),
            )
            require(len(trace) == 128 and trace == stats["trace"], "training trace mismatch")
            require(stats["gradient_parameters"] == stats["parameters"], "missing saved gradients")
            require([r["step"] for r in trace] == list(range(1, 129)), "training steps")
            signature = [(r["ids"], r["targets"]) for r in trace]
            if reference is None:
                reference = signature
            require(signature == reference, "unmatched exposure")
            for row in trace:
                require(math.isfinite(row["nll"]), "nonfinite training loss")
                require(len(row["ids"]) == 2, "training batch")
                require(
                    row["targets"] == sum(len(by_id[i]["text"].encode()) + 1 for i in row["ids"]),
                    "training target count",
                )
            presented = [by_id[i] for row in trace for i in row["ids"]]
            factual = [d for d in presented if "?=" in d["text"]]
            targets = sum(row["targets"] for row in trace)
            require(targets == stats["targets"], "training total")
            entry = dict(
                targets=targets,
                documents=len(presented),
                unique_documents=len({d["id"] for d in presented}),
                factual_presentations=len(factual),
                answer_targets_including_eos=sum(
                    len(d["text"].rsplit("?=", 1)[1].encode()) + 1 for d in factual
                ),
                nll_first=trace[0]["nll"],
                nll_last=trace[-1]["nll"],
                nll_blocks16=[
                    statistics.fmean(r["nll"] for r in trace[i : i + 16]) for i in range(0, 128, 16)
                ],
            )
            if checkpoints:
                import torch

                from toruk_lm.segment_delta_training import load

                # Strict reload only: no forward pass, optimizer step, or RNG restoration.
                for filename, expected in lock["sources"].items():
                    require(sha(ROOT / filename) == expected, f"loader source changed: {filename}")
                path = directory / "checkpoint.pt"
                meta = read(directory / "checkpoint-meta.json")
                require(sha(path) == meta["sha256"], "checkpoint hash")
                require(path.stat().st_size == meta["bytes"], "checkpoint size")
                identity = dict(
                    registration=REGISTRATION,
                    implementation=LOCK,
                    train=reg["data"]["train.json"],
                    runtime=json.dumps(reg["runtime"], sort_keys=True),
                )
                model, _, saved = load(path, identity)
                require(saved["variant"] == variant and saved["fit"]["seed"] == seed, "wrong cell")
                require(saved["next_step"] == 128 and saved["targets"] == targets, "wrong progress")
                require(saved["config"] == reg["config"], "wrong config")
                require(saved["tokenizer"] == reg["tokenizer"]["fingerprint"], "wrong tokenizer")
                require(
                    saved["data_digest"]
                    == hashlib.sha256(json.dumps(train, sort_keys=True).encode()).hexdigest(),
                    "wrong training documents",
                )
                require(
                    all(torch.equal(v, saved["model"][k]) for k, v in model.state_dict().items()),
                    "loaded tensors differ",
                )
                entry["strict_checkpoint_reload"] = "PASS (weights/moments/identities; no forward)"
                entry["checkpoint_sha256"] = meta["sha256"]
            result["training"][f"{seed}-{variant}"] = entry
    for name in [*sorted(read(RUN / "summary.json")["cells"]), "lexical"]:
        directory = RUN / "stages" / (name if name == "lexical" else f"generate-{name}")
        path = directory / "predictions.jsonl"
        require(sha(path) == read(directory / "generation-seal.json")["sha256"], "prediction seal")
        predictions = rows(path)
        require(len(predictions) == 25, "request count")
        require(
            [p["replay"] for p in predictions] == [False] * 24 + [True]
            and predictions[0]["result"] == predictions[-1]["result"],
            "replay mismatch",
        )
        cases = []
        for line, (p, case, label) in enumerate(
            zip(predictions[:24], inputs, labels, strict=True), 1
        ):
            require(p["id"] == case["id"] == label["id"], "case order")
            require(p["prefix"] == case["prefix"], "changed prompt")
            require(p["result"]["input_ids"] == [1, *(b + 3 for b in p["prefix"].encode())], "IDs")
            ids = p["result"]["generated_ids"]
            require(all(type(t) is int and 2 <= t < 259 for t in ids), "output ID range")
            raw = bytes(t - 3 for t in ids if t >= 3)
            prefix_bytes = p["prefix"].encode()
            tail_length = (len(prefix_bytes) + 1) % 24 or 24
            # Every v1 development input exceeds one segment. This is a byte
            # slice of saved input, not a new model execution or answer.
            first_context = prefix_bytes[-tail_length:].decode("utf-8", errors="strict")
            cases.append(
                dict(
                    id=case["id"],
                    category=label["category"],
                    gold=label["gold"],
                    raw=raw.decode("utf-8", errors="strict"),
                    ids=ids,
                    eos=2 in ids,
                    failure=classify(ids, label["gold"], score, inventory),
                    gold_substring=label["gold"].encode() in raw,
                    first_answer_context=first_context,
                    input_phase=(len(prefix_bytes) + 1) % 24,
                    source=f"{path.relative_to(ROOT).as_posix()}:{line}",
                )
            )
        cell = dict(
            classifications=dict(Counter(c["failure"] for c in cases)),
            eos=sum(c["eos"] for c in cases),
            gold_substrings=sum(c["gold_substring"] for c in cases),
            by_benchmark_category={
                category: dict(Counter(c["failure"] for c in cases if c["category"] == category))
                for category in data["CATEGORIES"]
            },
        )
        if name != "lexical":
            loss_directory = RUN / "stages" / f"score-{name}"
            saved_losses = rows(loss_directory / "losses.jsonl")
            require(len(saved_losses) == 32, "loss document count")
            losses = saved_losses[:24]
            require(
                [r["correct"] for r in losses] == [c["failure"] == "correct" for c in cases],
                "saved evaluator disagrees with frozen scorer",
            )
            for loss, case, label in zip(losses, inputs, labels, strict=True):
                require(loss["id"] == case["id"] == label["id"], "loss case order")
                require(loss["gold"] == label["gold"], "loss gold")
                require(loss["answer_targets"] == len(label["gold"].encode()) + 1, "suffix count")
                require(
                    loss["targets"] == len((case["prefix"] + label["gold"]).encode()) + 1,
                    "factual count",
                )
            totals = read(loss_directory / "loss-summary.json")
            for kind, records, loss_key, count_key in (
                ("factual", losses, "loss", "targets"),
                ("answer", losses, "answer_loss", "answer_targets"),
                ("prose", saved_losses[24:], "loss", "targets"),
            ):
                require(
                    math.isclose(sum(r[loss_key] for r in records), totals[kind + "_loss"])
                    and sum(r[count_key] for r in records) == totals[kind + "_targets"],
                    "loss totals",
                )
            cell["nll"] = {
                kind: totals[kind + "_loss"] / totals[kind + "_targets"]
                for kind in ("factual", "answer", "prose")
            }
            require(all(len(c["ids"]) == 8 and not c["eos"] for c in cases), "termination finding")
            require(all(p["result"]["budget_exhausted"] for p in predictions), "budget flag")
        if include_cases:
            cell["cases"] = cases
        result["cells"][name] = cell
    result["strict_checkpoints_checked"] = checkpoints
    result["training_forward_or_generation_executed"] = False
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoints", action="store_true", help="Strictly reload all six; no forward"
    )
    parser.add_argument(
        "--cases", action="store_true", help="Include every saved LM/control prediction"
    )
    options = parser.parse_args()
    print(json.dumps(audit(options.checkpoints, options.cases), indent=2, sort_keys=True))
