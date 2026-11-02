"""Probe whether a prior online-content refusal contaminates unrelated answers."""

import argparse
import json
from pathlib import Path

from toruk_lm.chat_foundation import PretrainedChatBackend

OBSERVED_REPLY = (
    "I'm sorry for any confusion, but as a chatbot, I don't have the capability "
    "to access or interact with online content."
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backbone-dir", type=Path, required=True)
    parser.add_argument("--selector-checkpoint", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    backend = PretrainedChatBackend(args.backbone_dir, args.selector_checkpoint)
    scenarios = {
        "fresh_math": [{"role": "user", "content": "what is 5+5"}],
        "prior_refusal": [
            {"role": "user", "content": "open YouTube"},
            {"role": "assistant", "content": "I cannot access online content."},
            {"role": "user", "content": "what is 5+5"},
        ],
        "prior_refusal_spaced_math": [
            {"role": "user", "content": "open YouTube"},
            {"role": "assistant", "content": "I cannot access online content."},
            {"role": "user", "content": "What is 5 + 5?"},
        ],
    }
    rows = []
    for mode in ("BASELINE", "TORUK"):
        for name, messages in scenarios.items():
            response = backend.reply_with_metrics(
                messages, args.max_new_tokens, mode=mode, temperature=0
            )
            rows.append({"scenario": name, "request": messages, "response": response})
        history = [
            {"role": "user", "content": "open youtube"},
            {"role": "assistant", "content": OBSERVED_REPLY},
        ]
        for question, budget in (("what is 5", 32), ("what is 5+5", 32), ("what is 5+5", 64)):
            history.append({"role": "user", "content": question})
            response = backend.reply_with_metrics(history, budget, mode=mode, temperature=0)
            rows.append(
                {
                    "scenario": "reported_transcript_replay",
                    "request": list(history),
                    "max_new_tokens": budget,
                    "response": response,
                }
            )
            history.append({"role": "assistant", "content": response["answer"]})
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": "what are you?"},
            {
                "role": "assistant",
                "content": "I'm a chatbot designed to assist users with various topics.",
            },
            {"role": "user", "content": "i am JinSakai"},
            {
                "role": "assistant",
                "content": (
                    "I'm sorry for any confusion, but as a chatbot, I don't have the ability "
                    "to assist with specific queries or provide information about specific topics."
                ),
            },
        ]
        for question, budget in (
            ("open youtube", 32),
            ("what is 5", 32),
            ("what is 5+5", 32),
            ("what is 5+5", 64),
        ):
            history.append({"role": "user", "content": question})
            response = backend.reply_with_metrics(history, budget, mode=mode, temperature=0)
            rows.append(
                {
                    "scenario": "full_history_generated",
                    "request": list(history),
                    "max_new_tokens": budget,
                    "response": response,
                }
            )
            history.append({"role": "assistant", "content": response["answer"]})
        fixed_history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": "what are you?"},
            {
                "role": "assistant",
                "content": "I'm a chatbot designed to assist users with various topics.",
            },
            {"role": "user", "content": "i am JinSakai"},
            {
                "role": "assistant",
                "content": (
                    "I'm sorry for any confusion, but as a chatbot, I don't have the ability "
                    "to assist with specific queries or provide information about specific topics."
                ),
            },
            {"role": "user", "content": "open youtube"},
            {"role": "assistant", "content": OBSERVED_REPLY},
            {"role": "user", "content": "what is 5"},
            {"role": "assistant", "content": OBSERVED_REPLY},
            {"role": "user", "content": "what is 5+5"},
        ]
        for budget in (32, 64):
            response = backend.reply_with_metrics(fixed_history, budget, mode=mode, temperature=0)
            rows.append(
                {
                    "scenario": "full_history_matched",
                    "request": fixed_history,
                    "max_new_tokens": budget,
                    "response": response,
                }
            )
    report = {"model": backend.model_id, "max_new_tokens": args.max_new_tokens, "rows": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
