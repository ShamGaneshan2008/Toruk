"""Strict-template follow-up using the unchanged frozen V1 scorer and intervention."""

import argparse
from pathlib import Path
from typing import Any

import recall_study as study

from toruk_lm.source_spans import SourceEnvelopeBackend

BASE_CASES = study.cases
BASE_BINDINGS = study.bindings


def strict_cases(split: str) -> list[dict[str, Any]]:
    n = {"training": 0, "development": 1, "heldout": 2}[split]
    result = BASE_CASES(split)
    for index, case in enumerate(result):
        p = ("Larch", "Zephyr", "Marigold")[n] + str(index)
        other = ("Aster", "Beryl", "Nacre")[n] + str(index)
        name = ("Tavian", "Seren", "Ysolde")[n]
        value = ("T", "D", "H")[n] + f"/{index}: 9_x!"
        old = f"obsolete-{n}-{index}"
        date = ("2041-01-09", "2042-02-10", "2043-03-11")[n]
        phrase = ("Keep;  calm!", "Count:  four beats!", "Wait?  Five turns.")[n]
        code_fact = (
            f"Project {p} has access code {value}.",
            f"The credential used to access {p} is {value}.",
            f"To unlock the project named {p}, enter {value}",
        )[n]
        code_query = (
            f"What is {p}'s code? Output only its exact bytes.",
            f"Give only the credential used to access {p}, including spacing.",
            f"Return verbatim the string that unlocks {p}; add no explanation.",
        )[n]
        kind = case["id"].split("-", 1)[1]
        records = [code_fact]
        question = code_query
        groups = [[value]]
        forbidden: list[str] = []
        if kind == "exact_quote":
            records = [
                (
                    f'{name} wrote "{phrase}" as a motto.',
                    f'The motto on {name}\'s badge reads "{phrase}".',
                    f'On the plaque belonging to {name}, these words appear: "{phrase}"',
                )[n]
            ]
            question = (
                f"Repeat {name}'s motto without enclosing quotes.",
                f"Transcribe just the badge motto for {name}; preserve every character.",
                f"Copy the words on {name}'s plaque exactly, omitting outer quote marks.",
            )[n]
            groups = [[phrase]]
        elif kind == "correction":
            records = [
                (
                    f"Project {p} has access code {old}.",
                    f"The credential used to access {p} is {old}.",
                    f"To unlock the project named {p}, enter {old}",
                )[n],
                (
                    f"Correction: project {p} access code is now {value}.",
                    f"I need to correct {p}'s credential: replace the previous one with {value}",
                    f"Revision for {p}: the old unlock string was mistaken; use {value} instead.",
                )[n],
            ]
            forbidden = [old]
        elif kind == "preservation":
            records += [
                (
                    f"Project {p} launches 2040-01-01.",
                    f"The scheduled launch of {p} was January 1, 2040.",
                    f"For {p}, a launch had been pencilled in for the first day of 2040.",
                )[n],
                (
                    f"Correction: project {p} launch is {date}; the code stays valid.",
                    f"Update only {p}'s launch to {date}. Leave its credential untouched.",
                    f"The calendar entry for {p} should read {date}. No unlock-string change.",
                )[n],
            ]
        elif kind == "name_date":
            records = [
                (
                    f"The lead of {p} is {name}, starting {date}.",
                    f"{name} takes charge of {p} on {date}.",
                    f"Leadership duties at {p} begin for {name} from {date}.",
                )[n]
            ]
            question = (
                f"When does {p}'s lead start? Date only, YYYY-MM-DD.",
                f"State only the YYYY-MM-DD date when {name} takes charge.",
                f"Which calendar date begins {name}'s leadership? Output YYYY-MM-DD only.",
            )[n]
            groups = [[date]]
        elif kind in ("gist", "gist_correction"):
            policy = (
                f"{p} holds messages while offline and retries when the network returns.",
                f"{p} queues outgoing messages during disconnection, then sends on recovery.",
                f"A network outage makes {p} retain unsent messages; it retries once online.",
            )[n]
            records = [policy]
            if kind == "gist_correction":
                records = [
                    (
                        f"{p} deletes messages during outages.",
                        f"The earlier policy at {p} was to discard undelivered messages.",
                        f"Previously, unsent messages at {p} were erased on disconnection.",
                    )[n],
                    (
                        "Correction: " + policy,
                        "Replace that policy: " + policy,
                        "Revised behavior, superseding the old rule: " + policy,
                    )[n],
                ]
            question = (
                f"What does {p} do about messages during outages?",
                f"Explain {p}'s current handling of disconnected delivery.",
                f"Describe how unsent messages survive and resume delivery at {p}.",
            )[n]
            groups = case["groups"]
            forbidden = case["forbidden"]
        elif kind in ("clear", "clear_gap", "ambiguous"):
            if kind == "ambiguous":
                records.append(
                    (
                        f"Project {other} has access code {old}.",
                        f"The credential used to access {other} is {old}.",
                        f"To unlock the project named {other}, enter {old}",
                    )[n]
                )
                groups, forbidden = [], [value, old]
            question = (
                "What is its code?",
                "Give the access credential belonging to that one.",
                "What string unlocks it? Give the exact string only.",
            )[n]
            if kind == "clear_gap":
                question = (
                    "Tell me that earlier project's code.",
                    "Which credential was assigned to the project mentioned before?",
                    "Repeat the unlock string for the earlier project.",
                )[n]
        elif kind == "missing":
            records, groups = [], []
            question = (
                f"What is {name}'s locker code?",
                f"Tell me the private locker credential belonging to {name}.",
                f"Supply the combination for {name}'s personal locker.",
            )[n]
        messages = []
        for record in records:
            messages.extend(
                [{"role": "user", "content": record}, {"role": "assistant", "content": "Recorded."}]
            )
        evidence = list(range(0, len(messages), 2))
        # Keep only the non-task-bearing long-gap scaffold from V1.
        weather = case["messages"][len(case["evidence"]) * 2 : -1]
        messages.extend(weather)
        messages.append({"role": "user", "content": question})
        case.update(
            id=f"v2-{split}-{kind}",
            messages=messages,
            evidence=evidence,
            groups=groups,
            forbidden=forbidden,
        )
    return result


def bindings() -> dict[str, str]:
    result = BASE_BINDINGS()
    for path in (Path(__file__), Path("docs/research/recall-v1-protocol.md")):
        result[str(path.resolve().relative_to(study.ROOT))] = study.sha(path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "development", "heldout"))
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    study.PROTOCOL = study.ROOT / "docs/research/recall-v2-protocol.md"
    study.cases = strict_cases
    study.bindings = bindings
    study.PretrainedChatBackend = SourceEnvelopeBackend
    if args.action == "register":
        study.register(args.run)
        study.write(args.run / "heldout.json", strict_cases("heldout"))
        study.write(
            args.run / "intervention.json",
            {
                "bindings": {
                    str(path): study.sha(path)
                    for path in (
                        Path("src/toruk_lm/source_spans.py"),
                        Path("tests/test_source_spans.py"),
                    )
                },
                "heldout_sha256": study.sha(args.run / "heldout.json"),
                "rationale": "Unchanged V1 development-selected intervention; strict templates.",
            },
        )
    else:
        if args.action == "heldout":
            rows = (args.run / "development.jsonl").read_text(encoding="utf-8").splitlines()
            if len(rows) != 48 or not (args.run / "development-cost.json").exists():
                raise ValueError("finish development before heldout")
        study.evaluate(args.run, args.action)


if __name__ == "__main__":
    main()
