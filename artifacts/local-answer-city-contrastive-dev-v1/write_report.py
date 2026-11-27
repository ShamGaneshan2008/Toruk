"""Render only saved independent audit records; never import a model or alter science."""

import json
from pathlib import Path

RUN = Path(__file__).resolve().parent
EXEC = RUN / "registered/execution"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    audit = read(RUN / "independent-audit.json")
    plan = read(RUN / "plan-final.json")
    lines = [
        "# City contrastive loss development v1 — measured result", "",
        f"Scientific gate: **{'PASS' if audit['decision'] == 'DEVELOPMENT_GATES_PASS' else 'FAIL'}**. "
        f"Decision: **{audit['decision']}**. Measurement integrity: **{audit['measurement_integrity']}**.",
        "", "One controlled objective intervention: first16 CE plus 0.1 times the mean city "
        "confuser softplus with margin 2. Control: unchanged v2 first16 CE. Two initialization "
        "seeds (601/947) cross two independent shuffle seeds (1301/1709), ordinary/recurrent, "
        "control/contrast. No historical checkpoint is used as a training initialization.", "",
        "The 96 training documents and 24 development cases are byte-identical to v2. "
        "These development cases were already diagnosed; results are adaptive development "
        "evidence, not independent generalization. Held-out data remains unopened. "
        "Production chat and pretrained backbones are unchanged. No memory or efficiency "
        "advantage is claimed.", "", "## Frozen identities and execution", "",
        f"Starting Git HEAD: `{plan['source_commit']}`. The working tree already contained "
        "the entity-dropout study, resume-integrity adapter and completed v2 diagnosis. "
        "Existing edits, frozen sources, raw evidence and ignored weights were preserved. "
        "No pull, reset, commit, push, release or deployment.", "",
        "Protocol/source/data/gates/caps froze before preparation. The single random rehearsal "
        "used seed 927113, no study examples and zero optimizer updates. Registration binds "
        "its seal and the 34 passing contract/measurement tests. Every registered scientific "
        "cell was attempted at most once; no cap, coefficient, seed or gate was changed.", "",
        f"Independent auditor verified {audit.get('optimizer_steps_verified', 'incomplete')} "
        f"recorded updates and {audit.get('scientific_seals', 'incomplete')} scientific stage seals. "
        "It reconstructs native outcomes, vectors, teacher losses, training/auxiliary arithmetic, "
        "controls, schedule exposure, token accounting, complete Job costs and the final gates "
        "without importing Torch or the training runner.", "",
        "## Per-cell scores", "",
        "Each tuple is exact / EOS / malformed / wrong-first / repetition. Training denominator "
        "is 96; development denominator is 24. NOT_RUN means not evaluated, never zero accuracy.", "",
        "| Initialization/shuffle | Model | Arm | Training | Development | Dev city/code/unknown |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    table = {}
    for seed, model, arm in plan["order"]:
        key = f"{seed}-{model}-{arm}"
        cell = audit.get("cells", {}).get(key, {})
        values = {}
        metrics = {}
        for split in ("train", "dev"):
            value = cell.get(split, {}).get("metrics")
            metrics[split] = value
            values[split] = "/".join(str(value[k]) for k in
                ("exact", "eos", "malformed", "wrong_first", "repetition")) if value else "NOT_RUN"
        cats = "/".join(str(metrics["dev"]["categories"][k]) for k in
                        ("city", "code", "unknown")) if metrics["dev"] else "NOT_RUN"
        lines.append(f"| {seed} | {model} | {arm} | {values['train']} | {values['dev']} | {cats} |")
        table[key] = metrics
    lines += ["", "## Matched development gates", "",
              "| Cell | Exact gain | Newly wrong cases | Fixed cases | Pair gate | Candidate floor |",
              "| --- | ---: | --- | --- | --- | --- |"]
    for key, p in audit.get("pairs", {}).items():
        lines.append(f"| {key} | {p['gain']:+d} | {', '.join(p['introduced']) or 'none'} | "
                     f"{', '.join(p['fixed']) or 'none'} | {p['pass_pair']} | "
                     f"{audit['floors'][key+'-contrast']} |")
    if not audit.get("pairs"):
        lines += ["", "Development comparison NOT_RUN because prerequisites did not pass."]
    lines += ["", "Every previously correct control case must remain correct; every non-ceiling "
              "control must improve. A perfect-control tie supplies no improvement evidence. "
              "Every candidate must pass exact/category/EOS/format/context-gain floors, both "
              "models need positive total gain, and recurrent601 city first NLL must decrease "
              "under both shuffles. Aggregates cannot override a failed conjunct.", ""]
    for seed, value in audit.get("city_first_nll", {}).items():
        lines.append(f"Recurrent city first NLL {seed}: control {value['control']:.9f}, "
                     f"contrast {value['contrast']:.9f}; gate {value['improved']}.")
    lines += ["", "## Complete scoped costs", "",
              "Parent Job totals already include nested stages; never add them twice. "
              "These costs include controllers, cold imports, I/O, descendants, observations "
              "and enclosed sealing. Outer observers, editing, registration and reporting "
              "outside measured Jobs have unknown full-lifetime cost; no complete-project "
              "efficiency claim follows.", "",
              "| Scope | CPU seconds | Wall seconds | Peak committed bytes | Status |",
              "| --- | ---: | ---: | ---: | --- |"]
    for name in ("preparation/budget", "registered/budget"):
        c = audit.get("costs", {}).get(name)
        if c:
            lines.append(f"| {name} | {c['cpu']:.6f} | {c['wall']:.6f} | {c['peak_private']} | {c['status']} |")
    lines += ["", "| Cell | Fit CPU/wall seconds | Train observation CPU/wall | Dev CPU/wall |",
              "| --- | --- | --- | --- |"]
    for seed, model, arm in plan["order"]:
        key = f"{seed}-{model}-{arm}"
        def cost(kind):
            c = audit.get("costs", {}).get(kind+"-"+key)
            return f"{c['cpu']:.6f}/{c['wall']:.6f}" if c else "NOT_RUN"
        lines.append(f"| {key} | {cost('fit')} | {cost('evaluate')} | {cost('development')} |")
    lines += ["", "All completed fits use 692,224 valid byte/EOS targets, 786,432 padded "
              "positions and CE weighted mass 876,544. Each logs 4,096 city contrastive "
              "contributions, including control diagnostics. Each observation's `token-costs.json` "
              "retains request counts, tokens and forward positions; raw predictions, vectors "
              "and teacher rows retain per-request CPU/wall costs and replay records.", "",
              "## Remaining candidate mistakes", "",
              "| Cell | Case | Expected | Actual | EOS | Malformed | Wrong first |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    failures = []
    for key, cell in audit.get("cells", {}).items():
        if not key.endswith("-contrast"):
            continue
        for split, phase in (("dev", "development"), ("train", "evaluate")):
            obs = cell.get(split)
            if not obs:
                continue
            raw = {r["id"]: r for r in [json.loads(s) for s in
                (EXEC/"stages"/f"{phase}-{key}/predictions-main.jsonl").read_text().splitlines()]
                   if not r["replay"]}
            for case in obs["metrics"]["cases"]:
                if case["exact"]:
                    continue
                pred = raw[case["id"]]["result"]
                failures.append(dict(cell=key, split=split, case=case, result=pred))
                lines.append(f"| {key} ({split}) | {case['id']} | `{json.dumps(case['gold'])}` | "
                    f"`{json.dumps(pred['answer'])}` | {case['eos']} | {case['malformed']} | {case['wrong_first']} |")
    if not failures:
        lines += ["", "No candidate mistakes among independently audited completed observations."]
    lines += ["", "## Evidence and limitations", "",
              "Frozen design: `plan-final.json`, `registration.json`, `sources/`, protocol and "
              "copied inputs. Execution: `registered/execution/stages/` contains every checkpoint, "
              "training trace, native answer, vector, teacher loss, token ledger, failure and "
              "observer seal. `independent-audit.json` is saved-only verification; "
              "`verification/` retains actual repository check commands/results.", "",
              "This is one intervention, two initialization and two shuffle seeds, one small "
              "grammar and a reused development set. Model widths differ; this is not an "
              "isolated memory-mechanism or equal-FLOPs comparison. Passing software checks "
              "does not establish improved accuracy, reliable transfer or efficiency.", "",
              "Recommended next action: " + (
                  "register a fresh independent local-answer generalization study before any memory comparison."
                  if audit["decision"] == "DEVELOPMENT_GATES_PASS" else
                  "preserve this failed attempt and perform a saved-only diagnosis of its remaining or introduced errors before considering another intervention."), ""]
    with (RUN/"case-failures.json").open("x",encoding="utf-8") as stream:
        json.dump(failures,stream,indent=2);stream.write("\n")
    with (RUN/"results.md").open("x",encoding="utf-8",newline="\n") as stream:
        stream.write("\n".join(lines))


if __name__ == "__main__":
    main()
