# Paired city batching development v1: prospective protocol

23 November 2026. Narrow hypothesis: concentrated same-entity contrasting city
examples in a minibatch may improve first-token discrimination. The completed
260-record probe establishes checkpoint preferences and answer-start path parity,
not the training cause. No missing contrast exposure was established.
No architecture, memory advantage, population, held-out or release claim.

This is a NEW study. It prospectively extends the 22 November two-fit
ordinary947 proposal at the user's request to ordinary/recurrent and two fixed
seeds, compares the original schedule, and adds development only after a strict
global training gate. The old proposal, studies and handoff are immutable.

## Exact examples and frozen identities

Use byte copies of the five original local-answer-dev-v1 files: 96 train
documents/inputs/labels and 24 fresh-combination development inputs/labels.
Original registration SHA-256:
c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4.
Each original data hash is checked. plan.json binds the exact copied bytes,
expanded schedules, all source snapshots, this protocol, tests, tokenizer,
runtime, original initial-state hashes and preservation baseline before rehearsal.
registration.json later binds the plan and successful rehearsal/contracts receipts
before any study update or answer. Exclusive markers prohibit a second attempt.

Train IDs train-000..095: uvo/pex/zim/nax, city la/mi/so/tu,
codes R-7/Q_2/V:4/Z!6, and unknown '?'. Each entity/category has two rotating
training values, templates A/B and two nonces. There are 32 examples/category.
Development IDs dev-000..023 use the other two entity/value combinations,
8/category, 12/template. This is the original development split, not held-out
evaluation. All answers occur in training. No new examples or adaptive templates.
Use original.validate for independent labels, balance and train/dev separation.
Assignment, query, answer and EOS fit together after the 31-byte prelude;
this is supplied-local copying, not a delayed-memory experiment.

## Three schedules, two seeds and two models

Seeds 601 and 947 are fixed in advance; initialization and data shuffle both vary
with seed. All three arms use identical initialization within model/seed. Expected
initial tensor hashes come from each original final training-summary.json.

1. original: keep the 96-document serialized order, shuffle using
   random.Random(seed+epoch), then split consecutively into twelve batches of 8.
2. city-shuffled: reserve offsets 0,3,6,9 of each twelve-step epoch for city
   batches. Sort the 32 city IDs, shuffle with Random(seed+100000+epoch),
   split into four batches of 8. Sort the 64 noncity IDs, shuffle with
   Random(seed+200000+epoch), split into eight batches used at other offsets.
3. city-paired: the same city slots and IDENTICAL noncity batches. Each entity's
   eight city IDs (two values x two templates x two nonces) form one complete
   city batch. Shuffle sorted entity names with Random(seed+100000+epoch).
   In both city schedules shuffle IDs inside each city batch with a fresh
   Random(seed+300000+12*epoch+offset).

All 9,216 expanded schedule rows (3 arms x 2 seeds x 1,536 steps) are frozen once,
shared by the ordinary and recurrent model at that seed. Contracts check counts,
pair composition, exact original shuffle, identical noncity order, and equal
per-step target counts between the two city schedules. The original comparison
also changes field timing; only city-paired versus city-shuffled isolates the
registered within-city composition change. Both comparisons must be reported.

Exactly 12 fits, 1,536 steps each, batch 8, 128 epochs. Every document appears
128 times per fit: 12,288 presentations and 692,224 scored byte/EOS targets.
Uniform full-document next-token CE, AdamW lr .003, betas (.9,.999), eps1e-8,
weight_decay .01, foreach=False, fused=False, clipping1.0. No weighting,
warmup, checkpoint selection, seed search, extensions, retries or early success stop.

OwnedConfig context32,width16,heads4,one layer,4 slots,max_document64.
Ordinary_matched is width18,heads2,FFN72,14,058 parameters. Memory_on is
width16,heads4,FFN64,14,416 parameters and256 bytes of recurrent state.
All weights train from scratch. State resets independently per document.
ByteTokenizer PAD0/BOS1/EOS2, byte+3, 259 IDs, frozen original fingerprint.
CPU float32, one Torch thread, deterministic algorithms.

To match dense work across differently composed batches, ALL arms right-pad x
to exactly64 (PAD0), y with ignore_index=-100, answer mask false. Each training
batch therefore processes512 positions in two32-position segments:
786,432 dense positions per fit. No valid targets/positions are moved.
Contracts compare valid losses/gradients with the original dynamic padding on
disposable examples. This common padding change means original-schedule results
are new measurements, not a promised bitwise reproduction of old weights.
Measured CPU/wall are reported; identical tensor shapes are not an equal-time
or efficiency claim. Widths differ, so cross-model results do not isolate memory.

Fixed fit order:601 ordinary original,shuffled,paired;601 recurrent paired,
shuffled,original;947 recurrent original,shuffled,paired;947 ordinary paired,
shuffled,original. Analyze each final checkpoint before the next fit.

## Measurements, gates and rejection

After each fit: save full checkpoint/optimizer/RNG, per-step IDs, full/history/
answer loss sums and target counts, gradient norms, initialization/final tensor
hashes, checkpoint hash/bytes, and complete cold Job cost.
Generate all96 training prefixes plus first-case replay, then seal raw IDs and
answers BEFORE opening evaluator labels. Existing OwnedSession, greedy budget8,
suppress PAD/BOS only, EOS stops; no question flush, repair, extraction or trimming.
Exact means native gold UTF-8 byte+3 IDs followed by EOS2. Save EOS, malformed
(closed nine-string inventory), repetitive and category/template scores.
Teacher-force original full-document losses separately. Save full259-ID prefix
vectors, gold ranks/probabilities, signed margins and first-token errors on all32
city cases, verify generated-first-ID parity, retaining every raw measurement.

Training mastery per cell requires ALL:96/96 complete exact answers,96/96 EOS,
zero malformed/repetitive outputs,32/32 city first IDs correct, no winner margin
<=1e-4, and replay/integrity success. Complete all12 registered fits/training
observations unless resource/integrity STOP; then require ALL12 cells to master
training before ANY development generation. This strict gate includes controls.
If it fails, STOP_TRAINING_FAILURE; development stays NOT_RUN. Do not relax it
because a candidate improved or the original comparator has a known weakness.

Primary sufficiency target is ordinary947. Reject paired sufficiency if its
paired cell fails training mastery, including any of the16 old first-byte failures
or regressions on the80 previously correct cases. Reject robustness if any paired
model/seed loses training exactness or increases city-first errors relative to
either comparator. If paired masters but either comparator matches its city-first
error count, record NO_PAIRING_SPECIFIC_SUPPORT_COMPARATOR_MATCHES. Only paired
mastery with strictly fewer target errors than BOTH comparators, and no regression
at other registered cells, supports targeted discrimination under this design.
This does not prove a general training cause or necessity of pairing.

If the global training gate passes: each cell generates24 development prefixes
plus replay, then an equal-width assignment-masked question-only diagnostic
24+replay. Main development requires>=22/24 exact,city>=7/8,code>=7/8,unknown8/8,
24/24 EOS,zero malformed,and>=8 known correct answers beyond question-only.
Report paired-original and paired-city-shuffled per seed/model. Generalization
support additionally requires every paired cell to meet those floors, no paired
exact/EOS regression against either comparator, and strictly more total paired
city matches than each comparator. Otherwise reject the development improvement
claim. These tiny adaptive development cases are not an independent final study.
If reached, save raw outputs and costs even if development gates fail.

## Resource rehearsal, stop and accounting

Before fitting, run focused contracts, including real Windows Jobs for successful,
failed, interrupted and abrupt controllers, descendants, cap kill and observer
interruption, under30 CPU AND wall seconds. Each terminated test must retain
complete final CPU and0 active descendants. Test work uses disposable examples.

One disposable numeric rehearsal, seed900301, different random tokens, three
8x64 forward/backward passes per model, zero optimizer updates. First pass is
cold/setup; last two give B=2*max(CPU,wall of last two)*1536+10 seconds.
Unchanged parameter hashes and empty optimizer state are required.
Cold rehearsal<=30 CPU AND wall,2GiB. B<=60 for EACH model, and
6*(Bordinary+Brecurrent)+24*20+80<=1500. Fail means STOP with no rehearsal retry,
fit, answer, seed/cap increase or revised protocol.

Caps fixed BEFORE rehearsal: cold fit60 CPU AND wall; training analysis20;
development analysis20; individual generation/loss/vector request2; contracts30;
rehearsal30; complete execution Job1500 CPU AND wall; memory2GiB; logical output
128MiB; sample50ms,max observation gap5s. The aggregate cap scales the old
two-fit scope to12 fits and optional development; it is a prospectively new cap,
not a changed old study receipt. Complete costs include all setup/contracts,
rehearsal,cold imports,freeze,workers,controllers,descendants,I/O and exit.
Nested stage totals are subsets: never add them again to the outer Job total.
Outer observer CPU-to-receipt is separate, not its full lifetime.
Editing/analysis outside these Jobs remains unmeasured.

lifetime_job.watch creates suspended workers, assigns a kernel Job, then resumes;
kill-on-close, memory limits, polling caps and final drain/query close lifetimes.
Controller-final receipts are diagnostic; kernel final totals remain authoritative.
Stop immediately on resource,monitor gap,nonfinite,hash,receipt,parity or replay
failure. Preserve partial traces, failed checkpoints if any, failed outputs and
all cost receipts. No attempt or failed file is overwritten.

Reports and offline checks run after execution in separately named scopes. Audit
saved rows without additional model inference. Preserve handoff and previous
frozen evidence by hashes before/after. New work stays uncommitted; new weights
remain ignored. Do not access held-out datasets or change production chat.
