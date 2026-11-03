"""Package fixed development-gate results without starting another experiment."""

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run
    if (run / "report.md").exists():
        raise ValueError("report already exists")
    summary = read(run / "summary.json")
    methods = summary["methods"]
    training = {str(seed): read(run / "train" / f"augmented-{seed}.json") for seed in (31, 47)}
    regressions = {
        seed: {
            category: {
                "old": value["correct"],
                "augmented": methods["augmented"][seed]["categories"][category]["correct"],
                "delta": methods["augmented"][seed]["categories"][category]["correct"]
                - value["correct"],
            }
            for category, value in methods["old"][seed]["categories"].items()
        }
        for seed in ("31", "47")
    }
    (run / "regressions.json").write_text(json.dumps(regressions, indent=2) + "\n")
    commands = []
    for directory in (run / "checks", run / "verification"):
        for path in sorted(directory.glob("*.json")):
            result = read(path)
            if "command" in result:
                commands.append({"label": path.stem, "record": path.as_posix(), **result})
    (run / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    lines = [
        "# Existing-model value-fidelity development gate",
        "",
        f"Milestone verdict: **{summary['milestone_status']}**. Development only. "
        "No new final set was generated or opened for scoring. Historical final "
        "artifacts were integrity-checked only, not used for fitting or checkpoint selection. "
        "The architecture, pretrained chat backbone and external conversational selector "
        "remain unchanged. Both 800-step fits were fixed in advance.",
        "",
        (run / "table.md").read_text(encoding="utf-8"),
        "",
        "Accuracy is exact per world, requiring both multi-fact answers to match. "
        "Token/work/latency totals cover 192 generated answers over 168 worlds. "
        "RSS includes interpreter/model loading and offline routing diagnostics. "
        "Recurrent positions and additional pooling/embedding positions are different "
        "workload proxies; neither is FLOPs, energy or total compute.",
        "",
        "## Deciding gate",
        "",
        "```json",
        json.dumps(summary["gates"], indent=2),
        "```",
        "",
        "## Categories and regressions",
        "",
        "| Training seed | Category | Old /24 | Augmented /24 | Change |",
        "|---|---|---:|---:|---:|",
    ]
    for seed, categories in regressions.items():
        for category, result in categories.items():
            lines.append(
                f"| {seed} | {category} | {result['old']} | {result['augmented']} "
                f"| {result['delta']:+d} |"
            )
    lines += [
        "",
        "## Memory evidence and routing",
        "",
        "| Method | Seed | Relevant records ingested /queries | Relevant suffix exposure "
        "/queries | Read /queries | Write /records | Full history scans, tokens |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        for seed in ("31", "47"):
            result = seeds[seed]
            read_score = (
                f"{result['read_correct']}/{result['read_queries']}"
                if "read_correct" in result
                else "N/A"
            )
            write_score = (
                f"{result['write_correct']}/{result['write_records']}"
                if "write_correct" in result
                else "N/A"
            )
            lines.append(
                f"| {method} | {seed} | {result['evidence_ingested']}/{result['evidence_queries']} "
                f"| {result['evidence_suffix_exposed']}/{result['evidence_queries']} "
                f"| {read_score} | {write_score} | {result['history_tokens_scanned']} |"
            )
    lines += [
        "",
        "Ingestion is not proof of faithful latent-state retention. Suffix exposure "
        "counts any contributing bytes, not necessarily a complete record. Correct "
        "generated values and the zero-state gap provide separate evidence of memory use.",
        "",
        "## Individual generated outputs",
        "",
        "| Seed | Kind | World | Query | Expected | Old | Augmented |",
        "|---|---|---|---|---|---|---|",
    ]
    for seed, groups in read(run / "examples.json").items():
        for kind, examples in groups.items():
            if not examples:
                lines.append(f"| {seed} | {kind} | No example | | | | |")
            for example in examples[:2]:
                for before, after in zip(
                    example["old"]["answers"], example["augmented"]["answers"], strict=True
                ):
                    values = [
                        seed,
                        kind,
                        example["augmented"]["id"],
                        after["query"],
                        after["expected"],
                        before["answer"],
                        after["answer"],
                    ]
                    lines.append(
                        "| "
                        + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values)
                        + " |"
                    )
    lines += [
        "",
        "Full histories are in development.json; all decoded answers and token IDs "
        "are in raw/*.json. No answer normalization, scripted output or gold-state "
        "injection was used. Offline labels only score runtime outputs.",
        "",
        "## Output diversity on known facts",
        "",
        "```json",
        json.dumps(
            {
                method: {
                    seed: methods[method][seed]["known_generated_distribution"]
                    for seed in ("31", "47")
                }
                for method in ("old", "augmented", "zero")
            },
            indent=2,
        ),
        "```",
        "",
        "## Conditional uncertainty",
        "",
        "Two trained checkpoints; paired worlds are "
        "clustered across those checkpoints and stratified by development seed/category. "
        "These are development diagnostics, not final-test or training-population intervals.",
        "",
        "```json",
        json.dumps(summary["uncertainty"], indent=2),
        "```",
        "",
        "## Each development world seed",
        "",
        "| Method | Training seed | World seed | Exact /56 | Known /40 | Unsupported /16 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        for seed in ("31", "47"):
            for world_seed, result in seeds[seed]["per_evaluation_seed"].items():
                lines.append(
                    f"| {method} | {seed} | {world_seed} | {result['correct']} "
                    f"| {result['known_correct']} | {result['unsupported']} |"
                )
    lines += [
        "",
        "## Training cost and identities",
        "",
        f"Total optimizer-loop time: {sum(v['training_seconds'] for v in training.values()):.3f} "
        "seconds; 1,600 optimizer steps and 25,600 sampled world presentations. "
        "One Torch CPU thread, float32; no model downloads, GPU jobs or paid compute. "
        "Full process durations include startup/checking and are in check records.",
        "",
        "```json",
        json.dumps(training, indent=2),
        "```",
        "",
        "Original source/split/old-checkpoint hashes are in registration.json; new "
        "checkpoint hashes were sealed in models.json before inference. New files keep "
        "the toruk-pooled-router-v2 model format with an explicit value-fidelity-dev-v1 "
        "training recipe and distinct paths/SHA values. All historical artifacts stay intact.",
        "",
        "## Exact commands and exit codes",
        "",
        "Registration exit-0 evidence is artifacts/checks/value-fidelity-register-20261103.json.",
        "",
        "| Check | Exit | Exact argv |",
        "|---|---:|---|",
    ]
    for command in commands:
        lines.append(
            f"| {command['label']} | {command['returncode']} | `{json.dumps(command['command'])}` |"
        )
    lines += [
        "",
        "This completes one development gate. No final qualification, research-paper "
        "claim, resource advantage, chat integration or deployment milestone is started. "
        "Finite shared symbols, synthetic permutations, two training seeds and shared-host "
        "timing limit interpretation. Original final answers were never used to fit this recipe.",
        "",
    ]
    (run / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (run / "final-git-status.txt").write_text(
        subprocess.check_output(["git", "status", "--short"], text=True)
    )
    for filename in (
        "scripts/report_value_fidelity_dev.py",
        "scripts/audit_value_fidelity_dev.py",
        "docs/research/value-fidelity-dev-v1-results.md",
        "README.md",
        ".gitattributes",
        "MANIFEST.in",
    ):
        path = Path(filename)
        target = run / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError("source archive collision")
        target.write_bytes(path.read_bytes())
    manifest = {
        "created_utc": datetime.now(UTC).isoformat(),
        "role": "development-only",
        "files": {
            p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(run.rglob("*"))
            if p.is_file()
        },
    }
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(summary["milestone_status"], "Development-only gate packaged; no next milestone started.")


if __name__ == "__main__":
    main()
