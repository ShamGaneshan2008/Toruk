# Local answer development v1: training prerequisite failed

20 November 2026. **Needs a specific new training design.** Three cells learned
all96 training answers; ordinary seed947 learned80/96 and produced four malformed
`lo` answers. All training continuations ended in EOS. The frozen all-cell
training gate failed, so **no development LM answers, development losses,
question-only LM controls, or registered deterministic-control stage were run**.
Fresh-combination generalization is unevaluated, not a measured development failure.

The registered run completed once with **complete workload-process accounting**:
103.500000 CPU /104.515580 wall seconds, zero active descendants. Its resource/
integrity envelope passed; its quality decision is `STOP_TRAINING_FAILURE`.
There was no extra fitting, checkpoint selection, cap increase, prompt repair,
or fallback to Answer16. No memory or architecture-advantage claim is supported.

## Starting repository and preserved v1 commit

Confirmed root `D:\Toruk` (`D:/Toruk` from Git), branch `main`, initial HEAD
`39c4e4756b24ca3d09c4a9aa8ae63b1a2b5ab208`. Initial status contained the existing
answer-trainability-v1 work: modified .gitattributes, its script/tests/protocol/
report, and study/preparation/verification artifact directories. Nothing was lost.

Reviewed342 inventory entries,32 numerical report rows,20 representative
predictions and56 links; byte/size/hash checks and frozen read-only audit passed.
Committed339 files, including all334 non-checkpoint inventory entries, inventory,
review receipt/script/report and narrow generated-cache exclusions. Diagnosis
and prior commits remain intact. **V1 record commit:**
`301dd9edbf12403aa97e5013247d5b1f33be0746`. No push.

[V1 commit review](answer-trainability-dev-v1-commit-review.md) explicitly preserves
its STOP receipt, both failed development gates, and UNKNOWN complete-lifetime
CPU. Its recorded lower bound stays300.109375 CPU seconds. Eight ignored v1
checkpoints stay local with unchanged hashes. Source snapshots retain exact
bytes, including the archived pyproject's blank EOF. Later engineering changes
coexist with the record; tree-based review validates the original committed
attributes rather than assuming mutable working attributes are still frozen.

The [saved-output diagnosis](local-answer-v1-saved-diagnosis.md) covers all16 old
development cases across eight cells:49 correct and79 failures among128 outputs.
Primary failures are68 wrong closed values, four closed malformed outputs and
seven EOS failures.58 wrong outputs match a known training answer to the same
question. No known fact is missing; no substitution of another supplied entity
or wrong-attribute value is directly verified. IDs, full texts and assignment/
query cores are split-disjoint.13/16 development questions repeat training
questions; both splits share one syntax. These facts support a question/entity
prior hypothesis without claiming to prove an internal confusion mechanism.
No v1 continuation was regenerated and no score or gate was changed.

## Accounting fix and pre-training prerequisites

NEW [lifetime_job.py](../../scripts/lifetime_job.py) uses Windows Job kernel
accounting after all controller/worker descendants exit. It also retains a
finally status receipt for cooperative controllers. It accounts abrupt exits
without a self-report, and drains the entire tree on cap/interruption.
[Engineering record](local-answer-accounting-v1.md) gives the implementation,
measurement boundary and failure tests. The frozen v1 controller was not edited.

Seven real-process accounting tests passed, covering success, failure,
KeyboardInterrupt, os._exit, observer cancellation, cap kill and a CPU-burning
descendant outliving its parent.21 scenario receipts from the first two suites
and the combined pre-training contracts are retained outside test caches;
15 are intentionally STOP and six PASS, all with complete lifetimes and zero
active processes. [Case index](../../artifacts/local-answer-accounting-v1/retained-test-cases/cases.json).
Combined contracts:11 passed before registration (seven accounting/four data and
numeric model contracts). These use no study fits or generated study answers.

The one numeric resource rehearsal used seed900301, three random8x64 forward/
backward passes per model and zero optimizer updates, with no study documents.
All gradients were finite. The predeclared projection was58 seconds per fit for
both models, below the unchanged120-second cap. Its cold Job CPU/wall was
3.265625 /3.984155 seconds; peak674,709,504 bytes.
[Rehearsal evidence](../../artifacts/local-answer-dev-v1-preparation/rehearsal-001/rehearsal.json)
and [complete cost](../../artifacts/local-answer-dev-v1-preparation/rehearsal-001/cost.json).
No alternate rehearsal or cap increase was used.

## Frozen protocol and study identity

[Protocol](local-answer-dev-v1-protocol.md),
[registration](../../artifacts/local-answer-dev-v1/registration.json),
[single-use marker](../../artifacts/local-answer-dev-v1/run-start.json),
[as-run source](../../artifacts/local-answer-dev-v1/sources/scripts/local_answer_dev.py),
[training gate](../../artifacts/local-answer-dev-v1/training-gate.json),
[summary](../../artifacts/local-answer-dev-v1/summary.json).

Registration SHA256, printed before any study fit or answer:
`c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4`.
It binds exact data, protocol/source snapshots, tokenizer, configurations,
runtime, seeds/order, steps, scoring/gates, caps and prerequisite receipts.
All those seals still match. The old v1 protocol/results/scorer stay unchanged.

Training has96 documents:24 canonical combinations x two templates x two prelude
nonces. Each entity appears with two distinct city values and two codes. The
24 development inputs use the other two values per entity/category; all nine
answer strings occur in training. Each split is balanced by city/code/unknown
and template. Two word orders are represented in BOTH splits; this is not a
test of an unseen question syntax. IDs, full prompts and canonical tuples are
split-disjoint. Unknown cases supply a role and ask for city. The31-byte prelude
plus BOS occupies segment one; the complete assignment, question, answer and
EOS fit together in segment two. Thus required information is local.

Unchanged byte tokenizer,259 IDs, PAD0/BOS1/EOS2, byte+3. Existing ordinary
matched LM:14,058 parameters; recurrent:14,416, four slots,256-byte state;
context32, one layer, float32 deterministic CPU, one Torch thread. Widths differ
(18 versus16), within2.55% parameter difference. No pretrained or old weights.

Uniform full-document CE is the ONLY objective, including EOS, without answer
weighting. Fixed seeds601/947; exactly1,536 AdamW steps, batch8, lr.003, clip1.0,
registered optimizer settings. Each document appears128 times per fit,12,288
presentations. Per fit:692,224 targets including36,864 answer/EOS targets.
Matched example order/target counts/padded forward positions per seed:711,856
positions at601 and711,920 at947. Across four fits:6,144 updates,49,152 document
presentations,2,768,896 targets and2,847,552 padded forward positions. Actual CPU
differs by configuration and is reported; equal FLOPs/compute are not claimed.

Final checkpoints only; fit order601 ordinary/recurrent,947 recurrent/ordinary.
After each fit,97 training requests (96 cases + replay), then separate
teacher-forced loss scoring. All four fits/stages completed once. No development
access by a fitted model was allowed until every training cell had>=90/96 exact,
96/96 EOS and zero malformed outputs.

## Training observations against the frozen gate

Counts exclude first-case replay. Greedy native IDs are scored exactly as gold
UTF-8 bytes+3 followed by EOS; no output is trimmed or repaired.

| Seed | Model | Exact /96 | EOS /96 | Malformed | Repetitive | City /32 | Code /32 | Unknown /32 | Template A/B /48 | Training gate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 601 | ordinary | 96 | 96 | 0 | 0 | 32 | 32 | 32 | 48/48 | PASS |
| 601 | recurrent | 96 | 96 | 0 | 0 | 32 | 32 | 32 | 48/48 | PASS |
| 947 | recurrent | 96 | 96 | 0 | 0 | 32 | 32 | 32 | 48/48 | PASS |
| 947 | ordinary | 80 | 96 | 4 | 0 | 16 | 32 | 32 | 40/40 | FAIL exact and format |

Total368/384 scored training answers exact,384/384 EOS, four malformed and no
repetitive outputs by the frozen definition. All four replays match native IDs
and work, bringing saved continuations to388. The failing model's16 wrong
answers all have a wrong FIRST emitted byte. Twelve are wrong closed city values;
four are closed `lo`, absent from the answer inventory. Closure alone is learned
in this run; content remains unstable for one initialization.

The16 failures are four canonical combinations repeated across both templates
and both nonce variants. They are not16 independent failure mechanisms:

| Ordinary947 training cases | Supplied local fact | Gold | Raw IDs | Continuation | Count |
| --- | --- | --- | --- | --- | ---: |
| train-004..007 | uvo city=mi | `mi` | `[111,114,2]` | `lo` + EOS, malformed | 4 |
| train-024..027 | pex city=mi | `mi` | `[118,114,2]` | `so` + EOS, wrong value | 4 |
| train-048..051 | zim city=so | `so` | `[119,120,2]` | `tu` + EOS, wrong value | 4 |
| train-076..079 | nax city=la | `la` | `[119,120,2]` | `tu` + EOS, wrong value | 4 |

The same failure across both word orders and nonces limits a simple template/
nonce explanation. Correct code and unknown behavior, explicit local evidence,
and universally emitted EOS exclude missing source data or absent EOS training
as explanations for these16 failures. The output pattern is consistent with
city-value interference or insufficient acquisition of the first answer byte;
no unseen logits, training interventions or internal-state attribution were
manufactured to identify a causal mechanism.

Every raw continuation and final checkpoint metadata is linked here:

| Cell | Raw training answers | Training trace | Checkpoint metadata |
| --- | --- | --- | --- |
| 601 ordinary | [raw](../../artifacts/local-answer-dev-v1/stages/generate-train-601-ordinary/predictions.jsonl) | [trace](../../artifacts/local-answer-dev-v1/stages/train-601-ordinary/training.jsonl) | [metadata](../../artifacts/local-answer-dev-v1/stages/train-601-ordinary/checkpoint-meta.json) |
| 601 recurrent | [raw](../../artifacts/local-answer-dev-v1/stages/generate-train-601-recurrent/predictions.jsonl) | [trace](../../artifacts/local-answer-dev-v1/stages/train-601-recurrent/training.jsonl) | [metadata](../../artifacts/local-answer-dev-v1/stages/train-601-recurrent/checkpoint-meta.json) |
| 947 recurrent | [raw](../../artifacts/local-answer-dev-v1/stages/generate-train-947-recurrent/predictions.jsonl) | [trace](../../artifacts/local-answer-dev-v1/stages/train-947-recurrent/training.jsonl) | [metadata](../../artifacts/local-answer-dev-v1/stages/train-947-recurrent/checkpoint-meta.json) |
| 947 ordinary | [raw](../../artifacts/local-answer-dev-v1/stages/generate-train-947-ordinary/predictions.jsonl) | [trace](../../artifacts/local-answer-dev-v1/stages/train-947-ordinary/training.jsonl) | [metadata](../../artifacts/local-answer-dev-v1/stages/train-947-ordinary/checkpoint-meta.json) |

Four `.pt` checkpoints remain local/git-ignored and strictly reload without new
model execution; hashes/sizes are saved. Trace IDs confirm each document128 times,
matching both models at each seed. The original checkpoint/data files are not
changed by audit. A checkout lacking checkpoint bytes cannot claim strict-load
reproduction from metadata alone.

## Loss trajectory and limits of average loss

Uniform losses are teacher-forced, not generation scores. The answer partition
includes EOS; there are288 answer/EOS targets among5,408 unique training targets
(5.3254%). No Answer16 experiment or new weighting condition was run.

| Seed | Model | First update CE | Last update CE | Final full training NLL | Final history NLL | Final answer/EOS NLL |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 601 | ordinary | 5.806232 | 0.130688 | 0.126283 | 0.132949 | 0.007781 |
| 601 | recurrent | 5.766353 | 0.133977 | 0.129397 | 0.136106 | 0.010135 |
| 947 | recurrent | 5.660182 | 0.129660 | 0.129054 | 0.135519 | 0.014129 |
| 947 | ordinary | 5.590914 | 0.147844 | 0.141583 | 0.144438 | 0.090816 |

All objectives/gradients remain finite and losses decline substantially. Small
average losses can hide a wrong first generated byte because teacher forcing
supplies the correct first byte for later targets; easy history/EOS targets also
dominate the average. The saved raw IDs prove the first-byte mistakes, but no
per-token probability/rank was saved and no new forward pass was run to obtain it.
These minibatch endpoints are not a convergence proof or a steps-to-success
measurement. Final-only checkpoints prevent a claim that an earlier one passed.

## Controls, skipped development and advancement

The pre-training static source-parser contract returned the authored answer for
all96 training and24 development prefixes. It used prefix only and confirms
that both local templates supply unambiguous sufficient information. This is a
handwritten source validation, **not** a trained LM result or a registered
post-training control score with raw continuations.

The separately registered parser/question-prior control worker, main development
workers and question-only LM diagnostic were conditional on the all-cell training
gate. They were NOT executed after its failure. Their absence is checked by the
audit; no apparent control success is inserted into the summary. Thus the task's
literal solvability is established, but learned dependence on local context and
fresh-combination accuracy remain unmeasured.

| Frozen condition | Result |
| --- | --- |
| Accounting contracts and complete lifetime closure | PASS |
| Numeric rehearsal/projected fit within fixed caps | PASS |
| Source/data/config/checkpoint/replay integrity and resource envelope | PASS |
| Every cell >=90/96 training exact,96 EOS,zero malformed | FAIL ordinary947 |
| Development >=22/24, category floors and24 EOS/zero malformed | NOT RUN |
| Known-case gain>=8 against question-only diagnostic | NOT RUN |
| Registered deterministic parser24/24 control stage | NOT RUN; static pre-training parser contract passed |
| Advancement to separately registered memory comparison | NO |

Passing training at three configurations does not establish an advantage for
recurrent memory. The task is local, configurations differ in width, sample size
is tiny, and no development architecture comparison was permitted.

## Complete registered-process costs and memory

The enclosing [Job receipt](../../artifacts/local-answer-dev-v1/execution/cost.json)
has statusPASS, complete_process_lifetimes=true, active_processes=0 and65 total
process lifetimes. User92.328125 + kernel11.171875 = **103.500000 CPU seconds**;
wall104.515580. This includes the run controller, phase workers, launchers,
transient descendants and inner stage-observer activity through process exit.
The [controller finally receipt](../../artifacts/local-answer-dev-v1/execution/controller-final.json)
also exists and reports normal completion of the quality-stop path.

Cold costs include import/setup, model/optimizer construction, traces, checkpoint
I/O and process teardown. Loop intervals are subsets. Units are seconds:

| Seed | Model | Cold fit CPU/wall | Loop CPU/wall | Training generation CPU/wall | Training loss CPU/wall | Fit peak Job bytes |
| --- | --- | --- | --- | --- | --- | ---: |
| 601 | ordinary | 13.968750 /14.605066 | 10.765625 /10.814636 | 3.531250 /4.051764 | 3.312500 /3.990764 | 675446784 |
| 601 | recurrent | 20.500000 /21.015847 | 17.234375 /17.241716 | 3.609375 /4.208873 | 3.406250 /4.017614 | 677105664 |
| 947 | recurrent | 20.546875 /21.253515 | 17.312500 /17.409811 | 3.625000 /4.326045 | 3.406250 /4.018622 | 676790272 |
| 947 | ordinary | 14.171875 /14.747969 | 10.812500 /10.864666 | 3.312500 /4.035139 | 3.187500 /3.892247 | 676204544 |

Four fits total69.187500 CPU /71.622398 wall; four training-generation stages
14.078125 /16.621821; four training-loss stages13.312500 /15.919247. Sum of12
stage workloads96.578125 CPU is a SUBSET of103.500000, not an extra charge. The
6.921875 difference covers the enclosing controller/inner-observer activity and
other registered work outside the phase Jobs. Enclosing wall already contains
the104.163465 stage-wall sum. Do not sum nested cost scopes with their parent.

Warm generation over388 requests totals1.125000 CPU /1.126822 wall seconds,
inside cold-generation cost. CPU clocks are quantized, so per-request zero ticks
do not mean free work. All raw request times are retained.

Kernel peak enclosing Job committed memory699,076,608 bytes (the cost key is
`peak_private`); maximum fit peak677,105,664. This is commit accounting, not
tensor-state size or RSS. Logical run-disk peak4,388,522 bytes. Maximum sample
gap0.103139 seconds. All fixed120-second fit/20-second evaluation/1,000-second
overall caps,2GiB memory and128MiB disk ceilings passed. The fixed1,536 steps
were not extended merely because wall time remained below the cap.

The OUTERMOST measurement observer is outside the registered Job; its6.453125
CPU-to-receipt snapshot is separate and not asserted as a full observer lifetime.
The measurement boundary was frozen before fitting. No complete lifetime project
total is claimed for design, editing, diagnosis and analysis outside that Job.
V1's unknown complete CPU remains unknown and is never replaced with this total.

Other disjoint scopes are reported separately: contracts4.562500 CPU /5.954813
wall; numeric rehearsal3.265625 /3.984155; freeze2.031250 /2.631629. Initial
accounting probe/suites and their intentional failed-case costs are retained in
the engineering artifacts, not omitted or counted as LM quality attempts.
No new study fit failed a cap/integrity check, and no fit/answer was retried.

## Offline checks, evidence and Git state

[Frozen audit](../../scripts/local_answer_dev.py) and independent
[saved-evidence audit](../../artifacts/local-answer-dev-v1/verify_saved.py) passed.
The independent [audit output](../../artifacts/local-answer-dev-v1/saved-audit.json)
includes every failure's raw IDs/source line, all stage costs, target accounting,
matched exposure/work, losses, gate checks and absence of forbidden development
stages. These commands fit no model or generate answers; strict load checks
construct models only to restore existing saved tensors.

All11 scoped repository checks passed, including29 focused numerical/process
tests, repository Ruff lint/format, Windows and Linux-target mypy (38 source files
each), frozen-source checks, current-study audits, committed v1/segment-delta
evidence audits and `git diff --check`.
[Coverage/commands](../../artifacts/local-answer-dev-v1-verification-001/coverage.json).
The verification Job closes81 process lifetimes:112.187500 CPU /107.011474 wall,
peak1,584,324,608 bytes, zero active processes, statusPASS.
[Verification receipt](../../artifacts/local-answer-dev-v1-verification-001/execution/cost.json).
Its seven repeated accounting scenarios are also retained outside disposable
fixtures: [case index](../../artifacts/local-answer-dev-v1-verification-001/retained-job-tests/cases.json).
Its outer observer8.312500 CPU-to-receipt is separate. No historical study run,
unfiltered held-out loader, web/deployment flow or live integration was invoked.
This is not a full-suite or hosted CI claim. Native Job tests are Windows-only
and use an explicit workspace basetemp.

Repeat read-only evidence review from Windows PowerShell:

```powershell
Set-Location D:\Toruk
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
.\.venv\Scripts\python.exe -B artifacts/answer-trainability-dev-v1-commit-review-001/review.py --revision 301dd9edbf12403aa97e5013247d5b1f33be0746
.\.venv\Scripts\python.exe -B scripts/diagnose_local_answer_v1.py
.\.venv\Scripts\python.exe -B scripts/local_answer_dev.py audit
.\.venv\Scripts\python.exe -B artifacts/local-answer-dev-v1/verify_saved.py
.\.venv\Scripts\python.exe -B artifacts/local-answer-dev-v1/verify_reports.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
git diff --check
git status --short
```

Do not rerun historical worker, freeze or run commands; the exclusive run marker
prohibits repeat execution. Their exact commands/costs are archived. The static
source controls and audits must not be substituted for skipped development LMs.

HEAD remains `301dd9edbf12403aa97e5013247d5b1f33be0746` on main, with no staged
files and no push. New work is uncommitted. Tracked edits are narrow .gitattributes
rules for new evidence/source bytes and .gitignore rules for generated local
test caches. New files are three research scripts (Job accounting, saved-v1
diagnosis, local study), two test modules, protocol/results/diagnosis/accounting
documents and four local-answer artifact directories (accounting, preparation,
study, verification). No production src/chat code changed, no held-out cases
were opened and no prior work was deleted or reformatted.

[Final inventory](../../artifacts/local-answer-dev-v1/artifact-inventory.json)
records hashes/sizes of the new sources, documents, raw evidence and local
checkpoints; generated pytest caches are excluded, while copied failed-process
test receipts are retained. [Final Git receipt](../../artifacts/local-answer-dev-v1/final-git-state.json)
records the unchanged HEAD and unstaged work. The inventory excludes its own
self-reference and does not replace unavailable checkpoint bytes in another checkout.

## Limits and one decision

No development LM score exists for this run, so neither generalization success
nor fresh-combination failure can be inferred. This tiny synthetic grammar,
finite shared inventories and repeated24 canonical training cores do not measure
broad language competence. Only four fits/two seeds were registered; three
successful training cells do not establish reliable seed-independent acquisition.
Data/targets/work were matched, but different widths and actual compute limit
architecture attribution. Checkpoint bytes are local; metadata alone cannot
reproduce a strict reload elsewhere.

**Decision: local answering needs a specific new training design.** Register a
two-phase, uniform-CE city-copy curriculum: first put contrasting values for the
same entity/question together in balanced city-only batches, then introduce the
mixed code/unknown tasks and second template at fixed predeclared exposure.
Keep per-field and first-answer-byte checks, EOS/exact gates and resource limits
fixed before any fit. This targets the observed city/first-byte failure instead
of selecting a weighted-objective seed or modifying the decoder/scorer. It is a
hypothesis for a new protocol, not a proven cure or additional training here.
Keep memory comparisons deferred until the development gates are actually met.
