"""Verify source provenance and report frozen scores and full preprocessing work."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import recall_study as study
from transformers import AutoTokenizer

from toruk_lm.chat_foundation import CHAT_INSTRUCTIONS
from toruk_lm.source_spans import SourceEnvelopeBackend, SourceSpanSelector


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    study.verify(args.run, True)
    tokenizer = AutoTokenizer.from_pretrained(study.BACKBONE, local_files_only=True)
    backend = SourceEnvelopeBackend.__new__(SourceEnvelopeBackend)
    backend.tokenizer = tokenizer
    backend.system_prompt = CHAT_INSTRUCTIONS
    old = study.ChatRelevanceSelector(study.SELECTOR)
    methods = {
        "recent": None,
        "lexical": study.LexicalContextSelector(),
        "old": old,
        "new": SourceSpanSelector(old),
    }
    summary: dict[str, Any] = {}
    work = []
    saved: dict[tuple[str, str], str] = {}
    for stage in ("before", "development", "heldout"):
        if not (args.run / f"{stage}.jsonl").exists():
            continue
        rows = [
            json.loads(line)
            for line in (args.run / f"{stage}.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        assert len(rows) == (36 if stage == "before" else 48)
        stage_summary = {}
        for row in rows:
            case, method = row["case"], row["method"]
            assert all(row[key] == value for key, value in study.score(row["answer"], case).items())
            if stage == "before":
                saved[case["id"], method] = row["answer"]
            elif stage == "development" and method != "new" and saved:
                assert saved[case["id"], method] == row["answer"], "nonreproducible before answer"
            for source in row["selected_evidence"]:
                assert source["content"] == case["messages"][source["turn"]]["content"]
                assert source["sha256"] == hashlib.sha256(source["content"].encode()).hexdigest()
            backend.selector = methods[method]
            messages = case["messages"]
            indices = (
                list(range(len(messages)))
                if backend.selector is None
                else backend.selector.select(messages)[0]
            )
            chosen = list(indices)
            fit_tokens = 0
            fit_attempts = 0
            while True:
                tokens = backend._tokens([messages[i] for i in chosen])
                fit_tokens += int(tokens.shape[-1])
                fit_attempts += 1
                if tokens.shape[-1] <= 512:
                    break
                chosen.pop(0)
                while len(chosen) > 1 and messages[chosen[0]]["role"] == "assistant":
                    chosen.pop(0)
            assert tokens[0].tolist() == row["prompt_ids"]
            prompt_text = tokenizer.decode(row["prompt_ids"], skip_special_tokens=False)
            intact = all(messages[i]["content"] in prompt_text for i in chosen)
            assert intact, "selected content changed in actual tokenized prompt"
            work.append(
                {
                    "stage": stage,
                    "id": case["id"],
                    "method": method,
                    "fit_tokenization_tokens": fit_tokens,
                    "fit_attempts": fit_attempts,
                    "history_tokenization_tokens": row["metrics"]["input_tokens"],
                    "prefill_tokens": row["metrics"]["selected_context_tokens"],
                    "scan_bytes": row["scan_bytes"],
                    "source_bytes": row["source_bytes"],
                    "all_selected_source_text_intact": intact,
                }
            )
        for method in methods:
            selected = [row for row in rows if row["method"] == method]
            if not selected:
                continue
            costs = [row for row in work if row["stage"] == stage and row["method"] == method]
            stage_summary[method] = {
                "correct": sum(row["correct"] for row in selected),
                "n": len(selected),
                "by_task": {
                    task: {
                        "correct": sum(r["correct"] for r in selected if r["case"]["task"] == task),
                        "n": sum(r["case"]["task"] == task for r in selected),
                    }
                    for task in sorted({r["case"]["task"] for r in selected})
                },
                "unsupported_proxy": sum(row["unsupported"] for row in selected),
                "failures": dict(Counter(row["failure"] for row in selected if row["failure"])),
                "prompt_tokens": sum(row["metrics"]["selected_context_tokens"] for row in selected),
                "output_tokens": sum(row["metrics"]["output_tokens"] for row in selected),
                "request_ms": sum(row["metrics"]["response_ms"] for row in selected),
                "selector_probe_ms": sum(row["selector_ms_probe"] for row in selected),
                "fit_probe_ms": sum(row["fit_ms_probe"] for row in selected),
                "peak_rss_bytes": max(
                    row["rss"].get("peak_wset", row["rss"]["rss"]) for row in selected
                ),
                "max_source_bytes": max(row["source_bytes"] for row in selected),
                "work": {
                    key: sum(row[key] for row in costs)
                    for key in (
                        "history_tokenization_tokens",
                        "fit_tokenization_tokens",
                        "fit_attempts",
                        "scan_bytes",
                    )
                },
            }
        summary[stage] = stage_summary
    study.write(args.run / "work.json", work)
    study.write(args.run / "summary.json", summary)
    lines = [
        "| Split / method | Exact /6 | Gist /2 | Clear /2 | Ambiguous /1 | "
        "Missing /1 | All /12 | Unsupported proxy |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for stage, methods_summary in summary.items():
        for method, result in methods_summary.items():
            counts = [
                str(result["by_task"][task]["correct"])
                for task in ("exact", "gist", "vague_clear", "vague_ambiguous", "missing")
            ]
            lines.append(
                f"| {stage} / {method} | "
                + " | ".join(counts)
                + f" | {result['correct']} | {result['unsupported_proxy']} |"
            )
    (args.run / "table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
