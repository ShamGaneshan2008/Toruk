"""Compare two explicit inference endpoints on fixed, non-research chat probes."""

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


def run(url: str, token: str, questions: list[dict], budget: int) -> dict:
    rows = []
    for question in questions:
        body = json.dumps(
            {"messages": [{"role": "user", "content": question["text"]}], "max_new_tokens": budget}
        ).encode()
        request = urllib.request.Request(
            url.rstrip("/") + "/api/infer",
            body,
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.load(response)
        metrics = result["metrics"]
        rows.append(
            {
                "id": question["id"],
                "answer": result["answer"],
                "expected": question["expected"],
                "exact": result["answer"].strip() == question["expected"].strip(),
                "metrics": metrics,
            }
        )
    return {
        "rows": rows,
        "exact_accuracy": sum(row["exact"] for row in rows) / len(rows),
        "input_tokens": sum(row["metrics"]["input_tokens"] for row in rows),
        "selected_context_tokens": sum(row["metrics"]["selected_context_tokens"] for row in rows),
        "output_tokens": sum(row["metrics"]["output_tokens"] for row in rows),
        "response_ms": sum(row["metrics"]["response_ms"] for row in rows),
        "memory_used": all(row["metrics"]["memory_used"] for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plain-url", required=True)
    parser.add_argument("--selected-url")
    parser.add_argument("--fixture", type=Path, default=Path("configs/chat-comparison-v1.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("TORUK_BACKEND_TOKEN")
    if not token:
        parser.error("TORUK_BACKEND_TOKEN must be set")
    if args.output.exists():
        parser.error("use a fresh output file")
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    if fixture.get("kind") != "chat-context-comparison-fixture-v1":
        parser.error("unsupported fixture")
    questions, budget = fixture["questions"], fixture["max_new_tokens"]
    plain = run(args.plain_url, token, questions, budget)
    result: dict[str, Any] = {"fixture": str(args.fixture), "plain": plain, "selected": None}
    if args.selected_url:
        selected = run(args.selected_url, token, questions, budget)
        result["selected"] = selected
        result["status"] = (
            "COMPARABLE"
            if selected["memory_used"]
            and [r["metrics"]["model"] for r in plain["rows"]]
            == [r["metrics"]["model"] for r in selected["rows"]]
            else "NO_VALID_CONTEXT_PATH"
        )
        result["efficiency_claim"] = (
            result["status"] == "COMPARABLE"
            and selected["exact_accuracy"] >= plain["exact_accuracy"]
            and selected["selected_context_tokens"] < plain["selected_context_tokens"]
        )
    else:
        result["status"] = "NO_VALID_CONTEXT_PATH"
        result["efficiency_claim"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
