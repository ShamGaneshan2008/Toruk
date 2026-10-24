# M7 frozen exploratory failure protocol

2026-10-20, before new held-out model evaluations. M6 provides a reproducible
negative pilot, not verified positive recall/revision. Its resource matching and
training-seed replication remain incomplete. These studies test failure persistence
and predictor fallback, not confirmation of a generalization advantage.

## Prerequisite and frozen selection

Verify M6 artifact/checkpoint/data hashes and unchanged model/scoring kernels,
then regenerate all fourteen saved validation comparisons from frozen checkpoints.
Require exact generated-token and scoring parity, ignoring wall-time differences.
No retraining, relabeling, predictor fitting, architecture or threshold changes.
No strongest M6 model exists at the primary endpoint (all tied at zero); use
the complete revision+predictor configuration and explicitly named controls.
Original M6 final-test data remain closed for scoring/selection.

Study A (templates): do the observed failures/fallbacks persist on two unseen
rendering families compared with an otherwise identical control? Use ordinary,
recurrent QA, revision always-write, revision+predictor and revision+heuristic.
Control template 2; unseen templates 4/5. Preserve events, values, entities,
questions, history order and correction count. Template 3, reserved by M6, is
not used. This is rendering robustness, not natural-language understanding.

Study B (load): how do failures change under longer irrelevant histories versus
more authoritative distractor facts at the same byte length? Use ordinary,
recurrent QA at 2/4/8 slots, revision always-write and revision+predictor. Cells:
control; 4/12 CLAIM distractors; 4/12 SET distractors. SET entity names have an
extra two-character prefix so each SET/CLAIM pair has exactly equal byte-token
length. Their authority cues necessarily differ. Claims add delay/exposure without
adding known facts; SET adds unrelated known facts. Original probe truths remain
unchanged. Fact count is input load, not measured slot occupancy or storage capacity.

## Data, splits and leakage

Use the existing controlled-world generator, oracle, tokenizer and first-line
greedy scorer. Local synthetic data only; no external corpus/access/download.
The repository has no LICENSE file; no distribution/publication is performed.
Data seeds 117 and 118, two worlds each; indices 40/41 and 50/51, respectively.
Assign evaluation world/template/cell identities before constructing examples.
Require no entity/ID overlap with M6 train/validation and at least two differences
among four known answer values after normalizing entity identities. Reject a
fixed candidate that violates this predeclared near-duplicate check; do not search
for a favorable outcome. Within-study near-duplicates are intentional paired
interventions, linked by anchor ID. Both studies reuse the same four anchors.

M7 datasets retain the v1 world format and `validation` loader role for scoring
compatibility, but carry an explicit M7 held-out/evaluation-only manifest and
training prohibition. No LM fitting export or train/test files are created.
Dataset bytes, split/cell, transformation metadata and protocol hashes must match.
The oracle scores only offline; runtime still receives history/current question
and bounded predictor inputs. No new question distribution or domain is claimed.

## Metrics, uncertainty and decision rules

Primary: the M6 four-group corrected/unchanged-name/unrelated-date/unrelated-number
macro exact accuracy, plus paired change against the same anchors' control.
Secondary: each group, unknown/ambiguous accuracy, attempted-answer coverage,
non-abstaining errors on uncertain probes, responses matching superseded values,
history/answer teacher-forced CE, predictor fallback/write rates and resource cost.
Do not call wrong non-abstaining outputs confident without confidence calibration.
Report per-data-seed outcomes and descriptive mean/sample SD over two data seeds.
All checkpoints use training seed 23: training-seed uncertainty remains unavailable.

No positive M6 generalization claim is eligible for confirmation. Additionally,
if control known-fact macro accuracy is below 50%, mark degradation onset and
capacity boundaries unidentifiable at the learning floor. Zero change from zero
is not successful transfer. Falsification/narrowing: primary decline under shift,
increased non-abstaining errors, or predictor degradation/fallback; report gains
as exploratory observations without tuning or causal attribution beyond the
specified paired intervention. Repeated-correction count stays three; no broad
update-sequence, domain-transfer or unlimited-context claim.

## Budget, cost and integrity

CPU, float32, one thread; frozen 16-token maximum, EOS stopping, no gold decoding.
Four worlds/24 answers per cell/method: 15 evaluations (360 answers) in templates,
30 evaluations (720 answers) in load. Detect hardware at run time; bound histories
by the trained 32-segment cap (2,048 tokens at context 64). Each study has a
110-second between-stage cap and a 120-second outer subprocess timeout. The M6
replay is separately capped. No model or predictor training in these studies.
New tests use independent tiny temporary worlds/checkpoints, not study outcomes.

Record full stage/command wall time (including load, scoring and IO), inference
time/forward token positions, text tokenized, teacher-forced work, proposal/decision
counts, parameter/state bytes, throughput, cumulative process peak working set,
and failed/incomplete stages. Historical M6 training/branch/predictor costs are
inherited and referenced, not counted as free or charged again per evaluation.
Process peaks are cumulative framework/process measurements, not per-model
allocated-memory comparisons. Test-loop token totals remain uninstrumented.

No retry for favorable scores. Validate expected cell/method completeness,
unique world/question pairs, checkpoint/data/protocol/code identities, strata
counts and paired anchors. Save raw answers, per-seed/stratified results and
manifests. Final-test access and confirmatory resource-matched claims remain
NOT_RUN. M7 can establish narrow failure observations, not paper readiness.

## Reproduction

With retained M6 checkpoints/source archive and fresh output paths/labels:

```powershell
python scripts/check.py m7-replay -- python -m toruk_lm verify-m6 --parent artifacts/m6-validation-001 --handoff artifacts/m6-handoff --output artifacts/m7-m6-replay
python scripts/check.py m7-templates -- python -m toruk_lm generalization --parent artifacts/m6-validation-001 --verification artifacts/m7-m6-replay/verification.json --study templates --output artifacts/m7-templates-001
python scripts/check.py m7-load -- python -m toruk_lm generalization --parent artifacts/m6-validation-001 --verification artifacts/m7-m6-replay/verification.json --study load --output artifacts/m7-load-001
```

Use `.venv` Python on Windows. Model checkpoints are retained locally under the
existing Git ignore rule; these commands require those artifacts. A clean-machine
training/source-archive reproduction belongs to the outstanding M8 handoff.
