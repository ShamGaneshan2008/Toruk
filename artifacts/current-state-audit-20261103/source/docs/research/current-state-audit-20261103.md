# Current-state audit and one blocker closed — 3 November 2026

Selected branch: **C, repair the evidence/replay pipeline**. Local loading and
chat work, and the trained selectors and integrated research models exist.
Before another model change, this audit found and reproduced a gap in binding
the actual files consumed when a sealed run is copied to another directory.
The original frozen negative result remains valid and unchanged.

## Repository and actual weights

Working directory: `C:\Users\susee\VS_CODE_PROJECT\Toruk`. Branch: `main`.
HEAD and freshly fetched origin/main:
`f7862c0789ed772c1068832962eba176a4fbcd1b`. Initial working tree was clean;
ahead/behind was 0/0. Both merge histories and backup branches are preserved.
There are no local commits absent from the visible remote. Unpublished work on
another device cannot be determined from this checkout or origin.

[Repository evidence](../../artifacts/current-state-audit-20261103/repository.json)
and [actual weight inventory](../../artifacts/current-state-audit-20261103/weights.json)
record paths, types, sizes and full SHA-256 values. The initial inventory found
84 weight/selector files totaling 1,277,384,735 bytes, including research/smoke
duplicates. The final inventory also identifies new tiny verification fixtures;
the original snapshot is retained as weights-initial.json. No checkpoint was
inferred from a documentation path or downloaded for this audit.

Key existing files are ordinary foundation weights, controlled smoke weights,
both pretrained backbones, JSON conversational selectors, integrated v1's four
checkpoints, and routing v2's two checkpoints. Qwen weights are 988,097,824 bytes;
SmolLM weights are 269,060,552 bytes; the new routing checkpoints are 871,337 bytes
each. Original evaluated M6 and minimal-demo checkpoints remain **absent**.
Configured Ollama support is separate; no external Ollama weights/service were
verified, and none are inferred from historical reports.

## Verified capability matrix

Statuses concern the described feature; useful research claims are assessed
separately. Command labels refer to full argv/exit codes in the
[command ledger](../../artifacts/current-state-audit-20261103/commands.json).
Code and checkpoint links are exact repository paths; ignored weights exist
locally and are absent from a public Git-only checkout.

| Item | Status | Code and checkpoint | Command and raw evidence | Limit |
|---|---|---|---|---|
| 1. Ordinary causal LM | TESTED | [model.py](../../src/toruk_lm/model.py), [engine.py](../../src/toruk_lm/engine.py); `artifacts/foundation-001/train/checkpoint.pt` | `ordinary-generate`; [real continuation](../../artifacts/current-state-audit-20261103/checks/ordinary-generate.log) | Generates ` 00000000000` on this probe; execution does not establish useful chat. |
| 2. Controlled recurrent experiments | TESTED smoke; historical M6 replay BLOCKED | [recurrent.py](../../src/toruk_lm/recurrent.py), [controlled.py](../../src/toruk_lm/controlled.py); actual [fresh smoke checkpoint](../../artifacts/current-state-audit-20261103/controlled-smoke/recurrent-full/checkpoint.pt) | `controlled-cli-smoke`; [raw resume/score results](../../artifacts/current-state-audit-20261103/controlled-smoke/summary.json) | Ordinary/recurrent resume passes; tiny smoke factual scores are zero. Original evaluated M6 weights are missing. |
| 3. Pretrained conversational backbone | TESTED | [chat_foundation.py](../../src/toruk_lm/chat_foundation.py); `artifacts/qwen-chat-001/backbone/model.safetensors` and `artifacts/chat-foundation-001/backbone/model.safetensors` | `chat-baseline-and-selector`, `refusal-replay`; [Qwen responses](../../artifacts/current-state-audit-20261103/chat-paired/results.json), [SmolLM replay](../../artifacts/current-state-audit-20261103/refusal-replay.json) | Third-party language ability, not Toruk-trained language weights. |
| 4. BASELINE page → proxy → Python | TESTED DOM/HTTP path | [page](../../web/vercel/public/index.html), [proxy](../../web/vercel/lib/proxy.js), [server](../../src/toruk_lm/inference_server.py); Qwen above | `page-handlers`, `chat-baseline-and-selector`; [live handler prompts/responses](../../artifacts/current-state-audit-20261103/page-handlers/page-handlers.log) | Real inference and page handlers in a DOM harness; an interactive browser session was not run. |
| 5. TORUK selection on that path | TESTED | [chat_selector.py](../../src/toruk_lm/chat_selector.py); [v2 selector](../../artifacts/chat-selector-v2-20261101/selector.json) | `chat-baseline-and-selector`; [paired result](../../artifacts/current-state-audit-20261103/chat-paired/results.json) | Both modes answer LIME42; 350→165 selected tokens on this one smoke case, not a research win. |
| 6. Trained conversational selector | TESTED integration | [v2 trainer](../../scripts/train_chat_selector_v2.py); [v1](../../artifacts/chat-selector-v1-20261101/selector.json), [v2](../../artifacts/chat-selector-v2-20261101/selector.json) | Same live command; [historical held-out result](chat-selector-v2-results.md) | Trained turn ranker only. Historical final score 22/28 versus recent 26/28. No fresh fitting in this audit. |
| 7. Integrated Toruk memory in LM inference | TESTED research-only | [integrated_memory.py](../../src/toruk_lm/integrated_memory.py), [pooled_router.py](../../src/toruk_lm/pooled_router.py); `artifacts/routing-v2-20261103/train/new-{31,47}.pt` | `primary-result-replay`; [new generated answers](../../artifacts/current-state-audit-20261103/primary-replay.json) | State directly conditions the small conditional byte decoder. It is not integrated into Qwen/chat. |
| 8. Correction/preservation/recall/unknown performance | FAILED useful-quality gate | Same research models and checkpoints | `primary-result-replay`, `frozen-package-scoring`; [unchanged per-category scores](../../artifacts/routing-v2-20261103/summary.json) | V2 correction 4/24, preservation 3/24, distant recall 4/24, unknown and ambiguity 24/24 each, multi-fact 0/24, both seeds. Value outputs collapse. |
| 9. Selected prompt reduction | TESTED descriptively | External selector above; integrated suffix unchanged | [live paired telemetry](../../artifacts/current-state-audit-20261103/chat-paired/results.json), [multi-seed table](../../artifacts/routing-v2-20261103/table.md) | Some selector prompts shrink. V2 integrated prompts do not. Preserved useful accuracy remains unestablished. |
| 10. Total resource efficiency | FAILED claim | [history/accounting code](../../scripts/study_routing_v2.py), same checkpoints | [registered full-history resources](../../artifacts/routing-v2-20261103/report.md), [fresh replay totals](../../artifacts/current-state-audit-20261103/primary-replay.json) | Full scans, state updates and extra routing work remain. No qualified latency/RSS/FLOP/energy advantage. |
| 11. Multi-seed held-out comparisons | TESTED negative result | [protocol](routing-v2-protocol.md), [bound replay](../../scripts/replay_routing_v2.py), exact checkpoints above | `primary-result-replay`: 2,016 world predictions /2,304 answers match; `frozen-package-scoring`: 6,912 saved answers and 216 files verify | Two training seeds, three evaluation seeds, finite shared vocabulary. Only primary load regenerated; stress outputs independently rescored, not newly generated. |
| 12. Inference-host build | BLOCKED | [Dockerfile](../../deploy/huggingface/Dockerfile), [allowlist packager](../../scripts/prepare_inference_package.py); requires absent M6 checkpoint | `docker-engine` exits 1; `host-package-prerequisite` exits 2; [logs](../../artifacts/current-state-audit-20261103/checks/docker-engine.log) | Docker CLI exists but engine pipe is unavailable. No image built; no host provisioned. Recipe existence is not a successful build. |
| 13. Authentic Vercel preview/public chatbot | BLOCKED locally; external existence unverified | [frontend config](../../web/vercel/vercel.json), [hosting guide](../vercel-chat.md); no local linked-project metadata | No Vercel CLI or `.vercel/project.json` found; Node/local page checks above | No authentic Vercel build/deployment was performed or verified. A frontend does not supply model inference. |

## One blocker and its closure

The retained historical verifier checks each pathname written in its freeze file.
In a copied run those names still identify the original directory, while evaluation
reads `final.json` and new checkpoints under the supplied run directory. A separate
probe copied only metadata, provided an empty final dataset and no copied weights,
and the historical verifier still returned success. This is an input-binding gap,
not proof that the original negative predictions used wrong data.

Before: [original verifier acceptance](../../artifacts/current-state-audit-20261103/binding-before.json).
After: [rejected alias](../../artifacts/current-state-audit-20261103/checks/alias-rejection-expected.log).
The latter intentionally exits **1** before model loading/generation and creates
no answer file; the rejection is the expected regression-test outcome.

Added [replay_routing_v2.py](../../scripts/replay_routing_v2.py), which binds actual
dataset/checkpoint paths to the reference seal, checks referenced raw answer
identities, loads the exact model/selector and compares fresh outputs against the
recorded answers, token IDs, evidence selection, workload and route diagnostics.
Copied inputs are accepted only when their consumed bytes match. Eight focused
[tests](../../tests/test_sealed_replay.py) cover matching copies, altered data,
altered/missing weights, altered metadata, ambiguous identities and modified
reference outputs. Existing frozen source, answers and model weights are untouched.

**Use this bound replay entry point for existing sealed results.** The old driver
remains preserved for historical source identity; its copied-run check alone is
not an adequate replay guarantee. This audit does not claim to rewrite that
immutable historical implementation or to harden every old experiment family.

## Reproduction and before/after model outputs

The full primary-load comparison was regenerated with existing checkpoints:

| Method | Original exact /168, seeds 31/47 | Fresh replay | Known /120 | Unsupported /48 |
|---|---:|---:|---:|---:|
| Recent | 30 /25 | 30 /25 | 7 /8 | 25 /31 |
| Lexical | 35 /25 | 35 /25 | 9 /8 | 22 /31 |
| Learned selector diagnostic | 35 /27 | 35 /27 | 9 /8 | 22 /29 |
| Old integrated | 23 /39 | 23 /39 | 6 /21 | 31 /30 |
| Routing v2 | 62 /62 | 62 /62 | 14 /14 | 0 /0 |
| Routing v2, state zeroed | 48 /48 | 48 /48 | 0 /0 | 0 /0 |

All generated strings/IDs and deterministic telemetry match. Fresh timings are
stored as new observations, not compared for byte equality or claimed speedups.
No new research model was trained; verification includes tiny CLI/test fixtures.
The primary replay command took 18.584 seconds including startup. It repeats
inference on previously scored test worlds solely for reproduction, not tuning.

Real replayed v2 examples remain `blue` for `color? Ben's is What` (expected blue),
`cat` for `pet? Cyd's is What` (expected green in preservation world
`8101-preservation-3`), and `blue` for `pet? Cyd's is What` (expected dog in
`8101-correction-2`). The decoder's value-collapse diagnosis is unchanged.

## Refusal-history diagnostic retained

[replay_refusal_diagnostic.py](../../scripts/replay_refusal_diagnostic.py) uses the
actual stored histories from
[full-history-matched.json](../../artifacts/chat-repetition-exact-20261101/full-history-matched.json).
It refuses a different model identity and records current generation config.
SmolLM2-135M-Instruct revision `12fd25f77366` prefix and actual weight identity
match the original model. BASELINE, temperature 0, top-p 1 and the original 32/64
output-token budgets are held fixed. Prompt-token counts match as well.

| Exact saved diagnostic | Before | After |
|---|---|---|
| Fresh `what is 5+5`, budget 32 | `5 + 5 = 10.` | Identical |
| Fixed full refusal history ending `what is 5+5`, budget 32 | `I'm sorry for any confusion, but as a chatbot, I don't have the capability to access or interact with online content.` | Identical |
| Same fixed history, budget 64 | Same refusal | Identical |

[Full before/after requests, answers and settings](../../artifacts/current-state-audit-20261103/refusal-replay.json)
remain diagnostic evidence. This behavior has **not** changed; it is not called
a repaired transport bug. The historical TORUK-mode replay is BLOCKED by missing
original M6 selector weights and was not relabeled using the newer JSON selector.
Qwen is a different backbone; its separate smoke cannot substitute for this test.

## Checks, CI and limits

Full Python suite: **168 passed**. Eight final focused binding tests also pass.
Runtime mypy passes on 28 source files; combined runtime and new replay scripts
pass on 30 files for both Windows and Linux analysis. An initial standalone
script-type invocation exposed missing
source-package search context and heterogeneous-list inference errors; its exit-1
log is retained, the annotations were corrected, and the combined check exits 0.
Focused lint/format, Node syntax, 13 ordinary Node tests, CLI generation/help/
diagnose, controlled resume smoke, and two separately enabled live page-handler
tests pass. Ordinary Node tests skip one optional live-handler test; the explicit
live suite runs it successfully. Interactive browser testing is unrun.

Repository-wide lint exits 1 on 49 existing findings in three frozen scripts;
format exits 1 for those same files. They remain unchanged. Fresh package build
and final `git diff --check` are recorded in the command ledger. Docker/Vercel
builds and historical TORUK refusal replay are blocked as documented above.
There is no paid job, new research training, model download or deployment.

For exact HEAD, [Actions run 41653980796](https://github.com/ShamGaneshan2008/Toruk/actions/runs/41653980796)
has web **success**, Python job **failure at Ruff**. Later Python format/types/
tests/build steps are skipped remotely. [Fresh remote evidence](../../artifacts/current-state-audit-20261103/remote-ci.json)
distinguishes this commit from the new uncommitted audit changes, which are
**NOT_RUN remotely**. Local checks are not remote CI passes.

## Separate verdicts and one next milestone

| Claim | Verdict |
|---|---|
| Useful chat | INCONCLUSIVE as a general capability; local Qwen examples work, historical refusal remains, broad reliable conversation unqualified. |
| Toruk-trained memory | TESTED implementation; useful-memory claim FAILED. |
| Factual accuracy | FAILED useful-quality gate; v2 known-world accuracy remains 14/120. |
| Selected-token reduction | TESTED on selector cases; preserved useful accuracy FAILED/unestablished. |
| Total efficiency | FAILED claim; full history/update work remains and no qualified cost advantage is shown. |
| Paper readiness | BLOCKED on useful factual quality and broader evidence; no novelty/publication claim. |
| Deployment/public readiness | BLOCKED on host/build/account prerequisites and answer quality. |

The next **single** milestone is a development-only value-fidelity gate for the
existing routing-v2 model: test training/development wording variation that
forces arbitrary values to survive, while retaining the existing architecture.
Require corrected and preserved factual quality plus safe abstention before
opening any new final set. Do not train/tune against this audit's replayed answers.
No second model, training objective, backbone replacement or deployment is added
in this milestone.

Exact Windows PowerShell replay:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
& $py scripts/replay_routing_v2.py --sealed-run artifacts/routing-v2-20261103 --loads 0 --output artifacts/current-state-replay.json
& $py scripts/audit_routing_v2.py --run artifacts/routing-v2-20261103 --manifest
& $py scripts/replay_refusal_diagnostic.py --reference artifacts/chat-repetition-exact-20261101/full-history-matched.json --backbone-dir artifacts/chat-foundation-001/backbone --output artifacts/refusal-replay-fresh.json
& $py -m pytest -q tests/test_sealed_replay.py -p no:cacheprovider
```

Outputs must be fresh. Replays require the original locally retained ignored
weights and the recorded runtime; Git alone does not distribute those weights.
Initial/final Git status and exact command/exit-code records are retained with
the audit. No commit, push or deployment was made during this task.
