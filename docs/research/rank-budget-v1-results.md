# Fixed-budget evidence selection, 4 November 2026

The candidate recovers distant evidence and increases fixed-test correctness from
4/12 to 8/12, but **fails the preregistered success criterion**: the frozen
unsupported-answer proxy increases from 2/12 to 3/12. It now answers one corrected
credential with its obsolete value. The candidate remains research-only; the
browser/server defaults are unchanged. This is a bounded mixed result, not a
qualified memory capability or a lower-total-cost claim.

Starting commit: `84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`, branch `main`, clean
Git status before work. README, architecture, experiment registry, current chat
guide and latest recall V2 report were read before mechanism edits. No weights,
backbone, scorer, evaluation questions or historical experiment files changed.
No commit, push, deployment, model download or research training was performed.

## Prerequisite reproduction and measured blocker

The latest full chat comparison is [recall V2](recall-results-20261104.md), using
the pinned local Qwen2.5-0.5B-Instruct backbone, 512 prompt tokens, 48 output
tokens, greedy decoding, 12 cases per split and 18 distraction pairs per case.
Installed dependency versions match the recorded `versions.json` exactly.

Fresh registration regenerated identical training/development/heldout JSON data.
Both inference stages completed. The independent
[replay comparison](../../artifacts/blocker-replay-20261104/comparison.json)
requires equality of all **96** cases/method rows' answers, prompt token IDs,
scores, source provenance, evidence-retention flags, source/scan bytes and
deterministic token counters. All matched. Timing and RSS naturally vary.
The unchanged reporter also independently reproduced prompt fitting and scores.
This is fresh inference, not saved-output rescoring alone. Original seals pass.

The initial command against the original output directory was correctly rejected
with `ValueError: refusing existing outputs`; originals were preserved and the
documented fresh-directory procedure was used. That protective rejection is not
an irreproducible experiment.

The reproduced envelope fails eight heldout cases: **five lost-evidence**, then
**three generation-despite-evidence** diagnoses under the unchanged attribution
rule. Recent context has 11 lost-evidence and one generation failure; lexical
and old learned selection each have five and three. No source-byte corruption
was found. The reporter's `evidence_retained` requires every marked source,
including unrelated launch facts; it is conservative rather than a causal proof.

Concrete selection failures in development identify the absolute cutoff: a
revised message policy scores **0.1857**, and an earlier credential **0.0994**,
both below the fixed **0.2** threshold despite available ranking slots. The old
envelope answers the former with the superseded policy and declines to answer
the latter. In reproduced heldout, it answers an unlock question with
`Clouds drift east.` and an unchanged unlock credential with the launch date
`2043-03-11`. These establish missing evidence as the dominant observed group;
they do not imply that thresholding explains every selection failure.

## Hypothesis and bounded implementation

The [protocol](rank-budget-v1-protocol.md) was written before mechanism edits.
Hypothesis: remove the learned ranker's absolute cutoff while preserving its
top-two ranking budget, recovering low-scoring evidence at lower request cost
per correct answer. Required heldout outcomes: **at least 6/12 correct**, **at
most 2/12 unsupported proxy**, and **at least 10% lower summed full-request
milliseconds per correct answer** against the reproduced envelope. All three
must pass.

`RankBudgetSelector` delegates the unchanged feature computation and scores to
the original checkpoint, retains the two highest-scoring earlier user turns,
then the same three recent turns, all in chronological order.
`RankBudgetEnvelopeSelector` retains the existing serialization and bounds:
64 messages/16 KiB input, eight source turns/4 KiB selected text, 512 final prompt
tokens. There is no answer parser, domain vocabulary, canned response, hidden
fallback, persistent memory or additional training.

Development ran once, then its outputs and intervention manifest were frozen.
Heldout ran once, with no mechanism edits or inference retries. Both use exactly
the existing V2 questions and scoring. Every recent/lexical/old baseline prompt
and answer matches the reproduction again, **72/72** across the two splits.
The V2 heldout set was already published; this follow-up is not a new unseen
test, and these tiny descriptive results do not establish generalization.

## Quality, gains and regressions

| Split / method | Exact /6 | Gist /2 | Clear reference /2 | Ambiguous /1 | Missing /1 | All /12 | Unsupported proxy |
|---|---:|---:|---:|---:|---:|---:|---:|
| Development / envelope before | 3 | 1 | 1 | 0 | 1 | 6 | 3 |
| Development / candidate | 3 | 2 | 2 | 0 | 0 | 7 | 3 |
| Heldout / recent | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| Heldout / lexical retrieval | 2 | 1 | 1 | 0 | 0 | 4 | 2 |
| Heldout / old learned selector | 2 | 1 | 1 | 0 | 0 | 4 | 2 |
| Heldout / envelope before | 2 | 1 | 1 | 0 | 0 | 4 | 2 |
| Heldout / candidate | 4 | 2 | 2 | 0 | 0 | 8 | 3 |

Development gains are the revised policy and earlier credential. The sole
development regression is missing evidence: a refusal changes wording and loses
the frozen matcher's `clarify` phrase. It still acknowledges unavailable
information. We retain the primary regression rather than repairing the rubric.

Heldout has **five gains and one regression**; all changed outputs appear in the
[comparison](../../artifacts/rank-budget-v1-20261104/comparison.json).

| Heldout case | Envelope before | Candidate | Outcome |
|---|---|---|---|
| Exact credential | `Clouds drift east.` | `H/0: 9_x!` | Gain |
| Distant credential | Uncertainty instead of value | `H/1: 9_x!` | Gain |
| Preserve credential after launch correction | `2043-03-11` | `H/4: 9_x!` | Gain |
| Message-handling gist | Missing frozen retention concept | Explicitly retains and retries online | Gain |
| Clear pronoun | `clouds drift east` | `H/8: 9_x!` | Gain |
| Corrected credential | `H/3: 9_x!` | `obsolete-2-3` | **Regression: stale correction** |

The regression admits the obsolete record alongside the revision; the same
decoder then chooses the obsolete value despite both being present. Exact motto
still becomes `"Wait? Five turns."`, changing spacing and adding outer quotes.
Ambiguity still elicits `H/10: 9_x!` instead of clarification. Missing evidence
still receives a refusal that the narrow frozen matcher fails to recognize.

Distant known-fact correctness (exact/gist/clear; ten questions with answers)
is **4/10 -> 8/10** heldout and **5/10 -> 7/10** development. All marked source
retention is **5/10 -> 9/10** heldout and **7/10 -> 9/10** development. Preservation
answers correctly despite dropping an unrelated marked launch turn. These are
fixed-gap results, not a context-length scaling curve.

The candidate's four heldout failures all retain marked evidence: one exact-copy
generation error, one stale correction, one ambiguous reference guess and one
uncertainty-rubric false negative. No failed candidate answer is attributed to
lost evidence, incorrect source bytes, or selector/memory cost. This descriptive
breakdown does not establish that all semantic errors have been detected.

The unchanged unsupported metric is a **proxy, not a complete false-assertion
count**. A separate posthoc assistant review uses the previous report's same rule
and records every answer/rationale in
[assertion-review.json](../../artifacts/rank-budget-v1-20261104/assertion-review.json).
It flags unsupported world assertions in 7/12 recent, 7/12 lexical, 6/12 old,
4/12 previous envelope and **2/12 candidate** answers (stale correction and
ambiguous binding). Refusals and exact-formatting deviations are treated
separately. This subjective, non-independent review does not replace the frozen
scores or turn the failed proxy gate into a pass. The old lexical/learned gist
passes still contain invented policy details under that review.

## Full-history work and resource costs

Heldout totals below are over 12 requests per method. Baseline rows are from the
candidate's matched run; the previous envelope row is the preceding reproduction.
All deterministic baseline counts match across both runs.

| Method | History tokenization | Fit tokens / attempts | Model prompt / output tokens | Logical scan bytes | Selector probe ms | Request seconds | Max source bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Recent | 8,138 | 50,782 /87 | 5,886 /167 | 0 | 0.035 | 56.70 | 1,842 |
| Lexical | 8,138 | 2,152 /12 | 2,152 /207 | 20,451 | 1.148 | 40.75 | 350 |
| Old learned | 8,138 | 1,816 /12 | 1,816 /191 | 20,451 | 3.641 | 37.42 | 350 |
| Envelope before | 10,304 | 2,552 /12 | 2,552 /221 | 20,451 | 3.461 | 42.16 | 350 |
| Candidate | 10,304 | 2,931 /12 | 2,931 /193 | 20,451 | 3.886 | 43.96 | 350 |

Zero recent-selector scan excludes its tokenization and repeated fitting.
Selector probe time measures the extra diagnostic selection, not a separately
instrumented inner-request duration. Request time includes real input
tokenization, selection, fitting and generation; it excludes the diagnostic
probes and model startup. Fit probe time is 10.70 -> 13.32 ms for before/candidate.
The envelope adds a validation/formatting pass; logical scan bytes are not a
count of every internal regex/encoding read. Token work is not FLOPs.

Compared with the envelope, candidate prompt tokens rise **14.9%**, prompt plus
output tokens **12.7%**, and summed request latency **4.3%**. Absolute total
request cost did **not** fall. Request time per correct answer falls from
**10.54 s to 5.49 s (47.9%)**, satisfying only the cost-per-correct gate.
Timing is descriptive on one CPU host in fixed method order; baseline timings
also drift between runs. There is no statistically controlled speed claim.

Cumulative framework/backbone-inclusive process peak is **2,474,401,792 bytes**
for the reproduction's heldout stage and **2,470,252,544 bytes** for the candidate
stage (about 2.30 GiB each). The same cumulative high-water mark applies across
methods within a stage; it is not per-selector allocation or a memory saving.
Maximum retained content remains 350 bytes; Python objects, model weights,
tokenizer buffers and envelope overhead are additional. There is no durable
memory state.

Candidate development/heldout evaluation-loop wall time is **162.25/179.03 s**;
full subprocess time including startup is **173.13/189.87 s**. Reproduction
full subprocess time is **202.46/176.52 s**. Four stages generate **192 answers**
in total. Registration, token-only reporting and engineering checks add separate
work retained in the command evidence. No research training or paid API tokens
were used; electricity/energy and FLOPs are unmeasured, so no dollar-cost or
total-compute saving is asserted.

The criterion therefore **FAILS**: correctness and cost-per-correct pass, but
unsupported proxy fails. The single next highest-priority blocker is **faithful
generation from retained evidence, especially rejecting obsolete corrected
values**. All four remaining candidate failures occur with marked evidence
available. Another intervention requires a new preregistered development study;
this heldout result must not be used for further tuning.

## Commands and engineering verification

Run from the repository root. Use fresh output directories; the drivers and
reporters refuse overwrites. Existing local pinned model and selector artifacts
are required. The full command/source/result ledger is under
[verification](../../artifacts/rank-budget-v1-20261104/verification/) and inference
logs under [checks](../../artifacts/rank-budget-v1-20261104/checks/).

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
$baseline = 'artifacts/blocker-replay-20261104'
$run = 'artifacts/rank-budget-v1-20261104'
& $py scripts/recall_v2.py register --run $baseline
& $py scripts/check.py --timeout 480 --output-dir "$baseline/checks" development -- $py scripts/recall_v2.py development --run $baseline
& $py scripts/check.py --timeout 480 --output-dir "$baseline/checks" heldout -- $py scripts/recall_v2.py heldout --run $baseline
& $py scripts/compare_recall_runs.py --reference artifacts/recall-v2-20261104 --replay $baseline --output "$baseline/comparison.json"
& $py scripts/report_recall.py --run $baseline
& $py -m ruff check src/toruk_lm/rank_budget.py scripts/rank_budget_study.py scripts/compare_recall_runs.py tests/test_rank_budget.py tests/test_compare_recall_runs.py
& $py -m ruff format src/toruk_lm/rank_budget.py scripts/rank_budget_study.py scripts/compare_recall_runs.py tests/test_rank_budget.py tests/test_compare_recall_runs.py
& $py -m pytest -q tests/test_rank_budget.py tests/test_compare_recall_runs.py
& $py scripts/rank_budget_study.py register --run $run
& $py scripts/check.py --timeout 480 --output-dir "$run/checks" development -- $py scripts/rank_budget_study.py development --run $run
& $py scripts/check.py --timeout 480 --output-dir "$run/checks" heldout -- $py scripts/rank_budget_study.py heldout --run $run
& $py scripts/rank_budget_study.py report --run $run
& $py scripts/report_rank_budget.py --reference $baseline --run $run
& $py artifacts/rank-budget-v1-20261104/review_assertions.py
& $py scripts/verify.py --output-dir "$run/verification"
& $py scripts/check.py --output-dir "$run/verification" node-check -- npm.cmd --prefix web/vercel run check
& $py scripts/check.py --output-dir "$run/verification" node-tests-utf8 -- npm.cmd --prefix web/vercel test
& $py scripts/check.py --timeout 300 --output-dir "$run/verification" research-types -- $py -m mypy scripts/rank_budget_study.py scripts/report_rank_budget.py scripts/compare_recall_runs.py --disable-error-code import-untyped --disable-error-code misc
git diff --check
```

`verify.py` records each local Python CI-equivalent command individually,
including editable installation, dependencies, imports, CLI diagnostics, frozen
source hashes, full Ruff lint/format, strict runtime mypy on Windows and Linux,
full pytest, ordinary/recurrent CPU smoke/config validation, artifact validation,
summarization, package build and whitespace checks. Research harness typing uses
the existing documented suppressions for untyped psutil and intentional backend
class substitution; runtime typing remains strict. No remote check of these
uncommitted changes is claimed.

| Final check | Result |
|---|---|
| Fresh reproduction and independent comparison | PASS, 96/96 exact rows |
| Candidate inference/reporting; baseline parity | PASS execution, 72/72 unchanged baseline rows; quality gate FAIL |
| Focused regression tests | PASS, 10 tests |
| Full Python suite | PASS, 195 tests, zero skips, 142.97 s |
| Full Ruff lint / formatting | PASS / PASS, 107 files formatted |
| Strict runtime mypy Windows / Linux | PASS / PASS, 30 files each |
| Research harness mypy with documented suppressions | PASS, three requested scripts |
| Node syntax / tests | PASS / PASS, 13 passed, one optional live-page skip |
| Dependency/import/install/CLI checks | PASS |
| Ordinary/recurrent smoke, resume/config/artifact checks | PASS execution; no factual-quality claim |
| sdist and wheel build | PASS |
| Frozen experiment source hashes | PASS, three historical files preserved |
| `git diff --check` / staged whitespace | PASS / PASS |
| Remote CI for uncommitted changes | NOT_RUN |

All 19 Python CI-equivalent commands in `verify.py` finish successfully. No live
browser/page-handler check was requested for unchanged UI code; the normal Node
suite's optional live test is visibly skipped. The first Node-test wrapper exits
1 because Windows cp1252 cannot print Node's Unicode checkmarks **after** the
underlying tests passed and their JSON/log records were written. This wrapper
failure is retained in final accounting; setting `PYTHONIOENCODING=utf-8` and
using the fresh `node-tests-utf8` label succeeds. The earlier original-output
reuse rejection is also retained as an expected protective failure. No failed
quality result, inference attempt, or engineering failure was erased.

Changed implementation: `src/toruk_lm/rank_budget.py`; experiment and audit
drivers: `scripts/rank_budget_study.py`, `scripts/report_rank_budget.py`,
`scripts/compare_recall_runs.py`; regression tests: `tests/test_rank_budget.py`
and `tests/test_compare_recall_runs.py`. Documentation updates README,
architecture, experiment registry, the original recall report, this report and
its preregistration. `.gitignore` excludes only the new local package-build
outputs. The two new artifact directories retain raw inference, seals, summaries,
review and command evidence; generated smoke checkpoints remain ignored.

See [final accounting](../../artifacts/rank-budget-v1-20261104/final-accounting.json)
for exact command argv/exits, changed paths and Git status. Work remains
uncommitted and no research capability or release gate is declared passed.

The subsequent [independent replication](independent-replication-v1-results.md)
reproduces this milestone's 96 rows exactly and confirms its failed criterion.
The frozen mechanism scores 9/24 versus lexical retrieval's 6/24 on separately
authored scenarios, with higher latency and model-token work. Both new
efficiency/quality gates fail. The original outputs and scores above are retained;
the new package is an exploratory tradeoff study, not an accepted quality fix.
