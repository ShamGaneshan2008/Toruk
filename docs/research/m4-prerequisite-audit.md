# M4 prerequisite audit and handoff

Date: 2026-10-20, Asia/Calcutta. Audited branch `main`, initially clean, HEAD
`a025f0148965089b24a69344a13cd8a6447afef9`. Repository and ancestor instructions
were searched; no AGENTS.md was found. Read README, all package modules, tests,
workflow, local verification scripts, milestone/architecture/research notes and
retained foundation configurations, manifests, training metrics and predictions.
The only local research specification was the explicitly proposed M3 contract;
no implemented controlled-world benchmark or longer research specification exists.

## Gate outcome: BLOCKED

The actual implementation is an ordinary causal decoder. This finding does not
depend on README/milestone assertions: `CausalLM.forward(tokens)` returns logits
only; its modules are embeddings, self-attention, MLP, normalization and output
projection. There is no memory reader, writer, state argument or state return.
`training_batch` shuffles independent windows; `engine.train` performs one step
per batch without ordered document lanes, unrolled memory or TBPTT. Generation
recomputes a bounded token suffix with no streaming session. Checkpoint loading
accepts only `toruk-ordinary-v1`. The data generator emits prose journals with
string IDs/text and no events, probes, correction semantics or independent oracle.

M2 and the whole M3 implementation/evaluation are missing, rather than a small
correctness repair in an existing memory baseline. There is no existing M3 state
interface or frozen controlled-world scoring protocol to reuse for M4. Establishing
these requires the prior benchmark and recurrent-model milestones, including a
new training comparison; adding a speculative writer/predictor would bypass the
requested verification gate. This task therefore follows the request's blocked
handoff path. No M4 labels, predictor, runtime recommendations or M5 code were
added. No foundation correctness failure was found by the checks below; no model
fix is claimed. A blocked prerequisite is not an experimental null result.

| Required M3 behavior | Status | Actual evidence / missing acceptance evidence |
| --- | --- | --- |
| Recurrent LM trains and generates | BLOCKED | Fresh ordinary training/reload/generation PASS; no recurrent model exists |
| Bounded memory and document reset | BLOCKED | Ordinary run reports zero recurrent-state bytes; zero state is not proof of a bounded working memory |
| Future text cannot affect earlier predictions | PASS for ordinary LM only | `test_future_tokens_cannot_change_earlier_logits`; no recurrent causal test available |
| Writes cannot affect their own segment | BLOCKED | No writer or update timing to test |
| Batch and inference-session state isolation | PASS for stateless ordinary model only; M3 BLOCKED | Padding/batch perturbation and repeated generation tests; no stateful sessions |
| Writer receives meaningful gradients | BLOCKED | Ordinary attention/embedding gradients PASS; writer parameters absent |
| Save/load and documented resume | PASS for ordinary model only; M3 BLOCKED | Bitwise model/optimizer/RNG equivalence and mismatch rejection; recurrent checkpoints explicitly unsupported |
| Reproducible matched baseline comparison | BLOCKED | Ordinary prose-smoke loss reproduced; no recurrent checkpoint, controlled-world QA or matched comparison |

## Fresh bounded foundation verification

Evidence directory: `artifacts/m4-prerequisite-001/`; command/output/source records:
`artifacts/checks/m4-gate-*.{json,log}`. Existing evidence was preserved. Every
wrapped command has a 120-second timeout. Two CPU profiling steps preceded the
80-step budget. Training used seed 23, batch 4, context 64, width 32, heads 4,
layers 2, float32, one thread, AdamW LR 0.003. Frozen fixture seed 17; 48 training
and 6 validation documents. Final test contents were not opened for scoring or
model selection. The existing fixture is not a replacement for M2.

Hardware was detected afresh: Intel i5-12450H (8 cores / 12 logical processors),
16,831,897,600 bytes system RAM, Intel UHD and NVIDIA RTX 3050 Laptop displays.
Python 3.14.6, PyTorch 2.14.1+cpu, CUDA unavailable in this build. Hardware and
package versions are retained; this differs from the prior experiment's machine.
An isolated `.venv` was created because the earlier environment was not present.
The checkout also lacked the prior ignored `.pt` files, so the new checkpoint was
trained rather than pretending the archived metrics proved reload behavior.

| Fresh measurement | Observed |
| --- | ---: |
| Model parameters | 44,096 |
| Recurrent-state storage | 0 bytes (ordinary model) |
| Profile: valid targets / optimizer-loop time | 352 / 0.0623804 s |
| Train: valid targets / optimizer-loop time | 16,312 / 1.2789348 s |
| Training throughput | 12,754.36 valid targets/s |
| Full train CLI wall time | 6.7532724 s |
| Reloaded validation loss | 1.2481076462 nats per byte-or-EOS token |
| Validation targets | 925 |
| Reloaded validation-loss time | 0.0336031 s |
| Generated tokens | 192 (6 x 32) |
| Prefix tokenization + recomputation + decode | 0.6344207 s total; 105.74 ms mean/example |
| Generated-token throughput | 302.64 tokens/s |
| Full evaluate CLI wall time | 7.2044330 s |
| Peak process/allocator memory | NOT_RUN; no instrumentation in the existing runner |
| M4 labels / predictor training / policy baselines / uncertainty | NOT_RUN; prerequisite gate BLOCKED |

Checkpoint SHA256:
`799a359e7a71ff7c37d7806ff64a654161d3506ccd41d8c76d78d43f8de96ab8`.
Train SHA256:
`c935a64824e4456f8fb76d544ce58a5102210df521cb55ebd860336399462286`.
Validation SHA256:
`8f5bb8d6ca2ad960d20063735a47883bd5637cacc30f04c0592d0c4c27963b06`.
Per-command source fingerprint:
`9df6808d9a8d8b753ebc0f7159ffbf104d9117ef2463810fb664b4be27236b39`.
It hashes checkout bytes (including Windows line endings); it need not equal the
previous machine's archive fingerprint. The handoff manifest additionally hashes
the changed research documents, evidence and locally retained checkpoints.

Raw predictions show repetitive text such as "The The The". These continuations
are not factual answers. No recall, correction, coverage, saturation or predictor
benefit can be inferred. Timing is single-run and some checks ran concurrently;
these numbers are reproducibility smoke measurements, not a speed comparison.
Explicit standalone training cost was 82 steps / 16,664 valid targets including
profiling. Test-suite training also ran; its wall time is recorded but its token
total is not instrumented. No failed model pilot occurred. Package setup/download
and human/tool research time are outside model-loop timings; no total CPU-hours
or total experiment token accounting is claimed.

## Reproduce the actual run

Use the installed environment and fresh destinations. These are foundation
commands; there is no executable M4 pilot to reproduce. Prefix each command with
`python scripts/check.py UNIQUE_LABEL --` to retain a bounded command record.

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m toruk_lm diagnose
.\.venv\Scripts\python.exe -m toruk_lm train --train artifacts/foundation-001/data/train.jsonl --validation artifacts/foundation-001/data/validation.jsonl --output artifacts/m4-gate-reproduction/profile --steps 2
.\.venv\Scripts\python.exe -m toruk_lm train --train artifacts/foundation-001/data/train.jsonl --validation artifacts/foundation-001/data/validation.jsonl --output artifacts/m4-gate-reproduction/train --steps 80
.\.venv\Scripts\python.exe -m toruk_lm evaluate --checkpoint artifacts/m4-gate-reproduction/train/checkpoint.pt --data artifacts/foundation-001/data/validation.jsonl --output artifacts/m4-gate-reproduction/eval --max-new-tokens 32
.\.venv\Scripts\python.exe -m pytest -q
```

## Local and remote checks

Local PASS: editable install with no dependency/build isolation; `pip check`;
package import; `python -m toruk_lm --help`; `diagnose`; `ruff check .`;
`ruff format --check src tests scripts`; `mypy` (7 package files); `pytest -q`
(9 passed, no skips); and `build --no-isolation` (sdist and wheel). Exact commands
and logs have the `m4-gate-` prefix. Whitespace and installed console-entry checks
are recorded separately with that prefix. The tests exercise ordinary causality,
batch separation, masking/shift, gradients, deterministic fixtures, exact resume
and a real subprocess make-fixture/train/evaluate/generate flow. They do not test
an M3 or M4 implementation. The optional NumPy-absent warning was retained.

Remote PASS for exact existing commit
`a025f0148965089b24a69344a13cd8a6447afef9`:
[CPU foundation, push run 39294787042](https://github.com/ShamGaneshan2008/Toruk/actions/runs/39294787042).
The read-only REST request was
`GET https://api.github.com/repos/ShamGaneshan2008/Toruk/actions/runs?head_sha=a025f0148965089b24a69344a13cd8a6447afef9&per_page=100`;
response retained in `artifacts/m4-remote-runs.json`. The GitHub connector's
PR-only workflow wrapper returned no runs; the direct request found the actual
push run. No workflow was triggered. New local documentation/evidence is
uncommitted and unpushed; remote validation of these edits is **NOT_RUN**.

## Research handoff

[Related work](related-work.md) records all five requested primary papers and
narrows the claim. [Conditional M4 protocol](m4-effect-predictor.md) separates
deployable inputs from future-only labels and defines candidate operations,
cache identities, metrics, controls, costs and planned tests. It remains a draft
until M2 scoring and the real M3 interface are verified.

Next prerequisite: implement/independently validate the controlled-world event
generator, world/document splits, oracle and autoregressive factual scorer, then
train and measure an ordinary baseline on that benchmark. Next establish M3's
read/write state interface, ordered training/TBPTT, resets/isolation, safe resume
and a matched-budget validation comparison with raw predictions. Only then can
M4 generate valid paired labels and test the predictor hypothesis. The complete
M3 contract is in `m3-memory-contract.md`.

Before M5, answer whether M3 learned useful delayed memory, whether retain/write
effects are identifiable and sufficiently variable, whether validation calibration
and policy decisions beat the heuristic, and whether measured total cost warrants
the controller. M4 status is **BLOCKED**, not complete or a demonstrated null result.
No commit, push, publication, tag, visibility change or paid compute was performed.
