"""Validate regenerated owned-LM evidence; no inference, fitting, or reference weights."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from study_owned_lm import success

from toruk_lm.owned_data import CATEGORIES, cases, digest
from toruk_lm.owned_lm import VARIANTS
from toruk_lm.owned_training import load, runtime_identity
from toruk_lm.tokenizer import ByteTokenizer

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def text_hashes(path):
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return {
        hashlib.sha256(value).hexdigest() for value in (content, content.replace(b"\n", b"\r\n"))
    }


def close(actual, expected, tolerances, label):
    require(
        math.isfinite(actual)
        and math.isfinite(expected)
        and math.isclose(actual, expected, **tolerances),
        f"numeric mismatch: {label}: {actual} vs {expected}",
    )


def validate(run, config_path, contract_path, reference=None):
    contract, config = read(contract_path), read(config_path)
    require(contract["schema"] == "toruk-owned-reproduction-v1", "unsupported protocol")
    mode = next((k for k, v in contract["configs"].items() if digest(config) == v), None)
    require(mode is not None, "config/protocol identity mismatch")
    require(mode != "primary" or reference is not None, "primary requires --reference")
    require(runtime_identity() == contract["runtime"], "model runtime identity mismatch")
    for name, expected in contract["sources"].items():
        require(source_hash(ROOT / name) == expected, f"source identity mismatch: {name}")
    registration, freeze, summary = (
        read(run / f"{n}.json") for n in ("registration", "freeze", "summary")
    )
    require(registration["schema"] == "toruk-owned-study-registration-v1", "registration schema")
    require(summary["schema"] == "toruk-owned-study-results-v1", "result schema")
    require(registration["config"] == config, "run config identity mismatch")
    require(
        registration["config_sha256"] in text_hashes(config_path),
        "config byte hash mismatch (LF/CRLF allowed)",
    )
    require(
        registration["runtime"] == freeze["runtime"] == contract["runtime"],
        "registered model identity mismatch",
    )
    require(
        registration["driver_sha256"] == freeze["driver_sha256"]
        and freeze["driver_sha256"] in text_hashes(ROOT / "scripts/study_owned_lm.py"),
        "registered driver identity mismatch",
    )
    require(
        registration["design_sha256"] in text_hashes(ROOT / "docs/research/owned-lm-v1-design.md"),
        "registered design identity mismatch",
    )
    require(summary["resume_equal"] is True and freeze["resume_equal"] is True, "resume failed")
    datasets = {}
    for split in ("train", "dev", "heldout"):
        rows = read(run / "data" / f"{split}.json")
        require(rows == cases(split, config[f"{split}_per_category"]), f"dataset mismatch: {split}")
        binding = registration["manifest"]["splits"][split]
        require(
            binding["sha256"] == digest(rows) and binding["count"] == len(rows),
            f"dataset hash/count mismatch: {split}",
        )
        datasets[split] = rows
    expected_keys = {
        f"{seed}-{variant}-{ablation}"
        for seed in config["seeds"]
        for variant in VARIANTS
        for ablation in (
            ("full", "no_read", "no_update")
            if variant == "memory_on"
            else ("full", "rolling")
            if variant.startswith("ordinary")
            else ("full",)
        )
    }
    require(set(summary["heldout"]) == expected_keys, "missing/extra evaluation conditions")
    require(
        {p.stem for p in (run / "heldout").glob("*.json")} == expected_keys,
        "missing/extra raw output files",
    )
    results = {}
    for name in sorted(expected_keys):
        result = read(run / "heldout" / f"{name}.json")
        seed, variant, ablation = name.split("-", 2)
        require(result["schema"] == "toruk-owned-evaluation-v1", "evaluation protocol mismatch")
        require(
            result["seed"] == int(seed)
            and result["variant"] == variant
            and result["ablation"] == ("full" if ablation == "rolling" else ablation)
            and result["rolling_diagnostic"] == (ablation == "rolling"),
            f"mode identity mismatch: {name}",
        )
        checkpoint = run / "models" / f"{seed}-{variant}" / "checkpoint.pt"
        checkpoint_hash = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        require(
            checkpoint_hash
            == freeze["checkpoints"][f"{seed}-{variant}"]
            == result["checkpoint_sha256"],
            f"checkpoint hash mismatch: {name}",
        )
        _, payload = load(checkpoint)
        require(
            payload["variant"] == variant
            and payload["options"]["seed"] == int(seed)
            and payload["config"] == config["model"]
            and payload["next_step"] == config["steps"]
            and payload["dataset"] == digest(datasets["train"]),
            f"checkpoint training lineage mismatch: {name}",
        )
        require(result["dataset"] == digest(datasets["heldout"]), "evaluation dataset mismatch")
        rows = result["rows"]
        require(len(rows) == len(datasets["heldout"]), "raw answer count mismatch")
        for row, document in zip(rows, datasets["heldout"], strict=True):
            require(
                row["id"] == document["id"]
                and row["category"] == document["category"]
                and row["expected"] == document["answer"]
                and row["prefix_sha256"] == digest(document["prefix"]),
                "raw input mismatch",
            )
            ids = row["generation"]["generated_ids"]
            require(
                0 < len(ids) <= config["max_new_tokens"]
                and all(type(i) is int and 2 <= i < 259 for i in ids)
                and 2 not in ids[:-1],
                "invalid generated IDs/budget",
            )
            answer = ByteTokenizer().decode(ids)
            require(answer == row["generation"]["answer"], "raw token/text mismatch")
            answer = answer.strip()
            flags = dict(
                correct=answer == document["answer"],
                unsupported=document["answer"] == "?" and answer not in ("?", ""),
                wrong_nonempty=bool(answer) and answer != document["answer"],
                stale=bool(document["obsolete"]) and answer == document["obsolete"],
                empty=not answer,
                invalid_utf8="\ufffd" in answer,
            )
            require(all(row[k] == v for k, v in flags.items()), "raw answer scoring mismatch")
            require(
                row["targets"]
                == row["nll_forward_positions"]
                == len(document["text"].encode()) + 1,
                "target accounting mismatch",
            )
        for key in ("correct", "unsupported", "wrong_nonempty"):
            require(result[key] == sum(r[key] for r in rows), f"metric rescore mismatch: {key}")
        require(result["questions"] == len(rows), "question count mismatch")
        for category in CATEGORIES:
            selected = [r for r in rows if r["category"] == category]
            require(
                result["categories"][category]
                == dict(n=len(selected), correct=sum(r["correct"] for r in selected)),
                "category rescore",
            )
        close(
            result["nll"],
            sum(r["loss_sum"] for r in rows) / sum(r["targets"] for r in rows),
            dict(rel_tol=0, abs_tol=1e-12),
            f"{name}/rescore",
        )
        close(
            result["byte_perplexity"],
            math.exp(result["nll"]),
            dict(rel_tol=0, abs_tol=1e-12),
            f"{name}/perplexity",
        )
        require(
            {k: v for k, v in result.items() if k != "rows"} == summary["heldout"][name],
            "summary/raw mismatch",
        )
        results[name] = result
    require(success(results, config["seeds"]) == summary["criterion"], "research gate mismatch")
    if reference is not None:
        require(mode == "primary", "historical reference requires primary config")
        for name, expected in contract["reference_files"].items():
            require(
                digest(read(reference / name)) == expected, f"reference integrity mismatch: {name}"
            )
        for name, result in results.items():
            old = read(reference / "heldout" / f"{name}.json")
            for key in (
                "schema",
                "variant",
                "seed",
                "ablation",
                "rolling_diagnostic",
                "dataset",
                "questions",
                "correct",
                "unsupported",
                "wrong_nonempty",
                "categories",
            ):
                require(result[key] == old[key], f"reference metric mismatch: {name}/{key}")
            close(result["nll"], old["nll"], contract["tolerances"], f"{name}/nll")
            for row, previous in zip(result["rows"], old["rows"], strict=True):

                def stable(r):
                    return {
                        k: v
                        for k, v in r.items()
                        if k not in ("loss_sum", "nll_seconds", "generation_seconds")
                    }

                require(stable(row) == stable(previous), f"reference raw output mismatch: {name}")
                close(row["loss_sum"], previous["loss_sum"], contract["tolerances"], name)
    return dict(
        status="PASS",
        mode=mode,
        conditions=len(results),
        answers=sum(r["questions"] for r in results.values()),
        reference_compared=reference is not None,
        research_gate=summary["criterion"]["passed"],
        nll={k: v["nll"] for k, v in results.items()},
        seconds=summary["seconds"],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--contract", type=Path, default=ROOT / "configs/owned-reproduction-v1.json"
    )
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.run, args.config, args.contract, args.reference), indent=2))
    except (ValueError, KeyError, OSError, TypeError) as error:
        parser.exit(1, f"Reproduction validation failed: {error}\n")


if __name__ == "__main__":
    main()
