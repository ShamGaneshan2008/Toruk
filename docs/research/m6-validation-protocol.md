# Validation pilot protocol: prerequisite recovery through M6

Frozen before the registered pilot on 2026-10-20. Earlier M4/M5 audit notes
describe the repository before the prerequisite implementations added in this
task. This is a tiny validation study; final matched-resource M6 remains partial.

## Question and resource limits

Does the complete bounded predictor/revision configuration improve mean generated
accuracy on corrected color, unchanged entity name, unrelated date and unrelated
number over simpler alternatives? The primary endpoint is the unweighted mean of
these four group accuracies. Secondary endpoints: all-six-group accuracy, unknown/
ambiguous accuracy and attempted-answer coverage, history and answer CE, predictor
calibration/ranking/regret, actual model work, elapsed time and process peak memory.

Predeclared seed 23 (the existing foundation seed), fixture seed 17, four worlds
per split, all six probes per world. One CPU thread, float32, 2-step ordinary and
recurrent profiles followed by 12 optimizer steps per configuration; context 64,
width 32, four heads, two layers. The CPU model size is chosen before any
validation result. Profile timings establish execution cost, not a tuning loop.
The outer command has a 120-second timeout; driver checks a 110-second elapsed
budget before each stage. Failed/incomplete stages retain their records and
outputs. No automatic retries or selection by favorable outcomes.

The driver writes `protocol.json` before generating data. The final test world
file is generated and hashed but never loaded/scored; unit tests use independent
temporary datasets. No validation-based coefficient, threshold or architecture
search. Across-seed variability is not estimable from one seed; report it as null,
not zero. World count is too small for reliable generalization claims. No final
test result, superiority, publication readiness or efficiency gain is claimed.

## M4 paired predictor

One selected decision per world: the final observed-history segment's write.
Operations are retain previous memory or accept its proposed next memory, from
the same pre-boundary model/state. Earlier writes are unchanged. Both branches
then answer the same six later questions independently, with equal budgets and
greedy generation; there are no optimizer steps or stochastic model layers.
Parameters and previous state are checked for mutation. A teacher-forced label
is retain minus write mean answer NLL (nats/byte including terminating newline).
This is a fixed-boundary local effect, not a full-history counterfactual matrix.

The runtime module `effect_predictor.py` takes only bounded previous/proposed
memory and the current masked hidden summary. It has no oracle/world/label imports.
Features are captured before question/answer access. Offline `effect_training.py`
owns labels and oracle-style outcome selection. A 16-hidden-unit tanh MLP fits
training-only normalized inputs/targets with MSE for 100 full-batch steps. The
checkpoint binds to the exact LM checkpoint. Train-set mean/scale and per-feature
support (max absolute standardized training value + 1) are fixed without validation.
Invalid or out-of-support inputs retain memory; support checking is not a general
OOD detector. Positive finite estimates write, ties/nonpositive estimates retain.

Label caches bind schema, checkpoint, code, data+manifest, split, operation set,
seed and budget; the feature/label payload has a checksum. Mismatches/corruption
are rejected. Baselines: retain, write, a proposal-displacement heuristic with
training-feature median threshold, shuffled predictor recommendations and measured
best-branch NLL oracle. The oracle is an offline upper bound on this single local
decision's NLL regret only; it is not a general upper bound on answer accuracy or
an inference policy. Actual runtime random policy uses seeded independent bits.
Raw branch answers, target counts, effects, features and costs are retained.

## M5 correction and preservation

The verified recurrent architecture is trained afresh with the same seed/world
order/number of steps. Every question branch starts from cloned observed-history
memory. Gold answers exist only in teacher-forced loss and offline scoring.
The verified forward-world/backwards-oracle semantics from `m2-controlled-worlds.md`
assign current corrected values; preservation targets are the unaffected entity
name and other entity's date/number. Obsolete values are never preservation targets.
History CE models actual observed text, including earlier records as historical
text; it is not a claim that obsolete records remain current truth.

Baseline loss: mean CE over all answer tokens + 0.1 mean history-token CE.
Revision loss: corrected answer mean CE + mean of the three per-probe preservation
CEs + 0.1 mean of unknown/ambiguous answer CEs + 0.1 history CE. Prefix/padding
targets are masked. Per-probe normalization prevents long date strings dominating
preservation. All weights are predeclared. The no-correction/no-preservation
ablations set only the respective term to zero; all branches are still executed
so their forward-work budget is comparable. No mechanism infers hidden authority.

The predictor influences only the last observed-history write at inference.
It is separately relabeled/refitted against each trained model's exact checkpoint;
reusing a predictor bound to old LM weights is rejected. No full sequential M5
controller, protected revisions or learned credibility mechanism is implemented.
Correction/preservation capability must be judged by generated answers, not loss.

## Baseline definitions and interpretation

Fourteen predeclared results: ordinary local-context QA; recurrent QA always-write
and predictor; revision always-write, predictor, heuristic, seeded random, final
retain, and full-history reset diagnostic; no-correction and no-preservation
always-write; recurrent QA with 2 and 8 slots; ordinary QA with width 40.
All main runs use equal worlds/probes/optimizer-step budgets. Recurrent/revision
variants at four slots have identical parameters; predictor inference adds its
own explicitly counted parameters. The width-40 ordinary sensitivity is only an
approximate parameter match. Capacity variants add/remove slot-specific biases
and state capacity. Reset changes the inference distribution and is a diagnostic.
Final retain prevents the last write only; it does not freeze all memory updates.

Removing revision/correction/preservation is compared under always-write to
isolate the objective. Removing prediction/using a heuristic/random decisions is
compared at the same fixed revision checkpoint. Capacity is compared on QA-only
training. Do not attribute comparisons that change both checkpoint/objective and
decision policy to one component. Equal steps do not match FLOPs or parameters;
extra branch generation/predictor training prevents an equal total-training-cost
claim. Inference state/compute budgets are measured but not exactly matched.

A null primary result, failure to beat the heuristic, or increased correction
accompanied by damaged preservation narrows/falsifies the pilot hypothesis. If
the predictor mostly falls back to retain, disclose it rather than calling this
learned decision quality. If every model fails to answer, distinguish failure to
learn the benchmark from evidence that a memory mechanism is intrinsically useless.

Costs include standalone profiles, every main model, label branches, generated
branch answers, predictor fits, teacher-forced offline scoring, runtime inference
and artifact-writing overhead in command wall time. Per-stage times and cumulative
process peak working set are recorded. The latter includes interpreter/framework/
all stages; it is not per-model tensor allocation or a fair peak-memory comparison.
Stored state bytes do not measure text read. Prior failed tests/pilots remain in
`artifacts/checks/m6-*` and `artifacts/m6-failed-tiny-001`, outside registered-pilot
loop totals. No total CPU-hour claim; test-suite token counts are uninstrumented.

The five requested primary-paper versions were inspected earlier in this same
session/date; see `related-work.md` for methods and overlap. Paired counterfactual
memory evaluation is prior art (especially MGPO and PAIR). Internal-state prediction
and this prototype's implementation choices are experimental distinctions only.

## Reproduction and next gate

```powershell
.\.venv\Scripts\python.exe scripts/check.py m6-pilot-reproduction -- .\.venv\Scripts\python.exe -m toruk_lm controlled-pilot --output artifacts/m6-reproduction --steps 12 --worlds 4 --answer-budget 16 --seconds 110
```

Use a fresh destination/label. Each artifact directory contains the exact config,
checkpoint/data identities, raw predictions and metrics; `stages.json` preserves
failure/timing evidence; `manifest.json` seals completed-run files. The driver
rejects missing/duplicate/stale/data-inconsistent comparison results.
Before M7, establish learning curves, multiple independent seeds, factorized
held-out shifts, matched total compute/inference budgets, stronger parameter
controls and a separately frozen final test protocol. This pilot cannot substitute
for those generalization prerequisites.
