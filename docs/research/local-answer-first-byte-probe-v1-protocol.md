# Local-answer first-byte margin/parity probe v1: registration

21 November 2026. Development-only inference measurement, implementing the
[reviewed proposal](local-answer-first-byte-v1-next-study-proposal.md) preserved
in commit `743c29ff1b1dc5c86b81de48888a4753860ef0f8`. No training, backward pass,
optimizer construction/update, new example, generated answer, curriculum change,
scorer change, production change, held-out access or push. Prior scores/gates
remain immutable. Only first-prefix scores and teacher-forced scores are measured.

## Freeze before every first forward

One exclusive bootstrap marker, zero-forward contract tests, then registration
and an exclusive run marker precede ALL model forwards. The registration freezes
this protocol, sources/snapshots, exact32 city TRAINING cases from local-answer-
dev-v1 in original order, native IDs/positions, gold byte/token IDs, all four
checkpoint hashes/configurations/runtime, original first IDs,260-record plan,
measurements, order and caps. It is written and its SHA printed before the first
worker. No registration or worker retry; retain partial evidence on every stop.

The existing local-answer registration is
`c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4`.
Only its training inputs/labels/documents, raw training continuations, checkpoint
metadata and saved weights are read. No development/held-out data is read by the
probe. No new prompt/value/template is constructed. Its32 city cases all have
prefix53 bytes, native prefix54 IDs including BOS, delimiter `?=` IDs66,64,
first-answer target y53/native gold index54/local causal-logit position21,
and answer mask y53..55. Verify byte-for-byte against original native inputs.

Cell order: ordinary601, recurrent601, recurrent947, ordinary947. Complete all
four prefix workers BEFORE any teacher worker, then teacher workers in that same
order. Prefix workers receive only prefixes and saved original first IDs; they
never open the gold file. Seal132 raw prefix vectors and selections before gold
is read for teacher forcing/evaluation. Teacher phase uses exactly the saved full
training document and original target shift, masks, local segments and entering
state schedule. Verify all native document/target IDs against the frozen plan.

## Models and exactly260 primary records

Load only the four existing final1536-step checkpoints with strict hash/cell/
configuration/progress checks; no checkpoint selection. Existing Toruk ordinary
matched14,058 parameters and recurrent14,416 parameters, context32, same byte
tokenizer and source/runtime as v1. CPU float32, one Torch thread, deterministic
algorithms, eval/no_grad. Construction and strict saved-state loading occur only
after registration. Snapshot model tensor and Python/Torch RNG hashes after load
and require exact equality after each worker. Never call generate or feed a
measured argmax back into a session.

Each prefix worker consumes BOS+prefix with original OwnedSession.consume once
per case, saving the first259 finite raw logits BEFORE argmax selection;32 cases
plus first-case replay =33 vectors. Selection is a separate sidecar. Each teacher
worker scores32 saved complete documents once, saving the first259 logits and
per-answer-byte/EOS CE. Primary vectors132+128=260; sidecars/derived annotations
are not extra inference records. Replay requires bit-equal native IDs/logits and
argmax, excluding times. Source/invariant/cap failures stop without retries.

Preserve finite logits as raw numbers, PAD/BOS suppression as `[0,1]` metadata.
Any nonfinite result is retained with its nonfinite values explicitly encoded
before STOP, never normalized into a valid result. No answer vocabulary filter,
forced EOS, sampling, trimming, extraction or relaxed acceptance.

For EACH of260 records, derive from saved vectors after prefix sealing: gold ID,
predicted ID,1-based expected-token rank among eligible IDs2..258 (descending
logit, lower ID breaks ties), gold/predicted logit, expected-minus-predicted and
predicted-minus-expected margins, raw probabilities over259 IDs, eligible
probabilities over257 IDs, runner-up margin and tie counts. Expected byte comes
from the frozen label, not a replacement model output. No v1 accuracy rescoring.

## Fixed stop rules and interpretation

1. Any checkpoint/source/runtime/input/native target/mask/position mismatch,
   nonfinite output, model/RNG mutation or incomplete lifetime accounting stops.
2. Every prefix argmax must equal its original saved first ID. Otherwise
   STOP_REPRODUCTION_FAILURE. Every first-case replay must match exactly.
3. Teacher/prefix vectors must have max absolute difference<=1e-5 AND the same
   eligible argmax, even inside tolerance. Otherwise STOP_NUMERICAL_PARITY_FAILURE.
4. For wrong gold, winner-minus-gold<=1e-4 flags near-tied gold. Independently,
   winner-minus-runner-up<=1e-4 flags a near-tied decision in any case. A correct
   gold's zero winner-minus-gold is not itself a near tie. No threshold tuning.
5. If all260 rows reproduce and pass parity, report rank/margin differences for
   all32 cases and the16 prior failures against all three passing checkpoints.
   Gold rank>1 with a stable losing margin explains the immediate first-token
   decision. It does not establish why training produced those weights or that
   pairing/a curriculum would repair them. No outcome authorizes training,
   development evaluation or a memory comparison in this registration.

## Complete accounting and immutable caps

The OUTER Windows Job contains bootstrap/contracts, controller, eight workers
and inner observers. Complete kernel user+system CPU<=200 seconds AND wall<=200;
Job committed memory2GiB, logical run disk128MiB, poll50ms, max gap5s. Each cold
prefix/teacher worker<=20 CPU AND wall; each case<=2 CPU/wall. Contracts, freeze
and controller combined<=40 CPU/wall, enforced during execution and reconciled
as outer lifetime totals minus the eight worker-job subsets. No cap increases.
The outermost observer is outside the Job; report its CPU-to-receipt separately,
not as a complete observer/project lifetime. Nested jobs are subsets, not added
to the complete outer total. Controllers also emit finally status receipts.

Cold setup, hash checks, saved-state loading, model teardown, vector I/O and
analysis are charged within the workload. All commands, raw vectors, selection/
cost/invariant records, seals, failures and completed process costs survive.
An external hard-kill of the outer measurement observer cannot create a valid
final receipt; it must not be described as a completed run. Final repeatable
audits perform no forward passes. Leave new probe work uncommitted.
