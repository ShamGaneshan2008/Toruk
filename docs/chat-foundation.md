# Experimental conversational foundation

Toruk's ordinary 12,112-parameter checkpoint learned a four-byte pattern, not conversation. This optional local foundation uses the **pretrained HuggingFaceTB/SmolLM2-135M-Instruct backbone**, pinned to revision `12fd25f77366fa6b3b4b768ec3050bf629380bac` (Apache-2.0 [model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct)). The pretrained model supplies language ability. Toruk's own frozen M6 recurrent architecture is a separate, experimental selector of earlier verbatim turns. It does not alter the backbone weights and has not shown a reliable quality or efficiency advantage.

## Windows PowerShell setup

From the repository root, with its existing CPU Python environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[chat]'
.\.venv\Scripts\python.exe scripts/download_chat_backbone.py --output artifacts/chat-foundation-001/backbone
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-secret'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --backbone-dir artifacts/chat-foundation-001/backbone --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --host 127.0.0.1 --port 8766
```

The downloader fetches only six pinned files, verifies the 269 MB safetensors SHA-256 `5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`, and writes a local identity manifest. The server loads local files only. The separate inference host must retain the model's license/attribution if the weights are redistributed. If the M6 checkpoint is unavailable, omit `--selector-checkpoint`; BASELINE still works and TORUK is visibly unavailable. The old `--checkpoint` option still accepts only `toruk-ordinary-v1` and cannot reinterpret M6.

The downloaded backbone directory is ignored by Git; provision those files separately on any inference host. No model weights are placed in the Vercel frontend project.

In a second PowerShell window:

```powershell
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-secret'
$env:TORUK_BACKEND_URL = 'http://127.0.0.1:8766'
$env:PORT = '3000'
node .\web\vercel\scripts\dev.mjs
```

Open `http://127.0.0.1:3000`; stop both servers with **Ctrl+C**. The web page shows the backbone, BASELINE/TORUK mode, memory use, input and selected token counts, and experimental limitations. BASELINE gives the backbone recent turns. TORUK runs the frozen M6 recurrent network over earlier turns, ranks their learned summaries against the latest question, and supplies up to two older turns plus the recent turns. This score was **not trained as semantic retrieval**, and the selector may omit a needed fact. The same backbone and tokenizer generate both modes. Sampling controls are temperature 0–2 and top-p 0–1; zero temperature is greedy. The model's chat template supplies role boundaries and assistant generation prefix; EOS and the output cap stop generation.

Requests are limited to 20 messages, 1,024 UTF-8 bytes each, 8 KiB total, 512 backbone prompt tokens and 64 output tokens. The Python server runs one generation at a time with two CPU threads. The Vercel proxy has a 60-second backend timeout and logs token counts, latency, backbone/model ID, mode and memory flag without message text. It keeps the backend token server-side. A separately hosted HTTPS inference service is required for Vercel; it may incur cost or outages. See the [Vercel guide](vercel-chat.md).

## Fixed local evaluation

The later, preregistered [20-case release evaluation](research/chat-release-evaluation-v2.md) is the current quality check. Its [paired result and raw answers](research/chat-release-v2-results.md) show **6/20 correct in each mode**, **14.96% fewer selected prompt tokens** in TORUK, and no execution errors. The primary 35% reduction threshold failed, and both modes missed the 60% conversational-quality floor. The measured quality tie therefore does **not** establish quality-preserving efficiency. The release set was evaluated once without changing the questions, scoring, backbone, or selector afterward.

The [protocol](research/chat-foundation-protocol.md) and [seven-category questions](../configs/chat-foundation-eval-v1.json) were recorded before inference. Run:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_chat_foundation.py --backbone-dir artifacts/chat-foundation-001/backbone --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --output artifacts/chat-foundation-001/my-evaluation.json
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py
```

The retained [paired result](../artifacts/chat-foundation-001/eval-results.json) has **0/7 strict-format correct** in each mode, zero execution failures, 710 full input tokens, 710 BASELINE selected tokens and 532 TORUK selected tokens. Both answered the planet and long-context code with the correct fact but failed the requested short output format; they failed reference, correction, preservation or unknown-answer tasks. The long-context case answered `The vault code is LIME42.` in both modes with 297 versus 119 selected tokens. This one case supports a measurable token reduction, not a general efficiency claim. The first aggregate run accidentally lost its raw per-case JSON to an evidence-filename collision; its log is retained. A later identical frozen rerun retained raw outputs. The first comparison rule also marked 0/7 versus 0/7 as efficiency; the [protocol](research/chat-foundation-protocol.md) records the post-result conservative correction. **Efficiency is not verified.**

The retained evaluation used 18.75 seconds in-process and reached 1,462,267,904 private bytes on Windows, below its 3 GiB stop. Per-mode aggregate generation/selection latency was 6,543 ms BASELINE versus 6,435 ms TORUK; those timings are one run and do not prove a speedup. Language quality comes from the pretrained backbone, and the selector's relevance has not been trained or validated for chat.

## Verification and readiness

Local versions: Python 3.14.6, Torch 2.14.1+cpu, Transformers 5.20.2, Safetensors 0.8.0, Node 24.19.0, npm 11.17.0. From repository HEAD `add917398efa061cc67b1b10aff3853acf3c526c`, with uncommitted user and task work preserved:

| Exact command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_chat_foundation.py tests/test_inference_server.py tests/test_chat.py tests/test_foundation.py` | 22 passed |
| `npm.cmd --prefix web/vercel run check` and `npm.cmd --prefix web/vercel test` | Syntax checks passed; 6 tests passed |
| `.\.venv\Scripts\python.exe scripts/check.py --timeout 120 --output-dir artifacts/chat-foundation-001 full-local-chat-smoke -- .\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py` | Passed: page, both modes, model identity, selected tokens and outage 503; [log](../artifacts/chat-foundation-001/full-local-chat-smoke.log) |
| `.\.venv\Scripts\python.exe scripts/check.py --timeout 90 --output-dir artifacts/chat-foundation-001 ordinary-path-regression-fixed -- .\.venv\Scripts\python.exe scripts/smoke_vercel_local.py` | Passed: old ordinary checkpoint still generates its `abc` pattern |
| `.\.venv\Scripts\python.exe -m toruk_lm generate --checkpoint artifacts/minimal-lm-demo-001/train/checkpoint.pt --prompt 'abc ' --max-new-tokens 16` | Passed; generated `abc abc abc abc ` |
| `.\.venv\Scripts\python.exe scripts/verify.py --prefix chat-foundation --output-dir artifacts/checks/chat-foundation-verification` | 98 tests, lint, format, research smoke, build and diff checks passed; overall exit 1 due the existing NumPy 2.5.4 stub's Python 3.12 `type` syntax under the project's Python 3.11 mypy target |
| `.\.venv\Scripts\python.exe -m mypy --python-version 3.14 src/toruk_lm` and script mypy with `MYPYPATH=src` | Passed: 21 source files and 3 new scripts; this does not replace the documented gate |
| `git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check` | Passed for tracked changes |

An initial ordinary smoke failed only because its assertion expected the old page notice; the assertion was updated and the same path passed. GitHub Actions for the exact HEAD commit returned no associated workflow runs or commit statuses; it has not tested these uncommitted changes. The Vercel CLI is absent, and no Vercel build, deployment or public URL was verified. **Local deployment passes; Vercel frontend readiness remains blocked on an authentic Vercel build and runtime check.**
