"""One frozen, paired chat comparison with retained raw and readable failures."""

import argparse
import hashlib
import json
import random
import re
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from evaluate_chat_foundation import MAX_PRIVATE_BYTES, private_bytes

from toruk_lm.chat_foundation import PretrainedChatBackend, weight_sha256

EXPECTED_CATEGORIES = {
    "instruction",
    "factual",
    "reference",
    "user_fact",
    "correction",
    "preservation",
    "long_retrieval",
    "irrelevant_history",
    "unknown",
    "ambiguous",
}


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def contains_phrase(answer: str, phrase: str) -> bool:
    target = normalized(phrase)
    if target.isalnum() and " " not in target:
        return re.search(r"(?<!\w)" + re.escape(target) + r"(?!\w)", answer) is not None
    return target in answer


def score_answer(answer: str, case: dict[str, Any]) -> dict[str, bool | None]:
    text = normalized(answer)
    exact = bool(case.get("exact", False))
    accepted = (
        text.strip(" .,!?:;\"'") in [normalized(value) for value in case["accepted"]]
        if exact
        else any(contains_phrase(text, value) for value in case["accepted"])
    )
    accepted = accepted and not any(contains_phrase(text, value) for value in case["forbidden"])
    return {
        "quality": accepted,
        "factual_correct": accepted if case.get("factual_expected") else None,
        "correction_correct": accepted if case.get("correction_expected") else None,
        "unsupported_answer": not accepted if case.get("unsupported_case") else None,
    }


def validate_fixture(fixture: dict[str, Any]) -> None:
    if (
        fixture.get("kind") != "toruk-chat-release-eval-v2"
        or fixture.get("max_new_tokens") != 32
        or fixture.get("temperature") != 0
        or fixture.get("top_p") != 1
    ):
        raise ValueError("v2 fixture settings differ from preregistered protocol")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or len(cases) != 20:
        raise ValueError("v2 requires 20 cases")
    seen: set[str] = set()
    counts: dict[str, int] = defaultdict(int)
    for case in cases:
        if case["id"] in seen or case["category"] not in EXPECTED_CATEGORIES:
            raise ValueError("duplicate case or unexpected category")
        seen.add(case["id"])
        counts[case["category"]] += 1
        messages = case["messages"]
        if not 1 <= len(messages) <= 20 or messages[-1]["role"] != "user":
            raise ValueError("invalid conversation length or final role")
        if [message["id"] for message in messages] != [f"m{n}" for n in range(len(messages))]:
            raise ValueError("message identifiers must be sequential")
        if any(
            message["role"] not in ("user", "assistant")
            or not message["content"].strip()
            or len(message["content"].encode("utf-8")) > 1024
            for message in messages
        ):
            raise ValueError("invalid message")
        if sum(len(message["content"].encode("utf-8")) for message in messages) > 8192:
            raise ValueError("conversation exceeds server byte limit")
        if not case["accepted"] or not isinstance(case["forbidden"], list):
            raise ValueError("missing scoring rubric")
    if set(counts) != EXPECTED_CATEGORIES or any(count != 2 for count in counts.values()):
        raise ValueError("expected two cases in each of ten categories")


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if "metrics" in row]
    return {
        "n": len(rows),
        "quality": sum(bool(row["score"]["quality"]) for row in rows),
        "factual_correct": sum(row["score"]["factual_correct"] is True for row in rows),
        "correction_correct": sum(row["score"]["correction_correct"] is True for row in rows),
        "unsupported_answers": sum(row["score"]["unsupported_answer"] is True for row in rows),
        "failures": len(rows) - len(valid),
        "input_tokens": sum(row["metrics"]["input_tokens"] for row in valid),
        "selected_tokens": sum(row["metrics"]["selected_context_tokens"] for row in valid),
        "output_tokens": sum(row["metrics"]["output_tokens"] for row in valid),
        "total_tokens": sum(row["metrics"]["total_tokens"] for row in valid),
        "latency_ms": round(sum(row["metrics"]["response_ms"] for row in valid), 3),
        "memory_used_cases": sum(row["metrics"]["memory_used"] is True for row in valid),
    }


def bootstrap(pairs: list[dict[str, Any]]) -> dict[str, list[float] | str]:
    rng = random.Random(23)
    reductions, quality_differences = [], []
    for _ in range(2000):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        baseline = sum(row["BASELINE"]["metrics"]["selected_context_tokens"] for row in sample)
        toruk = sum(row["TORUK"]["metrics"]["selected_context_tokens"] for row in sample)
        reductions.append(100 * (baseline - toruk) / baseline)
        quality_differences.append(
            100
            * sum(
                int(row["TORUK"]["score"]["quality"]) - int(row["BASELINE"]["score"]["quality"])
                for row in sample
            )
            / len(sample)
        )
    return {
        "selected_token_reduction_pct_95_interval": [
            round(statistics.quantiles(reductions, n=40)[0], 2),
            round(statistics.quantiles(reductions, n=40)[-1], 2),
        ],
        "quality_difference_pp_95_interval": [
            round(statistics.quantiles(quality_differences, n=40)[0], 2),
            round(statistics.quantiles(quality_differences, n=40)[-1], 2),
        ],
        "method": "2000 paired resamples, seed 23; descriptive for this fixed fixture",
    }


def safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")[:250]


def report(result: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    summary = result["summary"]
    lines = [
        "# Chat release candidate v2 — paired local result",
        "",
        f"Fixture SHA-256: `{result['fixture_sha256']}`. "
        f"Backbone: `{result['model']}`. Selector: `{result['selector_sha256']}`.",
        "",
        "| Mode | Quality | Selected tokens | Output tokens | Total tokens | "
        "Latency ms | Failures | Unsupported answers |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode in ("BASELINE", "TORUK"):
        row = summary[mode]
        lines.append(
            f"| {mode} | {row['quality']}/{row['n']} | {row['selected_tokens']} | "
            f"{row['output_tokens']} | {row['total_tokens']} | {row['latency_ms']} | "
            f"{row['failures']} | {row['unsupported_answers']} |"
        )
    lines += [
        "",
        f"Selected-token reduction: **{result['selected_token_reduction_pct']}%**; "
        f"quality difference: **{result['quality_difference_pp']} percentage points**. "
        f"Primary success: **{result['primary_success']}**.",
        "",
        "## Per-category quality",
        "",
        "| Category | BASELINE | TORUK |",
        "| --- | ---: | ---: |",
    ]
    for category, scores in result["per_category"].items():
        lines.append(f"| {category} | {scores['BASELINE']}/2 | {scores['TORUK']}/2 |")
    lines += [
        "",
        "## Failure cases and examples",
        "",
        "| Case | Mode | Selected IDs | Answer | Quality |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        for mode in ("BASELINE", "TORUK"):
            row = next(
                item for item in result["rows"] if item["id"] == case["id"] and item["mode"] == mode
            )
            selected_ids = safe_cell(row.get("metrics", {}).get("selected_message_ids", []))
            answer = safe_cell(row.get("answer", row.get("error", "")))
            lines.append(
                f"| {case['id']} | {mode} | {selected_ids} | {answer} | {row['score']['quality']} |"
            )
    lines += [
        "",
        "These are synthetic local probes with one deterministic decoding setting. "
        "A pretrained backbone supplies language ability; Toruk supplies only the "
        "experimental context selection. No general superiority follows from this set.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen v2 paired chat release evaluation")
    parser.add_argument("--fixture", type=Path, default=Path("configs/chat-release-eval-v2.json"))
    parser.add_argument("--backbone-dir", type=Path, required=True)
    parser.add_argument("--selector-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists() or args.output == args.report:
        parser.error("use fresh, distinct output and report paths")
    raw = args.fixture.read_bytes()
    fixture = json.loads(raw)
    validate_fixture(fixture)
    model = PretrainedChatBackend(args.backbone_dir, args.selector_checkpoint)
    cases = fixture["cases"]
    result: dict[str, Any] = {
        "schema": "toruk-chat-release-result-v2",
        "fixture": str(args.fixture),
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "model": model.model_id,
        "selector_sha256": weight_sha256(args.selector_checkpoint),
        "settings": {key: fixture[key] for key in ("max_new_tokens", "temperature", "top_p")},
        "rows": [],
        "status": "RUNNING",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    for case in cases:
        messages = [{"role": item["role"], "content": item["content"]} for item in case["messages"]]
        for mode in ("BASELINE", "TORUK"):
            try:
                response = model.reply_with_metrics(
                    messages,
                    fixture["max_new_tokens"],
                    mode=mode,
                    temperature=fixture["temperature"],
                    top_p=fixture["top_p"],
                )
                answer, metrics = response["answer"], response["metrics"]
                row = {
                    "id": case["id"],
                    "category": case["category"],
                    "mode": mode,
                    "answer": answer,
                    "score": score_answer(answer, case),
                    "metrics": metrics,
                }
            except Exception as error:
                row = {
                    "id": case["id"],
                    "category": case["category"],
                    "mode": mode,
                    "error": f"{type(error).__name__}: {error}",
                    "score": score_answer("", case),
                }
            result["rows"].append(row)
            result["private_bytes"] = private_bytes()
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            if result["private_bytes"] is not None and result["private_bytes"] > MAX_PRIVATE_BYTES:
                raise MemoryError("3 GiB private-memory stop reached")
    modes = {
        mode: [row for row in result["rows"] if row["mode"] == mode]
        for mode in ("BASELINE", "TORUK")
    }
    summary = {mode: aggregate(rows) for mode, rows in modes.items()}
    result["summary"] = summary
    pairs = [
        {mode: next(row for row in modes[mode] if row["id"] == case["id"]) for mode in modes}
        for case in cases
    ]
    if all("metrics" in row for pair in pairs for row in pair.values()):
        result["bootstrap"] = bootstrap(pairs)
        result["selected_token_reduction_pct"] = round(
            100
            * (summary["BASELINE"]["selected_tokens"] - summary["TORUK"]["selected_tokens"])
            / summary["BASELINE"]["selected_tokens"],
            2,
        )
    else:
        result["bootstrap"] = None
        result["selected_token_reduction_pct"] = None
    result["quality_difference_pp"] = round(
        100 * (summary["TORUK"]["quality"] - summary["BASELINE"]["quality"]) / len(cases),
        2,
    )
    result["per_category"] = {
        category: {
            mode: sum(
                row["score"]["quality"] is True
                for row in modes[mode]
                if row["category"] == category
            )
            for mode in modes
        }
        for category in sorted(EXPECTED_CATEGORIES)
    }
    correction = result["per_category"]["correction"]
    result["primary_success"] = bool(
        result["selected_token_reduction_pct"] is not None
        and result["selected_token_reduction_pct"] >= 35
        and summary["BASELINE"]["quality"] >= 12
        and summary["TORUK"]["quality"] >= 12
        and result["quality_difference_pp"] >= -5
        and correction["TORUK"] >= correction["BASELINE"]
        and summary["TORUK"]["unsupported_answers"] <= summary["BASELINE"]["unsupported_answers"]
        and summary["TORUK"]["failures"] <= summary["BASELINE"]["failures"]
    )
    result["seconds"] = round(time.perf_counter() - started, 3)
    result["status"] = "COMPLETE"
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report(result, cases), encoding="utf-8")
    print(json.dumps({"summary": summary, "primary_success": result["primary_success"]}, indent=2))


if __name__ == "__main__":
    main()
