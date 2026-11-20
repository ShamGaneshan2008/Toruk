# Answer trainability development v1: pre-training protocol

20 November 2026. New development-only study; does not revise segment-delta-v1.
Question: can the existing ordinary and recurrent Toruk byte LMs learn a complete
answer ending in EOS? No delta model, memory-mechanism comparison, held-out cases,
production chat, external model, downloads, deployment, or architecture claim.
Diagnosis record: `39c4e4756b24ca3d09c4a9aa8ae63b1a2b5ab208`.

## Freeze and single-use execution

Before any study fitting or answers, freeze this document, executable sources,
focused contract-test receipt, data files, runtime, model/optimizer settings,
order, thresholds and caps in `artifacts/answer-trainability-dev-v1/registration.json`.
Copy exact source bytes into `sources/`; seal all files with SHA256. Creation is
exclusive; `run-start.json` prohibits another run. No retry, sweep, checkpoint
selection, early success stopping, budget increase, or post-answer repair under
this version. Every attempted stage retains stdout, traces, cost and any partial
outputs. An integrity/resource failure stops immediately. Numerical model and
gradient fixture tests before freeze use no study documents, optimizer updates,
or generated study answers. Static data checks validate the declared splits.
Record preparation, tests, execution and later checks separately.

## Fixed data, tokenizer and local placement

Eight training documents only, then sixteen separate development documents.
Training: four city answers (`la`, `mi`, `so`, `tu`), two code answers (`R-7`,
`Q_2`), two unknowns (`?`). Development: eight city, four code, four unknown.
Names are `uvo`, `pex`, `zim`, `nax`; development recombines names and city/code
values, with every answer string represented in training. Exact example lists
are literals in the frozen generator; no random search or v1 data is an input.
IDs, full texts, and assignment/query cores are disjoint between the splits.
This is tiny synthetic IID recombination, not broad generalization.

Each document has a 31-byte irrelevant prelude ending in newline, then exactly
one assignment and one question. BOS plus prelude occupies the first32-ID
segment. The entire assignment, query, answer and EOS fit in the second segment.
Thus ordinary has the complete needed local context and recurrent has an active
read/write path from the first segment; no long-distance retention is required.
Known example core: `uvo city=la\nuvo city?=la`; unknown core supplies a `role`
assignment and asks for `city`, so the answer is `?`. Split-specific prelude
nonces are also disjoint. An independent last-assignment validator checks gold,
separation, bounds, category balance and local placement before freeze.

Unchanged `toruk-utf8-byte-v1`: PAD0/BOS1/EOS2, byte+3,259 IDs, no vocabulary
training. Complete documents are BOS + prefix + gold bytes + EOS. Each non-BOS
token is a next-token target exactly once. Training sees only training documents.
Generation inputs and evaluator-only labels are stored separately. Development
is frozen before training but is never evaluated before the training-only gate.

## Models, objectives and matched exposure

Use the existing `OwnedConfig(context=32,width=16,heads=4,layers=1,slots=4,
max_document_tokens=64)` factory without changing any existing implementation.
Ordinary is `ordinary_matched`: CausalLM width18,heads2,one layer,FFN72,
14,058 parameters. Recurrent is `memory_on`: OwnedMemoryLM width16,heads4,
one layer,FFN64,four slots,14,416 parameters,256-byte state. Parameter ratio
1.0255; widths differ, so this cannot isolate an architectural advantage.

Two objectives, applied identically to both models:

1. `uniform`: current full-document token-normalized CE, all target weights1.
2. `answer16`: identical CE with only gold answer bytes **and EOS** weighted16;
   all pre-answer targets retain weight1. No other supervision change.

For a batch with history and answer loss sums H and A and target counts Nh/Na,
the objective is `(H + w*A)/(Nh + w*Na)`, w=1 or16. No answer offset changes a
forward computation or inference input. Padding has no loss/weight. The
denominator is the actual batch's weighted target count, not number of documents.
Report raw token counts, weighted shares, unweighted loss sums, weighted
contributions and per-target losses/gradient norms at every step.

For actual parameter-gradient attribution, differentiate `H/D` and `w*A/D`
separately on the same graph; set the optimizer gradient to their sum. Save each
partition's L2 norm, dot product, combined pre-clip norm and projection onto the
combined gradient. Norms need not add; projections may be negative. Also save
each target's actual weighted logit-gradient L2 norm from CE probabilities.
These measurements distinguish weight mass from realized loss and gradients.
No claim that gradient norm is an additive percentage of learning.

Fresh initialization, seeds419/733. For a given seed and model, the objectives
start with byte-identical weights; model widths prevent identical initialization
across models. Float32 CPU, one Torch thread, deterministic algorithms, no
dropout. Every fit: exactly512 AdamW updates, batch4 complete documents, lr.003,
betas(.9,.999),eps1e-8,weight_decay.01,foreach=False,fused=False,clip norm1.0.
Epoch-shuffled order uses `random.Random(seed+epoch)`; all models/objectives
receive identical ordered documents for each seed. All8 documents appear256
times:2,048 presentations per fit. Same targets, forward positions, optimizer
steps, gradient instrumentation and final-checkpoint policy; measured compute
is reported rather than claimed equal. No state detach; reset between documents.
No pretraining or old checkpoint inputs. Final optimizer boundary only, in a new
strict format; retain optimizer, configuration, identities, initial weight hash,
progress and RNG, and hash the checkpoint bytes. No resume or intermediate pick.

Fit/generate/loss order (complete one training cell and its training-only check
before the next): seed419 uniform ordinary/recurrent, answer16 ordinary/recurrent;
seed733 answer16 recurrent/ordinary, uniform recurrent/ordinary. All eight fits
complete unless an integrity/resource error occurs. There is no quality-driven
retry. A failing cell does not cancel its predeclared matched comparisons.

## Training gate, development gate and stop decisions

After each final checkpoint, greedily generate all8 training prefixes and replay
the first once; save raw IDs before an evaluator opens labels and computes
losses. An objective passes the tiny-overfit prerequisite only if **both models
at both seeds** score8/8 exact, hence EOS-complete and correctly framed. If
neither objective passes, STOP: no development generation or loss evaluation.
Passing of only answer16 while uniform fails is allowed evidence about the
supervision hypothesis; it is not a reason to extend uniform training.

Only after the eight fixed training cells and gate receipt are saved, evaluate
the sixteen frozen development inputs for every cell of each passing objective,
using its same final tiny-training checkpoint with no further fitting. Do not
evaluate cells of a failing objective. Record this selection and avoid an
unmatched development comparison. Development success for an objective requires
at every model/seed: all16 outputs end in EOS and are complete members of the
answer inventory, >=12/16 exact, >=6/8 city, >=3/4 code, >=3/4 unknown. These are
pragmatic feasibility thresholds, not significance tests.

If the tiny gate passes but development fails, report a **generalization
failure** under this setup. If a development gate passes, the sole conclusion
is that complete answers are learnable on this narrow development task; only a
later separately registered study may compare memory mechanisms. No architecture
advantage is supported by this experiment in any outcome.

## Inference, exact scorer and metrics

Use existing `OwnedSession` for both models, identical continuous segment schedule,
no question flush. Greedy argmax, suppress PAD/BOS only, EOS eligible, cap8 new
IDs. Report existing session work counts (it consumes the last non-EOS generated
ID even at the cap). Scorer is exact equality to UTF-8 gold bytes+3 followed by
EOS. No trimming, normalization, answer extraction, forced tokens, EOS insertion,
or relaxed acceptance. Each generation worker reads prefixes only; the later
scoring phase reads labels and saved raw predictions. Replay equality includes
IDs and work counts, excluding measured request times.

Save every continuation including replay, native prompt IDs, budget exhaustion,
warm CPU/wall and work. A malformed output is not exactly one of the seven
declared answer strings followed by EOS, independently of whether its value is
correct for that case. Repetition is a separate flag: any contiguous one- or
two-ID block repeated at least three consecutive times. EOS completion includes
EOS-only output, which is also malformed. Report per-case/category exact,
EOS completion, malformed/repetitive counts, and train/dev full/history/answer
NLL including answer EOS. Losses are teacher-forced, separate from generated
accuracy. Report cold training, cold generation and cold scoring CPU/wall,
warm request CPU/wall, optimizer-loop costs and OS/sampled peak private memory.

## Fixed resource caps and accounting

No rehearsal fit. Per cold fit180 CPU and wall seconds. Per cold generation or
loss worker20 CPU/wall seconds; each request/loss document2 seconds. Contracts60,
preparation30, controller overhead60. Overall registered run2,400 CPU and wall
seconds. Private process-tree memory2GiB, logical study disk256MiB,50ms sampling,
maximum monitor gap5 seconds. Existing Windows process-tree watcher enforces
these without modification. An enclosing watcher measures the complete run
controller/tree once; nested stages are its subsets, not additive charges.
Controller also enforces its60-second own-CPU/active-overhead budget.

Up to8 fits,8 training generation workers,8 training scoring workers, then up
to8 development generation/scoring workers each. Training requests9 per cell;
development17 per eligible cell. Maximum72 training +136 development =208
requests,192 scored cases. No lexical control or ablations. Cold setup/checkpoint
loading is included. Preparation/contracts and later repository checks are
separately measured and reported; uninstrumented design/editing/review time is
unknown, not free. Raw memory measurements are distinct from neural state size.

The single-use controller, exact frozen data, test receipt and hashes constitute
the reproducible protocol. Re-running the study under this registration is
forbidden; read-only audit is repeatable. Leave all new study changes uncommitted.
