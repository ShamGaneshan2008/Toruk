# M7 exploratory failure studies

2026-10-20, `main`, base `a025f0148965089b24a69344a13cd8a6447afef9`.
All changes remain local and uncommitted. Status: **PARTIAL**. The bounded
studies execute; successful generalization and an identifiable capacity boundary
remain unsupported. [Frozen protocol and commands](m7-protocol.md).

## M6 prerequisite verification

The pre-edit M6 source/evidence seal matched all 201 recorded files and all twelve
final check records passed. The new replay independently checks the parent run
manifest, every recorded file/checkpoint hash, the original world semantics and
the six unchanged model/tokenizer/runtime/scoring source kernels against the
sealed source archive. It then regenerates all fourteen comparisons: **336/336
answers match the saved generated token IDs, answers, labels and group scores**.
Evidence: `artifacts/m7-m6-replay/{protocol,verification,stages}.json` and raw
per-method predictions. Replay driver 29.272 s, full command 32.417 s.

This verifies execution of the negative M6 pilot. It does not repair M6's limited
learning, single training seed, unequal parameter/total compute budgets or absent
final test. Equal world/optimizer-step budgets are recorded, not represented as
equal FLOPs. Objective/slot ablations are implemented but their contributions
remain unidentifiable at zero primary accuracy. No strongest model is established;
M7 includes the complete revision/predictor configuration with named controls.

## Frozen held-out design

Two small studies reuse the same four new semantic anchors (data seeds 117/118,
two worlds each), with disjoint entities/worlds from M6 train/validation and
predeclared answer-combination near-duplicate rejection. Three template cells
compare the original rendering with two new families; five load cells compare
control, 4/12 nonauthoritative CLAIM distractors and 4/12 authoritative SET facts.
SET/CLAIM pairs have exactly matched byte lengths and evidence distances.
All cases use the same six questions and fixed 16-token greedy answer budget.
No model/predictor fitting, threshold selection or outcome-based retry occurred.

Data are locally generated synthetic records; no external corpus or access rights
are involved, and nothing is distributed. M7 manifests explicitly identify
held-out evaluation-only data despite retaining the existing `validation` loader
role for kernel compatibility. No train files or fitting exports are produced.
Training loaders reject these datasets. M6 final-test template/data stay closed
for scoring and model selection. Manifest hashes cover the held-out data and
protocol, and checkpoint/predictor/tokenizer bindings are retained.

The new templates also change history length. Their contrast measures a rendering
intervention with that length effect; it does not isolate paraphrase semantics.
The density contrast changes authority cues and entity spelling intentionally.
All questions, attributes and three-correction structure remain familiar: these
are not second-domain or question-distribution-transfer experiments.

## Actual quality and uncertainty

All **45 cell/method evaluations, 1,080 answers** completed. Primary known-fact
macro accuracy is **0% in every cell/method**, separately **0% for each data
seed**, with descriptive data-seed sample SD zero. Every corrected, unchanged-name,
date and number stratum is at zero. This is four semantic anchors reused across
interventions and methods, not 1,080 independent examples. Two data seeds and one
training seed (23) give no estimate of training-seed uncertainty or reliable
population confidence interval.

Overall exact accuracy below includes unknown/ambiguous answers. It must not be
substituted for known-fact recall. Each entry has 24 answers.

| Method | Control | New template 4 | New template 5 | CLAIM +4 | CLAIM +12 | SET +4 | SET +12 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ordinary | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |
| Recurrent, 4 slots | 8.3% | 16.7% | 12.5% | 12.5% | 8.3% | 12.5% | 12.5% |
| Recurrent, 2 slots | 0% | NOT_RUN | NOT_RUN | 4.2% | 0% | 4.2% | 0% |
| Recurrent, 8 slots | 12.5% | NOT_RUN | NOT_RUN | 12.5% | 12.5% | 12.5% | 12.5% |
| Revision, write | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| Revision, predictor | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| Revision, heuristic | 0% | 0% | 0% | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |

Controls were evaluated independently in both studies and have identical generated
answers/scores. The ordinary model always answers `?`; its coverage is zero.
Recurrent nonzero scores come exclusively from uncertain probes. All revision
predictor decisions fall back before executing the learned MLP: 12/12 template
decisions and 20/20 load decisions. Only the final-history write is suppressed;
earlier memory writes still occur. No learned predictor benefit is demonstrated.

## Capacity and failure observations

Tested histories span **649–1,066 byte tokens including BOS**, known valid facts
span **6–20**, and observed probe evidence distances span **143–864 tokens**.
These are input ranges, not proven memory retention limits. Fixed float32 state
sizes at 2/4/8 slots are 256/512/1,024 bytes, with 56,960/57,088/57,344 parameters.
Ordinary has 44,096 parameters and no recurrent state; the predictor adds 4,641
parameters. No state size establishes recall, efficiency or saturation onset.

Revision write answers match superseded values in 2/24 cases in control and each
template cell, 3/24 under four added CLAIM or SET records, and 2/24 under twelve
records. Predictor answers match superseded values in 2/24 in every cell. These
are output-value matches, not proof the model retrieved a stale memory: the
model often emits the same `gold` answer. For example, anchor 117/40's corrected
truth is `green`, but the model outputs the earlier value `gold`; it emits `gd`
for unchanged name `Ada` and date `2026-10-21`, and `gol` for count `50`.
Unrelated facts already fail in control, so causal overwriting is unidentifiable.

Revision has four wrong nonempty/non-`?` uncertain answers out of eight uncertain
probes in every cell; its other uncertain failures are blank answers. These are
non-abstaining errors, not measured confidence. Unknown/ambiguous discrimination
and confidence calibration are not established. Correction count stays three;
no repeated-update-count boundary is measured.

History CE worsens from control 5.2047 to 5.2458 for recurrent and 5.2737 to 5.3242
for revision under twelve authoritative distractors; their matched CLAIM CEs
are 5.2219 and 5.2938. Ordinary control/SET+12 CE is 5.3731/5.3927. These teacher-
forced nats/byte diagnostics do not establish a causal memory penalty or matched-
compute advantage. Raw answer CE, per-seed metrics, strata, errors and policies
are in each cell's `analysis.json`, with independent aggregation in
`artifacts/m7-analysis.json` (204 study manifest entries verified).

## Measured costs

CPU float32, one thread, Python 3.14.6/Torch 2.14.1+cpu, Windows 11, 12 logical
CPUs. CUDA is unavailable to this environment. Each study used its frozen
110-second between-stage budget/120-second outer timeout without a failed stage.

| Measurement | Templates | Load |
| --- | ---: | ---: |
| Evaluations / answers | 15 / 360 | 30 / 720 |
| Driver / full command seconds | 29.710 / 32.845 | 58.938 / 62.045 |
| History+generation inference seconds | 25.978 | 53.345 |
| Model loading seconds | 0.340 | 0.678 |
| History tokens read including BOS | 49,800 | 105,216 |
| Question tokens / generated tokens | 6,120 / 5,760 | 12,240 / 11,520 |
| Inference forward-token positions | 285,240 | 564,996 |
| Offline answer-scoring forward positions | 26,232 | 46,170 |
| Derived inference / offline scoring forward calls | 6,858 / 606 | 13,812 / 1,130 |
| Derived memory proposals, including offline scoring | 5,832 | 12,210 |
| Final boundary decisions / writes | 48 / 28 | 100 / 80 |
| Cumulative process peak bytes | 311,234,560 | 313,155,584 |

Counts sum repeated work across models/cells. Inference throughput is retained
per cell as forwarded positions/second, not comparable output-token efficiency.
Proposal/call counts are derived from the unchanged kernel control flow; proposals
include offline state clones. Predictor support/fallback costs are inside measured
wall time; no MLP is executed on its 32 deployed M7 decisions. Stage/full-command
time also includes scoring, tokenization, integrity checks and IO. Peaks include
the interpreter/framework and are cumulative, not per-model allocated tensors.
No new study training occurred. Historical M6 training, paired-label generation,
predictor fitting and failed pilot costs remain referenced in both protocols and
the analysis record. Test-loop training tokens are uninstrumented. Recorded check
wall times include tests and initial failures, may overlap, and are not CPU-hours.

## Verification and handoff

Local **PASS**: 28 tests, zero skips (72.36 s pytest, 73.82 s command), including
four new split/hash/shift/strata/stale-artifact/real held-out CLI tests. Ruff lint,
format, mypy (14 package files), offline editable installation, dependency/import,
module/console help, diagnostics and wheel/sdist build pass. The optional NumPy
warning is retained. Initial mypy failure (two missing collection annotations)
was corrected; its FAIL record remains in `artifacts/checks/m7-initial-types.*`.
Focused tests and all bounded studies passed; no exclusions or metric-driven
retries. Commands and logs use `artifacts/checks/m7-*` labels.

Read-only GitHub API verification again finds **PASS** for existing HEAD only:
[run 39294787042](https://github.com/ShamGaneshan2008/Toruk/actions/runs/39294787042).
Current local code remains **NOT_RUN remotely**; no workflows were triggered.
Raw API response: `artifacts/m7-remote-runs.json`. Final-test scoring, multiple
training-seed replication and clean-machine reproduction are **NOT_RUN**.
No commit, push, branch creation, publishing or paid compute was performed.

Reproduction commands are in the frozen protocol. They require retained local
M6 checkpoints (ignored by Git) and the sealed M6 source archive; use fresh output
paths/check labels. `evaluate-heldout` additionally reproduces one explicitly
bound cell/method. `artifacts/m7-handoff` seals current source, environment and
evidence checksums; this local seal does not substitute for M8 reproduction.

## Interpretation and remaining work

The protocol requires control primary accuracy at least 50% before estimating a
degradation onset or capacity boundary. Every tested control fails this gate.
Zero change from zero is not successful transfer. The experiments support narrow
observations about failure persistence, abstention, superseded-value matches and
fallback behavior in the tested range. They support no superiority, efficiency,
unlimited context, broad understanding, novelty or paper-readiness claim.

M8 needs a clean-machine source/checkpoint reproduction, meaningful validation
learning before freezing a separate final test, multiple independent training
seeds, fairer parameter/total-compute comparisons and fuller test-loop accounting.
Any future training or design change needs a fresh protocol and untouched held-out
data; these exploratory cases have now been observed. Preserve the negative runs.
