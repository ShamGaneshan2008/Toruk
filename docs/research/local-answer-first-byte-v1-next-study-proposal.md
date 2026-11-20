# First-byte margin/parity probe v1 — bounded proposal, not executed

20 November 2026. One proposed development-only diagnostic study. **Zero training
or optimizer updates, zero new examples, no curriculum fit, no development or
held-out inputs, no multi-token answer regeneration.** Current work only reads
saved evidence; the inference below requires a new registration before execution.

## Question and fixed inputs

Does ordinary947's omitted `m` reflect reproducible first-token score/rank error,
a near tie, or numerical disagreement between prefix and teacher-forced paths?
The answer informs whether a later paired curriculum is worth testing; it does
not itself establish a curriculum benefit or architecture advantage.

Use ONLY the32 city TRAINING prefixes and corresponding saved labels from
local-answer-dev-v1, in original file order, with the four existing final
checkpoints: ordinary601, recurrent601, recurrent947, ordinary947. No new prompt,
value, template, position, seed, checkpoint selection or decoding rule. Model
widths/configuration, byte tokenizer, float32 deterministic CPU/one thread and
runtime must match v1. Evaluation mode/no_grad only; no backward, optimizer
construction or updates.

Before any inference, freeze exact32 IDs/full native inputs, all four checkpoint
hashes, source/runtime identities, logger, numerical comparisons, order and caps
in a NEW registration/artifact directory. Keep v1 bytes and scores immutable.
Require an exclusive run marker. Verify no parameter/RNG state is changed by
probing. No fallback to weighted supervision or additional checkpoints.

## Fixed measurements

For each checkpoint, first consume BOS+prefix through the original continuous
segment schedule and save the first-answer259-logit vector BEFORE selection,
native IDs, local position, PAD/BOS suppression list and argmax. Stop there:
do not feed that predicted token back or generate a continuation. Save all32
rows, then replay the first once and require equal native inputs/logits/argmax.
This phase receives prefixes only; seal its raw rows before opening gold labels.

Then, separately teacher-force each full saved training document with the same
checkpoint and record its first-answer259-logit vector, target ID, mask position,
and per-answer-byte/EOS CE. Evaluate gold rank, raw-vocabulary and eligible-ID
probabilities, winning margin, and ties only from the saved vectors. Preserve
raw finite logits; represent suppression as ID metadata, not invented finite
scores. Gold rank is1-based among eligible IDs2..258. Raw probabilities normalize
over all259 IDs; eligible probabilities normalize over IDs2..258. Tie-breaking
must match torch argmax's lowest-index selection.

Total132 prefix paths (128 cases +4 replays) and128 teacher-forced paths =260
fixed measurement rows. These are new inference measurements, explicitly not
claimed as saved v1 evidence. There are no free-form answers or accuracy rescoring.

## Caps and fixed stopping rules

- Eight cold workers: four prefix and four teacher-forced, <=20 CPU AND wall
  seconds each; <=2 CPU/wall seconds per case. Freeze/contracts/controller
  combined<=40 seconds; whole workload Job<=200 CPU AND wall seconds.
- Job memory2GiB, disk128MiB,50ms observation, maximum gap5 seconds. Use tested
  Windows Job lifetime accounting; record outer observer separately. Retain all
  rows, errors, costs and partial stages. No cap increases, retry or repair.
- Stop immediately on source/checkpoint/input/mask mismatch, nonfinite values,
  parameter/RNG mutation, incomplete Job closure, or any resource violation.
- Every prefix argmax must reproduce its original saved first ID; every replay
  must match. Otherwise STOP_REPRODUCTION_FAILURE and do not interpret curriculum.
- Compare teacher versus prefix vectors with maximum absolute difference<=1e-5,
  AND require the same eligible argmax even inside tolerance. Any violation is
  STOP_NUMERICAL_PARITY_FAILURE; investigate evaluation before proposing training.
- For a wrong prediction, tag winner-minus-gold logit margin<=1e-4 as near-tied
  gold; also record winner-minus-runner-up<=1e-4 for EVERY case. A passing gold's
  zero winner-minus-gold margin is not a near-tie indicator. Report all ranks and
  margins without changing thresholds or selecting cases. Near ties limit a
  confidence-collapse claim.
- If all rows reproduce with numerical parity, stop after260 rows and report
  the observed rank/margin pattern. Persistent gold rank>1 in the16 failures
  supports a first-byte distribution error; it still does not identify whether
  initialization, ordering or mixed-task competition caused it.

No outcome authorizes a curriculum fit, more examples/steps, development test or
memory comparison within this proposal. In particular, a parity failure would
falsify a purely training-discrimination account for the affected cases; correct
parity would leave the pairing/density hypothesis unproven. A later training
intervention would need its own matched-exposure controls and registration.
