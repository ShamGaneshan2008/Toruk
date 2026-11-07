# Local instruct chat on Windows PowerShell

Qwen/Qwen2.5-0.5B-Instruct is a third-party, Apache-2.0 instruct backbone,
not a Toruk-trained model ([official model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)).
Toruk supplies the server, limits, telemetry, and optional experimental context selection.
The [7 November launch gate](research/chat-launch-gate-20261107.md) includes fresh
proxy/server/model replies, failures, hosting measurements and the deployment decision.
Local use is an explicitly experimental pretrained-model demonstration. All tested
modes failed the frozen answer-quality gate; public deployment remains blocked.
For the frozen research comparisons, actual-component ablations and exploratory
draft, see the [independent replication package](research/independent-replication-v1-results.md).
An optional, explicitly named heuristic selector can now be enabled for the
[same-backbone context comparison](context-selection.md). It is separate from the
missing evaluated M6 checkpoint and does not restore that learned-memory result.

For the disabled-chat diagnosis and actual request evidence, see the
[readiness repair](research/readiness-fix-20261031.md). `--checkpoint` selects a
Toruk ordinary smoke fixture. Instruct chat requires `--backbone-dir` as below.

Before downloading: the Qwen model is Apache-2.0, about 1 GB on disk, and needs
about 2 GB for float32 parameters plus Python/Torch runtime and generation overhead.
The fresh Windows profile reached about 2.68 GB summed resident memory and 4.66 GB
private committed memory during startup/generation. Allow at least 6 GB available
memory as an estimate, preferably 8 GB headroom; this is not a measured Linux minimum.
No GPU is required; CPU inference uses two Torch threads. Close memory-heavy apps
if necessary. If the verified model files already exist locally, no download is
needed. Check the current installation first:

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
Test-Path .\artifacts\qwen-chat-001\backbone\toruk-backbone.json
Test-Path .\artifacts\qwen-chat-001\backbone\model.safetensors
.\.venv\Scripts\python.exe -c "import torch, transformers, safetensors; print(torch.__version__, transformers.__version__, safetensors.__version__)"
```

Run from the repository root. Python 3.11+ and Node 22+ are required.
For a new environment (omit creation if `.venv` already exists):

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -e '.[chat,dev]'
.\.venv\Scripts\python.exe scripts/download_chat_backbone.py --model qwen2.5
```

The downloader uses revision `7ae557604adf67be50417f59c2c2f167def9a775` and checks
the weight SHA-256 `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
It downloads about 1 GB into Git-ignored `artifacts/qwen-chat-001/backbone`.
Inference uses CPU float32 (about 2 GB for parameters, plus runtime overhead), two
Torch threads, local files only, and no remote model code. Download into a fresh
directory; the downloader refuses an existing nonempty directory. A verified
existing download can be reused without running the downloader again.

Terminal 1, backend:

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
$env:TORUK_BACKEND_TOKEN = 'local-development-only-token'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --backbone-dir .\artifacts\qwen-chat-001\backbone --host 127.0.0.1 --port 8766
```

Wait for **`Chat ready: Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf`** and the inference
listening message. `CHAT DISABLED [reason]` followed by `Readiness service only`
means the model did not load: follow the indicated setup action and restart the
backend. No model fallback occurs. Terminal 2, website:

```powershell
Set-Location 'C:\Users\susee\VS_CODE_PROJECT\Toruk'
$env:TORUK_BACKEND_TOKEN = 'local-development-only-token'
$env:TORUK_BACKEND_URL = 'http://127.0.0.1:8766'
$env:PORT = '3000'
$env:VERCEL_ENV = 'development'
node .\web\vercel\scripts\dev.mjs
```

Open `http://127.0.0.1:3000`. Expect the Qwen model ID, BASELINE, and memory disabled.
Reload once after a code update. If the page was opened before the model was ready,
click **Retry connection** after backend startup. A successful readiness check clears
the old error and enables both the message box and Send. If servers already occupy
these ports, stop those Toruk instances before launching replacements.
The UI defaults to 64 output tokens, matching the launch-gate budget.
Stop both servers with Ctrl+C in their respective terminals. The literal token
above is for loopback development. Backend credentials stay in server environments;
the browser sends requests only to the web proxy.

Terminal 3, test the same route the browser calls:

```powershell
Invoke-RestMethod 'http://127.0.0.1:3000/api/status'
Invoke-RestMethod 'http://127.0.0.1:8766/api/status'
Invoke-RestMethod 'http://127.0.0.1:8766/healthz'
Start-Process 'http://127.0.0.1:3000'
$payload = @{
  messages = @(@{ role = 'user'; content = 'What is 2 + 3?' })
  mode = 'BASELINE'
  max_new_tokens = 64
  temperature = 0
  top_p = 1
} | ConvertTo-Json -Depth 6
$reply = Invoke-RestMethod 'http://127.0.0.1:3000/api/chat' -Method Post -ContentType 'application/json' -Body $payload
$reply.answer
$reply.metrics
```

For a follow-up API request, include the previous user message and actual generated
assistant answer before the next user message. The service is stateless; the web
page keeps the transcript in memory. New chat clears it.

Automated integration and development-quality probes start and stop their own
backend and Node proxy on free loopback ports:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --backbone-dir .\artifacts\qwen-chat-001\backbone --baseline-only --chat-probes --max-new-tokens 64 --output-dir .readiness/qwen-chat-check
.\.venv\Scripts\python.exe -m pytest -q tests/test_chat.py tests/test_chat_foundation.py tests/test_chat_release_eval.py tests/test_inference_server.py
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
.\.venv\Scripts\python.exe scripts/smoke_chat_readiness.py --output-dir .readiness/unavailable-chat-check
$env:TORUK_LIVE_WEB_URL = 'http://127.0.0.1:3000'
node --test .\web\vercel\tests\ui.test.mjs
Remove-Item Env:TORUK_LIVE_WEB_URL
.\.venv\Scripts\python.exe scripts/verify.py --prefix local-chat --output-dir .readiness/local-chat-verification
git diff --check
```

`/api/status` is the canonical backend status route; `/status` is now an alias.
`/healthz` returns HTTP 200 only while the model is ready and HTTP 503 otherwise.
Status JSON remains HTTP 200 with an explicit `ready` flag and a safe `error_code`.
Missing demo checkpoints, missing/invalid backbone files, absent chat dependencies,
unavailable optional memory and stopped workers have separate actionable reasons.
Public responses never echo raw loading exceptions, private paths or tokens.

The UI tests execute the real page handlers with a DOM stand-in, including typed
input and follow-up history; the optional live case calls the real local proxy.
They do not replace an interactive browser/visual check. For saved Node test output
through `scripts/check.py` on Windows, use `python.exe -X utf8 scripts/check.py ...`
so console check marks do not fail under a legacy Windows output encoding.

Use a fresh output directory to retain prior evidence. Read exact responses in
`results.json`: successful HTTP or script execution does not mean useful answers.
The eight qualification scenarios and phrase rules are in
`configs/chat-qualification-v1.json`. These are development probes, not held-out
research evidence. Some phrase scores miss attribution errors or valid paraphrases.

Limits: 20 messages, 1,024 UTF-8 bytes per message, 8,192 history bytes, 16,384 body
bytes, 512 selected prompt tokens (including the server's conversation instructions
and chat template), 64 generated tokens, one generation at a time, eight connection
threads, a killable 45-second generation deadline, and a 60-second proxy deadline.
Old turns are dropped whole to fit; an overlong latest turn is rejected. This can
lose earlier facts. Telemetry counts the full formatted history before selection,
the actual formatted prompt sent to the model, generated token IDs including the
stop token, backend latency, and proxy latency. It does not measure all internal
model compute or establish end-to-end token savings.

The evaluated M6 selector at `artifacts/m6-validation-001/recurrent/checkpoint.pt`
is absent here. Explicitly selecting that checkpoint fails visibly; no replacement
was trained or substituted. TORUK can separately use the available trained JSON v2
selector or a named heuristic. Those selectors also failed the launch quality gate.
Restore the original evaluated weights before testing that path or making a matched
same-backbone efficiency comparison. Synthetic smoke checkpoints are incompatible
with the historical selector's evidence and cannot be silently substituted.

The separate [Ollama local-backbone path](research/local-backbone-llama32-20261101.md)
uses `--ollama-model` with its full `--ollama-digest`. Both local backbone paths
accept an explicit trained JSON `--selector-checkpoint`; the heuristic
`--context-selector` option requires `--backbone-dir`. Choose one selector option.
These integrations do not establish an accuracy or efficiency advantage.

For an explicit local context comparison, append **one** of these options to the
backend command, keeping the same Qwen directory. Then choose TORUK on the page:

Use `--selector-checkpoint .\artifacts\chat-selector-v2-20261101\selector.json`
for the separately trained ranker, or `--context-selector lexical-v2` for the
deterministic heuristic. Append these options to the backend command;
they are not separate PowerShell commands. BASELINE remains available
with either selector loaded. The Toruk-owned conversational checkpoint is research
CLI-only and failed 0/25 fresh regression answers; it is not a chat default or a
supported `--checkpoint` format for this inference server.

If requests say **busy**, wait for the current generation and retry; there is no
queue. If generation times out, restart Terminal 1, then click Retry connection.
For a malformed/overlong conversation, shorten the latest input or use New chat.
Stopping Terminal 1 makes the proxy return an explicit 503 without a generated
answer. Stop both terminal processes with Ctrl+C, then confirm the two URLs stop
responding. The automated gate uses free loopback ports and cleans up only its own
processes; it does not stop any Toruk servers you already have running.

Frozen selector artifacts have byte-sensitive hashes. Keep the repository's
`.gitattributes` rules: the v2 `selector.json` and `data/manifest.json` require
CRLF, while the frozen scripts and split data require LF. Changing only line
endings can invalidate the recorded checkpoint and evaluation hashes.

Historical SmolLM remains supported via `--model smollm2` in the downloader and its
existing backbone directory in the inference server. Its original template remains
unchanged for archived research reproduction. The Hugging Face deployment recipe
still explicitly selects SmolLM; Qwen has not been qualified for that deployment.
Ordinary `toruk-ordinary-v1` checkpoints remain supported as labeled smoke fixtures
via `--checkpoint`. The old minimal-demo file is absent in this checkout; its
documented command needs that artifact restored. Research training, checkpoint
formats, and archived evaluation fixtures are unchanged.
