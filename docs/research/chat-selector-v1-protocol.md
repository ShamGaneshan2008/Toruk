# Toruk chat selector v1 protocol (frozen before final scoring)

## Scope and audit

The M6 checkpoint `479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`
is `toruk-controlled-v1`, recurrent, byte-tokenized, trained for synthetic
controlled-world QA (`objective=qa`, 12 steps, width 32, four slots). Its
cosine summaries were not supervised with chat relevance pairs. It remains
untouched and is not a trained semantic selector. V1 is a separate learned
turn ranker; it does not modify the conversational backbone.

## Data boundary and frozen setup

`scripts/build_chat_selector_data.py` generates three JSONL splits with seeds
1701/2301/4701 and distinct `Trainperson`, `Devperson`, and `Finalperson`
entities and disjoint city pools. Each contains correction, preservation,
distraction, long-recall, and unknown cases. Train has 40 cases per category;
development and final have 12 each. Every case has 19 messages, an evidence
ID set, expected answer (or unknown), and obsolete value for correction.
Earlier evidence is at `m0`, a correction at `m8`; distracting user and
assistant turns fill the intervening history. The generator source hash and
all split hashes are stored in `manifest.json`. Training reads train and dev
only; final JSONL is opened by the evaluator after checkpoint and threshold
are written. Final results never change labels, threshold, model, or scorer.

The v1 scorer uses eight fixed lexical/position features for each earlier
turn: question-term coverage, shared-term count, subject cue, two-term cue,
correction marker, relative position, user role, and length. A logistic
ranker is trained on evidence/not-evidence labels with class-weighted binary
cross entropy, Adam, seed 73, learning rate 0.03, 120 full-batch steps.
Development evidence F1 chooses a probability threshold from
`0.10,0.15,...,0.90`; ties choose the higher threshold. At inference it
scores all earlier user turns, retains the last three messages and at most
two older turns above threshold. Unknown cases may retain zero older turns.
It reads the whole supplied history and is bounded in *selected context*,
not in history-reading work. This is a lightweight lexical ranker, not a
semantic LM or persistent memory state.

The pinned backbone is locally installed Ollama `llama3.2:latest`, digest
`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
(3.2B Q4_K_M). BASELINE and TORUK use the same tokenizer/chat template,
temperature 0, top-p 1, at most 512 selected prompt tokens, and at most 32
generated tokens. The only mode difference is turn selection. All supplied
messages are retained in the raw request. Measure exact Ollama prompt and
output counts, selected message IDs, response time, selector scan bytes and
time, and total prompt-evaluation tokens from metering and generation calls.

## Scoring and decision rules

Known-answer quality requires the expected value in the answer, with the
obsolete correction value absent. Unknown quality requires an explicit
uncertainty phrase (`don't know`, `do not know`, `not supplied`, `not provided`,
`no information`, or `cannot determine`) and no fabricated key. Evidence
retention requires all labeled evidence IDs in selected IDs; unknown evidence
retention requires no older selected turn. Unsupported answers count unknown
cases without explicit uncertainty or with a fabricated answer. Errors count
as incorrect and are reported separately. Compare category scores, overall
quality, evidence retention, selected tokens, total prompt-processing tokens,
selector scan cost, and end-to-end latency.

Call answer-quality improvement only if TORUK exceeds BASELINE by at least
10 percentage points, clears 60% quality, retains at least 80% of labeled
evidence, and has no more unsupported unknown answers. Call token reduction
at preserved quality only if selected tokens fall at least 35%, BASELINE
clears 60% quality, TORUK quality is no lower, and unknown-answer failures do
not increase. Report all failures and cost even if these criteria fail.
The generated templates and lexical features may favor this ranker; success
here would not establish general conversational memory or semantic transfer.
