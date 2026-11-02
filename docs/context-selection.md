# Same-backbone context selection experiment

This milestone compares bounded context selection with ordinary recent-turn
context using one local pretrained **Qwen/Qwen2.5-0.5B-Instruct** backbone.
The model supplies language ability. The heuristic selector is Toruk integration
code, not a Toruk-trained model and not the absent M6 learned-memory checkpoint.
See the [frozen protocol](research/context-eval-protocol-v1.md) and
[measured result](research/context-eval-results-v1.md).

Use the already installed, verified model at `artifacts/qwen-chat-001/backbone`.
No download is required on the tested machine. For a new installation, follow
[local setup](local-chat.md); the Apache-2.0 model is about 1 GB on disk and CPU
float32 needs about 2 GB for parameters plus runtime overhead. Python 3.11+,
Node 22+, Torch, Transformers and Safetensors are required.

Stop previous Toruk instances occupying ports 8766/3000 before starting replacements.
Terminal 1, Windows PowerShell:

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
$env:TORUK_BACKEND_TOKEN = 'local-development-only-token'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --backbone-dir .\artifacts\qwen-chat-001\backbone --context-selector lexical-v2 --host 127.0.0.1 --port 8766
```

Wait for `Chat ready`. Terminal 2:

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
$env:TORUK_BACKEND_TOKEN = 'local-development-only-token'
$env:TORUK_BACKEND_URL = 'http://127.0.0.1:8766'
$env:PORT = '3000'
node .\web\vercel\scripts\dev.mjs
```

Open `http://127.0.0.1:3000` and reload after code changes. The page displays the
backbone and selector identity. Select BASELINE or TORUK from Context; response
metadata includes mode, selector ID, full input tokens, actual selected prompt
tokens, output tokens and latency. "Context selection" does not mean persistent
learned memory. TORUK is a stateless, query-conditioned selection of verbatim
messages from the supplied transcript. Use New chat between independent scenarios.

`lexical-v1`: latest three messages plus two query-ranked older user messages.
`lexical-v2`: the same rule, retaining at most two immediately following explicitly
marked correction messages as well. The 512-token prompt fitting cap still applies
after selection. Conflicting facts and multi-hop chains have no general guarantee.
The selector scans all supplied history; saving backbone tokens is not a claim
that the whole pipeline read fewer tokens. Input/message/output/concurrency and
timeout limits from the local guide remain unchanged.

Reproduce the frozen final comparison from a third PowerShell terminal. Each run
starts and stops its own isolated backend/proxy on free loopback ports. Run them
sequentially with otherwise idle CPU, and use new output directories:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_context_selection.py --fixture configs/context-eval-final-v1.json --backbone-dir artifacts/qwen-chat-001/backbone --context-selector lexical-v1 --output-dir .readiness/context-final-v1
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_context_selection.py --fixture configs/context-eval-final-v1.json --backbone-dir artifacts/qwen-chat-001/backbone --context-selector lexical-v2 --output-dir .readiness/context-final-v2
```

Each `raw.json` contains the immutable synthetic dataset, selected message IDs and
text, source/config/tokenizer hashes, actual answers, scores, complete evidence
coverage, measured tokens and end-to-end HTTP latency. The summary prints to the
terminal. Run development with `configs/context-eval-dev-v1.json`; never change the
final set or tune further to its answers. `scripts/make_context_eval.py` documents
fixture construction and refuses to overwrite existing files; do not rerun it over
the checked-in frozen fixtures.

The content scorer uses fixed word-boundary accepted/forbidden phrases. Unsupported
flags mean incorrect non-abstaining answers. They do not exhaustively detect
unsupported claims; review raw text and evidence retention separately. Correct
guesses with incomplete required evidence are not successful grounded retrieval.
These short, shared-template cases are a pilot, not a paper-grade benchmark.

Checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_context_selection.py tests/test_chat_foundation.py tests/test_chat.py tests/test_chat_release_eval.py tests/test_inference_server.py
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
$env:TORUK_LIVE_WEB_URL = 'http://127.0.0.1:3000'
$env:TORUK_TEST_CONTEXT = 'lexical-v2'
node --test web/vercel/tests/ui.test.mjs
Remove-Item Env:TORUK_LIVE_WEB_URL
Remove-Item Env:TORUK_TEST_CONTEXT
.\.venv\Scripts\python.exe -X utf8 scripts/verify.py --prefix context --output-dir .readiness/context-verification
git diff --check
```

The live UI test executes actual page handlers in a DOM stand-in and sends normal,
follow-up, correction and missing-answer requests through the real proxy. It proves
enabled controls and transport, not interactive browser/visual behavior or correct
answers. Real browser confirmation requires a connected browser. GitHub Actions
now covers Python checks and model-free Node tests; the optional live/model cases
are skipped unless separately configured. No remote inference or deployment follows
from local tests.
