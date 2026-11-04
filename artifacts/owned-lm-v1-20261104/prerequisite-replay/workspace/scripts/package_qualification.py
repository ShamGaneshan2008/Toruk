"""Package post-evaluation evidence without changing the frozen experiment."""

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import torch


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    if path.exists():
        raise ValueError(f"refusing to overwrite {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run
    for name in (
        "scripts/package_qualification.py",
        "scripts/smoke_qualification_ui.py",
        "scripts/smoke_chat_foundation.py",
        "scripts/smoke_vercel_local.py",
        "scripts/check.py",
        "scripts/verify.py",
        "MANIFEST.in",
        "README.md",
        "docs/research/qualification-v1-results.md",
        "docs/research/qualification-v1-paper-outline.md",
        ".github/workflows/ci.yml",
        "web/vercel/public/index.html",
        "web/vercel/tests/ui.test.mjs",
        "web/vercel/tests/proxy.test.mjs",
        "web/vercel/lib/proxy.js",
        "web/vercel/scripts/dev.mjs",
        "web/vercel/package.json",
    ):
        path = Path(name)
        target = run / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError(f"source archive collision: {target}")
        target.write_bytes(path.read_bytes())
    summary = read(run / "summary.json")
    old = Path("artifacts/integrated-memory-v1-20261102")
    paths = {
        "ordinary_foundation": "artifacts/foundation-001/train/checkpoint.pt",
        "ordinary_minimal_demo": "artifacts/minimal-lm-demo-001/train/checkpoint.pt",
        "historical_controlled_recurrent": "artifacts/m6-validation-001/recurrent/checkpoint.pt",
        "controlled_smoke_only": (
            "artifacts/checks/public-gate-20261027/research-smoke/recurrent-full/checkpoint.pt"
        ),
        "chat_selector_v1": "artifacts/chat-selector-v1-20261101/selector.json",
        "chat_selector_v2": "artifacts/chat-selector-v2-20261101/selector.json",
        "qwen_chat_backbone": "artifacts/qwen-chat-001/backbone/model.safetensors",
        **{
            f"{v}_{s}": str(old / "train" / f"{v}-{s}.pt")
            for v in ("ordinary", "integrated")
            for s in (31, 47)
        },
    }
    inventory = {}
    for name, filename in paths.items():
        path = Path(filename)
        item = {"path": filename, "exists": path.exists()}
        if path.exists():
            with path.open("rb") as stream:
                item["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
            item["bytes"] = path.stat().st_size
            if path.suffix == ".pt":
                saved = torch.load(path, map_location="cpu", weights_only=True)
                item["format"] = saved.get("format")
        inventory[name] = item
    inventory["chat_wiring"] = {
        "server": "src/toruk_lm/inference_server.py -> inference_worker.py -> chat_foundation.py",
        "language": "third-party pinned Qwen, or separately configured Ollama",
        "selectors": "explicit JSON v1/v2, heuristic, or historical controlled checkpoint",
        "integrated_model": "research CLI only; incompatible with pretrained chat backbone",
        "ordinary_model": "optional labeled continuation smoke path; not instruct chat",
    }
    write(run / "inventory.json", inventory)
    records = []
    for directory in (run / "checks", run / "verification"):
        for path in sorted(directory.glob("*.json")):
            value = read(path)
            if "command" in value:
                records.append({"record": path.as_posix(), **value})
    write(run / "commands.json", records)
    costs = {
        f"{v}-{s}": read(old / "train" / f"{v}-{s}.json")
        for v in ("ordinary", "integrated")
        for s in (31, 47)
    }
    write(run / "training-costs.json", costs)
    examples = {}
    for seed in (31, 47):
        baseline = {
            p["id"]: p
            for p in read(run / "raw" / f"recent-{seed}.json")["predictions"]
            if p["load"] == 0
        }
        integrated = [
            p
            for p in read(run / "raw" / f"integrated-{seed}.json")["predictions"]
            if p["load"] == 0
        ]
        groups = {
            "gains": lambda p, baseline=baseline: p["correct"] and not baseline[p["id"]]["correct"],
            "regressions": lambda p, baseline=baseline: (
                not p["correct"] and baseline[p["id"]]["correct"]
            ),
            "preservation_failures": lambda p: p["category"] == "preservation" and not p["correct"],
            "unsupported": lambda p: any(a["unsupported"] for a in p["answers"]),
        }
        examples[str(seed)] = {
            name: [
                {"integrated": p, "recent": baseline[p["id"]]} for p in integrated if predicate(p)
            ][:5]
            for name, predicate in groups.items()
        }
    write(run / "examples.json", examples)
    verdicts = {}
    methods = summary["methods"]
    for method, seeds in methods.items():
        quality = True
        for seed in ("31", "47"):
            cell = seeds[seed]["0"]
            quality &= (
                cell["accuracy"] >= 0.8
                and cell["known_correct"] / cell["known_worlds"] >= 0.8
                and cell["unsupported"] / cell["unknown_queries"] <= 0.05
                and all(c["correct"] / c["worlds"] >= 0.7 for c in cell["categories"].values())
            )
        verdicts[method] = {"minimum_quality": "PASS" if quality else "FAIL"}
    for method in ("integrated", "learned"):
        better = all(
            summary["uncertainty"][method][f"difference_vs_{b}_95"][0] > 0
            and all(
                methods[method][s]["0"]["accuracy"] > methods[b][s]["0"]["accuracy"]
                for s in ("31", "47")
            )
            for b in ("recent", "lexical")
        )
        verdicts[method]["primary_repeatable_accuracy_improvement"] = "PASS" if better else "FAIL"
        verdicts[method]["useful_memory_benefit"] = (
            "PASS" if better and verdicts[method]["minimum_quality"] == "PASS" else "FAIL"
        )
        preserved = all(
            methods[method][s]["0"]["unsupported"] <= methods[b][s]["0"]["unsupported"]
            and all(
                methods[method][s]["0"]["categories"][c]["correct"]
                >= methods[b][s]["0"]["categories"][c]["correct"]
                for c in ("correction", "preservation")
            )
            for b in ("recent", "lexical")
            for s in ("31", "47")
        )
        verdicts[method]["correction_preservation"] = (
            "PASS" if preserved and verdicts[method]["minimum_quality"] == "PASS" else "FAIL"
        )
        cheaper = all(
            all(
                methods[method][s]["0"][key] < methods[b][s]["0"][key]
                for key in ("forward_positions", "response_ms")
            )
            and methods[method][s]["sampled_peak_rss"] < methods[b][s]["sampled_peak_rss"]
            for b in ("recent", "lexical")
            for s in ("31", "47")
        )
        verdicts[method]["quality_preserving_total_cost"] = (
            "PASS" if cheaper and verdicts[method]["minimum_quality"] == "PASS" else "FAIL"
        )
    verdicts["scope"] = {
        "population_training_seed_generalization": "INCONCLUSIVE: only two checkpoints",
        "conversational_integrated_memory": "INCONCLUSIVE: incompatible with chat backbone",
        "novelty_and_publication": "INCONCLUSIVE: no comprehensive literature/venue review",
        "resource_benchmark": "INCONCLUSIVE: shared host, verification ran concurrently",
    }
    write(run / "verdicts.json", verdicts)
    lines = [
        "# Qualification v1 detailed evidence",
        "",
        "All quality gates failed. Treat fluency, abstention ties, and smaller prompt "
        "counts separately from useful memory. Frozen data: 168 worlds, three evaluation "
        "seeds; stress repeats at +8/+32 turns. Two training checkpoints per method.",
        "",
        (run / "table.md").read_text(encoding="utf-8"),
        "",
        "Accuracy columns are exact world counts /168; unsupported counts are /48. "
        "For multi-fact worlds both answers must match. Selected/forward counts and latency "
        "are sums over 192 generated answers at load 0. RSS is the process peak sampled "
        "over all three loads, including loading; it cannot be attributed to load 0 alone.",
        "",
        "## Categories and stress",
        "",
        "| Method | Train seed | Added turns | Correct /168 | Known /120 | Unsupported /48 "
        "| Full scanned tokens | Selected tokens | Forward positions | Latency ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        for s in ("31", "47"):
            for load in ("0", "8", "32"):
                c = seeds[s][load]
                lines.append(
                    f"| {method} | {s} | {load} | {c['correct']} | {c['known_correct']} "
                    f"| {c['unsupported']} | {c['history_tokens_scanned']} "
                    f"| {c['selected_tokens']} | {c['forward_positions']} "
                    f"| {c['response_ms']:.1f} |"
                )
    lines += [
        "",
        "| Method | Seed | " + " | ".join(methods["recent"]["31"]["0"]["categories"]) + " |",
        "|---|---:|" + "---:|" * 7,
    ]
    for method, seeds in methods.items():
        for s in ("31", "47"):
            lines.append(
                f"| {method} | {s} | "
                + " | ".join(
                    str(v["correct"]) + "/" + str(v["worlds"])
                    for v in seeds[s]["0"]["categories"].values()
                )
                + " |"
            )
    lines += [
        "",
        "## Paired uncertainty",
        "",
        "Percentile 95% intervals for absolute "
        "accuracy differences; world clusters preserve training-seed pairing. "
        "Conditional on two trained models; no seed-population inference.",
        "",
        "| Method | Versus recent | Versus lexical |",
        "|---|---:|---:|",
    ]
    for method, values in summary["uncertainty"].items():
        lines.append(
            "| "
            + method
            + " | "
            + " | ".join(
                ", ".join(f"{x:.4f}" for x in values[f"difference_vs_{b}_95"])
                for b in ("recent", "lexical")
            )
            + " |"
        )
    lines += [
        "",
        "## Exact commands and exit codes",
        "",
        "Freeze command (observed exit 0, before generation):",
        "",
        "```powershell",
        ".\\.venv\\Scripts\\python.exe scripts/qualify_memory.py freeze "
        "--run artifacts/qualification-v1-20261103",
        "```",
        "",
        "Full source-identity records and logs accompany each command in commands.json.",
        "",
        "| Check | Exit | Exact argv (JSON array) |",
        "|---|---:|---|",
    ]
    for record in records:
        lines.append(
            f"| {Path(record['record']).stem} | {record['returncode']} "
            f"| `{json.dumps(record['command'])}` |"
        )
    lines += [
        "",
        "Training costs are copied verbatim into training-costs.json and are shared "
        "by inference ablations; do not count each ablation as a separately trained model. "
        "No optimizer steps were added for qualification. Raw outputs and original "
        "negative results remain intact.",
        "",
    ]
    (run / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (run / "final-status.txt").write_text(
        subprocess.check_output(["git", "status", "--short"], text=True), encoding="utf-8"
    )
    # This manifest intentionally excludes itself; includes report, sources and raw answers.
    write(
        run / "manifest.json",
        {
            "created_utc": datetime.now(UTC).isoformat(),
            "files": {
                p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(run.rglob("*"))
                if p.is_file()
            },
        },
    )
    print(json.dumps(verdicts, indent=2))


if __name__ == "__main__":
    main()
