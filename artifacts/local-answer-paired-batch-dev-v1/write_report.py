"""Write the post-run report once from saved evidence. Never execute a model."""
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()]

def write(path, raw):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(raw)

def main():
    audit = read(RUN / "independent-audit.json")
    plan = read(RUN / "plan.json")
    summary = read(RUN / "summary.json")
    costs = audit["complete_execution_cost"]
    checkcost = read(RUN / "verification/execution/cost.json")
    rehearsal = read(RUN / "preparation/rehearsal/rehearsal.json")
    replay = {}
    for seed in (601, 947):
        for model in ("ordinary", "recurrent"):
            old = ROOT / "artifacts/local-answer-dev-v1/stages" / f"generate-train-{seed}-{model}"
            new = RUN / "stages" / f"analyze-{seed}-{model}-original"
            oldraw = (old / "predictions.jsonl").read_bytes()
            assert hashlib.sha256(oldraw).hexdigest() == read(old / "seal.json")["sha256"]
            a, b = rows(old / "predictions.jsonl"), rows(new / "predictions-main.jsonl")
            assert len(a) == len(b) == 97
            matches = sum(x["id"] == y["id"] and
                          x["result"]["generated_ids"] == y["result"]["generated_ids"]
                          for x, y in zip(a[:-1], b[:-1], strict=True))
            assert matches == 96
            replay[f"{seed}-{model}"] = dict(matches=matches, count=96,
                                           old_training_predictions_sha256=hashlib.sha256(oldraw).hexdigest(),
                                           new_training_predictions_sha256=hashlib.sha256((new / "predictions-main.jsonl").read_bytes()).hexdigest())
    write(RUN / "original-saved-replay-comparison.json", json.dumps(
        dict(status="PASS", original_training_answers_reproduced=384, cells=replay,
             new_inference=False, compared_saved_native_ids_only=True), indent=2) + "\n")
    lines = [
        "# Paired city batching development v1: negative training result",
        "",
        "23 November 2026. **Pairing fails the registered sufficient-repair/no-regression",
        "criterion. Development was NOT RUN. The frozen registered offline auditor also",
        "FAILS because worker observation seals included still-growing monitor logs.**",
        "Those failures and all original seals are retained; no fit or inference was retried.",
        "",
        "Saved observations: ordinary947 scores80/96 under the original schedule,",
        "92/96 with city-only shuffled batches, and90/96 with same-entity paired batches.",
        "Pairing corrects all16 original failures but introduces six new first-token",
        "errors; city shuffling introduces four. This gives no pairing-specific benefit",
        "over the matched timing control and no memory or generalization advantage.",
        "",
        "## Scope and preregistration",
        "",
        "Git root D:/Toruk; initial branch main; HEAD",
        "aadc77d2589088e5386ccdc9a7a5c5784c89ca04. Initial tree clean.",
        "This study does not fetch, commit, push, install packages or alter production chat.",
        "The completed checkpoint handoff and consumed frozen evidence remain unchanged.",
        "",
        "Narrow hypothesis: concentrating contrasting city-copy examples within a batch",
        "may improve first-token discrimination. The old260-record probe established",
        "checkpoint preferences/parity, not the training cause. The earlier two-fit",
        "ordinary947 proposal remains unchanged. This separately versioned",
        "[protocol](local-answer-paired-batch-dev-v1-protocol.md) prospectively expands",
        "to seeds601/947, both models, the required original schedule, and an additional",
        "city-shuffled control that holds city timing constant when isolating pairing.",
        "",
        "[Frozen plan](../../artifacts/local-answer-paired-batch-dev-v1/plan.json)",
        "SHA-256: " + audit["plan_sha256"] + ".",
        "[Fit registration](../../artifacts/local-answer-paired-batch-dev-v1/registration.json)",
        "SHA-256: " + audit["registration_sha256"] + ".",
        "Plan/data/schedules/source hashes were frozen before the single rehearsal;",
        "registration additionally binds its successful receipts before any study update.",
        "",
        "All12 fits use the original96 training examples and fixed1536 AdamW steps,",
        "batch8,128 epochs,692224 scored targets and12288 presentations per fit.",
        "Ordinary has14058 parameters; recurrent14416. Each arm shares the original",
        "initial tensor hash within model/seed. Uniform CE, tokenizer, decoding and scorer",
        "are fixed; there is no weighting, added data, warmup, seed selection or extension.",
        "",
        "All arms right-pad training targets to64, giving786432 dense positions per fit.",
        "Disposable contracts verify equivalent valid losses/gradients against dynamic",
        "padding. The original batching order is exact, but common fixed padding means",
        "this was not promised as bitwise weight reproduction. Saved comparison now",
        "confirms all384 original-schedule native training answers match the old saved",
        "answers across the four model/seed cells; no old inference was repeated.",
        "See [comparison](../../artifacts/local-answer-paired-batch-dev-v1/original-saved-replay-comparison.json).",
        "Equal shapes/targets are not a claim of equal measured time or cross-model compute.",
        "",
        "## Paired versus original and matched control",
        "",
        "Each entry below is training exact/96; city first-token errors/32.",
        "",
        "| Seed | Model | Original | City shuffled | City paired | Development |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for seed in (601, 947):
        for model in ("ordinary", "recurrent"):
            values = []
            for arm in ("original", "city-shuffled", "city-paired"):
                m = audit["cells"][f"{seed}-{model}-{arm}"]["metrics"]
                values.append(f"{m['exact']}/96; {m['city_first_errors']}/32")
            lines.append(f"| {seed} | {model} | " + " | ".join(values) + " | NOT_RUN |")
    lines += [
        "",
        "EOS is96/96 in every cell. No repetitive output is observed. Original947",
        "ordinary retains four malformed 'lo' answers; all other cells have zero",
        "malformed outputs. Code/unknown answers remain32/32 in every cell.",
        "Nine cells master training; the three ordinary947 cells do not.",
        "",
        "Training mastery was predeclared as96/96 exact,96/96 EOS,zero malformed/",
        "repetitive outputs,32/32 city first IDs and no winner margin<=1e-4 in EVERY",
        "registered cell. It fails without changing any schedule, cap or gate.",
        "The as-run summary is STOP_TRAINING_FAILURE. No development generation,",
        "development loss or question-only stage was launched. The registered24-case",
        "fresh-combination development split is frozen but its generalization is unmeasured.",
        "",
        "Pairing fixes all16 original ordinary947 errors, including all eight missing-m",
        "selections, but regresses train-052..055 (zim city=tu, expected t becomes s)",
        "and train-072..073 (nax city=tu, expected t becomes l). City shuffling fixes",
        "the same16 but regresses only052..055. Thus paired gains10 exact over original",
        "but loses2 against the matched control; it does not preserve all80 original",
        "correct answers. No seed was selected or dropped after observing results.",
        "",
        "| Paired ordinary947 case | Expected / predicted byte | Gold rank | Gold-minus-top |",
        "| --- | --- | ---: | ---: |",
    ]
    for r in audit["cells"]["947-ordinary-city-paired"]["wrong_first"]:
        lines.append(f"| {r['id']} | {chr(r['expected_first_id']-3)} / {chr(r['predicted_first_id']-3)} | "
                     f"{r['expected_rank']} | {r['expected_minus_predicted_margin']:.9f} |")
    lines += [
        "",
        "The signed losing margins are well outside1e-4. All32 city vectors per cell",
        "are retained, not just these failures. The six paired errors are rank2",
        "preferences on locally supplied facts, not missing-input or EOS failures.",
        "Against the original arm, field timing and within-city composition both change;",
        "the matched shuffled arm prevents attributing the original-arm improvement",
        "specifically to pairing. This rejects sufficient repair under this design/budget,",
        "not every possible batching intervention. Initialization/shuffle/optimization",
        "mechanisms and broader generalization remain unresolved.",
        "",
        "## Complete cost and rehearsal",
        "",
        "Eighteen focused contracts passed, including exact exposure/pair construction,",
        "padding loss/gradient equivalence, strict gates, original initial hashes,",
        "and real success/failure/interrupt/abrupt/descendant/cap-stop process tests.",
        "The one seed900301 numeric rehearsal uses different random tokens, three",
        "forward/backward passes per model, zero optimizer updates and unchanged weights.",
        f"Both projected cold fits are58 seconds; projected aggregate is{rehearsal['projected_total_seconds']:.0f}",
        "seconds. Fixed fit cap60 and aggregate1500 CPU AND wall seconds passed.",
        "All scientific fit/analysis stages close successfully; no resource retry occurred.",
        "",
        "| Seed | Model | Arm | Cold fit CPU / wall s | Analysis CPU / wall s |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for key, c in sorted(audit["cells"].items()):
        lines.append(f"| {c['seed']} | {c['model']} | {c['arm']} | "
                     f"{c['complete_fit_cpu']:.6f} / {c['complete_fit_wall']:.6f} | "
                     f"{c['complete_analysis_cpu']:.6f} / {c['complete_analysis_wall']:.6f} |")
    lines += [
        "",
        "[Complete execution Job](../../artifacts/local-answer-paired-batch-dev-v1/execution/cost.json):",
        f"{costs['cpu']:.6f} CPU seconds = {costs['user_cpu']:.6f} user + {costs['kernel_cpu']:.6f} kernel;",
        f"{costs['wall']:.6f} wall seconds;0 active/{costs['total_processes']} total processes;",
        f"peak Job commit{costs['peak_private']} bytes; peak logical disk{costs['peak_disk']} bytes;",
        f"max monitor gap{costs['max_monitor_gap']:.9f}s. All absolute resource caps pass.",
        f"The residual beyond fit/analysis child Jobs is{audit['cpu_residual_including_preparation_and_controllers']:.6f}",
        "CPU seconds, including preparation, controllers and in-Job observers.",
        "Nested costs are subsets and are never added to the enclosing cost.",
        f"Outer observer CPU-to-receipt{costs['observer_cpu_to_receipt']:.6f}s is outside the Job;",
        "it is not a complete observer lifetime or project-wide cost.",
        "",
        f"Separate offline-check Job:{checkcost['cpu']:.6f} CPU/{checkcost['wall']:.6f} wall seconds,",
        "zero new model forwards/answers. Editing, source freeze and later reporting",
        "outside these Jobs have unmeasured costs. There is no total-efficiency claim.",
        "",
        "## Integrity defect and independent verification",
        "",
        "**Registered integrity is NOT PASS.** The frozen runner's audit fails with",
        "'observation seal'. Its observation-seal.json included resources.jsonl while",
        "the parent observer was still appending until worker exit. This occurs in all12",
        "analysis stages. The original runner, sources, seals, logs and failure remain",
        "unchanged; no stale hash was replaced and no scientific stage was rerun.",
        "",
        "The separate [saved verifier](../../artifacts/local-answer-paired-batch-dev-v1/verify_saved.py)",
        "and [audit](../../artifacts/local-answer-paired-batch-dev-v1/independent-audit.json)",
        "find each stale monitor hash matches an EXACT complete-line prefix of the final",
        "journal. All72 other sealed payload bindings match final bytes. Independent",
        "native-ID rescoring reproduces1152 scored answers,12 replays and384 city",
        "vectors/ranks/margins. All12 checkpoint byte hashes, traces, target/exposure",
        "counts, initialization identities and final kernel costs verify. This supports",
        "reporting saved negative observations, while retaining the failed registered",
        "integrity gate. The supplemental verifier deliberately exits2, not0.",
        "",
        f"All{audit['preserved_files']} protected old-evidence/handoff files retain their sizes/SHA-256.",
        "The old handoff ZIP remains b6e336cb004f3334a244101b6d3a102ccee3da6e3106fa447c565b2e6d731300.",
        "Its standalone verifier passes. The older unrelated portable-evidence verifier",
        "still fails on historical .gitattributes drift; that manifest was not changed.",
        "",
        "[Checks](../../artifacts/local-answer-paired-batch-dev-v1/checks.json) retain command",
        "logs for the original audit failure, supplemental exit2, older portable failure,",
        "passing old first-token audit/report, frozen sources, repository Ruff lint/format,",
        "dependency consistency and staged/unstaged git diff --check. No full model",
        "suite or additional smoke/generation job was run after registered execution.",
        "",
        "Repeat only the offline verifier (exit2 is expected and reports the seal defect):",
        "",
        "~~~powershell",
        "Set-Location D:\\Toruk",
        ".\\.venv\\Scripts\\python.exe -I -S -B artifacts/local-answer-paired-batch-dev-v1/verify_saved.py",
        "git diff --check",
        "git status -sb",
        "~~~",
        "",
        "Do not repeat prepare/launch/execute/worker or overwrite the consumed registration.",
        "New work remains uncommitted; all12 new .pt checkpoints remain Git-ignored/local.",
        "Held-out datasets and production chat were not accessed or changed.",
        "",
        "Next action: correct monitor sealing in a separately versioned harness using",
        "disposable process/log tests. The current results do not justify more training",
        "or opening development under this registration.",
    ]
    path = ROOT / "docs/research/local-answer-paired-batch-dev-v1-results.md"
    write(path, "\n".join(lines) + "\n")
    print(path)

if __name__ == "__main__":
    main()
