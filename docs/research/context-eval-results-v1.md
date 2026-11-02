# Same-backbone context selection: measured pilot

**The literal numeric target passed on this fixture: 43.03% fewer backbone input
tokens and the same 10/12 content score. Grounded answer-quality preservation did
not pass the support audit.** Both TORUK selectors answered two multi-hop questions
without retaining their required ownership links. This is a small synthetic pilot,
not evidence of general superiority, useful learned memory, or publication readiness.

The [protocol](context-eval-protocol-v1.md) and
[Windows commands](../context-selection.md) distinguish the experiment from the
absent M6 learned selector. All artifacts are local under
`artifacts/context-milestone-20261031/`. No private user conversation was evaluated.

## Three separate findings

1. **Pipeline:** the real inference worker and Node proxy ran successfully. Failed
   readiness handling remains tested. An actual page-handler test enabled typing
   and Send and submitted generated follow-up history through the real proxy.
   Interactive browser validation remains unavailable: discovery returned `[]`.
   A DOM stand-in is not a real visual/browser session.
2. **Chat usefulness:** the backbone answered a simple fact and recalled a name,
   but failed the live correction question and truncated an uncertainty reply.
   Locally operational chat is not a reliably useful assistant.
3. **Research measurement:** matching content scores used fewer backbone prompt
   tokens, but selected evidence was incomplete and grounding weakened. The model
   supplied language ability; the new selector is a heuristic, not trained memory.

## Actual local chat replies

These were generated through `http://127.0.0.1:3000/api/chat`, temperature 0,
top-p 1, max 32 output tokens. `phase1.json` retains every setup turn and metric.

- Basic: `What is the capital of France?` → `The capital of France is Paris.`
- Follow-up: after `My name is Mira.` and the generated `Mira is a person with your given name.`,
  `What is my name?` → `Your name is Mira.`
- Correction: after `The meeting is on Monday.` and the generated `The meeting is scheduled for Monday.`,
  `Correction: the meeting is on Friday. Which day is it now?` →
  `The current date is Tuesday.` **Wrong, unsupported response.**
- Unknown: `What is my childhood teacher's name? I have not provided it.` →
  `I'm sorry, but I don't have enough context to provide your childhood teacher's name accurately. Without knowing their full name or any additional details about them,`
  **Uncertainty expressed, output truncated at the configured cap.**

These outputs were preserved, not repaired or replaced by invented examples.
The original readiness repair was inspected first, and installed files/dependencies
were verified before inference. The old `abc` fixture was never used for chat.

## Exact matched configuration and provenance

- Backbone: `Qwen/Qwen2.5-0.5B-Instruct`, Apache-2.0, revision
  `7ae557604adf67be50417f59c2c2f167def9a775`.
- Weights SHA-256:
  `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
  Existing 988,097,824-byte weight file; no download or backbone fine-tuning.
- Tokenizer: pinned `Qwen2Tokenizer` configuration and chat template;
  `tokenizer.json` SHA-256
  `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`.
- CPU float32, two Torch threads, 512-token actual prompt cap including the same
  server conversation instructions in both modes; 32 generated tokens maximum.
  Greedy decoding (`do_sample=false`, temperature 0, top-p 1), use-cache enabled.
  Pinned generation config retains repetition penalty 1.1; its sampling defaults
  are overridden by the explicit greedy request. Full config contents/hashes are
  retained in every raw artifact.
- Torch `2.14.1+cpu`, Transformers `5.20.2`, Safetensors `0.8.0`; no extra model.
- Git HEAD: `66028db306a0176edfb48a163cba2f0b3106432a`, `main`, dirty initially.
  Measured Python/config source fingerprint:
  `69eae778a3a2eb11baab142281c4c393a6bb9d13132e8b7e82960bf3d307d998`.
  Final v1 and v2 runs have the same source fingerprint and dataset hash. Hash maps
  preserve individual source identities; `web-freeze.json` records the web sources.
- Final fixture SHA-256:
  `ff84f244aa623997e69e89228ef328be20d8382371645d5eef6b28b05fc4a14c`.
  Development fixture SHA-256:
  `d1f692826829461798b557a82f9e021a166928bc2aa99c82ee71e18cb2c637d1`.
  Six disjoint development cases; 12 final cases, two per required category.
  Entities/values differ but templates/distractors are shared: held-out instances,
  not held-out linguistic templates. Histories contain 13–19 messages and fit the
  baseline's cap. “Long-range” means earlier in these short transcripts.

BASELINE is unchanged recent-turn fitting. TORUK v1 keeps the latest three messages
and two older user messages ranked by query-term overlap. TORUK v2 adds at most
two explicitly marked corrections immediately following selected facts. Neither
reads labels or required-evidence annotations, rewrites facts, changes weights,
or persists state across requests. The missing learned M6 weights were not replaced.

Selector source/identity hashes in backend status:

- v1: `4c3ddbb70c2e156820de590da98029924bab20483c50be77c02460cb0c47d1ed`.
- v2: `f46f9f96c9c9ca47ba659e9cce6fcaff86371e84b6f444342c1a214f33958741`.

## Final comparison

Accuracy is the frozen accepted/forbidden content rubric. Each latency is one warm
caller-measured HTTP request including selection, tokenization, inference and proxy
overhead, excluding server startup. These are single sequential runs on one laptop;
they do not establish a statistically reliable latency improvement.

| Path | Accuracy | Automatic unsupported/stale flags | Audited unsupported/stale or ungrounded | Selected input mean / median | HTTP latency mean / median |
| --- | ---: | ---: | ---: | ---: | ---: |
| BASELINE, final v2 pair | 10/12 (83.3%) | 2 | 2 | 299.58 / 294 | 2541.75 / 2445.12 ms |
| TORUK lexical-v1 | 10/12 (83.3%) | 2 | 4 | 168.83 / 168 | 1953.23 / 1822.46 ms |
| TORUK lexical-v2 | 10/12 (83.3%) | 2 | 4 | 170.67 / 168.5 | 1710.44 / 1627.51 ms |

The v1 pair's baseline latency was 2795.17 / 2654.39 ms. Its baseline answers and
input token counts exactly match the v2 pair. Both paths became faster between
runs; do not attribute the before/after latency difference to the correction rule.

| Resource/support total | BASELINE | TORUK v1 | TORUK v2 |
| --- | ---: | ---: | ---: |
| Available formatted history tokens | 3595 | 3595 | 3595 |
| Actual backbone input tokens | 3595 | 2026 | 2048 |
| Generated tokens including stop tokens | 41 | 44 | 44 |
| Selected-input reduction | — | 43.64% | 43.03% |
| All required evidence retained | 12/12 | 8/12 | 10/12 |
| Evidence-bearing cases with full evidence | 8/8 | 4/8 | 6/8 |
| Correct answer AND complete required evidence | 10/12 | 8/12 | 8/12 |
| HTTP/generation failures | 0 | 0 | 0 |

The heuristic and tokenizer still read the full available history. Token savings
refer to what the backbone receives, not total end-to-end tokens processed. The
four general-knowledge/unknown cases have empty evidence lists; their evidence
coverage is vacuous. This is why the evidence-bearing subset is reported too.

Automatic unsupported flags mean incorrect non-abstaining answers under a fixed
regex/content rubric. A separate support audit reviewed all short final answers
and adds correctly guessed answers with incomplete required evidence. It does
not change the frozen correctness scores. `comparison-and-support-audit.json`
retains the per-row classification and confirms no answer regressions.

## The single focused improvement and remaining failures

In development, v1 selected the old delivery day and a related label description,
but dropped the intervening `Correction: it is Friday.` because it lacked subject
words. V2 retains that dependent correction alongside its selected original fact.
This was chosen before inspecting final outputs. Final questions, scoring and
decoding were never changed. There was no second tuning iteration.

| Before/after | Development v1 → v2 | Final v1 → v2 |
| --- | --- | --- |
| Correct answers | 5/6 → 5/6 | 10/12 → 10/12 |
| Complete evidence | 4/6 → 5/6 | 8/12 → 10/12 |
| Backbone input total | 1012 → 1023 | 2026 → 2048 |
| Answer regressions | 0 | 0 |

**The improvement fixes retention, not answering.** Both final correction answers
remain stale: Wednesday instead of Saturday, and Sunday instead of Tuesday. The
backbone makes the same errors even with all the evidence in BASELINE. Every TORUK
answer is textually identical before and after; v2 spends 22 extra tokens to keep
the two corrections. Token saving regresses by 0.61 percentage points.

Both multi-hop answers are correct strings, Juniper/Cedar, but TORUK retains only
the two depot alternatives and recent noise, omitting the camera-owner and
owner-locker links. Neither version demonstrates supported multi-hop retrieval.
All three paths score 2/2 in recall, conflict, irrelevant-history, multi-hop and
unknown categories; corrections score 0/2. The nominal multi-hop score hides that
TORUK support failure, which is why no grounded-quality advantage is claimed.

Numeric verdict: **35% fewer actual backbone input tokens without lower content
accuracy was met on this set**, with no more automatic unsupported flags. Stronger
verdict: **preserving grounded answer quality was not established**; the support
audit is worse, and reliable conversational correction remains a model blocker.

## Verification, commands and CI coverage

Exact startup/evaluation commands are in [the developer guide](../context-selection.md).
Runs retained commands, output and source identity via `scripts/check.py`:

Final outcomes: **all 18 `verify.py` stages passed**, including **120 Python tests
in 173.60 seconds**, both source mypy platforms, lint/format, research reproduction,
validation/summary, package build and diff checks. Focused tests passed 28 cases.
Node syntax checks and 10 regular Node tests passed (the optional live test is
skipped in the normal invocation). The separate live invocation passed both tests,
including actual TORUK recall of `PINE-54`, with selected earlier evidence and
`memory_used: true` on the last of three generated user turns. Script-only mypy
also passed with the documented import setting. No pipeline PASS is an answer-quality
PASS.

```powershell
# First development run; inspect before choosing the improvement.
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 240 --output-dir artifacts/context-milestone-20261031 dev-before -- .\.venv\Scripts\python.exe scripts/evaluate_context_selection.py --fixture configs/context-eval-dev-v1.json --backbone-dir artifacts/qwen-chat-001/backbone --context-selector lexical-v1 --output-dir artifacts/context-milestone-20261031/dev-before
# Same development fixture after the one focused correction-grouping change.
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 240 --output-dir artifacts/context-milestone-20261031 dev-after -- .\.venv\Scripts\python.exe scripts/evaluate_context_selection.py --fixture configs/context-eval-dev-v1.json --backbone-dir artifacts/qwen-chat-001/backbone --context-selector lexical-v2 --output-dir artifacts/context-milestone-20261031/dev-after
# Frozen final before/after runs, sequentially.
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 300 --output-dir artifacts/context-milestone-20261031 final-before -- .\.venv\Scripts\python.exe scripts/evaluate_context_selection.py --fixture configs/context-eval-final-v1.json --backbone-dir artifacts/qwen-chat-001/backbone --context-selector lexical-v1 --output-dir artifacts/context-milestone-20261031/final-before
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 300 --output-dir artifacts/context-milestone-20261031 final-after -- .\.venv\Scripts\python.exe scripts/evaluate_context_selection.py --fixture configs/context-eval-final-v1.json --backbone-dir artifacts/qwen-chat-001/backbone --context-selector lexical-v2 --output-dir artifacts/context-milestone-20261031/final-after
.\.venv\Scripts\python.exe -m pytest -q tests/test_context_selection.py tests/test_chat_foundation.py tests/test_chat_release_eval.py tests/test_inference_server.py
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
$env:TORUK_LIVE_WEB_URL = 'http://127.0.0.1:3000'
$env:TORUK_TEST_CONTEXT = 'lexical-v2'
node --test web/vercel/tests/ui.test.mjs
Remove-Item Env:TORUK_LIVE_WEB_URL
Remove-Item Env:TORUK_TEST_CONTEXT
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe scripts/verify.py --prefix context --output-dir artifacts/context-milestone-20261031/verification
git diff --check
```

Focused tests cover dependent correction retention, chronological/verbatim selection,
the seven-message bound, lack of cross-request state, fixture separation, scoring,
and actual post-fitting selected IDs. Real evaluation requests are multi-turn
through the proxy. The optional live UI test also exercises TORUK across a generated
three-user-turn conversation, checking selected earlier evidence and actual recall.

GitHub Actions previously checked Python only. A Node 22 `web` job now runs the
proxy/UI unit tests and syntax checks. The Python job covers the selector, request
validation, checkpoint compatibility, packaging and research pipeline. CI does not
download the chat backbone or run the optional live/model comparison; those were
run locally. No remote CI result for this uncommitted work is claimed.

Strict source typing is checked by the project gate. An extra script-only typing
attempt also entered older untyped `scripts/check.py`; the appropriate script
check uses `--follow-imports=silent` and `MYPYPATH=src`. New scripts received only
type annotations after measurement, with no algorithm, fixture or scoring changes.
Exact executed script copies are archived as `evaluated-evaluator.py` and
`evaluated-fixture-builder.py`; their hashes match the measured identities.

During live-UI result extraction, its wrapper metadata file was accidentally
overwritten. The generated turns are now separate in `live-ui-results.json`;
command/result metadata was recovered from the unchanged log and source snapshot,
with the missing original start timestamp explicitly disclosed. The scored
development/final evaluation artifacts were unaffected.

## Remaining blockers and repository state

Public deployment remains blocked on conversational reliability, supported evidence
handling, a qualified inference host, secure account/runtime configuration, and an
actual browser preview. Local proxy readiness does not verify a public host.

A credible research-paper claim needs independently designed held-out templates,
larger diverse workloads, corrections the backbone can actually follow, robust
multi-hop support, independent scoring, matched compute/resource accounting,
ablations against simple retrieval baselines, uncertainty/repeated runs and
independent replication. A short heuristic comparison is not evidence for the
original learned-memory architecture or a novel mechanism. M6 weights remain absent.

All work remains on `main`, with the initial dirty work preserved. Nothing was
committed, pushed, published or deployed. Local services remain on ports 8766/3000
with Qwen and the explicitly labeled `lexical-v2` selector; both BASELINE and TORUK
are selectable. No backbone or hosting account was substituted.
