# Toruk Vercel chatbot MVP — local build, not deployed

For the current host decision, missing-model blockers, deployable backend changes,
and exact account steps, read the [2026-10-27 public inference gate](public-inference-gate.md).
The measurements below are retained historical evidence.

This is a static Vercel page and Node proxy in `web/vercel`, plus a separately hosted Python/Torch inference service. The page uses **Toruk only** and gives an unavailable error when inference is not configured. The supported `toruk-ordinary-v1` checkpoint was trained on a tiny repeating `abc ` corpus; it is able to generate text but is **not a useful free-form chat model**. The M6 recurrent checkpoint is `toruk-controlled-v1`, which the ordinary generator rejects. The controlled smoke scored 0/12 exact answers.

An optional [chat foundation](chat-foundation.md) now loads a pinned, explicitly labeled pretrained SmolLM2-135M-Instruct backbone from local files and can use the M6 recurrent architecture as a separate experimental turn selector. This is a new inference mode; the ordinary checkpoint and its earlier smoke measurements below remain distinct.

## Current release decision (2026-10-26)

The fixed [20-case paired evaluation](research/chat-release-v2-results.md) answered **6/20** correctly in both BASELINE and TORUK modes. TORUK selected **1,546** prompt tokens versus **1,818** for BASELINE, a **14.96%** reduction below the preregistered **35%** target. Correction handling was **1/2** in both modes; unknown-answer handling was **0/2**. The pretrained backbone, rather than Toruk's selector, supplies the observed language capability. This is a working local prototype, not a qualified public answer service or a verified memory-efficiency result. The page displays these limitations.

The model file alone is about **269 MB**, and the v2 CPU evaluation reached **1,475,166,208 bytes private memory**. The earlier ordinary-checkpoint measurements below are not a benchmark for the pretrained chat path. Keep the Python/Torch inference service on a separately provisioned host; the small Vercel project contains only static files and Node API code. The host may cost money, sleep, or become unavailable, and no free always-on inference host is established. Vercel Hobby has usage limits even when the frontend itself builds.

For the chat foundation, start the inference server with `--backbone-dir artifacts/chat-foundation-001/backbone --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt` in place of the ordinary `--checkpoint ...` argument shown below. Both files must be provisioned on the inference host; the latter uses the controlled checkpoint only for turn selection. See [foundation setup](chat-foundation.md) for exact PowerShell commands. The frontend's project root is `web/vercel`; it must never include weights, Python packages, or local artifacts.

Before a public release, configure the protected inference service over HTTPS and set Vercel's server-side `TORUK_BACKEND_URL` and `TORUK_BACKEND_TOKEN` to that host and its shared token. Production and preview proxy functions reject plaintext HTTP backend URLs. In the Vercel project dashboard, use **Firewall → Configure → New Rule → Rate Limit**, select a fixed window and IP or JA4 key, then **Review Changes → Publish**. Hobby currently allows one rate-limit rule per project ([Vercel WAF rate limits](https://vercel.com/docs/vercel-firewall/vercel-waf/rate-limiting)); choose its threshold for the expected traffic and monitor usage. This is an operational setup step, not a control that this local task can activate. Keep the inference token private, and protect the inference host itself from direct public abuse. Do not point a browser directly at the Python service.

Local qualification commands from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_chat.py tests/test_chat_foundation.py tests/test_chat_release_eval.py tests/test_inference_server.py
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py
.\.venv\Scripts\python.exe scripts/smoke_vercel_local.py
.\.venv\Scripts\python.exe scripts/verify.py
git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check
```

The local Node preview exercises the page and proxy; it is not a Vercel build. An authentic `vercel build` requires a linked Vercel project and pulled project settings ([Vercel local build](https://vercel.com/docs/cli/deploying-from-cli)). This workspace has neither a Vercel CLI nor a linked `web/vercel/.vercel` project. Do not treat the local preview as a production runtime test. Later, after account configuration and deployment authorization, open the resulting Vercel URL and test both modes, outage behavior, mobile layout, and firewall telemetry before calling it live.

## Why inference stays off Vercel

Measured on Windows with Python 3.14.6 and CPU Torch 2.14.1 using [the retained measurement](../artifacts/vercel-feasibility-001/metrics.json):

| Item | Local measurement |
| --- | ---: |
| Supported checkpoint | 175,638 bytes; 12,112 parameters |
| Installed Torch package | 533,515,947 bytes (508.8 MiB) |
| Torch plus five installed runtime dependencies | 626,784,148 bytes (597.7 MiB) |
| Peak process working set / private memory | 312,496,128 / 688,910,336 bytes |
| Torch import / checkpoint load | 3.03 / 0.018 seconds |
| Fresh process wall time including 3 short generations | 6.53 seconds |
| Warm 16-token generation | 0.024, 0.016, 0.011 seconds |

These are **local Windows measurements**, not a Vercel Linux bundle or cold-start benchmark. Vercel documents a standard **500 MB uncompressed Python function limit**, **2 GB Hobby memory**, **300-second Hobby Fluid Compute duration**, and **4.5 MB request/response payload limit** ([function limits](https://vercel.com/docs/functions/limitations)). Vercel also announced a **5 GB large-function public beta** for Fluid Compute ([announcement](https://vercel.com/changelog/vercel-functions-can-now-be-up-to-5-gb-in-package-size)); this MVP does not rely on beta enrollment, Linux Torch packaging, or uncertain cold starts. Hobby includes usage quotas and is for personal, non-commercial projects ([Hobby plan](https://vercel.com/docs/plans/hobby)). A separate inference host may cost money or sleep, fail, or have its own quotas. **A free Vercel deployment alone cannot serve Toruk replies in this design.**

The Vercel project root is **`web/vercel`**, not the repository root. This keeps Python, Torch, checkpoints, tests and research artifacts out of the frontend upload. `public/` is static and `api/*.js` are Vercel Node functions ([Node runtime](https://vercel.com/docs/functions/runtimes/node-js), [static builds](https://vercel.com/docs/builds)). There are no npm runtime dependencies. The proxy has a 60-second backend timeout and never exposes the backend token in browser code.

## Windows PowerShell local setup

Use the existing Toruk `.venv`, or create/install the Python environment as described in the [README](../README.md). The local demo checkpoint must exist at `artifacts/minimal-lm-demo-001/train/checkpoint.pt`; use another **supported ordinary** checkpoint if necessary. In PowerShell window 1:

```powershell
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-local-token'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --checkpoint .\artifacts\minimal-lm-demo-001\train\checkpoint.pt --host 127.0.0.1 --port 8766
```

In PowerShell window 2, set the **same token** and start the Vercel-style local page:

```powershell
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-local-token'
$env:TORUK_BACKEND_URL = 'http://127.0.0.1:8766'
$env:PORT = '3000'
node .\web\vercel\scripts\dev.mjs
```

Open `http://127.0.0.1:3000`. Stop each server with **Ctrl+C**. The ordinary Python backend uses one CPU thread; the optional pretrained backbone uses two. Both process one generation at a time, allow at most 20 messages of 1,024 UTF-8 bytes each and 64 output tokens, and hold no shared user transcript. The browser holds its transcript in memory; **New chat** clears it. The proxy validates those same bounds, waits at most 60 seconds, and returns a useful error on outage. It logs input tokens, selected context tokens, output tokens, generation and proxy latency, model ID, mode and memory flag without logging message text.

Checks from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_chat.py tests/test_inference_server.py tests/test_foundation.py
node --test .\web\vercel\tests\proxy.test.mjs
.\.venv\Scripts\python.exe scripts/smoke_vercel_local.py
.\.venv\Scripts\python.exe scripts/verify.py
git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check
```

The smoke script starts and stops both local servers, verifies a Toruk reply and backend-outage error, and records a plain-context probe result. Its output is under `artifacts/vercel-feasibility-001/`.

## Vercel Hobby setup after review

No deployment was performed in this task. To prepare one later:

1. Arrange an independently hosted HTTPS Python service with Torch, the supported ordinary checkpoint, enough RAM (local private memory reached 689 MB; allow substantial headroom), and the command `python -m toruk_lm.inference_server --checkpoint /path/to/checkpoint.pt --host 0.0.0.0 --port $PORT`. Put TLS in front of it and set a long random `TORUK_BACKEND_TOKEN` there. Do not expose that token in a public repository or browser bundle. A free always-on host is **not** established here.
2. Create a Vercel Hobby project with **Root Directory `web/vercel`**, Framework Preset **Other**, static output `public`, and no build command. Add server-side project environment variables `TORUK_BACKEND_URL=https://your-inference-host.example` and `TORUK_BACKEND_TOKEN=<same secret>` for the environments you intend to use ([environment variables](https://vercel.com/docs/environment-variables)). Keep both variables private; do not prefix them with browser-public environment conventions. Changes apply to the next deployment.
3. Only after authorization to deploy, use Vercel's normal preview/build flow and inspect its build log, `/api/status`, page, reply, outage behavior and runtime logs. A Vercel URL must be opened and tested before claiming a live public chatbot ([CLI deployment guide](https://vercel.com/docs/projects/deploy-from-cli)). The Vercel CLI was unavailable in this local workspace, so no authentic `vercel build` output is claimed.

## Efficiency and capability status

The ordinary model's `selected_context_tokens` is the last local context window (32 tokens in the demo checkpoint). This is an architectural cap, **not** validated selective memory. The recurrent `Session` mechanism is trained for controlled worlds; its checkpoint is incompatible with ordinary free-form generation and the relevant smoke answer score is zero. Therefore this MVP does not enable a Toruk memory mode or claim fewer tokens at equal quality.

The fixed, author-written [chat probes](../configs/chat-comparison-v1.json) and [comparison script](../scripts/compare_chat_context.py) score answer quality and token/latency totals. The local plain path answered **0/3** probes exactly. No valid selected-context endpoint exists; the script records `NO_VALID_CONTEXT_PATH` and `efficiency_claim: false` ([result](../artifacts/vercel-feasibility-001/comparison.json)). These are not research held-out answers and were not used for tuning.

**Status:** CHAT UI WORKING **locally**; TORUK INFERENCE WORKING **as bounded text generation through the separate backend**, not as useful free-form chat; EFFICIENCY CLAIM VERIFIED **no**. Public availability additionally requires a reviewed inference host and a later tested Vercel deployment.

## Verification record (2026-10-26)

Local commands and outcomes:

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_chat.py tests/test_inference_server.py tests/test_foundation.py` | 18 passed |
| `npm.cmd --prefix web/vercel run check` and `npm.cmd --prefix web/vercel test` | Syntax checks passed; 4 Node tests passed |
| `.\.venv\Scripts\python.exe scripts/check.py --timeout 90 --output-dir artifacts/vercel-feasibility-001 smoke-final -- .\.venv\Scripts\python.exe scripts/smoke_vercel_local.py` | Page, real Toruk continuation, comparison, and outage passed in 12.09 seconds; [log](../artifacts/vercel-feasibility-001/smoke-final.log) |
| `.\.venv\Scripts\python.exe scripts/verify.py --prefix vercel-mvp --output-dir artifacts/checks/vercel-mvp-verification` | 95 tests, lint, format, research smoke, package build, and diff checks passed; overall exit 1 because two mypy stages failed on NumPy 2.5.4's Python 3.12 `type` syntax while the project targets Python 3.11 |
| `.\.venv\Scripts\python.exe -m mypy --python-version 3.14 src/toruk_lm/chat_runtime.py src/toruk_lm/inference_server.py scripts/compare_chat_context.py scripts/smoke_vercel_local.py` | Passed after correcting new script annotations |
| `git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check` | Passed |

Vercel CLI is absent, so an authentic local `vercel build` was unavailable. The static page and API routes were exercised by the local Node preview, not by Vercel's build/runtime. GitHub Actions for commit `add917398efa061cc67b1b10aff3853acf3c526c` showed no associated workflow runs or commit statuses; local uncommitted changes are not represented by remote CI.
