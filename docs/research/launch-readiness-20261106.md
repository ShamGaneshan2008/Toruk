# Local chatbot and public launch gate — 6 November 2026

Starting HEAD: `a450a0d6c4f293fb9b500968c35a5c051787d0a6`. Starting worktree:
`M .gitignore`, `D .idea/.gitignore` from the prior cleanup. This audit did not
commit, push, deploy, purchase hosting, or change frozen evaluation outputs.

## Decision and gates

**Local offer:** an explicitly experimental, loopback-only chat page with a
pretrained instruct backbone. BASELINE (recent context) is the default. TORUK
is an optional context selector, not a Toruk-trained answer generator. Toruk's
ordinary and owned checkpoints are research continuations, not chat defaults.

For a future public chatbot decision, set these minimum gates before a new
evaluation: at least 80% correct overall and 70% in each represented category;
all exact-string, correction, and unsupported/unknown probes correct; zero
refusal-carryover errors; zero unhandled request failures or model-identity
mismatches; and a completed same-backbone local load/outage/concurrency smoke.
A TORUK benefit claim additionally needs no quality regression, measured lower
**total** request cost and latency, and a paired uncertainty interval excluding
zero on independently authored held-out cases. These are prospective launch
thresholds, not retroactive scores or claims of statistical power.

The [frozen 20-case chat release](chat-release-v2-results.md) fails: BASELINE
6/20 and TORUK 6/20. Both get factual 2/2, but reference 0/2, user fact 0/2,
preservation 0/2, unknown 0/2, and irrelevant-history 0/2. Both give three
unsupported answers. The TORUK selector cuts selected prompt tokens from 1,818
to 1,546 (14.96%), while output tokens rise 254→278 and aggregate response
time rises 15,259.708→15,552.248 ms. Full input tokens are 1,818 in both modes;
selector scanning has a cost. [Raw answers and metrics](../../artifacts/chat-release-v2/raw.json)
show the per-case selected IDs, replies, tokens, latency, and failures. A
successful HTTP reply does not mean a correct answer.

The [owned conversation pilot](conversation-format-v1-results.md) is separate:
framing improves to 20/24, answer accuracy stays 0/24, exact strings fail 0/3,
and the full recorded refusal history exceeds its 512-byte prefix interface.
The prior [readiness comparison](conversation-readiness-v1-results.md) records
the pretrained Qwen reference answering short and full refusal-to-math probes,
while the owned model fails or returns an interface error. Its raw replies and
post-hoc semantic review are retained there. The [independent selector study](independent-replication-v1-results.md)
finds 9/24 Toruk answers versus 6/24 lexical answers on independent cards, but
higher token work and latency and an uncertainty interval including zero. It
records exact-string and stale-correction failures, selector overhead, CPU time,
and raw answers. These distinct model/dataset results must not be pooled.

No new quality inference was run in this audit: the Python interpreter in `.venv`
points to an inaccessible Python 3.14 installation, and `py -0p` finds no usable
installed Python. The pinned Qwen weight is also absent. Thus the above is
recorded evidence, not a fresh reproduction on this worktree.

## Request path and identities

`web/vercel/public/index.html` keeps the transcript in page memory and sends
`POST /api/chat` to `web/vercel/api/chat.js` → `lib/proxy.js`. The Node proxy
validates roles, nonempty text, body and token bounds, and mode; it adds the
server-side Bearer token and calls Python `POST /api/infer`. The Python
`inference_server.py` authenticates, validates again, reserves one generation
slot, and asks a killable `inference_worker.py` process to run
`chat_foundation.py` or the ordinary smoke backend. Metrics and answer return
through the proxy; the browser never receives the backend token. `GET /api/status`
passes model/backbone/selector identity and readiness to the page; backend
`/healthz` is 503 when unready. The browser now calls generated replies
“Assistant,” with the actual backbone shown in the header.

| Mode/source | Generator | Context behavior | Status |
| --- | --- | --- | --- |
| BASELINE with available local files | `HuggingFaceTB/SmolLM2-135M-Instruct@12fd25f77366` | Recent turns, 512-token prompt fit | Default, quality gate failed |
| TORUK with M6 selector | Same pretrained SmolLM2 | Historical `toruk-m6-controlled-qa` selector chooses turns | Experimental, quality gate failed |
| Qwen local option | `Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf` | Recent or separately configured selector | Weight absent in this checkout |
| `--checkpoint` | `toruk-ordinary-v1` byte LM | Plain continuation | Smoke only; ordinary checkpoint absent here |
| Owned LM CLI | `toruk-owned-next-token-v1` | Recurrent state and byte continuation | Not exposed in browser/API; chat gate failed |

The present SmolLM weight is 269,060,552 bytes, SHA-256
`5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`.
The present M6 selector is 750,487 bytes, SHA-256
`479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`.
Both match recorded manifests. Presence and hash verification do not prove they
load on this sandbox.

Code limits: 16,384 request-body bytes, 20 messages, 1,024 UTF-8 bytes per
message, 8,192 total history bytes, 1–64 generated tokens, 512 selected prompt
tokens, 10-second backend socket inactivity, 45-second model generation deadline,
60-second proxy deadline, one active generation, and eight connection handlers.
The proxy rejects invalid requests before inference, masks backend private error
text, reports outage/timeout, and rejects malformed/empty or inconsistent model
responses. The UI disables Send when unready and offers Retry connection.
Node tests cover these contracts; a real model smoke still remains.

## Hosting measurements and boundary

The [prior local Windows ordinary-checkpoint measurement](../../artifacts/checks/public-gate-20261027/measurement-retry/metrics.json)
measured 573,431 checkpoint bytes, 5.860 s startup, 83.6/73.3 ms first/second
64-token request, 503,615,488 peak process-tree RSS bytes, 1,241,243,648 peak
private bytes, and four overlapping requests yielding one 200 plus three busy
503s. Its installed Torch distribution files alone totaled 531,556,961 bytes;
Transformers 107,440,502 bytes; NumPy 54,161,255; SymPy 69,598,071; NetworkX
15,641,933; safetensors 911,391. These are installed file totals, not a Linux
image size. They describe the ordinary smoke model, **not** present-day SmolLM
startup, memory, throughput or concurrency. The current SmolLM package/image,
startup, peak memory and response/concurrent behavior remain unmeasured here.

The static page and small Node proxy fit the intended Vercel role. The Python
model belongs on a separately measured, access-controlled inference host. The
current [Vercel function limits](https://vercel.com/docs/functions/limitations)
include a 250 MB uncompressed Node bundle and 500 MB Python bundle; Hobby memory
is 2 GB, and current Fluid Compute duration defaults to 300 seconds. The
repository's `maxDuration: 70` is below that current Fluid limit but must be
checked in an authentic project build. The installed Torch files alone exceed
the Python bundle limit, before model weights and dependencies, so this package
cannot simply be placed in a Vercel Python function. This is a size inference,
not a tested Vercel build.

[Hugging Face Spaces hardware documentation](https://huggingface.co/docs/hub/spaces-overview)
lists CPU Basic at 2 vCPU/16 GB with no hourly hardware charge, but creating a
compute (Docker/Gradio) Space requires a paid plan; free hardware sleeps when
idle. CPU Upgrade is listed at $0.03/hour. Even a free frontend does not fund
inference, storage, network usage, or plan eligibility. If this candidate ever
passes quality, build the isolated Docker package locally, measure the exact
SmolLM+selector image/startup/RSS/parallel requests, then use a protected
preview and account usage limits before considering public access. No deployment
or hosting purchase occurred. Existing [deployment documentation](../public-inference-gate.md)
contains older measured figures and account steps; this audit supersedes its
checkpoint-absence and general hosting-limit assumptions for this checkout.

## Verification and blockers

Local Node syntax check passed; 18 Node tests passed, one live-proxy test skipped
without a running backend. Python tests, CLI checks, integration smoke, Ruff,
format, mypy, and `scripts/verify.py` could not execute because no accessible
Python interpreter was available. A genuine Vercel build and hosted runtime
were not run. `.github/workflows/ci.yml` includes Node syntax/tests, Python
package checks, full pytest, Ruff, format, native/Linux mypy, bounded research
smokes and a package build; it does not run a hosted model quality evaluation
or deployment smoke. No hosted CI result was inspected for this dirty tree.

**Public deployment: blocked.** The frozen chat quality result is far below the
predeclared launch gate, current model performance and host resources need a
fresh runnable environment, and no authentic Docker/Vercel preview has passed.
The one recommended next action is to restore an accessible Python environment
and run the existing local SmolLM+M6 end-to-end smoke and measurement commands
against the verified files before any new model or deployment work.
