# Public inference and Vercel gate — 2026-10-27

Public chatbot launch is **BLOCKED**. No deployment, upload, commit or push was authorized
or performed. There is no tested public URL. This document supersedes earlier deployment
readiness statements in `vercel-chat.md`; historical evaluation reports remain unchanged.

## Evidence and separate verdicts

Initial Git state: clean `main`, HEAD `636bd4e196729a9ee48bf2f5315cb8f85abaf61a`,
origin `ShamGaneshan2008/Toruk`. Changes made for this gate remain uncommitted.
The retained v2 evaluation records the older base `add9173`; its source hashes and
results are historical evidence, not proof of this working tree or deployed runtime.

| Gate | Verdict | Evidence |
| --- | --- | --- |
| Meaningful chat quality | FAIL | Retained SmolLM2 BASELINE and TORUK each scored 6/20. Available ordinary model repeats zeros. |
| Toruk memory integration | HISTORICAL OPERATIONAL PASS; current qualification BLOCKED | v2 selector used in 13/20 TORUK cases. Original M6 weights are missing here; semantic memory quality unproven. |
| Token reduction | BELOW TARGET | 1,818 → 1,546 selected prompt tokens, 14.96%, versus preregistered 35%. Selector itself still reads the history. |
| Answer-quality preservation | INCONCLUSIVE | Identical 6/20 scores on these synthetic probes; baseline fails 60% quality floor. No general preservation claim. |
| Local end-to-end operation | PASS for explicitly identified ordinary model | Current page/proxy/backend and outage smoke passed; evaluated chat pair cannot be rerun without its weights. |
| Public inference feasibility | CONDITIONAL; NOT VERIFIED | Prepared Docker recipe, but no Linux build, host account qualification, original selector, or deployed request test. |

Read [v2 raw evidence](../artifacts/chat-release-v2/raw.json) and
[retained interpretation](research/chat-release-v2-results.md). No new evaluation or
training changed those quality scores. The available ordinary checkpoint measured here is
`artifacts/foundation-001/train/checkpoint.pt`, 573,431 bytes, SHA-256
`0285d3fb6adc4e49a92b6c2f4f8226f607d8660d46d3a19d5fea33ca48065e94`.
The earlier `minimal-lm-demo-001/train/checkpoint.pt`, chat backbone directory, and
M6 selector checkpoint are absent. No other model is silently substituted.

## Host choice and current official terms

Select **Hugging Face Docker Space, CPU Basic, protected visibility**, for an
authenticated qualification backend with private source. This is a conditional
engineering choice, not a successful deployment or a zero-cost promise.

The [official Spaces overview](https://huggingface.co/docs/hub/main/en/spaces-overview)
documents 2 vCPU, 16 GB RAM, 50 GB ephemeral disk and no hourly CPU Basic charge.
However, new compute Spaces require a paid plan. The
[current Hub SDK guide](https://huggingface.co/docs/huggingface_hub/v2.2.0/guides/manage-spaces)
explicitly requires PRO for individual Docker/Gradio CPU Basic Spaces (otherwise HTTP 402).
Protected visibility also requires PRO or Team/Enterprise: source stays private while
the app origin is reachable. A fully private Space additionally requires Hugging Face
platform authorization and is not directly compatible with this proxy's single backend
Bearer header. Do not point Vercel at a private Space and expect its custom token to
authenticate to Hugging Face.

[CPU Basic sleeps after 48 hours of inactivity](https://huggingface.co/docs/hub/spaces-gpus).
Wakeup and model load can exceed the proxy timeout; retry after checking readiness.
There is no always-on guarantee. No official numeric quota for this custom Docker
route was established; do not invent a requests-per-minute allowance. The
[Hub rate limits](https://huggingface.co/docs/hub/rate-limits) govern Hub API/download
operations, not a throughput guarantee for `/api/infer`.

| Alternative | Current terms and fit |
| --- | --- |
| Render Free | [512 MB RAM, less than one CPU](https://render.com/pricing); insufficient headroom against retained chat memory and current two-process ordinary benchmark. [750 instance hours/workspace/month, sleep after 15 minutes, about one-minute wakeup, ephemeral disk](https://render.com/docs/free). No durable disk on Free; no verified numeric ephemeral capacity for this model. Reject for this package. |
| Vercel Python inference | Keep Torch/weights out of the frontend functions. Linux bundle/startup and memory were not qualified; no claim that a Windows dependency measurement establishes Linux compatibility. |
| Paid container/VM | A fallback requiring an account and budget. Start with at least 4 GB RAM and two CPU cores as an estimate for process isolation, then measure Linux peak memory and cold start. Not a tested specification or free tier. |

[Vercel Hobby](https://vercel.com/docs/plans/hobby) is personal/non-commercial and
usage-limited: currently 100 GB fast transfer, 1M function invocations, 4 CPU hours,
360 GB-hours provisioned memory; usage exhaustion can pause service. These are
account allowances, not promised chatbot capacity. Its frontend does not provide
the external inference computer.

The pinned [SmolLM2 revision's model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/blob/12fd25f77366fa6b3b4b768ec3050bf629380bac/README.md)
declares Apache-2.0. Serving is compatible with that license; preserve applicable
license/notice/attribution obligations when distributing weights. The downloader
now retains that card. No Toruk root LICENSE file was found; this task does not
invent a license for Toruk source or checkpoint. Owner rights and publication scope
must be settled before making either public. Protected source avoids public copying,
but still uploads code and the selector to the hosting provider: that needs separate authorization.

## Sizes, timings and limits of the measurements

The intended chat backbone weight file is approximately 269 MB in retained evidence,
loaded as float32 (roughly 540 MB for 135M parameters alone). Its expected SHA-256 is
`5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`.
Exact full backbone download and selector byte counts cannot be measured here because
those files are absent. The package manifest records exact selector size once restored.

Retained v2 chat requests used at most 32 new tokens, with latency 341–1,586 ms BASELINE
and 342–1,722 ms TORUK. First recorded requests were 341 and 342 ms respectively;
these exclude server startup and network. Reported private memory was 1,475,166,208
bytes; that field is a process snapshot, not a sampled peak guarantee. Fresh startup,
full cold first-response time, peak memory, 64-token latency and concurrent behavior
for the intended isolated chat pair remain **UNMEASURED**. They must be measured after
restoring the exact models, then again on the host.

Current Windows measurements for the available ordinary checkpoint only:

| Measurement | Result |
| --- | ---: |
| Server startup including model worker | 5.860 s |
| Startup plus first bounded request | 5.944 s |
| First / second 64-token HTTP request | 83.6 / 73.3 ms |
| Sampled process-tree peak RSS / private | 503,615,488 / 1,241,243,648 bytes |
| Four overlapping requests | One 200, three busy 503 responses |
| Torch installed files | 531,556,961 bytes |
| Transformers / safetensors installed files | 107,440,502 / 911,391 bytes |
| NumPy / SymPy / NetworkX installed files | 54,161,255 / 69,598,071 / 15,641,933 bytes |

These installed file counts include distribution-listed files, not all dependencies
or a Linux Docker image size. Process-tree private memory includes both interpreters.
Measurements and logs: `artifacts/checks/public-gate-20261027/measurement-retry/`.
The ordinary model remains unsuitable for chat regardless of its fast generation.

## Prepared backend and publication boundary

The start command in `deploy/huggingface/Dockerfile` is:

```text
python -m toruk_lm.inference_server --backbone-dir /app/backbone --selector-checkpoint /app/selector.pt --host 0.0.0.0 --port 7860
```

`GET /healthz` and `/api/status` report readiness, exact pinned backbone revision/hash,
selector hash, supported modes, model identity and experimental limitations. They expose
no messages or secrets. Readiness is not a quality qualification. `POST /api/infer`
requires `Authorization: Bearer <TORUK_BACKEND_TOKEN>`; empty server tokens refuse startup.
The browser sends requests only to the Vercel proxy.

Limits: 16,384 body bytes; 20 messages; 1,024 UTF-8 bytes/message; 8,192 history bytes;
64 output tokens; pretrained selected prompt at most 512 tokens; one generation at a
time with immediate busy 503; at most eight HTTP handler connections, excess closed;
10-second socket inactivity timeout; 120-second worker startup deadline; 45-second
generation deadline. Expired generation terminates the worker and fails closed;
restart the service before further generation. Socket inactivity is not a complete
wall-clock slow-client deadline. Use the host edge protection as well. Worker parent
death triggers worker exit. Proxy deadline is 60 seconds and Vercel functions allow 70.
Logs contain fixed events/numeric telemetry, not body text, tokens, query paths or traces.

`scripts/prepare_inference_package.py` copies exactly these files into a **new** folder:

- `README.md`, `Dockerfile`, `requirements.txt`, `.dockerignore` from `deploy/huggingface`.
- `scripts/download_chat_backbone.py` as `download_chat_backbone.py`.
- The original selector as `selector.pt`, only if SHA-256 equals
  `479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`.
- `src/toruk_lm/{__init__,chat_runtime,chat_foundation,inference_server,inference_worker,controlled,engine,data,model,recurrent,effect_predictor,worlds,tokenizer}.py`.
- Generated `publication-manifest.json` listing every copied path, size and SHA-256.

Those imported modules include some training routines because the existing checkpoint
loader depends on them; no training command runs. No datasets, transcripts, reports,
remote configuration, Git directory, environment files, credentials or other checkpoints
are copied. Backbone weights are downloaded at their fixed revision inside the image
build and checked, rather than uploaded from the research folder. No HF token is needed
for that public model. Do not add secrets as Docker build arguments or public variables.

Packaging was attempted and correctly blocked on the missing original selector.
The final package and Docker image therefore have **not** been built or tested.
Docker and Vercel CLIs and linked Vercel settings are absent here.

## PowerShell preparation and account steps

The following preparation commands are local. First restore the exact original M6
selector from your own trusted archive to the path shown; do not retrain a replacement.

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[chat,dev]'
.\.venv\Scripts\python.exe -m pip install psutil
Get-FileHash .\artifacts\m6-validation-001\recurrent\checkpoint.pt -Algorithm SHA256
.\.venv\Scripts\python.exe scripts/prepare_inference_package.py --selector artifacts/m6-validation-001/recurrent/checkpoint.pt --output .readiness/hf-inference
Get-Content .\.readiness\hf-inference\publication-manifest.json
# Requires Docker Desktop; builds locally, including pinned model download:
docker build -t toruk-inference-review .\.readiness\hf-inference
$env:TORUK_BACKEND_TOKEN = '<LONG_RANDOM_SHARED_SECRET>'
docker run --rm -p 7860:7860 --env TORUK_BACKEND_TOKEN toruk-inference-review
```

To requalify the intended model locally without Docker, download into a fresh folder,
then run the existing two-mode integration. These commands download but do not upload:

```powershell
.\.venv\Scripts\python.exe scripts/download_chat_backbone.py --output artifacts/chat-foundation-001/backbone
.\.venv\Scripts\python.exe scripts/measure_inference_host.py --backbone-dir artifacts/chat-foundation-001/backbone --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --output-dir .readiness/chat-host-measurement
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py
```

The legacy foundation smoke writes its named integration logs in the research directory;
archive those files first if preserving that run is necessary. The new measurement command
requires a fresh output directory. Local test URLs remain local.

After **separate explicit upload/deployment authorization**, perform these account steps:

1. Sign into Hugging Face, confirm PRO/eligible compute access and current terms.
   Create a Docker Space with CPU Basic and **protected** visibility. If only a private
   Space is acceptable, keep Vercel blocked until separate platform authentication is designed.
2. Review the entire publication manifest and selector disclosure. Upload only the
   reviewed `.readiness/hf-inference` contents via **Files → Add file → Upload files**.
   This uploads source/checkpoint to HF and triggers deployment; do not do it before authorization.
3. Under Space **Settings → Variables and secrets → New secret**, set
   `TORUK_BACKEND_TOKEN=<LONG_RANDOM_SHARED_SECRET>`. Restart and inspect the build/runtime
   logs. No environment variables belong in the public README. Record the exact HTTPS
   `https://<SPACE_SUBDOMAIN>.hf.space` origin supplied by HF; a placeholder is not a tested URL.
4. Run the authenticated health/generation checks below, recording model identity,
   startup, bounded latency, concurrent rejection, and memory in HF metrics. A failed or
   sleeping Space is not ready. Do not claim Docker compatibility from local Python success.
5. Vercel dashboard: create/import the project, Root Directory **`web/vercel`**, Framework
   **Other**, no build command, Output Directory **`public`**. Verify Fluid Compute/runtime
   settings support the 70-second function configuration. Enable protection for qualification
   previews; inspect the account's available protection options before sharing a link.
6. In Vercel **Settings → Environment Variables**, set server-only
   `TORUK_BACKEND_URL=https://<SPACE_SUBDOMAIN>.hf.space` and
   `TORUK_BACKEND_TOKEN=<SAME_SHARED_SECRET>` for the intended Preview/Production environment.
   No `NEXT_PUBLIC_` or `VITE_` variables. Leave Production unlaunched while quality is blocked.
7. Once authorized, use the dashboard deployment flow. Inspect the authentic build and
   function logs, test `/api/status`, both modes and backend outage on the resulting preview.
   Configure a Vercel firewall rate rule and monitor usage before any public launch.
   The page already labels BASELINE/TORUK, named backbone, 6/20 quality, 14.96% selected-token
   reduction, and unverified efficiency. Weights and secrets are outside `web/vercel/public`.

Public-origin verification, **only after an authorized deployment exists**:

```powershell
$env:TORUK_BACKEND_URL = 'https://<SPACE_SUBDOMAIN>.hf.space'
$env:TORUK_BACKEND_TOKEN = '<LONG_RANDOM_SHARED_SECRET>'
$headers = @{ Authorization = "Bearer $env:TORUK_BACKEND_TOKEN" }
$status = Invoke-RestMethod "$env:TORUK_BACKEND_URL/api/status" -Headers $headers -TimeoutSec 60
if (-not $status.ready -or $status.backbone_revision -ne '12fd25f77366fa6b3b4b768ec3050bf629380bac' -or $status.backbone_sha256 -ne '5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c' -or $status.selector_sha256 -ne '479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d') { throw 'Wrong or unavailable deployed model' }
$body = @{ messages = @(@{role='user';content='Reply with HELLO'}); mode='TORUK'; max_new_tokens=8; temperature=0; top_p=1 } | ConvertTo-Json -Depth 5
$reply = Invoke-RestMethod "$env:TORUK_BACKEND_URL/api/infer" -Method Post -Headers $headers -ContentType 'application/json' -Body $body -TimeoutSec 60
if ($reply.metrics.model -ne $status.model -or $reply.metrics.mode -ne 'TORUK' -or $reply.metrics.output_tokens -gt 8) { throw 'Generation identity/bounds mismatch' }
$reply
```

A one-turn TORUK request verifies mode handling; it does not exercise older-turn selection.
Also run the fixed multi-turn smoke against the deployed proxy before qualifying memory
integration. Check wrong-token rejection, busy requests and outage behavior. No such
public checks were performed in this task: no deployed origin or account authorization exists.

## Verification and decision

Final local qualification passed: **106 Python tests**, both mypy platforms, lint,
format, package/dependency/import/CLI checks, reproduction, validation, summary,
research execution smoke, wheel/sdist build, and both Git diff checks. The exact
documented command run was `.\.venv\Scripts\python.exe scripts/verify.py --prefix public-release --output-dir artifacts/checks/public-gate-release-20261027`;
it exited **0**, with `Failed checks: []`. This is the Python package gate, not a
Docker build or Vercel build. Node syntax checks and **8 Node tests** also passed.
Final local page/proxy/ordinary-model/outage smoke passed in **6.53 seconds**, recorded
in `artifacts/checks/public-gate-20261027/integration-final.json` and `.log`.
Static public files contain no backend URL/token configuration references or Bearer
header construction. The source allowlist totals 97,217 bytes and includes all internal
Python import dependencies; that check does not qualify a Docker image.

Initial failures were retained separately: missing optional Transformers dependencies,
a source identity mismatch while edits overlapped the first verification run, an
output-directory path error, a benchmark variable shadowing its imported module, and
deadline exceptions caught as generic OS errors. Dependencies were installed, code
errors corrected, and affected checks rerun. The final gate above passed. The packaging
refusal due to missing M6 weights remains an intentional blocker, not a bypassed check.

Run from repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_chat.py tests/test_chat_foundation.py tests/test_chat_release_eval.py tests/test_inference_server.py
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
.\.venv\Scripts\python.exe -m toruk_lm generate --checkpoint artifacts/foundation-001/train/checkpoint.pt --prompt 'Hello' --max-new-tokens 16
.\.venv\Scripts\python.exe scripts/smoke_vercel_local.py --checkpoint artifacts/foundation-001/train/checkpoint.pt --output-dir .readiness/ordinary-smoke
.\.venv\Scripts\python.exe scripts/verify.py --prefix public-gate --output-dir .readiness/verification
git diff --check
```

GitHub connector checks for exact HEAD `636bd4e196729a9ee48bf2f5315cb8f85abaf61a`
returned no associated PR-triggered workflow runs and no commit statuses. The connector's
workflow lookup covers PR-triggered runs only; push/manual Actions results were not established.
No remote CI success is claimed for this commit or the uncommitted changes.

Remaining account/manual blockers: restore evaluated weights; confirm checkpoint rights;
obtain HF compute eligibility; authorize the exact upload manifest and deployments;
install Docker/build the Linux package; configure HF secret and verify the public HTTPS
backend; link Vercel/settings/secrets, authentic build, protected preview runtime check;
improve chat quality and rerun a preregistered evaluation before public chatbot launch.

- INFERENCE BACKEND: **BLOCKED**
- VERCEL FRONTEND: **BLOCKED** (source prepared; production backend and authentic build missing)
- PUBLIC CHAT: **NOT VERIFIED**
- TORUK EFFICIENCY CLAIM: **UNSUPPORTED**
