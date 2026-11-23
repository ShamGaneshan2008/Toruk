# Value-start supervision development v1: prospective protocol

23 November 2026. CUSTOM Toruk weights only. No external pretrained model,
retrieval answer, parser-generated answer, API or production-chat modification.
This is one bounded objective intervention, not a memory architecture study.

## Readiness and motivation

The v2 harness is already committed at7cdded09, despite the request's historical
'uncommitted' wording. Phase1 reruns all24 disposable process tests, covering
normal/child/failed/timeout/interrupted exit, late writes, incomplete publication
and mutation. Readiness requires a PASS final receipt and verified observer seal.
No research fit occurs if readiness or resource rehearsal fails. Old v1 seals
remain unchanged and their registered integrity gate remains FAIL.

Saved-only diagnosis checks all12 prior final checkpoint identities, finite
tensors and1536-step optimizer progress without constructing a model or making
new forwards. The same initialization is verified across arms within model/seed.
All16 old ordinary947 failures were fixed by both city schedules; city shuffling
then misselected four formerly correct t cases, pairing six. All are saved
rank-two losing preferences; no near tie or missing local fact is demonstrated.
Schedules match total exposure and tensor work. Accuracy, norms and loss
correlations do not identify why optimization chose these competitors.
Initialization and shuffle effects across seeds remain confounded.

Hypothesis: stronger supervision of the FIRST answer byte after '?=' may improve
value discrimination while preserving suffix/EOS behavior. Compare first16
against uniform CE on the strongest relevant city-shuffled schedule. This differs
from the earlier answer16 study, which weighted ALL answer tokens on a smaller,
fixed-entity/value training set and failed development. No success is assumed.

## Exact frozen design

Version:toruk-local-answer-value-start-dev-v1. Seeds601/947, ordinary and recurrent,
two objectives = eight fresh fits. No prior weights are initialization.
Original96 training documents/inputs/labels and24 fresh-combination development
inputs/labels are copied byte-for-byte from local-answer-dev-v1 registration
c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4.
Train has32 city,32 code,32 unknown cases, two templates/two nonces.
Development has8/category,12/template; entity/value combinations are disjoint
from training, with shared answer vocabulary and syntax. It is development,
not an independent final or held-out study. Prior paired-batch development was
NOT_RUN. The experiment opens no held-out input. A pre-freeze search-scope incident is
recorded separately; zero unrelated artifact reads cannot be certified.

Freeze datasets and expanded schedules in plan.json before rehearsal. Exact
schedules are the saved city-shuffled rows for601/947 from paired-batch v1:
city offsets0,3,6,9 per12-step epoch, Random(seed+100000+epoch) city shuffle;
Random(seed+200000+epoch) noncity shuffle; within-city shuffle
Random(seed+300000+12*epoch+offset). The same1536 rows per seed apply to both
objectives and both models. All96 documents appear128 times:12288 presentations,
692224 actual byte/EOS targets,786432 padded positions per fit. Right-pad every
batch to8x64; two32-position segments, unchanged causal shift and answer boundary.
Native first-answer y/logit index=len(prefix UTF-8 bytes). No moved targets.

ByteTokenizer259 IDs,PAD0/BOS1/EOS2,byte+3,original fingerprint.
OwnedConfig context32,width16,heads4,one layer,four slots,max_document64.
Ordinary_matched width18,heads2,FFN72,14058 parameters; recurrent width16,heads4,
FFN64,14416 parameters. These are within3%, not exactly parameter/compute equal
across architectures. Arm comparisons within model share initialization,
parameters, data, optimizer and dense forward work. Actual total CPU/wall and
memory are measured; no equal-time or equal-FLOPs claim.

CPU float32,one Torch thread,deterministic algorithms. AdamW lr.003,betas(.9,.999),
eps1e-8,weight_decay.01,foreach=False,fused=False,clip1.0. Fixed1536 updates,
batch8,full-document BPTT,independent document state reset. Final checkpoint only.
No added examples, curriculum, architecture change, resumption, seed selection,
early success stop, additional steps or objective tuning.

Let H and A be summed history and answer CE including EOS, F summed CE at the
first answer position, nH/nA/nF their counts. Uniform extra0:
L=(H+A)/(nH+nA). Candidate extra15:
L=(H+A+15F)/(nH+nA+15nF).
Thus first answer byte weight16, every other byte including EOS weight1.
F comes from the same full logits: no additional model forward. Both arms compute
the same loss partitions for logging. Candidate weighted mass876544 targets/fit,
but actual targets and dense work are unchanged. All three unweighted NLLs
(full,answer,first) are compared separately after fitting.

Fixed order:601 ordinary uniform/first16;601 recurrent first16/uniform;
947 recurrent uniform/first16;947 ordinary first16/uniform.
All eight fits/training observations complete unless resource/integrity STOP.

## Answers, independent outcomes and gates

Greedy unchanged OwnedSession; prefix only, budget8,suppress PAD/BOS only,
stop at EOS. Fresh session per example, no question flush, extraction, trimming,
repair or answer supplied by a scorer. Only custom trained weights choose IDs.
Save all96 training prefixes+first-case replay before opening evaluator labels.
Save first-position full259-ID vectors for all96+replay, verifying free first-ID
parity and identical vector replay. Teacher-forced NLL is a separate observation.

Outcomes are separate: full exact gold native IDs followed by EOS; exact value
body (remove ONE terminal EOS only for this diagnostic); EOS presence; wrong
first byte; malformed value body (outside the nine-value vocabulary); repetition
(one/two-ID block repeated three times). No-EOS exact body may be value-correct
while full exact is false. This diagnostic never changes model output.

Candidate training mastery: EACH of four first16 cells must be96/96 full exact,
96/96 EOS,zero wrong first bytes,zero malformed/repetition. Report control mastery
under the SAME96/96 criterion separately. For development eligibility, uniform
controls need the original local-answer protocol's>=90/96 floor,96/96 EOS and
zero malformed/repetition. This floor is fixed before fitting, not chosen after
results. It permits studying generalization against an imperfect strong control;
it does not call92/96 'mastery'. Global training eligibility requires all candidate
mastery plus all control floors. If it fails, development is NOT_RUN for BOTH arms.
No data may be parsed by a fit loader except train-documents with split=train.

Training improvement additionally requires positive ordinary947 exact gain versus
uniform and no first16 exact regression at any registered model/seed. A failed
candidate mastery rejects sufficient repair, even if some old mistakes improve.
Matching or losing to uniform gives no objective-specific benefit.

Only if training eligibility passes, each frozen checkpoint generates the24
development inputs+replay ONCE, then24 equal-width assignment-masked question-only
inputs+replay. These diagnostic answers also come only from its own weights.
Main development floor for EACH candidate:>=22/24 full exact,city>=7/8,
code>=7/8,unknown8/8,EOS24/24,zero malformed/repetition,known exact gain>=8 over
question-only. Report both models/seeds/arms regardless of success.
Generalizable improvement additionally requires no per-cell exact/EOS regression
versus uniform and positive aggregate known-fact exact gain. No gates are retuned.

Studying memory architecture again requires all candidate training mastery,
all candidate development floors, demonstrable source dependence via question-only,
and no per-cell regression versus uniform, plus complete integrity/resource PASS.
This only justifies a NEW separately registered delayed-memory study; it proves
no memory advantage, natural dialogue competence, broad transfer or efficiency.

## Resource rehearsal and frozen caps

The disposable rehearsal is excluded from the registered arm comparison and
reported separately with its complete cost. Seed900503, different random8x64 IDs,
three forward/backward iterations per model/objective, ZERO optimizer steps.
Record all iterations, unchanged parameter hashes, empty optimizer state,
finite losses/gradients. First iteration is cold/setup. For each condition
B=2*max(CPU,wall over last two iterations)*1536+20.
Choose one common fit cap max(60,ceil(max(B)/10)*10), ceiling120 seconds.
If the ceiling or45-second CPU/wall rehearsal Job fails:STOP,no retry or fit.
This deterministic rule sizes caps using disposable runtime only. Final cap is
frozen in registration.json BEFORE any research fit; never raised afterward.

Other fixed caps: contract Job60; preparation budget150; each training evaluation
30; development observation30; per generation/vector/loss request2; complete
registered budget1500 CPU AND wall seconds;2GiB Job commit;128MiB logical generated output per preparation/registered branch;
poll50ms,max gap5s. Stop immediately on nonfinite,hash,replay,request,process,
receipt,monitor or resource failure. Preserve every failed/partial attempt.
A forced kill may prevent a checkpoint from being written; partial trace/cost
records still survive. Cooperative fit exceptions retain partial checkpoints.

The plan binds protocol/source snapshots,data,tokenizer,initial hashes,schedules,
optimizer,order and gates before rehearsal. The final registration additionally
binds readiness, saved diagnosis, contract/rehearsal seals and final caps.
Exclusive attempt-start marker permits a single registered execution.

All stages use lifetime_job_v2.watch_and_seal from the PARENT after workers exit.
Workers write data, never monitor seals. Closed stage directories are immutable.
The complete registered-budget Job contains the root study observer/controller,
nested workers and their sealing work. Its total already includes nested costs;
never add nested totals twice. Preparation, readiness and saved diagnosis are
distinct complete Jobs; report them separately and as a non-overlapping sum.
Pre-existing type-check caches and frozen inputs sit outside those output branches.
The outermost observer's complete lifetime and editing/reporting outside Jobs
remain unmeasured and must be disclosed.

## Preservation and audit

Protect old paired-batch files, prior v2/handoff records and existing ignored
checkpoints by before/after bytes+SHA-256. No historical seal or report is changed.
No commits or push in this task. New weights remain ignored/local.

After execution, independently verify all formal v2 seals, final kernel receipts,
per-step schedule/exposure/targets,checkpoint hashes,raw scorer outcomes,vector
argmax/ranks/margins,request limits,replays,and training/development decisions.
Audit outputs live OUTSIDE the sealed execution directories. Negative disposable
fixtures are retained as intentional failures, not confused with study seals.
Report local checks and hosted CI separately; hosted CI is not run here.
A quality failure can have valid integrity; neither implies overall research PASS.
