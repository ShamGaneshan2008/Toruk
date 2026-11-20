# Answer trainability development v1: overfit success, development failure

20 November 2026. **Both existing LMs can learn complete training answers ending
in EOS. Neither objective meets the predeclared development criteria.** All eight
fits achieve8/8 exact on the tiny training set. Development scores range4–9/16,
with incomplete or malformed answers remaining in several cells. The quality
decision is `STOP_GENERALIZATION_FAILURE`; no memory-mechanism study is justified.

**The registered enclosing cost envelope also failed:** the controller omitted
its final lifetime receipt. All40 individual model stages passed, but the outer
watcher correctly retained `STOP: worker cost receipt missing`. The results below
are audited saved quality observations and recorded stage measurements, not a
fully valid registered run or a complete lifetime-efficiency claim. No fit or
answer was retried, and no receipt or frozen protocol was repaired retrospectively.

## Repository and diagnosis preservation

Confirmed root `D:\Toruk`, branch `main`, initial HEAD
`febb3c5ebc8acf36bf60746515084d8e009bb231`. Initial status contained exactly the
two diagnosis additions. Reviewed all240 displayed prediction entries, eight raw
ID examples,47 links, six checkpoint loads, original evidence seals, Ruff and
whitespace checks. Committed **only**:

- [diagnosis report](segment-delta-dev-v1-diagnosis.md)
- [read-only diagnostic](../../scripts/diagnose_segment_delta_dev.py)

Diagnosis commit: **`39c4e4756b24ca3d09c4a9aa8ae63b1a2b5ab208`**. No push.
The diagnosis is a historical record of its pre-commit state. Its sources, all
segment-delta-v1 artifacts, protocol/scorer/results, and production chat remain
unchanged. The new study's work remains uncommitted.

## Frozen new protocol

[Protocol](answer-trainability-dev-v1-protocol.md),
[registration](../../artifacts/answer-trainability-dev-v1/registration.json),
[as-run sources](../../artifacts/answer-trainability-dev-v1/sources/scripts/answer_trainability_dev.py),
[single-use run marker](../../artifacts/answer-trainability-dev-v1/run-start.json),
[training gate](../../artifacts/answer-trainability-dev-v1/training-gate.json),
[quality summary](../../artifacts/answer-trainability-dev-v1/summary.json).

The registration SHA256, recorded before any study fit/answer, is
`d019194831da0039008f39ff3c3060f4384af3587cf5fa45f844a1ae56dc27a2`.
It binds exact data/source hashes, tokenizer fingerprint, runtime, optimizer,
model counts, seeds419/733, order, loss weights,512-step limit, caps, scorer and
success thresholds. Six focused contracts passed before the freeze. The source
and data seals still match; there was one registered execution, not a sweep.

Eight training documents: four cities, two punctuation-sensitive codes, two
unknowns. Sixteen separate development documents: eight cities, four codes,
four unknowns. [Training documents](../../artifacts/answer-trainability-dev-v1/train-documents.json),
[development prefixes](../../artifacts/answer-trainability-dev-v1/dev-inputs.json),
[development labels](../../artifacts/answer-trainability-dev-v1/dev-labels.json).
IDs, full texts, and assignment/query cores are disjoint. All seven answer
strings occur in training. Labels pass an independent source-assignment check.
There are no held-out cases in this study and none were opened elsewhere.

BOS plus31 irrelevant prelude bytes occupies the first32-ID segment. Assignment,
question, answer and EOS all fit together in the second segment. Both models see
the required local evidence; recurrent also has an active entering state. The
first segment contains no information needed to answer. This tests answering,
not long-distance memory, and avoids v1's nominal-local/segment-phase confound.

Models are the unchanged existing factory's `ordinary_matched` (width18,
heads2,one layer,14,058 parameters) and `memory_on` (width16,heads4,one layer,
four slots,14,416 parameters,256-byte recurrent state), context32. Parameter
difference2.55%; different widths remain a causal-comparison limitation.
Float32 deterministic CPU, one Torch thread; no pretrained weights.

Each cell uses512 AdamW steps, batch4 complete documents, lr.003, clip1.0 and
the frozen optimizer settings. Each training document appears256 times:2,048
presentations,115,200 targets including6,144 answer/EOS targets per fit. All
models/objectives use identical ordered documents per seed and matched nominal
forward positions:117,944 at419;117,952 at733, including padding. Across the
eight fits:4,096 updates,16,384 presentations,921,600 targets,943,584 forward
positions. For each model/seed, both objectives start with identical weights.
Measured compute differs; no claim of equal CPU or equal FLOPs.

Two objectives only: full-document uniform CE, and the same CE with answer bytes
plus EOS weighted16 while pre-answer targets remain weight1. The objective is
`(H + w*A)/(Nh + w*Na)`. Both gradient partitions are differentiated on the same
graph and summed before common clipping/AdamW. There is no other arm-specific
change. Final checkpoints only; no early selection, extra fitting, or retries.

All eight training cells passed8/8 exact, so both objectives qualified for
development. The [gate receipt](../../artifacts/answer-trainability-dev-v1/training-gate.json)
was written before any development generation/loss evaluation. Each objective
would need all four model/seed cells to have16/16 EOS-complete inventory answers,
>=12/16 exact and category floors6/8 city,3/4 code,3/4 unknown. Neither passes.

## Exact quality observations

Counts exclude replays. There are64 scored training outputs and128 development
outputs, plus16 deterministic replays =208 saved continuations. Every replay
matches the first case's generated IDs and work. Greedy decoding suppresses only
PAD/BOS, cap8, with EOS eligible. The scorer compares native IDs to gold UTF-8
bytes+3 then EOS, with no trimming, inserted EOS, or repaired answers.

| Seed | Objective | Model | Train exact/EOS /8 | Dev exact /16 | Dev EOS /16 | Dev malformed | Dev repetitive | Dev city/code/unknown exact |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 419 | uniform | ordinary | 8/8 | 7 | 16 | 0 | 0 | 2/8,1/4,4/4 |
| 419 | uniform | recurrent | 8/8 | 6 | 15 | 1 | 0 | 0/8,2/4,4/4 |
| 419 | answer16 | ordinary | 8/8 | 5 | 14 | 5 | 0 | 0/8,2/4,3/4 |
| 419 | answer16 | recurrent | 8/8 | 5 | 16 | 1 | 0 | 1/8,1/4,3/4 |
| 733 | uniform | ordinary | 8/8 | 9 | 15 | 1 | 0 | 1/8,4/4,4/4 |
| 733 | uniform | recurrent | 8/8 | 4 | 14 | 2 | 0 | 0/8,2/4,2/4 |
| 733 | answer16 | ordinary | 8/8 | 8 | 16 | 0 | 0 | 3/8,1/4,4/4 |
| 733 | answer16 | recurrent | 8/8 | 5 | 15 | 1 | 0 | 0/8,2/4,3/4 |

All training outputs are exact, EOS-complete, non-malformed and non-repetitive.
Development totals:49/128 exact,121/128 EOS,11 malformed,0 repetitive by the
frozen definition. EOS-only output counts toward EOS completion and also counts
as malformed. A closed wrong inventory value is well formed but not exact.
Repetition means a contiguous one- or two-ID block repeated three consecutive
times; absence of that narrow flag is not a claim of fluent language.

Uniform gets26/64 development answers exact; answer16 gets23/64. Paired changes
are -2,-1,-1,+1 cases (419 ordinary/recurrent,733 ordinary/recurrent).
The change improves exact development accuracy in one of four pairs and lowers
it in three. This tiny correlated development sample supports no significance
or architecture-advantage claim.

All raw continuations, including failures and replays, are in the linked cells:

| Cell | Training raw predictions | Development raw predictions | Training trace/checkpoint metadata |
| --- | --- | --- | --- |
| 419 uniform ordinary | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-419-uniform-ordinary/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-419-uniform-ordinary/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-419-uniform-ordinary/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-419-uniform-ordinary/checkpoint-meta.json) |
| 419 uniform recurrent | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-419-uniform-recurrent/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-419-uniform-recurrent/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-419-uniform-recurrent/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-419-uniform-recurrent/checkpoint-meta.json) |
| 419 answer16 ordinary | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-419-answer16-ordinary/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-419-answer16-ordinary/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-419-answer16-ordinary/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-419-answer16-ordinary/checkpoint-meta.json) |
| 419 answer16 recurrent | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-419-answer16-recurrent/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-419-answer16-recurrent/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-419-answer16-recurrent/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-419-answer16-recurrent/checkpoint-meta.json) |
| 733 uniform ordinary | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-733-uniform-ordinary/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-733-uniform-ordinary/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-733-uniform-ordinary/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-733-uniform-ordinary/checkpoint-meta.json) |
| 733 uniform recurrent | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-733-uniform-recurrent/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-733-uniform-recurrent/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-733-uniform-recurrent/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-733-uniform-recurrent/checkpoint-meta.json) |
| 733 answer16 ordinary | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-733-answer16-ordinary/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-733-answer16-ordinary/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-733-answer16-ordinary/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-733-answer16-ordinary/checkpoint-meta.json) |
| 733 answer16 recurrent | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-train-733-answer16-recurrent/predictions.jsonl) | [raw](../../artifacts/answer-trainability-dev-v1/stages/generate-dev-733-answer16-recurrent/predictions.jsonl) | [trace](../../artifacts/answer-trainability-dev-v1/stages/train-733-answer16-recurrent/training.jsonl), [metadata](../../artifacts/answer-trainability-dev-v1/stages/train-733-answer16-recurrent/checkpoint-meta.json) |

Eight final `.pt` checkpoints remain locally present and git-ignored. Metadata
records exact bytes/hashes; frozen audit strictly reloads weights without fitting
or generating answers. Another checkout lacking these bytes cannot reproduce
that part of the audit merely from metadata.

## Raw examples and failure interpretation

The irrelevant prelude precedes these cores; it is retained in each raw row.

| Split/case and cell | Query core | Gold | Saved generated IDs | Raw continuation |
| --- | --- | --- | --- | --- |
| train-000, all8 cells | `uvo city=la\nuvo city?=` | `la` | `[111,100,2]` | `la` + EOS |
| dev-000, all8 cells | `uvo city=mi\nuvo city?=` | `mi` | `[111,100,2]` | `la` + EOS; wrong training-associated value |
| dev-006,419 answer16 ordinary | `nax city=la\nnax city?=` | `la` | `[2]` | Empty/EOS-only; malformed despite EOS completion |
| dev-008,419 answer16 ordinary | `zim code=R-7\nzim code?=` | `R-7` | `[85,35,117,100,108,64,113,100]` | `R rai=na`, no EOS |
| dev-011,419 uniform recurrent | `zim code=Q_2\nzim code?=` | `Q_2` | `[85,48,58,64,48,62,35,117]` | `R-7=-; r`, no EOS |
| dev-012,733 uniform recurrent | `uvo role=so\nuvo city?=` | `?` | `[111,100,2]` | `la` + EOS; unsupported known value on an unknown |

The all-eight-cell dev-000 behavior directly demonstrates failure to follow a
changed source assignment even though it is in local context. Memorizing
entity/value associations is a plausible explanation: training has only one
city value per entity. The saved outputs do not prove an internal causal
mechanism. Wrong closed answers, EOS-only output, and unfinished code fragments
are distinct failures; permissive scoring would obscure them.

## Losses and measured supervision contributions

These are final-checkpoint teacher-forced NLLs, with the **uniform** token
denominator for comparability across objectives. Answer suffix includes EOS.
Per-document full/history/answer losses and cost are retained in every
`stages/loss-{train|dev}-{cell}/losses.jsonl` and `metrics.json`; these are
distinct from free-generation accuracy.

| Seed | Objective | Model | Train full NLL | Train answer NLL | Dev full NLL | Dev answer NLL |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 419 | uniform | ordinary | 0.081018 | 0.012736 | 0.713062 | 1.165105 |
| 419 | uniform | recurrent | 0.055296 | 0.018631 | 0.696390 | 1.033329 |
| 419 | answer16 | ordinary | 0.084213 | 0.005927 | 0.698842 | 1.091449 |
| 419 | answer16 | recurrent | 0.073495 | 0.008560 | 0.671999 | 1.322392 |
| 733 | uniform | ordinary | 0.056547 | 0.015604 | 0.722762 | 1.328038 |
| 733 | uniform | recurrent | 0.058270 | 0.018396 | 0.738281 | 1.613767 |
| 733 | answer16 | ordinary | 0.068649 | 0.006177 | 0.627984 | 1.030820 |
| 733 | answer16 | recurrent | 0.060616 | 0.007811 | 0.885952 | 1.416763 |

The unique training file has450 targets,24 answer/EOS targets (5.3333%), including
eight EOS targets. Pooled weighted answer mass is5.3333% for uniform and47.4074%
for answer16. Actual batch denominators vary and are logged. EOS is supervised
in both arms. Unlike v1, this local tiny set has no prose/long filler mix and
repeats examples256 times; comparison with v1 therefore does not isolate weighting.

Every training step saves native target IDs, answer offsets, per-target CE,
weighted loss and weighted logit-gradient norm. Actual parameter-gradient
partitions are measured before clipping, including their dot product, combined
norm and projections. The numerical tests compare their sum to direct weighted
CE gradients and the recorded logit norms to autograd. The poststudy audit checks
all target IDs/counts/weights, per-token loss arithmetic, gradient decomposition
and valid logit-gradient bounds from saved CE. Full logits were not saved, so it
does not independently recompute every logit-gradient norm from probabilities.

| Seed | Objective | Model | Answer share of summed update loss | Mean history parameter-gradient L2 | Mean answer parameter-gradient L2 | Mean answer projection on total |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 419 | uniform | ordinary | 8.1242% | 0.265215 | 0.043985 | 0.041094 |
| 419 | uniform | recurrent | 7.6177% | 0.277688 | 0.043983 | 0.040989 |
| 419 | answer16 | ordinary | 40.6635% | 0.185077 | 0.186096 | 0.300778 |
| 419 | answer16 | recurrent | 41.3650% | 0.196814 | 0.199889 | 0.315828 |
| 733 | uniform | ordinary | 8.1324% | 0.269135 | 0.044899 | 0.040207 |
| 733 | uniform | recurrent | 8.5498% | 0.282639 | 0.051072 | 0.050369 |
| 733 | answer16 | ordinary | 38.9808% | 0.186455 | 0.184910 | 0.287418 |
| 733 | answer16 | recurrent | 42.3405% | 0.193476 | 0.204272 | 0.328321 |

Loss shares sum the already normalized H/D and w*A/D contributions over512
updates. Projection is `dot(g_answer,g_total)/||g_total||^2`, averaged by step;
it is not an additive gradient-norm share or percentage of learning. The two
partition norms need not add because of alignment/cancellation. After summing,
the same clipping rule and AdamW are applied in both arms.

Answer share of summed squared **logit** gradient norms changes from7.33–8.03%
to90.53–91.87%; unlike parameter norms, squared logit norms sum across distinct
token positions. EOS contributes1.86–2.36% of summed update loss in uniform,
8.03–10.03% in answer16. Thus the weighting intervention actually changes loss
and gradients, rather than merely recording a nominal coefficient.

The result supports a narrow conclusion:16× answer supervision is unnecessary
for tiny-set overfit at this exposure and is insufficient to meet the frozen
development criteria. It improves training answer NLL in all four pairs but not
development exact accuracy consistently. It does not refute weighting under
other data, budgets, or models.

## Costs, memory, and the failed enclosing receipt

Cold costs below include setup, model construction, checkpoint I/O and the
stage monitor's measured CPU. Training also includes every-step gradient
instrumentation and token trace serialization. Units are seconds; no setup or
diagnostic work is subtracted to imply production efficiency.

| Seed | Objective | Model | Cold fit CPU/wall | Loop CPU/wall | Fit peak private bytes | Dev generation CPU/wall | Dev scoring CPU/wall |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| 419 | uniform | ordinary | 10.265625 /9.597927 | 5.296875 /5.595335 | 672309248 | 4.375000 /3.942012 | 4.390625 /4.004139 |
| 419 | uniform | recurrent | 14.250000 /12.527275 | 8.437500 /8.603375 | 672980992 | 4.390625 /4.071105 | 4.500000 /4.143434 |
| 419 | answer16 | ordinary | 11.390625 /9.916565 | 5.859375 /5.897528 | 672169984 | 4.671875 /4.100305 | 4.500000 /3.941585 |
| 419 | answer16 | recurrent | 14.703125 /12.500474 | 8.562500 /8.611871 | 673562624 | 4.687500 /4.117354 | 4.468750 /3.981474 |
| 733 | uniform | ordinary | 11.875000 /9.933910 | 5.843750 /5.904798 | 672452608 | 4.671875 /4.116651 | 4.468750 /4.010320 |
| 733 | uniform | recurrent | 15.359375 /12.842662 | 8.781250 /8.899632 | 671932416 | 4.609375 /4.051866 | 4.468750 /3.935438 |
| 733 | answer16 | ordinary | 11.312500 /9.683649 | 5.625000 /5.638562 | 672333824 | 4.296875 /4.000512 | 4.484375 /3.960735 |
| 733 | answer16 | recurrent | 15.250000 /13.070821 | 8.921875 /8.951987 | 672202752 | 4.781250 /4.285531 | 4.718750 /4.100654 |

Per-cell cold training/training-generation/training-scoring/development-generation/
development-scoring costs, all corresponding peaks, and warm request costs are
available without rounding in the
[diagnostic summary](../../artifacts/answer-trainability-dev-v1/diagnostic-summary.json).
It retains the captured commands and CPU scopes; limits and worker receipts are
stored in each stage's `cost.json`/`worker.json`. All individual stage resource,
finite-state, checkpoint-identity and replay checks passed.

| Scope (disjoint within stage ledger) | CPU seconds | Wall seconds |
| --- | ---: | ---: |
| Eight cold fits | 104.406250 | 90.073283 |
| Eight training-generation stages,72 requests | 33.781250 | 31.987876 |
| Eight training-loss stages | 33.625000 | 31.660753 |
| Eight development-generation stages,136 requests | 36.484375 | 32.685336 |
| Eight development-loss stages | 36.000000 | 32.077780 |
| Sum of40 nested stages | 244.296875 | 218.485028 |
| Pre-freeze contracts, separate | 5.046875 | 6.578166 |
| Preparation/freeze, separate | 4.125000 | 4.251627 |

Warm generation CPU/wall across all208 requests is0.765625 /0.830234 seconds,
a subset of the cold generation stages. Tiny-request CPU is quantized by the
Windows process clock; a near-zero individual measurement is not free work.
Cold initialization dominates these short continuations.

Maximum individual model-stage private peak673,648,640 bytes; enclosing sampled
process-tree peak693,628,928. Freeze/private peak738,996,224 and contract peak
699,404,288 are separate preparation scopes. Registered logical disk peak
72,501,730 bytes. All recorded request/worker durations, memory, disk and sampling
gaps are below their numerical caps. These are OS/sampling measurements, not
tensor-state capacity or energy measurements. No hardware-stable efficiency
claim follows from one small run.
Maximum recorded monitor gap0.132231 seconds; maximum generation/loss request
CPU or wall0.030250 seconds.

The [outer receipt](../../artifacts/answer-trainability-dev-v1/execution/cost.json)
reports219.009071 wall seconds,293.828125 sampled CPU seconds and statusSTOP.
The controller's `run` branch omitted `worker_receipt`; the same source writes
receipts for each model worker. Consequently the outer watcher cannot reconcile
the controller's final lifetime CPU/OS peak. Its sampling also does not reconcile
every descendant's final receipt. The raw outer CPU is not a complete total.

[Separate accounting](../../artifacts/answer-trainability-dev-v1/poststudy-accounting.json)
preserves this rather than replacing the receipt:244.296875 nested-stage CPU
(already including55.218750 controller-monitor CPU), plus0.062500 measured
controller CPU outside those snapshots, plus55.750000 outer-monitor CPU gives
**at least300.109375 CPU seconds** in disjoint recorded scopes. Full lifetime CPU
remains unknown. Do not add55.281250 total controller CPU to the nested stages
again; most of it is already charged there. Do not add the enclosing sampled
CPU to those stages. The outer wall interval already encloses all stages.

No cap was raised, failure receipt rewritten, missing receipt fabricated, or
training/generation repeated. The formal registered envelope remains invalid
even though its sampled values are far below numeric limits and quality failed
independently. Design/editing, diagnosis review and other uninstrumented work
have unknown CPU; neither this ledger nor stage sums are full project cost.

## Offline validation and reproducibility

The [study implementation](../../scripts/answer_trainability_dev.py) supports a
repeatable **read-only** `audit` command. The independent
[poststudy audit](../../artifacts/answer-trainability-dev-v1/poststudy-audit.py)
verifies all raw answers, native prompts, source/data seals, matching exposure
and initialization, per-token weighting arithmetic and gradient partitions.
It explicitly reports `envelope_valid=false`; evidence validation does not
upgrade the failed resource envelope.

```powershell
Set-Location D:\Toruk
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git show --stat --oneline 39c4e4756b24ca3d09c4a9aa8ae63b1a2b5ab208
.\.venv\Scripts\python.exe -B scripts/answer_trainability_dev.py audit
.\.venv\Scripts\python.exe -B artifacts/answer-trainability-dev-v1/poststudy-audit.py
.\.venv\Scripts\python.exe -B artifacts/answer-trainability-dev-v1/verify-report.py
.\.venv\Scripts\python.exe -B artifacts/segment-delta-dev-v1-commit-review-001/review.py --revision HEAD --inspect-checkpoints
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m mypy --platform linux
.\.venv\Scripts\python.exe -B scripts/check_frozen_sources.py
git diff --check
git status --short
```

The historical freeze, single-use `run`, and per-worker commands are archived
in their cost receipts. Do not rerun them. Both audit commands perform no study
fit, optimizer update, or answer generation. The frozen audit reloads local
checkpoint weights. The poststudy audit is stdlib-only and uses saved evidence.

[Focused tests](../../tests/test_answer_trainability_dev.py) cover split/label
validation and placement, strict scorer behavior, declared parameter counts,
teacher-forced/session alignment, future-answer isolation, and equivalence of
partitioned parameter/logit gradients to direct weighted CE. Before freeze,
all6 passed without optimizer updates or generated study answers. Later scoped
verification ran those6 plus12 existing numerical tokenizer/model/stream/memory
tests: **18 passed**. Existing tests that fit old studies, load case datasets,
or invoke unfiltered research/held-out runners were excluded explicitly.

Verification attempt001 exceeded its90-second mypy subprocess timeout after
the earlier six checks had passed; its complete
[failure log](../../artifacts/answer-trainability-dev-v1-checks-001/monitor/output.log)
and [cost](../../artifacts/answer-trainability-dev-v1-checks-001/monitor/cost.json)
remain. Recorded CPU63.546875/wall105.899075 seconds, sampled private peak
1,141,469,184 bytes, statusSTOP. The timed-out process was not left running.
The check wrapper also placed its final receipt outside the monitor directory;
the second verification wrapper corrects that path. These are verification
changes, not changes to any frozen study source or training/evaluation budget.

Verification attempt002 used240 seconds per check and a600-second enclosing
check budget. All10 checks passed: frozen study audit, independent evidence
audit, historical segment-delta evidence review,18 focused tests, repository
Ruff lint/format, Windows and Linux-target mypy (38 source files each), three
frozen-source hashes and `git diff --check`. See its
[explicit coverage and commands](../../artifacts/answer-trainability-dev-v1-checks-002/coverage.json),
[monitor receipt](../../artifacts/answer-trainability-dev-v1-checks-002/monitor/cost.json),
and [output](../../artifacts/answer-trainability-dev-v1-checks-002/monitor/output.log).
Recorded CPU131.375000/wall116.313669 seconds, peak private1,578,860,544 bytes,
statusPASS. Verification is outside the registered study ledger; monitor CPU
figures are measured scopes, not a complete lifetime project total. There was
no repeat training or generation. No full-suite, web/deployment or hosted CI pass
is claimed. Report/link/table validation and final whitespace checks are
additional read-only checks.

Final HEAD remains the diagnosis commit; no new changes are staged. The sole
tracked modification is an append to `.gitattributes` that preserves raw bytes
and source line endings for this new study. Untracked additions are the new
protocol/results, study script and numerical tests, plus the study, preflight,
preparation and both verification artifact directories. All existing work is
preserved and nothing was pushed. The [final artifact inventory](../../artifacts/answer-trainability-dev-v1/artifact-inventory.json)
includes hashes and sizes, including locally ignored checkpoints; it does not turn missing
checkpoint bytes in a future checkout into reproducibility.

## Limitations and next action

This is a tiny, deliberately local, synthetic task with shared names, grammar
and seven answer strings. Each entity has just one city assignment in training;
training accuracy can be achieved by memorization. Development recombination
exposes that limitation but does not establish which computation was learned.
Sixteen correlated cases and two seeds do not measure broad generalization or
conversational competence. No natural-language/prose quality gate was part of
this narrowly registered study. The two model configurations differ in width
and actual compute. Final-only evaluation does not measure steps-to-overfit.

Compared with segment-delta-v1, context, placement, training repetition, dataset
mix and gradient instrumentation all differ. Only the two objectives **within
this new study** form the predeclared supervision comparison. The results cannot
attribute v1's zero solely to weighting or justify a memory architecture claim.
The failed enclosing receipt independently prevents formal advancement.

**One next action: register a new local-answer generalization study with multiple
training values per entity and corrected controller accounting.** Keep memory
comparisons deferred. This is a recommendation, not an executed protocol change:
v1 remains stopped, and no additional training is authorized by this report.
