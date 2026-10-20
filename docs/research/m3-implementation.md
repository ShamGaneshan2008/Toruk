# Bounded recurrent prerequisite: implemented protocol

2026-10-20. This supersedes the design-only status of the earlier proposed M3
contract for the new controlled trainer. M4/M5 are not implied by this work.
The original ordinary model, trainer and checkpoint format remain available.

`RecurrentLM` reuses the causal decoder blocks and reads the same previous memory
after each complete decoder block through cross-attention. This is an explicit
change from the proposed placement between self-attention and FF; the backbone
itself is unchanged. Memory is `[batch, slots, width]`, initialized to zero per
document/session; default 4 slots, width 32, float32 = 512 bytes per lane.
Slot-specific proposal biases have small seeded random initialization to avoid
slot symmetry. A masked final-hidden mean, previous memory and separate proposal/
gate projections form the next state. Current logits never read that next state.
Fully padded lanes preserve memory exactly; padded positions contribute no writer
summary. There is no growing archive or KV cache.

Training uses one complete bounded document per optimizer step (one lane), in
seeded shuffled world order. History is segmented in order; its last partial
segment is explicitly committed before independent question branches. Positions
restart per segment. Writer gradients flow through the complete history and
question segments; the configurable maximum is 32 history segments, minimum 2.
Documents exceeding that cap are rejected. This is bounded full-document BPTT,
not the earlier proposed two-segment truncated schedule. No parameter step occurs
inside a live recurrent graph. A world is drained before a checkpoint/next step;
there is no supported mid-document resume. Multi-lane training is not implemented;
the model's batch isolation and padded-lane behavior are tested separately.

The target convention is one shifted score per observed-history byte after BOS;
the last observed byte has no history target. Question-prefix targets are masked,
and every answer byte/newline is scored exactly once from preceding inputs.
The history last logit is not used to score a question's first byte; question
text is conditioning, not an answer target. Each question starts from a clone
of the same history state, preventing answers/questions from contaminating other
probes. Ordinary QA training uses exactly the same histories/questions/answers,
but computes answer logits with its rolling local context. It does not inherit
the recurrent state or extra runtime data. Loss is mean answer-token CE plus
0.1 times mean history-token CE, fixed before validation. This baseline is
trained on all six query categories; no revision-specific objective exists yet.

The comparison matches worlds, probes, tokenizer, initialization seed, optimizer
steps and loss weights. It does NOT match parameters or FLOPs: readers/writer add
parameters, and the ordinary rolling-answer computation processes more token
positions. Both actual parameter counts and forwarded token positions are
reported. They must not be described as an M6 matched-resource comparison.

Checkpoints include model/optimizer, configurations, absolute next step, Python/
Torch RNG, tokenizer, combined data/manifest fingerprints, code fingerprint and
drained-document marker. Resume rejects configuration/data/code/format/boundary
changes. The same-runtime CPU test compares model/optimizer/RNG bitwise. CUDA
training and cross-process inference-session persistence are unsupported.

`Session` owns its memory and active segment, commits once when full, supports
explicit partial flush, clone and reset. Each generation call receives only
question tokens, never gold answers. Session/full-segment parity is tested in
the same no-grad evaluation context (Torch may choose different MHA kernels
in grad versus no-grad mode). Bounded state storage is not tokens read.

Validation compares first-line greedy generated answers separately from teacher-
forced answer/history loss. The final test loader is not exposed by this CLI.
Inference timing includes history processing and question generation, excluding
model load and offline answer scoring; model-forward token counts are retained.
CPU peak memory remains uninstrumented. Tiny runs can establish execution and
gradient correctness but cannot demonstrate useful delayed memory or M6 readiness.

Reproduction, with frozen worlds from `make-worlds` and fresh output paths:

```powershell
python -m toruk_lm train-controlled --train DATA/train.jsonl --validation DATA/validation.jsonl --variant ordinary --output RUN/ordinary --steps 12
python -m toruk_lm train-controlled --train DATA/train.jsonl --validation DATA/validation.jsonl --variant recurrent --output RUN/recurrent --steps 12
python -m toruk_lm evaluate-controlled --checkpoint RUN/ordinary/checkpoint.pt --data DATA/validation.jsonl --output RUN/ordinary-eval
python -m toruk_lm evaluate-controlled --checkpoint RUN/recurrent/checkpoint.pt --data DATA/validation.jsonl --output RUN/recurrent-eval
```

These are prerequisite smoke comparisons. A useful-memory claim requires
longer, independently budgeted validation learning curves and reset/heuristic
diagnostics; M4 then requires its own paired-label and predictor gate.
