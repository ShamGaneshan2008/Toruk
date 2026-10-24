# Current implementation

Toruk-LM is the model family; `toruk_lm` is the package. The ordinary decoder uses
learned byte/position embeddings, pre-norm causal self-attention and a GELU MLP
per layer, final normalization, and an untied output projection. Dropout is zero.
The ordinary variant has no memory. The additional controlled/recurrent research
pipeline is documented in [M3 implementation](research/m3-implementation.md) and
[M4–M6 protocol](research/m6-validation-protocol.md). Protected revisions do not exist.

ByteTokenizer has PAD=0, BOS=1, EOS=2, UTF-8 byte b mapped to b+3. Its immutable
identity/fingerprint is recorded in checkpoints. Padding is right-only; fully
padded examples are rejected. Attention excludes padded keys and future tokens;
cross entropy ignores targets -100. Loss normalization counts valid targets.

Each document is encoded independently, then partitioned into input windows of
at most C tokens, excluding final EOS. Targets are shifted once by the loader.
The previous window's final logit scores the next window's first input token.
That token is not scored again. Windows restart positional embeddings at zero.
Training windows shuffle with seed+epoch, deterministically; the ordinary model
has no state between windows. Validation uses ordered document windows and the
same context limit. This reports nonoverlapping-window byte/EOS loss, not the
loss of a full rolling context at every position.

Greedy generation recomputes the last at most C tokens on every step with
positions restarted at zero. BOS/PAD are suppressed in sampling; EOS stops.
There is no cache or streaming memory session. Calls do not mutate document
state. Evaluation separates teacher-forced text loss from generated text
continuations. Continuations are not factual QA and have no accuracy claim.

Training is float32 CPU AdamW, fixed LR, deterministic algorithms, one CPU thread
by default. Finite loss and gradients are mandatory. Checkpoints save completed
optimizer boundaries atomically with model, optimizer, scheduler=None, Python and
CPU Torch RNG states, configurations, tokenizer hash, train/validation hashes,
and next-step/example cursor. No CUDA training is supported in this stage.
Resume reconstructs the same deterministic window ordering and rejects changed
configuration/data/tokenizer/format. Exact continuation is tested on this CPU
runtime; cross-version/platform bitwise reproducibility is not promised.
No mid-update or recurrent mid-document resume contract is supported.

Data generation writes all three splits and their fingerprints without fitting
the tokenizer. The pilot consumes train/validation only; the final test split is
never loaded for scoring. The generator is a small prose fixture, not M2's
controlled-world generator/oracle. Train rejects overlapping IDs and identical
train/validation text. Generated fixture IDs across all splits are tested disjoint.

The proposed future memory design is in [research/m3-memory-contract.md](research/m3-memory-contract.md).

The preceding sections document the preserved ordinary foundation. The proposed
contract is historical; the implemented one-lane bounded-document trainer and
its explicit deviations are in the M3 implementation note. Controlled-world
generation/scoring is in `worlds.py`; recurrent state/session code in
`recurrent.py`; ordered training and answer evaluation in `controlled.py`;
runtime prediction in `effect_predictor.py`; future-only supervision in
`effect_training.py`; bounded experiments/integrity aggregation in `comparisons.py`.
Runtime prediction does not import world/oracle/offline label code. The new
controlled checkpoint format is separate from ordinary checkpoints.

`generalization.py` verifies the sealed M6 kernels and reproduces saved generated
answers before allowing frozen-checkpoint M7 studies. Held-out manifests bind
data, transformations, model/predictor hashes and protocols; evaluation-only
datasets are rejected by training loaders. The original model, tokenizer,
generation and scoring kernels are unchanged. Oracle/stratum analysis remains
offline. See [M7 protocol](research/m7-protocol.md) for study scope and limits.
