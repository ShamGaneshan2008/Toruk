# Paired city batches v1: one bounded training intervention proposal

22 November 2026. **Proposed only; no training or generation is authorized or
executed in this review.** This design changes city batch composition, with a
matched city-batch control. It does not add warmup, answer weighting, templates,
data, model capacity or steps. A future separate registration must freeze exact
batch-ID schedules, implementation, runtime and tests before any fitting.

## Question, fixed scope and controls

Does forcing same-entity contrasting city values into every city batch repair
the reproducible first-byte preference errors, beyond an identically timed
city-only batch schedule without forced grouping? Original random batches already
contained contrasts. The hypothesis is greater concentration, not missing pairs.

Use ONLY the original96 training documents/labels/inputs bound by local-answer-
dev-v1 registration `c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4`.
No development or held-out cases, new examples or altered prefixes/targets.
Both templates and nonces remain. Keep the exact original byte tokenizer and
ordinary-matched configuration: context32,width18,heads2,one layer, FFN72,
259-ID vocabulary,14,058 parameters, max_document64. Only seed947, the prospectively
identified failing cell, with two fresh fits: control first, paired second.
This targeted experiment estimates no seed-population or architecture effect.

Both arms start from identical seed947 initialization, requiring the original
initial-state tensor hash `32dd98b749a3b8967ea10910adbb7eec22bfe69210b009163182479d81d8eba5`.
No warm start from final saved weights and no new initialization/seed search.
Uniform full-document next-token CE including EOS, no weighting; same original
AdamW lr.003,betas(.9,.999),eps1e-8,weight_decay.01,foreach=False,fused=False,
clip1.0. CPU float32, one thread, deterministic algorithms. Full-document BPTT
with reset per document, original `make_batch`/`forward_batch`/loss partition.
Exactly1536 steps, batch8,128 epochs of96 documents per arm. Every document128
presentations,692224 targets per arm. No early checkpoint selection or extension.

## Fully specified single change

Epoch e=0..127; sort IDs lexically before each specified shuffle. Partition
the32 city documents and64 noncity documents by ORIGINAL training labels.
Reserve step offsets0,3,6,9 of each12-step epoch for four city batches in BOTH
arms. All other offsets consume the same eight noncity batches, obtained from
`random.Random(947+200000+e).shuffle(noncity_ids)`, split consecutively into8.

- Control city batches: shuffle all32 city IDs using
  `random.Random(947+100000+e)`, then split consecutively into four batches of8.
- Paired city batches: each entity has exactly8 city documents = two values x
  two templates x two nonces. Shuffle the sorted four entity names using
  `random.Random(947+100000+e)`; each entity group is one city batch. Thus each
  fixed entity/template has both training values in that batch.
- Shuffle IDs inside each city batch using a fresh
  `random.Random(947+300000+12*e+offset)` in BOTH arms. Noncity order is identical.

Freeze expanded3072 batch-ID rows and verify per-document exposure, per-step
target counts and padded forward positions match between arms. All city
documents have the same length, so regrouping preserves those counts; noncity
batches are identical. Parameters, optimizer updates, data and token work match;
measure actual CPU/wall rather than claim equal FLOPs. The intervention is
within-city composition only. A comparison to original fully mixed batching
would conflate composition with field timing and is outside this design.

## Fixed observations, gates and finite stop

Save every step's full/history/answer losses and targets, gradient norm, batch
IDs, final checkpoint/hash and complete lifetime CPU/wall/peak memory. Preserve
every failed attempt and partial output; no retries or budget increases.
After each final checkpoint, evaluate all96 ORIGINAL training prefixes plus
first-case replay with the original greedy OwnedSession decoder: PAD/BOS-only
suppression, cap8, no question flush, exact native gold+EOS scorer. Save every
raw continuation before scoring; no trimming, inserted EOS or extraction.
Separately measure teacher-forced training losses and first-answer ranks/margins
for all32 city cases, keeping those measurements distinct from generated answers.

Prospective success of the paired arm requires ALL96 complete exact gold+EOS
answers, zero malformed/repetitive outputs, all16 previously failing city first
bytes rank1 with winner-minus-runner-up>1e-4, replay/hash/accounting integrity,
and no regression on the original80 correct cases. This is a new study gate,
not a revision of v1's failed90/96 prerequisite. Compare both arms at identical
fixed final step; do not choose whichever checkpoint/seed looks favorable.

- Paired fails: reject its sufficiency under this design/budget; stop without
  added examples, steps, weighting, seeds or another curriculum.
- Both pass: repair is not specific to forced pairing; city-batch scheduling
  remains a candidate explanation, not a proven causal mechanism.
- Only paired passes: supports this composition intervention in ordinary947;
  does not identify an initialization-only cause or establish generalization.
- Only control passes, or neither passes: no support for forced pairing.

Before fitting, require exact expanded schedule/initialization/target contracts
and a separate zero-update resource rehearsal within30 CPU/wall seconds. Its
registered projection must fit60 CPU AND wall seconds per cold fit,20 per
generation/loss stage,2 per request, and200 CPU AND wall seconds for the complete
execution Job,2GiB commit and128MiB logical output. Stop on rehearsal, cap,
nonfinite, integrity or accounting failure, without fit/rehearsal retries.
Charge setup, rehearsal, loading, cold imports, controllers, all descendants and
exit in the future enclosing Job; outer observer separately. Two fits maximum,
3072 optimizer updates total. No development stage in this proposal.

Once both arms and frozen observations finish, stop and report these outcomes.
No result authorizes a development run or memory comparison within this design;
those require later separate registration. Current action is to preserve this
one proposal without executing it.
