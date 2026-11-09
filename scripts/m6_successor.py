"""One sealed M6 successor study; new random selector, frozen backbone, no historical weights."""

import argparse
import hashlib
import importlib.metadata
import json
import random
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("recent", "lexical", "toruk")
OLD_HASH = "479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def cases(split: str, seed: int, copies: int) -> list[dict[str, Any]]:
    if split not in ("development", "heldout"):
        raise ValueError("evaluation split required")
    rng = random.Random(seed)
    dev = split == "development"
    pool = (
        ["Bern", "Genoa", "Lille", "Dakar", "Vaduz", "Muscat"]
        if dev
        else ["Graz", "Busan", "Bremen", "Sofia", "Lusaka", "Riga"]
    )
    result = []
    for kind in ("distant", "correction", "preservation", "exact", "reference", "missing"):
        for index in range(copies):
            tag = ("D" if dev else "H") + f"{rng.getrandbits(40):010X}"
            value, obsolete = rng.sample(pool, 2)
            if kind in ("exact", "reference"):
                value = tag + (":  A/7!" if kind == "exact" else "-KITE")
                obsolete = ""
            if kind == "exact":
                fact = (
                    f"The literal marker for {tag} is {value}"
                    if dev
                    else f"Store {value} verbatim as marker {tag}."
                )
                query = (
                    f"Quote the literal marker {tag} exactly; nothing else."
                    if dev
                    else (
                        f"Return only the stored marker for {tag}, "
                        "retaining punctuation and spaces."
                    )
                )
            elif kind == "reference":
                fact = (
                    f"I call route {tag} by nickname {value}."
                    if dev
                    else f"The name I gave itinerary {tag} was {value}."
                )
                query = (
                    "What nickname did I give that route?"
                    if dev
                    else "Which name did I give that itinerary?"
                )
            else:
                fact = (
                    f"Dispatch city for record {tag} is {value}."
                    if dev
                    else f"Destination town assigned to record {tag}: {value}."
                )
                query = (
                    f"What is the dispatch city for record {tag}?"
                    if dev
                    else f"Which destination town belongs to record {tag}?"
                )
            messages = [
                {"role": "user", "content": fact},
                {"role": "assistant", "content": "Noted."},
            ]
            required = [0]
            if kind == "correction":
                messages[0]["content"] = fact.replace(value, obsolete)
                correction = (
                    f"Correction: record {tag} dispatch city is {value}."
                    if dev
                    else f"Update: the destination town for record {tag} has changed to {value}."
                )
                messages += [
                    {"role": "user", "content": correction},
                    {"role": "assistant", "content": "Noted."},
                ]
                required = [2]
            elif kind == "preservation":
                correction = (
                    f"The snack for record {tag} changed to kiwi."
                    if dev
                    else f"Update only the meal for record {tag} to pasta."
                )
                messages += [
                    {"role": "user", "content": correction},
                    {"role": "assistant", "content": "Noted."},
                ]
            elif kind == "missing":
                query = (
                    f"What is the locker key for record {tag}? It was never supplied. "
                    "Say unknown if unavailable."
                )
                value, obsolete, required = "unknown", "", []
            for gap in range(18):
                note = (
                    f"Weather entry {gap}: drifting clouds crossed the quiet valley "
                    "before a mild afternoon breeze, while the instruments "
                    "logged pressure and humidity."
                )
                messages += [
                    {"role": "user", "content": note},
                    {"role": "assistant", "content": "Weather entry received."},
                ]
            messages.append({"role": "user", "content": query})
            result.append(
                {
                    "id": f"{split}-{kind}-{index}",
                    "split": split,
                    "kind": kind,
                    "value": value,
                    "obsolete": obsolete if kind == "correction" else "",
                    "required": required,
                    "tag": tag,
                    "messages": messages,
                }
            )
    return result


def leakage_audit(dev: list[dict[str, Any]], held: list[dict[str, Any]], train_text: str) -> None:
    if {c["id"] for c in dev} & {c["id"] for c in held}:
        raise ValueError("cross-split IDs")
    if {c["value"] for c in dev if c["kind"] != "missing"} & {
        c["value"] for c in held if c["kind"] != "missing"
    }:
        raise ValueError("cross-split factual values")
    for case in dev + held:
        if case["kind"] != "missing" and case["value"].casefold() in train_text.casefold():
            raise ValueError("evaluation value in selector training text")

    def templates(rows: list[dict[str, Any]]) -> set[str]:
        values = set()
        for c in rows:
            if c["kind"] == "missing":
                continue  # Shared explicit uncertainty instruction is disclosed scaffolding.
            text = c["messages"][0]["content"] + " " + c["messages"][-1]["content"]
            for literal in (c["value"], c["obsolete"], c["tag"]):
                if literal:
                    text = text.replace(literal, "VALUE")
            values.add(" ".join(text.casefold().split()))
        return values

    if templates(dev) & templates(held):
        raise ValueError("cross-split task templates")


def inference_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    return [{"role": m["role"], "content": m["content"]} for m in case["messages"]]


def score(answer: str, case: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(answer.casefold().split())
    missing = case["kind"] == "missing"
    abstain = any(
        x in text
        for x in (
            "unknown",
            "don't know",
            "do not know",
            "not provided",
            "not supplied",
            "cannot know",
            "cannot access",
            "can't access",
            "don't have",
            "do not have",
            "cannot provide",
            "unable to provide",
        )
    )
    target = " ".join(case["value"].casefold().split())
    stale = bool(case["obsolete"] and case["obsolete"].casefold() in text)
    correct = (
        abstain
        if missing
        else answer.strip() == case["value"]
        if case["kind"] == "exact"
        else bool(re.search(r"(?<!\w)" + re.escape(target) + r"(?!\w)", text))
    ) and not stale
    return {
        "correct": bool(correct),
        "unsupported_abstention_proxy": missing and not abstain,
        "stale_assertion_proxy": stale,
    }


def verify(run: Path) -> dict[str, Any]:
    reg = read(run / "registration.json")
    for name, expected in reg["bindings"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("Registered input drift: " + name)
    for name, expected in reg["dependencies"].items():
        if importlib.metadata.version(name) != expected:
            raise ValueError("Registered dependency drift: " + name)
    return reg


def register(run: Path, config_path: Path, backbone: Path) -> None:
    if (run / "registration.json").exists():
        raise ValueError("already registered")
    from toruk_lm.chat_foundation import BACKBONE_SHA256, read_backbone_manifest
    from toruk_lm.tokenizer import ByteTokenizer
    from toruk_lm.worlds import make_worlds

    config = read(config_path)
    manifest = read_backbone_manifest(backbone)
    if manifest["model_sha256"] != BACKBONE_SHA256:
        raise ValueError("registered SmolLM backbone required")
    make_worlds(run / "training-data", config["world_seed"], 4)
    dev = cases("development", config["development_seed"], 1)
    held = cases("heldout", config["heldout_seed"], 4)
    train_text = (run / "training-data/train.jsonl").read_text(encoding="utf-8")
    leakage_audit(dev, held, train_text)
    write(run / "development.json", dev)
    write(run / "heldout.json", held)
    write(run / "config.json", config)
    paths = [
        config_path,
        Path(__file__),
        ROOT / "pyproject.toml",
        *sorted((ROOT / "src/toruk_lm").glob("*.py")),
    ]
    paths += [p for p in backbone.iterdir() if p.is_file()]
    paths += [run / "development.json", run / "heldout.json", run / "config.json"]
    paths += list((run / "training-data").glob("*"))
    paths += [
        ROOT / "tests/test_m6_successor.py",
        ROOT / "docs/research/m6-successor-v1-protocol.md",
    ]
    with zipfile.ZipFile(run / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if not path.is_relative_to(backbone):
                archive.writestr(path.relative_to(ROOT).as_posix(), path.read_bytes())
    paths.append(run / "source.zip")
    if config.get("preflight_run"):
        prior = ROOT / config["preflight_run"]
        paths += [
            prior / "technical-amendment.json",
            prior / "registration.json",
            prior / "source.zip",
        ]
        paths += list(prior.glob("*-cost.json")) + list(prior.glob("*-worker.json"))
        paths += list(prior.glob("*-answers.jsonl"))

    write(
        run / "registration.json",
        {
            "experiment": "m6-successor-v1",
            "historical_m6": "NOT REPRODUCIBLE",
            "config": config,
            "backbone": backbone.relative_to(ROOT).as_posix(),
            "backbone_identity": manifest,
            "selector_tokenizer": ByteTokenizer.fingerprint,
            "checkpoint_format": "toruk-controlled-v1; new experiment-bound sidecar",
            "bindings": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
            "dependencies": {
                name: importlib.metadata.version(name)
                for name in ("torch", "transformers", "tokenizers", "safetensors", "psutil")
            },
            "git_head": subprocess.check_output(
                ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
                cwd=ROOT,
                text=True,
            ).strip(),
            "python": sys.version,
            "data_provenance": (
                "New deterministic owned synthetic worlds and authored conversational "
                "templates; no historical questions or checkpoint."
            ),
            "leakage": (
                "disjoint IDs, known values, task-bearing templates and literal training-value "
                "exclusion passed; unknown instruction/weather scaffolding shared"
            ),
        },
    )
    print("Registered before any selector training or evaluation.")


def cpu() -> float:
    value = psutil.Process().cpu_times()
    return value.user + value.system


def tree_memory(process: Any) -> tuple[int, int]:
    tree = [process, *process.children(recursive=True)]
    infos = [child.memory_info() for child in tree if child.is_running()]
    return (
        sum(info.rss for info in infos),
        sum(getattr(info, "private", getattr(info, "vms", 0)) for info in infos),
    )


def run_job(run: Path, name: str, mode: str, method: str = "") -> None:
    reg = verify(run)
    write(run / f"{name}-started.json", {"mode": mode, "method": method, "once": True})
    command = [
        sys.executable,
        str(Path(__file__)),
        "worker",
        "--run",
        str(run),
        "--mode",
        mode,
        "--name",
        name,
        "--method",
        method,
    ]
    limit = (
        reg["config"]["training_seconds"]
        if mode in ("profile", "train")
        else reg["config"]["evaluation_seconds_per_method"]
    )
    peak_rss = peak_private = 0
    start, controller = time.perf_counter(), cpu()
    with (run / f"{name}.log").open("x", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        observed = psutil.Process(process.pid)
        failure = None
        while process.poll() is None:
            try:
                rss, private = tree_memory(observed)
                peak_rss = max(peak_rss, rss)
                peak_private = max(peak_private, private)
                disk = 0
                for path in run.rglob("*"):
                    try:
                        if path.is_file():
                            disk += path.stat().st_size
                    except FileNotFoundError:
                        pass
                previous = sum(read(p)["wall_seconds"] for p in run.glob("*-cost.json"))
                prior = reg["config"].get("preflight_run")
                if prior:
                    previous += sum(
                        read(p)["wall_seconds"] for p in (ROOT / prior).glob("*-cost.json")
                    )
                if (
                    time.perf_counter() - start > limit
                    or previous + time.perf_counter() - start > reg["config"]["total_seconds"]
                ):
                    failure = "registered elapsed-time cap"
                elif peak_private > reg["config"]["memory_bytes"]:
                    failure = "registered private-memory cap"
                elif disk > reg["config"]["disk_bytes"]:
                    failure = "registered experiment-disk cap"
                if failure:
                    for child in reversed(observed.children(recursive=True)):
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    process.kill()
                    break
            except psutil.NoSuchProcess:
                break
            time.sleep(0.05)
        code = process.wait()
    write(
        run / f"{name}-cost.json",
        {
            "command": command,
            "returncode": code,
            "wall_seconds": time.perf_counter() - start,
            "controller_cpu_seconds": cpu() - controller,
            "peak_rss_bytes": peak_rss,
            "peak_private_bytes": peak_private,
            "failure": failure,
        },
    )
    if code or failure:
        raise RuntimeError(f"{name} failed; preserve logs and do not rerun this phase")


def worker(run: Path, mode: str, method: str, name: str) -> None:
    start = time.perf_counter()
    reg = verify(run)
    config = reg["config"]
    if mode in ("profile", "train"):
        from toruk_lm.controlled import train_controlled
        from toruk_lm.model import ModelConfig

        result = train_controlled(
            run / "training-data/train.jsonl",
            run / "training-data/validation.jsonl",
            run / mode,
            "recurrent",
            steps=2 if mode == "profile" else 12,
            seed=config["training_seed"] + (1 if mode == "profile" else 0),
            config=ModelConfig(width=32, context=64, layers=2, heads=4),
            slots=4,
        )
        checkpoint = run / mode / "checkpoint.pt"
        if sha(checkpoint) == OLD_HASH:
            raise ValueError("new checkpoint unexpectedly equals historical identity")
        write(
            run / f"{name}-worker.json",
            {
                "result": result,
                "checkpoint_sha256": sha(checkpoint),
                "experiment": "m6-successor-v1",
                "initialization": "new random parameters",
                "self_memory": psutil.Process().memory_info()._asdict(),
                "lifecycle_cpu_seconds": cpu(),
                "worker_seconds": time.perf_counter() - start,
            },
        )
        return
    import torch

    from toruk_lm.chat_foundation import PretrainedChatBackend, TorukContextSelector
    from toruk_lm.context_selection import LexicalContextSelector

    checkpoint = run / "train/checkpoint.pt"
    if sha(checkpoint) != read(run / "train-worker.json")["checkpoint_sha256"]:
        raise ValueError("successor checkpoint identity drift")
    if mode == "heldout":
        frozen = read(run / "freeze.json")
        if frozen["checkpoint_sha256"] != sha(checkpoint):
            raise ValueError("heldout freeze mismatch")
    counts: dict[str, int] = {}

    class Backend(PretrainedChatBackend):
        generated_ids: list[int]
        prompt_ids: list[int]
        fitting = False

        def _tokens(self, messages: list[dict[str, str]]) -> Any:
            result = super()._tokens(messages)
            key = (
                "fit_token_positions"
                if getattr(self, "fitting", False)
                else "history_token_positions"
            )
            counts[key] = counts.get(key, 0) + result.numel()
            return result

        def _fit(self, messages: list[dict[str, str]], indices: list[int]) -> tuple[Any, list[int]]:
            self.fitting = True
            try:
                result = super()._fit(messages, indices)
            finally:
                self.fitting = False
            self.prompt_ids = result[0][0].tolist()
            return result

    backend = Backend(ROOT / reg["backbone"])
    backend.selector = (
        TorukContextSelector(checkpoint)
        if method == "toruk"
        else LexicalContextSelector("lexical-v1")
        if method == "lexical"
        else None
    )
    handles = []

    def hook(key: str) -> Any:
        def count(module: Any, args: Any, kwargs: Any) -> None:
            tokens = kwargs.get("input_ids")
            if tokens is None and args:
                tokens = args[0]
            if tokens is not None:
                counts[key] = counts.get(key, 0) + tokens.numel()
                counts[key + "_calls"] = counts.get(key + "_calls", 0) + 1

        return count

    handles.append(
        backend.model.register_forward_pre_hook(
            hook("backbone_forward_positions"), with_kwargs=True
        )
    )
    if method == "toruk":
        handles.append(
            backend.selector.model.register_forward_pre_hook(
                hook("selector_byte_positions"), with_kwargs=True
            )
        )
    generate = backend.model.generate

    def capture(**kwargs: Any) -> Any:
        result = generate(**kwargs)
        backend.generated_ids = result[0, kwargs["input_ids"].shape[-1] :].tolist()
        return result

    backend.model.generate = capture
    rows = read(run / ("heldout.json" if mode == "heldout" else "development.json"))
    if mode != "heldout":
        rows = rows + [{**rows[0], "id": rows[0]["id"] + "-replay"}]
    first_row = None
    setup_seconds = time.perf_counter() - start
    with (run / f"{name}-answers.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for case in rows:
            counts.clear()
            tick, before_cpu = time.perf_counter(), cpu()
            messages = inference_messages(case)
            response = backend.reply_with_metrics(
                messages,
                config["max_new_tokens"],
                mode="BASELINE" if method == "recent" else "TORUK",
                temperature=0,
                top_p=1,
            )
            elapsed, request_cpu = time.perf_counter() - tick, cpu() - before_cpu
            selected = [int(s[1:]) for s in response["metrics"]["selected_message_ids"]]
            row = {
                "id": case["id"],
                "kind": case["kind"],
                "method": method,
                **response,
                "score": score(response["answer"], case),
                "request_wall_seconds": elapsed,
                "request_cpu_seconds": request_cpu,
                "work": dict(counts),
                "prompt_ids": backend.prompt_ids,
                "generated_ids": backend.generated_ids,
                "selected_sources": [{"id": f"m{i}", **messages[i]} for i in selected],
                "required_evidence_retained": set(case["required"]) <= set(selected),
                "selector_state_bytes": 512 if method == "toruk" else 0,
                "request_history_bytes": sum(len(m["content"].encode()) for m in messages),
            }
            if row["metrics"]["output_tokens"] != len(row["generated_ids"]) or row["metrics"][
                "selected_context_tokens"
            ] != len(row["prompt_ids"]):
                raise ValueError("raw token accounting mismatch")
            if first_row is None:
                first_row = row
            if case["id"].endswith("-replay"):
                if any(
                    row[k] != first_row[k]
                    for k in (
                        "answer",
                        "prompt_ids",
                        "generated_ids",
                        "selected_sources",
                        "work",
                        "score",
                    )
                ):
                    raise ValueError("deterministic smoke replay failed")
            stream.write(json.dumps(row) + "\n")
            stream.flush()
    write(
        run / f"{name}-worker.json",
        {
            "self_memory": psutil.Process().memory_info()._asdict(),
            "lifecycle_cpu_seconds": cpu(),
            "setup_seconds": setup_seconds,
            "worker_seconds": time.perf_counter() - start,
            "cases": len(rows),
            "checkpoint_sha256": sha(checkpoint),
            "model": backend.model_id,
            "generation_config": backend.model.generation_config.to_dict(),
            "torch_threads": torch.get_num_threads(),
        },
    )


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cases": len(rows),
        "correct": sum(r["score"]["correct"] for r in rows),
        "unsupported_proxy": sum(r["score"]["unsupported_abstention_proxy"] for r in rows),
        "stale_proxy": sum(r["score"]["stale_assertion_proxy"] for r in rows),
        "prompt_tokens": sum(r["metrics"]["selected_context_tokens"] for r in rows),
        "output_tokens": sum(r["metrics"]["output_tokens"] for r in rows),
        "request_wall_seconds": sum(r["request_wall_seconds"] for r in rows),
        "request_cpu_seconds": sum(r["request_cpu_seconds"] for r in rows),
        "work": {
            key: sum(r["work"].get(key, 0) for r in rows)
            for key in (
                "history_token_positions",
                "fit_token_positions",
                "backbone_forward_positions",
                "selector_byte_positions",
                "selector_byte_positions_calls",
            )
        },
        "evidence_retained": sum(r["required_evidence_retained"] for r in rows),
        "categories": {
            kind: {
                "n": sum(r["kind"] == kind for r in rows),
                "correct": sum(r["score"]["correct"] for r in rows if r["kind"] == kind),
            }
            for kind in sorted({r["kind"] for r in rows})
        },
    }


def summarize(run: Path) -> dict[str, Any]:
    verify(run)
    results = {}
    for method in METHODS:
        rows = [
            json.loads(line)
            for line in (run / f"heldout-{method}-answers.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        totals = aggregate(rows)
        totals["total_cpu_seconds"] = totals["total_wall_seconds"] = 0.0
        for stage in (
            f"smoke-{method}",
            f"heldout-{method}",
            *(("profile", "train") if method == "toruk" else ()),
        ):
            cost, worker_result = (
                read(run / f"{stage}-cost.json"),
                read(run / f"{stage}-worker.json"),
            )
            totals["total_cpu_seconds"] += (
                worker_result["lifecycle_cpu_seconds"] + cost["controller_cpu_seconds"]
            )
            totals["total_wall_seconds"] += cost["wall_seconds"]
        prior = read(run / "config.json").get("preflight_run")
        if prior:
            old = ROOT / prior
            stages = [f"smoke-{method}"] + (["profile", "train"] if method == "toruk" else [])
            for stage in stages:
                previous_cost = read(old / f"{stage}-cost.json")
                previous_worker = read(old / f"{stage}-worker.json")
                totals["total_cpu_seconds"] += (
                    previous_worker["lifecycle_cpu_seconds"]
                    + previous_cost["controller_cpu_seconds"]
                )
                totals["total_wall_seconds"] += previous_cost["wall_seconds"]
        cost = read(run / f"heldout-{method}-cost.json")
        totals["heldout_peak_rss_bytes"] = cost["peak_rss_bytes"]
        totals["heldout_peak_private_bytes"] = cost["peak_private_bytes"]
        results[method] = totals
    toruk = results["toruk"]
    gates = {}
    for baseline in ("recent", "lexical"):
        other = results[baseline]
        gates[baseline] = {
            "quality_floor": min(toruk["correct"], other["correct"]) / toruk["cases"] >= 0.6,
            "noninferiority": (toruk["correct"] - other["correct"]) / toruk["cases"] >= -0.05,
            "unsupported": toruk["unsupported_proxy"] + toruk["stale_proxy"]
            <= other["unsupported_proxy"] + other["stale_proxy"],
            "cpu_saving": toruk["total_cpu_seconds"] <= 0.9 * other["total_cpu_seconds"],
            "wall_saving": toruk["total_wall_seconds"] <= 0.9 * other["total_wall_seconds"],
        }
    result = {
        "experiment": "m6-successor-v1",
        "historical_m6": "NOT REPRODUCIBLE",
        "checkpoint_sha256": read(run / "train-worker.json")["checkpoint_sha256"],
        "results": results,
        "gates": gates,
        "pass": all(all(g.values()) for g in gates.values()),
        "cost_scope": (
            "Each method's cold setup + development/smoke + heldout; Toruk also pays "
            "all new profile/training. CPU includes controller. Shared environment "
            "installation/backbone-copy/data-registration excluded and recorded separately. "
            "Forward positions use different selector-byte/backbone-native units; "
            "not FLOPs/energy."
        ),
    }
    write(run / "results.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("register", "train", "smoke", "freeze", "heldout", "summarize", "worker")
    )
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/m6-successor-v1.json")
    parser.add_argument("--backbone-dir", type=Path)
    parser.add_argument("--mode", default="")
    parser.add_argument("--method", default="")
    parser.add_argument("--name", default="")
    args = parser.parse_args()
    run = args.run.resolve()
    if args.action == "register":
        register(run, args.config.resolve(), args.backbone_dir.resolve())
    elif args.action == "worker":
        worker(run, args.mode, args.method, args.name)
    elif args.action == "train":
        run_job(run, "profile", "profile")
        run_job(run, "train", "train")
    elif args.action in ("smoke", "heldout"):
        if args.action == "heldout":
            frozen = read(run / "freeze.json")
            if frozen["registration_sha256"] != sha(run / "registration.json"):
                raise ValueError("registration changed after freeze")
        for method in verify(run)["config"]["method_order"]:
            run_job(run, f"{args.action}-{method}", args.action, method)
    elif args.action == "freeze":
        verify(run)
        for method in METHODS:
            if read(run / f"smoke-{method}-cost.json")["returncode"]:
                raise ValueError("smoke execution failed")
        write(
            run / "freeze.json",
            {
                "registration_sha256": sha(run / "registration.json"),
                "checkpoint_sha256": sha(run / "train/checkpoint.pt"),
                "development_outputs": {m: sha(run / f"smoke-{m}-answers.jsonl") for m in METHODS},
            },
        )
    else:
        print(json.dumps(summarize(run), indent=2))


if __name__ == "__main__":
    main()
