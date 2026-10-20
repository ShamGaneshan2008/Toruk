# Controlled-world prerequisite v1

Introduced during the M6 prerequisite work on 2026-10-20. This extends the package
with its first controlled-world benchmark; the older prose fixture is preserved.
This is M2 prerequisite work, not an M6 comparison or verified M5 foundation.

The generator assigns world/document/split identity before generating events or
probes. Training uses two rendering templates and 1/2 corrections; validation
uses a third template and 3 corrections; final test uses a fourth and 4 corrections.
Entity identifiers are disjoint across splits. Attribute types are shared; whole
attribute vocabularies are not held out. Split shifts are deliberately bundled:
their effects cannot be attributed individually. A later generalization study
needs factorial controls. All three splits are generated/fingerprinted; the
model pilot opens only training/validation. There is no test-scoring CLI yet.

SET/FIX visibly identify authoritative facts. CLAIM/QUOTE/IF/DENY explicitly do
not update records under the displayed task legend. CONFLICT explicitly marks
an attribute uncertain; its answer becomes `?` until resolved by a later FIX/SET.
This tests a specified symbolic convention, not real-world source credibility.
The forward simulator and independently implemented backwards-query oracle must
agree. Evaluation rechecks labels and rendering against events, rejects changed
data hashes and split misuse, and never passes event records/labels to inference.

Six queries cover a repeatedly corrected color, unchanged name of that entity,
another entity's date and number, an unknown attribute and an ambiguous color.
Distractors and obsolete quotations/hypotheticals are explicit. Runtime receives
only rendered observed history and the current question through ObservedPrompt.
Other questions, world tables, gold answers and future events are absent. Gold
answers enter ordinary teacher-forced training exports and offline scoring only.

Ordinary baseline: unchanged causal decoder, tokenizer, independent-window loss,
AdamW and CPU training CLI. Each training example is one world's observed history,
one question and its answer; there is no cross-question state. The ordinary model
has only its established context when generating. Baseline generation is greedy,
fixed maximum 16 tokens, EOS-stopping, scores the first newline-delimited line
without case/whitespace/value normalization. Date, number and name matching are
exact strings. Generation never gets gold answer tokens. Full output tokens and
timing remain in raw predictions even after a newline.

Primary prerequisite measurement: per-category exact generated-answer accuracy
on validation, with sample counts and nonempty/non-`?` answer coverage. Correct
`?` answers count as correct on unknown/ambiguous probes but as abstentions for
coverage. Invalid nonempty answers are attempted answers, not correct abstentions.
Teacher-forced text validation loss is separate. The standalone recipe below
(not run in this task) uses fixture seed 17, training seed 23, 8 worlds per split
and two profiling steps before an 80-step ordinary run,
default batch 4/context 64/width 32/layers 2/heads 4, one CPU thread. Commands use
the existing 120-second wrapper. No tuning on final test and no superiority claim.
Time, input tokenization, generated tokens and local context are separate from
state storage. This standalone evaluator does not instrument CPU peak memory.
The actual registered pilot used four worlds and 12 controlled-training steps,
and measured cumulative process peak separately; see `m6-validation-protocol.md`
and `m6-results.md`. The standalone recipe is not a claimed experiment result.

Required gate evidence: oracle/simulator checks; correction/non-authority/unknown
semantics; split/ID/template/pattern isolation; stale/forged artifact rejection;
runtime-input sentinel perturbations; exact scoring; and a real CLI generation,
training, reload, answer/scoring integration. Passing these establishes a small
controlled benchmark baseline only. M3–M5 still require their own implementation
and evidence before the requested M6 controlled comparisons can proceed.

Reproduction uses fresh output paths:

```powershell
python -m toruk_lm make-worlds --output artifacts/worlds-reproduction/data --worlds-per-split 8 --seed 17
python -m toruk_lm train --train artifacts/worlds-reproduction/data/train_lm.jsonl --validation artifacts/worlds-reproduction/data/validation_lm.jsonl --output artifacts/worlds-reproduction/profile --steps 2
python -m toruk_lm train --train artifacts/worlds-reproduction/data/train_lm.jsonl --validation artifacts/worlds-reproduction/data/validation_lm.jsonl --output artifacts/worlds-reproduction/train --steps 80
python -m toruk_lm evaluate-worlds --checkpoint artifacts/worlds-reproduction/train/checkpoint.pt --data artifacts/worlds-reproduction/data/validation.jsonl --output artifacts/worlds-reproduction/eval --max-new-tokens 16
```
