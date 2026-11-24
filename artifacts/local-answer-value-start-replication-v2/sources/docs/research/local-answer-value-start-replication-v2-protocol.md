# Value-start replication v2: crossed initialization and shuffle registration

24 November 2026. Development only. No held-out files, external answer provider,
production chat, deployment, commit or push. Preserve all historical records and
local checkpoints. This is an objective replication, not a memory comparison.

## Precondition and scope

Value-start v1 is preserved in reviewed commit
`91f2e2b8e6b171c1b1f4fb27898f37f17b6b93ed`, with STOP_DEVELOPMENT_FAILURE,
the pre-freeze search-scope exception, raw answers, audit and observer seals.
Its unchanged independent verifier passed with readable access outside the
sandbox:737 protected files,337 paired-batch files,65 previous ignored weights,
24 scientific stage seals and all original answer rescoring. The sandbox denied
access to historical fixture trees and reported324 apparent deletions; those
are recorded separately, never restored or edited here. The failed sandbox
audit and successful read-only access check are not research fit attempts.
V1's388-entry reviewed payload inventory includes its eight local checkpoints.

The old instruction-scope incident remains disclosed. This task uses explicit
file reads and searches confined to named source/document paths. No held-out
input is opened or used. Previous results are not retuned or rescored as v2.
Use unchanged lifetime_job_v2.watch_and_seal: observer drains/closes the Job and
monitor streams before final receipts and seals. Workers never seal monitors.
No fit if prerequisites, contracts, rehearsal or final registration fail.

## Frozen data and independent axes

Initialization seeds601,947 CROSS shuffle seeds1301,1709, both ordinary and
recurrent, both uniform and first16 =16 fresh fits,8 matched objective pairs.
IDs i601-s1301,i601-s1709,i947-s1301,i947-s1709 are identifiers, never a single
random seed. Model/RNG setup uses ONLY initialization seed; epoch ordering uses
ONLY shuffle seed. All initialization tensor hashes are fixed from original
same-config initial states and checked before each fit. Each initialization/model
must be identical across both objectives AND both shuffle seeds. Each schedule
must be identical across initializations/objectives/models for the same shuffle.

Four NEW three-byte entity names:bek,dov,ral,sun. Values remain city la,mi,so,tu;
codes R-7,Q_2,V:4,Z!6; unknown '?'. This renaming applies to BOTH v2 train and
development. The old four entities' finite combinations are exhausted by prior
train+development, so old entities could not meet the requested fresh-combination
constraint. It changes the replication dataset versus v1 and limits direct
between-study attribution; all comparisons within v2 remain matched.

For entity index e, training has values e,e+1 mod4; development e+2,e+3, separately
for city,code,and role-with-city-query unknown cases. Train24 canonical cores x
two word-order templates x two nonce preludes=96 documents,32/category,48/template.
Dev24 fresh canonical cores,8/category,12/template, one alternating A/B template
per core. Both templates/all answer strings appear in training.31-byte nonce+
filler prelude plus BOS fills segment1; assignment/query/answer/EOS fit segment2.
New IDs v2-train-NNN,v2-dev-NNN. No same canonical tuple or prompt crosses the
split. Before fitting, compare canonical tuples against explicit permitted
local-answer-dev-v1 training/development labels and value-start-v1 development
labels; these include known diagnostic cases. New entities are disjoint, so all
development entity/value pairs and canonical tuples are fresh. Do not search or
load any held-out material. Freeze exact bytes, IDs, labels and overlap receipt.

City-shuffled schedule:128 epochs,12 batches/epoch,8 documents/batch. City slots
0,3,6,9. Shuffle city32 IDs via Random(shuffle+100000+epoch), other64 IDs via
Random(shuffle+200000+epoch); shuffle within each city batch using
Random(shuffle+300000+12*epoch+offset). Expanded1536 rows per crossed cell are
frozen; duplicated shuffle schedules must be byte-identical across initialization.
Each document appears128 times:12288 presentations,692224 valid byte/EOS targets,
786432 padded forward positions per fit. Dense8x64 batches/two32-token segments.

## Models, objective, initialization and order

Unchanged ByteTokenizer259 IDs,PAD0/BOS1/EOS2,UTF-8 byte+3,original fingerprint.
OwnedConfig context32,width16,heads4,one layer,four slots,max_document64.
ordinary_matched:width18,heads2,FFN72,14058 parameters. recurrent memory_on:
width16,heads4,FFN64,14416 parameters. Within-model paired parameters/data/work
match; between-model widths/actual compute differ. No equal-FLOPs claim.

Fresh model per fit, no prior final checkpoint initialization. CPU float32,
one Torch thread, deterministic algorithms. AdamW lr.003,betas(.9,.999),eps1e-8,
weight_decay.01,foreach=False,fused=False,clip1.0. Exactly1536 updates,full-document
BPTT,reset state per document,final checkpoint only.16 fits maximum,24576 updates
total. No weak-seed retry,resume,checkpoint selection,extra steps or examples.

H,A,F are summed history,answer/EOS,first-answer-token CE; nH,nA,nF counts.
uniform=(H+A)/(nH+nA). first16=(H+A+15F)/(nH+nA+15nF).
Thus only the first answer token has weight16; suffix and EOS remain1. Both arms
compute all partitions from the SAME logits and identical dense model work.
Actual target mass692224 versus weighted mass876544; log all target contributions,
losses,gradient norm and matched batch IDs. Unweighted full/answer/first NLL is
separate from weighted training objective and free-generation accuracy.

Order: crossed IDs in the order listed above; ordinary then recurrent within
each. For crossed-index+model-index even,uniform then first16; otherwise first16
then uniform. After each fit, one training observation. Complete all16 cells
unless integrity/resource STOP. Only then decide global development eligibility.

## Frozen scoring and gates

Original OwnedSession greedy,cap8,suppress PAD/BOS only,EOS2; fresh session per
example,continuous segmentation,no question flush. Raw native IDs saved before
scoring. Exact=gold byte IDs followed by EOS, with no trimming,insertion,answer
extraction or repairs. Report value-body-only diagnostic separately (remove one
terminal EOS for that diagnostic only),wrong first byte,EOS,malformed body outside
nine-string inventory,and one/two-ID block repeated three times. Replays retained.
Save first259-logit vectors,first-ID parity,rank,probability,margins,teacher NLL
and per-request cost for all training inputs+first replay (97 per checkpoint).

Candidate mastery: EACH of8 first16 cells96/96 exact and EOS,zero wrong first,
malformed or repetition. Control mastery is the same96 threshold,reported
separately. Development eligibility requires ALL candidate mastery plus EACH
uniform control>=90/96 exact,96 EOS,zero malformed/repetition. This inherited
control floor is NOT mastery. If global eligibility fails,development for BOTH
arms is NOT_RUN; do not open dev in an evaluation worker. Frozen dev construction,
overlap validation and byte-hash integrity are preparation, not fitted evaluation.

Training objective benefit additionally requires no paired exact regression and
positive summed exact gain; report all8 paired deltas,never aggregate alone.

Only if eligible, each checkpoint generates24 dev inputs+replay ONCE, then24
equal-width assignment-masked question-only inputs+replay ONCE. Question-only is
a neural source-dependence diagnostic against original labels,not an answerable
alternative benchmark or rule-solved control.

Every candidate dev cell must have exact>=22/24,city>=7/8,code>=7/8,unknown8/8,
EOS24/24,zero malformed/repetition,and known-fact exact gain>=8 versus its own
question-only answers. Consistent replication additionally requires EACH of8
matched pairs strictly POSITIVE full exact gain,with no city/code/unknown or EOS
regression. A tie,including a perfect control ceiling,is not evidence of positive
improvement. Thus aggregate gains cannot rescue a regressing/tied pair. Report
all cells by model,initialization,shuffle,objective; gains by both axes/model.

Gates pass=>REPLICATION_GATES_PASS (objective effect only). Training gate fails=>
STOP_TRAINING_FAILURE. Otherwise any failed development/pair gate=>
STOP_DEVELOPMENT_FAILURE. Integrity/source/seal/accounting failure=>BLOCKED,keep
all partial evidence; never repair sealed evidence. No outcome in this study
establishes a recurrent-memory,long-context,total-efficiency or chatbot advantage.

## One rehearsal, fixed caps and accounting

Plan/source/data/schedules/gates freeze BEFORE rehearsal. One disposable rehearsal,
seed902407,different random8x64 IDs,three forward/backward iterations per model/
objective,ZERO optimizer steps,unchanged weights and empty optimizer state.
It is not a scored fit and uses no study example. First iteration is cold;
B=2*max(CPU,wall over last two iterations)*1536+20 per condition.
Common cold-fit cap=max(60,10*ceil(max(B)/10)),ceiling120 seconds. If rehearsal
Job>45 CPU/wall or selected cap>120,STOP without retry or research fit. Freeze
selected cap plus prerequisite observer seals in final registration BEFORE fit1.

Other fixed caps:contracts60,preparation150,evaluation/development30,request2,
complete registered-budget1800 CPU AND wall seconds;2GiB Job commit,128MiB logical
generated output per preparation/registered branch,poll50ms,max monitoring gap5s.
No cap increase after seeing answers. Scoped tests include24 disposable native
Job tests and new numerical/data/seed/gate contracts before research fitting.

All stages use lifetime_job_v2.watch_and_seal from parent AFTER full Job closure;
workers never seal monitor logs. The registered budget encloses the run observer,
controller,nested workers and sealing; its total already includes nested costs.
Preparation/rehearsal and later audit/check Jobs are separate non-overlapping
scopes. Outermost observer CPU-to-receipt is not its complete lifetime; editing,
registration and reporting outside Jobs remain unmeasured. No total-efficiency
claim. Retain every failure,trace,raw output,checkpoint,cost,monitor and final seal.
Exclusive attempt marker and output creation prevent overwrite/retry.

Independent saved-only auditor recomputes all answers/gates from raw native IDs,
all vector measurements,all24576 steps/schedule exposures/target masses,strict
checkpoint byte hashes,seals,closed kernel costs and source preservation. Keep
audit/results outside sealed execution. Local validation is separate from hosted
CI (not invoked). No full repository research smoke or held-out evaluation.
Leave every v2 change uncommitted and do not push/deploy.
