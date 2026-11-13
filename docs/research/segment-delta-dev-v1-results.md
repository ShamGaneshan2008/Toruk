# Segment delta development v1: negative feasibility result

13 November 2026. **NO-GO at both seeds. Stop this mechanism at this version.**
All six fits and the fixed development matrix completed within their ceilings.
The candidate and both matched LMs answered zero factual questions exactly;
the separate lexical grammar control answered all 24. Delta used more training
and inference CPU/wall than the recurrent control. No held-out evaluation,
quality-driven retry, checkpoint selection, prompt repair or production change.

## 1. Starting and final Git state

Root `D:/Toruk`, branch `main`, HEAD and local `origin/main`:
`ab6d3a65538b5f33d17efe4f45189906f1394a38`. Initial status was
`## main...origin/main` plus only the pre-existing untracked
`docs/research/toruk-custom-lm-architecture-decision-v1.md`. That draft remains
byte-identical, SHA256
`cd57eef6d1fb1b8ab66c71a3c40f0f09cc02a9b3afe3dde6aca3de44e9784d23`.
The saved `preflight.json` was written after the new v2 ADR, so its status also
lists v2; it is not a literal receipt of the earlier first status command.

Final HEAD/branch unchanged; no tracked file was edited. All additions remain
uncommitted for review. The machine-readable final status and file inventory
are in `artifacts/segment-delta-dev-v1/final-git-state.json` and
`artifact-inventory.json`. No fetch was needed for this pinned local study;
remote freshness is unknown. Nothing was pushed, deployed or published.

## 2. Architecture and what changed

The [v2 decision](toruk-custom-lm-architecture-decision-v2.md) locates the existing
ordinary, recurrent and owned next-token LMs, conditional integrated LM,
external Qwen chat backbone, selectors and deterministic answer policy. The
pretrained backbone supplies chat language ability; this experiment uses none
of its weights, tokenizer or answer policy. M6 remains nonreproducible and all
earlier negative findings remain unchanged.

New `SegmentDeltaLM` carries S[8,8], reads it through learned normalized queries
inside a causal local transformer, and writes learned key/value associations
with `S <- S + beta*k*(v-S^T*k)^T`. Current-segment logits read only the entering
state; the ordered writer commits after a full segment. Full-document next-token
loss backpropagates across segments. Updates see only consumed token hidden
vectors, never evaluator labels, entity tables, retrieval or source offsets.
Partial-prefix recomputation does not commit provisional updates. Documents
reset; clone/isolation, padding and exact resume have numerical tests.

This replaces the existing segment-mean slot update and cross-attention reader
with a different neural computation. It adapts the known
[fast-weight delta rule](https://proceedings.mlr.press/v139/schlag21a.html);
[Gated Delta Networks](https://arxiv.org/abs/2412.06464) already studies delta/local
attention hybrids. It is not a novel memory rule or a renamed context selector.
The ADR also compares RMT, compressed memory, selective state-space and RECOMP
primary research. No global or IEEE novelty claim.

Existing `CausalLM` and `OwnedMemoryLM` implementations and checkpoint loaders
are unchanged. Width/FFN allocation differs to match active parameter counts;
this compares whole configurations, not the writer equation alone. All models
use the same nonoverlapping segment schedule, including ordinary inference;
this is not a comparison against an optimized rolling-window/KV-cache baseline.

## 3. Frozen protocol, data and caps

The [protocol](segment-delta-dev-v1-protocol.md) was frozen before prototype
implementation or study training. Sources were sealed after contract tests and
before any study fit or answer. Both seals remain unchanged:

| Identity | SHA256 |
| --- | --- |
| Registration | `bb828757efe6f4073d7d1c74405aa7c73120e11fcfdfff6c09b8a95812e1d2dd` |
| Implementation lock | `8711afee882f4e4837e4048a878447c1d1706220ca72faa7ed5270c07e878984` |
| Training file | `b4cc4a2761a4886a7190d4f824c46a5cc04cfc54d5016edba43cb6255e71f3df` |
| Development inputs | `e499c01db31deb74ca8ccb81aa0e7e0edb92d0228d530e953f465fa1c5ab3fce` |
| Evaluator-only labels | `5bf8856568194c8d0f8ae1f68250a65125c519801bd22a41e164c579d43e09a3` |
| Development prose | `47807cf9edae3e96077b8086352bd2b4e1b9efb23fa2355768a0e15ad3393fba` |

Per-case hashes and full source maps are in `implementation-lock.json`;
protocol/runtime/tokenizer/config/order/caps are in `registration.json`.
Runtime: Python3.12.14, Torch2.15.0+cpu, psutil7.2.2, float32 deterministic CPU,
one Torch thread. Unchanged fixed259-ID byte tokenizer; local context/segment24,
maximum192 targets (actual train maximum178). Ordinary13,914 parameters;
recurrent14,288; delta14,277. Both recurrent states256 bytes; local token buffer
at most192 tensor bytes, with Python/container overhead additional.

Training160 fresh documents (128 factual,32 prose), development24 factual
and8 prose; no held-out split or old case/checkpoint input. IDs and complete
texts are disjoint, but entities/grammar/finite values are shared: synthetic IID,
not generalization. Training/dev generator seeds831107/831109; fit seeds113/227.
Labels are authored by the generator and checked by a separate last-assignment
source check, not independently human adjudicated. Generation workers open no
label file; teacher-forced gold scoring runs in separate later evaluator workers.

Each fit uses 128 AdamW steps, batch 2 complete documents, lr .003, betas (.9,.999),
eps1e-8, weight decay.01, clip1.0, foreach/fused disabled. Uniform byte/EOS CE,
full-document BPTT, identical document order and targets per seed/cell. Shared
shaped backbone tensors share initialization. Final step only; no pretrained
weights. New strict format `toruk-segment-delta-dev-v1` stores drained optimizer
boundaries, optimizer/RNG/cursor and source/data/runtime identities.

Greedy decoding, suppress PAD/BOS, EOS stopping,8-ID cap; exact gold bytes then
EOS required. Unknown accepts only `?`. No trimming, repair or relaxed scoring.
Ten model/ablation workers and one lexical worker each make24 requests plus
first-case replay:275 requests,264 scored outputs,24 unique questions. Ten
additional workers compute losses. Study order matches registration exactly.

Fixed caps:150 CPU/wall seconds per fit,20 per generation/loss worker,
1.5 per request/loss document,1500 overall,2GiB process-tree private memory,
128MiB run disk,50ms polling and maximum5s observation gap. No caps were raised.

## 4. Commands and retained attempts

Exact stage commands are preserved in every `cost.json`; sources and executable
preparation scripts are saved under the run directory. Windows PowerShell
commands used, in order (historical commands, **do not rerun this registration**):

```powershell
Set-Location D:\Toruk
.\.venv\Scripts\python.exe scripts/segment_delta_watch.py --directory artifacts/segment-delta-dev-v1/rehearsal --root artifacts/segment-delta-dev-v1 --seconds 20 -- .venv/Scripts/python.exe artifacts/segment-delta-dev-v1/rehearse.py
.\.venv\Scripts\python.exe scripts/segment_delta_watch.py --directory artifacts/segment-delta-dev-v1/rehearsal-002 --root artifacts/segment-delta-dev-v1 --seconds 20 -- .venv/Scripts/python.exe artifacts/segment-delta-dev-v1/rehearse-002.py
.\.venv\Scripts\python.exe scripts/segment_delta_data.py --root artifacts/segment-delta-dev-v1
.\.venv\Scripts\python.exe scripts/segment_delta_watch.py --directory artifacts/segment-delta-dev-v1/prepare --root artifacts/segment-delta-dev-v1 --seconds 60 -- .venv/Scripts/python.exe artifacts/segment-delta-dev-v1/freeze.py
.\.venv\Scripts\python.exe scripts/segment_delta_study.py contracts --root artifacts/segment-delta-dev-v1
.\.venv\Scripts\python.exe scripts/segment_delta_study.py seal --root artifacts/segment-delta-dev-v1
.\.venv\Scripts\python.exe scripts/segment_delta_study.py run --root artifacts/segment-delta-dev-v1
.\.venv\Scripts\python.exe scripts/verify_segment_delta_dev.py --output-dir artifacts/segment-delta-dev-v1-verification-001
```

The CLI exposes internal `worker --stage train/generate/score` entries with
seed/variant/ablation and fresh directory arguments; the controller records
their full invocations and refuses a second run marker. A future reproduction
needs a separate fresh attempt directory and fresh preparation/check receipts;
copying earlier cost receipts is not a fresh measurement.

Disposable attempt001 completed three numerical backwards with no optimizer
step or generated answer, then monitor finalization failed on a process-exit
race. Preserve raw trace and worker receipt; final controller CPU is unknown.
The monitor was fixed before registration. Disjoint random attempt002 passed;
it selected no architecture/decoding setting. Both are excluded from scores.
Early lint reported style errors before formatting; focused type checks then
passed. All ten contract tests passed on their first test execution; pytest
reported a cache-permission warning, and later verification used a writable
fresh cache. There were no registered cell failures, repairs or retries.

## 5. Every quality/cost cell

Cold evaluation includes generation, teacher-forced scoring and1/10 of measured
shared helper cost. CPU and wall are seconds. Ablations reuse the delta fit,
so their incremental training charge is zero; do not sum its fit again.

| Seed/cell | Exact /24 | Distant /16 | Prose NLL | Factual NLL | Answer NLL | Train CPU/wall | Eval CPU/wall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
|113 ordinary|0|0|2.1367|.9818|3.7727|6.359 /5.903|9.500 /9.206|
|113 recurrent|0|0|2.3603|1.0990|3.6014|8.422 /7.571|10.063 /9.784|
|113 delta|0|0|2.2005|1.0124|3.5633|14.813 /12.386|11.063 /10.325|
|113 delta no-read|0|0|2.2107|1.1118|3.9210|reuse|10.516 /9.973|
|113 delta no-write|0|0|2.2107|1.1118|3.9210|reuse|9.953 /9.424|
|227 ordinary|0|0|2.3141|1.0072|3.9014|6.563 /5.830|10.750 /9.808|
|227 recurrent|0|0|2.4618|1.0813|3.8635|8.750 /7.579|10.703 /9.971|
|227 delta|0|0|2.2080|.9943|3.7610|14.797 /12.389|10.984 /10.154|
|227 delta no-read|0|0|2.3740|1.1094|3.9997|reuse|11.453 /10.539|
|227 delta no-write|0|0|2.3740|1.1094|3.9997|reuse|10.813 /10.166|

Each of the six categories (distant, correction, related-field, unknown,
exact-copy, local) scores 0/4 in every LM cell. All 240 scored LM outputs exhaust
the8-token budget without EOS; they are incorrect, not abstentions. For example,
delta113 returns `ty=ty=ty` for the first gold `la`; delta227 returns `s falls.`.
All four unknown cases produce unsupported non-unknown continuations at each
cell. No successful correction or preservation is demonstrated; zero exact
obsolete-value matches cannot be read as successful revision. Full generated
IDs and category failures are retained in `predictions.jsonl` and `summary.json`.

Actual distant byte-gap bins25..64/65..96/97..128/129+ contain3/4/4/5 cases;
each LM scores0/3,0/4,0/4,0/5. A distance effect is not identifiable when local
copying also fails. Read/write ablations change NLL but do not change exact
accuracy; a differentiable memory path is not useful retained factual memory.

The separate lexical overlap/recency/copy control scores24/24, all categories4/4,
with cold CPU2.484s/wall2.354s. It scans2723 bytes across25 requests, retains at
most164 raw history bytes, and emits75 output IDs including EOS. This is a
grammar parser/retriever with no trained LM; its success is not attributed to
Toruk weights or generalized language understanding. Its tiny raw history is
smaller than the candidate's256-byte matrix, so no storage saving is shown.

All model cells execute identical stream work here:2748 input IDs,200 generated
IDs including replay,2923 consumed IDs,4876 forward positions including1953
recomputed positions,107 full segment boundaries. Full delta/recurrent read and
write4876 positions; no-read removes reads and no-write removes writes.
Ordinary performs neither. Each cell's separate teacher-forced scoring adds3288
positions. Equal byte counts do not mean equal operations. No token reduction or
FLOP-efficiency claim; a FLOP ledger was not a required primary measure.

Each of the three fits at seed113 consumes26,523 targets, and each at227 consumes
25,926:157,347 total targets,768 updates,1536 document presentations. The raw
step/ID/loss traces establish matching training exposure. Optimizer checkpoints:
ordinary196,661 bytes each; recurrent215,814 each; delta213,246/213,182.
All six SHA256 identities are in `stages/train-*/checkpoint-meta.json` and the
summary. Weights remain locally present and git-ignored; hashes do not substitute
for missing checkpoint bytes in another checkout.

## 6. Complete measured ledger and its limits

| Disjoint scope | CPU seconds | Wall seconds |
| --- | ---: | ---: |
| Six fits, including cold setup/checkpoints |59.703|51.658|
| Registered total: preparation/contracts/seal, fits, inference/loss, lexical, controller |168.047|153.553|
| Successful disposable rehearsal002 |4.766|4.768|
| Failed rehearsal001 |at least5.656|at least9.733|
| Post-study byte/hash/accounting audit |.406|.575|
| Post-study scoped repository verification |151.781|189.342|

The six fits are a subset of registered total, not another additive charge.
Shared inference allocation is CPU11.094/wall12.103s divided equally over ten
model workers; the project total counts it once. All model warm generation
requests together cost CPU3.484/wall3.465s, a subset of their cold stages. Cold
imports/checkpoint setup dominate this tiny workload; setup per model worker
is separately retained. The lexical receipt's setup zero is an unmeasured
placeholder, not proof of free setup: its incidental Torch module import is
included in its full cold CPU/wall and cannot be subtracted.

Maximum registered stage private memory683,909,120 bytes; contract-test peak
709,373,952, both below2GiB. Maximum observed registered monitor gap.116s,
below5s; all request caps passed. Raw disk observations and OS private peaks
are retained, separately from256-byte tensors. Verification has its own scope
and peak1,605,488,640 bytes; it is not a model memory measurement.

Early source/paper inspection, editing, uninstrumented data creation/format/type
commands and final narrative/inventory work lack a complete process-tree CPU
receipt. Failed rehearsal001 also lacks final monitor cost. These costs are
**unknown, not zero**; a complete measured lifetime project total cannot be
claimed. Instrumented study total is not total human/agent effort. Post-study
checks are separately charged and do not alter the frozen efficiency verdict.
The final artifact ledger records known totals/lower bounds and these gaps.
No paid service, external inference, runtime installation or model download.

Delta/recurrent charged inference CPU ratios1.099/1.026 and wall1.055/1.018
both miss the required<=.90. Training CPU ratios1.759/1.691 and wall1.636/1.635
miss<=1.50. The result therefore fails efficiency even before including unknown
early project overhead. Two small cold runs do not establish stable hardware
throughput or an amortized lifetime-cost result.

## 7. Gate decisions and meaning

| Predeclared gate | Seed113 | Seed227 |
| --- | --- | --- |
|18/24 exact and four-case gains over both LMs|FAIL|FAIL|
|12/16 distant and four-case gains|FAIL|FAIL|
|No category count regression|PASS, vacuous0 ties|PASS, vacuous0 ties|
|All four unknowns exact abstentions|FAIL|FAIL|
|Read and write ablations each lose two distant answers|FAIL|FAIL|
|Prose NLL<=1.05x ordinary|PASS|PASS|
|Inference CPU and wall<=.90x recurrent|FAIL|FAIL|
|Training CPU and wall<=1.50x recurrent|FAIL|FAIL|
|Parameter/state, source/data/replay and runtime ceilings|PASS|PASS|
|Conjunctive advancement|**FAIL**|**FAIL**|

Phase1 isolation and Phase2 rehearsal/registration gates passed. Phase3
engineering contracts passed. Phase4 rejected the hypothesis at both seeds;
there is no advancement, held-out rescue, larger fit or alternate decoder.

This establishes an implemented, trainable, isolated Toruk byte LM with a
different bounded state update and an auditable negative small-budget study.
It does not establish useful factual memory, total efficiency, conversational
competence, novelty or generalization. All LMs failing locally also prevents
isolating a long-distance weakness or concluding that delta rules cannot work
with other budgets. The fixed budget did not yield a usable factual mechanism.

## 8. New verification and inventory

New local evidence, not hosted CI or earlier saved receipts:
ten contract tests passed; later35 disposable-fixture/regression tests passed;
web20 passed/one live-integration test skipped; lint/format passed; Windows and
Linux-target mypy each passed38 source files; editable installation, pip check,
import, CLI help/diagnose, frozen historical sources, wheel/sdist build and Git
whitespace checks passed. The post-study audit independently checks raw scoring,
replays, training order/targets, checkpoints, frozen identities and caps.

`scripts/verify.py:main` was invoked unchanged through
`scripts/verify_segment_delta_dev.py`; `coverage.json` explicitly marks this as
a subset. Ten historical research/reproduction stages were skipped, including
owned-LM smoke which otherwise opens held-out data. Pytest was limited to six
disposable-fixture modules. This is **not a full unfiltered repository-suite or
hosted-CI pass**. Prior archived check receipts were not reused as new checks.

New files: this report, the v2 architecture decision, frozen protocol;
`src/toruk_lm/segment_delta.py`, `segment_delta_training.py`;
`scripts/segment_delta_data.py`, `segment_delta_watch.py`,
`segment_delta_study.py`, `verify_segment_delta_dev.py`;
`tests/test_segment_delta.py`. No existing tracked source/result was edited.

New artifact directories:

- `artifacts/segment-delta-dev-v1/`: preflight, both disposable numerical
  attempts, frozen train/dev inputs and evaluator labels, data manifest,
  registration, protocol/implementation source snapshots, case hashes, contracts,
  source lock, single-use run marker, six checkpoints/metadata/traces,27 stage
  cost/resource/stdout receipts, raw predictions/replays/losses, summary and audit.
- `artifacts/segment-delta-dev-v1-verification-001/`: new scoped check logs/JSON,
  explicit coverage/skips, disposable test workspace and package build outputs.
- `artifacts/segment-delta-dev-v1-verification-cost-001/`: separate verification
  worker, process-tree trace and total cost. Full paths, bytes and SHA256 values
  are listed in the final artifact inventory; generated bytecode caches excluded.

## 9. Exactly one recommended next step

**Stop the segment-delta-v1 mechanism at this failed development gate and retain
the evidence package.**
