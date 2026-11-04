# Toruk-owned next-token LM v1 — frozen technical design

Version: `toruk-owned-next-token-v1`, 4 November 2026. This is a small CPU
language-model path, not a pretrained chatbot or a claim of a new memory algorithm.
The existing recurrent core already reads learned state into token logits. The
smallest complete implementation will reuse that architecture and supply ordinary
next-token training, explicit boundaries, safe resume and architectural comparisons.

## Prerequisite and lineage

The ordinary CausalLM, RecurrentLM, conditional IntegratedMemoryLM/PooledRouterLM,
chat selector, Qwen backbone, long-gap evaluation and independent replication
exist. The latest owned-model replays initially fail only on drifted registered
`pyproject.toml`. The archived metadata restores all strict checks in an isolated
copy: 2,304 routing and 1,920 development answers reproduce exactly, retaining
their failed quality gates. No original files or seals are changed. The latest
chat replication is separately replayed and remains a prerequisite audit, not
training data or an architecture baseline for this model.

## Embeddings, decoder and direct memory read

Use the fixed 259-token UTF-8 ByteTokenizer (PAD/BOS/EOS = 0/1/2), learned token
and segment-position embeddings, and the existing pre-norm causal transformer
decoder: width 32, two layers, four heads, GELU MLP, zero dropout, untied output
projection. Local segment context is **32 tokens**. Attention masks forbid future
tokens and padded keys. Final layer normalization feeds next-token logits.

Reuse RecurrentLM's four dense 32-float slots and per-layer normalized
cross-attention. The read vector is added to current hidden states before the
next-token output projection; it is not a text selector or external model prompt.
The full-mode implementation must match existing RecurrentLM numerically with
identical weights. Explicit read/commit switches expose real ablations without
altering the historical recurrent source or checkpoints.

## Persistent state, update and boundaries

State begins as zeros for each new document/conversation. After current-segment
logits, the masked mean of final hidden states is joined with each old slot.
Shared linear proposal/tanh and sigmoid gates, plus existing learned slot
offsets, produce the convex gated update. The update cannot change logits of the
segment just scored. From zero initialization state remains bounded in [-1,1].
State is `[1,4,32]` float32: **512 tensor bytes**, independent of document length.
Inference additionally stores at most 32 local token IDs and last logits; Python
objects and model/optimizer/training graphs are outside that tensor bound.

No tensor state, local tokens, gradients or question output cross an unrelated
document boundary. Each document loss and each independent evaluation question
starts a new session. Explicit session reset and cloning support streaming tests.
Only trained parameters and optimizer/RNG/data-progress state cross training
batches. Questions cannot borrow generated answers from another evaluation case.

## Objective and gradient path

Train from scratch on **all next-token targets** in each document, including EOS,
not only answer spans. No slot-address labels, evidence labels, symbolic parser,
pretrained embeddings or answer lookup are used. Shift targets once; score each
non-BOS target once, including the first token of each subsequent segment.
Normalize each optimizer batch by its actual valid-target count.

Keep the graph through memory updates across the entire bounded document
(at most **384 input/target positions**, twelve segments). Do not detach state
within a document. Backpropagate once per batch of complete independent documents,
then discard all document graphs. This is bounded full-document BPTT, not
unbounded streaming training. The writer receives gradients through later
segments' token predictions. Tests must demonstrate nonzero writer and reader
gradients and changed token logits when earlier state changes.

## Checkpoints, training and inference

Use a distinct `toruk-owned-next-token-v1` checkpoint type and validate tokenizer,
model/train config, runtime identity, finite weights, optimizer/RNG state and
data fingerprints. Save only after an optimizer step over complete documents;
no recurrent mid-document checkpoint is supported. Save model, AdamW state,
Python/Torch CPU RNG and deterministic next-step/document cursor atomically.
Resume into a fresh output directory and reject changed input bytes or settings.
Old ordinary, controlled, integrated and pooled checkpoints must fail clearly in
the new loader; existing loaders must continue to reject this new format.

The experimental CLI trains, evaluates and generates under this identity. It
does not change any browser/server backbone or existing BASELINE/TORUK selector.
Generation is greedy with PAD/BOS suppressed, EOS stopping and a 16-token cap.
The recurrent and memory-disabled controls use the same segment-aligned runtime.
The ordinary baseline also reports its **existing rolling-context generator**
as a stronger diagnostic, so gains cannot be attributed silently to resetting
the ordinary local window at segment boundaries. All forwarded positions and
history-ingestion costs are recorded.

## Parameter/cost budget and comparisons

Planned allocated counts (validated against actual modules before training):

- A: existing ordinary width-32 decoder, **43,072 parameters**, no state.
- B: the recurrent allocation with read and update disabled, **56,064**, effective
  token path equal to the width-32 ordinary decoder; memory weights inactive.
- C: memory enabled, **56,064**, 512 state tensor bytes.
- Parameter-matched ordinary diagnostic: width 38, two heads, two layers,
  **56,620 parameters**, within 1% of C, same 32-token context.

All fit variants consume the same ordered training documents, target tokens,
optimizer batches, two training seeds (31/47), AdamW 0.003 and **256 steps** with
two documents per step. Maximum is 1,572,864 training target positions across
eight fits, plus bounded profiling/verification separately. One CPU thread,
float32, deterministic algorithms; a 600-second study cap and explicit step/
document/model-size limits prevent unbounded training. A two-step profile on
training examples estimates cost before the registered study, without opening
heldout results. Token matching is exact; effective capacity and FLOPs are not
identical. Report actual parameters, active gradients, times, work and memory.

Evaluate C with read removed and update commits removed separately, using the
same frozen C checkpoint. These are distribution-shift ablations, not separately
trained equal-capacity models. B is separately trained without memory. Do not
invent learned routing, protected revision or semantic compression.

## Data and heldout criterion

Create new bounded document worlds in six categories: distant recall, correction,
preservation, exact strings, local control and absent evidence. Text contains
records, distractions, one question and its continuation answer. Train/dev/heldout
use seeds 3201/4201/5201, disjoint IDs and full document texts; the finite entity,
value and grammar inventory is shared. This is an IID synthetic capacity study,
not unseen-template, unseen-entity or natural-conversation generalization.

Use 32/4/8 cases per category for train/dev/heldout. Reference answers are never
passed to generation; teacher-forced loss is separate from free generation.
Open heldout only after all fits and development evaluations are frozen. No
heldout-driven budget extensions or retries. The CPU smoke uses two steps, one
seed and tiny separate fixture counts; it cannot pass a research quality gate.

Predeclared research success: at both training seeds, C must improve heldout byte/
EOS NLL by at least **0.05 nats** over A and B, and improve distant-recall plus
correction exact accuracy by **10 percentage points** over both; correction and
preservation must not regress, and unsupported absent-evidence answers must not
increase. It must also beat the parameter-matched ordinary diagnostic on those
NLL/accuracy conditions. Removing either memory read or update must worsen C's
NLL by at least **0.01 nats** on average across seeds. Every condition is required.
Always report exact copying, invalid/empty outputs, stale corrections, generation
budget exhaustion, training/inference cost and peak memory, even if all gates fail.

Separately, the engineering identity gate requires direct state-to-logit effects,
cross-update gradients, deterministic replay/resume, explicit reset and bounded
generation. Passing that gate supports calling this a Toruk-owned experimental
LM; it does **not** imply useful factual memory or readiness for conversation.

Future work, not implemented here: natural-dialogue pretraining, persistent
cross-document user memory, learned fact routing, protected correction, semantic
compression, KV caching, GPU training and a qualified conversational product.
