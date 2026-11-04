"""Summarize separate datasets, paired uncertainty, ablations and full request work."""

import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

from independent_replication import METHODS, verify


def wilson(correct: int, n: int) -> list[float]:
    z = 1.959963984540054
    p = correct / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def paired_interval(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> dict[str, Any]:
    """Positive quality difference / latency saving favors a over b."""
    aa = {r["case"]["id"]: r for r in a}
    bb = {r["case"]["id"]: r for r in b}
    if aa.keys() != bb.keys() or not aa:
        raise ValueError("Unpaired cases")
    ids = sorted(aa)
    rng = random.Random(741)
    quality, savings = [], []
    for _ in range(10000):
        picked = rng.choices(ids, k=len(ids))
        quality.append(
            sum(int(aa[i]["correct"]) - int(bb[i]["correct"]) for i in picked) / len(ids)
        )
        base = sum(bb[i]["metrics"]["response_ms"] for i in picked)
        savings.append(1 - sum(aa[i]["metrics"]["response_ms"] for i in picked) / base)
    quality.sort()
    savings.sort()
    return {
        "quality_delta_95": [quality[250], quality[9749]],
        "latency_saving_fraction_95": [savings[250], savings[9749]],
        "bootstrap_resamples": 10000,
        "bootstrap_seed": 741,
        "unit": "scenario, paired across methods",
        "limitation": (
            "Authored scenarios are not a random population sample; no training-seed uncertainty."
        ),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    correct = sum(row["correct"] for row in rows)
    known = [r for r in rows if r["case"]["task"] not in ("missing", "vague_ambiguous")]
    return {
        "n": n,
        "correct": correct,
        "accuracy_wilson95": wilson(correct, n),
        "unsupported_proxy": sum(r["unsupported"] for r in rows),
        "distant_known_correct": sum(r["correct"] for r in known),
        "distant_known_n": len(known),
        "all_marked_known_sources_retained": sum(r["evidence_retained"] for r in known),
        "by_task": {
            task: {
                "correct": sum(r["correct"] for r in rows if r["case"]["task"] == task),
                "n": sum(r["case"]["task"] == task for r in rows),
            }
            for task in sorted({r["case"]["task"] for r in rows})
        },
        "failures": dict(Counter(r["failure"] for r in rows if r["failure"])),
        "request_ms": sum(r["metrics"]["response_ms"] for r in rows),
        "request_cpu_ms": sum(r["timing"]["request_cpu_ms"] for r in rows),
        "selector_ms": sum(r["timing"]["selector_ms"] for r in rows),
        "history_tokenization_ms": sum(r["timing"]["history_tokenization_ms"] for r in rows),
        "fit_ms": sum(r["timing"]["fit_ms"] for r in rows),
        "model_generate_ms": sum(r["timing"]["model_generate_ms"] for r in rows),
        "prompt_tokens": sum(r["work"]["prefill_tokens"] for r in rows),
        "output_tokens": sum(r["work"]["output_tokens"] for r in rows),
        "history_token_positions": sum(r["work"]["history_token_positions"] for r in rows),
        "fit_token_positions": sum(r["work"]["fit_token_positions"] for r in rows),
        "fit_attempts": sum(r["work"]["fit_attempts"] for r in rows),
        "logical_scan_bytes": sum(r["work"]["logical_scan_bytes"] for r in rows),
        "max_source_bytes": max(r["work"]["source_bytes"] for r in rows),
        "cumulative_process_peak_bytes": max(r["memory"]["peak_bytes"] for r in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    verify(args.run)
    audit = json.loads((args.run / "audit.json").read_text(encoding="utf-8"))
    if audit != {"status": "PASS", "rows": 216, "model_inference": False}:
        raise ValueError("Complete provenance/scoring audit required")
    result: dict[str, Any] = {
        "suites": {},
        "ablations": {},
        "primary_rubric": "unchanged recall_study.score; unsupported is a proxy",
        "new_training_steps": 0,
        "energy_flops_dollar_cost": "NOT_MEASURED",
        "independent_human_adjudication": "NOT_RUN",
    }
    lines = [
        "| Dataset / method | Correct | Unsupported proxy | Prompt / output tokens | "
        "Request s | CPU s | Selector ms | Peak GiB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for suite in ("controlled", "independent"):
        rows = [
            json.loads(line)
            for line in (args.run / f"{suite}.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        grouped = {method: [r for r in rows if r["method"] == method] for method in METHODS}
        stats = {method: summarize(values) for method, values in grouped.items()}
        full, lexical = stats["toruk"], stats["lexical"]
        interval = paired_interval(grouped["toruk"], grouped["lexical"])
        gates = {
            "correct_at_least_lexical": full["correct"] >= lexical["correct"],
            "unsupported_proxy_no_greater": full["unsupported_proxy"]
            <= lexical["unsupported_proxy"],
            "request_ms_strictly_lower": full["request_ms"] < lexical["request_ms"],
            "prompt_plus_output_strictly_lower": full["prompt_tokens"] + full["output_tokens"]
            < lexical["prompt_tokens"] + lexical["output_tokens"],
            "positive_paired_quality_or_latency_interval": interval["quality_delta_95"][0] > 0
            or interval["latency_saving_fraction_95"][0] > 0,
        }
        result["suites"][suite] = {
            "methods": stats,
            "toruk_vs_lexical_paired95": interval,
            "gates": gates,
            "frozen_proxy_efficiency_gate_passed": all(gates.values()),
            "stage_cost": json.loads((args.run / f"{suite}-cost.json").read_text(encoding="utf-8")),
        }
        result["ablations"][suite] = {}
        for method in METHODS:
            stat = stats[method]
            lines.append(
                f"| {suite} / {method} | {stat['correct']}/{stat['n']} | "
                f"{stat['unsupported_proxy']} | "
                f"{stat['prompt_tokens']} / {stat['output_tokens']} | "
                f"{stat['request_ms'] / 1000:.2f} | {stat['request_cpu_ms'] / 1000:.2f} | "
                f"{stat['selector_ms']:.3f} | {stat['cumulative_process_peak_bytes'] / 2**30:.3f} |"
            )
            if method not in ("no_envelope", "no_learned_rank", "restore_cutoff"):
                continue
            other = {r["case"]["id"]: r for r in grouped[method]}
            gains, regressions = [], []
            for row in grouped["toruk"]:
                old = other[row["case"]["id"]]
                if row["correct"] and not old["correct"]:
                    gains.append(row["case"]["id"])
                elif old["correct"] and not row["correct"]:
                    regressions.append(row["case"]["id"])
            result["ablations"][suite][method] = {
                "full_minus_ablation_correct": full["correct"] - stat["correct"],
                "full_minus_ablation_unsupported_proxy": full["unsupported_proxy"]
                - stat["unsupported_proxy"],
                "full_minus_ablation_request_ms": full["request_ms"] - stat["request_ms"],
                "gains": gains,
                "regressions": regressions,
                "paired95": paired_interval(grouped["toruk"], grouped[method]),
            }
    review_path = args.run / "assertion-review.json"
    if review_path.exists():
        result["posthoc_assistant_assertion_review"] = json.loads(
            review_path.read_text(encoding="utf-8")
        )["summary"]
    for path, value in ((args.run / "summary.json", result),):
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    with (args.run / "table.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
