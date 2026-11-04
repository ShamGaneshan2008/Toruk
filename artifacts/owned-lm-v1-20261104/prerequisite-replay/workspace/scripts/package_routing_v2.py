"""Post-evaluation report and integrity package for the registered Path A study."""

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    if path.exists():
        raise ValueError(f"refusing to overwrite {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run
    summary = read(run / "summary.json")
    methods = summary["methods"]
    quality = {}
    for method, seeds in methods.items():
        quality[method] = all(
            (c := seeds[s]["0"])["accuracy"] >= 0.8
            and c["known_correct"] / c["known_worlds"] >= 0.8
            and c["unsupported"] / c["unknown_queries"] <= 0.05
            and all(v["correct"] / v["worlds"] >= 0.7 for v in c["categories"].values())
            for s in ("31", "47")
        )
    route_improved = all(
        methods["new"][s]["0"][metric + "_correct"] / methods["new"][s]["0"][metric + denominator]
        > methods["old"][s]["0"][metric + "_correct"] / methods["old"][s]["0"][metric + denominator]
        for s in ("31", "47")
        for metric, denominator in (("read", "_queries"), ("write", "_records"))
    )
    known_improved = all(
        methods["new"][s]["0"]["known_correct"] > methods["old"][s]["0"]["known_correct"]
        for s in ("31", "47")
    )
    stronger = all(
        summary["uncertainty"]["new"][f"difference_vs_{b}95"][0] > 0 for b in ("recent", "lexical")
    )
    useful = quality["new"] and stronger
    verdicts = {
        "path": "A",
        "target_routing_improved_both_seeds": "PASS" if route_improved else "FAIL",
        "target_factual_improved_both_seeds": "PASS"
        if route_improved and known_improved
        else "FAIL",
        "minimum_quality_by_method": {m: "PASS" if v else "FAIL" for m, v in quality.items()},
        "requested_gates": {
            "useful_conversational_answers": (
                "INCONCLUSIVE: synthetic research decoder; Qwen integration smoke only"
            ),
            "toruk_owned_useful_learned_memory": "PASS" if useful else "FAIL",
            "fewer_selected_tokens_preserved_quality": (
                "FAIL: same integrated prompt budget; quality gate required"
            ),
            "lower_total_resource_cost": (
                "FAIL: full history updates and extra routing work; no qualified cost reduction"
            ),
            "generalization": "PASS on this narrow held-out grammar"
            if useful
            else "FAIL on useful factual transfer; broader conversation unestablished",
            "research_paper_readiness": "INCONCLUSIVE"
            if useful
            else "FAIL: qualified evidence prerequisites unmet",
            "protected_preview_readiness": (
                "FAIL: Path A; no qualified integrated chat candidate or preview gate"
            ),
            "public_chatbot_readiness": "FAIL: no qualified public release candidate",
        },
        "mechanism_exists": (
            "PASS: learned routing/state influence tested; distinct trained checkpoints"
        ),
    }
    save(run / "verdicts.json", verdicts)
    regressions = {}
    for s in ("31", "47"):
        regressions[s] = {
            c: {
                "old": v["correct"],
                "new": methods["new"][s]["0"]["categories"][c]["correct"],
                "delta": methods["new"][s]["0"]["categories"][c]["correct"] - v["correct"],
            }
            for c, v in methods["old"][s]["0"]["categories"].items()
        }
    save(run / "category-changes.json", regressions)
    training = {str(s): read(run / "train" / f"new-{s}.json") for s in (31, 47)}
    save(run / "training-costs.json", training)
    worlds = {(w["id"], w["load"]): w for w in read(run / "final.json")}
    collapse = {"posthoc": True, "no_new_inference_or_tuning": True, "seeds": {}}
    for s in (31, 47):
        grouped = defaultdict(Counter)
        expected = defaultdict(Counter)
        for p in read(run / "raw" / f"new-{s}.json")["predictions"]:
            if p["load"] == 0:
                for answer in p["answers"]:
                    if answer["evidence"]:
                        source = worlds[p["id"], 0]["events"][answer["evidence"][0]]
                        grouped[source["operation"]][answer["answer"]] += 1
                        expected[source["operation"]][answer["expected"]] += 1
        collapse["seeds"][str(s)] = {
            "generated_by_authoritative_operation": dict(grouped),
            "expected_by_authoritative_operation": dict(expected),
        }
    save(run / "output-collapse.json", collapse)
    commands = []
    for directory in (run / "checks", run / "verification"):
        for p in sorted(directory.glob("*.json")):
            value = read(p)
            if "command" in value:
                commands.append({"record": p.as_posix(), **value})
    save(run / "commands.json", commands)
    lines = [
        "# Path A routing v2: measured evidence",
        "",
        "One registered routing intervention; old baselines/weights unchanged. "
        "Final worlds use previously unused word-order templates and three fresh seeds. "
        "This tests permutation transfer in a finite domain, not conversational capability.",
        "",
        (run / "table.md").read_text(encoding="utf-8"),
        "",
        "All primary columns are load-0 totals over 168 worlds /192 generated answers. "
        "Both answers must match in multi-fact worlds. RSS is sampled over loading, "
        "all loads and offline routing diagnostics. Forward positions are recurrent "
        "work only; extra routing positions count additional embedding/pooling work, "
        "which must not be treated as free or added as equivalent FLOPs.",
        "",
        "## Routing and evidence exposure",
        "",
        "| Method | Seed | Read correct /queries | Write correct /records | "
        "Relevant suffix exposure /144 | Relevant ingestion /144 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        for s in ("31", "47"):
            c = seeds[s]["0"]
            lines.append(
                f"| {method} | {s} | "
                + (
                    f"{c['read_correct']}/{c['read_queries']} | "
                    f"{c['write_correct']}/{c['write_records']} | "
                    if "read_correct" in c
                    else "N/A | N/A | "
                )
                + f"{c['evidence_suffix_exposed']}/{c['evidence_queries']} "
                + f"| {c['evidence_ingested']}/{c['evidence_queries']} |"
            )
    lines += [
        "",
        "Suffix exposure counts any contributing bytes, not a full usable record. "
        "Integrated history ingestion is not evidence of semantic state retention. "
        "Read/write labels score diagnostic outputs offline; inference sees only text. "
        "Posthoc saved-output analysis finds a collapse at both seeds: every queried "
        "revised fact generates blue (72 queries), and every queried original fact "
        "generates cat (72 queries), despite varied reference values. This association "
        "does not prove a causal localization to one encoder layer. Perfect top-1 "
        "address accuracy does not imply uncontaminated soft state or faithful decoding. "
        "The 14 correct known worlds are insufficient evidence of useful value recall.",
        "",
        "## Categories: old versus new",
        "",
        "| Seed | Category | Old /24 | New /24 | Change |",
        "|---|---|---:|---:|---:|",
    ]
    for s, cats in regressions.items():
        for cat, values in cats.items():
            lines.append(
                f"| {s} | {cat} | {values['old']} | {values['new']} | {values['delta']:+d} |"
            )
    lines += [
        "",
        "## Paired uncertainty",
        "",
        "Intervals are conditional on two trained models. Worlds are clustered, "
        "including training-seed pairing. Repeated stress loads are not independent data.",
        "",
        "```json",
        json.dumps(summary["uncertainty"], indent=2),
        "```",
        "",
        "## Stress loads and history accounting",
        "",
        "| Method | Seed | Added turns | Exact /168 | Known /120 | Unsupported /48 | "
        "Scanned tokens | Selected tokens | Forward positions | Extra routing | Latency ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        for s in ("31", "47"):
            for load in ("0", "8", "32"):
                c = seeds[s][load]
                lines.append(
                    f"| {method} | {s} | {load} | "
                    + " | ".join(
                        str(c[k])
                        for k in (
                            "correct",
                            "known_correct",
                            "unsupported",
                            "history_tokens_scanned",
                            "selected_tokens",
                            "forward_positions",
                            "extra_routing_embedding_positions",
                        )
                    )
                    + f" | {c['response_ms']:.1f} |"
                )
    lines += [
        "",
        "## Per-evaluation-seed accuracy",
        "",
        "| Method | Training seed | World seed | Exact /56 | Known /40 | Unsupported /16 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, seeds in methods.items():
        for s in ("31", "47"):
            for world_seed, c in seeds[s]["eval_seeds"].items():
                lines.append(
                    f"| {method} | {s} | {world_seed} | {c['correct']} "
                    f"| {c['known_correct']} | {c['unsupported']} |"
                )
    lines += ["", "## Generated gains, failures and regressions", ""]
    for s, groups in read(run / "examples.json").items():
        lines += [
            f"### Training seed {s}",
            "",
            "| Kind | World | Query | Expected | Old generated | New generated |",
            "|---|---|---|---|---|---|",
        ]
        for name, examples in groups.items():
            if not examples:
                lines.append(f"| {name} | No such example | | | | |")
            for pair in examples[:2]:
                for old, new in zip(pair["old"]["answers"], pair["new"]["answers"], strict=True):
                    vals = [
                        name,
                        pair["new"]["id"],
                        new["query"],
                        new["expected"],
                        old["answer"],
                        new["answer"],
                    ]
                    lines.append(
                        "| "
                        + " | ".join(v.replace("|", "\\|").replace("\n", " ") for v in vals)
                        + " |"
                    )
    lines += [
        "",
        "## Verdicts",
        "",
        "```json",
        json.dumps(verdicts, indent=2),
        "```",
        "",
        "## Compute",
        "",
        f"New optimization: 1,600 steps, 25,600 sampled case presentations, "
        f"{sum(v['training_seconds'] for v in training.values()):.3f} seconds in optimizer loops. "
        "All training uses one Torch CPU thread; no GPU/download/paid compute. "
        "All evaluation cells ran serially before verification. OS/shared-host activity "
        "is uncontrolled; report latency/RSS observations without speedup claims.",
        "",
        "Training and per-process peak memory, all parent wall times, and separate "
        "offline diagnostic time are retained in JSON. RSS is sampled every 5 ms and "
        "can miss short peaks; it includes framework/model loading and diagnostics. "
        "All history is rebuilt for each query, including both multi-fact answers.",
        "",
        "## Exact commands and exit codes",
        "",
        "Registration command and its exit-0 record are in "
        "artifacts/checks/routing-v2-register-20261103.json. Every command below has a "
        "source identity, full log, parent duration and result.",
        "",
        "| Check | Exit | Exact argv |",
        "|---|---:|---|",
    ]
    for c in commands:
        lines.append(
            f"| {Path(c['record']).stem} | {c['returncode']} | `{json.dumps(c['command'])}` |"
        )
    (run / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run / "final-status.txt").write_text(
        subprocess.check_output(["git", "status", "--short"], text=True)
    )
    for filename in (
        "scripts/package_routing_v2.py",
        "scripts/audit_routing_v2.py",
        "scripts/smoke_qualification_ui.py",
        "scripts/check.py",
        "scripts/verify.py",
        "docs/research/routing-v2-results.md",
        "README.md",
        "MANIFEST.in",
    ):
        path = Path(filename)
        target = run / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError(f"archive collision {target}")
        target.write_bytes(path.read_bytes())
    save(
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
