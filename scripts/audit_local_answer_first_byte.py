"""Saved-only first-byte audit: no model construction, forward, fitting or generation."""

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts/local-answer-dev-v1"
CELLS = ("947-ordinary", "601-ordinary", "601-recurrent", "947-recurrent")
REGISTRATION = "c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(inspect_checkpoints=False):
    require(sha(RUN / "registration.json") == REGISTRATION, "registration changed")
    reg = read(RUN / "registration.json")
    for name, expected in reg["sources"].items():
        require(sha(RUN / "sources" / name) == sha(ROOT / name) == expected, name)
    for name in ("train-documents.json", "train-inputs.json", "train-labels.json"):
        require(sha(RUN / name) == reg["data"][name], "training data changed")
    documents, inputs, labels = [
        read(RUN / name)
        for name in ("train-documents.json", "train-inputs.json", "train-labels.json")
    ]
    by_id = {d["id"]: d for d in documents}
    label_by_id = {label["id"]: label for label in labels}
    predictions, losses, traces, metadata, class_counts = {}, {}, {}, {}, {}
    for cell in CELLS:
        path = RUN / "stages" / f"generate-train-{cell}" / "predictions.jsonl"
        require(sha(path) == read(path.parent / "seal.json")["sha256"], "prediction seal")
        raw = rows(path)
        require(len(raw) == 97 and raw[0]["result"] == raw[-1]["result"], "replay")
        predictions[cell] = {p["id"]: p for p in raw[:-1]}
        loss_rows = rows(RUN / "stages" / f"loss-train-{cell}" / "losses.jsonl")
        losses[cell] = {r["id"]: r for r in loss_rows}
        train_dir = RUN / "stages" / f"train-{cell}"
        trace = rows(train_dir / "training.jsonl")
        traces[cell] = trace
        seed = int(cell.split("-")[0])
        require(len(trace) == 1536, "steps")
        for step, row in enumerate(trace):
            expected = []
            for offset in range(8):
                epoch, position = divmod(step * 8 + offset, 96)
                order = list(range(96))
                random.Random(seed + epoch).shuffle(order)
                expected.append(documents[order[position]]["id"])
            require(row["ids"] == expected, "epoch-shuffled order")
            target_count = sum(len(by_id[i]["text"].encode()) + 1 for i in expected)
            require(row["history_targets"] + row["answer_targets"] == target_count, "targets")
            require(
                row["forward_positions"]
                == 8 * max(len(by_id[i]["text"].encode()) + 1 for i in expected),
                "padded positions",
            )
        for p, case in zip(raw[:-1], inputs, strict=True):
            require(p["id"] == case["id"] and p["prefix"] == case["prefix"], "case order")
            require(p["input_ids"] == [1, *(b + 3 for b in case["prefix"].encode())], "native IDs")
            require(
                not any(k in p["result"] for k in ("logits", "probabilities", "rank")),
                "new evidence schema",
            )
        meta = read(train_dir / "checkpoint-meta.json")
        stats = read(train_dir / "training-summary.json")
        checkpoint = train_dir / "checkpoint.pt"
        require(
            sha(checkpoint) == meta["sha256"] and checkpoint.stat().st_size == meta["bytes"],
            "checkpoint bytes",
        )
        require(len(list(train_dir.glob("*.pt"))) == 1, "unexpected checkpoint candidates")
        metadata[cell] = dict(**meta, **stats, payload_inspected=inspect_checkpoints)
        if inspect_checkpoints:
            import torch

            saved = torch.load(checkpoint, weights_only=True, map_location="cpu")
            require(
                saved["registration"] == REGISTRATION and saved["config"] == reg["config"],
                "checkpoint identity",
            )
            require(
                saved["steps"] == 1536
                and saved["seed"] == seed
                and saved["variant"] == cell.split("-")[1],
                "checkpoint cell/progress",
            )
            require(
                saved["initial_sha256"] == stats["initial_sha256"] and saved["targets"] == 692224,
                "checkpoint exposure",
            )
            require(
                all(float(v["step"]) == 1536 for v in saved["optimizer"]["state"].values()),
                "optimizer boundary",
            )
            require(
                all(torch.isfinite(v).all() for v in saved["model"].values()), "nonfinite weights"
            )
        class_counts[cell] = dict(
            Counter(
                chr(predictions[cell][label["id"]]["result"]["generated_ids"][0] - 3)
                for label in labels
                if label["category"] == "city"
            )
        )

    def signature(trace):
        return [
            (r["ids"], r["history_targets"], r["answer_targets"], r["forward_positions"])
            for r in trace
        ]

    require(
        signature(traces["947-ordinary"]) == signature(traces["947-recurrent"]),
        "947 exposure mismatch",
    )
    require(
        signature(traces["601-ordinary"]) == signature(traces["601-recurrent"]),
        "601 exposure mismatch",
    )
    failed = []
    slots, cooccurrences = defaultdict(Counter), Counter()
    paired_batches = Counter()
    for row in traces["947-ordinary"]:
        values = defaultdict(set)
        for slot, identity in enumerate(row["ids"]):
            slots[identity][slot] += 1
            if label_by_id[identity]["category"] == "city":
                values[by_id[identity]["prefix"].splitlines()[-1]].add(by_id[identity]["gold"])
        for query, golds in values.items():
            if len(golds) == 2:
                paired_batches[query] += 1
        for identity in row["ids"]:
            if (
                label_by_id[identity]["category"] == "city"
                and len(values[by_id[identity]["prefix"].splitlines()[-1]]) == 2
            ):
                cooccurrences[identity] += 1
    for label in labels:
        identity = label["id"]
        p = predictions["947-ordinary"][identity]
        expected_ids = [*(b + 3 for b in label["gold"].encode()), 2]
        actual_ids = p["result"]["generated_ids"]
        if actual_ids == expected_ids:
            continue
        prefix = p["prefix"]
        start = len(prefix.encode())
        comparisons = {}
        for cell in CELLS[1:]:
            other = predictions[cell][identity]
            require(other["result"]["generated_ids"] == expected_ids, "passing comparison differs")
            require(
                other["prefix"] == prefix and other["input_ids"] == p["input_ids"],
                "comparison prompt",
            )
            require(
                losses[cell][identity]["history_targets"] == start
                and losses[cell][identity]["answer_targets"] == 3,
                "comparison target boundary",
            )
            comparisons[cell] = dict(
                ids=other["result"]["generated_ids"],
                first_id=expected_ids[0],
                answer_suffix_loss=losses[cell][identity]["answer_loss"],
                probability=None,
                rank=None,
            )
        loss = losses["947-ordinary"][identity]
        require(
            start == 53 and loss["history_targets"] == 53 and loss["answer_targets"] == 3,
            "target partition",
        )
        require(p["input_ids"][-2:] == [66, 64] and len(p["input_ids"]) == 54, "answer delimiter")
        require(actual_ids[0] != expected_ids[0] and actual_ids[-1] == 2, "first divergence/EOS")
        require(loss["answer_loss"] >= math.log(2) - 1e-5, "CE inconsistent with first argmax miss")
        require(
            sum(slots[identity].values()) == 128 and len(slots[identity]) == 8, "exposure/lanes"
        )
        failed.append(
            dict(
                id=identity,
                template=label["template"],
                canonical=label["canonical"],
                gold=label["gold"],
                expected_first=dict(
                    char=label["gold"][0], byte=label["gold"].encode()[0], id=expected_ids[0]
                ),
                predicted_first=dict(
                    char=chr(actual_ids[0] - 3), byte=actual_ids[0] - 3, id=actual_ids[0]
                ),
                actual_ids=actual_ids,
                expected_ids=expected_ids,
                actual_text=p["result"]["answer"],
                probability=None,
                rank=None,
                probability_rank_recorded=False,
                teacher_answer_suffix_loss=loss["answer_loss"],
                mask=dict(
                    start_y=53,
                    stop_y_exclusive=56,
                    label_ids=expected_ids,
                    full_doc_gold_token_index=54,
                    causal_input_index=53,
                    local_logit_index=21,
                    source="reconstructed from sealed code and saved bytes; not a mask dump",
                ),
                prompt=dict(
                    prefix=prefix,
                    byte_length=53,
                    native_length=54,
                    delimiter_ids=[66, 64],
                    first_segment_ids=32,
                    answer_context=bytes(t - 3 for t in p["input_ids"][32:]).decode(),
                ),
                malformed=not any(
                    actual_ids == [*(b + 3 for b in value.encode()), 2]
                    for value in ("la", "mi", "so", "tu", "R-7", "Q_2", "V:4", "Z!6", "?")
                ),
                batch_slot_histogram=dict(slots[identity]),
                presentations=128,
                contrast_copresentations=cooccurrences[identity],
                passing_comparisons=comparisons,
                raw_source=(
                    "artifacts/local-answer-dev-v1/stages/"
                    f"generate-train-947-ordinary/predictions.jsonl:{labels.index(label) + 1}"
                ),
            )
        )
    require(len(failed) == 16 and sum(c["malformed"] for c in failed) == 4, "failure set")
    require(
        not list((RUN / "stages").glob("*dev*")) and not (RUN / "stages/controls").exists(),
        "v1 stop changed",
    )
    return dict(
        status="PASS",
        registration_sha256=REGISTRATION,
        failed_cases=failed,
        city_first_class_counts=class_counts,
        paired_same_question_batches=dict(sorted(paired_batches.items())),
        paired_query_events=sum(paired_batches.values()),
        checkpoint_metadata=metadata,
        initialization_and_order_share_seed=True,
        paired_events_are_not_distinct_batches=True,
        recorded_first_byte_probabilities_available=False,
        mask_positions_are_reconstructed=True,
        training_forward_or_generation_executed=False,
        development_evaluated=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-checkpoints", action="store_true")
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    result = audit(options.inspect_checkpoints)
    if options.output:
        if not options.output.resolve().is_relative_to(ROOT):
            raise ValueError("Output must stay inside D:/Toruk")
        options.output.parent.mkdir(parents=True, exist_ok=True)
        with options.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    print(
        json.dumps(
            dict(
                status=result["status"],
                failures=len(result["failed_cases"]),
                malformed=sum(c["malformed"] for c in result["failed_cases"]),
                paired_query_events=result["paired_query_events"],
                checkpoint_payloads=options.inspect_checkpoints,
                training_forward_or_generation_executed=False,
            ),
            sort_keys=True,
        )
    )
