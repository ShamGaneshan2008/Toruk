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
