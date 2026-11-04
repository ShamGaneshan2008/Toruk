"""Fixed-question, fixed-backbone follow-up to the reproduced recall V2 study."""

import argparse
import json
import sys
from pathlib import Path

import recall_study as study
import recall_v2

import toruk_lm.source_spans as spans
from toruk_lm.rank_budget import RankBudgetEnvelopeSelector

BASE_BINDINGS = recall_v2.bindings


def bindings() -> dict[str, str]:
    result = BASE_BINDINGS()
    for name in (
        "scripts/rank_budget_study.py",
        "docs/research/recall-v2-protocol.md",
        "tests/test_rank_budget.py",
    ):
        path = study.ROOT / name
        result[str(path.relative_to(study.ROOT))] = study.sha(path)
    return result


def configure() -> None:
    # Both evaluation and tokenizer-only reporting construct the candidate in
    # the existing "new" method slot. The other three methods remain unchanged.
    spans.SourceSpanSelector = RankBudgetEnvelopeSelector
    study.PROTOCOL = study.ROOT / "docs/research/rank-budget-v1-protocol.md"
    study.cases = recall_v2.strict_cases
    study.bindings = bindings
    study.PretrainedChatBackend = spans.SourceEnvelopeBackend


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "development", "heldout", "report"))
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    configure()
    if args.action == "register":
        study.register(args.run)
        study.write(args.run / "heldout.json", recall_v2.strict_cases("heldout"))
        study.write(
            args.run / "intervention.json",
            {
                "bindings": bindings(),
                "heldout_sha256": study.sha(args.run / "heldout.json"),
                "rationale": "Remove only the absolute cutoff; retain learned top-two ranking.",
            },
        )
    elif args.action == "report":
        import report_recall

        sys.argv = [sys.argv[0], "--run", str(args.run)]
        report_recall.main()
    else:
        if args.action == "heldout":
            frozen = json.loads((args.run / "development-freeze.json").read_text(encoding="utf-8"))
            for name, digest in frozen.items():
                if study.sha(args.run / name) != digest:
                    raise ValueError("development freeze drift")
        study.evaluate(args.run, args.action)
        if args.action == "development":
            rows = (args.run / "development.jsonl").read_text(encoding="utf-8").splitlines()
            if len(rows) != 48:
                raise ValueError("incomplete development")
            study.write(
                args.run / "development-freeze.json",
                {
                    name: study.sha(args.run / name)
                    for name in ("development.jsonl", "development-cost.json", "intervention.json")
                },
            )


if __name__ == "__main__":
    main()
