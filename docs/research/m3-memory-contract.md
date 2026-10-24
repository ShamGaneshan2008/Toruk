# M3 proposed recurrent-memory contract (not implemented)

Historical design from the foundation audit. Subsequent M6 prerequisite work
implemented a bounded subset with explicit deviations; see
[actual M3 protocol](m3-implementation.md) and [measured results](m6-results.md).
The original design below is preserved, not claimed to be implemented verbatim.

Status: design only. The initial repository has no M1 or M2 implementation. The
current changes establish the ordinary-LM prerequisite; this document is not
evidence of recurrent-memory behavior or a completed M3.

## State and causal update

Initial configuration: 8 slots, width equal to decoder width, float32, shape
`[batch, 8, width]`. Each document begins with all-zero state. State lives only
within that document and that session. There is no archive, token buffer outside
the active segment, or growing attention cache. Storage is `batch * 8 * width * 4`
bytes, excluding parameters, current activations and optimizer state.

All decoder layers read the same **previous** segment state `M_s` through a learned
cross-attention residual after causal self-attention. Queries project normalized
decoder activations; keys and values project memory. Slots are always valid,
including initial zero slots. Decoder self-attention masks future tokens and
right padding. Padded queries do not contribute to writer summaries or loss.

Only after all logits of segment s are computed, form `h_bar`, the mean final
decoder hidden activation over valid input positions. For each slot j:

```
proposal_j = tanh(Wp @ h_bar + Up @ M_s[j] + slot_proposal_bias[j])
gate_j = sigmoid(Wg @ h_bar + Ug @ M_s[j] + slot_gate_bias[j])
M_next[j] = (1 - gate_j) * M_s[j] + gate_j * proposal_j
```

Matrices are shared across slots, biases differ per slot, and gates are
elementwise vectors of width W. No dropout initially. A fully padded lane returns
the previous memory exactly; its summary is computed with count clamped to one,
and its update selected away. Padding must have zero gradient contribution.
No in-place update of `M_s`: `M_next` is readable only in subsequent segments.

## Tokens, positions, and boundary target

Use the existing byte tokenizer. Each document is `[BOS, bytes..., EOS]`.
Input segments partition all tokens except EOS into consecutive blocks of at most
context size C. Position IDs restart at zero per segment, as in the ordinary LM.
Segment input `tokens[a:a+C]` predicts `tokens[a+1:a+C+1]`.
The **previous segment's last logit** scores the first input token of the next
segment. Its score uses only `M_s` and the previous segment's inputs. The next
segment can read `M_next` and begins by predicting its second token; it does not
rescore its first input token. Thus a boundary token is scored once, without
its own input or a state derived from that input being used to predict it.
Loss targets never enter the writer. EOS is predicted and then the lane resets.

## Data lanes and gradients

Documents are shuffled deterministically by seed and epoch, split at document
level before segmentation, then assigned to lanes. Segments within a lane arrive
in document order. On assignment of a new document, reset only that lane before
its first prediction. Never share state across lanes or dataset splits.

Initial configurable TBPTT horizon: 2 segments. Accumulate summed cross entropy
and valid-target count across a horizon, divide once, backward, check finite
loss/gradients, clip, step, then detach the resulting memory before the next
horizon. Do not step parameters inside a live unrolled graph. The second
segment's predictions must backpropagate through the first segment's writer.
A horizon of 1 cannot train this writer through subsequent predictions and must
be rejected for this baseline. End-of-document short horizons are allowed;
they provide no writer learning if only one segment remains. Reset lanes with
out-of-place operations that preserve gradients for continuing lanes.

## Streaming and checkpoints (planned)

A session owns one bounded memory tensor and one active prefix of at most C
tokens. Incremental input is ordered; recompute active-segment logits against
unchanged `M_s` as needed. Commit exactly once when C input tokens have been
consumed, after computing their logits; partial prefixes remain uncommitted.
An explicit `flush()` may commit a partial segment and starts a new segment
position convention; this differs from leaving it partial. End-of-document reset
discards any state. No KV caching in the first implementation. Full-segment and
incremental consumption agree when their commit boundaries match.

Before benchmark questions, clone both memory and any uncommitted prefix from
the same observed-history session. Each question runs in its own branch. Answers
and other questions never enter the shared observed-history state. No oracle
values or future questions initialize state. Concurrent sessions own separate
tensor storage. Report time for every history token and all writes/reads, plus
question/answer generation; compressed storage does not reduce tokens read.

First supported memory-training resume should be only at drained document-lane
boundaries, after an optimizer step and graph detach. Record model, optimizer,
scheduler (if any), tokenizer, configuration, all RNGs, dataset fingerprints,
document order/cursor and safe-boundary marker. Reject mid-document resume until
memory, per-lane document association, segment cursors and partial horizon
semantics are implemented and tested. Cross-process inference-session persistence
is not planned for M3. None of this memory-session behavior currently exists.

## Required evidence

Implement and test causality, write timing, writer/read gradients, resets, lane
and session isolation, padding invariance, fixed state capacity, commit parity,
boundary scoring and checkpoint/resume. Complete M2's independent oracle and
controlled-world validation protocol before any memory-benefit experiment.
