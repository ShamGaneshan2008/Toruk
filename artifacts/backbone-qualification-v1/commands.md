# Windows PowerShell reproduction and actual commands

All work was local. The current evidence directory is immutable: exclusive-output
creation prevents overwriting or repeating it. Reproduction below uses a NEW
output directory and exactly the registered source/config/models/data seeds.
It does not rerun any of the 24 successor questions. Those old saved cases are
read offline only to check overlap.

## Environment

This task reused D:\Toruk\.venv from the previous successor setup; no new runtime
dependencies were installed. The full verifier reinstalls the same editable
local package with no dependencies. For a fresh environment, the repository's
method is:

```powershell
Set-Location D:\Toruk
& 'C:\Users\susee\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -e '.[chat,dev]'
```

Use `requirements-lock.txt`/`environment.json` to check the exact measured
versions; registration refuses drift from sealed versions during a run. Network
installation of latest versions alone is not exact environment reproduction.
Restore the exact `source.zip` members if current bound source differs; extract
into a separate checkout, preserving existing work. Model/tokenizer files have
individual hashes in `registration.json`; both raw weights are separately pinned.

The run read the existing SmolLM input and copied verified Qwen input from
`C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\qwen-chat-001\backbone` to
`artifacts/backbone-qualification-v1/backbones/qwen` without changing either
revision. `input-provenance.json` records hashes and paths. On a fresh device
ONLY, missing candidate files can be restored to empty paths with the existing
pinned downloader:

```powershell
.\.venv\Scripts\python.exe scripts/download_chat_backbone.py --model smollm2 --output artifacts/m6-successor-v1/backbone
.\.venv\Scripts\python.exe scripts/download_chat_backbone.py --model qwen2.5 --output artifacts/backbone-qualification-v1/backbones/qwen
```

These are external pretrained generator weights, not the missing historical M6
selector. Do not overwrite existing successor files or substitute another model.

## Reproduce in fresh output (not executed a second time here)

```powershell
Set-Location D:\Toruk
$ErrorActionPreference = 'Stop'
$env:GIT_CONFIG_COUNT = '1'
$env:GIT_CONFIG_KEY_0 = 'safe.directory'
$env:GIT_CONFIG_VALUE_0 = 'D:/Toruk'
$run = 'artifacts/backbone-qualification-v1-replay-' + (Get-Date -Format yyyyMMddTHHmmss)
.\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py register --run $run
if ($LASTEXITCODE) { throw 'Registration failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py development --run $run
if ($LASTEXITCODE) { throw 'Development controller failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py freeze --run $run
if ($LASTEXITCODE) { throw 'Freeze failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py heldout --run $run
if ($LASTEXITCODE) { throw 'Held-out controller failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py summarize --run $run
if ($LASTEXITCODE) { throw 'Aggregation failed' }
Get-Content "$run/results.json"
```

A controller command finishing does not itself mean a candidate passed. Read
per-stage returncode/failure and aggregate `qualifies`; technically failed
candidates remain failures without inference retries. Fixed resource caps are
inside the sealed config and enforced by the worker-tree watchdog.

## Actual measured commands and retained outcomes

Each inference stage below was run once after successful registration:

```powershell
.\.venv\Scripts\python.exe scripts/check.py --timeout 150 --output-dir artifacts/backbone-qualification-v1/checks registration-final .\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py register --run artifacts/backbone-qualification-v1
.\.venv\Scripts\python.exe scripts/check.py --timeout 650 --output-dir artifacts/backbone-qualification-v1/checks development .\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py development --run artifacts/backbone-qualification-v1
.\.venv\Scripts\python.exe scripts/check.py --timeout 60 --output-dir artifacts/backbone-qualification-v1/checks candidate-freeze .\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py freeze --run artifacts/backbone-qualification-v1
.\.venv\Scripts\python.exe scripts/check.py --timeout 650 --output-dir artifacts/backbone-qualification-v1/checks heldout-once .\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py heldout --run artifacts/backbone-qualification-v1
.\.venv\Scripts\python.exe scripts/check.py --timeout 60 --output-dir artifacts/backbone-qualification-v1/checks aggregate .\.venv\Scripts\python.exe -X utf8 scripts/qualify_answer_backbone.py summarize --run artifacts/backbone-qualification-v1
```

All five wrapper results PASS. Candidate qualification is separately SmolLM FAIL,
Qwen PASS. The first registration attempt failed tokenizer-only preflight before
model inference; its files/log and initial static-check failures are preserved.
After the explicit tokenizer API correction registration succeeded. No numerical
protocol, input data, candidate or generation setting was changed after inference.

Relevant checks (exact commands, with wrapper JSON/logs in checks/):

```powershell
$env:PYTEST_ADDOPTS = '--basetemp=D:/Toruk/.readiness/bq1-preregister-sealed'
.\.venv\Scripts\python.exe -m pytest tests/test_backbone_qualification.py -q
.\.venv\Scripts\python.exe -m ruff check scripts/qualify_answer_backbone.py tests/test_backbone_qualification.py
.\.venv\Scripts\python.exe -m ruff format --check scripts/qualify_answer_backbone.py tests/test_backbone_qualification.py
.\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/qualify_answer_backbone.py
.\.venv\Scripts\python.exe scripts/check.py --timeout 120 --output-dir artifacts/backbone-qualification-v1/checks integration .\.venv\Scripts\python.exe -X utf8 scripts/smoke_chat_foundation.py --backbone-dir artifacts/backbone-qualification-v1/backbones/qwen --baseline-only --output-dir artifacts/backbone-qualification-v1/integration --max-new-tokens 64
$env:PYTEST_ADDOPTS = '--basetemp=D:/Toruk/.readiness/backbone-qualification-full-verification'
.\.venv\Scripts\python.exe -X utf8 scripts/verify.py --prefix backbone --output-dir artifacts/backbone-qualification-v1/verification
git -c safe.directory=D:/Toruk diff --check
git -c safe.directory=D:/Toruk diff --cached --check
```

Use a fresh pytest basetemp/output for later checks. Parent `.readiness` exists;
forward slashes avoid Windows pytest-addopts parsing issues. No credentials
are needed for local inference. The integration smoke exercises a preexisting
non-successor fixture through page/proxy/server; it is not new quality evidence
and uses the existing production prompt defaults, not this sealed research
instruction. It passes page/status, response/proxy metrics and outage handling.

`verification/backbone-*.json` each records exact argv, source hashes, returncode,
status, elapsed seconds and its raw log. `hosted-ci.json` separately records the
observed successful Actions run for the starting committed source only. Hosted
CI has not run this uncommitted code or either qualification model inference.

## Verification failure investigation (no model generation)

Initial `scripts/verify.py` returned 1: 25 stages passed, Python stage had
288 passed and one existing page/proxy HTTP-fixture failure. Preserve that log.
The fixture passed in isolation with unchanged code; a full-suite confirmation
was then run once in a fresh temp directory:

```powershell
$env:PYTEST_ADDOPTS='--basetemp=D:/Toruk/.readiness/backbone-http-diagnostic'
.\.venv\Scripts\python.exe scripts/check.py --timeout 90 --output-dir artifacts/backbone-qualification-v1/checks http-diagnostic .\.venv\Scripts\python.exe -m pytest tests/test_web_integration.py -q
$env:PYTEST_ADDOPTS='--basetemp=D:/Toruk/.readiness/backbone-full-suite-confirmation'
.\.venv\Scripts\python.exe scripts/check.py --timeout 420 --output-dir artifacts/backbone-qualification-v1/checks full-tests-confirmation .\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check.py --timeout 120 --output-dir artifacts/backbone-qualification-v1/checks sealed-runner-types .\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/qualify_answer_backbone.py
```

Read `verification-summary.json` for both initial and confirmation outcomes.
No initial failures were overwritten and no frozen protocol was amended.

Final outcome: full-suite confirmation PASS, 289/289 in 135.81 s; isolated
HTTP fixture PASS, all other 25 original verifier stages PASS. The initial
verifier exit code remains 1, and its failure log is preserved. No source was
changed between the failed suite and successful confirmation.
