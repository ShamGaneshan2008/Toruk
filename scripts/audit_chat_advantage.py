"""Audit the historical comparison; optional BASELINE replay never substitutes a selector."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from evaluate_chat_release_v2 import aggregate, bootstrap, score_answer, validate_fixture
from qualify_chat_launch import aggregate as launch_aggregate
from qualify_chat_launch import score as launch_score

from toruk_lm.chat_foundation import PretrainedChatBackend

FIXTURE_SHA256 = "86e31ab8afccb0e7ab88817fc11b7be4585a7d261c3d99f93eef60540c63a0c6"
SELECTOR_SHA256 = "479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d"
MODEL = "HuggingFaceTB/SmolLM2-135M-Instruct@12fd25f77366"
MODES = ("BASELINE", "TORUK")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def selected_sources(case: dict[str, Any], metrics: dict[str, Any]) -> list[dict[str, str]]:
    ids = metrics["selected_message_ids"]
    messages = case["messages"]
    valid = [message["id"] for message in messages]
    if (
        not ids
        or len(ids) != len(set(ids))
        or any(value not in valid for value in ids)
        or ids != sorted(ids, key=valid.index)
        or ids[-1] != valid[-1]
        or metrics["selected_messages"] != len(ids)
    ):
        raise ValueError("invalid selected source identifiers")
    return [dict(message) for message in messages if message["id"] in ids]


def model_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    """Project only role/content, keeping scoring labels outside the generator."""
    return [{"role": item["role"], "content": item["content"]} for item in case["messages"]]


def frozen_fixture_bytes(path: Path) -> bytes:
    """Recover only a verified CRLF checkout transformation, never changed content."""
    original = path.read_bytes()
    for candidate in (original, original.replace(b"\r\n", b"\n")):
        if hashlib.sha256(candidate).hexdigest() == FIXTURE_SHA256:
            return candidate
    raise ValueError("frozen fixture identity mismatch")


def audit(fixture_path: Path, raw_path: Path) -> dict[str, Any]:
    fixture = json.loads(frozen_fixture_bytes(fixture_path))
    raw = json.loads(raw_path.read_bytes())
    validate_fixture(fixture)
    if raw["fixture_sha256"] != FIXTURE_SHA256:
        raise ValueError("frozen fixture identity mismatch")
    settings = {key: fixture[key] for key in ("max_new_tokens", "temperature", "top_p")}
    if (
        raw["model"] != MODEL
        or raw["selector_sha256"] != SELECTOR_SHA256
        or raw["settings"] != settings
        or raw["status"] != "COMPLETE"
    ):
        raise ValueError("historical model/selector/settings/status mismatch")
    cases = {case["id"]: case for case in fixture["cases"]}
    expected = {(key, mode) for key in cases for mode in MODES}
    observed = [(row["id"], row["mode"]) for row in raw["rows"]]
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError("missing, duplicate or unexpected comparison rows")
    rows = []
    for original in raw["rows"]:
        case = cases[original["id"]]
        if original["category"] != case["category"] or "error" in original:
            raise ValueError("category mismatch or unsuccessful historical request")
        score = score_answer(original["answer"], case)
        if score != original["score"]:
            raise ValueError("saved score does not match frozen rubric")
        metrics = original["metrics"]
        for name in ("input_tokens", "selected_context_tokens", "output_tokens", "total_tokens"):
            if type(metrics[name]) is not int or metrics[name] < 0:
                raise ValueError("token counts must be nonnegative integers")
        if (
            metrics["total_tokens"] != metrics["selected_context_tokens"] + metrics["output_tokens"]
            or metrics["selected_context_tokens"] > metrics["input_tokens"]
            or metrics["selected_context_tokens"] > 512
            or metrics["output_tokens"] > settings["max_new_tokens"]
            or metrics["mode"] != original["mode"]
            or metrics["model"] != MODEL
        ):
            raise ValueError("inconsistent token accounting or request identity")
        rows.append({**original, "selected_sources": selected_sources(case, metrics)})
    summaries = {mode: aggregate([row for row in rows if row["mode"] == mode]) for mode in MODES}
    if summaries != raw["summary"]:
        raise ValueError("saved aggregate differs from independently rescored rows")
    pairs = [
        {
            mode: next(row for row in rows if row["id"] == key and row["mode"] == mode)
            for mode in MODES
        }
        for key in cases
    ]
    if bootstrap(pairs) != raw["bootstrap"]:
        raise ValueError("saved paired uncertainty differs")
    reduction = round(
        100
        * (summaries["BASELINE"]["selected_tokens"] - summaries["TORUK"]["selected_tokens"])
        / summaries["BASELINE"]["selected_tokens"],
        2,
    )
    if reduction != raw["selected_token_reduction_pct"]:
        raise ValueError("saved selected-token reduction differs")
    return {
        "scope": "saved-output audit, not fresh paired inference",
        "fixture_sha256": FIXTURE_SHA256,
        "checkout_fixture_sha256": digest(fixture_path),
        "fixture_crlf_reconstruction": digest(fixture_path) != FIXTURE_SHA256,
        "raw_sha256": digest(raw_path),
        "summary": summaries,
        "selected_token_reduction_pct": reduction,
        "bootstrap": raw["bootstrap"],
        "rows": rows,
        "full_system_efficiency": "UNESTABLISHED",
        "missing_historical_costs": [
            "selector forward/token work",
            "selector-only CPU/wall time",
            "history/fitting tokenization work",
            "per-mode peak process memory",
            "total model FLOPs or energy",
        ],
        "warning": "total_tokens is backbone prompt + generated tokens, not complete system work",
    }


def replay_baseline(fixture: dict[str, Any], backend: Any, old_rows: list[dict[str, Any]]) -> dict:
    rows = []
    for case in fixture["cases"]:
        response = backend.reply_with_metrics(
            model_messages(case),
            fixture["max_new_tokens"],
            mode="BASELINE",
            temperature=fixture["temperature"],
            top_p=fixture["top_p"],
        )
        old = next(row for row in old_rows if row["id"] == case["id"] and row["mode"] == "BASELINE")
        rows.append(
            {
                "id": case["id"],
                "category": case["category"],
                "mode": "BASELINE",
                **response,
                "score": score_answer(response["answer"], case),
                "same_answer": response["answer"] == old["answer"],
                "same_selected_tokens": response["metrics"]["selected_context_tokens"]
                == old["metrics"]["selected_context_tokens"],
            }
        )
    return {
        "scope": "fresh BASELINE only; TORUK historical replay BLOCKED",
        "rows": rows,
        "summary": aggregate(rows),
        "all_answers_match": all(r["same_answer"] for r in rows),
    }


def audit_latest_launch(directory: Path) -> dict[str, Any]:
    """Rescore the newer three-system archive; intermediate rollout turns cost work."""
    suite = json.loads((directory / "suite.json").read_bytes())
    registration = json.loads((directory / "registration.json").read_bytes())
    cases = {case["id"]: case for case in suite["cases"]}
    result: dict[str, Any] = {}
    histories = []
    for name in ("qwen-recent", "qwen-trained-v2", "qwen-lexical-v2"):
        path = directory / name / "results.json"
        saved = json.loads(path.read_bytes())
        rows = saved["rows"]
        for row in rows:
            if row["id"] in cases:
                case = cases[row["id"]]
            elif row["id"].startswith("generated-"):
                scenario = row["id"].removeprefix("generated-").rsplit("-", 1)[0]
                case = {**suite["scenarios"][scenario], "category": row["category"]}
            else:
                case = {"category": "repetition", "answer": "10"}
            if launch_score(row["content"], case) != row["score"]:
                raise ValueError("latest launch score mismatch")
        scored = [row for row in rows if row.get("scored_final_turn", True)]
        recalculated = launch_aggregate(scored, registration["gate"])
        if any(saved["summary"][key] != value for key, value in recalculated.items()):
            raise ValueError("latest launch aggregate mismatch")
        totals: dict[str, float] = {}
        for row in rows:
            for key, value in row["response"].get("metrics", {}).items():
                if type(value) in (int, float):
                    totals[key] = totals.get(key, 0) + value
        if totals != saved["summary"]["all_request_metric_totals"]:
            raise ValueError("latest launch intermediate-turn cost omitted or changed")
        histories.append(
            {row["id"]: row["request"]["messages"] for row in rows if row["id"] in cases}
        )
        result[name] = {
            "results_sha256": digest(path),
            "summary": saved["summary"],
            "sampled_peak_process_tree": saved["peak_process_tree"],
            "all_request_cpu_seconds": sum(row["inference_tree_cpu_seconds"] for row in rows),
            "rows": rows,
        }
    if not all(history == histories[0] for history in histories):
        raise ValueError("latest static histories are not matched")
    return {
        "scope": "saved-output rescore only; generated rollout histories can differ",
        "matched_static_histories": len(cases),
        "methods": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=Path("configs/chat-release-eval-v2.json"))
    parser.add_argument("--raw", type=Path, default=Path("artifacts/chat-release-v2/raw.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay-baseline", type=Path, metavar="BACKBONE_DIR")
    parser.add_argument("--launch-dir", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh output path")
    result = audit(args.fixture, args.raw)
    if args.launch_dir:
        result["latest_launch_archive"] = audit_latest_launch(args.launch_dir)
    checkpoint = Path("artifacts/m6-validation-001/recurrent/checkpoint.pt")
    result["selector_prerequisite"] = {
        "path": str(checkpoint),
        "expected_sha256": SELECTOR_SHA256,
        "present": checkpoint.is_file(),
        "identity_matches": checkpoint.is_file() and digest(checkpoint) == SELECTOR_SHA256,
    }
    if args.replay_baseline:
        started = time.perf_counter()
        backend = PretrainedChatBackend(args.replay_baseline)
        if backend.model_id != MODEL:
            raise ValueError("refusing a different historical backbone")
        # Verify all archived selected prompt counts using the actual local tokenizer.
        fixture = json.loads(args.fixture.read_bytes())
        for row in result["rows"]:
            prompt = [{"role": s["role"], "content": s["content"]} for s in row["selected_sources"]]
            if backend._tokens(prompt).shape[-1] != row["metrics"]["selected_context_tokens"]:
                raise ValueError("archived selected context disagrees with tokenizer")
            row["prompt_token_ids"] = backend._tokens(prompt)[0].tolist()
        result["fresh_baseline"] = replay_baseline(fixture, backend, result["rows"])
        result["fresh_baseline"]["startup_and_replay_seconds"] = time.perf_counter() - started
        result["backbone_manifest"] = json.loads(
            (args.replay_baseline / "toruk-backbone.json").read_bytes()
        )
        result["generation_config"] = backend.model.generation_config.to_dict()
        result["backbone_file_hashes"] = {
            path.name: digest(path) for path in args.replay_baseline.iterdir() if path.is_file()
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("summary", "selector_prerequisite")}, indent=2))
    if "fresh_baseline" in result:
        print(
            "Fresh baseline:",
            result["fresh_baseline"]["summary"],
            "all answers match:",
            result["fresh_baseline"]["all_answers_match"],
        )


if __name__ == "__main__":
    main()
