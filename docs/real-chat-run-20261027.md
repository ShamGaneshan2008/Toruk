# Real local chat run — 2026-10-27

The pretrained chat backbone now runs locally. **Verdict: BLOCKED for dependable
meaningful chat**. It no longer repeats `abc`, but failed arithmetic within both
supported test budgets and confused the user's identity with its own. Its correction
response did incorporate green. These probes do not supersede the retained 6/20 score.

Initial branch: `main`; HEAD `636bd4e196729a9ee48bf2f5315cb8f85abaf61a`.
Existing public-inference-gate changes were preserved. No commit, push, upload or
deployment was performed. This task downloaded public model files only.

## Exact model and file verification

Use **HuggingFaceTB/SmolLM2-135M-Instruct**, revision
`12fd25f77366fa6b3b4b768ec3050bf629380bac`. Page model ID:
`HuggingFaceTB/SmolLM2-135M-Instruct@12fd25f77366`.
This is a pretrained backbone with an optional Toruk memory selector, currently
running **BASELINE without Toruk memory**. It is not a Toruk-trained chat model.

The backbone directory was initially absent. The repository downloader fetched its
seven allowlisted files (271,177,292 bytes) into
`artifacts/chat-foundation-001/backbone` and wrote `toruk-backbone.json`.
The 269,060,552-byte `model.safetensors` has verified SHA-256
`5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`.
Config: Llama, 30 layers, width 576, 9 attention heads, 3 KV heads, vocabulary 49,152.
The existing loader uses CPU float32, the supplied chat template, local files only,
no remote model code, a 512-token selected prompt and at most 64 output tokens.
The downloaded files are Git-ignored.

`artifacts/m6-validation-001/recurrent/checkpoint.pt` is still missing. Omit
`--selector-checkpoint`; requesting a missing component prevents model loading.
TORUK mode remains disabled in the page and rejected by the API. No other checkpoint
was substituted. The minimal-lm-demo checkpoint was not used in this task.

## Terminal 1 — backend

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
$env:TORUK_BACKEND_TOKEN = 'toruk-local-chat-test-20261027'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --backbone-dir .\artifacts\chat-foundation-001\backbone --host 127.0.0.1 --port 8766
```

This shared token is a local test value, not a production secret. Wait for the listening
message. The required model and optional dependencies now exist on this device.

## Terminal 2 — website

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
$env:TORUK_BACKEND_TOKEN = 'toruk-local-chat-test-20261027'
$env:TORUK_BACKEND_URL = 'http://127.0.0.1:8766'
$env:PORT = '3000'
node .\web\vercel\scripts\dev.mjs
```

Open **http://127.0.0.1:3000**. Expect the model ID above, BASELINE and memory disabled.
Use New chat between unrelated scenarios. The page defaults to 32 output tokens;
the secondary run used its existing 64-token option. Stop servers with Ctrl+C.
Both ports were free when checked. Smoke servers were stopped after testing; if an
older instance occupies either port later, stop it in its own terminal before starting.

## End-to-end tests and diagnosis

All prompts traversed the browser's Node `/api/chat` route, authenticated Python
`/api/infer`, and the pinned backbone. Every generation returned HTTP 200, the exact
expected model ID and `memory_used: false`. Follow-up and correction histories used
the actual preceding generated assistant replies. Temperature 0, top-p 1.

The missing-model configuration problem is fixed by the verified download and the
explicit BASELINE command. There was no demonstrated role-transport or chat-template
defect. Increasing output from 32 to 64 still did not produce the arithmetic answer.
Poor model answers are not claimed fixed. No model weights, prompts, evaluation
fixtures, UI or generation algorithm were tuned to these questions.

The smoke script now supports explicit `--baseline-only`, `--chat-probes`,
`--max-new-tokens`, model-path and output-directory options. Original two-mode behavior
remains the default. The BASELINE smoke checks no memory use, unsupported TORUK
rejection, exact model identity and outage 503. New output directories preserve
historical research logs. Passing execution assertions does not mean correct answers.

Reproduce using fresh output directories:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --baseline-only --chat-probes --output-dir .readiness/real-chat-recheck
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --baseline-only --chat-probes --max-new-tokens 64 --output-dir .readiness/real-chat-recheck-64
```

- [32-token raw run, including setup turns](../artifacts/checks/real-chat-20261027/smoke/results.json): local smoke passed in 34.22 seconds.
- [64-token raw run, including setup turns](../artifacts/checks/real-chat-20261027/smoke-64/results.json): local smoke passed in 28.34 seconds.
- Focused Python tests: 20 passed. Node syntax checks and all 8 Node tests passed. `git diff --check` passed.
- GitHub for exact HEAD returned no PR-triggered workflow runs and no combined statuses. The connector covers first-page PR-triggered runs only; push/manual Actions results were not established. No remote CI pass is claimed for uncommitted work.

Full documented verification command:

```powershell
.\.venv\Scripts\python.exe scripts/verify.py --prefix real-chat --output-dir artifacts/checks/real-chat-verification-20261027
```

Final result: **exit 0, all 18 stages PASS, 106 Python tests passed**. This includes
both mypy platforms, lint/format, dependency/import/CLI checks, reproduction,
validation/summary, research execution smoke, package build, and both diff checks.
These infrastructure checks do not establish answer quality. The separate browser-API
smokes above exercised the downloaded pretrained model; the verification pipeline's
generated research checkpoints were not substituted into those chat tests.

## Actual target responses

### 32 output-token cap

arithmetic — What is 2 + 3?

`	ext
2 + 3 is a simple arithmetic operation that can be performed using basic arithmetic operations. In mathematics, addition is a fundamental operation that combines two numbers to produce
`

follow_up — What is my name?

`	ext
My name is Mira, and I'm a friendly AI chatbot. I'm here to help you with your queries, whether it's about a specific topic,
`

correction — Correction: my favorite color is green. What is my favorite color now?

`	ext
I'm glad you like the color green. It's a beautiful and versatile choice that can be found in many different forms. You can choose from various shades,
`

### 64 output-token cap

arithmetic — What is 2 + 3?

`	ext
2 + 3 is a simple arithmetic operation that can be performed using basic arithmetic operations. In mathematics, addition is a fundamental operation that combines two numbers to produce a single number.

In this case, we have two numbers, 2 and 3, and we want to add them together. The basic arithmetic
`

follow_up — What is my name?

`	ext
My name is Mira, and I'm a helpful AI chatbot designed to assist users in various aspects of life. I'm ready to help, and I'm here to assist you. What's your name?
`

correction — Correction: my favorite color is green. What is my favorite color now?

`	ext
I'm glad you like the color green. It's a versatile and timeless choice that can be found in many different forms. You can choose from various shades, from light greens to dark greens, and even some vibrant shades like navy or charcoal. Green is also a great choice for adding a touch of sophistication to any outfit
`
