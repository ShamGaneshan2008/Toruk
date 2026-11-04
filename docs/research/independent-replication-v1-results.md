# Independent replication and research evidence — 4 November 2026

**The central efficiency/quality claim is not established.** The frozen Toruk
candidate improves the primary score on these small sets, but costs more than
simple lexical retrieval. Its independent correctness advantage has a paired
interval that includes zero. This is an exploratory tradeoff, not a verified
advantage or a submission-ready positive result.

Base commit: `84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`, branch `main`. The
starting tree was already dirty with the previous rank-budget milestone: five
modified tracked files, eight new code/doc files and two evidence directories.
That work was preserved. Initial status and environment are retained in
`artifacts/independent-replication-20261104/start.json` and `environment.json`.
No commit, push, deployment, paid API call or new research training was performed.

## Phase 1 evidence gate

README, architecture, previous protocols, raw outputs, scorer, checkpoint metadata
and final report were inspected. The previous package's **126 sealed outputs**
verify. A fresh run of the original rank-budget driver reproduces **96/96**
development/heldout rows exactly: actual prompt IDs, answers, frozen scores,
selected evidence/hashes, retention flags and deterministic work counters.
The unchanged tokenizer-only reporter also passes. Timing/RSS are not equality
requirements. See the [fresh comparison](../../artifacts/independent-replication-20261104/phase1/comparison.json).

The previous criterion remains **failed**: its heldout candidate has 8/12 correct,
but 3/12 unsupported proxy exceeds the registered maximum of 2/12. It was not
treated as an accepted quality fix. The new controlled run additionally preserves
36/36 main-method prompts/answers from this replay, and restoring the cutoff
matches all 12 previous-envelope outputs. Instrumentation did not change answers.

Actual backbone/tokenizer/runtime and selector files are hash-bound before
independent data construction. Backbone: Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, weight SHA256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
Selector SHA256: `abd9d2d1c20edb3ad5cf3282f8a26fca49fb44d508d4ba2ada5ebc9c666b7548`.
Its historical data seeds are 711/991/1423; fitting seed 173. Recall V2 is
deterministic enumeration. New independent assembly seed: **20261104**.

The mechanism freeze predates scenario-card construction. A later complete
registration seals datasets, code, protocol, old scoring function, runtime
dependencies, model/tokenizer files and balanced method order before inference.
Dependency versions and file hashes are rechecked at evaluation/audit time.

## Separate evaluation sets and fixed comparisons

The controlled set contains 12 already published V2 cases with 18 weather-gap
pairs. It is a replication/ablation set, not fresh generalization evidence.
The independent set consists of **24 newly hand-authored operational scenario
cards** assembled by a different seeded procedure, with heterogeneous distractors
and varying early event positions: 47–57 messages and 19–25 trailing distraction
pairs. There are four cases each for distant facts, corrections, preservation,
exact strings, vague references and insufficient evidence. Two facts originate
from assistant turns. There are no independent gist questions, so dataset
aggregates must not be pooled.

The leakage audit finds zero exact normalized task-text overlaps with historical
selector train/dev/final and recall V1/V2 data. This is not proof of semantic
template or pretraining disjointness. The same assistant authored and reviewed
the scenarios after learning earlier failure modes; “independent” describes
the dataset procedure, not independent investigators or human adjudication.

All methods share local CPU float32 Qwen, two Torch threads, the same system
instructions, temperature 0/top-p 1, 512 prompt tokens and 48 generated tokens.
No thresholds or mechanism code changed after freezing. Method order rotates
by case and is balanced across both sets. Source limits and input limits remain
the original ones. Full history tokenization/selector work is counted.

| Set / method | Correct | Unsupported proxy | Prompt / output tokens | Request s | CPU s |
|---|---:|---:|---:|---:|---:|
| Controlled / recent | 0/12 | 2 | 5,886 /167 | 59.07 | 118.20 |
| Controlled / lexical retrieval | 4/12 | 2 | 2,152 /207 | 40.21 | 80.00 |
| Controlled / Toruk | 8/12 | 3 | 2,931 /193 | 43.84 | 86.91 |
| Independent / recent | 3/24 | 3 | 12,136 /450 | 134.92 | 269.73 |
| Independent / lexical retrieval | 6/24 | 9 | 4,293 /204 | 52.92 | 105.53 |
| Independent / Toruk | 9/24 | 8 | 5,783 /204 | 63.33 | 126.34 |

Primary scores use the **unchanged narrow lexical rubric**, not independent
semantic ground truth. Known distant-fact correctness is 8/10 versus lexical
4/10 on controlled and 9/18 versus 6/18 independently. All-marked-source retention
is 9/10 versus 5/10 and 12/18 versus 11/18 respectively. Marked-source retention
is conservative: it can require unrelated facts that the question does not need.

The [complete generated table](../../artifacts/independent-replication-20261104/evaluation/table.md),
[summary/intervals/ablations](../../artifacts/independent-replication-20261104/evaluation/summary.json),
[independent raw answers](../../artifacts/independent-replication-20261104/evaluation/independent.jsonl),
and [controlled raw answers](../../artifacts/independent-replication-20261104/evaluation/controlled.jsonl)
retain every outcome. The tokenizer-only audit passes **216/216** prompts,
selected source bytes/hashes, generated-token decoding, scores and token counters.

## Actual-component ablations

| Variant | Controlled correct /12 | Independent correct /24 | Independent unsupported proxy | Independent request s | Independent prompt / output tokens |
|---|---:|---:|---:|---:|---:|
| Full Toruk | 8 | 9 | 8 | 63.33 | 5,783 /204 |
| Remove envelope | 7 | 9 | 8 | 56.48 | 4,247 /230 |
| Remove learned ranking | 0 | 1 | 5 | 120.81 | 5,886 /698 |
| Remove cutoff relaxation: restore 0.2 | 4 | 8 | 8 | 71.62 | 5,362 /300 |

Removing the envelope preserves the top-two learned selection and changes only
its existing rendering/instruction bundle. On independent cases the envelope
adds two passes (bread topping and duffel colour) but loses two (latch copying
and the crate-serial refusal rubric), giving **no aggregate gain** while adding
6.85 request seconds and 1,536 prompt tokens. These are real regressions, not
excluded cases. Controlled envelope gain is one gist answer.

Removing learned ranking replaces its scores with constants while preserving
candidate eligibility, top-two capacity, recency retention and the envelope.
The resulting recent eligible-turn tie-breaking loses most distant facts; this
does not establish learned superiority over lexical retrieval. Restoring the
cutoff changes only the prior relaxation choice. The full candidate gains one
independent pronoun answer, while its original controlled stale-correction
regression remains visible. No recurrent writer, summary store or fact editor
is fabricated for these ablations.

## Uncertainty, criterion and assertions

Independent accuracy Wilson 95% intervals: Toruk **21.2–57.3%**, lexical
**12.0–44.9%**. Paired bootstrap quality difference is **−4.2 to +29.2 percentage
points**, so a positive correctness advantage is inconclusive. Paired latency
“saving” interval is **−37.2% to −1.6%**, favoring lexical retrieval on this
host/sample. Controlled quality difference is **0 to +66.7 points**, and its
latency-saving interval is **−44.7% to +11.1%**. Intervals use 10,000 paired
scenario resamples, seed 741; the authored cases are not a random population
sample, and no training-seed/hardware uncertainty is measured.

The registered efficiency/quality gate **fails on both sets**. Independent
correctness and unsupported-proxy conditions pass, but request latency and model
tokens are higher and the positive-interval condition fails. Controlled also
fails the unsupported-proxy condition. A better ratio of cost per correct
answer does not satisfy the requirement for lower absolute request cost.

An exhaustive, method-label-omitted review of **151 unique answers** covers all
216 outputs. It is a **posthoc assistant review**, not independent human grading,
and focuses on answer bindings/identifiable added policy assertions; generic
refusal commentary is not a complete semantic audit. Flags by method are:

| Set | Recent | Lexical | Toruk | No envelope | No learned ranking | Restore cutoff |
|---|---:|---:|---:|---:|---:|---:|
| Controlled, flagged answer assertions /12 | 7 | 7 | 2 | 4 | 10 | 4 |
| Independent, flagged answer assertions /24 | 11 | 11 | 5 | 9 | 11 | 6 |

All source-ledger comparisons and rationales are retained in
[assertion-review.json](../../artifacts/independent-replication-20261104/evaluation/assertion-review.json).
Exact-format errors, abstention, true but irrelevant statements and unsupported
assertions are recorded separately. The frozen proxy and this subjective review
are not interchangeable: e.g. explicit “serial number was not logged” fails the
old uncertainty matcher, while several wrong exact-value answers do not trigger
its unsupported proxy. No primary score or gate was repaired after inference.

## Failure examples and attribution

Independent Toruk has 15 primary failures: five lost-marked-evidence diagnoses
and ten generation-despite-evidence diagnoses. The latter include actual model
errors and rubric false negatives. The former can include unrelated marked
sources, so the counts are observable diagnostics rather than complete causes.

| Case | Source/required behavior | Toruk output | Interpretation |
|---|---|---|---|
| Studio contact | Assistant recorded `Liora Venn` | `The Copper-Print Studio` | Assistant-origin source cannot enter older-user-turn ranking; missing evidence |
| Archive bin | `R-6` explicitly corrected to `T-2` | `R-6` | Both source turns retained; stale correction |
| Rehearsal date | `2045-08-16` moved to `2045-08-23` | `2045-08-16` | Both source turns retained; stale correction |
| Tram platform | Platform 9; number-only answer required | `platform 9` | Fact recognizable; frozen exact-output failure |
| Bell engraving | `Hold!  then listen.` | `"Hold! Then listen."` | Source retained; quotes, spacing and case changed |
| Ambiguous spare key | Two lockers, different key locations | `The spare key is in the copper bowl.` | Candidate guessing despite both sources |
| Missing serial | Serial explicitly unlogged | `According to the conversation, the equipment crate's serial number was not logged.` | Honest absence report; frozen uncertainty matcher fails |

Both assistant-origin cases fail for every method. Toruk's older candidate
filter explicitly considers only user turns. No compression corruption is
observed: selected raw text remains intact in actual decoded prompts; decoder
copying/interpretation failures are separate. See the complete
[Toruk failure rows](../../artifacts/independent-replication-20261104/evaluation/toruk-failures.json).

## Full-history token and compute accounting

| Independent metric, 24 requests | Recent | Lexical | Toruk |
|---|---:|---:|---:|
| Full-history tokenization positions | 22,626 | 22,626 | 27,976 |
| Fit tokenization positions / attempts | 252,126 /346 | 4,293 /24 | 5,783 /24 |
| Model prompt + output tokens | 12,586 | 4,497 | 5,987 |
| Logical selector scan bytes | 0 | 59,593 | 59,593 |
| Actual selector ms | 0 | 3.488 | 11.017 |
| Actual history-tokenization ms | 99.75 | 72.92 | 75.64 |
| Actual fitting ms | 722.32 | 16.77 | 19.92 |
| Model generation ms | 134,090 | 52,822 | 63,222 |
| Total request CPU seconds | 269.73 | 105.53 | 126.34 |
| Maximum selected source bytes | 2,707 | 350 | 354 |

Toruk's independent prompt-plus-output work is **33.1% higher** and request
latency **19.7% higher** than lexical. Controlled model-token work is **32.4%
higher**, latency **9.0% higher**. Zero recent selector scan excludes its full
history tokenization and repeated fitting. Logical scan bytes do not count every
internal validation/regex/encoding pass. The source envelope increases rendered
full-history tokens even before selection. Request CPU time covers all threads;
two Torch threads explain CPU seconds near twice wall seconds.

Independent process peak is **2,468,274,176 bytes**; controlled peak is
**2,469,486,592 bytes** (about 2.30 GiB each). These are cumulative OS process
high-water marks dominated by the shared backbone/framework, not per-method
allocations or demonstrated memory savings. Source-content bytes exclude model,
tokenizer and Python object/envelope overhead. There is no persistent memory.

New independent/controlled evaluation-loop wall times are **500.14/275.76 s**;
startup is **7.23/7.42 s**; complete subprocess times are **510.15/285.96 s**.
The Phase 1 development/heldout subprocesses took **164.09/157.47 s**. Across
the four inference commands: **312 answers, 81,846 model prompt tokens, 4,861
output tokens and 1,117.67 subprocess seconds**. Phase 2 request CPU time sums
to **1,546.80 s**; the historical Phase 1 driver did not measure CPU time.
Distinct evaluation units are 24 independent and 12 controlled scenarios;
repeated answers must not be treated as 312 independent samples.

The [total accounting](../../artifacts/independent-replication-20261104/total-cost-accounting.json)
keeps scope boundaries explicit. Checkpoint startup, token-only audit, bootstrap,
logging and engineering commands add separately recorded work. Historical
selector/Qwen training cost, exact FLOPs, energy and electricity price are
unmeasured. New research training and paid API calls are zero; bounded CPU
verification smokes train separately and make no factual-quality claim.
Neither short prompts nor this partial lifecycle accounting establish a lower
total-resource advantage.

## Paper package, claims and reproducibility

The local [draft](independent-replication-v1/draft.md) contains the problem,
falsifiable hypothesis, implemented Mermaid architecture, datasets, leakage
controls, measured results links and limitations. The [claim ledger](independent-replication-v1/claim-ledger.md)
links every empirical/method claim to code, protocol, raw artifact or primary
source, explicitly marking unsupported claims. The
[positioning matrix](independent-replication-v1/positioning.md) and bibliography
cover selected primary work through August 2026, including RMT, Memorizing
Transformers, LongMem, ReadAgent, LLMLingua-2, LongMemEval, Mem0, SimpleMem,
LongMemEval-V2 and EARM. Their reported costs are not matched Toruk experiments.
No first-of-kind, IEEE Xplore absence, general memory or strong-compressor
superiority claim is made.

[PowerShell and CI reproduction instructions](independent-replication-v1/reproduce.md)
describe a fresh Phase 1 replay, independent/controlled inference, token-only
audit and reporting. The overlay archive includes code/config/docs/raw evidence
and small backbone support files, but excludes pretrained weights and generated
training checkpoints. It targets the stated base checkout; it is not a published
release or a model redistribution.

## Verification and failures retained

All **20** local Python CI-equivalent commands pass, including the new
`independent_replication.py validate-cases` command. Full pytest: **204 passed,
zero skips, 132.96 s**. Full Ruff lint and formatting pass (111 Python files);
strict runtime mypy passes on Windows and Linux (30 files each); three research
scripts pass with the existing psutil/class-substitution suppressions. Node
syntax passes; Node tests have **13 passes and one optional live-test skip**.
Ordinary/recurrent CLI smoke, resume, dependency/import/config/artifact checks,
package build and whitespace checks pass. No live browser was run.

GitHub Actions and the repository verification script now cover independent
case/oracle/bounds validation without downloading weights. Actual pinned-model
inference is **not** covered by hosted CI. No hosted run for this uncommitted
work was launched or observed; hosted status is **NOT_RUN**.

Initial failures remain in the command ledger: four lint findings, a new test
fixture that accidentally removed the terminal user question before testing the
short-gap check, one missing type annotation, and a posthoc review-preparation
encoding error caused by an implicit Windows text decoder. The fixes occurred
before live inference except the last, which corrected only UTF-8 review input;
raw answers/scoring/mechanism were unchanged. The original incorrectly decoded
review input remains retained beside the explicit-UTF-8 replacement. An ad-hoc
summary inspection also hit a Python syntax error; it had no artifact/inference
effect. The initial package build passed with an unmatched optional JSON glob
warning before the final claim-ledger JSON existed. Final build/overlay checks
and exact command argv/exits are recorded in final accounting.

The single most important remaining submission step is **external replication
with independent human adjudication on a real conversational benchmark**, using
the frozen mechanism, fair stronger baselines and the same full-history cost
accounting. This local package supports inspection of an exploratory result;
it does not justify a paper claiming a verified broad advantage.
