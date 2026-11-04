"""Bounded, sealed exact/gist/reference study; no gold labels enter inference."""

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psutil
import torch

from toruk_lm.chat_foundation import PretrainedChatBackend
from toruk_lm.chat_selector import ChatRelevanceSelector
from toruk_lm.context_selection import LexicalContextSelector

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/recall-v1-protocol.md"
BACKBONE = ROOT / "artifacts/qwen-chat-001/backbone"
SELECTOR = ROOT / "artifacts/chat-selector-v2-20261101/selector.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def cases(split: str) -> list[dict[str, Any]]:
    """Offline-only labels and disjoint wording. No fitted model or runtime parser."""
    n = {"training": 0, "development": 1, "heldout": 2}[split]
    person = ("Iona", "Velin", "Oraya")[n]
    project = ("Kestrel", "Cobalt", "Juniper")[n]
    other = ("Maple", "Saffron", "Quartz")[n]
    code = ("TR:8_x!", "DV:4_q!", "HO:7_z!")[n]
    old = ("TR-OLD", "DV-OLD", "HO-OLD")[n]
    date = ("2031-02-06", "2032-03-07", "2033-04-08")[n]
    phrase = ("Wait; then go!", "Pause:  two steps!", "Look;  three times?")[n]
    fact = (
        f"Project {project} has access code {code}.",
        f"The access code assigned to project {project} is {code}.",
        f"For {project}, use this access code: {code}",
    )[n]
    query = (
        f"What is project {project}'s access code? Reply with the code only.",
        f"Give only the access code for project {project}.",
        f"Return project {project}'s access code verbatim, without explanation.",
    )[n]
    rows: list[tuple[str, str, list[str], str, list[list[str]], list[str]]] = [
        ("exact_code", "exact", [fact], query, [[code]], []),
        ("exact_code_gap", "exact", [fact], query, [[code]], []),
        (
            "exact_quote",
            "exact",
            [f'{person} wrote this motto: "{phrase}"'],
            f"Repeat {person}'s motto exactly, excluding the enclosing quotation marks.",
            [[phrase]],
            [],
        ),
        (
            "correction",
            "exact",
            [
                f"Project {project} access code is {old}.",
                f"Correction: project {project} access code is now {code}.",
            ],
            query,
            [[code]],
            [old],
        ),
        (
            "preservation",
            "exact",
            [
                fact,
                f"Project {project} launch is 2030-01-01.",
                f"Correction: project {project} launch is now {date}. The code is unchanged.",
            ],
            query,
            [[code]],
            [],
        ),
        (
            "name_date",
            "exact",
            [f"The lead of {project} is {person}, starting {date}."],
            f"Return only the start date of {project}'s lead in YYYY-MM-DD format.",
            [[date]],
            [],
        ),
        (
            "gist",
            "gist",
            [
                (
                    f"{project} delays sending messages until the network returns, then retries.",
                    f"When offline, {project} holds outgoing messages and sends them after reconnection.",
                    f"{project} keeps messages during a connection outage; on recovery it retries delivery.",
                )[n]
            ],
            f"How does {project} handle messages during a network outage?",
            [
                ["hold", "keep", "queue", "store", "delay", "retain"],
                ["reconnect", "return", "recover", "restor", "back", "available", "online"],
            ],
            [],
        ),
        (
            "gist_correction",
            "gist",
            [
                f"{project} deletes messages while offline.",
                f"Correction: {project} queues messages while offline and retries after reconnection.",
            ],
            f"Describe {project}'s current offline message policy.",
            [["queue", "store", "keep", "hold", "retain"], ["retr", "resend", "send"]],
            ["deletes", "discards"],
        ),
        (
            "clear",
            "vague_clear",
            [fact],
            (
                "What is its access code?",
                "Give its access code only.",
                "Which access code belongs to it? Reply with the code only.",
            )[n],
            [[code]],
            [],
        ),
        (
            "clear_gap",
            "vague_clear",
            [fact],
            (
                "What is that project's access code?",
                "What code did that earlier project use?",
                "Give the access code of the earlier project.",
            )[n],
            [[code]],
            [],
        ),
        (
            "ambiguous",
            "vague_ambiguous",
            [fact, f"Project {other} has access code {old}."],
            (
                "What is its access code?",
                "Which access code does it use?",
                "Tell me that one's access code.",
            )[n],
            [],
            [code, old],
        ),
        ("missing", "missing", [], f"What is {person}'s private locker code?", [], []),
    ]
    result = []
    for kind, task, records, question, groups, forbidden in rows:
        messages = []
        for record in records:
            messages.extend(
                [{"role": "user", "content": record}, {"role": "assistant", "content": "Noted."}]
            )
        evidence = list(range(0, len(messages), 2))
        for gap in range(18):
            messages.extend(
                [
                    {
                        "role": "user",
                        "content": f"Unrelated weather note {gap}: clouds drift east; no project update.",
                    },
                    {"role": "assistant", "content": "Weather note received."},
                ]
            )
        messages.append({"role": "user", "content": question})
        result.append(
            {
                "id": f"{split}-{kind}",
                "split": split,
                "task": task,
                "messages": messages,
                "evidence": evidence,
                "groups": groups,
                "forbidden": forbidden,
            }
        )
    return result


def score(answer: str, case: dict[str, Any]) -> dict[str, Any]:
    lower = answer.casefold()
    uncertain = bool(
        re.search(
            r"don't know|do not know|not (?:provided|specified|clear)|unclear|ambiguous|"
            r"which (?:one|project)|could (?:you|refer)|clarif|cannot determine|can't determine|"
            r"not enough|insufficient",
            lower,
        )
    )
    forbidden = any(value.casefold() in lower for value in case["forbidden"])
    task = case["task"]
    if task == "exact":
        correct = answer.strip() == case["groups"][0][0]
    elif task in ("missing", "vague_ambiguous"):
        correct = uncertain and not forbidden
    else:
        correct = (
            all(any(value.casefold() in lower for value in group) for group in case["groups"])
            and not forbidden
        )
    return {
        "correct": correct,
        "exact_string": correct if task == "exact" else None,
        "gist_correct": correct if task == "gist" else None,
        "referent_correct": correct if task.startswith("vague") else None,
        "appropriate_clarification": correct if task == "vague_ambiguous" else None,
        "unsupported": forbidden or (task in ("missing", "vague_ambiguous") and not uncertain),
    }


def bindings() -> dict[str, str]:
    paths = [
        Path(__file__),
        PROTOCOL,
        SELECTOR,
        *sorted((ROOT / "src/toruk_lm").glob("*.py")),
        *sorted(path for path in BACKBONE.iterdir() if path.is_file()),
    ]
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def register(run: Path) -> None:
    run.mkdir(parents=True, exist_ok=False)
    write(run / "training.json", cases("training"))
    write(run / "development.json", cases("development"))
    write(
        run / "registration.json",
        {
            "schema": "recall-v1",
            "bindings": bindings(),
            "data": {name: sha(run / f"{name}.json") for name in ("training", "development")},
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "settings": {"prompt_tokens": 512, "output_tokens": 48, "temperature": 0, "top_p": 1},
        },
    )


def verify(run: Path, final: bool = False) -> None:
    seal = json.loads((run / "registration.json").read_text(encoding="utf-8"))
    for path, digest in seal["bindings"].items():
        if sha(ROOT / path) != digest:
            raise ValueError(f"registered input drift: {path}")
    for name, digest in seal["data"].items():
        if sha(run / f"{name}.json") != digest:
            raise ValueError("dataset drift")
    if final:
        frozen = json.loads((run / "intervention.json").read_text(encoding="utf-8"))
        for path, digest in frozen["bindings"].items():
            if sha(ROOT / path) != digest:
                raise ValueError("intervention drift")
        if sha(run / "heldout.json") != frozen["heldout_sha256"]:
            raise ValueError("heldout drift")


def evaluate(run: Path, stage: str) -> None:
    verify(run, stage != "before")
    output = run / f"{stage}.jsonl"
    if output.exists():
        raise ValueError("refusing existing outputs")
    split = "heldout" if stage == "heldout" else "development"
    data = json.loads((run / f"{split}.json").read_text(encoding="utf-8"))
    backend = PretrainedChatBackend(BACKBONE)
    trained = ChatRelevanceSelector(SELECTOR)
    methods: dict[str, Any] = {"recent": None, "lexical": LexicalContextSelector(), "old": trained}
    if stage != "before":
        from toruk_lm.source_spans import SourceSpanSelector

        methods["new"] = SourceSpanSelector(trained)
    started = time.perf_counter()
    with output.open("x", encoding="utf-8") as stream:
        for case in data:
            for method, selector in methods.items():
                backend.selector = selector
                backend.selector_id = getattr(
                    selector, "kind", getattr(selector, "selector_id", None)
                )
                scan_start = time.perf_counter()
                indices = (
                    list(range(len(case["messages"])))
                    if selector is None
                    else selector.select(case["messages"])[0]
                )
                selector_ms = (time.perf_counter() - scan_start) * 1000
                fit_start = time.perf_counter()
                tokens, chosen = backend._fit(case["messages"], indices)
                fit_ms = (time.perf_counter() - fit_start) * 1000
                response = backend.reply_with_metrics(
                    case["messages"],
                    48,
                    mode="BASELINE" if selector is None else "TORUK",
                    temperature=0,
                    top_p=1,
                )
                assert chosen == [
                    int(item[1:]) for item in response["metrics"]["selected_message_ids"]
                ]
                retained = set(case["evidence"]) <= set(chosen)
                scored = score(response["answer"], case)
                failure = None
                if not scored["correct"]:
                    failure = "generation_despite_evidence" if retained else "lost_evidence"
                row = {
                    "case": case,
                    "method": method,
                    **response,
                    **scored,
                    "evidence_retained": retained,
                    "failure": failure,
                    "selected_evidence": [
                        {
                            "turn": i,
                            "content": case["messages"][i]["content"],
                            "sha256": hashlib.sha256(
                                case["messages"][i]["content"].encode()
                            ).hexdigest(),
                        }
                        for i in chosen
                    ],
                    "prompt_ids": tokens[0].tolist(),
                    "selector_ms_probe": selector_ms,
                    "fit_ms_probe": fit_ms,
                    "scan_bytes": sum(len(m["content"].encode()) for m in case["messages"])
                    if selector
                    else 0,
                    "source_bytes": sum(
                        len(case["messages"][i]["content"].encode()) for i in indices
                    ),
                    "rss": psutil.Process().memory_info()._asdict(),
                }
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                print(stage, case["id"], method, scored["correct"], failure, flush=True)
    write(
        run / f"{stage}-cost.json",
        {
            "wall_seconds": time.perf_counter() - started,
            "note": "Includes diagnostic selection/fit replay plus measured request; request metrics exclude probe.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("register", "before", "freeze", "development", "heldout")
    )
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "register":
        register(args.run)
    elif args.action == "freeze":
        verify(args.run)
        # The new module is additive, so original registered runtime bytes stay sealed.
        paths = [ROOT / "src/toruk_lm/source_spans.py", ROOT / "tests/test_source_spans.py"]
        write(args.run / "heldout.json", cases("heldout"))
        write(
            args.run / "intervention.json",
            {
                "bindings": {str(path.relative_to(ROOT)): sha(path) for path in paths},
                "heldout_sha256": sha(args.run / "heldout.json"),
                "before_sha256": sha(args.run / "before.jsonl"),
                "rationale": "See development failures and intervention.md; no heldout inference yet.",
            },
        )
    else:
        evaluate(args.run, args.action)


if __name__ == "__main__":
    main()
