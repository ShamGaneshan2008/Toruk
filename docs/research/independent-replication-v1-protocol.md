# Independent replication protocol v1 — 4 November 2026

Starting commit `84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`; the previous
rank-budget milestone is present as uncommitted work and must be preserved.
First verify its seals and freshly reproduce all 96 development/heldout answers,
prompts, scores and deterministic work counters using its original driver.
Failure of that gate stops the study before paper drafting. Record the previous
criterion unchanged: it failed its unsupported-answer proxy threshold.

The mechanism is frozen in `artifacts/independent-replication-20261104/mechanism-freeze.json`
before independent case construction. All runtime modules, actual backbone,
tokenizer and learned selector bytes are bound. No training, new threshold,
prompt tuning or answer-driven mechanism edits are permitted. This is an
independent *dataset procedure*, not independent investigators or adjudicators.

## Second evaluation set

Author 24 operational scenario cards from scratch, with four cases each for
distant facts, corrections, preservation, exact strings, vague references and
insufficient evidence. Cards describe field stations, workshops, travel and
household logistics rather than project access codes and repeated weather.
Each card specifies chronological events, a question, oracle answer/concepts,
obsolete or competing values and source indices. Include both user-origin and
assistant-origin facts. Vague cases split clear and genuinely ambiguous references.
Question and fact templates are not copied from the original controlled generator.

Use a separate seeded assembly procedure (`20261104`) to sample heterogeneous
distractors and insert event cards at varying early positions, with at least
18 subsequent distraction pairs before each final question. Preserve event
order. No fact is changed by distractor generation. Seal all cases, source cards,
code, protocol, rubric, method order and actual model dependencies before any
independent inference. Compare exact task-bearing text with historical selector
training/development/final data and controlled V1/V2 cases. No fit uses these data.
This is authored synthetic data, not a real-world population sample or an
external benchmark. Shared language and latent pretraining leakage cannot be ruled out.

Run 24 independent cases once. Also run all six methods on the 12 published
controlled heldout cases, using the same instrumentation and balanced order.
Keep independent and controlled results separate. No retries for bad answers.
An interrupted run must remain visible and cannot be silently replaced.

## Comparisons and actual-component ablations

All comparisons use local Qwen2.5-0.5B-Instruct, CPU float32, two Torch threads,
the identical system instructions, greedy temperature 0/top-p 1, 512 prompt
tokens and 48 output tokens. Raw input limits are 64 messages/16 KiB. Toruk's
selected-source limits remain eight turns/4 KiB; no per-method extra model.

1. `recent`: existing recent-context fitting without a selector.
2. `lexical`: unchanged deterministic lexical-v1 retrieval (simple baseline).
3. `toruk`: frozen RankBudgetEnvelopeSelector.
4. `no_envelope`: same RankBudgetSelector, ordinary role-turn rendering.
5. `no_learned_rank`: same top-two capacity, recent-three retention and envelope,
   with constant scores replacing the learned scorer; existing tie-breaking
   retains recent eligible turns. This removes learned/query ranking, not storage.
6. `restore_cutoff`: unchanged SourceSpanSelector with the old learned 0.2 cutoff;
   same envelope. This removes the prior cutoff-relaxation intervention.

Do not invent recurrent memory, fact editing, summary writing or other components
in the conversational path. The separate integrated decoder prototypes are not
the system evaluated here. Lexical retrieval is the simple baseline; this study
does not claim to implement or benchmark a learned compressor.

Rotate method order deterministically per question, balanced over 24 cases.
Record warm model initialization and full subprocess wall time separately.

## Scoring and falsifiable claim

Keep the previous `recall_study.score` bytes unchanged on both datasets.
Each new card maps to its existing exact/gist/clear/ambiguous/missing task schema.
Exact answer scoring preserves case, punctuation and internal whitespace; only
outer whitespace is stripped. Retain the known narrow uncertainty matcher and
its false negatives. Never repair a score using evaluation responses.

Report raw answers and an additional exhaustive posthoc assistant assertion
review, with rule/rationale per answer and explicit non-independent status.
An asserted answer binding must follow the source ledger and its latest
corrections. Mere refusal/generic advice and exact formatting deviations are
separate. The automatic unsupported field remains a proxy, not full semantic
ground truth. Review does not replace primary scores. Submission-quality
adjudication requires external reviewers and is outside this study.

The central claim is supported in this bounded independent sample only if Toruk
has at least the lexical baseline's correctness, no more primary unsupported
answers, and strictly fewer full-request milliseconds AND model prompt+output
tokens, without omitting selection/tokenization work. Require a strictly positive
paired 95% bootstrap interval for correctness gain or latency saving before any
confirmatory superiority wording. Compute paired intervals over scenarios using
10,000 resamples, seed 741. Report descriptive Wilson intervals for accuracy.
Tiny nonrandom authored scenarios limit every interval's population interpretation.
Energy/FLOPs/monetary and historical training costs are unmeasured: do not claim
they decreased. The same criterion is descriptive on the already published
controlled set, which cannot supply fresh generalization evidence.

## Accounting and integrity

Retain each question's full history, selected indices before/after 512-token
fitting, actual prompt IDs, selected source hashes, raw answer, frozen scores,
source retention, preprocessing and generation timing, input/fitting/prefill/output
token work, logical scan bytes, source bytes and process RSS/high-water peak.
Instrument actual requests, with diagnostic reconstruction outside request time.
Full subprocess logs include startup; offline scoring/analysis is separate.
Process high water is cumulative, not per-method allocation. Source text bounds
exclude model/framework/Python object overhead. State which values are measured
directly and which are proxies. Never equate tokenizer positions with FLOPs.

Refuse changed inputs and existing outputs. Audit exact source text against
original histories and prompts, recompute scores and counters, and seal final
artifacts. CI must exercise dataset validation and integrity without downloading
weights; live reproduction requires explicitly supplied local pinned weights.
Run the repository verification script and relevant Node tests. No hosted CI,
paid training, publication, commit, push or deployment is launched.
