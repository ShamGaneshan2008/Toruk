"""Run the frozen three-way held-out comparison for chat selector v2."""

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

from evaluate_local_backbone import gpu_memory_mib
from probe_ollama_backbone import available_ram_gib

from toruk_lm.chat_selector import ChatRelevanceSelector, words
from toruk_lm.ollama_chat import OllamaChatBackend

UNKNOWN = ("don't know", "do not know", "not supplied", "not provided", "no information", "cannot determine")


class LexicalSelector:
    kind = "nonlearned-lexical-v2"
    sha256 = None

    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        if len(messages) <= 3:
            return list(range(len(messages))), False
        query = words(messages[-1]["content"])
        scored = [(len(query & words(message["content"])), index)
                  for index, message in enumerate(messages[:-3]) if message["role"] == "user"]
        chosen = {index for overlap, index in sorted(scored, reverse=True)[:2] if overlap > 0}
        chosen.update(range(len(messages) - 3, len(messages)))
        return sorted(chosen), bool(scored)


def contains(answer: str, value: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(value.casefold()) + r"(?!\w)", answer.casefold()) is not None


def score(answer: str, case: dict) -> tuple[bool, bool]:
    if not case["expected"]:
        uncertain = any(phrase in answer.casefold() for phrase in UNKNOWN)
        asserted = bool(re.search(r"\b(?:TRAIN|DEV|FINAL)CODE\d+\b", answer, re.I))
        asserted = asserted or any(contains(answer, value) for value in ("Mysuru", "Nashik", "Udaipur", "Ranchi"))
        return uncertain and not asserted, not uncertain or asserted
    complete = all(contains(answer, value) for value in case["expected"])
    obsolete = any(contains(answer, value) for value in case["forbidden"])
    return complete and not obsolete, obsolete


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--selector-checkpoint", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh output path")
    manifest_path = args.data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen = json.loads(args.freeze.read_text(encoding="utf-8"))
    expected = {"manifest": sha(manifest_path), "final": sha(args.data_dir / "final.jsonl"),
                "checkpoint": sha(args.selector_checkpoint), "evaluator": sha(Path(__file__)),
                "protocol": sha(Path("docs/research/chat-selector-v2-protocol.md"))}
    if any(frozen.get(key) != value for key, value in expected.items()):
        raise ValueError("frozen file hash mismatch")
    if manifest["split_sha256"]["final"] != expected["final"] or frozen["digest"] != args.digest:
        raise ValueError("final split or model digest mismatch")
    checkpoint = json.loads(args.selector_checkpoint.read_text(encoding="utf-8"))
    if checkpoint.get("protocol") != "chat-selector-v2" or checkpoint.get("data_manifest_sha256") != expected["manifest"]:
        raise ValueError("selector checkpoint is not bound to v2 data")
    cases = [json.loads(line) for line in (args.data_dir / "final.jsonl").read_text(encoding="utf-8").splitlines()]
    if any(case["split"] != "final" or case["template_family"] != "final" for case in cases):
        raise ValueError("unexpected final case")
    before = {"available_ram_gib": available_ram_gib(), "gpu_memory_mib": gpu_memory_mib()}
    backend = OllamaChatBackend(args.model, args.digest, args.selector_checkpoint)
    trained = backend.selector
    lexical = LexicalSelector()
    rows = []
    start = time.perf_counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        for method in ("BASELINE", "LEXICAL", "TORUK"):
            backend.selector = trained if method == "TORUK" else lexical if method == "LEXICAL" else None
            try:
                response = backend.reply_with_metrics(case["messages"], 32, mode="BASELINE" if method == "BASELINE" else "TORUK", temperature=0, top_p=1)
                answer, metrics = response["answer"], response["metrics"]
                correct, unsupported = score(answer, case)
                selected = {int(item[1:]) for item in metrics["selected_message_ids"]}
                recent = set(range(len(case["messages"]) - 3, len(case["messages"])))
                row = {"id": case["id"], "category": case["category"], "method": method,
                       "history_length": case["history_length"], "messages": case["messages"],
                       "evidence_ids": case["evidence_ids"], "expected": case["expected"],
                       "forbidden": case["forbidden"], "answer": answer, "correct": correct,
                       "unsupported": unsupported, "evidence_retained": all(i in selected for i in case["evidence_ids"]) if case["evidence_ids"] else None,
                       "unnecessary_older_selected": len(selected - recent) if not case["evidence_ids"] else None,
                       "metrics": metrics}
            except Exception as error:
                row = {"id": case["id"], "category": case["category"], "method": method,
                       "messages": case["messages"], "expected": case["expected"],
                       "evidence_ids": case["evidence_ids"], "error": f"{type(error).__name__}: {error}",
                       "correct": False, "unsupported": False, "evidence_retained": False if case["evidence_ids"] else None}
            rows.append(row)
            args.output.write_text(json.dumps({"status": "RUNNING", "rows": rows}, indent=2) + "\n", encoding="utf-8")
            print(case["id"], method, row["correct"], flush=True)
    summary = {}
    for method in ("BASELINE", "LEXICAL", "TORUK"):
        subset = [row for row in rows if row["method"] == method]
        valid = [row for row in subset if "metrics" in row]
        summary[method] = {"correct": sum(row["correct"] for row in subset), "cases": len(subset),
                           "unsupported": sum(row["unsupported"] for row in subset),
                           "errors": len(subset) - len(valid),
                           "known_evidence_retained": sum(row["evidence_retained"] is True for row in subset),
                           "known_evidence_cases": sum(row["evidence_retained"] is not None for row in subset),
                           "unnecessary_older_selected": sum(row.get("unnecessary_older_selected") or 0 for row in subset),
                           "available_history_tokens": sum(row["metrics"]["input_tokens"] for row in valid),
                           "selected_tokens": sum(row["metrics"]["selected_context_tokens"] for row in valid),
                           "total_prompt_eval_tokens": sum(row["metrics"]["total_prompt_eval_tokens"] for row in valid),
                           "selector_scan_bytes": sum(row["metrics"]["selector_scan_bytes"] for row in valid),
                           "selector_ms": round(sum(row["metrics"]["selector_ms"] for row in valid), 3),
                           "response_ms": round(sum(row["metrics"]["response_ms"] for row in valid), 3),
                           "by_category": {category: {"correct": sum(row["correct"] for row in subset if row["category"] == category),
                                                      "cases": sum(row["category"] == category for row in subset)}
                                           for category in manifest["categories"]}}
    result = {"schema": "toruk-chat-selector-final-v2", "status": "COMPLETE", "freeze": frozen,
              "model": backend.model_id, "selector_sha256": trained.sha256,
              "settings": {"temperature": 0, "top_p": 1, "max_new_tokens": 32, "max_prompt_tokens": 512},
              "memory_before": before,
              "memory_after": {"available_ram_gib": available_ram_gib(), "gpu_memory_mib": gpu_memory_mib()},
              "wall_seconds": round(time.perf_counter() - start, 3), "summary": summary, "rows": rows}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
