# Frozen Qwen long-history v1 - blocked before held-out

**Registered verdict: NOT PASSED / BLOCKED. No held-out accuracy or selector
advantage is established.** Windows entered idle sleep during TORUK development.
On wake the watchdog detected exhausted elapsed limits; the required freeze
rejected development. No held-out arm ran. No timing subtraction, budget increase,
selector/scorer change or favorable inference retry followed this failure.

## Starting and ending checkout

Working directory `D:\Toruk`, branch `main`, starting commit
`25d4ec09e01397b43b9b16ad08faeca7cdb22eb0`.

```text
## main...origin/main
 M .gitattributes
 M .gitignore
 M README.md
 M docs/architecture.md
 M docs/experiments.md
 M docs/reproducibility.md
 M pyproject.toml
?? .idea/Toruk.iml
?? .idea/inspectionProfiles/
?? .idea/misc.xml
?? .idea/modules.xml
?? .idea/vcs.xml
?? artifacts/backbone-qualification-v1/
?? artifacts/m6-successor-v1/
?? artifacts/qwen-long-history-v1/
?? configs/backbone-qualification-v1.json
?? configs/m6-successor-v1-execution.json
?? configs/m6-successor-v1.json
?? docs/research/backbone-qualification-v1-protocol.md
?? docs/research/backbone-qualification-v1-results.md
?? docs/research/m6-successor-v1-protocol.md
?? docs/research/m6-successor-v1-results.md
?? scripts/m6_successor.py
?? scripts/qualify_answer_backbone.py
?? tests/test_backbone_qualification.py
?? tests/test_m6_successor.py
```

Ending status (same branch and commit; nothing staged):

```text
## main...origin/main
 M .gitattributes
 M .gitignore
 M README.md
 M docs/architecture.md
 M docs/experiments.md
 M docs/reproducibility.md
 M pyproject.toml
?? .idea/Toruk.iml
?? .idea/inspectionProfiles/
?? .idea/misc.xml
?? .idea/modules.xml
?? .idea/vcs.xml
?? artifacts/backbone-qualification-v1/
?? artifacts/m6-successor-v1/
?? artifacts/qwen-long-history-v1/
?? configs/backbone-qualification-v1.json
?? configs/m6-successor-v1-execution.json
?? configs/m6-successor-v1.json
?? configs/qwen-long-history-v1.json
?? docs/research/backbone-qualification-v1-protocol.md
?? docs/research/backbone-qualification-v1-results.md
?? docs/research/m6-successor-v1-protocol.md
?? docs/research/m6-successor-v1-results.md
?? docs/research/qwen-long-history-v1-protocol.md
?? docs/research/qwen-long-history-v1-results.md
?? scripts/m6_successor.py
?? scripts/qualify_answer_backbone.py
?? scripts/qwen_long_history.py
?? tests/test_backbone_qualification.py
?? tests/test_m6_successor.py
?? tests/test_qwen_long_history.py
```

`artifacts/qwen-long-history-v1/starting-state.json` records the initial full diff,
empty staged diff, untracked inventory, hardware and 593 prior file hashes.
Original shared-file bytes are backed up in initial-files/. Ending Git status and
byte-preservation results are in final-state.json. Existing successor and
qualification artifacts, source/config/protocol/report files and all eight IDE
files are preserved. No commit, push, deployment, publication, paid work or new
selector/backbone training. Historical M6 remains **NOT REPRODUCIBLE**, with its
original expected hash unchanged. The new comparison does not pool old scores.

Existing documented `.venv` was reused: Python 3.12.14, Torch 2.15.0+cpu,
Transformers 5.22.2, Tokenizers 0.23.3, Safetensors 0.8.0, Psutil 7.2.2;
Node 24.15.0/npm 11.12.1. No runtime dependency/model download was needed.
Ryzen 5 5600G, six cores/twelve logical CPUs, 25,116,758,016 RAM bytes;
13,321,891,840 available RAM bytes and 710,211,481,600 free disk bytes at start.
Environment/lock and hashes of all inspected inputs, including 179 previous raw
answers, are retained in environment.json, requirements-lock.txt and read-inputs.json.

## Frozen protocol and identities

[Protocol](qwen-long-history-v1-protocol.md),
[config](../../configs/qwen-long-history-v1.json), valid attempted registration
`artifacts/qwen-long-history-v1/execution-v2/registration.json` and source.zip
were sealed before development. Registration SHA-256:
`489b9a6ee3756f07fc709c2bd2dea91bc761265269ad4853ae27c67e38724a86`. Mechanisms, dataset, scoring and numerical
criteria were fixed before any new candidate answer. Model/tokenizer files match
backbone-qualification-v1 byte for byte.

Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, raw safetensors SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
Apache-2.0 provenance comes from the unchanged qualified identity and pinned
[license](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/7ae557604adf67be50417f59c2c2f167def9a775/LICENSE).
TORUK uses existing successor toruk-controlled-v1 checkpoint
`artifacts/m6-successor-v1/execution/train/checkpoint.pt`, raw SHA-256
`f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49`.
It is the previously trained 12-step recurrent-summary/cosine selector, not lost
historical M6 or a newly trained replacement. Lexical uses unchanged lexical-v1.

All arms share the qualification system instruction, native Qwen chat template,
Reference/Question/Answer wrapper and 64-token answer cap. Selected transcript
turns are rendered verbatim as chronological User:/Assistant: lines inside that
same reference wrapper. Only original role/content reaches selection/generation;
source IDs, expected values, alternatives and evidence indices are offline.
Greedy float32 CPU, two threads, generation seed 81751, request temperature 0,
top-p 1, one beam, repetition penalty 1, KV cache and common GenerationConfig.
Full uses every source turn; no gold-aware oracle subset. Recent/lexical/TORUK
fit their selected whole turns to 512 native tokens without dropping instruction
or question. Production backend and its prompt/defaults are unchanged.

Pinned model max_position_embeddings is 32768; tokenizer model_max_length is
larger. Reserve 64 output positions. Full-context overflow blocks registration
for the entire dataset, without truncation/exclusion. Tokenizer preflight verified
full prompts of 766-828 tokens, all over 512 and below the actual limit. This is
a modest 43-47-turn synthetic history study, not a 32K-capacity demonstration.

Fresh owned synthetic data: seven development cases (seed 82811), 28 held-out
(seed 82831), four each for distant facts, corrections, distractors, exact copying,
preservation, vague references and missing information. Two vague cases are
ambiguous: held-out has 22 known and six UNKNOWN answers. Generic log scaffolding
is shared; split-specific questions/expected values/IDs differ. Recursive literal
overlap checks passed against 5,162 prior records from 132 JSON/JSONL files,
including both previous studies. Scanner limits and searched hashes are retained
in leakage.json; archives/pretraining and semantic equivalence are not exhaustively
covered. No held-out answer was generated, examined or used for tuning.

Primary metric is equal-case/category answer accuracy. Frozen rubric inherits
qualification word-boundary/alternative/negation matching, exact whole-answer
literal equality and explicit uncertainty credit. Store all-case exact-match and
stale/unsupported proxies separately. No post-answer scoring repair occurred.
Success requires all arms complete within caps; full and TORUK >=17/28 overall
and >=14/22 known; TORUK loses no more than five points overall or one case per
category to each other arm; no added stale/unsupported proxy; >=10% lower complete
CPU AND wall versus BOTH recent and lexical. All conditions are conjunctive.

Limits: 6 GiB worker-tree private memory, 3 GiB study/input disk, 300 s per arm/split,
30 s per question, 1200 summed new evaluation seconds. Fresh sequential workers,
50 ms watchdog, final worker OS private peaks and exclusive-output guards.

## Technical prerequisite failures and evidence

The first registered development controller hit Windows PermissionError reading
an atomically replaced progress file. Its full worker finished all seven cases
plus replay, but controller/resource accounting was lost. That attempt is INVALID,
retained under the root with source.zip and preflight-attempt-1/ copied source.
A monitoring-only amendment added bounded file-read retries and guaranteed child
cleanup, before any held-out generation. No development answer was inspected for
tuning before the amendment. Data/full prompt IDs are byte-identical, and models,
scoring, quality gates and resource caps are unchanged (amendment-parity.json).
The fresh execution-v2 registration reserves 73.307 s conservatively for this
invalid attempt against the same 1200 s cap; it does not reset/increase the limit.

Full and lexical development then completed with exact first-case replay. During
TORUK development Windows System logs record:

- Kernel-Power event 42: entering sleep, reason System Idle.
- Power-Troubleshooter event 1: sleep `2026-11-08T15:35:16.4072437Z`, wake
  `2026-11-08T15:56:06.5668497Z` (about 1250.16 seconds).
- Kernel-General event 1: hardware-clock resynchronization delta 1,240,753 ms.

Exact messages/providers/timestamps are retained in windows-power-events.json.
TORUK stage records 1255.801 wall seconds but 25.063 sampled CPU seconds.
The OS could not run the watchdog while asleep; it tripped the 300-second stage
and 1200-second total limits on resume. Recent was immediately stopped because
the total was exhausted. `freeze` returned 1: development prerequisite failed.
The development controller wrapper itself returned 0, because it records worker
failures rather than treating them as quality success. This wrapper PASS is NOT
an experiment PASS. No freeze.json or heldout-started file exists.

## Four-arm results

| Arm | Held-out completed | Held-out accuracy | Development completed/correct | Status |
|---|---:|---|---:|---|
| Full evidence | 0/28 | NOT RUN | 7/7, 5 correct | Development completed |
| Recent 512 | 0/28 | NOT RUN | 0/7 | Stopped after total cap |
| Lexical-v1 512 | 0/28 | NOT RUN | 7/7, 7 correct | Development completed |
| TORUK 512 | 0/28 | NOT RUN | 1/7, 0 correct | Host sleep; elapsed cap |

Development scores exclude replay. This is not a matched held-out result or proof
that lexical beats TORUK. Quality/regression/efficiency gates are **NOT TESTED**;
completion/resource prerequisites fail, so the registered conjunction cannot pass.
No missing answer is silently assigned a fabricated zero-score answer.

Development-only case-type scores (numerator/actually completed; not held-out):

| Type | Full | Recent | Lexical | TORUK |
|---|---|---|---|---|
| Distant | 1/1 | NOT RUN | 1/1 | 0/1 |
| Correction | 0/1 | NOT RUN | 1/1 | NOT RUN |
| Distractor | 1/1 | NOT RUN | 1/1 | NOT RUN |
| Exact copying | 0/1 | NOT RUN | 1/1 | NOT RUN |
| Preservation | 1/1 | NOT RUN | 1/1 | NOT RUN |
| Vague reference | 1/1 | NOT RUN | 1/1 | NOT RUN |
| Missing information | 1/1 | NOT RUN | 1/1 | NOT RUN |

## Per-case evidence and failure analysis

`execution-v2/development-*-answers.jsonl` retains every raw answer, selected
verbatim context, indices, rendered prompt/token IDs, generated IDs, correctness,
abstention/exact-match flags, evidence retention and failure classification.
`development-review.json` gives the 15 completed arm/case records across seven development questions.
No held-out answers exist. Full/lexical retained evidence in all six known dev
cases; TORUK retained it in its one completed known case. All three observed
wrong answers therefore fail downstream of evidence selection:

- Full correction: expected `linen cabinet`, answered `archive cabinet` despite
  the explicit correction in the full prompt.
- Full exact: expected `DEV/PUTYAOKYO:  R-4!`, answered `DEV/PUTYAOKYO: R-4!`.
  The full quoted evidence was retained; lost internal spacing is a generator
  failure. Lexical copied it exactly with a shorter selected prompt.
- TORUK distant: required source retained, but answer `delivery ledger
  LHD-4F9D48AA0B8B` omits requested `copper quay`.

Full and lexical each validly abstained on the missing-information dev case.
No primary scoring concern was used to change these outcomes. The tiny incomplete
development sample cannot isolate general selector effects or validate quality.

## Cost ledger and limits of comparison

The following is observed development work INCLUDING completed replays, not a
common completed workload. TORUK's interrupted second request has no saved
per-question output; its partial work is in process CPU, not fabricated row sums.

| Arm | Prompt/output tokens in saved rows | Generation CPU/wall s | Selector CPU/wall s | Stage CPU/wall s | Sampled private GiB |
|---|---:|---:|---:|---:|---:|
| Full | 6307/41 | 93.859/46.732 | 0/0.00034 | 119.656/56.474 | 3.831 |
| Recent | none | none | none | 0.891/1.413 | startup only |
| Lexical | 1404/97 | 43.844/21.726 | 0/0.00196 | 63.516/31.179 | 3.787 |
| TORUK | 150/17 | 6.109/3.060 | 0.859/0.216 | 25.063/1255.801 | 3.777 |

Zero lexical CPU is below this Windows process CPU timer's resolution, not proof
of no work. Actual lexical scanning: 172 term calls / 19,776 bytes. TORUK's saved
request: 2,806 byte positions / 65 forwards and state updates, 512-byte nominal
recurrent state, no persistent cross-query state. It rescans every history.
Backbone forward positions: full 6,340, lexical 1,493, TORUK 166; BPE and selector
byte positions are separate units. Full-history tokenization: 6,307 positions
for full and lexical, 767 for completed TORUK; fit tokenization: 0, 1404, 150.
These partial counts do not include unsaved interrupted request work; process
CPU includes its sampled work. RSS/private/OS peaks, fit/request timing and exact
counts are retained per stage/row. No process peak exceeds 6 GiB. Disk peaks are
about 1.003 GB, below 3 GiB.

Recorded development stages total 209.125 CPU s and 1344.866 wall s, including
host sleep. Invalid first preflight adds a known 102.750 worker CPU s and 52.807
worker wall s; its lost controller CPU is UNKNOWN. Controller wrapper wall is
20.500 s overlapping that worker, hence use the conservative 73.307 s upper bound,
not a fake exact additive duration. Complete experiment CPU cannot be reconstructed
from these incomplete records. No full-system efficiency win is claimed.

No new training. Historical successor profile/training ledger, four saved stages
including its original technical rerun: 14.578 CPU s, 17.673 wall s. Registered
amortization was N=28 held-out queries: 0.521 CPU s and 0.631 wall s/query, charged
once to TORUK alongside its new development/cold held-out costs. There are zero
completed held-out queries, so this planned workload is NOT realized and no
measured cost-per-held-out-answer is available. N=1000 sensitivity would allocate
0.01458 CPU/0.01767 wall s per query for training only, not measure a larger workload.
Early original training parent-memory samples were invalid; do not claim known
training peak RAM. External common Qwen pretraining/download/environment cost
is not a new selector cost and is outside this local operating comparison.
General engineering checks are separately logged, not credited as a model saving.

## Verification and changed files

New research runner, twelve contract tests, versioned config, protocol/results and
artifacts/qwen-long-history-v1 evidence. README/architecture/experiments/reproduction
and attributes/ignore receive append-only notes. No production model, selector,
prior scorer, defaults or prior study artifact was edited.

Local `scripts/verify.py` returned **0**, all **26 stages PASS**. Python:
**301 passed in 141.43 s**, including the real page-handler / Node proxy / Python
HTTP fixture. No HTTP fixture retry was needed in this task. Node standalone:
20 passed, one opt-in live test skipped (covered separately by the Python fixture).
Ruff lint/format, Windows/Linux Mypy, frozen sources, dependency/import/CLI checks,
data validators, bounded existing train/resume/ablation/reproduction fixtures,
source/wheel build and staged/unstaged diff checks passed. Explicit Mypy including
the new runner passed 36 files before registration. Twelve new contracts cover
fresh/leakage-safe data, metadata-free input projection, identical wrapper,
whole-turn fit, overflow rejection, scoring, attribution, gates, replay cost,
identity/overwrite guards, progress-file contention and child cleanup.

Exact argument arrays and raw logs are in checks/ and verification/;
[PowerShell record](../../artifacts/qwen-long-history-v1/commands.md) distinguishes
executed commands from blocked/planned commands. Engineering verification used
a temporary process-scoped SetThreadExecutionState system-required request,
restored afterward, to prevent repeating the host-idle failure. No global power
setting changed and no candidate/held-out inference resumed. Existing tiny
fixture training is engineering verification, not selector fitting. No extra
pretrained-model HTTP smoke was run after the budget stop; the real HTTP fixture
and actual research development workers provide the applicable integration checks.
No interactive browser or deployment was run.

Observed [hosted CI run 42465162288](https://github.com/ShamGaneshan2008/Toruk/actions/runs/42465162288)
succeeded for the starting commit only. Its Python 3.12/Node 22 jobs cover
static/unit/HTTP-contract/CLI/smoke/build checks, plus Windows owned-LM path-with-
spaces reproduction. It does not cover these uncommitted changes or pretrained
long-history inference. See hosted-ci.json and verification-summary.json.

## One next blocker

An awake benchmark host under a newly authorized, explicitly registered bounded
attempt. Prevent idle sleep with a process-scoped power request during that future
attempt, restore it afterward, and retain these failures. The current fixed budget
is exhausted; do not silently reset it or continue the frozen held-out run. The
28 held-out questions remain untouched and no held-out-driven mechanism tuning
has occurred. No selector-quality or cost verdict can be supplied until all four
arms complete under a valid registered attempt.
