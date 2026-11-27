# Local-answer entity dropout dev v1 — frozen prospective design

26 November 2026. Development only. One intervention: replace both three-byte
entity mentions by `ref` in exactly half of each training document's 128 scheduled
presentations. No evaluation transformation. Uniform loss in BOTH arms. Zero
change to production chat, historical protocols/scores, optimizer or decoding.
This is a local-answer shortcut hypothesis test, not a memory comparison.

## Evidence before model work

The saved-only diagnosis independently audits crossed value-start v2: measurement
integrity PASS, training mastery 96/96 in all16 cells, reliability FAIL. All34 dev
errors have wrong first argmax/rank>1/negative gold-top margin;22 return an entity's
training value. Five are malformed,one lacks EOS,none repeats under the original
definition. Templates A/B have21/13 failures,not proof of a template cause.
No correct complete answer was rejected. Per-case inputs/raw IDs/margins and all
three v2 tied/regressing pairs are retained separately before any forward here.
This measures the token choices,not how training caused them.

Hypothesis: entity/value correlations permit shortcuts; partial entity dropout
reduces reliance on them while retaining named-entity training exposures. The
intervention does not repair inference,EOS logic or scoring. Falsification within
this budget: failure of original-input training mastery,any non-ceiling pair
without positive dev gain,any paired regression,remaining candidate floor/format/
EOS failures,or failure to reduce recurrent601 city first-token NLL in BOTH
shuffle seeds. An accuracy change alone cannot establish the causal mechanism.

## Frozen cases, controls and independent seeds

Exactly the original v2 train96 and dev24 inputs/labels/documents, byte copied
under new paths and hash bound; same 24 distinct dev cases,not new validation.
The cases were previously diagnosed: results are adaptive development evidence.
No held-out case is opened or evaluated. No claim of untouched generalization.
Same two templates,nonce preludes,all values and unknown cases. Original train
canonical tuples are disjoint from dev. Dropout introduces only entity `ref`,
never a development entity/value tuple. Query field,value,answer,delimiter and
all byte lengths/target masks stay unchanged. `ref` must be absent from originals.

Initialization601/947 CROSS shuffle1301/1709,ordinary/recurrent,uniform/drop50:
16 fresh fits,8 matched pairs. Same city-shuffled1536 batch rows,8 records per
batch. For original document index d and epoch e,replace entities iff
`(d+e)%2==0` in drop50; uniform uses originals. Each ID has64 original+64 anonymous
presentations. Materialize both views and entire schedules before training.
All histories and answers stay in original order; replacements consume no RNG.
Fresh uniform controls must exactly reproduce v2 final tensor hashes and all
native train/dev predictions; otherwise integrity BLOCKED,not scientific failure.
No saved final weights initialize a research fit. Historical controls are also
reported,not silently substituted for a failed fresh control.

Same ByteTokenizer259,byte+3,PAD0/BOS1/EOS2,context32,max_document64; ordinary
width18/heads2/FFN72/14058 parameters; recurrent16/4/64/14416. CPU float32,
deterministic algorithms,one Torch thread. Same initial hashes as v2; runtime
identity pinned.1536 updates/fit,128 epochs,12288 document presentations,
692224 valid targets,786432 padded forward positions per cell. Uniform CE of
all valid history+answer/EOS targets; no first-token weighting. Same AdamW
lr.003,betas(.9,.999),eps1e-8,weight_decay.01,foreach=False,fused=False,clip1.
No extra examples,steps,resume,selection or weak-cell retry. V2 balanced execution
order with `first16` renamed `drop50`. Final checkpoint only,all partials retained.

## Measurements and gates

Unchanged greedy OwnedSession,cap8,suppress only PAD/BOS,EOS2,fresh session per
request,continuous segmentation. Raw native IDs saved before exact scoring.
No trimming,EOS insertion,answer repair or constrained answer vocabulary.
Save train96+replay,dev24+replay,dev question-only24+replay,first259-logit vectors,
rank/probability/margin/argmax parity,per-case unweighted teacher full/answer/first
NLL,exact/category/EOS/malformed/repetition,training trace and gradient norms.
Save every request CPU/wall,input and generated token count,forward positions;
training loop and complete kernel process-tree CPU/wall/peak memory/disk/gaps.

Global training gate before any fitted development read: ALL16 cells must attain
96/96 exact and EOS on original named training inputs,zero wrong-first,malformed
and repetition. Complete all16 train cells unless integrity/resource STOP. A
training gate failure means development NOT_RUN for both arms;save STOP.

Candidate dev EACH8:exact>=22/24,city>=7/8,code>=7/8,unknown8/8,EOS24/24,
zero malformed/repetition,known-context exact gain>=8 versus question-only.
No paired exact/category/EOS regression;zero added malformed/repetition.
EVERY non-ceiling uniform control(<24) must have positive candidate exact gain;
perfect-control ties are allowed and explicitly not evidence of improvement.
Positive total exact gain in BOTH model types. Additionally recurrent601 city
first-token teacher NLL must fall versus uniform under BOTH shuffle seeds.
The ceiling rule is new and prospective: v2's strict-positive-all8 gate remains
FAILED unchanged. No aggregate can rescue a regression/floor or mechanism failure.
PASS=>DEVELOPMENT_GATES_PASS;train failure=>STOP_TRAINING_FAILURE;otherwise
STOP_DEVELOPMENT_FAILURE;integrity/resource failure=>BLOCKED. No memory advantage.

## Fixed caps, one rehearsal and accounting

Design/data/source hashes freeze before rehearsal;registration binds successful
contracts/rehearsal seals BEFORE fit1. One random-data rehearsal(seed918733),
three forward/backward iterations/model,ZERO optimizer updates,no study examples.
Reject if `2*max(last-two CPU/wall)*1536+20>90` for either model. Never increase
the fixed caps after rehearsal or outputs. Rehearsal45 CPU/wall;each fit90,
each train/dev observation40,each request2;entire registered experiment1800 CPU
AND wall seconds,2GiB Job commit,128MiB output,max monitor gap5s,poll50ms.
Contracts60;preparation180. If prerequisite/cap/accounting/source failure,STOP
without retry;save partial outputs and closed accounting receipts.

Use unchanged lifetime_job_v2 observer-owned seals AFTER process-tree closure.
Outer registered budget encloses the study observer/controller/all workers and
sealing. Its lifetime includes nested stages;do not add stage costs twice.
Preparation/contracts/rehearsal,saved diagnosis,final audit/checks are separate
scopes;unmeasured editing/registration/reporting costs remain unknown. No complete
project-efficiency claim. Persist exclusive attempt marker,all request/trace
streams,failed attempts,raw outputs,checkpoints and final receipts/seals. No
worker seals its own monitor. Scientific outputs are never overwritten.

Offline auditor rechecks independent native scores,all vectors/ranks/margins,
tokens and targets,schedules/dropout exposures,control parity,source/checkpoint
hashes,all nested/root seals and complete costs. Focused tests,lint/format,types,
frozen evidence and diff checks are reported separately from hosted CI. No commit,
pull,reset,push,deploy or change to any earlier scientific gate or payload.
