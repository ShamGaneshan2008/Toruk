# Exact next experiment: city contrastive loss development v1

**PROPOSAL ONLY — NOT RUN.** No training, rehearsal, model forward, new answer,
held-out access or production change is authorized by this diagnosis artifact.
Create a separately registered attempt before any future model work. Suggested
new namespace: `artifacts/local-answer-city-contrastive-dev-v1/`; refuse an
existing attempt. Never extend or retry value-start v2 or entity-dropout v1.

## Hypothesis and one intervention

V2's 34 mistakes already have incorrect first-token preferences; 22 outputs match
a value previously trained for that entity/category. Training mastery does not
establish evidence-conditioned generalization. The optimization cause is unknown.
The later entity-dropout study failed, so do not repeat that intervention.

Test whether penalizing confusion between the two **training** city values for
each entity improves fresh-combination answering without losing previously correct
cases. This is a test of one objective modification, not a proven explanation of
the old failure or a memory comparison.

Control: the unchanged v2 first16 objective and city-shuffled schedule:

`L16 = (H + A + 15 F) / (nH + nA + 15 nF)`.

Candidate: **only** add `0.1 * Lcity`, with

`Lcity = mean_city_examples softplus(2 + z_first[c] - z_first[g])`.

`g` is the first native gold-answer byte ID. `c` is the first byte ID of the
other city value for that entity, derived exclusively from the frozen 96 training
labels. Each entity has exactly two training city values with distinct first
bytes. No development value or failure label selects the confuser. `z_first` is
the same teacher-forced first-answer logit vector already used for first16 CE.
For a batch with no city examples, define `Lcity = 0`. Code and unknown examples
retain their original objective. Freeze margin 2 and coefficient 0.1 once; no
search, retuning, alternative coefficients or changes after results.

Both arms compute/log the same diagnostic; the control adds no gradient from it.
No extra model forward, data example, optimizer update or changed decoding is
allowed. Extra candidate backward arithmetic has a measured cost; equal FLOPs
and an efficiency advantage are not assumed. Log CE and auxiliary losses
separately. Keeping first16 as this experiment's control does not promote it to
a reliable default.

## Frozen inputs and matched design

Byte-copy these files from `local-answer-value-start-replication-v2`, preserving
the exact bytes and verifying these SHA-256 identities before fitting:

| Input | SHA-256 |
| --- | --- |
| `train-documents.json` | `b406991cef36bdacdbc7462d35e7760bbb7192bb859a64608b0e223863821bfb` |
| `train-inputs.json` | `98e31e1fc992c66e0927dbba5d19591b045b2c37f747c2cdde8f45bb31c7bf76` |
| `train-labels.json` | `0b8306aae6427d954f473527e334699c5631b9a7b43942dadf7a2b2415bad6a5` |
| `dev-inputs.json` | `625f96f9a3c07c95c07d1026eca1442d28192d6c4ee43c54260b95b013b1c49b` |
| `dev-labels.json` | `790361d1401fae4c632fd90d5824864bee567dd43d4bd09158e61195492068e2` |
| `schedules.json` | `81f0bfd50b224c6595808d4f736d2947bbc9dd6a6007fa834d44e623b386786c` |

Dev IDs are exactly `v2-dev-000` through `v2-dev-023`, eight cases per category.
These are diagnosed, repeatedly observed development cases. Any future result
is adaptive development evidence, **not independent validation**. Do not inspect
or use a held-out corpus. Canonical train/dev overlap must remain zero.

Cross initialization 601/947 with shuffle 1301/1709, ordinary/recurrent, control/
candidate: **16 fresh fits, eight matched pairs**, final checkpoint only.
Same tokenizer, native IDs, 32-token segmentation, model configurations and
parameter counts as v2 (ordinary 14,058; recurrent 14,416). Same CPU float32,
one thread, deterministic algorithms, AdamW lr .003, betas (.9,.999), eps 1e-8,
weight decay .01, foreach=False, fused=False and clip 1.0. Exactly 1,536 updates,
batch 8, 128 presentations/document: 692,224 valid targets and 786,432 padded
positions/fit. Both arms keep CE weighted mass 876,544. The added city term has
4,096 scheduled training-example contributions/fit, reported separately.

Fresh identical within-pair initialization, independent initialization/shuffle
axes, unchanged input/target masks and per-document state reset. Counterbalance
fit arm order using crossed-index plus model-index parity, as in v2. No selection
of seeds, intermediate checkpoints, data variants or weak-cell retries.

## Eligibility, evaluation and no-regression gate

1. Freeze implementation, source/data/runtime hashes, confuser map, schedules,
   arm order, tests, gates and caps before rehearsal. Require the original v2
   runtime (Python 3.12.14, Torch 2.15.0+cpu, psutil 7.2.2 and recorded Windows
   platform). Do not waive source/evidence checks or relabel an old decision.
2. All 16 fits must score **96/96 exact and EOS**, with zero malformed, repetitive
   or wrong-first outputs on the original training inputs. Each control must
   reproduce v2's corresponding first16 final tensor hash and training native
   continuations. If any prerequisite fails, candidate development is NOT_RUN.
3. After global training eligibility, evaluate all eight controls once on the
   frozen dev and equal-width question-only inputs, including one replay each.
   Require exact v2 first16 native continuation parity before any candidate dev
   generation. A control mismatch stops the attempt, without inference retries.
4. Evaluate each candidate once with unchanged greedy OwnedSession, cap 8,
   PAD/BOS suppression and EOS 2. Score raw gold bytes plus EOS without trimming
   or repair; retain first-logit vectors, teacher losses and all native outputs.
5. Every candidate must meet exact >=22/24, city >=7/8, code >=7/8, unknown 8/8,
   EOS 24/24, zero malformed/repetition, and known-fact context gain >=8 over its
   own question-only condition. Require no category or EOS regression.
6. **Casewise no regression:** every dev case correct in its matched control
   must remain exactly correct in the candidate. Every non-ceiling control
   (<24) must have a strictly positive candidate exact gain. A ceiling control
   must remain 24/24; its tie is not evidence of improvement. Require positive
   total gain separately in ordinary and recurrent models. Mean city first-token
   teacher NLL must also decrease for recurrent601 under both shuffle seeds.

The ceiling rule and casewise gate apply only to this prospective proposal.
V2's strict-positive-all-eight gate remains failed. Aggregate gains cannot rescue
a failed cell, newly wrong case, category, EOS, or mechanism gate.

## Fixed resources and stop conditions

One disposable random-ID rehearsal, seed 927113, three forward/backward iterations
per model/arm, **zero optimizer updates** and no study examples. Cap rehearsal at
45 CPU and wall seconds; reject if `2*max(last-two CPU/wall)*1536 + 20 > 90`
for any condition. No second rehearsal or larger cap.

Preparation cap 150 CPU/wall seconds; contract checks 60. Each fit 90; each
training observation, control dev or candidate dev stage 30; each request 2.
Entire registered branch **1,800 CPU AND wall seconds**, 2 GiB Job commit,
128 MiB logical output, polling 50 ms, maximum monitoring gap 5 seconds. Count
complete process-tree lifetimes, imports/I/O/controllers/descendants and sealing.
The parent budget already includes nested stages; never add them twice.
Audit/check/reporting outside that branch are separate scopes, not zero cost.

- Missing/mismatched runtime, source, data, checkpoint, seal or accounting:
  **BLOCKED**, no evidence repair, and no fit if detected before fitting.
- Rehearsal projection or any resource cap fails: **STOP_RESOURCE**, preserve
  partial outputs; no retries, extra steps or cap increases.
- Training mastery fails: **STOP_TRAINING_FAILURE**, no development generation.
- Control tensor/native-output parity fails: **STOP_CONTROL_REPRODUCTION**;
  no candidate dev generation if detected at its prerequisite barrier.
- Any development quality, casewise no-regression, positive-gain or NLL gate
  fails: **STOP_DEVELOPMENT_FAILURE**; preserve the failed result and stop.
- All gates pass: **DEVELOPMENT_GATES_PASS** only. A fresh independently
  registered generalization study would still be needed; no memory, chatbot,
  release or total-efficiency claim follows.

Preserve all raw records and failed attempts with observer-owned seals after
complete process-tree closure. No worker seals growing monitor streams. This
proposal is not a launch request; this task performs saved-only diagnosis.
