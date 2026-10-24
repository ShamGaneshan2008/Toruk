# M4 conditional protocol and prerequisite gate

Historical pre-implementation draft. Subsequent M6 work implemented and ran a
smaller fixed-boundary pilot; see [actual protocol](m6-validation-protocol.md)
and [results](m6-results.md). The original blocked audit/draft is retained below.

Status on 2026-10-20: **BLOCKED before implementation**. This is an internal
candidate protocol, not a frozen experiment or evidence of an M4 pipeline.
The public CLI currently has no M4 commands. See [audit](m4-prerequisite-audit.md).
There is no implemented M3 interface to reuse, and no M2 world generator/oracle
or established factual scoring conventions. Inventing an unrelated memory model
or relabeling the prose fixture would not establish the requested baseline.

## Candidate experiment, to freeze after M2/M3 verification

- Decision: at a completed segment boundary, retain previous memory (reference)
  or accept the existing writer's proposed next state. No protected revisions,
  new backbone, archive or M5 controller. The ordinary recurrent baseline always
  accepts the proposal. Operations act on independent state clones.
- Runtime features: fixed-size previous memory, proposed memory and masked
  current-segment hidden summary from the frozen M3 model. Token IDs, question
  text, continuation, gold table and raw-history buffer are excluded from the
  predictor interface. Feature extraction must precede continuation/probe access.
- Output: predicted reference loss minus candidate loss, in mean nats per
  scored downstream token; positive means expected improvement. Retain has
  exactly zero effect by definition. Predict one scalar for the write candidate
  with a small MLP; use training-only normalization and squared-error fitting.
- Recommendation: accept write only when the estimate exceeds a validation-set
  threshold; ties, invalid/nonfinite inputs or incompatible model/feature schema
  retain memory. Unsupported shapes are errors. Out-of-range normalized features
  trigger an explicitly recorded retain fallback using training-set bounds;
  this is a limited support check, not a reliable general OOD detector.
- Labels: replay a frozen training document to a selected boundary, snapshot
  state, then evaluate retain/write under identical continuation, probe targets,
  seeds and token budget with no weight updates. Measure both absolute branch
  losses and their paired difference. Future observations and answer labels are
  permitted only inside the offline evaluator. Greedy probe answers must start
  from question prefixes without gold answer tokens. Keep probe accuracy separate
  from token-loss labels; do not silently combine different units.
- Intervention semantics: after this one intervention, both branches use the
  same frozen M3 writer policy. The estimand is a bounded-horizon effect under
  subsequent normal writes, not the effect of permanently freezing memory.
  Record all actual targets and counts so differing branch token counts cannot
  change the denominator. Probe branches clone the same observed-history state
  and never write questions/answers back to shared history.
- Cache identity: schema/generator/feature versions, model/checkpoint SHA256,
  tokenizer, exact split/data SHA256, code fingerprint, operation set, boundary,
  horizon/probe budget and seeds. Store initial-state and target fingerprints,
  branch-state checksums, outcomes and cost. Reject mismatch/corruption; never
  place outcomes or future identifiers in serialized runtime feature tensors.
- Pilot caps proposed for later validation: CPU, one thread, seeds 17/23, at
  most 8 training and 4 validation documents, one selected boundary each,
  two operations, at most two continuation segments and two probes per boundary,
  100 predictor optimizer steps, 120-second subprocess timeout per stage.
  Profile first; reduce the pilot if it cannot fit. Do not execute these stages
  until a frozen M2 split/probe manifest and verified M3 checkpoint exist.

## Evaluation and cost protocol to freeze

Split by world/document before selecting boundaries. Train fits labels/features;
validation selects the threshold and any feature bounds. Keep test unopened
until the complete protocol, code/data identities and primary metrics are frozen.
Validation labels are scoring-only, never optimizer inputs.

Primary decision metric: mean paired regret relative to the measured best
candidate. Compare predicted effects with MAE/RMSE, predicted-versus-observed
effect bins (counts, means and calibration residuals), pairwise ranking accuracy
with declared tie tolerance, and harmful-write precision/recall. Report class
counts and undefined metrics explicitly. Report delayed-answer exact accuracy,
recall, correction, unrelated-fact preservation and abstention coverage under
M2's verified scorer, with history/distractor/saturation strata. Use document-level
paired bootstrap intervals if sample size permits; a tiny pilot cannot support
a superiority conclusion.

Baselines share the same bounded observed information: always retain, always
write (M3 without prediction), a training-fixed heuristic based on proposal/state
distance, seeded shuffled predictor outputs, and measured-outcome oracle selection
as an offline upper bound. Specify the heuristic/threshold on training/validation
before test access. Add feature ablations (no previous memory; no proposal) and
an equal-parameter predictor control. Offline oracle code must not be imported
by runtime inference. Paired offline selection alone is insufficient: re-run
complete held-out documents under each deployed decision policy because policy
choices change subsequent state distributions.

Count label-generation tokens, forward steps, branch count, elapsed time and
peak process memory; predictor parameters, training steps/time and inference
latency; full model/history throughput, writes, end-to-end answer latency and
bounded-state bytes. Account for replay and all failed pilots. Measure latency
with warmup/repetitions and report timing scope. State bytes are storage, never
tokens read or proof of time savings. A null result remains a null result.

## Required implementation tests after the gate opens

Sentinel perturbations of future/gold fields must leave serialized runtime
features identical; branches must share initial-state and downstream-target
hashes; parameter/RNG snapshots must prove no sibling training. Cover state-copy
independence, deterministic labels, cache mismatch rejection for each identity,
finite shapes, nonzero predictor gradients, checkpoint parity, oracle/runtime
separation and a real bounded label/train/evaluate CLI integration. These tests
are currently **NOT_RUN**, since the relevant implementation does not exist.

Before M5, resolve whether the verified M3 state carries delayed information,
whether the labels have measurable variation, whether the predictor beats the
heuristic on validation and complete policy rollouts, and whether its overhead
and calibration justify a controller. No M5 mechanism is authorized by this note.
