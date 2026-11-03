# Existing-model value-fidelity development gate v1

Registered before implementation, training and development generation on
3 November 2026. This completes only the audit's recommended development gate.
No final/test split will be generated or evaluated and no deployment is included.

## Failure, one change, and predicted regression

Routing-v2 has real checkpoints and perfect top-1 routes on its prior controlled
word-order study, but outputs blue for all revised facts and cat for all original
facts: 14/120 known worlds at both seeds. Existing source/evidence integrity and
2,016 primary-world prediction parity were verified by the completed audit.
The bottleneck is Toruk's synthetic memory/value path, not Qwen language ability.
Top-1 routing alone cannot distinguish value encoding, soft-state contamination,
query conditioning and decoder failures.

Change only training-time record/query rendering: add fixed word-order variation
to the original 384 training worlds. Use the unchanged PooledRouterLM architecture,
70,208 parameters, value/answer computation, objective, seed initialization,
optimizer, sampled-world sequence, local context and memory capacity. Refit from
the same initial seeds, not from a silently substituted pretrained backbone.
Keep an independent augmentation RNG so sampled-world order stays matched.

Expected behavior: generated values should vary correctly with supplied facts
instead of operation-associated constants. Possible regressions: harder training
may lower fit under the same step budget, impair abstention, introduce correction
or preservation errors, or fail to transfer to untrained permutations. Retain
every outcome and stop after the fixed plan, including a failed gate.

## Frozen development plan and budgets

Train seeds 31 and 47, exactly 800 steps each, batch 16, Adam 0.003, gradient clip
1.0, answer CE + 0.25*(read/write address CE), one CPU Torch thread, float32.
The original 384 training worlds are the only fitting data. Four record orders
and four query orders are sampled per presentation with RNG seed+200000.
Detailed order tables are fixed in the private implementation note and script.
Neither training order family includes the old final template. No answer parser,
scripted output, backbone change, extra objective, or model architecture is added.

Use three fresh development world seeds 9101/9102/9103, eight worlds per category
per seed, seven categories: correction, preservation, distant, ambiguity,
distraction, multi-fact, unknown. Two fixed development record/query orders are
disjoint from all training orders and prior final word-order templates. Reuse
the finite trained entity/value vocabulary and established offline event oracle;
this does not test natural-language or unseen-entity generalization. Multi-fact
requires two independently generated answers to match for a correct world.

Save and hash these **development** worlds before model fitting; labels are only
for scoring, never runtime inputs. Hash source, protocol, training data and old
checkpoint identities before fitting. After fitting, hash both new checkpoints
before development inference. No step-budget selection or metric-guided retries.
This set remains development material; its results are not final-test evidence.

At most 180 seconds and 2 GiB sampled RSS for each training subprocess, sampled
every 5 ms. Evaluation is capped at 180 seconds per seed/method. Maximum new
research fitting is 1,600 steps /25,600 sampled world presentations and six
minutes of one-thread optimizer execution. No downloads, GPU/paid jobs, search,
large pretraining or additional milestone. Verification checks have separate
bounded timeouts; they are not claimed free.

## Comparison and deciding success

Evaluate unchanged recent and lexical controls using existing ordinary checkpoints,
old routing-v2 checkpoints, augmented checkpoints, and augmented checkpoints with
state zeroed only at answer time. All methods use the same development worlds,
byte tokenizer, 96-token suffix, 64-token record/query caps and 12-token greedy
answers. Ordinary and integrated weights are different; baseline weights remain
unchanged. Qwen and conversational JSON selectors remain separate from this gate.

PASS requires, **at each training seed**, all of:

- >=80% exact world accuracy and >=80% exact known-world accuracy.
- >=80% correction accuracy and >=80% preservation accuracy.
- <=5% unsupported answers among unknown/ambiguous queries.
- Zeroing state lowers known-world accuracy by >=50 percentage points, to verify
  that local context/default output alone does not satisfy value fidelity.

Otherwise report FAIL, or BLOCKED for missing prerequisites/failed execution.
Report category regressions, even if the aggregate gate passes. Correctness is
exact generated UTF-8 equality; only `?` is correct for unsupported/ambiguous
evidence. Each prediction stores actual generated token IDs, expected/decoded
answers, correctness, unsupported flags, selected and suffix record IDs, relevant
record exposure/ingestion, and offline read/write routing diagnostics. Gold event
keys, values and addresses are never passed to runtime inference.

Count full history scans, selected prompt tokens, memory update token positions,
update cells, recurrent forward positions, additional routing embedding positions,
state bytes, answer latency, process wall time and sampled/high-water RSS. Rebuild
history for every query, charging multi-fact reads twice. Routing diagnostics are
timed separately; RSS includes them. Positions are workload proxies, not FLOPs or
energy. Shared-host timings do not establish a controlled speed advantage.

Report each evaluation/training seed and category. Conditional paired 95% world-
cluster bootstrap intervals use 2,000 samples, RNG 9301, stratified by world seed
and category with both training seeds preserved. Only two trained models are
available; do not infer a training-population confidence interval or paper result.
Preserve old checkpoints, raw results and frozen data byte for byte. A passing
development gate only justifies planning a separate untouched final study later;
it does not authorize or complete that next milestone.
