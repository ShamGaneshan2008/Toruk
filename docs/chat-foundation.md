# Experimental conversational foundation

For this device's current model files, working BASELINE commands, and verbatim
browser-API responses, see the [2026-10-27 real chat run](real-chat-run-20261027.md).
The original M6 selector is missing here; that run explicitly disables Toruk memory.

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

To test a different locally supported instruct backbone, download a fixed revision with its independently obtained SHA-256:

```powershell
.\.venv\Scripts\python.exe scripts/download_chat_backbone.py --model OWNER/MODEL --revision FULL_REVISION --sha256 EXPECTED_MODEL_SAFETENSORS_SHA256 --output artifacts/other-chat-backbone
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --backbone-dir artifacts/other-chat-backbone --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --host 127.0.0.1 --port 8766
```

This path currently requires a single `model.safetensors`, a Transformers causal LM and tokenizer that load locally without remote code, a chat template, and EOS/pad tokens. It retains the 512-token prompt cap. The manifest records the exact model, revision, and weight hash; status and response metrics expose the model identity. A different model has not been validated by the retained evaluation. For a BASELINE/TORUK comparison, use the same backbone, decoding settings, and questions in both modes. Backbone quality is separate from Toruk selector performance.

### Local Ollama backbone on a small GPU

The inference server also accepts a model already installed in **local** Ollama at `127.0.0.1:11434`. Pin its full digest from Ollama's `/api/tags`; do not rely on a mutable tag alone. For example, in PowerShell:

```powershell
$expectedDigest = 'a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72'
$tag = (Invoke-RestMethod http://127.0.0.1:11434/api/tags).models | Where-Object name -eq 'llama3.2:latest'
if ($null -eq $tag -or $tag.digest -ne $expectedDigest) { throw 'The installed Llama 3.2 model does not match the tested digest.' }
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-secret'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --ollama-model $tag.name --ollama-digest $expectedDigest --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --host 127.0.0.1 --port 8766
```

Start `ollama serve` in another PowerShell window first if the local service is stopped. The tested `llama3.2:latest` is the 3B Q4_K_M instruct variant. It was already installed on this device, so this run downloaded zero bytes. On another machine, `ollama pull llama3.2:3b-instruct-q4_K_M` downloads about 2.0 GB; verify its full digest before using these commands. The [Ollama model listing](https://ollama.com/library/llama3.2/tags) identifies the variant, and the [Meta model card](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) gives its Llama 3.2 Community License. This is a custom license, not Apache-2.0. The measured local disk model is 2,019,393,189 bytes. At a 4,096-token Ollama context, the loaded runner occupied 2,347,688,263 bytes of VRAM; plan for roughly 2.5 GiB GPU memory plus OS/driver headroom and host RAM. The tested device has 4,096 MiB VRAM and 16,831,897,600 bytes physical RAM. Free system RAM was about 1.0–1.5 GiB during the run, so other applications can affect cold-load latency and reliability.

The server checks the digest, warms the model before advertising readiness, uses Ollama's token counts to fit the same 512-token prompt ceiling, and uses the same frozen Toruk selector and model in both modes. Status and reply metrics show the model and digest. Omit `--selector-checkpoint` if unavailable; TORUK then remains disabled. The historical SmolLM2 research result remains tied to its original backbone. See the [separate Llama 3.2 local comparison](research/local-backbone-llama32-20261101.md) for raw replies, RAM, VRAM, latency, and limitations.

To use the separately trained **Toruk chat selector v1** from the local research run, replace the `--selector-checkpoint` value above with `artifacts/chat-selector-v1-20261101/selector.json`. This JSON checkpoint is a supervised lexical turn ranker, distinct from the M6 controlled-world `.pt` checkpoint. It reads all supplied history, keeps at most two older evidence turns plus the latest three, and is bounded by the same 512-token backbone prompt limit. Status and chat responses identify the selector format and SHA-256; the page shows its identity when TORUK mode is available and whether TORUK was active for the reply. The [frozen protocol](research/chat-selector-v1-protocol.md) and [result report](research/chat-selector-v1-results.md) describe what it learned and where it fails. The pretrained Ollama model still supplies conversational language ability.

To run the separate **v2 trained selector**, use the same verified `$expectedDigest` and `$tag` from above, then start the inference server in one PowerShell window:

```powershell
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-secret'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --ollama-model $tag.name --ollama-digest $expectedDigest --selector-checkpoint artifacts/chat-selector-v2-20261101/selector.json --host 127.0.0.1 --port 8766
```

Start the Node proxy using the second window below and open `http://127.0.0.1:3000`. Status and replies show `toruk-chat-selector-v2`, its checkpoint SHA, the pretrained backbone identity, selected token counts, latency, and whether selection ran. The [v2 held out result](research/chat-selector-v2-results.md) found lower answer quality than recent-turn context, so TORUK remains an experimental mode; it does not indicate a reliable memory advantage.

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
