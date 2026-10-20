# Experiment registry

## foundation-001 — ordinary-LM prerequisite, validation only

Run date: 2026-10-19 (Asia/Calcutta). Base commit:
`334fe510780bda7b622ae7821a970c40d9f7dd2a`, uncommitted changes.
Source file hashes per command are in `artifacts/checks/*.json`; the final source
snapshot, source fingerprint, environment and artifact hashes are in
`artifacts/foundation-001/{source.zip,environment.txt,manifest.json}`.
Checkpoints are retained locally but ignored by Git. No commit/push or paid
compute was used. Exact command arrays and wall times are in the check records;
the full former README with reproduction instructions is preserved separately
outside this Git working tree. Run `python scripts/verify.py` for local CI equivalents.

Hardware: AMD Ryzen 5 5600G, 6 cores / 12 logical processors; AMD Radeon integrated
graphics, Windows 11. Python 3.12.14, PyTorch 2.14.1+cpu. CUDA is unavailable in
the installed build; this does not inventory every possible hardware backend.
Windows CIM initially denied access in the sandbox; the approved read-only retry
identified CPU/display hardware. RAM and CPU allocator peak are not reported.

The two-step profile took 0.02034 seconds of optimizer-loop time (~17,307 valid
tokens/s). Only after profiling, the budget was selected: 80 optimizer steps,
batch 4, context 64, width 32, heads 4, layers 2, float32, one CPU thread, AdamW
LR 0.003, seed 23. The command wrapper enforces a 120-second timeout. CLI startup
and full command wall times are retained separately; no long job was launched.

Dataset: deterministic prose **smoke fixture**, seed 17, 60 documents, split
48/6/6 by document. It is not the required controlled-world benchmark or oracle.
Train SHA256 `c935a64824e4456f8fb76d544ce58a5102210df521cb55ebd860336399462286`;
validation SHA256 `8f5bb8d6ca2ad960d20063735a47883bd5637cacc30f04c0592d0c4c27963b06`.
Exact bytes/fingerprints are retained in `data/`; generation fingerprints all
splits, but final test documents are never loaded for model training/scoring.

| Measurement | Observed |
| --- | ---: |
| Parameters | 44,096 |
| Recurrent state bytes | 0 (ordinary model) |
| Valid training targets over 80 steps | 16,312 |
| Optimizer-loop time including batching/finite checks | 0.59391 s |
| Training throughput | 27,465 valid tokens/s |
| Full training CLI process wall time | 4.48263 s |
| Reloaded validation loss | 1.248108 nats / byte-or-EOS token |
| Validation scored targets | 925 |
| Reloaded validation loss computation | 0.01166 s |
| Generated continuations | 6 × 32 tokens = 192 tokens |
| Prefix-tokenization + local recomputation + decode time | 0.18086 s total |
| Mean continuation latency | 30.14 ms |
| Generated-token throughput | 1,061.6 tokens/s |
| Full evaluation CLI process wall time | 4.69564 s |
| Peak allocated memory | NOT_RUN; CPU allocator peak instrumentation absent |

`train/metrics.json` retains all step losses and gradient norms.
`eval/predictions.json` retains prefixes, generated token IDs/text, separate
reference suffixes, observed-history length, retained local-context length and
per-example timing. The model receives no gold suffix during generation.
`eval/metrics.json` retains reload checkpoint SHA256 and scoring/timing data.
Loss is from nonoverlapping document windows; generation uses a rolling local
context with positions restarted. These are explicitly distinct protocols.

Limitations: extremely small, templated corpus and short run. Generation is
repetitive (e.g. "The The The"). Lower teacher-forced loss is not evidence of
factual recall, unknown handling, or useful text quality. No memory model was
trained, so memory benefit, corrected/unchanged-fact accuracy, distance curves,
answer coverage, saturation, reset ablation and full recurrent-history timings
are **NOT_RUN**. There is no factual QA accuracy to report. The ordinary LM
tokenizes the entire prefix but retains only 64 tokens for inference; its
context size is never reported as the number of input tokens read.

## Verification and remote CI

Each recorded check has PASS/FAIL/NOT_RUN/BLOCKED status, exact command or tool
request, base revision/source fingerprint, and evidence path. See
`artifacts/checks/` and `artifacts/audit.json`. Initial lint/type failures are
retained alongside corrected final checks. The installed PyTorch emits an
optional NumPy-absent warning; no exercised operation needs NumPy.

Remote base commit was verified through GitHub. The commit-workflow connector
returned `workflow_runs: []` for exact base SHA, but only supports the first page
of pull-request-triggered runs. This is not proof that all Actions are absent.
The new CPU workflow is uncommitted and has **NOT_RUN remotely**. Local Windows
checks cover its install/import/help/diagnostics/lint/format/types/tests/build
commands; Ubuntu runner behavior remains unverified. No remote pass is claimed.

Final local results: **PASS** editable installation, dependency/import checks,
CLI help/diagnostics, Ruff lint/format, mypy (7 source files), pytest (**9 passed**,
including subprocess CLI integration and bitwise checkpoint-resume equivalence),
sdist/wheel build and whitespace check. All 11 local CI-equivalent commands
passed. Initial lint/type **FAIL** records remain under `initial-*` and were
corrected without weakening assertions. Final source hashes are recorded per
check. Remote verification of this uncommitted code remains **NOT_RUN**.

M3 status: **BLOCKED at the missing-prerequisite gate**. The ordinary LM
foundation is implemented. M2 is the next dependency; M3's proposed memory
contract is documented, with implementation and measured comparison outstanding.

## m4-prerequisite-001 — gate audit, not an M4 experiment

Date: 2026-10-20 (Asia/Calcutta); clean starting `main`, base commit
`a025f0148965089b24a69344a13cd8a6447afef9`. The implemented package still has no
M2 controlled-world oracle or M3 recurrent model. M4 is **BLOCKED**. The only
model run was a fresh CPU reproduction of the ordinary foundation: two profiling
steps then 80 optimizer steps, same frozen training/validation bytes and seeds.
No final test data were scored. No branch labels or effect-predictor metrics exist.

Fresh validation loss: **1.2481076462 nats/byte-or-EOS**, 925 targets; 44,096
parameters; zero recurrent-state bytes. Training processed 16,312 targets in
1.2789348 s; full CLI 6.7532724 s. Six 32-token continuations took 0.6344207 s
including prefix tokenization and local recomputation; full evaluation CLI
7.2044330 s. These repetitive continuations are not factual recall results.
Hardware: i5-12450H, 12 logical CPUs, 16,831,897,600 bytes RAM, RTX 3050 Laptop
present but CPU-only PyTorch used; Python 3.14.6, Torch 2.14.1+cpu, one thread.
This differs from the foundation-001 machine. No cross-machine speed claim.

Local install/package/import/help/diagnostics/lint/format/types/tests/build passed;
pytest reports 9 passed, zero skips. All new check records use `m4-gate-` labels
to preserve prior evidence. Remote push CI for this exact base commit passed
([run](https://github.com/ShamGaneshan2008/Toruk/actions/runs/39294787042)); remote
checks of local edits remain NOT_RUN. New checkpoint files are retained locally
under the existing Git ignore rule. No commit/push or paid compute was used.

See [full gate report](research/m4-prerequisite-audit.md) for commands, costs,
coverage gaps and evidence paths; `artifacts/m4-prerequisite-001/` contains fresh
configurations, raw predictions, metrics, hardware, environment and handoff manifest.
The [related-work comparison](research/related-work.md) rejects novelty claims for
paired counterfactual evaluation. The [M4 draft](research/m4-effect-predictor.md)
is conditional on establishing the absent benchmark and recurrent interface.

## M5 prerequisite audit — no model experiment

2026-10-20 (Asia/Calcutta), same `main` HEAD
`a025f0148965089b24a69344a13cd8a6447afef9`, preserving existing local M4 edits.
Current source identity matches the prior verified snapshot; all 49 prior sealed
evidence/document files matched before this handoff was appended. M4 still lacks
runnable branch generation, a predictor, recurrent model and controlled-world
oracle. **M5 BLOCKED** under the request's prerequisite stop rule.

No revision training, branch generation or final-test evaluation was run; all
correction/preservation metrics and comparisons are NOT_RUN. The prior 9 passing
foundation tests and exact-commit remote foundation CI remain prior evidence,
not M5 tests/results. Fresh CLI and whitespace evidence uses `m5-gate-` labels.
See [M5 handoff](research/m5-prerequisite-audit.md) for acceptance gaps,
reproduction limits and evidence needed before M6; machine-readable audit is
`artifacts/m5-prerequisite-audit.json`. No commit/push or paid compute.

## m6-validation-001 — prerequisite implementation and negative comparison

2026-10-20 (Asia/Calcutta), `main`, base
`a025f0148965089b24a69344a13cd8a6447afef9`, uncommitted source; prior edits and
evidence preserved. Missing M2–M5 prototype code was implemented and tested.
Frozen protocol: four worlds/split, seed 23, generator seed 17, 12 steps/model,
two 2-step CPU profiles, 16-token greedy answers, one thread, 110-second driver
budget, 120-second outer timeout. Final test was not opened/scored.

All 14 configurations scored **0% corrected/preserved known-fact macro accuracy**.
Ordinary overall accuracy was 33.3%, solely from `?` on every question. Recurrent
overall accuracy was 8.3%, recurrent+predictor 12.5%, revision variants 0%; nonzero
scores come only from uncertain probes. Both predictors retained the final write
on all validation worlds due to out-of-support features. Revision predictor
regret (0.000513 nats) was worse than heuristic (0.000117). No learned benefit.

Registered cost: 100 LM steps including profiles / 101,256 training forward-token
positions; 32 branches / 13,066 label forward positions / 107,808 generated-branch
forward positions; 200 predictor steps. LM loop 16.981 s, labels 25.285 s,
predictor fitting 0.380 s. Driver 87.341 s, full process 90.935 s. Cumulative
process peak 352,514,048 bytes (336.18 MiB), including framework/all stages.
CPU-only Torch 2.14.1, Python 3.14.6, 12 logical CPUs, Windows 11.

Retained failed integration pilot `artifacts/m6-failed-tiny-001` ended at a
checkpoint/evaluation directory collision, fixed before registration: additional
6 LM steps / 8,344 forward positions / 8 branches / 100 predictor steps,
9.090 s stage wall time. No metric-driven retry. Test/failed-check timing records
are retained; test training-token totals are incomplete. No CPU-hour total claim.

Local PASS: 24 tests, zero skips, lint/format, types, dependencies/package,
help/diagnostics. Initial FAIL records retained. Exact existing-HEAD remote CI
passed; unpushed code is NOT_RUN remotely. Raw answers, configs, hashes and logs
are retained. See [protocol/commands](research/m6-validation-protocol.md),
[results/limitations](research/m6-results.md), and `artifacts/m6-analysis.json`.
M6 is **PARTIAL**, with final test, multiple seeds and full resource matching
outstanding. No commit, push or paid compute.

## m7-templates-001 / m7-load-001 — exploratory failure persistence

2026-10-20, same `main` base `a025f0148965089b24a69344a13cd8a6447afef9`,
uncommitted working tree. Prerequisite `m7-m6-replay`: fourteen frozen M6
comparisons, 336 answers reproduced exactly, 32.417 s full command. M6 remains
an incomplete negative pilot with no matched-total-compute or final-test claim.

Frozen studies use four new anchors (two each from data seeds 117/118), training
seed 23, 16-token greedy answers, no new fitting. Templates: 3 cells × 5 methods,
360 answers, 32.845 s command. Load: 5 cells × 6 methods, 720 answers, 62.045 s.
All 45 evaluations have 0% known-fact macro accuracy separately on both data
seeds; descriptive seed SD zero, training-seed uncertainty unavailable. Ordinary
33.3% overall comes only from abstention. Revision predictor falls back 32/32;
no learned advantage. At 649–1,066 tokens, 6–20 known facts and 2/4/8 slots,
capacity onset is unidentifiable at the predeclared learning floor.

Inference positions: 285,240 / 564,996; separate offline scoring: 26,232 / 46,170.
Process peaks: 311,234,560 / 313,155,584 bytes, cumulative framework-inclusive.
No new study training; inherited M6 costs and initial failed checks remain recorded.
No failed study stages, exclusions or favorable-score retries. Test-token totals
remain incomplete. Dataset/protocol/checkpoint hashes and all raw predictions,
per-seed strata and costs are retained; 204 study manifest entries independently
verified. Local 28 tests/zero skips and CI equivalents PASS, old exact-HEAD remote
CI PASS, current edits NOT_RUN remotely, final test NOT_RUN.

**M7 PARTIAL**. See [protocol and reproduction commands](research/m7-protocol.md),
[results, failure examples and M8 requirements](research/m7-results.md),
`artifacts/m7-analysis.json`, and `artifacts/m7-handoff`. No commit, push,
publishing, new branch or paid compute.
