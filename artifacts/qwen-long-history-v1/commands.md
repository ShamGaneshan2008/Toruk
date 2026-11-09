# Windows PowerShell commands: qwen-long-history-v1

Working directory D:\Toruk. Existing documented .venv and both frozen model
inputs were reused. No dependency/model download or new selector training.
All inference below is local CPU float32 with two Torch threads.

## Actual sequence (held-out NOT RUN)

```powershell
Set-Location D:\Toruk
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py register --run artifacts/qwen-long-history-v1
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py development --run artifacts/qwen-long-history-v1
```

The initial development controller failed while reading an atomically replaced
progress file on Windows. The worker completed, but valid controller/resource
accounting was lost. Preserve the root attempt and its checks/development.log.
The monitoring-only amendment is documented in the protocol and preflight-attempt-1.
No held-out generation occurred and no development answer was used for tuning.
After passing the amendment's tests/static checks:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py register --run artifacts/qwen-long-history-v1/execution-v2
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py development --run artifacts/qwen-long-history-v1/execution-v2
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py freeze --run artifacts/qwen-long-history-v1/execution-v2
# NOT EXECUTED: heldout --run artifacts/qwen-long-history-v1/execution-v2 (prerequisite failed)
# NOT EXECUTED: summarize --run artifacts/qwen-long-history-v1/execution-v2 (no heldout results)
```

Wrappers in checks/*.json retain exact argument arrays, source hashes, wall time,
returncodes and raw log paths. They invoke the same .venv python, -X utf8,
scripts/check.py with 120-second registration, 1230-second development/heldout,
and 60-second freeze/summary deadlines. The independent worker watchdog enforces
the tighter frozen per-request/stage/cumulative/memory/disk limits.

## Future authorized reproduction only (current budget exhausted)

Use the final source.zip and exact dependency versions in requirements-lock.txt
and environment.json. Restoring into a separate checkout avoids overwriting work.
Reproduction requires exact Qwen files in the directory in the config, verified
against qualification registration, and the exact successor selector checkpoint.
No historical M6 substitution. The original backbone/selector artifacts and
historical training-cost ledgers are inputs; restore their exact bytes from the
saved bundles if missing. Do not retrain and relabel replacement bytes as original.
A fresh network download can restore only the pinned public Qwen assets; compare
EVERY file hash to qualification registration before running. This task did not
download anything. The existing environment method is documented in
README.md and the previous successor report.

```powershell
Set-Location D:\Toruk
$ErrorActionPreference='Stop'
$run='artifacts/qwen-long-history-v1-replay-' + (Get-Date -Format yyyyMMddTHHmmss)
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py register --run $run
if ($LASTEXITCODE) { throw 'Registration failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py development --run $run
if ($LASTEXITCODE) { throw 'Development controller failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py freeze --run $run
if ($LASTEXITCODE) { throw 'Development prerequisites failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py heldout --run $run
if ($LASTEXITCODE) { throw 'Held-out controller failed' }
.\.venv\Scripts\python.exe -X utf8 scripts/qwen_long_history.py summarize --run $run
if ($LASTEXITCODE) { throw 'Summary failed' }
Get-Content "$run/results.json"
```

Do not repeat the invalid preflight. The config conservatively reserves its
73.307-second wall upper bound, without increasing any cap. Exclusive-output
creation prevents reruns/overwrites of an existing attempt. Worker errors remain
in per-stage cost files; controller exit alone is not a quality PASS. Read the
registered conjunctive verdict and every cost/quality gate. Reproduction timings
can differ by device. No model rerun was used to regenerate this report.

## Verification commands

```powershell
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0='D:/Toruk'
$env:PYTEST_ADDOPTS='--basetemp=D:/Toruk/.readiness/long-history-monitor-contracts'
.\.venv\Scripts\python.exe -m pytest tests/test_qwen_long_history.py -q
.\.venv\Scripts\python.exe -m ruff check scripts/qwen_long_history.py tests/test_qwen_long_history.py
.\.venv\Scripts\python.exe -m ruff format --check scripts/qwen_long_history.py tests/test_qwen_long_history.py
.\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/qwen_long_history.py
$env:PYTEST_ADDOPTS='--basetemp=D:/Toruk/.readiness/qwen-long-history-full-verification'
.\.venv\Scripts\python.exe -X utf8 scripts/verify.py --prefix long-history --output-dir artifacts/qwen-long-history-v1/verification
# No additional pretrained integration generation after the budget stop; pytest runs the real page/proxy/Python fixture.
git -c safe.directory=D:/Toruk diff --check
git -c safe.directory=D:/Toruk diff --cached --check
```

Integration is a separate existing non-successor fixture through the real local
page/proxy/server. It uses production defaults, not the research transcript
wrapper, and adds no primary score. Full verification includes Node syntax/tests,
Python tests/HTTP contract, lint/format/types, CLI validation/bounded fixture
train/resume/reproduction, frozen-source checks and wheel/source build. Those
small fixture trainings are engineering checks, not new selector/backbone fitting.
Use fresh pytest basetemp and output paths when repeating general checks. Keep
any intermittent HTTP fixture failure log; report isolated/full retries separately.
Hosted CI observations are in hosted-ci.json and cover the starting commit only.


Final development outcome: full and lexical completed; TORUK exceeded elapsed
limits after confirmed host idle sleep, recent stopped on exhausted total.
The development wrapper PASS means only controller completion. Freeze was run
through checks/freeze-blocked.json and returned 1. Heldout and summarize were
NOT EXECUTED. Offline blocked-results.json and development-review.json preserve
partial accounting; no missing held-out answers were fabricated.

System diagnostics (read only) used Get-WinEvent on System events 1,42,107,506,507
from two minutes before checks/development-amended.json started_utc; matching
Power/Kernel-General records are saved in windows-power-events.json. They prove
idle sleep from 15:35:16 UTC to 15:56:06 UTC. No sleep duration was subtracted
from registered timings and no new evaluation budget was created.

The general verifier was wrapped in a temporary process-scoped
SetThreadExecutionState(ES_CONTINUOUS|ES_SYSTEM_REQUIRED) request, restored with
ES_CONTINUOUS in a finally block. Exact PowerShell is in verification-command.ps1.
This guard was used ONLY for engineering verification, not to retroactively
repair or resume the frozen experiment. A future fresh attempt requires an
explicitly registered bounded budget and awake-host prerequisite.

Final verification: scripts/verify.py returned 0, all 26 stages PASS; Python
301 passed in 141.43 s, Node 20 passed/one opt-in skip; no HTTP retry needed.
This does not change the BLOCKED experiment status or authorize held-out inference.
