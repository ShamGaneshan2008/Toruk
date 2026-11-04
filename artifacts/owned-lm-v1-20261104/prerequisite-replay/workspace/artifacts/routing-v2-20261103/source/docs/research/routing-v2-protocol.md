# Path A: routing v2 preregistration — 3 November 2026

Decision made before implementation/training/new final generation: pursue Path A.
Qualification v1 failed useful memory, quality-preserving efficiency, and reliable
generalization. Its conditional aggregate accuracy pass is not the useful claim.
Retain all v1 sources, weights, final data and negative results unchanged.

The largest measured failure is unreliable factual transfer: integrated seed 31
recalls 0/120 known qualification worlds; seed 47 recalls 31/120 and produces
45/48 unsupported unknown/ambiguous answers. Earlier held-out diagnostics found
read routing correct on 20/96 and 29/96 queries and write routing correct on
129/971 and 350/971 records. These are measurements, not proof that routing alone
causes every wrong answer. Raw histories contain the required facts, and state
removal cannot repair factual recall. Shared decoder/template-transfer failures
remain a competing explanation. Exact-scoring and overlapping task-category
limitations must be audited separately from model failure.

## One bounded change and predictions

Change only the learned routing representation to be insensitive to record/query
word order. Keep the value encoder, answer decoder, local suffix, slot update
equation, parameter allocation, supervised objective, training worlds, batches,
optimizer, seed and step budget unchanged. Technical implementation details
belong in the Git-ignored private architecture note. Use a distinct checkpoint
identity and loader; never reinterpret v1 weights as a trained v2 checkpoint.

Expected effect: improve held-out read/write routing and known factual accuracy
relative to v1. Possible regressions: order-sensitive attribution or negation,
unknown abstention, correction versus unauthoritative-claim discrimination, and
answer decoding may still fail because its representations remain order-sensitive.
A routing improvement alone does not establish useful generated answers.
No backbone replacement, answer parser, scripted response or test-answer input.

## Training, development, and final isolation

Use only the original integrated-study 384 training worlds for fitting. Exactly
800 steps, batch 16, Adam 0.003, one CPU thread, float32, seeds 31 and 47, same
sampling and 0.25 addressing-loss coefficient. Use the original 96 development
worlds for diagnostics only. No hyperparameter search or checkpoint selection:
always evaluate the 800-step checkpoint, retaining development failures. Cap each
training subprocess at 300 seconds and evaluation subprocess at 180 seconds.
Abort and retain failures on nonfinite gradients or sampled RSS above 2 GiB.
Record optimizer-loop time, sampled/high-water process memory and parent wall
time. No downloads, GPU training, paid compute, or deployment.

After training and development, seal source, protocol, configuration, all relevant
checkpoints, tokenizer and data before generating final answers. Three fresh
world seeds 8101/8102/8103, eight worlds per category, seven categories matching
qualification: correction, preservation, distant recall, ambiguity, distraction,
multi-fact, unknown. Generate independent event draws; reuse the established
offline authoritative-write oracle. Reuse the finite trained symbols explicitly.
Final record template: `{name} {value} {field} {Set|Change|Claim}.`; final query:
`{field}? {name}'s is What`. These reorder the training vocabulary; they do not
claim lexical, entity, semantic or naturalistic generalization. No training or
development uses these template families. Assert no exact history/query overlap
with any old train/development/final or qualification worlds. Stress +0/+8/+32
irrelevant writes as paired worlds; preserve the same distractor prefix.
Multi-fact requests query both corrected and unrelated preserved keys separately.

## Fixed comparisons and measurements

Unchanged controls: historical ordinary decoder at seeds 31/47 with recent,
deterministic lexical, and frozen learned-v2 external selection. Compare old
integrated v1, new routing v2, and new v2 with state zeroed at answer time.
External selection is an unqualified distribution-shift diagnostic. Ordinary and
integrated models share allocated architecture/training budget, not exact weights.
The pretrained Qwen/Ollama chatbot remains separate and unchanged. Run existing
local Qwen chat checks separately; their integration pass is not research quality.

Primary targeted metric: mean of query read-routing accuracy and record
write-routing accuracy, reported separately too, at load 0, against old integrated
v1. Improvement requires both routing accuracies to rise at each training seed.
Generated known-world accuracy must also improve at both seeds before calling
the target failure improved as a factual mechanism. Report paired world-cluster
bootstrap 95% intervals, 2,000 samples, RNG 9301, stratified by evaluation seed
and category and preserving training-seed pairing. Intervals condition on these
two checkpoints; report individual training/evaluation-seed scores separately.

Useful-memory gate remains >=80% overall and known-world exact accuracy, >=70%
in each category, <=5% unsupported unknown/ambiguous answers at both seeds, and
positive paired lower confidence bounds versus both recent and lexical baselines.
Report every category regression versus old v1. A tie from abstention fails quality.
No selected-token claim without quality preservation. Total-resource improvement
additionally requires lower forwarded workload, measured end-to-end latency and
sampled peak RSS in both seeds against recent and lexical. Wall time and RSS are
observations on a shared host, not isolated benchmarks or FLOPs/energy estimates.

Use unchanged exact UTF-8 answer equality with only `?` correct when unsupported.
Multi-fact world correctness requires both answers. Store all raw generated IDs,
texts, expectations, correctness and unsupported flags. Ambiguous wording remains
incorrect under primary scoring; append reviewer commentary separately if needed.
Record selector-chosen IDs and IDs contributing suffix bytes. Offline evidence
retention asks whether the latest authoritative relevant record contributes any
suffix bytes; this is partial-record exposure, not complete evidence comprehension.
Integrated state has no discrete evidence IDs: full-history evidence ingestion
is reported separately from routing correctness and generated factual recall.

Record per-query full history tokens scanned, selected tokens, memory update
tokens/cells, forwarded positions, extra routing embedding positions (v2 only),
state bytes, selection/inference latency, sampled process RSS every 5 ms and OS
high-water memory. Pooling work is additional even though it adds no GRU positions;
do not subtract it or equate position counts with total compute. Rebuild state
for each query, charging multi-fact histories twice. Time diagnostics separately
from inference; gold labels score routes offline and never enter runtime.

Run focused behavior/gradient/padding/reload/incompatibility tests before final
inference. Retain failed runs; no silent replacement or metric-guided retry.
Package source/config/data/checkpoint IDs, exact PowerShell argv/exit codes,
generated failures, aggregate uncertainty, compute and all eight requested gates.
Check Python CLI/tests/types/lint/format/build, Node, local chat, Git diff and
exact-commit GitHub Actions. Freeze verification must reject drift. Preserve
private files and original dirty work. No preview/public deployment under Path A.
