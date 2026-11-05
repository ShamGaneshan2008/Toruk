"""Derive complete raw tables and cost accounting without changing the frozen study."""

import argparse
import json
from pathlib import Path

from toruk_lm.owned_training import write_json


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def cell(value):
    return (
        "`" + json.dumps(value, ensure_ascii=True).replace("|", "\\|").replace("`", "\\u0060") + "`"
    )


def integration_audit(summary, decision):
    """Apply every release requirement, including zero refusal errors explicitly."""
    candidate = summary["candidate"]
    refusal = candidate["categories"]["refusal"]
    return {
        "quality_and_framing": decision["integration"],
        "zero_refusal_errors": refusal["exact"] == refusal["n"],
        "pass": decision["integration"] and refusal["exact"] == refusal["n"],
    }


def report(run):
    summary = read(run / "summary.json")
    decision = read(run / "decision.json")
    write_json(
        run / "integration-audit.json",
        {
            suite: integration_audit(summary[suite], decision[suite])
            for suite in ("primary", "regression")
        },
    )
    rows = [r for path in sorted(run.glob("outputs-*.json")) for r in read(path)]
    for suite in ("development", "primary", "regression"):
        selected = [r for r in rows if r["suite"] == suite]
        conditions = list(summary[suite])
        table = [
            "# Raw answers: " + suite,
            "",
            "Owned answers are unmodified role-line continuations; quotes/newlines are shown.",
            "Errors are explicit. Inputs and answers are in the sealed data files.",
            "",
            "| Case | Expected | " + " | ".join(conditions) + " |",
            "|---|---|" + "---|" * len(conditions),
        ]
        for case in dict.fromkeys(r["case"] for r in selected):
            group = [r for r in selected if r["case"] == case]
            table.append(
                "| "
                + case
                + " | "
                + cell(group[0]["expected"])
                + " | "
                + " | ".join(
                    cell(
                        next(r for r in group if r["condition"] == c)["error"]
                        or next(r for r in group if r["condition"] == c)["raw_answer"]
                    )
                    for c in conditions
                )
                + " |"
            )
        (run / f"raw-{suite}.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    control = read(run / "models/control/checkpoint.json")
    first = read(run / "models/candidate/step256.json")
    second = read(run / "models/candidate/checkpoint.json")
    resources = {
        "candidate": {
            "targets": second["training_targets_total"],
            "seconds": first["seconds"] + second["seconds"],
            "cpu_seconds": first["cpu_seconds"] + second["cpu_seconds"],
            "peak_rss": max(r["memory"]["process_lifetime_peak_rss"] for r in (first, second)),
            "resume_boundary": second["resumed_from"],
        },
        "control": {
            "targets": control["training_targets_total"],
            "seconds": control["seconds"],
            "cpu_seconds": control["cpu_seconds"],
            "peak_rss": control["memory"]["process_lifetime_peak_rss"],
        },
        "total_optimized_targets": control["training_targets_total"]
        + second["training_targets_total"],
        "checkpoint_bytes": sum(p.stat().st_size for p in (run / "models").rglob("*.pt")),
        "dollars": "No paid API, accelerator or job; energy/dollar cost not measured.",
        "rss_monitor_caveat": "Parent-process samples can miss the Windows venv launcher's "
        "child. Use the actual training process OS lifetime high-water marks above. "
        "Trainer checks RSS at fit boundaries, not every optimizer boundary. "
        "This is a protocol enforcement deviation; observed peaks are below the caps.",
    }
    write_json(run / "resources.json", resources)
    lines = [
        "# Derived metrics",
        "",
        "EOS termination is not exposed by the external backend and is unavailable there.",
        "External forward-position accounting is also unavailable, not zero work.",
        "",
    ]
    for suite, conditions in summary.items():
        lines += [
            "## " + suite,
            "",
            "| Condition | N | Content exact | Framed | EOS | Errors | Unknown proxy | "
            "Repeated trigrams | Unique | Seconds | Prompt tokens | Output tokens |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for c, s in conditions.items():
            eos = "unavailable" if c == "external_qwen" else s["terminated"]
            framed = "native content" if c == "external_qwen" else s["framed"]
            lines.append(
                f"| {c} | {s['n']} | {s['exact']} | {framed} | {eos} | "
                f"{s['errors']} | {s['unsupported_unknown_proxy']} | "
                f"{s['repeated_trigrams']} | {s['unique_nonempty']} | "
                f"{s['seconds']:.4f} | {s['prompt_tokens']} | {s['output_tokens']} |"
            )
        lines += [
            "",
            "Category exact scores:",
            "",
            "| Category | " + " | ".join(conditions) + " |",
            "|---|" + "---|" * len(conditions),
        ]
        for category in conditions["candidate"]["categories"]:
            lines.append(
                "| "
                + category
                + " | "
                + " | ".join(
                    f"{s['categories'][category]['exact']}/{s['categories'][category]['n']}"
                    for s in conditions.values()
                )
                + " |"
            )
        lines.append("")
    (run / "metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(resources, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    report(parser.parse_args().run)
