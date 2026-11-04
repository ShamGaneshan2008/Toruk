# Reproduce and audit the evidence

Run from the Toruk repository root. Base commit is
`84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`; the replication overlay includes the
previous uncommitted milestone and this study. No commit, publication or hosted
CI run is performed by these commands. Use **fresh output paths**. Existing
artifacts are immutable evidence and the commands refuse to overwrite them.

## Environment and checkpoints

The recorded run uses Windows 11, Python 3.12.14, CPU Torch 2.14.1+cpu,
Transformers 5.20.2, Tokenizers 0.23.3, Safetensors 0.8.0 and psutil 7.2.2.
`registration.json` records actual package/platform versions and all consumed
source/model/tokenizer hashes; the evidence directory also retains the complete
installed-package version list. Cross-platform or cross-version bitwise output
equivalence is not promised. Preserve the overlay's original source bytes and
line endings; do not restamp hashes to force replay.

The backbone is Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, weights SHA256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
The trained selector is `artifacts/chat-selector-v2-20261101/selector.json`,
SHA256 `abd9d2d1c20edb3ad5cf3282f8a26fca49fb44d508d4ba2ada5ebc9c666b7548`.
Its training data seeds are 711/991/1423 for train/dev/final; its fitting seed is
173. The independent assembly seed is 20261104; controlled recall V2 is a
deterministic enumeration, not a random-seed training run. No new fitting occurs.

For a fresh environment, install dependencies before inference. The exact
recorded versions, rather than newest compatible packages, are the target:

```powershell
py -3.12 -m venv .venv
$py = '.\.venv\Scripts\python.exe'
& $py -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
& $py -m pip install -e '.[dev,chat]'
& $py -m pip install transformers==5.20.2 tokenizers==0.23.3 safetensors==0.8.0 psutil==7.2.2
& $py -m pip check
```

The archive omits the approximately 1 GB pretrained weights. It supplies the
small original backbone support/config/tokenizer/license files so their recorded
bytes are available. If the pinned weights are absent, download to a **fresh**
temporary model directory, then copy only the verified weight file into the
overlay's existing backbone directory. Do not run this block in the original
workspace when its weights already exist:

```powershell
& $py scripts/download_chat_backbone.py --model qwen2.5 --output artifacts/qwen-fetch-replication
if ($LASTEXITCODE -ne 0) { throw 'Pinned download failed' }
Copy-Item -LiteralPath artifacts/qwen-fetch-replication/model.safetensors -Destination artifacts/qwen-chat-001/backbone/model.safetensors
Get-FileHash -Algorithm SHA256 artifacts/qwen-chat-001/backbone/model.safetensors
```

The command refuses a nonempty download directory and checks the fixed weight
digest. No alternate model or automatic fallback is permitted. Download/network
availability on another machine is not validated by this local run.

## Phase 1: actual model replay

The retained run uses `artifacts/independent-replication-20261104/phase1`. For a
new replay, choose a distinct name as below. The two inference commands generate
96 answers; they do not train. Allow several CPU minutes and about 2.3 GiB of
process memory for the loaded model/runtime. Resource needs can differ by host.

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
$phase1 = 'artifacts/my-replication-phase1'
& $py scripts/rank_budget_study.py register --run $phase1
if ($LASTEXITCODE -ne 0) { throw 'Registration failed' }
& $py scripts/rank_budget_study.py development --run $phase1
if ($LASTEXITCODE -ne 0) { throw 'Development replay failed' }
& $py scripts/rank_budget_study.py heldout --run $phase1
if ($LASTEXITCODE -ne 0) { throw 'Heldout replay failed' }
& $py scripts/compare_recall_runs.py --reference artifacts/rank-budget-v1-20261104 --replay $phase1 --output "$phase1/comparison.json"
if ($LASTEXITCODE -ne 0) { throw 'STOP: original evidence did not reproduce' }
& $py scripts/rank_budget_study.py report --run $phase1
```

`comparison.json` must say `exact_reproduction: true` with zero row differences
in both splits. Raw prompts, generated answers, evidence and scoring/token-work
fields must agree, not merely aggregate accuracy. Timing and RSS are excluded
from equality because they vary. The previous intervention's unsupported proxy
must still be read as a failed quality gate, regardless of replay exit code.

## Phase 2: frozen independent set and ablations

The existing `mechanism-freeze.json` predates independent card construction.
Use that freeze; do not create a new mechanism after seeing the evaluation data.
The source/weight identities are verified before registration and every live
stage. The driver also rechecks Phase 1 raw-answer parity and dependency versions.

```powershell
$run = 'artifacts/my-independent-evaluation'
& $py scripts/independent_replication.py register --run $run --phase1 $phase1
if ($LASTEXITCODE -ne 0) { throw 'Independent registration failed' }
& $py scripts/check.py --timeout 1250 --output-dir "$run/checks" independent -- $py scripts/independent_replication.py evaluate --run $run --suite independent
if ($LASTEXITCODE -ne 0) { throw 'Preserve interrupted/failed independent outputs; do not overwrite' }
& $py scripts/check.py --timeout 1250 --output-dir "$run/checks" controlled -- $py scripts/independent_replication.py evaluate --run $run --suite controlled
if ($LASTEXITCODE -ne 0) { throw 'Preserve interrupted/failed controlled outputs; do not overwrite' }
& $py scripts/independent_replication.py audit --run $run
```

These stages generate **144 independent and 72 controlled answers**, with the
same six methods and balanced order. Each stage is capped at 1,200 driver
seconds and each answer at 48 tokens. Logs retain source fingerprints and exact
commands. No measurement-driven retries are part of the registered study.

The tokenizer-only audit verifies all 216 prompts, source bytes/hashes, generated
token decoding, source selection, fixed scores and actual tokenization counts.
It does not load model weights for new inference and is not human semantic
adjudication. Review all unique question/answer combinations against their source
ledgers using the frozen assertion-review rule; retain raw outputs and mark the
review as subjective assistant annotation. An optional `assertion-review.json`
is included by the summary script without changing primary scores:

```powershell
& $py scripts/report_independent_replication.py --run $run
```

The summary refuses to run before a complete passing audit and refuses existing
output files. Confidence intervals and gate conditions are implemented in the
sealed reporter; do not change them using test answers.

## Engineering and CI

```powershell
& $py scripts/verify.py --output-dir artifacts/my-replication-verification
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
& $py -m mypy scripts/independent_cases.py scripts/independent_replication.py scripts/report_independent_replication.py --disable-error-code import-untyped --disable-error-code misc
git diff --check
```

The research-script suppressions match the existing study harness: untyped psutil
and intentional backend class substitution. Runtime checks remain strict.

GitHub Actions and `scripts/verify.py` now also execute:

```sh
python scripts/independent_replication.py validate-cases --run artifacts/ci-independent-cases
```

This validates 24 cards, oracle contracts, deterministic assembly, bounds and
distance without model downloads. Unit tests cover actual instrumentation using
an explicit test double, mutation rejection, ablation contracts, leakage and the
validation CLI. The test double is never used by live evaluation. Normal hosted
CI **does not reproduce the pinned-backbone inference**; it lacks those weights.
No hosted workflow run for these uncommitted changes was launched or observed.
The full local verification script covers installation, types, lint/format,
tests, CLI smokes, source seals, small CPU execution/resume, build and whitespace.
See the final command ledger for actual exits, including initial failures.

## Artifact map

`artifacts/independent-replication-20261104/` contains initial status, mechanism
freeze, Phase 1 replay, sealed independent/controlled datasets and raw responses,
token-only audit, cost/uncertainty summaries, assertion review, command logs,
environment metadata, final seals/accounting and the replication overlay archive.
The draft and claim ledger live alongside this guide. These files support
inspection; they do not replace an external replication or submission review.
