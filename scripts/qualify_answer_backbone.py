"""Sealed plain-context backbone qualification. No selector, fitting, or old-question replay."""

import argparse
import hashlib
import importlib.metadata
import json
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

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "backbone-qualification-v1"
SYSTEM = (
    "Use only the supplied reference to answer its question, including explicit corrections. "
    "Return just the requested value without explanation. If the requested information "
    "is missing, reply UNKNOWN. When asked to copy a quotation, preserve its text exactly."
)
KINDS = ("binding", "correction", "preservation", "literal", "reference", "missing")


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")


def make_cases(split: str, seed: int, count_per_kind: int) -> list[dict[str, Any]]:
    if split not in ("development", "heldout"):
        raise ValueError("new qualification split required")
    dev = split == "development"
    rng = random.Random(seed)
    pools = {
        "binding": ["ochre", "teal"]
        if dev
        else ["maroon", "indigo", "bronze", "magenta", "turquoise"],
        "correction": ["Tuesday", "Saturday"]
        if dev
        else ["Monday", "Wednesday", "Thursday", "Friday", "Sunday"],
        "preservation": ["apricot", "nectarine"]
        if dev
        else ["fig", "guava", "plum", "tangerine", "coconut"],
        "reference": ["Beatrice", "Jasper"] if dev else ["Nora", "Emil", "Soren", "Ada", "Milan"],
    }
    output = []
    for kind in KINDS:
        for i in range(count_per_kind):
            tag = ("QUALD-" if dev else "QUALH-") + f"{rng.getrandbits(40):010X}"
            auxiliary = ("AUXD-" if dev else "AUXH-") + f"{rng.getrandbits(40):010X}"
            value, alternatives = "UNKNOWN", []
            if kind in pools:
                pool = pools[kind]
                value = pool[i % len(pool)]
                alternatives = [pool[(i + 1) % len(pool)]]
            if kind == "binding":
                if dev:
                    record = (
                        f"Badge {tag} has color {value}. Badge {auxiliary} has "
                        f"color {alternatives[0]}."
                    )
                    question = f"What color does badge {tag} have?"
                else:
                    record = (
                        f"A register assigns {value} paint to item {tag}. A "
                        f"separate item {auxiliary} has {alternatives[0]} paint."
                    )
                    question = f"Which paint is assigned to item {tag}?"
            elif kind == "correction":
                if dev:
                    record = (
                        f"The first form for {tag} lists {alternatives[0]}. An "
                        f"amended form changes its inspection day to {value}; the "
                        "first form is obsolete."
                    )
                    question = f"On what day is the inspection for {tag} after the amendment?"
                else:
                    record = (
                        f"Roster {tag} originally scheduled service for "
                        f"{alternatives[0]}. A revision notice replaces that "
                        f"weekday with {value}."
                    )
                    question = f"Which weekday is now official for roster {tag}?"
            elif kind == "preservation":
                if dev:
                    record = (
                        f"Handbook {tag} lists fruit {value} and cover silver. "
                        "Only its cover changes to copper; the fruit entry stays "
                        "valid."
                    )
                    question = f"What fruit is still listed in handbook {tag}?"
                else:
                    record = (
                        f"Catalog {tag} records flavor {value} and file class "
                        "SOFT. Only the file class is revised to HARD; the "
                        "flavor does not change."
                    )
                    question = f"What flavor is retained in catalog {tag}?"
                alternatives = []
            elif kind == "literal":
                letters = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(7))
                value = f"QD_{letters}:5  +" if dev else f"QH[{letters}]  | 8z"
                if dev:
                    record = f'The quoted sign for {tag} reads "{value}".'
                    question = f"Copy the quoted sign for {tag} with its spacing."
                else:
                    record = f'An engraving attached to {tag} is "{value}".'
                    question = f"Reproduce only the engraving text attached to {tag}, exactly."
            elif kind == "reference":
                if dev:
                    record = f"A clerk monitors parcel {tag}. That same parcel belongs to {value}."
                    question = "Who owns the parcel being monitored?"
                else:
                    record = (
                        f"A technician places package {tag} on a bench. The note "
                        f"about that package names {value} as its custodian."
                    )
                    question = "Who is the custodian of the package on the bench?"
                alternatives = []
            else:
                if dev:
                    record = (
                        f"Register {tag} lists only a container mass of 14 grams. "
                        "No serial number is recorded."
                    )
                    question = f"What serial number is specified in register {tag}?"
                else:
                    record = (
                        f"Sheet {tag} specifies a crate label SOFT and includes "
                        "no entry for its access phrase."
                    )
                    question = f"Which access phrase does sheet {tag} specify?"
            prompt = f"Reference:\n{record}\n\nQuestion:\n{question}\n\nAnswer:"
            output.append(
                {
                    "schema": SCHEMA,
                    "id": f"bq1-{split}-{kind}-{i}",
                    "split": split,
                    "kind": kind,
                    "tag": tag,
                    "auxiliary": auxiliary,
                    "expected": value,
                    "alternatives": alternatives,
                    "question": question,
                    "prompt": prompt,
                }
            )
    return output


def messages(case: dict[str, Any]) -> list[dict[str, str]]:
    if case.get("schema") != SCHEMA or "prompt" not in case:
        raise ValueError("only new qualification cases are accepted")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": case["prompt"]}]


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def phrase(text: str, value: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(normalized(value)) + r"(?!\w)", text))


def score(answer: str, case: dict[str, Any]) -> dict[str, Any]:
    text = normalized(answer)
    abstention = bool(
        re.search(
            "\\b(?:unknown|unavailable|not (?:known|available|pr"
            "ovided|supplied|given|recorded|listed|specified)|"
            r"(?:do not|don't) know|(?:cannot|can't) determine|insufficient information)\b",
            text,
        )
    )
    guessed = bool(re.search(r"\b(?:maybe|probably|could be|might be|guess)\b", text))
    asserted = re.search(
        r"\b(?:phrase|serial number|token|code|key|answer)\s+(?:is|equals|:)\s+(\S+)", text
    )
    invented_after_abstention = bool(
        asserted
        and asserted.group(1).strip(".,!?")
        not in {"not", "unknown", "unavailable", "missing", "unspecified"}
    )
    correct = (
        abstention and not guessed and not invented_after_abstention
        if case["kind"] == "missing"
        else answer.strip() == case["expected"]
        if case["kind"] == "literal"
        else phrase(text, case["expected"])
        and not abstention
        and not any(phrase(text, value) for value in case["alternatives"])
        and not bool(re.search(r"\bnot\s+" + re.escape(normalized(case["expected"])), text))
    )
    return {
        "correct": bool(correct),
        "abstention": abstention,
        "wrong_listed_value": any(phrase(text, value) for value in case["alternatives"]),
        "unsupported_response_proxy": case["kind"] == "missing" and not correct,
    }


def question_shape(case: dict[str, Any]) -> str:
    text = case.get("question", case.get("messages", [{}])[-1].get("content", ""))
    text = re.sub(r"\b(?:QUAL[DH]|AUX[DH])-[0-9A-F]+\b|\b[DH][0-9A-F]{10}\b", "ID", text)
    return normalized(text)


def leakage(
    dev: list[dict[str, Any]], held: list[dict[str, Any]], legacy: list[dict[str, Any]]
) -> dict[str, Any]:
    sets = [dev, held, legacy]
    ids = [{c["id"] for c in rows} for rows in sets]
    values = [
        {normalized(c.get("expected", c.get("value", ""))) for c in rows if c["kind"] != "missing"}
        for rows in sets
    ]
    shapes = [{question_shape(c) for c in rows} for rows in sets]
    for i, j in ((0, 1), (0, 2), (1, 2)):
        if ids[i] & ids[j] or values[i] & values[j] or shapes[i] & shapes[j]:
            raise ValueError("cross-split or successor overlap")
    return {
        "status": "PASS",
        "counts": [len(x) for x in sets],
        "rule": "No shared IDs, known expected values or normalized"
        " question templates; generic instructions shared. "
        "No training. Not proof of semantic/pretraining dis"
        "jointness.",
    }


def verify(run: Path) -> dict[str, Any]:
    reg = read(run / "registration.json")
    for name, expected in reg["bindings"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("registered identity drift: " + name)
    for name, expected in reg["dependencies"].items():
        if importlib.metadata.version(name) != expected:
            raise ValueError("registered dependency drift: " + name)
    return reg


def register(run: Path, config_path: Path) -> None:
    from transformers import AutoTokenizer

    from toruk_lm.chat_foundation import read_backbone_manifest

    config = read(config_path)
    dev = make_cases("development", config["development_seed"], 2)
    held = make_cases("heldout", config["heldout_seed"], 5)
    legacy_path = ROOT / "artifacts/m6-successor-v1/execution/heldout.json"
    legacy = read(legacy_path)
    write(run / "development.json", dev)
    write(run / "heldout.json", held)
    write(run / "leakage.json", leakage(dev, held, legacy))
    write(run / "config.json", config)
    paths = [
        Path(__file__),
        config_path,
        ROOT / "tests/test_backbone_qualification.py",
        ROOT / "docs/research/backbone-qualification-v1-protocol.md",
        legacy_path,
    ]
    paths += list((ROOT / "src/toruk_lm").glob("*.py"))
    prompts: dict[str, dict[str, list[int]]] = {}
    model_files = []
    for alias, spec in config["candidates"].items():
        directory = ROOT / spec["directory"]
        manifest = read_backbone_manifest(directory)
        if any(manifest[k] != spec[k] for k in ("model", "revision", "model_sha256")):
            raise ValueError("candidate identity mismatch")
        files = [p for p in directory.iterdir() if p.is_file()]
        paths += files
        model_files += [p.relative_to(ROOT).as_posix() for p in files]
        tokenizer = AutoTokenizer.from_pretrained(
            directory, local_files_only=True, trust_remote_code=False
        )
        prompts[alias] = {}
        for case in dev + held:
            ids = tokenizer.apply_chat_template(
                messages(case), tokenize=True, add_generation_prompt=True, return_dict=False
            )
            if not isinstance(ids, list) or any(not isinstance(x, int) for x in ids):
                raise ValueError("tokenizer must return a flat integer token sequence")
            ids = cast(list[int], ids)
            if len(ids) > config["max_prompt_tokens"]:
                raise ValueError("qualification context would truncate evidence")
            if case["prompt"] not in tokenizer.decode(ids, skip_special_tokens=False):
                raise ValueError("qualification source changed during tokenization")
            prompts[alias][case["id"]] = ids
    write(run / "prompt-ids.json", prompts)
    paths += [
        run / n
        for n in (
            "development.json",
            "heldout.json",
            "config.json",
            "leakage.json",
            "prompt-ids.json",
        )
    ]
    with zipfile.ZipFile(run / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if path.relative_to(ROOT).as_posix() not in model_files:
                archive.writestr(path.relative_to(ROOT).as_posix(), path.read_bytes())
    paths.append(run / "source.zip")
    write(
        run / "registration.json",
        {
            "schema": SCHEMA,
            "config": config,
            "model_files": model_files,
            "bindings": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
            "dependencies": {
                n: importlib.metadata.version(n)
                for n in ("torch", "transformers", "tokenizers", "safetensors", "psutil")
            },
            "system_instructions": SYSTEM,
            "python": sys.version,
            "note": "No candidate inference before registration; tokeni"
            "zer-only fit checks. No selector or training.",
        },
    )
    print(
        "Registered both candidate identities, source, fres"
        "h data, prompt IDs and all gates before inference."
    )


def cpu() -> float:
    value = psutil.Process().cpu_times()
    return value.user + value.system


def tree_stats(process: Any) -> tuple[int, int, dict[int, float]]:
    rss = private = 0
    usage = {}
    try:
        processes = [process, *process.children(recursive=True)]
    except psutil.NoSuchProcess:
        return 0, 0, {}
    for child in processes:
        try:
            info, times = child.memory_info(), child.cpu_times()
            rss += info.rss
            private += getattr(info, "private", getattr(info, "vms", 0))
            usage[child.pid] = times.user + times.system
        except psutil.NoSuchProcess:
            pass
    return rss, private, usage


def progress(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream)
    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.01)


def evaluate(run: Path, split: str) -> None:
    if split == "heldout":
        seal = read(run / "candidate-freeze.json")
        if seal["registration_sha256"] != sha(run / "registration.json"):
            raise ValueError("pre-held-out candidate freeze mismatch")
    order = ("smollm", "qwen") if split == "development" else ("qwen", "smollm")
    eligible = (
        read(run / "candidate-freeze.json").get("eligible", list(order))
        if split == "heldout"
        else list(order)
    )
    for alias in order:
        if alias not in eligible:
            write(
                run / f"heldout-{alias}-cost.json",
                {
                    "returncode": 1,
                    "failure": "development execution failed; no held-out inference",
                    "wall_seconds": 0,
                    "cpu_seconds": 0,
                    "peak_rss_bytes": 0,
                    "peak_private_bytes": 0,
                },
            )
            continue
        started, controller_before = time.perf_counter(), cpu()
        reg = verify(run)
        config = reg["config"]
        name = f"{split}-{alias}"
        write(
            run / f"{name}-started.json",
            {
                "split": split,
                "candidate": alias,
                "heldout_attempts": 1 if split == "heldout" else 0,
            },
        )
        command = [
            sys.executable,
            str(Path(__file__)),
            "worker",
            "--run",
            str(run),
            "--split",
            split,
            "--candidate",
            alias,
        ]
        usage: dict[int, float] = {}
        peak_rss = peak_private = 0
        failure = None
        with (run / f"{name}.log").open("x", encoding="utf-8") as log:
            child = subprocess.Popen(
                command,
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            process = psutil.Process(child.pid)
            while child.poll() is None:
                rss, private, used = tree_stats(process)
                peak_rss, peak_private = max(peak_rss, rss), max(peak_private, private)
                for pid, seconds in used.items():
                    usage[pid] = max(usage.get(pid, 0), seconds)
                prior = sum(read(p)["wall_seconds"] for p in run.glob("*-cost.json"))
                elapsed = time.perf_counter() - started
                p = run / f"{name}-progress.json"
                active = read(p) if p.exists() else {}
                files = set(p for p in run.rglob("*") if p.is_file()) | {
                    ROOT / n for n in reg["model_files"]
                }
                disk_bytes = 0
                for path in files:
                    try:
                        disk_bytes += path.stat().st_size
                    except FileNotFoundError:
                        pass
                if peak_private > config["memory_bytes"]:
                    failure = "registered private-memory cap"
                elif elapsed > config["phase_seconds"] or prior + elapsed > config["total_seconds"]:
                    failure = "registered elapsed-time cap"
                elif disk_bytes > config["disk_bytes"]:
                    failure = "registered disk cap"
                elif (
                    active.get("active")
                    and time.monotonic() - active["started"] > config["request_seconds"]
                ):
                    failure = "registered per-request deadline"
                if failure:
                    for descendant in reversed(process.children(recursive=True)):
                        try:
                            descendant.kill()
                        except psutil.NoSuchProcess:
                            pass
                    child.kill()
                    break
                time.sleep(0.05)
            code = child.wait()
        worker_path = run / f"{name}-worker.json"
        if worker_path.exists():
            result = read(worker_path)
            usage[result["pid"]] = max(usage.get(result["pid"], 0), result["lifecycle_cpu_seconds"])
            if result["memory"].get("peak_pagefile", 0) > config["memory_bytes"]:
                failure = "OS lifetime private-memory cap"
        elif code == 0:
            failure = "worker result missing"
        write(
            run / f"{name}-cost.json",
            {
                "command": command,
                "returncode": code,
                "failure": failure,
                "wall_seconds": time.perf_counter() - started,
                "cpu_seconds": sum(usage.values()) + cpu() - controller_before,
                "controller_cpu_seconds": cpu() - controller_before,
                "peak_rss_bytes": peak_rss,
                "peak_private_bytes": peak_private,
                "cpu_scope": "worker/launcher sampled CPU, worker final lifetime"
                " CPU, controller including verification",
            },
        )
        print(json.dumps({"stage": name, "returncode": code, "failure": failure}), flush=True)


def worker(run: Path, split: str, alias: str) -> None:
    started = time.perf_counter()
    reg = verify(run)
    config = reg["config"]
    import torch
    from transformers import GenerationConfig

    from toruk_lm.chat_foundation import PretrainedChatBackend

    torch.manual_seed(config["generation_seed"])
    torch.use_deterministic_algorithms(True)
    backend = PretrainedChatBackend(ROOT / config["candidates"][alias]["directory"])
    backend.system_prompt = ""  # Explicit identical system message is supplied to both models.
    assert backend.selector is None
    backend.model.generation_config = GenerationConfig(
        do_sample=False,
        num_beams=1,
        repetition_penalty=1.0,
        use_cache=True,
        eos_token_id=backend.tokenizer.eos_token_id,
        pad_token_id=backend.tokenizer.pad_token_id,
        max_new_tokens=config["max_new_tokens"],
        temperature=1.0,
        top_p=1.0,
    )
    generate = backend.model.generate
    captured: list[int] = []

    def capture(**kwargs: Any) -> Any:
        result = generate(**kwargs)
        captured[:] = result[0, kwargs["input_ids"].shape[-1] :].tolist()
        return result

    backend.model.generate = capture
    cases = read(run / f"{split}.json")
    if split == "development":
        cases += [{**cases[0], "id": cases[0]["id"] + "-replay", "is_replay": True}]
    expected_prompts = read(run / "prompt-ids.json")[alias]
    setup_seconds = time.perf_counter() - started
    name = f"{split}-{alias}"
    first = None
    with (run / f"{name}-answers.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for case in cases:
            message_list = messages(case)
            ids = backend._tokens(message_list)[0].tolist()
            original_id = case["id"].removesuffix("-replay")
            if ids != expected_prompts[original_id]:
                raise ValueError("candidate prompt drift")
            progress(
                run / f"{name}-progress.json",
                {"active": True, "started": time.monotonic(), "case": case["id"]},
            )
            tick, before_cpu = time.perf_counter(), cpu()
            response = backend.reply_with_metrics(
                message_list, config["max_new_tokens"], mode="BASELINE", temperature=0, top_p=1
            )
            wall, cpu_seconds = time.perf_counter() - tick, cpu() - before_cpu
            progress(run / f"{name}-progress.json", {"active": False, "case": case["id"]})
            if response["metrics"]["selected_message_ids"] != ["m0", "m1"]:
                raise ValueError("evidence truncation or selector detected")
            if (
                len(ids) != response["metrics"]["selected_context_tokens"]
                or len(captured) != response["metrics"]["output_tokens"]
            ):
                raise ValueError("raw token accounting mismatch")
            row = {
                "id": case["id"],
                "kind": case["kind"],
                "candidate": alias,
                "is_replay": case.get("is_replay", False),
                **response,
                "score": score(response["answer"], case),
                "messages": message_list,
                "prompt_ids": ids,
                "generated_ids": list(captured),
                "wall_seconds": wall,
                "cpu_seconds": cpu_seconds,
                "full_evidence_retained": True,
            }
            if first is None:
                first = row
            if case.get("is_replay") and any(
                row[k] != first[k]
                for k in ("answer", "score", "messages", "prompt_ids", "generated_ids")
            ):
                raise ValueError("deterministic development replay failed")
            stream.write(json.dumps(row) + "\n")
            stream.flush()
    write(
        run / f"{name}-worker.json",
        {
            "pid": os.getpid(),
            "lifecycle_cpu_seconds": cpu(),
            "setup_seconds": setup_seconds,
            "worker_seconds": time.perf_counter() - started,
            "memory": psutil.Process().memory_info()._asdict(),
            "model": backend.model_id,
            "generation_config": backend.model.generation_config.to_dict(),
            "torch_threads": torch.get_num_threads(),
            "generation_requests": len(cases),
            "selector": None,
            "development_replay": split == "development",
        },
    )


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for r in rows if not r.get("is_replay")]
    known = [r for r in scored if r["kind"] != "missing"]
    return {
        "cases": len(scored),
        "correct": sum(r["score"]["correct"] for r in scored),
        "known_cases": len(known),
        "known_correct": sum(r["score"]["correct"] for r in known),
        "abstentions": sum(r["score"]["abstention"] for r in scored),
        "unknown_correct": sum(r["score"]["correct"] for r in scored if r["kind"] == "missing"),
        "wrong_listed_values": sum(r["score"]["wrong_listed_value"] for r in scored),
        "unsupported_response_proxy": sum(r["score"]["unsupported_response_proxy"] for r in scored),
        "online_wall_seconds": sum(r["wall_seconds"] for r in rows),
        "online_cpu_seconds": sum(r["cpu_seconds"] for r in rows),
        "prompt_tokens": sum(r["metrics"]["selected_context_tokens"] for r in rows),
        "output_tokens": sum(r["metrics"]["output_tokens"] for r in rows),
        "categories": {
            k: {
                "n": sum(r["kind"] == k for r in scored),
                "correct": sum(r["score"]["correct"] for r in scored if r["kind"] == k),
            }
            for k in KINDS
        },
    }


def passed(summary: dict[str, Any], completed: bool) -> bool:
    return bool(
        completed
        and summary["cases"] == 30
        and summary["known_cases"] == 25
        and summary["correct"] >= 18
        and summary["known_correct"] >= 15
    )


def summarize(run: Path) -> None:
    reg = verify(run)
    results = {}
    for alias in reg["config"]["candidates"]:
        development_path = run / f"development-{alias}-answers.jsonl"
        development = (
            [json.loads(s) for s in development_path.read_text(encoding="utf-8").splitlines()]
            if development_path.exists()
            else []
        )
        path = run / f"heldout-{alias}-answers.jsonl"
        rows = (
            [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]
            if path.exists()
            else []
        )
        summary = aggregate(rows)
        cost = read(run / f"heldout-{alias}-cost.json")
        complete = cost["returncode"] == 0 and cost["failure"] is None
        summary.update(
            qualifies=passed(summary, complete),
            heldout_cost=cost,
            development=aggregate(development),
        )
        results[alias] = summary
    eligible = [alias for alias, result in results.items() if result["qualifies"]]
    selected = (
        min(eligible, key=lambda a: results[a]["heldout_cost"]["cpu_seconds"]) if eligible else None
    )
    write(
        run / "results.json",
        {
            "schema": SCHEMA,
            "results": results,
            "selected": selected,
            "selection_rule": "Lowest held-out CPU among predeclared candidates p"
            "assing both fixed 60% gates and caps",
            "claim_scope": "External plain-context answer backbone only. No se"
            "lector or long-history superiority claim.",
        },
    )
    if selected:
        identity = reg["config"]["candidates"][selected]
        write(
            run / "qualified-backbone.json",
            {
                "schema": SCHEMA,
                "candidate": selected,
                **identity,
                "system_instructions": SYSTEM,
                "registration_sha256": sha(run / "registration.json"),
                "generation_policy": reg["config"]["generation_policy"],
                "budget": {
                    k: reg["config"][k]
                    for k in (
                        "memory_bytes",
                        "disk_bytes",
                        "phase_seconds",
                        "total_seconds",
                        "request_seconds",
                    )
                },
                "scores": {
                    k: results[selected][k]
                    for k in ("cases", "correct", "known_cases", "known_correct")
                },
                "status": "Qualified on this new fixed plain-context set; no "
                "Toruk-selector contribution",
            },
        )
    print(json.dumps({"selected": selected, "results": results}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("register", "development", "freeze", "heldout", "summarize", "worker")
    )
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/backbone-qualification-v1.json"
    )
    parser.add_argument("--split", default="")
    parser.add_argument("--candidate", default="")
    args = parser.parse_args()
    run = args.run.resolve()
    if args.action == "register":
        register(run, args.config.resolve())
    elif args.action == "worker":
        worker(run, args.split, args.candidate)
    elif args.action in ("development", "heldout"):
        evaluate(run, args.action)
    elif args.action == "freeze":
        reg = verify(run)
        eligible = []
        for alias in reg["config"]["candidates"]:
            cost = read(run / f"development-{alias}-cost.json")
            if cost["returncode"] == 0 and cost["failure"] is None:
                eligible.append(alias)
        write(
            run / "candidate-freeze.json",
            {
                "registration_sha256": sha(run / "registration.json"),
                "models": reg["config"]["candidates"],
                "eligible": eligible,
                "development_outputs": {
                    a: sha(run / f"development-{a}-answers.jsonl") for a in eligible
                },
            },
        )
    else:
        summarize(run)


if __name__ == "__main__":
    main()
