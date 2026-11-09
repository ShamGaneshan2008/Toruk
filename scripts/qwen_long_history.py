"""Registered frozen-Qwen long-history comparison; no training."""

import argparse
import importlib.metadata
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, cast

import psutil  # type: ignore[import-untyped]
from qualify_answer_backbone import (
    SYSTEM,
    cpu,
    normalized,
    phrase,
    progress,
    read,
    sha,
    tree_stats,
    verify,
    write,
)
from qualify_answer_backbone import score as base_score

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "qwen-long-history-v1"
KINDS = ("distant", "correction", "distractor", "literal", "preservation", "reference", "missing")
ARMS = ("full", "recent", "lexical", "toruk")


def make_cases(split: str, seed: int, per_kind: int, gap_pairs: int) -> list[dict[str, Any]]:
    if split not in ("development", "heldout"):
        raise ValueError("new long-history split required")
    dev = split == "development"
    rng = random.Random(seed)
    pools = {
        "distant": ["copper quay"]
        if dev
        else ["juniper bridge", "sedge pier", "granite mooring", "birch landing"],
        "correction": ["linen cabinet"]
        if dev
        else ["ceramic cupboard", "woven basket", "ivory drawer", "brass trunk"],
        "distractor": ["mulberry"]
        if dev
        else ["blackcurrant", "gooseberry", "boysenberry", "elderberry"],
        "preservation": ["hyacinth"] if dev else ["anemone", "freesia", "gladiolus", "ranunculus"],
        "reference": ["velvet depot"]
        if dev
        else ["maple annex", "osprey hall", "hazel pavilion", "kestrel station"],
    }
    cases = []
    for kind in KINDS:
        for i in range(per_kind):
            tag = ("LHD-" if dev else "LHH-") + f"{rng.getrandbits(48):012X}"
            other = ("AUXD-" if dev else "AUXH-") + f"{rng.getrandbits(48):012X}"
            pool = pools.get(kind, ["UNKNOWN"])
            value = pool[i % len(pool)]
            alternatives: list[str] = []
            messages: list[dict[str, str]] = []
            required: list[int] = []

            def add(role: str, content: str, target: list[dict[str, str]] = messages) -> int:
                target.append({"role": role, "content": content})
                return len(target) - 1

            if kind == "distant":
                first = (
                    f"Delivery ledger {tag} assigns the meeting point {value}."
                    if dev
                    else f"Shipping register {tag}: the unloading location is {value}."
                )
                required = [add("user", first)]
                question = (
                    f"Which meeting point was assigned in delivery ledger {tag}?"
                    if dev
                    else f"What unloading location is recorded for shipping register {tag}?"
                )
            elif kind == "correction":
                alternatives = ["discarded chest" if dev else "retired locker"]
                add("user", f"The storage location for {tag} is {alternatives[0]}.")
                question = (
                    f"After the update, where is the material for {tag} stored?"
                    if dev
                    else f"Where must the parcel for {tag} be stored under the revised instruction?"
                )
            elif kind == "distractor":
                required = [add("user", f"The approved jam ingredient for order {tag} is {value}.")]
                alternatives = ["damson" if dev else "cloudberry"]
                add("assistant", "The ingredient record is noted.")
                add(
                    "user",
                    f"A different order {other} uses {alternatives[0]}; it is not order {tag}.",
                )
                question = (
                    f"What approved jam ingredient belongs to order {tag}?"
                    if dev
                    else f"Name the jam ingredient approved for order {tag}, not the other order."
                )
            elif kind == "literal":
                letters = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(9))
                value = f"DEV/{letters}:  R-4!" if dev else f"HIST/{letters}:  S_6?"
                required = [add("user", f'The quoted plate for {tag} reads "{value}".')]
                question = (
                    f"Copy only the quoted plate for {tag}, with exact spaces."
                    if dev
                    else f"Return exactly the text inside the quotation on plate {tag}."
                )
            elif kind == "preservation":
                required = [
                    add("user", f"Garden record {tag} names flower {value} and folder shade beige.")
                ]
                question = (
                    f"Which flower remains in garden record {tag}?"
                    if dev
                    else (
                        f"Which flower is still specified by garden record {tag} "
                        "after the folder update?"
                    )
                )
            elif kind == "reference":
                add("assistant", "I cannot name the owner of an unrelated object without a record.")
                required = [add("user", f"Crate {tag} is routed to {value}.")]
                if not dev and i % 2:
                    add("user", f"Crate {other} is routed to willow lodge.")
                    value = "UNKNOWN"
                question = (
                    "Where is that same crate routed?"
                    if dev
                    else (
                        "Where is that crate supposed to go? Give UNKNOWN "
                        "if the referent is ambiguous."
                    )
                )
            else:
                add(
                    "user",
                    f"Inventory {tag} specifies a weight of 23 kilograms and a seal marked PLAIN.",
                )
                question = (
                    f"Which override password is given for inventory {tag}?"
                    if dev
                    else f"What audit password is recorded for inventory {tag}?"
                )
            add("assistant", "Record noted.")
            for j in range(gap_pairs):
                add(
                    "user",
                    f"Archive log {j}: the clerk counted empty folders beside a quiet window, "
                    "then checked the unused shelf and closed the book.",
                )
                add("assistant", "Log noted.")
                if j == 2 and kind == "correction":
                    change = (
                        f"Update for {tag}: replace the old storage location with {value}; "
                        "the earlier entry is obsolete."
                        if dev
                        else (
                            f"Correction for {tag}: store the parcel in {value} instead; "
                            "cancel the retired location."
                        )
                    )
                    required = [add("user", change)]
                    add("assistant", "Revision noted.")
                if j == 3 and kind == "preservation":
                    add(
                        "user",
                        f"Update for garden record {tag}: change only the folder shade to amber; "
                        "keep its flower entry unchanged.",
                    )
                    add("assistant", "Folder update noted.")
            if kind == "reference":
                if not dev and i % 2:
                    add(
                        "user",
                        "I am looking at two crates now. I have not indicated which one I mean.",
                    )
                    required = []
                else:
                    required.append(
                        add(
                            "user",
                            f"I am looking at crate {tag}. "
                            "My next question concerns that same crate.",
                        )
                    )
                add("assistant", "I will use the referenced record.")
            add("user", question)
            cases.append(
                {
                    "schema": SCHEMA,
                    "id": f"lh1-{split}-{kind}-{i}",
                    "kind": kind,
                    "split": split,
                    "question": question,
                    "expected": value,
                    "alternatives": alternatives,
                    "required": required,
                    "messages": messages,
                }
            )
    return cases


def inference_turns(case: dict[str, Any]) -> list[dict[str, str]]:
    if case.get("schema") != SCHEMA:
        raise ValueError("only fresh long-history cases accepted")
    return [{"role": m["role"], "content": m["content"]} for m in case["messages"]]


def envelope(turns: list[dict[str, str]], selected: list[int]) -> list[dict[str, str]]:
    last = len(turns) - 1
    if not selected or selected != sorted(set(selected)) or last not in selected:
        raise ValueError("chronological selection including question required")
    reference = "\n".join(
        f"{turns[i]['role'].capitalize()}: {turns[i]['content']}" for i in selected if i != last
    )
    prompt = f"Reference:\n{reference}\n\nQuestion:\n{turns[-1]['content']}\n\nAnswer:"
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]


def score(answer: str, case: dict[str, Any]) -> dict[str, Any]:
    scored_case = {**case, "kind": "missing" if case["expected"] == "UNKNOWN" else case["kind"]}
    result = base_score(answer, scored_case)
    result["exact_match"] = answer.strip() == case["expected"]
    result["stale_assertion_proxy"] = case["kind"] == "correction" and any(
        phrase(normalized(answer), v) for v in case["alternatives"]
    )
    return result


def failure(result: dict[str, Any], case: dict[str, Any], selected: list[int]) -> str:
    if result["correct"]:
        return "correct"
    if case["expected"] == "UNKNOWN":
        return "unsupported or unresolved question answered without valid abstention"
    if result["stale_assertion_proxy"]:
        return "stale fact asserted"
    if not set(case["required"]) <= set(selected):
        return "required evidence omitted"
    if result["abstention"]:
        return "unnecessary abstention with evidence present"
    return "generator failed with required evidence present"


def records(value: Any) -> list[dict[str, Any]]:
    found = []
    if isinstance(value, dict):
        if "id" in value and any(k in value for k in ("question", "messages", "prompt")):
            found.append(value)
        else:
            for x in value.values():
                found.extend(records(x))
    elif isinstance(value, list):
        for x in value:
            found.extend(records(x))
    return found


def question_key(case: dict[str, Any]) -> str:
    question = case.get("question", "")
    if not question and case.get("messages"):
        question = case["messages"][-1].get("content", "")
    question = re.sub(
        r"\b(?:LH[DH]|AUX[DH]|QUAL[DH])-[0-9A-F]+\b|\b[DH][0-9A-F]{10}\b", "ID", question
    )
    return normalized(question)


def check_overlap(
    dev: list[dict[str, Any]], held: list[dict[str, Any]], prior: list[dict[str, Any]]
) -> dict[str, Any]:
    sets = [dev, held, prior]
    ids = [{str(c["id"]) for c in rows} for rows in sets]
    values = [
        {normalized(str(c.get("expected", c.get("value", "")))) for c in rows} - {"", "unknown"}
        for rows in sets
    ]
    questions = [{question_key(c) for c in rows} - {""} for rows in sets]
    for i, j in ((0, 1), (0, 2), (1, 2)):
        if ids[i] & ids[j] or values[i] & values[j] or questions[i] & questions[j]:
            raise ValueError(
                f"overlap {i}/{j}: IDs={ids[i] & ids[j]}, "
                f"values={values[i] & values[j]}, questions={questions[i] & questions[j]}"
            )
    return {
        "status": "PASS",
        "counts": [len(x) for x in sets],
        "scope": (
            "No shared IDs, known gold values or normalized questions. "
            "Not semantic/pretraining independence."
        ),
    }


def previous_cases(run: Path) -> tuple[list[dict[str, Any]], dict[str, str], list[str]]:
    prior, sources, skipped = [], {}, []
    for folder in ("configs", "artifacts"):
        for path in sorted((ROOT / folder).rglob("*")):
            if (
                not path.is_file()
                or path.is_relative_to(run)
                or path.is_relative_to(ROOT / "artifacts/qwen-long-history-v1")
                or path.suffix not in (".json", ".jsonl")
            ):
                continue
            if any(p in ("backbone", "backbones", "package", "initial-files") for p in path.parts):
                continue
            if path.stat().st_size > 5_000_000:
                skipped.append(path.relative_to(ROOT).as_posix())
                continue
            try:
                data = (
                    [json.loads(s) for s in path.read_text(encoding="utf-8-sig").splitlines()]
                    if path.suffix == ".jsonl"
                    else json.loads(path.read_bytes())
                )
            except (ValueError, OSError):
                skipped.append(path.relative_to(ROOT).as_posix())
                continue
            cases = records(data)
            if cases:
                prior.extend(cases)
                sources[path.relative_to(ROOT).as_posix()] = sha(path)
    return prior, sources, skipped


def training_cost(config: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for prefix in config["cost_policy"]["historical_training_runs"]:
        worker, cost = read(ROOT / (prefix + "-worker.json")), read(ROOT / (prefix + "-cost.json"))
        rows.append(
            {
                "source": prefix,
                "cpu_seconds": worker["lifecycle_cpu_seconds"] + cost["controller_cpu_seconds"],
                "wall_seconds": cost["wall_seconds"],
                "note": "Original training/profile, not rerun. Early parent RAM sampling invalid.",
            }
        )
    return {
        "new_training_seconds": 0,
        "original_profile_and_training": rows,
        "cpu_seconds": sum(x["cpu_seconds"] for x in rows),
        "wall_seconds": sum(x["wall_seconds"] for x in rows),
    }


def register(run: Path, config_path: Path) -> None:
    from transformers import AutoTokenizer

    config = read(config_path)
    qualified_path = ROOT / config["backbone_freeze"]
    qualified = read(qualified_path)
    directory = ROOT / config["backbone_directory"]
    if (
        sha(directory / "model.safetensors") != qualified["model_sha256"]
        or qualified["system_instructions"] != SYSTEM
        or qualified["generation_policy"] != config["generation_policy"]
    ):
        raise ValueError("qualified backbone/decoding identity mismatch")
    old_registration = read(ROOT / "artifacts/backbone-qualification-v1/registration.json")
    if (
        sha(ROOT / "artifacts/backbone-qualification-v1/registration.json")
        != qualified["registration_sha256"]
    ):
        raise ValueError("qualification registration mismatch")
    model_files = [p for p in directory.iterdir() if p.is_file()]
    for p in model_files:
        if sha(p) != old_registration["bindings"][p.relative_to(ROOT).as_posix()]:
            raise ValueError("qualified tokenizer/model file drift")
    if sha(ROOT / config["selector_checkpoint"]) != config["selector_sha256"]:
        raise ValueError("successor selector drift")
    tokenizer = AutoTokenizer.from_pretrained(
        directory, local_files_only=True, trust_remote_code=False
    )
    context_limit = min(
        read(directory / "config.json")["max_position_embeddings"], tokenizer.model_max_length
    )
    dev = make_cases(
        "development",
        config["development_seed"],
        config["development_per_kind"],
        config["gap_pairs"],
    )
    held = make_cases(
        "heldout", config["heldout_seed"], config["heldout_per_kind"], config["gap_pairs"]
    )
    prior, sources, skipped = previous_cases(run)
    overlap = check_overlap(dev, held, prior)
    overlap.update(
        source_files=sources,
        skipped_files=skipped,
        scanner_policy=(
            "Recursive JSON/JSONL <=5 MB in configs/artifacts; model assets, "
            "initial backups and entire current study excluded; archives not searched."
        ),
    )
    prompt_ids = {}
    for case in dev + held:
        turns = inference_turns(case)
        ids = tokenizer.apply_chat_template(
            envelope(turns, list(range(len(turns)))),
            tokenize=True,
            add_generation_prompt=True,
            return_dict=False,
        )
        if not isinstance(ids, list) or any(not isinstance(x, int) for x in ids):
            raise ValueError("flat token IDs required")
        ids = cast(list[int], ids)
        if len(ids) + config["max_new_tokens"] > context_limit:
            raise ValueError(
                "full-evidence overflow; registration blocked, no truncation/exclusion"
            )
        if len(ids) <= config["bounded_prompt_tokens"]:
            raise ValueError("history must exceed bounded prompt budget")
        prompt_ids[case["id"]] = ids
    outputs = {
        "config.json": config,
        "development.json": dev,
        "heldout.json": held,
        "leakage.json": overlap,
        "full-prompt-ids.json": prompt_ids,
        "training-cost.json": training_cost(config),
    }
    for name, value in outputs.items():
        write(run / name, value)
    paths = [
        Path(__file__),
        ROOT / "scripts/qualify_answer_backbone.py",
        config_path,
        ROOT / "tests/test_qwen_long_history.py",
        ROOT / "docs/research/qwen-long-history-v1-protocol.md",
        qualified_path,
        ROOT / "artifacts/backbone-qualification-v1/registration.json",
        ROOT / config["selector_checkpoint"],
        *model_files,
        *list((ROOT / "src/toruk_lm").glob("*.py")),
        *(run / name for name in outputs),
    ]
    for prefix in config["cost_policy"]["historical_training_runs"]:
        paths += [ROOT / (prefix + "-cost.json"), ROOT / (prefix + "-worker.json")]
    with zipfile.ZipFile(run / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for p in paths:
            if p not in model_files and p.suffix != ".pt":
                archive.writestr(p.relative_to(ROOT).as_posix(), p.read_bytes())
    paths.append(run / "source.zip")
    write(
        run / "registration.json",
        {
            "schema": SCHEMA,
            "config": config,
            "qualified": qualified,
            "context_limit": context_limit,
            "system_instructions": SYSTEM,
            "bindings": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
            "model_files": [p.relative_to(ROOT).as_posix() for p in model_files]
            + [config["selector_checkpoint"]],
            "dependencies": {
                n: importlib.metadata.version(n)
                for n in ("torch", "transformers", "tokenizers", "safetensors", "psutil")
            },
            "python": sys.version,
            "registered_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "note": "Tokenizer-only preflight; no inference or new training before registration.",
        },
    )
    print(
        json.dumps(
            {
                "registered": True,
                "cases": [len(dev), len(held)],
                "context_limit": context_limit,
                "full_prompt_range": [
                    min(map(len, prompt_ids.values())),
                    max(map(len, prompt_ids.values())),
                ],
                "previous_records": len(prior),
            }
        )
    )


def validate_full_context(prompt_tokens: int, context_limit: int, answer_tokens: int) -> None:
    if prompt_tokens + answer_tokens > context_limit:
        raise ValueError("full-evidence overflow; no truncation or exclusion")


def fit_context(
    turns: list[dict[str, str]], indices: list[int], encode: Any, limit: int
) -> tuple[list[int], Any, int]:
    chosen = list(indices)
    positions = 0
    while True:
        tokens = encode(envelope(turns, chosen))
        positions += tokens.numel()
        if tokens.shape[-1] <= limit:
            return chosen, tokens, positions
        if len(chosen) == 1:
            raise ValueError("question/instruction exceeds budget")
        chosen.pop(0)


def worker(run: Path, split: str, arm: str) -> None:
    started = time.perf_counter()
    reg = verify(run)
    config = reg["config"]
    import torch
    from transformers import GenerationConfig

    from toruk_lm.chat_foundation import PretrainedChatBackend, TorukContextSelector
    from toruk_lm.context_selection import LexicalContextSelector

    torch.manual_seed(config["generation_seed"])
    torch.use_deterministic_algorithms(True)
    backend = PretrainedChatBackend(ROOT / config["backbone_directory"])
    backend.system_prompt = ""
    backend.model.generation_config = GenerationConfig(
        do_sample=False,
        num_beams=1,
        repetition_penalty=1.0,
        use_cache=True,
        eos_token_id=backend.tokenizer.eos_token_id,
        pad_token_id=backend.tokenizer.pad_token_id,
        max_new_tokens=64,
        temperature=1.0,
        top_p=1.0,
    )
    selector: Any = (
        TorukContextSelector(ROOT / config["selector_checkpoint"])
        if arm == "toruk"
        else LexicalContextSelector("lexical-v1")
        if arm == "lexical"
        else None
    )
    counts: dict[str, int] = {}
    if arm == "lexical":
        from toruk_lm import context_selection

        original_terms = context_selection.terms

        def measured_terms(text: str) -> set[str]:
            counts["lexical_term_calls"] = counts.get("lexical_term_calls", 0) + 1
            counts["lexical_term_bytes"] = counts.get("lexical_term_bytes", 0) + len(text.encode())
            return original_terms(text)

        context_selection.terms = measured_terms

    def hook(key: str) -> Any:
        def count(module: Any, args: Any, kwargs: Any) -> None:
            tokens = kwargs.get("input_ids", args[0] if args else None)
            if tokens is not None:
                counts[key] = counts.get(key, 0) + tokens.numel()
                counts[key + "_calls"] = counts.get(key + "_calls", 0) + 1

        return count

    backend.model.register_forward_pre_hook(hook("backbone_positions"), with_kwargs=True)
    if arm == "toruk":
        selector.model.register_forward_pre_hook(hook("selector_byte_positions"), with_kwargs=True)
    cases = read(run / f"{split}.json")
    if split == "development":
        cases += [{**cases[0], "id": cases[0]["id"] + "-replay", "is_replay": True}]
    name = f"{split}-{arm}"
    first = None
    setup = time.perf_counter() - started
    with (run / f"{name}-answers.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            counts.clear()
            turns = inference_turns(case)
            progress(
                run / f"{name}-progress.json",
                {"active": True, "started": time.monotonic(), "case": case["id"]},
            )
            tick, before = time.perf_counter(), cpu()
            full_tokens = backend._tokens(envelope(turns, list(range(len(turns)))))
            if (
                full_tokens[0].tolist()
                != read(run / "full-prompt-ids.json")[case["id"].removesuffix("-replay")]
            ):
                raise ValueError("registered full prompt changed")
            counts["history_bpe_tokenization_positions"] = full_tokens.numel()
            selection_tick, selection_cpu = time.perf_counter(), cpu()
            proposed = selector.select(turns)[0] if selector else list(range(len(turns)))
            selection_wall, selection_used = (
                time.perf_counter() - selection_tick,
                cpu() - selection_cpu,
            )
            fit_tick, fit_cpu = time.perf_counter(), cpu()
            if arm == "full":
                chosen, tokens, positions = proposed, full_tokens, 0
                validate_full_context(tokens.shape[-1], reg["context_limit"], 64)
            else:
                chosen, tokens, positions = fit_context(
                    turns, proposed, backend._tokens, config["bounded_prompt_tokens"]
                )
            fit_wall, fit_used = time.perf_counter() - fit_tick, cpu() - fit_cpu
            counts["fit_bpe_tokenization_positions"] = positions
            counts["memory_updates"] = counts.get("selector_byte_positions_calls", 0)
            gen_tick, gen_cpu = time.perf_counter(), cpu()
            with torch.inference_mode():
                output = backend.model.generate(
                    input_ids=tokens,
                    max_new_tokens=64,
                    do_sample=False,
                    eos_token_id=backend.tokenizer.eos_token_id,
                    pad_token_id=backend.tokenizer.pad_token_id,
                    use_cache=True,
                )
            gen_wall, gen_used = time.perf_counter() - gen_tick, cpu() - gen_cpu
            generated = output[0, tokens.shape[-1] :].tolist()
            answer = str(backend.tokenizer.decode(generated, skip_special_tokens=True)).strip()
            scored = score(answer, case)
            state_bytes = (
                selector.model.initial_state().numel()
                * selector.model.initial_state().element_size()
                if arm == "toruk"
                else 0
            )
            row = {
                "id": case["id"],
                "kind": case["kind"],
                "arm": arm,
                "is_replay": case.get("is_replay", False),
                "answer": answer,
                "score": scored,
                "failure": failure(scored, case, chosen),
                "prompt_messages": envelope(turns, chosen),
                "prompt_ids": tokens[0].tolist(),
                "generated_ids": generated,
                "proposed_indices": proposed,
                "selected_indices": chosen,
                "selected_sources": [{"id": f"m{i}", **turns[i]} for i in chosen],
                "required_evidence_retained": set(case["required"]) <= set(chosen),
                "full_evidence_retained": len(chosen) == len(turns),
                "history_bytes": sum(len(m["content"].encode("utf-8")) for m in turns),
                "selector_history_bytes": sum(len(m["content"].encode("utf-8")) for m in turns)
                if selector
                else 0,
                "selector_state_bytes": state_bytes,
                "persistent_state_bytes": 0,
                "work": dict(counts),
                "prompt_tokens": tokens.numel(),
                "output_tokens": len(generated),
                "total_tokens": tokens.numel() + len(generated),
                "selector_wall_seconds": selection_wall,
                "selector_cpu_seconds": selection_used,
                "fit_wall_seconds": fit_wall,
                "fit_cpu_seconds": fit_used,
                "generation_wall_seconds": gen_wall,
                "generation_cpu_seconds": gen_used,
                "request_wall_seconds": time.perf_counter() - tick,
                "request_cpu_seconds": cpu() - before,
                "selector_identity": getattr(selector, "sha256", None),
                "model": backend.model_id,
            }
            assert counts["backbone_positions"] == row["prompt_tokens"] + row["output_tokens"] - 1
            if first is None:
                first = row
            if case.get("is_replay") and any(
                row[k] != first[k]
                for k in (
                    "answer",
                    "score",
                    "prompt_ids",
                    "generated_ids",
                    "selected_indices",
                    "work",
                )
            ):
                raise ValueError("deterministic replay failed")
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            progress(run / f"{name}-progress.json", {"active": False, "case": case["id"]})
    write(
        run / f"{name}-worker.json",
        {
            "pid": os.getpid(),
            "lifecycle_cpu_seconds": cpu(),
            "setup_seconds": setup,
            "worker_seconds": time.perf_counter() - started,
            "memory": psutil.Process().memory_info()._asdict(),
            "generation_config": backend.model.generation_config.to_dict(),
            "torch_threads": torch.get_num_threads(),
            "selector_sha256": getattr(selector, "sha256", None),
            "requests": len(cases),
        },
    )


def read_progress(path: Path) -> dict[str, Any]:
    for attempt in range(5):
        try:
            return read(path) if path.exists() else {}
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.01)
    raise AssertionError("unreachable")


def terminate_tree(process: Any, child: Any) -> None:
    try:
        for descendant in reversed(process.children(recursive=True)):
            try:
                descendant.kill()
            except psutil.NoSuchProcess:
                pass
    except psutil.NoSuchProcess:
        pass
    if child.poll() is None:
        child.kill()


def run_stage(run: Path, split: str, arm: str) -> None:
    started, before = time.perf_counter(), cpu()
    reg = verify(run)
    config = reg["config"]
    name = f"{split}-{arm}"
    write(run / f"{name}-started.json", {"split": split, "arm": arm, "attempt": 1})
    command = [
        sys.executable,
        str(Path(__file__)),
        "worker",
        "--run",
        str(run),
        "--split",
        split,
        "--arm",
        arm,
    ]
    usage: dict[int, float] = {}
    peak_rss = peak_private = peak_disk = 0
    reason = None
    with (run / f"{name}.log").open("x", encoding="utf-8") as log:
        child = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        process = psutil.Process(child.pid)
        try:
            while child.poll() is None:
                rss, private, used = tree_stats(process)
                peak_rss, peak_private = max(peak_rss, rss), max(peak_private, private)
                for pid, seconds in used.items():
                    usage[pid] = max(usage.get(pid, 0), seconds)
                elapsed = time.perf_counter() - started
                prior = config.get("invalid_preflight_wall_upper_seconds", 0) + sum(
                    read(p)["wall_seconds"]
                    for p in run.glob("*-cost.json")
                    if p.name != "training-cost.json"
                )
                study = ROOT / "artifacts/qwen-long-history-v1"
                scope = study if run.is_relative_to(study) else run
                files = set(p for p in scope.rglob("*") if p.is_file()) | {
                    ROOT / n for n in reg["model_files"]
                }
                disk = 0
                for p in files:
                    try:
                        disk += p.stat().st_size
                    except FileNotFoundError:
                        pass
                peak_disk = max(peak_disk, disk)
                active_path = run / f"{name}-progress.json"
                active = read_progress(active_path)
                if peak_private > config["memory_bytes"]:
                    reason = "private-memory cap"
                elif disk > config["disk_bytes"]:
                    reason = "disk cap"
                elif elapsed > config["phase_seconds"] or prior + elapsed > config["total_seconds"]:
                    reason = "elapsed cap"
                elif (
                    active.get("active")
                    and time.monotonic() - active["started"] > config["request_seconds"]
                ):
                    reason = "request deadline"
                if reason:
                    try:
                        for p in reversed(process.children(recursive=True)):
                            try:
                                p.kill()
                            except psutil.NoSuchProcess:
                                pass
                    except psutil.NoSuchProcess:
                        pass
                    child.kill()
                    break
                time.sleep(0.05)
        except Exception as error:
            reason = f"monitor failure: {type(error).__name__}: {error}"
        finally:
            if child.poll() is None:
                terminate_tree(process, child)
        code = child.wait()
    worker_path = run / f"{name}-worker.json"
    if worker_path.exists():
        w = read(worker_path)
        usage[w["pid"]] = max(usage.get(w["pid"], 0), w["lifecycle_cpu_seconds"])
        if w["memory"].get("peak_pagefile", 0) > config["memory_bytes"]:
            reason = "OS private-memory cap"
    elif code == 0:
        reason = "worker output missing"
    write(
        run / f"{name}-cost.json",
        {
            "command": command,
            "returncode": code,
            "failure": reason,
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": sum(usage.values()) + cpu() - before,
            "controller_cpu_seconds": cpu() - before,
            "peak_rss_bytes": peak_rss,
            "peak_private_bytes": peak_private,
            "peak_disk_bytes": peak_disk,
            "cpu_scope": (
                "controller integrity checks + sampled launcher + final worker lifetime CPU"
            ),
        },
    )
    print(json.dumps({"stage": name, "returncode": code, "failure": reason}), flush=True)


def rows(run: Path, name: str) -> list[dict[str, Any]]:
    path = run / f"{name}-answers.jsonl"
    result = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                result.append(json.loads(line))
            except ValueError:
                break
    return result


def aggregate(data: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for r in data if not r.get("is_replay")]
    gold = {c["id"]: c for c in cases}
    known = [r for r in scored if gold[r["id"]]["expected"] != "UNKNOWN"]
    result = {
        "cases": len(scored),
        "correct": sum(r["score"]["correct"] for r in scored),
        "known_cases": len(known),
        "known_correct": sum(r["score"]["correct"] for r in known),
        "abstentions": sum(r["score"]["abstention"] for r in scored),
        "unknown_correct": sum(
            r["score"]["correct"] for r in scored if gold[r["id"]]["expected"] == "UNKNOWN"
        ),
        "unsupported_proxy": sum(r["score"]["unsupported_response_proxy"] for r in scored),
        "stale_proxy": sum(r["score"]["stale_assertion_proxy"] for r in scored),
        "known_evidence_retained": sum(r["required_evidence_retained"] for r in known),
        "categories": {
            k: {
                "n": sum(c["kind"] == k for c in cases),
                "correct": sum(r["score"]["correct"] for r in scored if r["kind"] == k),
            }
            for k in KINDS
        },
        "failures": {
            f: sum(r["failure"] == f for r in scored)
            for f in sorted({r["failure"] for r in scored})
        },
    }
    for key in (
        "prompt_tokens",
        "output_tokens",
        "total_tokens",
        "request_cpu_seconds",
        "request_wall_seconds",
        "selector_cpu_seconds",
        "selector_wall_seconds",
        "fit_cpu_seconds",
        "fit_wall_seconds",
        "generation_cpu_seconds",
        "generation_wall_seconds",
        "history_bytes",
        "selector_history_bytes",
    ):
        result[key] = sum(r[key] for r in data)
    result["work"] = {
        k: sum(r["work"].get(k, 0) for r in data)
        for k in sorted({k for r in data for k in r["work"]})
    }
    return result


def criteria(
    results: dict[str, Any], config: dict[str, Any], count: int, known: int
) -> dict[str, bool]:
    gate = config["criteria"]
    toruk = results["toruk"]
    full = results["full"]

    def floor(r: dict[str, Any], prefix: str) -> bool:
        return r["correct"] >= math.ceil(count * gate[prefix + "_min_accuracy"]) and r[
            "known_correct"
        ] >= math.ceil(known * gate[prefix + "_min_known_accuracy"])

    checks = {
        "all_complete_and_caps": all(
            r["complete"] and r["cases"] == count and r["known_cases"] == known
            for r in results.values()
        ),
        "full_evidence_quality_floor": floor(full, "oracle"),
        "toruk_quality_floor": floor(toruk, "toruk"),
    }
    for arm in gate["quality_against"]:
        baseline = results[arm]
        checks["accuracy_vs_" + arm] = (
            baseline["correct"] - toruk["correct"]
        ) / count * 100 <= gate["max_accuracy_regression_pp"]
        checks["category_vs_" + arm] = all(
            baseline["categories"][k]["correct"] - toruk["categories"][k]["correct"]
            <= gate["max_category_regression_cases"]
            for k in KINDS
        )
    for arm in ("full", "lexical", "recent"):
        checks["assertion_proxies_vs_" + arm] = (
            toruk["unsupported_proxy"] <= results[arm]["unsupported_proxy"]
            and toruk["stale_proxy"] <= results[arm]["stale_proxy"]
        )
    for arm in gate["efficiency_against"]:
        for metric in ("cpu_seconds", "wall_seconds"):
            checks[metric + "_vs_" + arm] = (
                toruk["charged_total"][metric]
                <= (1 - gate["cpu_and_wall_reduction_fraction"])
                * results[arm]["charged_total"][metric]
            )
    return checks


def summarize(run: Path) -> None:
    reg = verify(run)
    config = reg["config"]
    cases = read(run / "heldout.json")
    results = {}
    training = read(run / "training-cost.json")
    for arm in ARMS:
        result = aggregate(rows(run, "heldout-" + arm), cases)
        held_cost = read(run / f"heldout-{arm}-cost.json")
        dev_cost = read(run / f"development-{arm}-cost.json")
        result["heldout_cost"] = held_cost
        result["development_cost"] = dev_cost
        result["development"] = aggregate(
            rows(run, "development-" + arm), read(run / "development.json")
        )
        result["complete"] = all(
            c["returncode"] == 0 and c["failure"] is None for c in (held_cost, dev_cost)
        )
        result["charged_total"] = {
            k: held_cost[k] + dev_cost[k] + (training[k] if arm == "toruk" else 0)
            for k in ("cpu_seconds", "wall_seconds")
        }
        result["training_amortized_per_heldout_query"] = {
            k: training[k] / len(cases) if arm == "toruk" else 0
            for k in ("cpu_seconds", "wall_seconds")
        }
        result["workload_sensitivity"] = {
            str(n): {
                k: result["charged_total"][k]
                - (training[k] if arm == "toruk" else 0)
                + (training[k] * len(cases) / n if arm == "toruk" else 0)
                for k in ("cpu_seconds", "wall_seconds")
            }
            for n in config["cost_policy"]["sensitivity_queries"]
        }
        results[arm] = result
    checks = criteria(results, config, len(cases), sum(c["expected"] != "UNKNOWN" for c in cases))
    write(
        run / "results.json",
        {
            "schema": SCHEMA,
            "registration_sha256": sha(run / "registration.json"),
            "results": results,
            "criteria": checks,
            "verdict": "PASS" if all(checks.values()) else "FAIL",
            "training_cost": training,
            "scope": (
                "single synthetic local trial; no population/general-chat or historical-M6 claim"
            ),
        },
    )
    print(
        json.dumps(
            {
                "verdict": "PASS" if all(checks.values()) else "FAIL",
                "criteria": checks,
                "scores": {a: [r["correct"], r["cases"]] for a, r in results.items()},
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("register", "development", "freeze", "heldout", "summarize", "worker")
    )
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/qwen-long-history-v1.json")
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--split", choices=("development", "heldout"))
    args = parser.parse_args()
    run = args.run.resolve()
    if args.action == "register":
        register(run, args.config.resolve())
    elif args.action == "worker":
        worker(run, args.split, args.arm)
    elif args.action == "summarize":
        summarize(run)
    elif args.action == "freeze":
        reg = verify(run)
        for arm in ARMS:
            cost = read(run / f"development-{arm}-cost.json")
            if cost["returncode"] != 0 or cost["failure"] is not None:
                raise ValueError("development prerequisite failed; heldout blocked")
        write(
            run / "freeze.json",
            {
                "registration_sha256": sha(run / "registration.json"),
                "development_outputs": {
                    a: sha(run / f"development-{a}-answers.jsonl") for a in ARMS
                },
                "note": (
                    "Mechanisms/settings fixed before development; "
                    "no tuning, technical/replay gate only."
                ),
            },
        )
    else:
        reg = verify(run)
        if args.action == "heldout":
            seal = read(run / "freeze.json")
            if seal["registration_sha256"] != sha(run / "registration.json") or any(
                sha(run / f"development-{a}-answers.jsonl") != s
                for a, s in seal["development_outputs"].items()
            ):
                raise ValueError("freeze identity drift")
        for arm in reg["config"][args.action + "_order"]:
            run_stage(run, args.action, arm)


if __name__ == "__main__":
    main()
