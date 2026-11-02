# Disabled local chat: diagnosis and repair

The backend and proxy now load **Qwen/Qwen2.5-0.5B-Instruct** successfully and report
`ready: true`. Both are running at `http://127.0.0.1:8766` and
`http://127.0.0.1:3000`. Reload the page once for the updated UI; it now has a
**Retry connection** button. Start commands are in [the PowerShell guide](../local-chat.md).

## Root cause established against the running service

The original backend really was running with:

```powershell
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --checkpoint .\artifacts\minimal-lm-demo-001\train\checkpoint.pt --host 127.0.0.1 --port 8766
```

That file does not exist in this checkout. Before changing the loader, invoking
`OrdinaryChatBackend` directly against it produced this actual error:

```text
ChatError: Cannot load checkpoint: [Errno 2] No such file or directory: 'artifacts\minimal-lm-demo-001\train\checkpoint.pt'
```

The worker previously closed its pipe without forwarding the reason. The parent
replaced that with “Model startup failed; check provisioned model identity.” The
CLI logged only “Checkpoint load failed” but still announced a listening server.
Public status then hid the reason behind “unavailable or incompatible”. The page
correctly disabled controls on `ready: false`, but checked readiness only once.

`GET /status` originally returned 404 because the backend supported `/api/status`
and `/healthz`. This was a wrong diagnostic route, not evidence of a missing HTTP
server. `/status` is now a compatible alias.

The source checkout already contained unfinished work from the previous task;
those changes were preserved. No model was assumed present: the optional
dependencies and all local Qwen files were inspected, and the actual model loader
verified the weight hash before announcing readiness.

## Installed model and attribution

- Model: `Qwen/Qwen2.5-0.5B-Instruct`.
- Revision: `7ae557604adf67be50417f59c2c2f167def9a775`.
- Weight SHA-256: `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Local directory: `artifacts/qwen-chat-001/backbone`.
- Weight size: 988,097,824 bytes; about 1 GB with tokenizer/config files.
- License: Apache-2.0, included locally as `LICENSE`.
- Installed versions: Torch `2.14.1+cpu`, Transformers `5.20.2`, Safetensors `0.8.0`.
- Runtime: CPU float32, two Torch threads, about 2 GB for parameters plus overhead;
  no GPU required. No new model download or dependency installation was necessary.

Qwen supplies pretrained language capability. Toruk supplies the bounded service
and optional research selector. The evaluated selector is absent, so this setup is
**BASELINE, memory disabled**. These answers do not establish a Toruk accuracy or
token-efficiency improvement. The ordinary repeating-text checkpoint was not used
or substituted.

## Changes made

- `chat_runtime.py`: typed startup failures with fixed safe error codes; separately
  identify missing, invalid and incompatible ordinary checkpoints.
- `chat_foundation.py`: distinct codes for absent/invalid model files, missing chat
  dependencies, incompatible backbone setup and unavailable optional selector.
- `inference_worker.py`: send the startup category through the worker pipe instead
  of losing it on EOF. Raw exception strings and paths never cross that boundary.
- `inference_server.py`: log `CHAT DISABLED [code]` with a setup action and label
  failed startup as a readiness-only service. Add `/status`; unready `/healthz`
  returns 503. `/api/status` returns `ready: false`, `error_code` and a safe action.
  A worker that dies after startup now reports a restart action too.
- `web/vercel/lib/proxy.js`: map only allowlisted failure codes to browser messages;
  never forward arbitrary model-loading error strings. Preserve the category for
  unready chat requests.
- `public/index.html`, `public/chat_state.js`: controls start disabled, enable only
  for an explicitly ready backend, show the safe cause, and recover via Retry.
  A failed retry clears stale readiness and disables both controls.
- Python and Node tests: real worker failure codes, incompatible checkpoints,
  absent dependencies, readiness/health semantics, privacy, actual page handlers,
  sending controls and generated follow-up history.
- `scripts/smoke_chat_readiness.py`: real failed-startup backend/proxy integration.
- README and local guide: current two-terminal PowerShell commands, model setup
  checks, size/license/hardware needs, status routes and retry/troubleshooting.

## Real requests after switching the running services

The original listeners were identified before stopping them. Only those Toruk
services were replaced. The newly started backend log says:

```text
INFO: Chat ready: Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf
INFO: Toruk inference listening on 127.0.0.1:8766
```

Backend and proxy status both returned `ready: true`, the expected model identity,
no error and `memory_supported: false`.

The live UI test fetched the actual page, executed its actual handlers with a DOM
stand-in, checked that typing and Send were enabled, assigned the input value and
submitted it through the real Node proxy to the loaded model. Generation paused
the controls, then enabled them again. Follow-up history contained the real preceding
assistant response. These are exact outputs, at the UI's default 32-output-token cap:

| User message | Actual assistant response | Input / selected / output | Backend ms |
| --- | --- | --- | ---: |
| What is the capital of France? | The capital of France is Paris. | 96 / 96 / 8 | 2148.459 |
| My name is Mira. | Mira is a person with your given name. | 95 / 95 / 11 | 2638.592 |
| What is my name? | Your name is Mira. | 120 / 120 / 7 | 2354.502 |

All reported `memory_used: false`. The first question was a separate conversation;
the final two were a real generated two-turn exchange.

**Interactive browser validation remains unrun.** Browser runtime discovery returned
an empty list. The DOM-handler tests validate control state and transport, not visual
layout, focus behavior or an actual physical browser session. No browser test is
claimed on the basis of a fetched HTML page alone.

## Commands and results

Evidence is retained under `artifacts/readiness-fix-20261031/`. Wrapper JSON records
include the exact expanded commands and source identity. All commands ran from
the repository root in Windows PowerShell.

```powershell
# 28 focused Python tests passed.
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 180 --output-dir artifacts/readiness-fix-20261031 focused-python -- .\.venv\Scripts\python.exe -m pytest -q tests/test_chat.py tests/test_chat_foundation.py tests/test_chat_release_eval.py tests/test_inference_server.py

# Node syntax checks passed; 10 regular Node tests passed, one optional live test skipped.
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 120 --output-dir artifacts/readiness-fix-20261031 node-check -- npm.cmd --prefix web/vercel run check
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 120 --output-dir artifacts/readiness-fix-20261031 node-tests -- npm.cmd --prefix web/vercel test

# Optional live test was separately run: both UI tests passed, none skipped.
$env:TORUK_LIVE_WEB_URL = 'http://127.0.0.1:3000'
node --test .\web\vercel\tests\ui.test.mjs
Remove-Item Env:TORUK_LIVE_WEB_URL

# Both real failed-startup cases passed: missing checkpoint and missing backbone.
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 150 --output-dir artifacts/readiness-fix-20261031 failed-startup-integration -- .\.venv\Scripts\python.exe scripts/smoke_chat_readiness.py --output-dir artifacts/readiness-fix-20261031/failed-startup

# Real instruct integration passed: page, identity, generated histories,
# unsupported TORUK rejection and no-answer 503 after backend outage.
.\.venv\Scripts\python.exe scripts/check.py --timeout 240 --output-dir artifacts/readiness-fix-20261031 instruct-integration -- .\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --backbone-dir artifacts/qwen-chat-001/backbone --baseline-only --chat-probes --max-new-tokens 64 --output-dir artifacts/readiness-fix-20261031/integration

.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check src tests scripts
.\.venv\Scripts\python.exe -m mypy
$env:MYPYPATH = 'src'
.\.venv\Scripts\python.exe -m mypy scripts/smoke_chat_readiness.py
git diff --check
```

Lint, formatting, source type checking, readiness-script type checking and diff
checks passed. A focused inference-server rerun covers the added healthy-healthcheck
assertions. No complete project `verify.py` run is claimed for this repair.

Initial development failures were corrected: a test expected HTTP 200 from an
unhealthy `/healthz` and was updated for the deliberate 503 contract; a smoke-script
type error was fixed with JSON type narrowing. The first live evidence wrapper
ran the two Node tests successfully and saved `live-page.log` and `live-page.json`,
then its console printing failed under Windows cp1252 on a check-mark character.
This is recorded as a wrapper failure, not a chat failure. Subsequent wrappers use
`-X utf8`; the preserved live log contains the exact three HTTP 200 generated replies.

The expanded instruct probes retain known model-quality limitations, including
incorrect first-person attribution of the user's favorite color. They are
development checks, not a research superiority result or general accuracy guarantee.

## Remaining state

The actual model-loading blocker is resolved locally. Reload
`http://127.0.0.1:3000` and use the running chat; Retry connection is available if
readiness changes. The backend and web service remain running in hidden background
processes. Launcher/frontend IDs are recorded in
`artifacts/readiness-fix-20261031/local-processes.json`. For future interactive
two-terminal runs, stop the existing Toruk instances first to avoid port conflicts.

Interactive browser confirmation, more reliable answers, the original evaluated
Toruk selector and a controlled efficiency comparison remain outstanding. No host,
deployment, remote model or paid service was introduced. Nothing was committed,
pushed or deployed; existing uncommitted work was preserved.
