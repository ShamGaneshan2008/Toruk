# Qwen long-history v3: development evidence audit and one admission gate

9 November 2026. **Development only. No research win; no held-out evaluation.**
The one gated variant scores 5/7, versus unchanged TORUK 1/7 and lexical 7/7.
It fixes five omissions, including exact copying and preservation, retains the
distant-answer generation error, and introduces an unsupported-password answer.
The no-loss-versus-lexical development target FAILS. No post-answer revision or
second candidate was tried.

## Working tree, old evidence and identities

The first command printed directory `C:\Users\susee\VS_CODE_PROJECT\Toruk` and
Git root `C:/Users/susee/VS_CODE_PROJECT/Toruk`. Earlier scientific inputs remain
in `D:/Toruk`. Initial HEAD was `25d4ec09e01397b43b9b16ad08faeca7cdb22eb0`, with
existing uncommitted v2 files. During implementation HEAD advanced externally to
`3e99626765dc6c4c9f5e6e84c4d02c169405b955` ("Add Qwen long-history protocols
and relevance gate"). No assistant commit/push/reset/checkout/stash/deployment
command was issued. The external commit and registration-time status are retained
in `external-git-change.json` and `attempt-001/starting-state.json`.

All 78 v2 registered input hashes and 45 sealed output hashes matched before
implementation and again at registration. V1/v2 evidence and source remain
unchanged; final preservation records also cover v2 supplemental evidence.
Six old D-drive package archives cannot be read and receive size/mtime checks
only, not a content-integrity claim. No held-out answer file was inspected or
generated. Only development cases were parsed; old bindings were checked by hash.

Backbone remains Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, weights SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
The shared successor checkpoint remains
`f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49`.
No weights were trained or reserialized. New implementation identity:
`8aca709df839b45dfa772f08b905882cef87ea6da5f08d04c96f770e178e4f93`.
See [selector-identity.json](../../artifacts/qwen-long-history-v3/attempt-001/selector-identity.json)
for separate gate-source and original-weight hashes.

## Seven-question v2 failure audit

All proposed TORUK sources fit within 512 tokens: there was no fit eviction.
Selected indices are chronological, selected text matches the original messages,
and rendered prompts match the shared envelope. No ordering reversal or prompt
rendering corruption was observed. Source IDs below refer to each case's original
history; IDs do not identify the same content across different cases. Each arm
also retains the identical latest three turns shown in the last column.

| Case / required answer | V2 TORUK older sources | Lexical older sources | Required sources | Common latest three | Diagnosis |
|---|---|---|---|---|---|
| Distant / `copper quay` | m0 location; m1 acknowledgement | m0 location; m38 archive log | m0 | m40,m41,m42 | Qwen returns ledger ID despite m0 containing the answer. Different selected composition may affect decoding; no isolated proof of an ordering/rendering cause. |
| Correction / `linen cabinet` | m0 obsolete `discarded chest`; m1 acknowledgement | m0 obsolete source; m8 explicit update | m8 | m42,m43,m44 | Required correction omitted; irrelevant acknowledgement consumes a slot. Correction never entered the prompt, rather than appearing in reversed order. |
| Distractor / `mulberry` | m1 ingredient acknowledgement; m3 acknowledgement | m0 approved ingredient; m2 competing order explicitly marked different | m0 | m42,m43,m44 | Answer-bearing source omitted in favor of acknowledgements. UNKNOWN is understandable from this selected prompt but fails the full-history task. |
| Exact copy / `DEV/PUTYAOKYO:  R-4!` | m1 and m3 acknowledgements | m0 exact quotation; m38 archive log | m0 | m40,m41,m42 | Quote omitted. This is not a whitespace-rendering or demonstrated copying failure: the quote never reached Qwen. |
| Preservation / `hyacinth` | m2 and m14 archive logs | m0 flower+shade; m10 update changing only shade | m0 | m42,m43,m44 | Original flower omitted, along with the unrelated shade correction. This does not demonstrate forgetting a supplied unchanged fact. |
| Reference / `velvet depot` | m3 and m5 archive logs | m1 route; m41 archive log | m1 and m43 | m43,m44,m45 | Recent crate anchor retained, but its earlier destination omitted; output repeats crate ID. |
| Missing / `UNKNOWN` | m0 weight/seal; m1 acknowledgement | m0 weight/seal; m38 archive log | No answer-bearing source exists | m40,m41,m42 | Correct abstention in v2. Inventory has a weight and PLAIN seal, but no override password. |

The exact original questions are:

1. `Which meeting point was assigned in delivery ledger LHD-4F9D48AA0B8B?`
2. `After the update, where is the material for LHD-BC47D0CEDA8C stored?`
3. `What approved jam ingredient belongs to order LHD-0B27D1C0E888?`
4. `Copy only the quoted plate for LHD-EBC6A8AD0D79, with exact spaces.`
5. `Which flower remains in garden record LHD-370844F31736?`
6. `Where is that same crate routed?`
7. `Which override password is given for inventory LHD-672B0E99F45C?`

[v2-development-diagnosis.json](../../artifacts/qwen-long-history-v3/attempt-001/v2-development-diagnosis.json)
retains each required source verbatim, both selectors' exact supplied evidence,
proposed/fitted IDs, answers, scores and attribution. Five failures are upstream
omissions with irrelevant replacements; distant recall is a downstream wrong
answer with evidence present. These are observable pipeline diagnoses, not an
exhaustive causal explanation of Qwen's internal computation.

## The one implemented change

[LexicalAdmissionSelector](../../src/toruk_lm/relevance_gate.py) admits an older
turn to the existing recurrent cosine competition only if it is a user turn
with at least one non-stopword query term in common, using lexical-v1's unchanged
tokenizer/stopwords. All recurrent summaries/state updates still run in original
order, including rejected/assistant/recent turns. Keep at most two older turns
plus the latest three, in source order, with unchanged 512-token whole-turn fit.
No answer extraction, correction rule, template/ID special case or prompt change.

This explicit lexical-plus-recurrent hybrid targets the observed candidate
admission failures. It is not semantic retrieval or evidence of learned
superiority. It can reject useful paraphrases and assistant-authored facts,
retain misleading overlaps, and underfill a slot that lexical fills with a
zero-overlap turn. There is no second fallback/tuning variant in this run.

The [v3 protocol](qwen-long-history-v3-protocol.md), config, gate, runner, tests,
development files, diagnosis, checkpoint manifest and source ZIP were registered
before new answers in `attempt-001/registration.json`. Evaluation is deliberately
adaptive on the seven already observed v2 development questions. No new dataset
or independent split was created; `development-overlap.json` records exact reuse
and the absence of new/training cases. Workers enforce the seven sealed IDs and
do not receive a held-out case file.

Fresh sequential controls are BEFORE, LEXICAL and AFTER, each seven questions
plus first-case replay. BEFORE and LEXICAL reproduce v2 prompt IDs, source IDs,
answers, generated IDs, frozen scores and work counters exactly. Every replay
matches. All arms share Qwen identity, source histories/questions, instructions,
native template, greedy 64-token decoding and 512-token budget. Selection traces
are serialized for all arms and charged in selector timing. The AFTER recurrent
byte-forward positions match BEFORE on every case: summaries/state scans were
not removed. V2 full/recent evidence is not relabeled as fresh v3 measurements.

## Before/after answers and selected prompt tokens

Exact strings, including the internal double space, are retained in raw JSON.
The table's short ledger/crate-ID descriptions stand for the full literal
answers listed immediately below.

| Case | Required | BEFORE answer | AFTER answer | Lexical answer | Prompt tokens BEFORE / AFTER / lexical |
|---|---|---|---|---|---:|
| Distant | copper quay | ledger ID | same ledger ID | correct sentence containing copper quay | 150 / 145 / 173 |
| Correction | linen cabinet | archive | correct linen-cabinet sentence | same correct sentence | 146 / 173 / 173 |
| Distractor | mulberry | UNKNOWN | mulberry | mulberry | 132 / 188 / 188 |
| Exact copy | double-spaced plate | Log noted | exact double-spaced plate | exact double-spaced plate | 129 / 152 / 180 |
| Preservation | hyacinth | UNKNOWN | flower hyacinth | flower hyacinth | 172 / 183 / 183 |
| Reference | velvet depot | crate ID | velvet depot | velvet depot | 160 / 126 / 154 |
| Missing | UNKNOWN | UNKNOWN | PLAIN (wrong seal field) | UNKNOWN | 157 / 152 / 180 |

Full literal answers for the longer cells:

```text
Distant BEFORE and AFTER:
delivery ledger LHD-4F9D48AA0B8B

Distant LEXICAL:
Delivery ledger LHD-4F9D48AA0B8B assigned the meeting point copper quay.

Correction AFTER and LEXICAL:
LHD-BC47D0CEDA8C is stored in the linen cabinet.

Exact-copy required, AFTER and LEXICAL (two spaces after colon):
DEV/PUTYAOKYO:  R-4!

Reference BEFORE:
crate LHD-C0BA0B7AB5DF
```

AFTER older-source IDs are m0 (distant), m0+m8 (correction), m0+m2 (distractor),
m0 (literal), m0+m10 (preservation), m1 (reference) and m0 (missing), plus the
same recent-three sets above. Known required-evidence retention improves from
1/6 to 6/6; lexical retains 6/6. Exact copy improves 0/1 to 1/1, and preservation
0/1 to 1/1. Against BEFORE: five improvements, one regression, one shared failure.
Against lexical: zero wins, two losses, five ties on this adapted development set.

## Selector and complete measured costs

Per-question selector CPU/wall milliseconds, including identical trace-writing
instrumentation. Zero lexical CPU is below process-timer resolution, not zero work.

| Case | BEFORE CPU / wall ms | AFTER CPU / wall ms | Lexical CPU / wall ms |
|---|---:|---:|---:|
| Distant | 593.750 / 161.479 | 687.500 / 139.425 | 0 / 0.973 |
| Correction | 218.750 / 104.865 | 218.750 / 115.668 | 0 / 1.334 |
| Distractor | 218.750 / 108.730 | 187.500 / 105.093 | 0 / 0.928 |
| Exact copy | 187.500 / 107.657 | 218.750 / 107.560 | 0 / 0.734 |
| Preservation | 187.500 / 98.494 | 203.125 / 109.046 | 0 / 0.689 |
| Reference | 296.875 / 164.564 | 234.375 / 118.740 | 0 / 0.883 |
| Missing | 187.500 / 93.147 | 218.750 / 109.047 | 0 / 0.641 |

| Seven scored cases | BEFORE | AFTER | Lexical |
|---|---:|---:|---:|
| Accuracy | 1/7 | 5/7 | 7/7 |
| Selected prompt / output tokens | 1046 / 41 | 1119 / 65 | 1231 / 72 |
| Selector CPU / wall seconds | 1.891 / 0.839 | 1.969 / 0.805 | below resolution / 0.00618 |
| Generation CPU / wall seconds | 26.750 / 13.554 | 34.063 / 17.573 | 47.484 / 23.897 |
| Full request CPU / wall seconds | 28.859 / 14.449 | 36.234 / 18.434 | 47.656 / 23.957 |

| Complete cold stage, INCLUDING replay | BEFORE | AFTER | Lexical |
|---|---:|---:|---:|
| Prompt / output tokens | 1196 / 58 | 1264 / 82 | 1404 / 97 |
| Selector CPU / wall seconds | 2.109 / 0.942 | 2.188 / 0.917 | below resolution / 0.00675 |
| Stage CPU / wall seconds | 57.906 / 29.599 | 65.703 / 32.876 | 82.031 / 39.955 |
| Sampled tree private peak bytes | 4,071,579,648 | 4,070,633,472 | 4,063,207,424 |

All 24 generations completed once, with no model retries, interruptions or
resource errors. Caps were fixed before inference: 180 wall/360 CPU seconds per
stage, 540 wall/1080 CPU cumulative, 30 seconds/request, 6 GiB worker-tree private
memory, 3 GiB study/input disk. Process-scoped idle-sleep prevention succeeded
and was restored. Clock/active-request/memory heartbeats and all incurred stages
remain in raw evidence. CPU includes controller plus sampled process tree with
final worker lifetime supplement; memory sampling can miss peaks and RSS can
double-count shared pages. Preparation/audit/check costs are separate records.

AFTER uses more prompt tokens than BEFORE, and fewer than lexical. Its complete
stage costs more than BEFORE; it also has lower accuracy than lexical. One
fixed-order local run with different output lengths and cache/load effects does
not establish a stable efficiency advantage. No FLOPs, energy, or total-system
saving follows from the token counts. No new training was done; inherited
profile/training (14.578125 CPU / 17.6733196 wall seconds) and unknown training
peak RAM remain disclosed separately, without a seven-question amortization claim.

## Remaining failures, limitations and checks

Distant recall still retains the complete copper-quay source yet returns the
ledger ID. Lexical additionally supplies a zero-overlap archive turn and answers
correctly. This demonstrates sensitivity to selected prompt composition; it does
not isolate an order effect, rendering defect or a generally sufficient prompt.

Missing information regresses to PLAIN, which is the seal marking in m0, not a
password. No password source exists. Classify this as unsupported Qwen generation
under the changed selected context, with irrelevant-field substitution. The
selector change caused a pipeline regression even though it retained all known
evidence. No output checker, extra instruction or second gate was added afterward.

All diagnostics except no-case-loss-versus-lexical pass; that condition fails.
The seven questions were explicitly used to design the rule, so these are
development-fitting observations. No confidence interval or generalization
claim is justified. Keep the held-out boundary closed. The recommended change
is the one implemented lexical admission rule, retained only as a development
candidate with unresolved abstention and distant-answer failures, not a release
or research advantage.

Ten new contracts and the nine existing v2 monitor contracts pass. They cover
high-scoring acknowledgement exclusion, irrelevant-turn rejection, continued
state updates across rejected turns, top-two/recent-three bounds, exact source
bytes, zero-overlap behavior, checkpoint-bound identity, short histories and
held-out-ID rejection. Explicit package/controller Mypy and source Ruff pass;
pre-registration static failures are retained in checks/. Broader local
`scripts/verify.py` returned 0 with all 26 stages PASS: 293 Python tests passed
in 154.33 seconds, Node passed 20 tests with one opt-in skip, lint/format and
default/Linux types passed, and package/data/fixture/build/diff checks passed.
Verification and its final summary are in artifacts/qwen-long-history-v3/;
general fixture tests are separate from Qwen inference. No hosted CI is claimed.

## Evidence paths and files changed

- [Protocol](qwen-long-history-v3-protocol.md), [config](../../configs/qwen-long-history-v3.json), [gate](../../src/toruk_lm/relevance_gate.py).
- [Registration and source ZIP](../../artifacts/qwen-long-history-v3/attempt-001/registration.json).
- [Complete per-case before/after audit](../../artifacts/qwen-long-history-v3/attempt-001/results.json).
- [Original v2 per-case diagnosis](../../artifacts/qwen-long-history-v3/attempt-001/v2-development-diagnosis.json).
- [Raw BEFORE outputs](../../artifacts/qwen-long-history-v3/attempt-001/arms/before/rehearsal/development-toruk-answers.jsonl).
- [Raw AFTER outputs](../../artifacts/qwen-long-history-v3/attempt-001/arms/after/rehearsal/development-toruk-answers.jsonl).
- [Raw lexical outputs](../../artifacts/qwen-long-history-v3/attempt-001/arms/lexical/rehearsal/development-lexical-answers.jsonl).

Each arm directory includes exact selected sources, prompt/output IDs, frozen
scores, selection traces, byte/BPE work counters, setup/request/component timing,
process-tree memory, logs and heartbeats. New files are the research gate, v3
protocol/config/report, development runner, offline reporter, contract tests and
v3 artifacts. Existing v1/v2 source/evidence is preserved. No held-out answer was
opened or generated, and the assistant did not commit, push or deploy.
