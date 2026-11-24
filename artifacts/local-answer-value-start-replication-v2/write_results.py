"""Render already audited results; never imports a model or changes sealed files."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    audit = read(BASE / "independent-audit.json")
    assert audit["measurement_integrity"] == "PASS"
    summary = read(BASE / "registered/execution/summary.json")
    plan = read(BASE / "plan-final.json")
    prep = read(BASE / "preparation/budget/cost.json")
    budget = read(BASE / "registered/budget/cost.json")
    rehearsal = read(BASE / "preparation/rehearsal/cost.json")
    rehearsal_result = read(BASE / "preparation/rehearsal/rehearsal.json")
    measured_scopes = [
        ("Preparation including contracts/rehearsal", prep),
        ("Registered budget", budget),
        ("Independent saved-only audit", read(BASE / "audit-execution/cost.json")),
        ("Repository verification", read(BASE / "verification/execution/cost.json")),
    ]
    failures = {}
    lines = [
        "# Value-start replication v2: crossed initialization and shuffle results",
        "",
        "24 November 2026. Registered decision: **" + audit["decision"] + "**. "
        "Measurement integrity: **PASS**. This is an objective replication, not a memory study.",
        "",
        "## Preservation and registered design",
        "",
        "Git root D:/Toruk, branch main, HEAD91f2e2b8e6b171c1b1f4fb27898f37f17b6b93ed; "
        "local origin/main matches (0/0). No commit, push or deployment. Value-start v1 is "
        "preserved in that reviewed commit, including STOP_DEVELOPMENT_FAILURE, its "
        "search-scope exception, raw outputs, independent audit and seals. The unchanged "
        "v1 verifier passed outside sandbox read restrictions:737 protected files,337 "
        "paired-batch files,65 old ignored checkpoints,24 scientific seals. Its388-entry "
        "review inventory additionally binds all eight v1 weights. Initial sandbox access "
        "errors produced324 apparent Git deletions; readable Git reports no actual tracked "
        "changes. No historical files or permissions were repaired.",
        "",
        "[Precondition](../../artifacts/local-answer-value-start-replication-v2/precondition.json), "
        "[starting state](../../artifacts/local-answer-value-start-replication-v2/starting-state.json). "
        "The v1 scope incident remains disclosed; it cannot be recast as zero unrelated "
        "artifact access. V2 uses only named permitted development material; no held-out "
        "input or external model generated a research answer.",
        "",
        "Initialization601/947 CROSS shuffle1301/1709, ordinary/recurrent, uniform/first16: "
        "16 fresh fits,8 matched objective pairs. Initial hashes match within initialization/"
        "model across objectives AND shuffle seeds; schedules match within shuffle across "
        "initializations/models/objectives and differ across the two shuffle seeds.",
        "",
        "New entities bek,dov,ral,sun are used in BOTH splits, because the old four entities' "
        "entity/value combinations were exhausted by earlier train+development. This is a "
        "procedural replication on a renamed task, not an identical-data reproduction. "
        "Train96 documents/24 canonical cores; dev24 fresh canonical combinations,8/category. "
        "Train uses two rotated values/entity; dev the other two, with shared answer "
        "vocabulary and both templates. Frozen overlap checks against original training/"
        "development and v1 development/known diagnostics found zero canonical overlap. "
        "This says nothing about uninspected held-out material.",
        "",
        "Original byte tokenizer, context32, ordinary14058/recurrent14416 parameters; "
        "float32 deterministic CPU, one thread.1536 AdamW steps/fit, batch8, same optimizer "
        "and city-shuffled dense8x64 work. Each document128 presentations,692224 valid "
        "targets and786432 padded positions/fit. First16 weights only the first answer "
        "token16; all suffix/EOS targets stay1. Weighted mass876544; uniform692224. "
        "No extra model forward for weighting. Final checkpoints only, no retries/resume.",
        "",
        "Greedy OwnedSession, cap8, PAD/BOS-only suppression, EOS2. Exact scorer requires "
        "unaltered native gold bytes followed by EOS; no trimming, insertion or repair. "
        "Value-body accuracy is a separate diagnostic. Every raw continuation, first-token "
        "vector, teacher loss, request cost, training trace and checkpoint is retained. "
        "New weights remain local/ignored and are not recoverable from Git metadata alone.",
        "",
        "[Protocol](local-answer-value-start-replication-v2-protocol.md). "
        "Final plan SHA256: `" + audit["plan_sha256"] + "`. "
        "Registration SHA256: `" + audit["registration_sha256"] + "`.",
        "",
        "The initial plan.json/source snapshots are preserved as a preflight draft. "
        "Typing annotations and metadata source bindings were corrected before the one "
        "rehearsal or any fit/answer; plan-final.json/sources-final bind the operative "
        "source. Data, seed matrix, schedules, objectives, gates and caps did not change. "
        "Draft lint/type failures and unmeasured editing cost are in draft-history.json. "
        "No sealed evidence was altered.",
        "",
        "## Per-cell accuracy against frozen gates",
        "",
        "Training eligibility requires ALL8 candidates exact96/EOS96/no first errors, "
        "malformed/repetition, plus ALL8 controls exact>=90/EOS96/zero malformed/repetition. "
        "Control mastery remains96 and is reported separately. If eligibility fails, "
        "both arms' development are NOT_RUN. Development candidate floors:>=22/24,city>=7,"
        "code>=7,unknown8,EOS24,zero malformed/repetition,known context gain>=8. Reliable "
        "improvement also requires STRICTLY positive exact gain in EACH8 matched pairs "
        "and no category/EOS regression. Aggregate gains cannot rescue a tie/regression.",
        "",
        "| Init | Shuffle | Model | Objective | Train /96 | Train city/code/unknown | Train EOS/malformed/repetition | Dev /24 | Dev city/code/unknown | Dev EOS/malformed/repetition | Context gain |",
        "| ---: | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: |",
    ]
    cost_rows = []
    raw_rows = []
    pair_rows = []
    for seed in plan["crossed_seeds"]:
        for model in ("ordinary", "recurrent"):
            for arm in ("uniform", "first16"):
                key = f"{seed}-{model}-{arm}"
                cell = audit["cells"][key]
                train = cell["training"]["metrics"]
                dev = cell.get("development", {}).get("metrics")
                cats = lambda m: "/".join(
                    str(m["categories"][k]) for k in ("city", "code", "unknown")
                )
                flags = lambda m: f"{m['eos']}/{m['malformed']}/{m['repetition']}"
                lines.append(
                    f"| {cell['initialization_seed']} | {cell['shuffle_seed']} | {model} | {arm} | {train['exact']} | {cats(train)} | {flags(train)} | {dev['exact'] if dev else 'NOT_RUN'} | {cats(dev) if dev else 'NOT_RUN'} | {flags(dev) if dev else 'NOT_RUN'} | {dev['known_context_gain'] if dev else 'NOT_RUN'} |"
                )
                cost = lambda c: f"{c['cpu']:.6f}/{c['wall']:.6f}"
                cost_rows.append(
                    f"| {key} | {cost(cell['fit_cost'])} | {cost(cell['evaluate_cost'])} | {cost(cell['development_cost']) if dev else 'NOT_RUN'} | {cell['fit_cost']['peak_private']} |"
                )
                base = f"../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/"
                raw_rows.append(
                    f"| {key} | [train]({base}evaluate-{key}/predictions-main.jsonl) | "
                    + (
                        f"[dev]({base}development-{key}/predictions-main.jsonl)"
                        if dev
                        else "NOT_RUN"
                    )
                    + f" | [checkpoint metadata]({base}fit-{key}/checkpoint-meta.json) |"
                )
                failures[key] = dict(
                    training=cell["training"]["wrong_first_examples"],
                    development=cell.get("development", {}).get("wrong_first_examples", []),
                )
            c, u = (audit["cells"][f"{seed}-{model}-{arm}"] for arm in ("first16", "uniform"))
            delta = c["training"]["metrics"]["exact"] - u["training"]["metrics"]["exact"]
            d = (
                c["development"]["metrics"]["exact"] - u["development"]["metrics"]["exact"]
                if audit["development_evaluated"]
                else "NOT_RUN"
            )
            pair_rows.append(f"| {seed} | {model} | {delta} | {d} |")
    lines += [
        "",
        "Global training eligibility: **" + str(audit["training_gate"]) + "**. "
        "Candidate mastery: **" + str(audit["candidate_training_mastery"]) + "**. "
        "Control eligibility: **" + str(audit["controls_eligibility"]) + "**. "
        "Development evaluated: **" + str(audit["development_evaluated"]) + "**.",
        "",
        "| Crossed seeds | Model | Training first16-minus-uniform exact | Development exact delta |",
        "| --- | --- | ---: | ---: |",
        *pair_rows,
        "",
        "Consistent objective improvement: **"
        + str(audit["consistent_objective_improvement"])
        + "**. "
        "A training-only effect does not establish fresh-combination accuracy. "
        "Missing development results are not scored as zero or inferred failures. "
        "Any development regressions/ties remain failed registered improvement gates.",
        "",
        "## Complete scoped costs and retained attempts",
        "",
        "Seconds below are complete kernel Job lifetimes, including controllers, "
        "descendants, cold imports/setup/checkpoint I/O, monitoring/sealing where "
        "enclosed, and exit. Parent totals already include nested worker totals.",
        "",
        "| Scope | CPU s | Wall s | Peak committed bytes | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name, cost in measured_scopes:
        lines.append(
            f"| {name} | {cost['cpu']:.6f} | {cost['wall']:.6f} | {cost['peak_private']} | {cost['status']} |"
        )
    lines += [
        "",
        "Non-overlapping measured scope sum: "
        f"CPU{sum(c['cpu'] for _, c in measured_scopes):.6f},"
        f"wall{sum(c['wall'] for _, c in measured_scopes):.6f} seconds. "
        "Audit and repository verification are separate from registered scientific cost; "
        "they perform zero model forwards. Initial v1 access checks/read-only precondition "
        "and preservation checks outside Jobs have unmeasured costs.",
        "",
        f"The single seed902407 random-data rehearsal used zero optimizer updates and "
        f"no study examples:CPU{rehearsal['cpu']:.6f},wall{rehearsal['wall']:.6f}; "
        f"selected common fit cap{rehearsal_result['selected_fit_cap']} before fitting. "
        "It is already inside preparation, excluded from scores and not added twice. "
        "All70-second fit/30-second observation/2-second request/1800-second CPU AND "
        "wall overall caps,2GiB commit,128MiB output and5-second monitoring-gap limits "
        "were verified. All jobs closed with0 active processes. No weak seed was retried.",
        "",
        f"Registered peak output{budget['peak_disk']} bytes,maximum gap{budget['max_monitor_gap']:.6f}s,"
        f"{budget['total_processes']} process lifetimes,{budget['terminated_processes']} forcibly terminated. "
        f"Registered outer observer CPU-to-receipt{budget['observer_cpu_to_receipt']:.6f}s is outside "
        "that Job and is NOT its complete lifetime. Source editing,preflight,registration "
        "and final reporting outside Jobs are unmeasured. No complete project cost or "
        "total-efficiency claim is available.",
        "",
        "| Cell | Cold fit CPU/wall | Training observation CPU/wall | Dev + question-only CPU/wall | Fit peak commit bytes |",
        "| --- | --- | --- | --- | ---: |",
        *cost_rows,
        "",
        "[Registered complete receipt](../../artifacts/local-answer-value-start-replication-v2/registered/budget/cost.json). "
        "Scientific sealed directories are immutable; audit/report outputs live outside them.",
        "",
        "## Raw evidence, independent integrity and checks",
        "",
        "| Cell | Raw training | Raw development | Checkpoint identity |",
        "| --- | --- | --- | --- |",
        *raw_rows,
        "",
        "[Independent audit](../../artifacts/local-answer-value-start-replication-v2/independent-audit.json) "
        "and [all failed first-token records](../../artifacts/local-answer-value-start-replication-v2/failure-index.json). "
        "The audit independently reconstructs every exact/value/EOS/format/repetition "
        "score,first-vector argmax/rank/probabilities/margins,teacher NLL,replay,all "
        f"{audit['optimizer_steps_verified']} optimizer steps,targets/exposures,initialization "
        f"and schedule independence,{audit['formal_scientific_stage_seals']} scientific stage seals, "
        "root/budget seals,kernel monitor closure,and v1 payload preservation. "
        "Its model-forward count is0. Original v1's negative decision and older "
        "paired-batch integrity failure remain unchanged.",
        "",
        "34 pre-fit contracts passed:24 native accounting/sealing tests and10 "
        "numerical/data/independent-seed/gate tests. No research update in those tests. "
        "Post-run repository lint/format,focused typing,frozen sources,dependency "
        "checks and git diff --check are recorded in verification/checks.json. "
        "Hosted CI:NOT_RUN. Full research smoke/verify.py:NOT_RUN, because it installs/"
        "trains/generates unrelated material. Native accounting is Windows-specific.",
        "",
        "Offline reproduction (no model forwards or generation):",
        "",
        "~~~powershell",
        ".\\.venv\\Scripts\\python.exe -I -S -B scripts/audit_value_start_replication_v2.py",
        ".\\.venv\\Scripts\\python.exe -B artifacts/local-answer-value-start-replication-v2/verify_report.py",
        "git diff --check",
        "~~~",
        "",
        "Do not rerun prepare/resources/register/launch or workers. The attempt is "
        "consumed; all partial/failure receipts and initial draft/type issues are retained.",
        "",
        "## Limitations and one next action",
        "",
        "Only2 initialization x2 shuffle seeds/model,one small synthetic grammar,shared "
        "finite answer vocabulary,new training entity names,and reused known initialization "
        "seeds. This development study estimates no held-out performance or population-wide "
        "reliability. Across-model widths and actual CPU differ. Any benefit shared by "
        "ordinary/recurrent is an objective effect in this design,not a recurrent-memory "
        "advantage. No delayed context,real conversation or total-efficiency test occurred.",
        "",
    ]
    if audit["consistent_objective_improvement"]:
        lines.append(
            "**Recommended next action:** register an independent fresh-development confirmation of the objective effect; defer memory and production claims."
        )
    else:
        lines.append(
            "**Recommended next action:** stop treating first-token x16 as a reliable default under this design; preserve the crossed negative/seed-sensitive result and do not launch a memory comparison."
        )
    analysis = ["## Objective effect, failures and seed sensitivity", ""]
    if audit["development_evaluated"]:
        totals = {}
        for arm in ("uniform", "first16"):
            records = [
                c["development"]["metrics"]
                for k, c in audit["cells"].items()
                if k.endswith("-" + arm)
            ]
            totals[arm] = {
                key: sum(r[key] for r in records)
                for key in ("exact", "eos", "malformed", "repetition")
            }
        analysis += [
            f"Aggregate exact:uniform{totals['uniform']['exact']}/192 versus "
            f"first16{totals['first16']['exact']}/192. These are repeated model/case observations "
            "on24 distinct development cases, not192 independent examples. "
            f"EOS totals uniform{totals['uniform']['eos']}/192 versus first16{totals['first16']['eos']}/192; "
            f"malformed counts{totals['uniform']['malformed']} versus{totals['first16']['malformed']}; "
            f"repetition counts{totals['uniform']['repetition']} versus{totals['first16']['repetition']}.",
            "",
            "| Model | Uniform exact /96 | First16 exact /96 | Gain |",
            "| --- | ---: | ---: | ---: |",
        ]
        for model in ("ordinary", "recurrent"):
            u, c = (
                sum(
                    cell["development"]["metrics"]["exact"]
                    for cell in audit["cells"].values()
                    if cell["model"] == model and cell["objective"] == arm
                )
                for arm in ("uniform", "first16")
            )
            analysis.append(f"| {model} | {u} | {c} | {c - u} |")
        analysis += [
            "",
            "| Factor | Level | Uniform exact /96 | First16 exact /96 | Gain |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for factor, levels in (("initialization_seed", (601, 947)), ("shuffle_seed", (1301, 1709))):
            for level in levels:
                u, c = (
                    sum(
                        cell["development"]["metrics"]["exact"]
                        for cell in audit["cells"].values()
                        if cell[factor] == level and cell["objective"] == arm
                    )
                    for arm in ("uniform", "first16")
                )
                analysis.append(f"| {factor} | {level} | {u} | {c} | {c - u} |")
        gains = list(audit["per_pair_dev_gains"].values())
        analysis += [
            "",
            f"Pairs: {sum(g > 0 for g in gains)} improved,{sum(g == 0 for g in gains)} tied,"
            f"{sum(g < 0 for g in gains)} regressed. Both models have positive aggregate "
            "objective gains, but the effect is not consistent across initialization/order. "
            "Ordinary601 regresses/ties while ordinary947 improves under both orders; "
            "recurrent947's gain differs across shuffle seeds. This is seed-sensitive "
            "evidence, not a uniformly reliable intervention. It does not identify the "
            "internal optimization mechanism or a benefit specifically caused by memory.",
            "",
            "First16 candidate failures (all raw native continuations retained):",
            "",
            "| Crossed cell | Case | Gold | Raw generated IDs | EOS | Gold rank | Gold-minus-top |",
            "| --- | --- | --- | --- | --- | ---: | ---: |",
        ]
        for key, cell in audit["cells"].items():
            if cell["objective"] != "first16":
                continue
            for case in cell["development"]["wrong_first_examples"]:
                analysis.append(
                    f"| {key} | {case['id']} | {case['gold']} | `{case['generated_ids']}` | {case['generated_ids'][-1] == 2} | {case['gold_rank']} | {case['gold_minus_top']:.6f} |"
                )
        analysis += [
            "",
            "Both recurrent601 candidates fail city>=7 (5/8 each) and format gates; "
            "shuffle1301 also has an EOS failure. Ordinary601/shuffle1301 loses one "
            "previously correct city answer. No repetition is recorded under the fixed "
            "one/two-ID-block definition. All candidate exact errors begin at the first "
            "answer byte; one also fails termination. Higher aggregate accuracy cannot "
            "override these failures or the two tied pairs.",
            "",
        ]
    else:
        analysis += [
            "The training gate closed development. No development benefit/regression or "
            "reliability estimate is inferred from missing observations.",
            "",
        ]
    position = lines.index("## Complete scoped costs and retained attempts")
    lines[position:position] = analysis
    lines += [
        "",
        "All new work remains uncommitted. Historical sources,reports,seals and local "
        "checkpoints were preserved. No production chat,commit,push or deployment.",
        "",
    ]
    with (BASE / "failure-index.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(failures, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    path = ROOT / "docs/research/local-answer-value-start-replication-v2-results.md"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines))
    print(json.dumps(dict(report=str(path), cells=16, decision=audit["decision"])))


if __name__ == "__main__":
    main()
