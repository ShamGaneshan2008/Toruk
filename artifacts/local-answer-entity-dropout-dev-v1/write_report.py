"""Render saved-only diagnosis/study/audit records; no model work."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent


def read(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def main():
    diagnosis = read("saved-v2-diagnosis.json")
    result = read("independent-audit.json")
    summary = read("registered/execution/summary.json")
    preparation = read("preparation/budget/cost.json")
    registered = read("registered/budget/cost.json")
    receipt = read("registered-budget-receipt.json")
    out = [
        "# Local-answer entity dropout dev v1 — results",
        "",
        "26 November 2026. Development only. Decision: **" + result["decision"] + "**.",
        "Measurement integrity: **" + result["status"] + "**. No memory/architecture advantage is inferred.",
        "",
        "## Starting state and preservation",
        "",
        "Git root D:/Toruk, branch main, HEAD and origin/main both "
        "`916efdd4b63dd63fab08ffabb8ab6e8313dc4bf2`, initially clean. No pull/reset/commit/push. "
        "All historical studies and ignored weights preserved; the old inaccessible preparation "
        "fixture was left untouched. Independent v2 audit passes with its STOP_DEVELOPMENT_FAILURE "
        "unchanged. The new audit checks all " + str(result["protected_v2_files"]) + " reviewed v2 payloads.",
        "",
        "## Saved-output diagnosis reproduced before model work",
        "",
        "[Raw 34-failure table](../../artifacts/local-answer-entity-dropout-dev-v1/saved-v2-failures.md), "
        "[complete saved diagnosis](../../artifacts/local-answer-entity-dropout-dev-v1/saved-v2-diagnosis.json). "
        "The original independent v2 auditor reconstructed all 48 stage seals, 24576 recorded "
        "updates, native prompts/scores and logit preferences without a model forward.",
        "",
        "All16 original cells mastered training96/96. Across development, uniform had26 errors "
        "and first16 had8. All34 begin with a wrong first byte, gold rank>1 and negative "
        "gold-minus-top margin.22 return an entity's training value. Five are malformed;one "
        "also fails EOS. None repeats by the registered criterion. Templates A/B account for21/13 "
        "errors out of equal-sized template groups; templates and canonical case difficulty are "
        "confounded, so this is not an isolated template effect. Three errors share the "
        "question-only first byte; source use is partial,not absent. Required facts are present "
        "in every failed prompt. No correct complete answer was rejected. Every saved argmax "
        "matches the generator's first token; inference/scoring/measurement defects were not found.",
        "",
        "V2 reliability failures: ordinary i601-s1301 regressed24->23;ordinary i601-s1709 "
        "tied24;recurrent i947-s1301 tied23. Recurrent i601-s1301 and i601-s1709 first16 each "
        "scored21/24 with city5/8 and malformed output;the former also had EOS23/24. "
        "Candidate failures are v2-dev-012 (ral city=la) in four cells;v2-dev-013 (city ral=mi) "
        "in both recurrent601 cells;v2-dev-018 (sun city=mi) in both recurrent601 cells. "
        "The first-byte preferences explain emitted choices,not how optimization created them. "
        "Entity/value shortcuts are a testable hypothesis rather than a verified mechanism.",
        "",
        "| V2 cell | Exact /24 | City/code/unknown | Wrong first | EOS | Malformed |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for key, m in diagnosis["cells"].items():
        out.append(f"| {key} | {m['exact']} | " + "/".join(str(m["categories"][c]) for c in ("city", "code", "unknown"))
                   + f" | {m['wrong_first']} | {m['eos']} | {m['malformed']} |")
    out += ["", "## Frozen intervention and control", "",
            "[Protocol](local-answer-entity-dropout-dev-v1-protocol.md); "
            "[registration](../../artifacts/local-answer-entity-dropout-dev-v1/registration.json); "
            "[plan](../../artifacts/local-answer-entity-dropout-dev-v1/plan.json). "
            "Plan SHA256 `" + read_sha("plan.json") + "`;registration SHA256 `" + read_sha("registration.json") + "`.",
            "",
            "One training-only intervention: both entity mentions become three-byte `ref` in "
            "64/128 presentations/document, with exact deterministic parity scheduling;the other64 "
            "retain original names. Uniform CE in both arms. Identical initialization601/947 crossed "
            "with shuffle1301/1709,models,1536 steps,batch8,optimizer,city schedule,byte lengths and "
            "token work. Fresh uniform controls must reproduce v2 final tensor hashes and every "
            "native train/dev continuation. Candidate dropout never changes development prompts. "
            "The train/dev canonical overlap remains0 even after adding anonymous training views. "
            "Development reuses the24 diagnosed v2 cases:adaptive exploratory evidence,not a new "
            "validation sample. Historical first16 was not selected as the primary control.",
            "",
            "Caps were frozen before model work:fit90s,observation40s,request2s,registered1800 CPU "
            "AND wall seconds,2GiB commit,128MiB output,max gap5s. All32 prerequisite contracts passed. "
            "The single seed918733 random rehearsal made0 updates,used0 study examples,and projected "
            "68s for both models. No cap increased,no fit retried. Source and protocol bytes were "
            "frozen before rehearsal;pre-fit formatting/type issues were corrected before the freeze "
            "(long lines/import order and two missing/inferred annotations).",
            "",
            "The training gate requires all16 original-input training scores96/96,full EOS and zero "
            "malformed/repetition/wrong-first. Development can open only after that. Candidate floors "
            "are>=22/24,city>=7,code>=7,unknown8,EOS24,zero malformed/repetition,context gain>=8. "
            "No paired exact/category/EOS regression;every non-ceiling control must improve,positive "
            "model totals,and recurrent601 city first NLL must improve under both shuffles. "
            "Ceiling ties are permitted prospectively;they are not improvement evidence. V2's original "
            "strict-positive-all8 gate stays failed.",
            "", "## Registered per-cell results", "",
            "| Init/shuffle/model | Arm | Train /96 | Train EOS/malformed/repetition | Dev /24 | Dev city/code/unknown | Dev EOS/malformed/repetition | Train full/answer/first NLL |",
            "| --- | --- | ---: | --- | ---: | --- | --- | --- |"]
    for key, cell in result["cells"].items():
        t, d = cell["train"], cell.get("dev")
        arm = key.rsplit("-", 1)[1]
        dev = str(d["exact"]) if d else "NOT_RUN"
        categories = "/".join(str(d["categories"][c]) for c in ("city", "code", "unknown")) if d else "—"
        formats = f"{d['eos']}/{d['malformed']}/{d['repetition']}" if d else "—"
        out.append(f"| {key.rsplit('-',1)[0]} | {arm} | {t['exact']} | "
                   f"{t['eos']}/{t['malformed']}/{t['repetition']} | {dev} | {categories} | {formats} | "
                   + "/".join(f"{t[k]:.6f}" for k in ("full_nll", "answer_nll", "first_nll")) + " |")
    out += ["", "Training gate: **" + str(result["training_gate"]) + "**. Development evaluated: **"
            + str(result["development_evaluated"]) + "**. Decision: **" + result["decision"] + "**.",
            "", "[Independent audit](../../artifacts/local-answer-entity-dropout-dev-v1/independent-audit.json) "
            "contains every failed case,raw continuation,pair gate,candidate floor and cost. "
            "[Sealed execution summary](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/summary.json).",
            "", "| Pair | Exact delta | Pair gate |", "| --- | ---: | --- |"]
    for key, gain in result["pair_gains"].items():
        out.append(f"| {key} | {gain} | {result['pair_gates'][key]} |")
    if result["development_evaluated"]:
        out += ["", "| Recurrent601 city first-token NLL | Uniform | Dropout | Mechanism gate |",
                "| --- | ---: | ---: | --- |"]
        for seed, values in summary["comparison"]["recurrent601_city_first_nll"].items():
            out.append(f"| {seed} | {values['uniform']:.6f} | {values['drop50']:.6f} | {values['improved']} |")
        regressions = [key for key, gain in result["pair_gains"].items() if gain < 0]
        out += ["", "Exact regressions: " + (", ".join(regressions) if regressions else "none") + ". "
                "Candidate floors: " + json.dumps(result["candidate_floors"], sort_keys=True) + ". "
                "Pair gates also test category/EOS regressions;the independent audit retains each gate."]
    out += ["", "Measured preferences and the training-origin hypothesis remain distinct. "
            "Any gain is consistent with this data intervention,not proof of an internal entity-copy "
            "mechanism. A failed registered gate rejects the intervention as a reliable fix in this "
            "design;neither pooled accuracy nor one favorable seed overrides it."]
    out += ["", "## Costs and raw evidence", "",
            "Nested stage costs below are included in the registered budget;do not add them again. "
            "All are complete Windows Job lifetimes including cold imports,I/O,controllers and "
            "descendants. Preparation and registered totals do not overlap. Outermost observer, "
            "editing,registration,saved diagnosis outside a Job and report-writing lifetime costs "
            "are unknown. No complete project-cost or total-efficiency claim.",
            "",
            f"Preparation CPU/wall: {preparation['cpu']:.6f}/{preparation['wall']:.6f}s. "
            f"Registered CPU/wall: **{registered['cpu']:.6f}/{registered['wall']:.6f}s**. "
            f"Registered peak commit {registered['peak_private']} bytes,peak disk {registered['peak_disk']} bytes, "
            f"max monitor gap {registered['max_monitor_gap']:.6f}s,active processes {registered['active_processes']}. "
            "Budget seal SHA256 `" + receipt["sha256"] + "`.",
            "", "| Cell | Fit CPU/wall s | Train observation CPU/wall s | Dev CPU/wall s | Targets / padded positions | Generated train/dev tokens including replays |",
            "| --- | --- | --- | --- | --- | --- |"]
    for key, cell in result["cells"].items():
        costs = result["costs"]
        fit = costs[f"registered/execution/stages/fit-{key}"]
        train = costs[f"registered/execution/stages/evaluate-{key}"]
        dev = costs.get(f"registered/execution/stages/development-{key}")
        dcost = f"{dev['cpu']:.6f}/{dev['wall']:.6f}" if dev else "NOT_RUN"
        train_tokens = cell["train_token_costs"]["main"]["generated_tokens"]
        dev_tokens = sum(cell["dev_token_costs"][mode]["generated_tokens"] for mode in ("main", "question-only")) if dev else "NOT_RUN"
        out.append(f"| {key} | {fit['cpu']:.6f}/{fit['wall']:.6f} | {train['cpu']:.6f}/{train['wall']:.6f} | "
                   f"{dcost} | 692224 / 786432 | {train_tokens}/{dev_tokens} |")
    out += ["", "Each stage's `token-costs.json` retains input/generated/teacher target/forward "
            "counts and request CPU/wall,including replays. Every raw native continuation,first "
            "logit vector,teacher loss,training step,checkpoint and monitor is retained. Checkpoints "
            "are ignored local inputs,with exact metadata hashes;no replacement weights were created.",
            "", "| Cell | Training raw | Development raw | Fit metadata |",
            "| --- | --- | --- | --- |"]
    base = "../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages"
    for key, cell in result["cells"].items():
        dev = f"[raw]({base}/development-{key}/predictions-main.jsonl)" if cell.get("dev") else "NOT_RUN"
        out.append(f"| {key} | [raw]({base}/evaluate-{key}/predictions-main.jsonl) | {dev} | "
                   f"[metadata]({base}/fit-{key}/checkpoint-meta.json) |")
    out += ["", "## Verification and limits", "",
            "Independent audit rechecks original v2 integrity,all new nested/root seals,all native "
            "scores and first-token ranks/margins,uniform loss partitions,1536 schedules/fit,64/64 "
            "dropout exposures,checkpoint/source bytes,control tensor/prediction parity and complete "
            "closed accounting. Its model-forward count is0. Relevant repository checks are in "
            "[verification receipts](../../artifacts/local-answer-entity-dropout-dev-v1/verification-checks.json). "
            "Hosted CI NOT_RUN;no push authorized. This is one small synthetic grammar,two initialization "
            "and two order seeds,finite shared values,and reused diagnostic development cases. "
            "No long-history,memory or chatbot advantage follows.",
            "", "Offline checks (no research launcher rerun):", "", "```powershell",
            ".venv/Scripts/python.exe -B scripts/audit_entity_dropout_dev.py",
            ".venv/Scripts/python.exe -m pytest -q tests/test_entity_dropout_dev.py tests/test_value_start_replication_v2.py tests/test_lifetime_job.py tests/test_lifetime_job_v2.py",
            ".venv/Scripts/python.exe -m ruff check .",
            ".venv/Scripts/python.exe -m ruff format --check src tests scripts",
            ".venv/Scripts/python.exe -m mypy",
            ".venv/Scripts/python.exe -m mypy --platform linux",
            "git diff --check", "```", "",
            "Do not rerun prepare/resources/register/launch:the attempt is consumed and all paths "
            "are exclusive. Changes remain uncommitted for review.", ""]
    out += ["Recommended next action: " + (
        "register an independent fresh-development replication before adopting entity dropout."
        if result["decision"] == "DEVELOPMENT_GATES_PASS" else
        "reject entity dropout as a reliable fix under this budget and preserve the failed gate;do not extend or retry this run."), ""]
    path = ROOT / "docs/research/local-answer-entity-dropout-dev-v1-results.md"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(out))
    print(path)


def read_sha(name):
    import hashlib
    return hashlib.sha256((RUN / name).read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
