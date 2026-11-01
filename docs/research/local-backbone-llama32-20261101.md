# Local Llama 3.2 backbone experiment — 2026-11-01

This is a **new exploratory experiment**, separate from the frozen SmolLM2
[release result](chat-release-v2-results.md). Language quality here comes from
the external pretrained backbone. The Toruk M6 checkpoint only chooses which
verbatim earlier turns reach that backbone. Neither component was trained in
this experiment.

## Device and model

Windows reported 16,831,897,600 bytes physical RAM (15.68 GiB), with
1,245,499,392 bytes available in the initial check. `nvidia-smi` reported an
NVIDIA GeForce RTX 3050 Laptop GPU with 4,096 MiB VRAM, initially unused.
WMI queries were denied, so RAM came from `GlobalMemoryStatusEx`; GPU figures
came from `nvidia-smi` and Ollama `/api/ps`.

The selected local model is `llama3.2:latest`, the 3.2B parameter Q4_K_M
instruct build. The full installed Ollama manifest digest is
`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`;
the source is the [Ollama Llama 3.2 Q4_K_M listing](https://ollama.com/library/llama3.2/tags),
derived from [Meta Llama 3.2 3B Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct).
Its license is the **Llama 3.2 Community License**, not Apache-2.0. The
installed on-disk download is 2,019,393,189 bytes (about 2.02 GB). It was
already present; **new download: 0 bytes, paid API cost: zero**. A fresh local
installation would transfer about 2.0 GB. The loaded Ollama runner reported
2,935,656,282 bytes total size, including 2,347,688,263 bytes in VRAM at
`num_ctx=4096`; `nvidia-smi` showed about 2,350 MiB used and 1,613 MiB free.
Allow about 2.5 GiB GPU memory plus driver headroom and host RAM. This fit
on the measured device, although only about 1.0–1.5 GiB system RAM was free
during the runs. Cold loading and other applications can cause paging.

The existing SmolLM2 download constants and its 269 MB SHA-256 check remain
available. The existing recurrent selector checkpoint is
`artifacts/m6-validation-001/recurrent/checkpoint.pt`, SHA-256
`479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`.
It loads through the separate byte-tokenized turn selector; its weights are
**not** inserted into Llama hidden states. When absent, TORUK mode is
unavailable. Both available modes used this one Ollama digest, its tokenizer
and chat template, greedy temperature 0, top-p 1, 512 selected prompt tokens,
and 32 output tokens for the paired fixture.

## Exact refusal-history replay

The [raw replay](../../artifacts/chat-backbone-llama32-20261101/refusal-rerun.json)
contains every supplied turn, answer, count, selected ID, and request latency.
It replays `hello`, `what are you?`, `i am JinSakai`, `open youtube`, `what is 5`,
and `what is 5+5`, including the earlier assistant refusal and the repeated
online-content refusal. No turn was removed before selection. On the **matched
history**, BASELINE retained all 11 turns (205 prompt tokens) and answered
`5 + 5 = 10` in 803 ms; TORUK selected IDs `m0,m2,m8,m9,m10` (78 tokens)
and gave the same answer in 988 ms. A fresh one-turn `what is 5+5` also
answered `5 + 5 = 10` in both modes (31 prompt tokens). Generated-history
replays answered the first two arithmetic turns appropriately in both modes.
Fresh one-turn probes also returned `HELLO`, `7`, Rome, and 100 degrees Celsius;
the page smoke recalled `Mira` after a new two-turn chat. Their exact replies
and counts are in the paired and end-to-end artifacts below.
One repeated BASELINE question produced a garbled “Déjà vu” opening; this
is a separate quality flaw. SmolLM2 repeated the irrelevant refusal in both
modes in the original matched probe; that behavior was **not fixed by Toruk**.

## Paired quality and context selection

The [raw paired rerun](../../artifacts/chat-backbone-llama32-20261101/paired-v2-exploratory-rerun.json)
embeds the actual prompts, replies, strict scores, token counts, selected
message IDs, request latency, and before/after RAM and GPU measurements.
It reused the unchanged [20-case v2 fixture](../../configs/chat-release-eval-v2.json)
for exploratory comparison. This is not a new preregistered held-out result.

| Mode | Strict score | Selected prompt tokens | Output tokens | Aggregate request time | Errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| BASELINE | 17/20 | 1,682 | 266 | 18.84 s | 0 |
| TORUK | 17/20 | 1,399 | 265 | 25.12 s | 0 |

TORUK selected **16.8% fewer prompt tokens** but took longer overall. The
selector still reads earlier content, and Ollama metering runs add overhead.
The original frozen SmolLM2 result was **6/20 in each mode**, with 14.96%
fewer selected tokens in TORUK. The higher Llama 3.2 answers show a backbone
quality improvement on this reused fixture, not a Toruk memory gain or a
controlled model-only quality claim. The original 35% selected-token goal
remains unmet; there is no efficiency result.

Both Llama modes answered the two corrections (Thursday and floor five),
both long-range facts (CEDAR-19 and violet), and both irrelevant-history
questions (7 and Mercury). For `long_key`, BASELINE used 218 tokens and
TORUK 103; for `long_color`, 204 versus 93. Both modes answered the unknown
PIN cautiously. The unchanged lexical scorer marked `unknown_maiden`,
`ambiguous_season`, and `ambiguous_pronoun` wrong in both modes, although the
verbatim replies include “haven't provided,” “can't determine,” and “don't
have enough information.” These are useful uncertainty answers but do not
match the fixture's accepted phrases exactly; the frozen scorer was not
rewritten after seeing them. The 32-token cap also visibly cuts off some
answers. A separate [first pass](../../artifacts/chat-backbone-llama32-20261101/paired-v2-exploratory.json)
had one BASELINE Ollama error on `user_fact_pet`; its incomplete token totals
were not used in the table. The repeat kept the same prompts and settings and
had no errors. No reliability claim follows from two local passes.

## Commands, checks, and cost

Run from the repository root in Windows PowerShell, with local Ollama running:

```powershell
$digest = 'a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72'
.\.venv\Scripts\python.exe scripts/probe_ollama_backbone.py --model llama3.2:latest --digest $digest --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --output artifacts/chat-backbone-llama32-20261101/refusal-my-run.json
.\.venv\Scripts\python.exe scripts/evaluate_local_backbone.py --model llama3.2:latest --digest $digest --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --output artifacts/chat-backbone-llama32-20261101/paired-my-run.json
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --ollama-model llama3.2:latest --ollama-digest $digest --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --chat-probes --output-dir artifacts/chat-backbone-llama32-20261101/proxy-my-run
```

Each evidence script requires a fresh output path to avoid overwriting the
retained artifacts. The paired rerun took 55.45 s wall time for 40 answers
plus metering calls. GPU electricity was not metered. There was no API bill.
The exact PowerShell server and page startup commands are in
[the chat foundation guide](../chat-foundation.md).

Checks: focused Python tests **26 passed**; Node syntax check and **11 Node
tests passed**. Ruff lint and format checks passed for the changed Python
paths. The selected-backbone [end-to-end smoke](../../artifacts/chat-backbone-llama32-20261101/proxy-current/results.json)
passed the page, both modes, fresh chats, full model identity, token metrics,
and outage 503. `compileall` and `git diff --check` passed. A current
[SmolLM2 end-to-end regression](../../artifacts/chat-backbone-llama32-20261101/smollm-current-retry/results.json)
also passed both modes and outage handling. Its first attempt failed during
Windows multiprocessing handle duplication (`WinError 5`), then the isolated
retry passed. Mypy could not start from this sandbox: the venv launcher
reported access denied to its base Python 3.14 executable. The archived
release result and weights were not changed.

Remaining research work is to train and validate a chat-relevance selector
on separate data, evaluate unseen histories with independent seeds and a
quality floor, and account for full selector and metering cost. A future
genuinely Toruk-trained conversational LM requires the separate training
program described in [architecture](../architecture.md#future-a-genuinely-toruk-trained-conversational-lm).
