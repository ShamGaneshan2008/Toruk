# M6 successor v1 ? completed negative result, 8 November 2026

**Verdict: FAIL.** The new selector does not establish the joint accuracy/cost
advantage. On the single frozen held-out comparison it scores 5/24, versus
7/24 for simple lexical retrieval and 0/24 for recent context. It costs more
than lexical retrieval and loses two corrections. All methods fail the 60%
quality floor. Historical M6 remains **NOT REPRODUCIBLE**; none of its results
are pooled here and its expected hash was not changed.

## Starting checkout and setup

Checkout: `D:\Toruk`, branch `main`, starting commit
`25d4ec09e01397b43b9b16ad08faeca7cdb22eb0`. Initial `git status -sb`:

```text
## main...origin/main
?? .idea/Toruk.iml
?? .idea/inspectionProfiles/
?? .idea/misc.xml
?? .idea/modules.xml
?? .idea/vcs.xml
```

Tracked/staged diffs were empty. The optional research branch was not created.
The `.idea` files are preserved and their byte hashes are checked against
`artifacts/m6-successor-v1/starting-state.json`. No commit, push, deployment,
publication, paid computation or unbounded training was performed.

`.venv` was absent. The documented virtualenv/CPU Torch/editable-install method
was used with the available Python 3.12.14 interpreter:

```powershell
Set-Location D:\Toruk
& 'C:\Users\susee\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -e '.[chat,dev]'
```

`py` and `python` were absent from PATH; this did not block using the actual
interpreter. Installed runtime: Python 3.12.14, Torch 2.15.0+cpu,
Transformers 5.22.2, Tokenizers 0.23.3, Safetensors 0.8.0, Psutil 7.2.2;
Node 24.15.0/npm 11.12.1. All distributions and pinned versions are retained in
`environment.json` and `requirements-lock.txt`. The active package is the new
editable D-drive checkout. Optional type stubs were tried and removed because
they invalidate an existing unrelated import suppression; no model source was
changed to accommodate them.

Host: Windows 11 build 26100, AMD Ryzen 5 5600G, 6 physical cores/12 logical CPUs,
25,116,758,016 physical RAM bytes; about 12.6 GB available at setup and 713 GB
free on D:. Training/inference use CPU, not a GPU.

The common generator is external `HuggingFaceTB/SmolLM2-135M-Instruct`, revision
`12fd25f77366fa6b3b4b768ec3050bf629380bac`, weights SHA-256
`5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`.
A local copy of that exact pinned backbone was verified before and after copying
from the C-drive checkout. No Toruk selector checkpoint was copied. The reason
for this small backbone was the proposed 3 GiB memory cap; its weak conversational
quality remains a major limitation. Backbone/tokenizer/config hashes are sealed
in the registration and the local copy is excluded from Git.

## Frozen design and technical amendment

The [protocol](m6-successor-v1-protocol.md), base config
`configs/m6-successor-v1.json`, and final execution config
`configs/m6-successor-v1-execution.json` record the new experiment. Original
registration precedes any training; execution registration precedes its repeated
bounded training and **all held-out inference**. Sources and data are preserved
verbatim in each registration's `source.zip`.

Training uses fresh random parameters with seed 8041 and new synthetic controlled
worlds from seed 8031: four training worlds, four validation worlds, 12 AdamW
steps, width 32, two layers, four heads, context 64, four recurrent slots,
57,088 parameters and one CPU thread. The existing controlled QA trainer and
existing recurrent-summary/cosine turn selector are reused. This is not supervised
conversational retrieval training. A separate two-step profile uses seed 8042.
The synthetic world test file is generated/hash-bound but not fitted or scored.

Development has six cases (seed 8051); held-out has 24 (seed 8061), four each
for distant city facts, corrections, preservation, exact literals, clear references
and missing information. IDs, known values and task-bearing templates are disjoint
across these conversation splits and known evaluation values are absent literally
from selector training text. Weather-gap and explicit uncertainty scaffolding are
shared. There are 18 distraction pairs per history and 39?41 messages; the ordinary
web API's 20-message limit is not expanded. This is a research-backend comparison.
No held-out labels reach training or generation; generators receive only role/content.

All methods use the same exact questions, backbone/template, float32, two Torch
threads, 512 native prompt tokens, 32 native output tokens, greedy temperature 0,
top-p 1 and pinned generation configuration. Recent-context fitting drops oldest
whole turns. Lexical-v1 uses word overlap for two older user turns plus the latest
three. TORUK uses its new recurrent summaries to select two older turns plus the
latest three, before the same fitting code. No hidden model, answer rules,
post-hoc threshold change, prompt rewrite or backbone tuning was added.

The frozen numerical success criterion requires **all** of the following against
**both** baselines: each system at least 60% accurate; TORUK no more than five
percentage points worse; no extra unsupported-abstention/stale proxy flags;
and at least 10% lower measured total CPU **and** wall time. Each method pays cold
startup, development/replay and held-out work; TORUK additionally pays every new
profile/training attempt. Each split/method has its own process and memory peak.

Limits: 110 s per profile/train worker; 180 s per evaluation worker; 900 s summed
experiment workers, including the retained preflight; 3 GiB sampled worker-tree
private memory; 3 GiB experiment disk excluding the environment. The corrected
watchdog samples every 50 ms and kills descendants on cap violations. All valid
execution phases stayed inside their caps. Total charged job wall time was
260.605 s. Sampled memory caps are not OS-enforced allocation limits.

**One technical amendment occurred before held-out inference.** The initial
Windows venv process is a small launcher; its actual Python model process is a
child. The first watchdog sampled only the launcher, so those memory peaks are
invalid. `technical-amendment.json`, the original registration/source ZIP and all
training/smoke outputs are preserved. No held-out generation existed at amendment.
The correction monitors descendants, records worker OS lifetime memory peaks,
handles concurrent temporary-file renames and kills the whole worker tree on a
cap violation. A regression test covers the launcher/child distinction.

Execution was repeated in the fresh `execution/` namespace with the same data,
seeds, model mechanism, scoring and gates. Both profile and trained checkpoint
hashes reproduced **exactly**; all first-attempt CPU/wall work is charged, not
hidden or treated as a favorable retry. There are two 2-step profiles and two
12-step fits in total, 28 optimizer steps across independent runs; the final
selector itself has 12 steps. Each development run has six cases plus one exact
first-case replay per method. All six real-model replay checks passed. The final
`freeze.json` binds the checkpoint, execution registration and development outputs.
Held-out then ran **once per method: 72 requests, no exclusions or execution errors**.

## Checkpoint and provenance

New selector SHA-256:

```text
f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49
```

File: `artifacts/m6-successor-v1/execution/train/checkpoint.pt`, 750,423 bytes.
Format remains `toruk-controlled-v1`; `train-worker.json` identifies the new
experiment, random initialization, seed, data, config and exact bytes. It is not
the historical `479c5ee...` checkpoint and is never installed at its path.
The server's inherited `toruk-m6-controlled-qa` kind labels the mechanism; the full
SHA and experiment sidecar identify this distinct new checkpoint.

To avoid losing another ignored `.pt` file, a local
[selector-bundle.zip](../../artifacts/m6-successor-v1/selector-bundle.zip)
contains the exact weight bytes, provenance, registration/freeze/config and frozen
source. Its round-trip member hash was verified without reserializing tensors.
Bundle SHA-256: `f7ceeb84443cad7ac82f3d37483c0902c6e463f3bba78c033f8b455f5cbb662f`.
This bundle was created locally, not published or uploaded.

## Matched results and complete charged work

The primary frozen scorer is unchanged: word-boundary matching for factual values,
obsolete-value rejection, whole-string equality for exact copying and a fixed
uncertainty phrase list. `results-audit.json` independently verifies all 72 scores,
identical question IDs, selected-source text, prompt/generated IDs and actual
cached-backbone forward positions. `raw-answer-review.md` displays every answer.

| Metric | Recent context | Lexical retrieval | New TORUK selector |
|---|---:|---:|---:|
| Frozen accuracy | 0/24 | 7/24 | 5/24 |
| Distant facts | 0/4 | 3/4 | 3/4 |
| Corrections | 0/4 | 4/4 | 2/4 |
| Preservation / exact / reference / missing, each | 0/4 | 0/4 | 0/4 |
| Known-case evidence retained | 0/20 | 20/20 | 15/20 |
| Unsupported-abstention proxy | 4 | 4 | 4 |
| Stale-value proxy | 0 | 0 | 2 |
| Selected held-out prompt tokens | 11,914 | 3,538 | 3,539 |
| Generated held-out tokens | 493 | 360 | 408 |
| Actual backbone forward positions | 12,383 | 3,874 | 3,923 |
| Full-history tokenization positions | 19,818 | 19,818 | 19,818 |
| Fitting tokenization positions, including rejected fits | 148,500 | 3,538 | 3,539 |
| Selector byte positions / forward-update calls | 0 / 0 | 0 / 0 | 75,520 / 1,828 |
| Held-out online request CPU s | 106.781 | 54.109 | 64.938 |
| Held-out online request wall sum s | 53.353 | 26.907 | 32.267 |
| Charged total CPU s | 212.109 | 121.891 | 152.219 |
| Charged total wall s | 106.193 | 65.010 | 89.403 |
| Sampled held-out tree RSS bytes | 970,653,696 | 944,893,952 | 945,090,560 |
| Sampled held-out tree private bytes | 1,416,380,416 | 1,423,818,752 | 1,419,870,208 |

Online request time starts before full-history tokenization and ends after answer
decoding. Total charges also include cold model loading, both development smokes
and their replay calls, all TORUK profile/fitting work and sampled controller CPU.
There are 38 generated requests per method including development/replays, 114 total.
Selector byte positions and backbone BPE positions are reported separately, not
added as equivalent tokens. Four 32-float slots occupy 512 bytes per selector state;
that excludes parameters, Python/history storage, temporary states and backbone KV
cache. State resets per request; this is not a persistent semantic memory store.

This is the complete charged research pipeline scope, not FLOPs/energy or a
production browser/proxy measurement. Common environment installation, backbone
copy/data registration and integrity-wrapper bookkeeping before job timers are
excluded. Outer command wall records remain available. Worker OS peak private
observations are also retained; sampled RSS sums can double-count shared pages.
Verification/integration costs are engineering checks, separate from comparison
costs. No all-system or energy-efficiency claim follows from these partial units.

TORUK uses 70.30% fewer prompt tokens than recent context and has 28.24% lower
charged CPU/15.81% lower wall time, but does not reach useful quality. Compared
with lexical retrieval, it scores two fewer primary answers and uses **24.88%
more CPU and 37.52% more wall time**, with essentially identical prompt size.
Held-out online inference alone also costs TORUK about 20% more CPU and wall
time than lexical, so this difference does not depend on charging the technical
preflight. Both joint gates fail. No favorable alternative accounting can remove
the failed quality floor. No cost-per-correct-answer claim substitutes for the registered gate.

## Raw failures, regressions and scorer limitations

Recent context omits all 20 known-case evidence spans. Lexical retains all 20;
TORUK retains 15, losing two correction spans and three exact-marker spans.
Among TORUK's 19 primary failures, five lose needed evidence, eleven fail with
task context present, and three are rubric false negatives. Lexical has 17
failures despite retained task context. These labels are offline interpretations,
not measurements of internal reasoning.

Examples from the frozen outputs:

- Correction `heldout-correction-1`: current Lusaka, obsolete Bremen. Lexical
  answers Lusaka; TORUK drops the correction and answers Bremen.
- Correction `heldout-correction-2`: current Bremen, obsolete Riga. Lexical
  answers Bremen; TORUK drops the correction and answers Riga.
- Both selectors retain the fourth distant source but answer `Hanoi, Vietnam`
  instead of the recorded town. Evidence selection alone cannot repair the generator.
- Even with preservation or exact evidence retained, many replies are
  `Weather entry received.`; clear-reference replies refuse to provide names.
- Several missing-key replies say `not known` or `not available`. These are
  sensible abstentions omitted from the frozen matcher. It was not edited.

Separate manual review accepts three additional missing-case replies each for
recent/TORUK, giving 3/24, 7/24 and 8/24 for recent/lexical/TORUK under that narrow
post-hoc adjustment. This does not replace the primary metric; every adjusted
score is still below 60%, and TORUK still costs more than lexical retrieval.
The proxy flags are not counts of invented keys.

A narrow task-assertion review identifies eight incorrect town/city values in
recent answers, one in lexical and three in TORUK (including its two obsolete
corrections). Recent also asserts an unsupported origin country in one answer.
No private locker-key value is fabricated. Generic assistant-capability claims
are outside this review; it is not exhaustive semantic ground truth.

The single trial uses synthetic weather distractions, one fitted seed, shared
scaffolding and a weak external generator. It does not establish population
noninferiority, capacity scaling, gist compression or a general architectural
failure. The twelve-step controlled-world selector fit is not task-matched
conversational retrieval supervision. Long research histories exceed the web
API limit, so the measured gains cannot be advertised as production chat gains.

## Commands, verification and reproduction

Exact argument arrays, source identities, durations and logs are in `checks/` and
`verification/`. The executed primary sequence was:

```powershell
.\.venv\Scripts\python.exe scripts/m6_successor.py register --run artifacts/m6-successor-v1 --backbone-dir artifacts/m6-successor-v1/backbone
.\.venv\Scripts\python.exe scripts/m6_successor.py train --run artifacts/m6-successor-v1
.\.venv\Scripts\python.exe scripts/m6_successor.py smoke --run artifacts/m6-successor-v1
# Record the documented technical amendment; retain all preceding files.
.\.venv\Scripts\python.exe scripts/m6_successor.py register --run artifacts/m6-successor-v1/execution --config configs/m6-successor-v1-execution.json --backbone-dir artifacts/m6-successor-v1/backbone
.\.venv\Scripts\python.exe scripts/m6_successor.py train --run artifacts/m6-successor-v1/execution
.\.venv\Scripts\python.exe scripts/m6_successor.py smoke --run artifacts/m6-successor-v1/execution
.\.venv\Scripts\python.exe scripts/m6_successor.py freeze --run artifacts/m6-successor-v1/execution
.\.venv\Scripts\python.exe scripts/m6_successor.py heldout --run artifacts/m6-successor-v1/execution
.\.venv\Scripts\python.exe scripts/m6_successor.py summarize --run artifacts/m6-successor-v1/execution
.\.venv\Scripts\python.exe artifacts/m6-successor-v1/audit_results.py
```

A clean replication should use the final corrected runner and **base config** in
a fresh output directory; do not intentionally repeat the invalid monitoring
preflight. Its questions, seeds and model settings are identical. It measures its
own hardware/costs and need not incur this run's extra technical-development costs:

```powershell
Set-Location D:\Toruk
# Reuse this verified environment, or create Python 3.12 .venv as above.
.\.venv\Scripts\python.exe -m pip install -r artifacts/m6-successor-v1/requirements-lock.txt --extra-index-url https://download.pytorch.org/whl/cpu
$run = 'artifacts/m6-successor-v1-replication'
# If the verified local backbone is absent, obtain the same public pinned files:
# .\.venv\Scripts\python.exe scripts/download_chat_backbone.py --model smollm2 --output artifacts/successor-backbone/backbone
$backbone = 'artifacts/m6-successor-v1/backbone'
.\.venv\Scripts\python.exe scripts/m6_successor.py register --run $run --config configs/m6-successor-v1.json --backbone-dir $backbone
.\.venv\Scripts\python.exe scripts/m6_successor.py train --run $run
.\.venv\Scripts\python.exe scripts/m6_successor.py smoke --run $run
.\.venv\Scripts\python.exe scripts/m6_successor.py freeze --run $run
.\.venv\Scripts\python.exe scripts/m6_successor.py heldout --run $run
.\.venv\Scripts\python.exe scripts/m6_successor.py summarize --run $run
```

Use fresh paths: started markers and exclusive writes reject reruns/overwrites.
For bit-identical weights, use the saved source bytes, same Python/dependencies
and CPU behavior; cross-platform bitwise equality is not promised. The lock file's
editable line refers to D:\Toruk; another checkout must install itself explicitly.
Expected raw answers/scores can be compared independently of device timing.
The selector bundle permits exact-byte recovery without retraining or touching
historical M6. Extract into a fresh directory, then verify its checkpoint with
`Get-FileHash -Algorithm SHA256` against the new full hash above.

Local checks completed:

- `python -m pytest -q`: **280 passed in 139.85 s**, including real page-handler ?
  Node proxy ? Python HTTP fixture integration. Six new tests cover data separation,
  deterministic data, raw identity/drift, scoring, label projection, units and
  Windows worker-tree memory. Real smoke generation replay and repeated training
  hashes provide additional deterministic evidence without rerunning held-out.
- Ruff lint/format, package mypy for default/Windows and Linux, and explicit
  `mypy src/toruk_lm scripts/m6_successor.py`: PASS.
- Node syntax/tests: **20 passed, one opt-in live-page test skipped**.
- CLI, dependency/import, frozen source, dataset/leakage, bounded reproduce/resume,
  package source/wheel builds: PASS through **all 26 scripts/verify.py stages**.
- Real pretrained/new-selector HTTP integration passes through server and Node
  proxy, preserving new SHA, BASELINE/TORUK metrics and outage 503. It is an
  engineering check, not another held-out evaluation. Its LIME42 probe succeeds
  in BASELINE and TORUK invents `HGVH`; HTTP success is not answer-quality success.
- `git diff --check`: PASS; final output/state is retained separately.

The full verification invocation used process-local Git ownership trust and an
explicit forward-slash temp path after preserving generated temp directories:

```powershell
$env:GIT_CONFIG_COUNT = '1'
$env:GIT_CONFIG_KEY_0 = 'safe.directory'
$env:GIT_CONFIG_VALUE_0 = 'D:/Toruk'
New-Item -ItemType Directory -Force .readiness | Out-Null
$env:PYTEST_ADDOPTS = '--basetemp=D:/Toruk/.readiness/m6-successor-full-tests'
.\.venv\Scripts\python.exe -X utf8 scripts/verify.py --prefix successor --output-dir artifacts/m6-successor-v1/verification
.\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/m6_successor.py
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --backbone-dir artifacts/m6-successor-v1/backbone --selector-checkpoint artifacts/m6-successor-v1/execution/train/checkpoint.pt --output-dir artifacts/m6-successor-v1/integration --max-new-tokens 32
git -c safe.directory=D:/Toruk diff --check
```

Use a new verification/temp/integration output path when repeating these commands.
The initial temp-path and optional-stub setup failures are retained in check logs;
the new experiment source passed checks before its sealed held-out run.

GitHub Actions covers Node 22 tests and Python 3.12 lint/format/types, pytest/HTTP
fixture integration, data/leakage validation, bounded smokes and builds, with an
additional Windows reproduction job. Hosted
[run 42465162288](https://github.com/ShamGaneshan2008/Toruk/actions/runs/42465162288)
was observed successful for starting commit `25d4ec09...`. It does not cover these
new uncommitted changes or pretrained scientific evaluation.

Changed files are the new runner, six tests, two configs, protocol/results,
README/architecture/experiment/reproduction notes, evidence attributes/ignores and
this study's artifacts. Production selector/model/scorer/default behavior remains
unchanged. Final Git state and `.idea` preservation checks are in `final-state.json`.
Ending branch/commit remain `main` / `25d4ec09e01397b43b9b16ad08faeca7cdb22eb0`.
The tree contains the documented new source/config/evidence/docs and no staged
changes; all eight pre-existing `.idea` files match their starting byte hashes.
Experiment artifacts occupy about 281 MB, below the 3 GiB cap.

**Single next blocker:** the shared backbone does not clear the factual-quality
floor under this budget. A separately registered backbone qualification is needed
before claiming useful quality-preserving efficiency; this trial remains negative.
