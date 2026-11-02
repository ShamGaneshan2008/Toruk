# Context selection milestone protocol v1

Written before final evaluation. Development: `configs/context-eval-dev-v1.json`
(six cases); final: `configs/context-eval-final-v1.json` (12 cases, two per category).
Only synthetic conversations. Final answers must not guide changes to the selector,
questions, scoring, model, prompt or decoding. Templates and distractors are shared;
values and entities differ. This is a small held-out-instance test, not independent
language generalization. Dataset hashes are retained in every raw result.

Use the installed, hash-checked Qwen2.5-0.5B-Instruct at revision
`7ae557604adf67be50417f59c2c2f167def9a775`, CPU float32, two Torch threads,
512 prompt tokens including the existing conversation instructions, 32 generated
tokens, temperature 0, top-p 1. Keep the pinned generation config (including its
repetition penalty 1.1). No training or backbone/prompt tuning in this milestone.
Both modes use identical tokenizer, system instructions and output limits.

BASELINE uses the existing chronological recent-turn fitting algorithm.
TORUK uses an explicitly configured **heuristic**, not the absent learned M6 model:
`lexical-v1` retains the latest three messages plus two older user messages ranked
by query term overlap, with recent-message tie breaking. The first development run
lost the terse correction and returned the stale day. It also guessed the correct
multi-hop answer with an incomplete evidence chain. BASELINE itself failed the
terse correction, even though it retained it.

Make exactly one focused improvement: `lexical-v2` groups selected older user facts
with immediately following explicitly marked correction turns. Retain at most two
additional correction messages. No reconstruction, fact substitution, label access,
embedding model, checkpoint replacement or cross-request state. Preserve v1 for the
matched before/after evaluation. Do not add a second change based on final outputs.

Run development again with v2. Freeze source before running final, then evaluate
both selectors once on the unchanged final fixture, each paired with BASELINE.
The baseline is repeated to detect drift; answers and input token counts should be
identical across runs. Warm up once per mode with fixed unscored input. Shuffle
mode order per question with seed 23. Requests go through a real local Node proxy
and authenticated inference worker. Never run scored v1/v2 evaluations concurrently.

Correctness: case-insensitive word-boundary match of any accepted phrase and no
forbidden phrase. This fixed content rubric does not enforce requested output
format. Unsupported flag: incorrect non-abstaining answer, using the evaluator's
fixed uncertainty regex. These are automatic error flags, not a complete semantic
hallucination detector. Inspect every raw final answer for false positives and
additional unsupported assertions; record that audit separately without changing
the frozen score. Evidence support is reported independently: all required source
message IDs must survive actual prompt fitting. A correct answer with missing
required evidence is not evidence of successful retrieval. Empty evidence lists
for general-knowledge/unknown questions count vacuously; report grounded categories
separately when interpreting support.

Record full available formatted history tokens, actual formatted prompt tokens,
generated token count (including stop tokens), selected message/evidence IDs,
required evidence coverage, model/backend time and caller end-to-end HTTP latency.
End-to-end latency includes selection, tokenization, fitting, model generation and
proxy/HTTP overhead; excludes service startup. All older messages are scanned by
the heuristic: reduced backbone prompt tokens do not mean fewer total tokens read.
No warmed latency result is a cold-start, throughput or concurrency claim.

Store immutable raw requests, selected verbatim messages, answers, scores, dataset
hash, model/revision/weight hash, tokenizer/config hashes and contents, package
versions, Git HEAD and source-file hash map. Capture pre-v2 source identity in the
initial development artifact. Final comparison uses both selectors from the same
frozen code snapshot. Fresh output directories only; retain partial failures.

Numeric target: at least 35% aggregate reduction in actual backbone input tokens
with no lower answer accuracy, no more unsupported flags, and no request failures.
Report mean/median selected tokens and HTTP latency, per-category scores, evidence
coverage and before/after regressions. A result on these 12 highly related cases
cannot establish broad superiority or research-paper credibility. If fewer than
70% of BASELINE answers are correct, quality preservation is especially weak
evidence even if the numeric token target passes. No public deployment in this task.
