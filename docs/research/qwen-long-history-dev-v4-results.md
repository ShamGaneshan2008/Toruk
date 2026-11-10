# Qwen long-history development v4: audit of the two remaining v3 failures

10 November 2026. **No selector change is supported by these failures. Toruk
remains 5/7 versus lexical retrieval's 7/7.** This is a new offline audit of
saved development evidence, not a new inference run or independent evaluation.
Before and after this audit have identical selectors, prompts and saved answers.
No held-out answer file was parsed, scored or generated.

## Baseline and scope

The requested C-drive workspace was at `e3c143a` with 32 untracked verification
directories, and lacked `b079377`. Following the user's instruction to isolate
the work, the clean local repository `D:/Toruk` supplied an independent shared
clone at:

```text
C:/Users/susee/AppData/Local/Temp/Toruk-qwen-development-v4-b079377
```

Before changes, this checkout had empty Git status and detached HEAD
`b079377b913615046ffa3977382ae0d016dca2be`. Its Git objects are read through a
local alternate; its working tree, index and refs are independent. Both original
working trees were preserved. The initial audit performed no commit, push or
deployment. The subsequent user-authorized review commit contains only the
audit code, tests and this report.

[baseline.json](../../artifacts/qwen-long-history-dev-v4/baseline.json) seals 472
files: all tracked v1–v3 artifacts, protocols, results, configs, code and tests;
portable evidence; and the relevant selector, rendering and scorer sources.
Preservation compares raw SHA-256 bytes, including held-out files by hash only.
It does not parse held-out labels or answers. All 472 match after the audit.

The review covers README, architecture, the three protocols/results, recurrent
and lexical selection, v3 admission and tracing, prompt fitting, generation
settings, and the registered qualification/long-history scoring functions.
V1 remains blocked after host sleep; v2 remains a development rehearsal and
unexecuted held-out proposal; v3 remains its original adaptive 5/7 result.
Their protocols, failures, results, hashes and cost ledgers are unchanged.

## Reproducible development audit

[audit_qwen_development_v4.py](../../scripts/audit_qwen_development_v4.py) reads
only explicitly named development files and rejects held-out input paths before
opening them. It authenticates consumed files against portable evidence hashes
or the original registration. It extracts only the registered scorer, envelope
and input-projection functions, without running dataset generators or workers.
It uses the preserved Qwen tokenizer offline, with no backbone weights.

All three saved v3 arms (ungated BEFORE, lexical, gated AFTER) pass these checks
for seven scored questions plus the first-question replay, 24 requests total:

- Original selected source text and chronological prompt envelope match exactly.
- Native Qwen prompt IDs reproduce; output IDs decode to the exact saved answers.
- Proposed/fitted indices, required-source retention and gate traces agree.
- Gate overlap and top-two choices agree with the saved cosine scores; lexical
  choices reproduce directly from the original role/content histories.
- The original frozen scorer and failure labels reproduce every saved decision.
- Prompt/output totals and seven-case/replay-inclusive cost sums match v3's report.
- All three saved replays reproduce answer, score, prompt/output IDs, work and sources.

This audits recorded cosine scores; it does not rerun recurrent forwards or model
generation. The offline environment is Python 3.12.14, Torch 2.14.1+cpu and
Transformers 5.20.2, distinct from the original workers. Native prompt/output
verification succeeds despite that runtime difference; no fresh inference parity
is claimed. The new script never invokes the broad portable answer verifier,
which would also rescore other studies' held-out outputs.

[audit.json](../../artifacts/qwen-long-history-dev-v4/audit.json) contains complete
raw development rows, exact source indices/text, omitted indices, full rendered
native prompts, prompt/output IDs, scores, traces-derived checks and costs.
Its separate audit work took 7.0625 CPU / 8.1290471 wall seconds in this invocation;
this engineering cost is not a selector speedup or fresh model measurement.

## Failure 1: distant meeting point

Question: `Which meeting point was assigned in delivery ledger LHD-4F9D48AA0B8B?`

The v3 gate admits only m0 among older turns. It contains:

```text
Delivery ledger LHD-4F9D48AA0B8B assigns the meeting point copper quay.
```

Toruk proposes and supplies `[0,40,41,42]`; lexical proposes and supplies
`[0,38,40,41,42]`. No fit eviction occurs, and both are well below 512 tokens.
Both retain the full required source m0. Toruk's exact user prompt is:

```text
Reference:
User: Delivery ledger LHD-4F9D48AA0B8B assigns the meeting point copper quay.
User: Archive log 19: the clerk counted empty folders beside a quiet window, then checked the unused shelf and closed the book.
Assistant: Log noted.

Question:
Which meeting point was assigned in delivery ledger LHD-4F9D48AA0B8B?

Answer:
```

Lexical adds the following original m38 line immediately before Archive log 19:

```text
User: Archive log 18: the clerk counted empty folders beside a quiet window, then checked the unused shelf and closed the book.
```

The other omitted older sources are the initial acknowledgement and archive
user/assistant log turns. None adds a missing meeting-point fact. The full
history and exact omitted indices are retained in the new audit.

Toruk returns `delivery ledger LHD-4F9D48AA0B8B`; lexical returns
`Delivery ledger LHD-4F9D48AA0B8B assigned the meeting point copper quay.`
The frozen primary scorer rejects the former because it lacks the required
word-boundary value. It accepts the latter, even though its whole-answer exact
match is false. This is the registered known-fact rubric, not a scorer defect.

**Attribution: generation with required evidence present.** There is no observed
selection omission, text corruption, order reversal or budget eviction.
The extra lexical log changes prompt composition, but supplies no answer.

## Failure 2: absent override password

Question: `Which override password is given for inventory LHD-672B0E99F45C?`

Again, the gate admits only older m0. It contains:

```text
Inventory LHD-672B0E99F45C specifies a weight of 23 kilograms and a seal marked PLAIN.
```

Toruk supplies `[0,40,41,42]`; lexical supplies `[0,38,40,41,42]`, with no fit
eviction. Toruk's exact user prompt is:

```text
Reference:
User: Inventory LHD-672B0E99F45C specifies a weight of 23 kilograms and a seal marked PLAIN.
User: Archive log 19: the clerk counted empty folders beside a quiet window, then checked the unused shelf and closed the book.
Assistant: Log noted.

Question:
Which override password is given for inventory LHD-672B0E99F45C?

Answer:
```

Lexical inserts the same m38 Archive log 18 line as above. The complete history
contains no override password. Its omitted acknowledgement/log turns add none.
The dataset's empty required-source set is vacuously retained; this flag alone
does not prove that a requested fact exists or that abstention will succeed.

Toruk returns `PLAIN`, the unrelated seal marking. Lexical returns `UNKNOWN`.
The unchanged missing-information scorer requires valid abstention and rejects
`PLAIN`, with `unsupported_response_proxy=true`. Lexical passes primary and
exact-match scoring. There is no scorer error to repair.

**Attribution: unsupported generation / irrelevant-field substitution.** No
answer-bearing source exists for the selector to recover. V3's context change
introduced this pipeline regression relative to ungated BEFORE's `UNKNOWN`,
but this does not identify a general selector correction.

## Shared rendering, token counts and charged work

Both arms have this identical system instruction and native chat template:

```text
Use only the supplied reference to answer its question, including explicit corrections. Return just the requested value without explanation. If the requested information is missing, reply UNKNOWN. When asked to copy a quotation, preserve its text exactly.
```

Original generation: pinned Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, weights SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`,
float32 CPU/two threads, seed 81751, greedy one beam, cache, 64-token output cap.
No instruction, source order, model, decoding policy or scoring rule changed.

The following are original v3 measurements, unchanged after this audit.
Output counts include the native end token.

| Case / arm | Prompt / output tokens | Selector CPU / wall ms | Generation CPU / wall s | Request CPU / wall s |
|---|---:|---:|---:|---:|
| Distant / Toruk | 145 / 17 | 687.500 / 139.425 | 6.797 / 3.492 | 7.625 / 3.655 |
| Distant / lexical | 173 / 25 | below resolution / 0.973 | 14.031 / 6.838 | 14.109 / 6.862 |
| Missing / Toruk | 152 / 3 | 218.750 / 109.047 | 2.969 / 1.540 | 3.219 / 1.655 |
| Missing / lexical | 180 / 2 | below resolution / 0.641 | 2.953 / 1.509 | 2.984 / 1.514 |

Each Toruk question rescans all history and makes 65 recurrent forwards/updates:
2,806 byte positions for distant, 2,816 for missing. Lexical scans 21 term inputs,
2,429 / 2,439 bytes, with no recurrent forwards. Full-history BPE accounting is
767 / 774 positions in both arms. The additional lexical log costs 28 prompt
tokens in each case. Fewer prompt tokens do not establish lower complete work.

## Before/after answers and complete development comparison

No intervention was implemented, so **Toruk before = Toruk after** in this table.
These are authenticated saved answers, not newly generated after answers.

| Development category | Toruk before = after | Lexical | Toruk prompt/output | Lexical prompt/output |
|---|---|---|---:|---:|
| Distant | `delivery ledger LHD-4F9D48AA0B8B` (wrong) | `Delivery ledger LHD-4F9D48AA0B8B assigned the meeting point copper quay.` | 145/17 | 173/25 |
| Correction | `LHD-BC47D0CEDA8C is stored in the linen cabinet.` | same | 173/20 | 173/20 |
| Distractor | `mulberry` | same | 188/3 | 188/3 |
| Exact copy | exact plate below | same | 152/13 | 180/13 |
| Preservation | `flower hyacinth` | same | 183/5 | 183/5 |
| Reference | `velvet depot` | same | 126/4 | 154/4 |
| Missing | `PLAIN` (wrong) | `UNKNOWN` | 152/3 | 180/2 |

The exact-copy answer preserves two internal spaces:

```text
DEV/PUTYAOKYO:  R-4!
```

| Seven scored development cases | Historical ungated v3 BEFORE | V3 Toruk before this audit | Toruk after this audit | Lexical |
|---|---:|---:|---:|---:|
| Correct | 1/7 | 5/7 | 5/7, unchanged | 7/7 |
| Prompt / output tokens | 1046 / 41 | 1119 / 65 | unchanged | 1231 / 72 |
| Selector CPU / wall s | 1.891 / 0.839 | 1.969 / 0.805 | unchanged | below resolution / 0.00618 |
| Generation CPU / wall s | 26.750 / 13.554 | 34.063 / 17.573 | unchanged | 47.484 / 23.897 |
| Full request CPU / wall s | 28.859 / 14.449 | 36.234 / 18.434 | unchanged | 47.656 / 23.957 |

| Complete original cold stage, including replay | Ungated BEFORE | V3 Toruk | Lexical |
|---|---:|---:|---:|
| Prompt / output tokens | 1196 / 58 | 1264 / 82 | 1404 / 97 |
| Selector CPU / wall s | 2.109 / 0.942 | 2.188 / 0.917 | below resolution / 0.00675 |
| Stage CPU / wall s | 57.906 / 29.599 | 65.703 / 32.876 | 82.031 / 39.955 |

V3 versus lexical has zero wins, two losses and five ties. Both retain all six
known required-source sets; the two generation failures remain unresolved.
V3 previously improved on ungated Toruk, but did not beat lexical. This audit
changes no accuracy or cost result. Single fixed-order historical timings with
different output lengths, cache effects and host load cannot isolate selector
efficiency. The inherited selector profile/training cost remains 14.578125 CPU /
17.6733196 wall seconds, with unknown training peak RAM. No new selector or backbone training,
amortized efficiency, energy or FLOPs advantage is claimed.

## Why no selector change

Adding a fallback just to fill the unused older slot would insert zero-overlap
archive prose in these failures. The observed success of those two lexical
prompts does not establish that irrelevant padding is a general improvement.
Changing field handling or instructions would require a separately justified
intervention. No answer, question ID, expected fact, scorer change or output
repair was embedded in a selector. The existing v3 gate and every runtime source
remain byte-identical. There is no second candidate, new tuning run or held-out
test in this work. **Toruk did not improve over lexical retrieval.**

## Checks and reproduction

From the isolated checkout, using its local Python environment:

```powershell
.\.venv\Scripts\python.exe scripts/audit_qwen_development_v4.py --baseline artifacts/qwen-long-history-dev-v4/baseline.json --output artifacts/qwen-long-history-dev-v4/review-audit.json
.\.venv\Scripts\python.exe -m pytest -q tests/test_qwen_development_v4.py tests/test_qwen_long_history_v3.py tests/test_qwen_long_history_v2.py tests/test_qwen_long_history.py
npm.cmd --prefix web/vercel test
.\.venv\Scripts\python.exe scripts/verify.py --prefix review-v4 --output-dir artifacts/qwen-long-history-dev-v4/review-verification
git diff --check
```

Output files are exclusive: use a fresh output path when repeating the audit.
The local environment reads installed dependencies from the original C-drive
environment; editable installation and generated check outputs stay in the
isolated checkout. The original model-worker environment is not modified.

Focused checks pass: 48 Python tests, including 17 new audit tests; Node 20 pass,
one opt-in live test skipped. New tests distinguish selection omission from
generation, reject prompt/source/token/score corruption, reject held-out input
paths, detect frozen-file drift, and audit actual saved development evidence.
The initial check-wrapper invocation placed options after its remainder
argument and could not start the command; its FAIL receipt is preserved as
`checks/dev-v4-focused-preflight.*`. The corrected invocation passed without
model inference. Initial local implementation errors were corrected before
the saved audit; no frozen source was changed to accommodate them.

`scripts/verify.py` returned 0: all 26 stages PASS. Its full Python suite passed
344 tests in 157.11 seconds; Node passed 20 with one opt-in skip. Package lint,
format, native/Linux typing, frozen sources, dependency/CLI/data checks, existing
tiny fixture smokes, build and staged/unstaged diff checks passed. Those existing
fixture training/generation checks are engineering verification, separate from
the Qwen development comparison and its unopened held-out answers.

The final audit script also passes explicit Mypy with the package (37 source
files), lint/format, and a final rerun of all 48 focused contracts. A first
script-only Mypy invocation exposed one missing annotation and failed to discover
the local package types; its FAIL receipt is retained. The annotation was added,
and explicitly including `src/toruk_lm` resolved package discovery. This did not
change audit behavior or frozen code. Whitespace checks also cover the new,
untracked script, tests and report using `git diff --no-index --check`.

Machine-readable final check and preservation results are in
[verification-summary.json](../../artifacts/qwen-long-history-dev-v4/verification-summary.json).
Generated development evidence and verification receipts remain local and
untracked. The integration test uses the tracked portable manifest, so it does
not require those local receipts in a fresh checkout.
