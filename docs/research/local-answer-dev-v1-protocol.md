# Local answer development v1: pre-training registration

20 November 2026. Development only. New registration; does not revise or repair
the frozen answer-trainability-v1 record committed at
`301dd9edbf12403aa97e5013247d5b1f33be0746`. Uniform next-token training is the only
condition. No answer16 selection, long-history test, memory advantage, held-out
cases, production-chat change, deployment or push.

## Question and fixed design

Can ordinary and recurrent Toruk LMs answer fresh local entity/value combinations
after each entity has appeared with multiple training values? The saved v1
diagnosis finds68 closed wrong values, four closed malformed answers and seven
EOS failures among128 development predictions;58 failures match a training
question's known answer. That motivates varied entity/value coverage rather
than selection of a favorable weighted-objective cell.

Fixed names `uvo,pex,zim,nax`; city values `la,mi,so,tu`; codes `R-7,Q_2,V:4,Z!6`.
For entity index e, train on value indices e and e+1 modulo4; development uses
e+2 and e+3. Apply this rotation independently to city/code assignments and to
role assignments queried for the absent city. Every answer string occurs in
training. Each entity has two city and two code values in training; finite
vocabularies remain shared. No split is a held-out evaluation split.

Train24 canonical assignment/query cores, two templates and two prelude variants
per core =96 full documents. Development24 fresh canonical combinations, one
template per core, alternating A/B within each entity/category pair. Development
has8 city,8 code,8 unknown, balanced12 cases per template. Train has32 per
category and48 per template. A is `uvo city=la\nuvo city?=la`; B swaps word order
in both lines: `city uvo=la\ncity uvo?=la`. Unknown supplies role and asks city.
Both templates and every query entity/attribute occur in training. No new syntax
is introduced only at development. Exact lists/generator and hashes are frozen.

A31-byte nonce/filler prelude plus BOS exactly occupies segment one. Assignment,
query, answer and EOS fit together in segment two (context32); irrelevant prelude
is not required to answer. IDs/full prompts/canonical entity-source-field-value-
query-field tuples are split-disjoint. Independent last-assignment validation
checks authored gold, categories, template balance, coverage and local placement.
Maximum64 next-token targets. Separate generation-prefix and evaluator-label
files; no labels are opened by generation. No v1 documents/checkpoints are inputs.

## Frozen models, exposure and inference

Unchanged259-ID UTF-8 byte tokenizer, PAD0/BOS1/EOS2, byte+3, fingerprint bound.
Existing OwnedConfig context32,width16,heads4,one layer,four slots,max_document64.
Ordinary `ordinary_matched`: width18,heads2,FFN72,14,058 parameters; recurrent
`memory_on`: width16,heads4,FFN64,14,416 parameters,256-byte state. Within3% budget;
different widths/actual compute forbid isolating architecture as a causal factor.

Fresh seeds601/947; no old weights. Float32 deterministic CPU, one Torch thread.
Exactly1,536 AdamW updates per fit, batch8, lr.003,betas(.9,.999),eps1e-8,
weight_decay.01,foreach=False,fused=False,clip1.0. Uniform token-normalized CE
including EOS, no answer weighting. Full-document BPTT, reset state per document.
Every document appears128 times:12,288 presentations; canonical cores appear512
times across the two templates/preludes. Epoch shuffle Random(seed+epoch);
same ordered examples, steps, targets and padded forward positions per seed for
both models. Record actual compute and H/A loss sums, targets and gradient norm.
Final checkpoint only; no early stopping/selection, fit retries or budget changes.

Fit order601 ordinary/recurrent,947 recurrent/ordinary. After each fit, generate
all96 training inputs plus first-case replay, then separately teacher-force
losses. All four fits complete unless cap/integrity failure. Tiny-v1 is not rerun.
Development is permitted only if each cell has>=90/96 training exact,96/96 EOS
and zero malformed outputs. Otherwise record training failure and stop before
development. No extra training buys a pass.

Greedy existing OwnedSession for both models, cap8, suppress PAD/BOS only,
continuous segment schedule without question flush. Exact scorer: native IDs
equal gold UTF-8 bytes+3 then EOS. No trimming, insertion, extraction or repair.
Generation saves raw native IDs and every continuation, including EOS/cap status,
before any label file is opened for scoring. Score full/history/answer NLL with
EOS teacher-forced; keep it separate from free-generation accuracy.

## Local-context controls and fixed gates

After the training gate, evaluate all24 development cases and first-case replay
per cell; then a question-only diagnostic for each same checkpoint. That control
replaces the complete assignment line with equal-width dots, preserves the
question/prelude/positions, and compares against ORIGINAL labels to measure loss
of factual accuracy. It is not scored as a newly answerable task or mixed into
main scores. No fitted control, question flush, memory ablation or old data.

Two separate deterministic controls receive original prefix only: last matching
assignment parser (otherwise `?`), and most frequent training answer by question
(ties lexical). Both explicitly construct output IDs/EOS and are reported as
handwritten controls, never as learned LM successes. Parser must get24/24.
Question-only accuracy, EOS, malformed flags and raw outputs are retained.

For EACH model at EACH seed, all main development requirements must hold:

1. >=22/24 exact; >=7/8 city,>=7/8 code,8/8 unknown.
2.24/24 EOS, zero malformed outputs (closed answer from the nine-string inventory).
3. On16 known cases, >=8 more exact than its question-only diagnostic.
4. Deterministic source parser24/24; all seals, counts, replay and resource checks pass.

All four cells must pass for local answering to be ready for a separately
registered memory comparison. These are small development feasibility gates,
not significance tests. A failed generalization gate means a specific new
training design or stopping under this budget, never an architecture advantage.
Repetitive flag independently means one/two-ID block repeated three times.

## Accounting engineering prerequisite and numeric rehearsal

Use NEW `scripts/lifetime_job.py`; leave v1 controller/watcher and receipts alone.
Create each Windows process suspended, assign it to a kernel Job before resume,
wait for ActiveProcesses=0, query final Job user+kernel CPU and peak committed
private memory, then close handles. Descendant CPU remains available after exit.
All cooperative controllers write status in finally as an additional diagnostic;
kernel accounting also covers abrupt exits without that file. Failure, cap kill
and KeyboardInterrupt terminate/drain descendants and retain final accounting.

Before registration, real process tests must pass for successful controller,
failed/interrupting controller, os._exit, observer interruption, cap kill, and
child outliving parent with coarse sampling. No study fitting before these pass.
Complete lifetime scope is the workload Job, including controller, workers and
inner observers. The OUTERMOST measurement observer is outside the Job and its
CPU-to-receipt snapshot is reported separately, never added as a complete
observer lifetime or counted twice. Design/analysis outside the Job is unknown.

One numeric rehearsal, seed900301, three maximum8x64 random-token forward/
backward passes per model, no optimizer updates, no study documents/answers.
Construct AdamW for setup but do not step. First pass is setup; last two establish
steady iteration bound. Every pass/cold cost retained. Require finite gradients,
complete Job accounting, cold rehearsal<=30 CPU/wall seconds and2GiB memory,
and `2*max(last_two_iteration_CPU_or_wall)*1536 +10 <=120` seconds for BOTH
models. This conservative projection includes fixed setup/optimizer/trace margin.
If it fails, STOP without training; no increasing caps or alternate rehearsal
under this version. Rehearsal CPU and failed attempts stay in the ledger.

## Fixed caps, seals, execution and decision

Cold fit120 CPU AND wall seconds; generation/loss20 each; request/loss document2.
Contracts30, freeze20, deterministic controls10. Complete registered run1,000
CPU/wall seconds, workload Job private memory2GiB, logical run disk128MiB,
sampling50ms with maximum gap5s. Stop immediately on cap/integrity error. Kernel
memory limit and kill-on-Job-close apply. No cap or source/gate repairs after
fits. Resource observations and failed stages survive interruptions.

Freeze this document, source snapshots, all data, tokenizer/config/runtime,
seeds/order/steps, scoring/gates, accounting-test and rehearsal cost/summary
hashes into `artifacts/local-answer-dev-v1/registration.json` BEFORE training.
Exclusive run-start marker prohibits repetition. Each worker verifies seals;
each stage's complete Job costs are subsets of the enclosing complete Job and
are not summed with it. OS lifetime CPU supersedes sampling estimates; no
controller self-report is used to close CPU accounting.

Maximum requests:4x97 training +4x25 main +4x25 question-only +2x24 deterministic
=636 saved continuations,624 scored rows (replays excluded). Record all costs,
raw native prompts/continuations, training trace, checkpoint/hash, EOS/malformed/
repetitive metrics and losses. Preparation, tests, rehearsal and later checks
are separate measured scopes. Report final Git state; leave new work uncommitted.
No held-out data, production change, push or deployment in any outcome.
