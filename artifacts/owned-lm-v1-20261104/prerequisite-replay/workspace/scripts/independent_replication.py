"""Sealed, bounded independent chat evaluation; local pinned weights only."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import independent_cases as data
import psutil
import recall_study as study
import torch
from compare_recall_runs import compare

from toruk_lm.chat_foundation import CHAT_INSTRUCTIONS
from toruk_lm.rank_budget import RankBudgetEnvelopeSelector, RankBudgetSelector
from toruk_lm.source_spans import SourceEnvelopeBackend, SourceSpanSelector

ROOT = data.ROOT
METHODS = ("recent", "lexical", "toruk", "no_envelope", "no_learned_rank", "restore_cutoff")
PROTOCOL = ROOT / "docs/research/independent-replication-v1-protocol.md"
FREEZE = ROOT / "artifacts/independent-replication-20261104/mechanism-freeze.json"


class ConstantRanker:
    """Remove the learned scorer, keeping its candidate set and tie-breaking."""

    sha256 = "constant-score-ablation-v1"

    def score(self, query: str, content: str, role: str, index: int, total: int) -> float:
        return 0.0


def methods() -> dict[str, Any]:
    ranker = study.ChatRelevanceSelector(study.SELECTOR)
    return {
        "recent": None,
        "lexical": study.LexicalContextSelector(),
        "toruk": RankBudgetEnvelopeSelector(ranker),
        "no_envelope": RankBudgetSelector(ranker),
        "no_learned_rank": RankBudgetEnvelopeSelector(ConstantRanker()),
        "restore_cutoff": SourceSpanSelector(ranker),
    }


class MeasuredBackend(SourceEnvelopeBackend):
    """Count actual request tokenization and fitting, without repeated fit probes."""

    def reset_measurements(self) -> None:
        self.phase = "history"
        self.work = {"history_token_positions": 0, "fit_token_positions": 0, "fit_attempts": 0}
        self.selection_ms = 0.0
        self.fit_ms = 0.0
        self.history_tokenization_ms = 0.0
        self.generation_ms = 0.0
        self.before: list[int] = []
        self.chosen: list[int] = []
        self.prompt_ids: list[int] = []
        self.generated_ids: list[int] = []

    def _tokens(self, messages: list[dict[str, str]]) -> torch.Tensor:
        started = time.perf_counter()
        tokens = super()._tokens(messages)
        count = int(tokens.shape[-1])
        if self.phase == "fit":
            self.work["fit_token_positions"] += count
            self.work["fit_attempts"] += 1
        else:
            self.work["history_token_positions"] += count
            self.history_tokenization_ms += (time.perf_counter() - started) * 1000
        return tokens

    def _fit(
        self, messages: list[dict[str, str]], indices: list[int]
    ) -> tuple[torch.Tensor, list[int]]:
        self.before = list(indices)
        started = time.perf_counter()
        self.phase = "fit"
        try:
            tokens, chosen = super()._fit(messages, indices)
        finally:
            self.phase = "history"
        self.fit_ms = (time.perf_counter() - started) * 1000
        self.chosen = list(chosen)
        self.prompt_ids = tokens[0].tolist()
        return tokens, chosen


def instrument(backend: MeasuredBackend, selectors: dict[str, Any]) -> None:
    generate = backend.model.generate

    def timed_generate(**kwargs: Any) -> Any:
        started = time.perf_counter()
        result = generate(**kwargs)
        backend.generation_ms = (time.perf_counter() - started) * 1000
        backend.generated_ids = result[0, kwargs["input_ids"].shape[-1] :].tolist()
        return result

    backend.model.generate = timed_generate
    for selector in selectors.values():
        if selector is None:
            continue

        def attach(current: Any) -> None:
            select = current.select

            def timed_select(messages: list[dict[str, str]]) -> tuple[list[int], bool]:
                started = time.perf_counter()
                result: tuple[list[int], bool] = select(messages)
                backend.selection_ms = (time.perf_counter() - started) * 1000
                return result

            current.select = timed_select

        attach(selector)


def resolve(relative: str) -> Path:
    return ROOT / relative.replace("\\", "/")


def verify(run: Path) -> dict[str, Any]:
    manifest = json.loads((run / "registration.json").read_text(encoding="utf-8"))
    for path, digest in manifest["bindings"].items():
        if data.sha(resolve(path)) != digest:
            raise ValueError(f"Registered dependency drift: {path}")
    for name, digest in manifest["datasets"].items():
        if data.sha(run / name) != digest:
            raise ValueError(f"Registered dataset drift: {name}")
    for name, expected in manifest.get("dependencies", {}).items():
        if importlib.metadata.version(name) != expected:
            raise ValueError(f"Registered dependency version drift: {name}")
    return manifest


def validate_cases(run: Path) -> None:
    """CI validation requires source cards only; no model or historical artifacts."""
    cases = data.build()
    # This checks the question/oracle contract, not any model's capability.
    for case in cases:
        if case["task"] in ("exact", "vague_clear"):
            assert study.score(case["groups"][0][0], case)["correct"]
        else:
            assert study.score("Could you clarify?", case)["correct"]
    run.mkdir(parents=True, exist_ok=False)
    study.write(run / "cases.json", cases)
    study.write(
        run / "validation.json",
        {
            "status": "PASS",
            "scope": "dataset/oracle/schema validation only; no backbone inference",
            "seed": data.SEED,
            "n": len(cases),
            "cards_sha256": data.sha(data.CARDS),
            "cases_sha256": data.sha(run / "cases.json"),
        },
    )
    print("Validated 24 independent cases; no model inference.")


def register(run: Path, phase1: Path) -> None:
    comparison = json.loads((phase1 / "comparison.json").read_text(encoding="utf-8"))
    if not comparison["exact_reproduction"]:
        raise ValueError("Phase 1 reproduction gate failed")
    if not compare(ROOT / "artifacts/rank-budget-v1-20261104", phase1)["exact_reproduction"]:
        raise ValueError("Phase 1 raw-answer reproduction gate failed")
    study.verify(phase1, True)
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    for path, digest in frozen["bindings"].items():
        if data.sha(resolve(path)) != digest:
            raise ValueError(f"Mechanism freeze drift: {path}")
    independent = data.build()
    leakage = data.leakage_audit(independent)
    run.mkdir(parents=True, exist_ok=False)
    study.write(run / "independent.json", independent)
    controlled = json.loads((phase1 / "heldout.json").read_text(encoding="utf-8"))
    study.write(run / "controlled.json", controlled)
    study.write(run / "leakage-audit.json", leakage)
    paths = [
        Path(__file__),
        data.CARDS,
        ROOT / "scripts/independent_cases.py",
        ROOT / "scripts/report_independent_replication.py",
        ROOT / "scripts/recall_study.py",
        ROOT / "scripts/compare_recall_runs.py",
        ROOT / "tests/test_independent_replication.py",
        FREEZE,
        PROTOCOL,
        phase1 / "comparison.json",
        phase1 / "development.jsonl",
        phase1 / "heldout.jsonl",
        phase1 / "registration.json",
    ]
    bindings = {path.replace("\\", "/"): digest for path, digest in frozen["bindings"].items()}
    bindings.update(leakage["historical_bindings"])
    bindings.update({path.resolve().relative_to(ROOT).as_posix(): data.sha(path) for path in paths})
    study.write(
        run / "registration.json",
        {
            "schema": "toruk-independent-replication-v1",
            "bindings": bindings,
            "datasets": {
                name: data.sha(run / name)
                for name in ("independent.json", "controlled.json", "leakage-audit.json")
            },
            "settings": frozen["settings"],
            "methods": list(METHODS),
            "method_order": "rotate by case index modulo 6",
            "seed": data.SEED,
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "python": sys.version,
            "platform": platform.platform(),
            "dependencies": {
                name: importlib.metadata.version(name)
                for name in ("torch", "transformers", "tokenizers", "safetensors", "psutil")
            },
            "new_training_steps": 0,
        },
    )
    print("Registered datasets, mechanisms, scoring, settings and dependencies.")


def evaluate(run: Path, suite: str) -> None:
    started = time.perf_counter()
    output = run / f"{suite}.jsonl"
    if output.exists() or (run / f"{suite}-cost.json").exists():
        raise ValueError("Refusing existing evaluation outputs")
    verify(run)
    cases = json.loads((run / f"{suite}.json").read_text(encoding="utf-8"))
    backend = MeasuredBackend(study.BACKBONE)
    selectors = methods()
    instrument(backend, selectors)
    process = psutil.Process()
    loop_start = time.perf_counter()
    with output.open("x", encoding="utf-8") as stream:
        for index, case in enumerate(cases):
            order = METHODS[index % len(METHODS) :] + METHODS[: index % len(METHODS)]
            for method in order:
                if time.perf_counter() - started > 1200:
                    raise TimeoutError("Bounded evaluation exceeded 1200 seconds")
                backend.selector = selectors[method]
                backend.selector_id = method
                backend.reset_measurements()
                rss_before = process.memory_info().rss
                cpu_start = time.process_time()
                response = backend.reply_with_metrics(
                    case["messages"],
                    48,
                    mode="BASELINE" if method == "recent" else "TORUK",
                    temperature=0,
                    top_p=1,
                )
                cpu_ms = (time.process_time() - cpu_start) * 1000
                memory = process.memory_info()._asdict()
                assert backend.chosen == [
                    int(item[1:]) for item in response["metrics"]["selected_message_ids"]
                ]
                retained = set(case["evidence"]) <= set(backend.chosen)
                scores = study.score(response["answer"], case)
                row = {
                    "schema": "toruk-independent-answer-v1",
                    "suite": suite,
                    "case": case,
                    "method": method,
                    "order": list(order),
                    **response,
                    **scores,
                    "evidence_retained": retained,
                    "failure": None
                    if scores["correct"]
                    else ("generation_despite_evidence" if retained else "lost_evidence"),
                    "selected_before_fit": backend.before,
                    "selected_after_fit": backend.chosen,
                    "selected_evidence": [
                        {
                            "turn": i,
                            "role": case["messages"][i]["role"],
                            "content": case["messages"][i]["content"],
                            "sha256": hashlib.sha256(
                                case["messages"][i]["content"].encode()
                            ).hexdigest(),
                        }
                        for i in backend.chosen
                    ],
                    "prompt_ids": backend.prompt_ids,
                    "generated_ids": backend.generated_ids,
                    "work": {
                        **backend.work,
                        "prefill_tokens": response["metrics"]["selected_context_tokens"],
                        "output_tokens": response["metrics"]["output_tokens"],
                        "logical_scan_bytes": sum(
                            len(m["content"].encode()) for m in case["messages"]
                        )
                        if backend.selector is not None
                        else 0,
                        "source_bytes": sum(
                            len(case["messages"][i]["content"].encode()) for i in backend.before
                        ),
                    },
                    "timing": {
                        "selector_ms": backend.selection_ms,
                        "history_tokenization_ms": backend.history_tokenization_ms,
                        "fit_ms": backend.fit_ms,
                        "model_generate_ms": backend.generation_ms,
                        "request_cpu_ms": cpu_ms,
                    },
                    "memory": {
                        "rss_before": rss_before,
                        "rss_after": memory["rss"],
                        "peak_bytes": memory.get("peak_wset", memory["rss"]),
                        "peak_scope": "OS process high water"
                        if "peak_wset" in memory
                        else "sampled RSS",
                    },
                }
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                print(suite, case["id"], method, scores["correct"], flush=True)
    study.write(
        run / f"{suite}-cost.json",
        {
            "startup_seconds": loop_start - started,
            "loop_seconds": time.perf_counter() - loop_start,
            "function_wall_seconds": time.perf_counter() - started,
            "rows": len(cases) * len(METHODS),
            "note": "Full subprocess additionally includes Python/import startup; see check log.",
        },
    )


def audit(run: Path) -> None:
    from transformers import AutoTokenizer

    verify(run)
    backend = MeasuredBackend.__new__(MeasuredBackend)
    backend.tokenizer = AutoTokenizer.from_pretrained(study.BACKBONE, local_files_only=True)
    backend.system_prompt = CHAT_INSTRUCTIONS
    selectors = methods()
    total = 0
    for suite, n in (("independent", 24), ("controlled", 12)):
        rows = [
            json.loads(line)
            for line in (run / f"{suite}.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        cases = json.loads((run / f"{suite}.json").read_text(encoding="utf-8"))
        gold = {case["id"]: case for case in cases}
        if len(rows) != n * len(METHODS) or len(
            {(r["case"]["id"], r["method"]) for r in rows}
        ) != len(rows):
            raise ValueError("Incomplete or duplicate evaluation rows")
        for row in rows:
            case = row["case"]
            assert case == gold[case["id"]]
            assert all(row[key] == value for key, value in study.score(row["answer"], case).items())
            backend.selector = selectors[row["method"]]
            backend.reset_measurements()
            backend._tokens(case["messages"])
            indices = (
                list(range(len(case["messages"])))
                if backend.selector is None
                else backend.selector.select(case["messages"])[0]
            )
            tokens, chosen = backend._fit(case["messages"], indices)
            assert chosen == row["selected_after_fit"] and indices == row["selected_before_fit"]
            assert tokens[0].tolist() == row["prompt_ids"]
            assert int(tokens.shape[-1]) <= 512
            assert row["evidence_retained"] == (set(case["evidence"]) <= set(chosen))
            assert (
                backend.tokenizer.decode(row["generated_ids"], skip_special_tokens=True).strip()
                == row["answer"]
            )
            assert len(row["generated_ids"]) == row["metrics"]["output_tokens"]
            assert row["work"]["output_tokens"] == len(row["generated_ids"])
            assert row["work"]["prefill_tokens"] == int(tokens.shape[-1])
            assert row["metrics"]["input_tokens"] == backend.work["history_token_positions"]
            assert row["work"]["source_bytes"] == sum(
                len(case["messages"][i]["content"].encode()) for i in indices
            )
            assert row["work"]["logical_scan_bytes"] == (
                sum(len(m["content"].encode()) for m in case["messages"])
                if backend.selector is not None
                else 0
            )
            assert all(row["work"][key] == value for key, value in backend.work.items())
            decoded = backend.tokenizer.decode(row["prompt_ids"], skip_special_tokens=False)
            for source in row["selected_evidence"]:
                content = case["messages"][source["turn"]]["content"]
                assert source["content"] == content and content in decoded
                assert source["sha256"] == hashlib.sha256(content.encode()).hexdigest()
            total += 1
    study.write(run / "audit.json", {"status": "PASS", "rows": total, "model_inference": False})
    print(f"Audited {total} answers, prompts, sources, scores and tokenization work.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "evaluate", "audit", "validate-cases"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--phase1", type=Path)
    parser.add_argument("--suite", choices=("controlled", "independent"))
    args = parser.parse_args()
    if args.action == "validate-cases":
        validate_cases(args.run)
    elif args.action == "register":
        if args.phase1 is None:
            parser.error("register requires --phase1")
        register(args.run, args.phase1)
    elif args.action == "evaluate":
        if args.suite is None:
            parser.error("evaluate requires --suite")
        evaluate(args.run, args.suite)
    else:
        audit(args.run)


if __name__ == "__main__":
    main()
