# Trained Toruk chat selector v1 — local result

Protocol: [chat selector v1](chat-selector-v1-protocol.md). Frozen identity and
source hashes: [`freeze.json`](../../artifacts/chat-selector-v1-20261101/freeze.json).
Raw final prompts, replies, selected IDs, token counts, timing, errors, and
memory measurements: [`final-paired.json`](../../artifacts/chat-selector-v1-20261101/final-paired.json).

## What was trained

The historical M6 checkpoint is a four-slot recurrent byte-level model trained
for controlled-world QA, not chat relevance. Its source and SHA-256 are
unchanged. The new selector is a separate eight-feature logistic ranker over
earlier user turns. It optimizes class-weighted binary cross entropy on
evidence labels, then uses a development-selected threshold to keep at most
two older turns plus the last three messages. It reads every supplied message.
There is no persistent state across requests and no pretrained language
ability in this ranker. Llama 3.2 remains the answer generator.

Train/dev/final counts are 200/60/60 cases, with distinct synthetic entities,
city pools, and seeds 1701/2301/4701. The corrected Windows newline writer
produced the frozen split hashes in the data manifest; an earlier generated
directory failed its hash check before training and was never evaluated.
Training used seed 73, 120 Adam steps at 0.03, positive class weight 5, and
1,600 labeled train turns. The final train loss was 0.209049; development
evidence F1 was 0.8 at threshold 0.8. Optimizer loop: 0.171 s on CPU. The
1,172-byte checkpoint is `artifacts/chat-selector-v1-20261101/selector.json`, SHA-256
`09b804ee11a93e22426870c2c29481f209c8b8b99862ed74e0c6286a5861ad92`.
This is a tiny learned lexical component, not a semantic conversational LM.
The learned weights favor question-word overlap (2.19), shared terms (1.93),
and a subject match (1.51); the correction-marker weight is 1.05 and relative
position is -1.89. That negative position weight favors older turns in this
dataset and may hurt other histories. Full weights are in the checkpoint.

## Held-out paired comparison

The same installed Ollama `llama3.2:latest` digest
`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
uses greedy temperature 0, top-p 1, a 512-token prompt cap, and 32 output
tokens in both modes. Only turn selection differs. The sealed final split was
opened only after the model, threshold, data hashes, and scorer were frozen.

The single sealed final run took **556.85 s wall time** for 120 answers and
metering calls. It had no API errors. All raw prompts and replies remain in
the linked JSON. The strict answer scorer was fixed in the frozen evaluator.

| Measure | BASELINE recent turns | TORUK trained selector |
| --- | ---: | ---: |
| Correct answers | 12/60 | 60/60 |
| Known evidence retained | 0/48 | 48/48 |
| Unknown cases with unnecessary older turns | 12/12 | 0/12 |
| Unsupported unknown answers | 0 | 0 |
| Selected prompt tokens | 25,176 | 12,071 |
| Output tokens | 1,632 | 675 |
| Total Ollama prompt-evaluation tokens, including metering | 390,816 | 85,204 |
| Additional selector history scan | 0 | 251,326 UTF-8 bytes |
| Selector time | 0 | 111.6 ms |
| Aggregate response time | 444.40 s | 73.69 s |
| Errors | 0 | 0 |

The selected-prompt reduction is **52.05%**. TORUK gained **80 percentage
points** of strict answer quality on these generated histories. Category
scores were 0/12 versus 12/12 for each of correction, preservation,
distraction, and long-range recall; both modes were 12/12 for unknowns.
One correction example: BASELINE kept `m12`–`m18` and said it had no
information about `Finalperson000`; TORUK kept `m0,m8,m16,m17,m18` and
answered that the corrected city was Nashik. One long-range example kept
`m0` and answered `FINALKEY000`; BASELINE had dropped `m0` and could not
answer. The unknown example answered “I don't know” in both modes; TORUK
selected only the recent three messages.

This **meets the frozen synthetic answer-quality improvement rule**, including
full labeled evidence retention and no added unsupported unknown answers.
It **does not meet the token-efficiency-at-preserved-quality rule**: BASELINE
quality was only 20%, below the protocol's 60% floor. The measured token and
latency reductions are properties of this local implementation and fixture.
BASELINE's repeated Ollama generation calls to meter and trim a long prompt
account for much of its 390,816 prompt-evaluation tokens and latency; this
is a confounder for attributing speed to the ranker. TORUK still read the
entire supplied history to score it. Free system RAM fell from 0.470 to
0.266 GiB during the run; GPU memory used rose from 2,346 to 2,364 MiB.
Paging and other host load limit timing comparisons.

## Transfer failure and limits

The [local page smoke](../../artifacts/chat-selector-v1-20261101/page-smoke/results.json)
loaded the exact v1 checkpoint, exposed its full SHA-256 and
`toruk-chat-selector-v1` identity, ran both modes through the page proxy,
and returned a visible 503 when the backend was stopped. It also exposed a
real regression outside training vocabulary: on the older **vault code**
probe, BASELINE answered `LIME42`, while TORUK selected only `m10,m11,m12`
and falsely said no code had been given. The ranker was trained on
**archive key** wording; lexical overlap did not transfer to this paraphrase.
This failure is retained. No threshold or weights were changed after the
final run or page smoke.

The final split has different entities, values, and seeds, but the same
generator family and question wording as train/dev. It was constructed so
the useful fact is early and ordinary recent-turn context drops it. This
demonstrates a narrow supervised selection behavior, not semantic retrieval,
robust memory, or a general chatbot quality improvement. The next research
change is to train on paraphrase and varied dialogue sources, compare against
a simple lexical retrieval baseline as well as recent turns, and freeze a
new held-out evaluation with a stronger baseline quality floor. Do not
reuse these final cases for tuning.

## Reproduction and checks

From the repository root, with the model available in local Ollama:

```powershell
$digest = 'a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72'
.\.venv\Scripts\python.exe scripts/build_chat_selector_data.py --output-dir artifacts/chat-selector-v1-20261101/data-reproduction
.\.venv\Scripts\python.exe scripts/train_chat_selector.py --data-dir artifacts/chat-selector-v1-20261101/data-reproduction --output artifacts/chat-selector-v1-20261101/selector-reproduction.json
.\.venv\Scripts\python.exe scripts/evaluate_trained_chat_selector.py --data-dir artifacts/chat-selector-v1-20261101/data-reproduction --selector-checkpoint artifacts/chat-selector-v1-20261101/selector-reproduction.json --model llama3.2:latest --digest $digest --output artifacts/chat-selector-v1-20261101/final-reproduction.json
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --ollama-model llama3.2:latest --ollama-digest $digest --selector-checkpoint artifacts/chat-selector-v1-20261101/selector.json --output-dir artifacts/chat-selector-v1-20261101/page-smoke-reproduction
```

Use fresh output paths for another reproduction. Windows PowerShell server
and page startup are also documented in [chat foundation](../chat-foundation.md).
To chat through the existing page, use these PowerShell commands in separate
windows after verifying that local Ollama holds the digest above:

```powershell
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-secret'
.\.venv\Scripts\python.exe -m toruk_lm.inference_server --ollama-model llama3.2:latest --ollama-digest a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72 --selector-checkpoint artifacts/chat-selector-v1-20261101/selector.json --host 127.0.0.1 --port 8766
```

```powershell
$env:TORUK_BACKEND_TOKEN = 'choose-a-long-random-secret'
$env:TORUK_BACKEND_URL = 'http://127.0.0.1:8766'
$env:PORT = '3000'
node .\web\vercel\scripts\dev.mjs
```

Open `http://127.0.0.1:3000` and select TORUK. Status and reply metrics show
the v1 selector kind and SHA-256. The page remains a local research tool.
The original M6 checkpoint and all frozen prior chat evaluations remain
separate. The [legacy M6 regression smoke](../../artifacts/chat-selector-v1-20261101/m6-regression/results.json)
passed with the same Ollama backbone and still answered `LIME42` in TORUK
mode. It identifies itself as `toruk-m6-controlled-qa` rather than v1.

| Check command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_chat_selector.py tests/test_ollama_chat.py tests/test_chat_foundation.py tests/test_inference_server.py tests/test_chat_release_eval.py tests/test_chat.py` | 31 passed |
| `npm.cmd --prefix web/vercel run check` | Passed |
| `npm.cmd --prefix web/vercel test` | 11 passed |
| `.\.venv\Scripts\python.exe -m ruff check` on the 11 changed Python source/script/test paths | Passed |
| `.\.venv\Scripts\python.exe -m ruff format --check` on the same paths | Passed |
| `.\.venv\Scripts\python.exe -m compileall -q src/toruk_lm scripts/build_chat_selector_data.py scripts/train_chat_selector.py scripts/evaluate_trained_chat_selector.py scripts/smoke_chat_foundation.py` | Passed |
| `.\.venv\Scripts\python.exe -m mypy --python-version 3.14 src/toruk_lm` | Could not start: sandbox denied access to the venv base Python 3.14 executable |
| `git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check` | Passed for tracked files |

Git HEAD is `66028db306a0176edfb48a163cba2f0b3106432a` on `main`.
The working tree is dirty with pre-existing chat/backbone edits plus these
selector changes; the new protocol, scripts, tests, checkpoint, split data,
and raw results are untracked. The private architecture note is ignored by
Git. No commit, reset, deployment, or changes to the M6 checkpoint or frozen
evaluation artifacts were made.
