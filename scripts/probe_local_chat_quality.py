"""Record deterministic local chat replies for carryover and fresh-chat probes."""

import argparse
import json
from pathlib import Path

from toruk_lm.chat_foundation import PretrainedChatBackend

SCENARIOS = {
    "youtube_then_math": [
        "Can you open YouTube for me?",
        "What is 5 + 5?",
        "What is 7 times 8?",
    ],
    "fresh_math": ["What is 5 + 5?"],
    "fresh_instruction": ["Reply with exactly the word OK and nothing else."],
    "fresh_correction": [
        "My favorite color is blue.",
        "Correction: my favorite color is green. What is my favorite color now?",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backbone-dir", type=Path, required=True)
    parser.add_argument("--selector-checkpoint", type=Path)
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    backend = PretrainedChatBackend(args.backbone_dir, args.selector_checkpoint)
    scenarios = {}
    for mode in ("BASELINE", "TORUK") if args.selector_checkpoint else ("BASELINE",):
        scenarios[mode] = {}
        for name, prompts in SCENARIOS.items():
            history: list[dict[str, str]] = []
            turns = []
            for prompt in prompts:
                history.append({"role": "user", "content": prompt})
                result = backend.reply_with_metrics(
                    history, args.max_new_tokens, mode=mode, temperature=0
                )
                turns.append(
                    {"prompt": prompt, "answer": result["answer"], "metrics": result["metrics"]}
                )
                history.append({"role": "assistant", "content": result["answer"]})
            scenarios[mode][name] = turns
    report = {
        "model": backend.model_id,
        "max_new_tokens": args.max_new_tokens,
        "scenarios": scenarios,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
