# Toruk custom LM architecture decision v1

12 November 2026. **Design for review only. Choose a segment delta-memory byte
LM for one bounded implementation milestone; do not start a training study.**

Initial checks: Git root `D:/Toruk`, clean `main`, HEAD
`ab6d3a65538b5f33d17efe4f45189906f1394a38`. Work in this task is code inspection,
primary-paper review, arithmetic and this document. No model was constructed,
trained or used to generate answers; no held-out dataset was opened. No new
cases, checkpoint, registration, answer-policy experiment or production edit.

The goal remains a Toruk-owned mechanism that preserves useful long-history
information and answers accurately with less computation or bounded local
context. A Qwen interface does not establish that Toruk learned language. The
learned selector has not established superiority to lexical retrieval. Preserve
the [source-faithful v1 negative result](source-faithful-development-v1-results.md):
T-LM 8/12, L-LM 7/12, T-P and L-P 11/12; both policies fail on a known-fact
regression, and the tied policy cells fail selector superiority. Its gates and
all archived evidence remain unchanged. Synthesis is still not ready: four
earlier answers omitted a premise and all 12 forced continuations abstained.
The original 48-case study remains unregistered and unrun.

## 1. What the repository actually implements

Locations below are relative to the root at the checked HEAD. These are code
paths inspected, not checkpoints loaded or experiments replayed.

| Location and entry point | Trainable mechanism and actual boundary |
|---|---|
| [model.py](../../src/toruk_lm/model.py), `ModelConfig:11`, `DecoderBlock:32`, `CausalLM:58`, `loss_sum:85`, `generate:99` | Ordinary causal byte transformer: learned token/position embeddings, pre-norm self-attention, GELU FFN, untied token head. No recurrent state or KV cache. Ordinary generation repeatedly forwards the recent window. |
| [recurrent.py](../../src/toruk_lm/recurrent.py), `RecurrentLM:13`, `forward:34` | A trainable transformer with per-layer cross-attention to K dense slots. After current-segment logits, one mean hidden vector and each old slot produce tanh proposals and sigmoid gates, with learned slot offsets. All slots see the same segment mean; there is no explicit entity/attribute address or source-span guarantee. |
| Same file, `Session:71`, `consume:108`, `flush:127`, `generate:135` | Explicit document state, cloning and reset. Legacy consume forwards each growing prefix and counts that repeated work. A complete segment commits; partial flush is an additional forward. Questions can affect a session unless isolated by clone/reset. |
| [owned_lm.py](../../src/toruk_lm/owned_lm.py), `OwnedConfig:18`, `OwnedMemoryLM:50`, `build_model:108`, `segment:116`, `document_loss:129`, `OwnedSession:151` | A genuine Toruk-owned next-token path. Memory feeds token logits directly. Full mode preserves the recurrent core's algebra; read/write removals remove real operations. Document loss uses full-document BPTT without segment detach. Batched chunk ingestion improves on legacy per-byte prefill; answer generation still recomputes an uncached local prefix. |
| [owned_training.py](../../src/toruk_lm/owned_training.py), `load:90`, `train:154`, `evaluate:284` | AdamW, finite-gradient checks, clip 1.0, deterministic document order, token-normalized loss. Atomic optimizer-boundary checkpoints contain weights, optimizer, RNG, variant/config, runtime/tokenizer/data identity and progress. Format `toruk-owned-next-token-v1`; load rejects mismatches. Existing evaluation strips outer whitespace, so it must not silently supply a new byte-exact scorer. |
| [engine.py](../../src/toruk_lm/engine.py), `setup:50`, `load_checkpoint:57`, `load_model:93`, `restore_training_state:111`, `train:195` | Ordinary-LM training and strict `toruk-ordinary-v1` checkpoints; fixed learning rate, dataset/cursor/RNG/optimizer validation, atomic save. Independent ordinary windows are not a recurrent training protocol. |
| [controlled.py](../../src/toruk_lm/controlled.py), `history_pass:30`, `answer_loss:92`, `load_controlled:131`, `train_controlled:158` | Another trainable ordinary/recurrent route, including supervised controlled-answer objectives. Its `toruk-controlled-v1`, drained-document boundary differs from owned next-token checkpoints. Merely sharing tensor dimensions does not make these checkpoint formats interchangeable. |
| [tokenizer.py](../../src/toruk_lm/tokenizer.py), `ByteTokenizer:6` | Fixed 259 IDs: PAD 0, BOS 1, EOS 2, UTF-8 byte +3. No learned vocabulary. Decode uses replacement for invalid UTF-8; future exact scoring must inspect raw byte IDs before that replacement. |
| [owned_data.py](../../src/toruk_lm/owned_data.py), `cases:17`, `write_data:63`, `load_data:85`; [owned primary config](../../configs/owned-lm-primary-v1.json) | Existing bounded synthetic grammar/split generator and size constraints, inspected as code/config only. It can create held-out files automatically; do not call it for the proposed development-only path. No existing split is input to this decision. |
| [integrated_memory.py](../../src/toruk_lm/integrated_memory.py), `IntegratedMemoryLM:50`, `update_vectors:94`, `prepare:107`, `decode:119`, `load_integrated:144`, `IntegratedSession:161` | Already has a custom GRU record encoder, learned slot/no-write address, dense overwrite values, query read and autoregressive byte decoder. Slot-address supervision is an explicit inductive bias. This conditional QA model is not the ordinary transformer LM or a new mechanism to rediscover. Its state persistence is checkpoint-bound. |
| [chat_foundation.py](../../src/toruk_lm/chat_foundation.py), `TorukContextSelector:106`, `_summary:144` | Uses frozen controlled recurrent hidden summaries to cosine-rank original turns. It returns text indices, not state decoded as an answer. The recurrent checkpoint was not trained as a general semantic retriever. |
| [context_selection.py](../../src/toruk_lm/context_selection.py), `terms:13`, `LexicalContextSelector:17`; [relevance_gate.py](../../src/toruk_lm/relevance_gate.py), `LexicalAdmissionSelector:13` | Lexical retrieval and the research v3 lexical-admission/recurrent-ranking combination. The latter still processes all turns neurally, including turns not admitted. Neither adds language ability or makes omitted history semantically absent. |
| [chat_selector.py](../../src/toruk_lm/chat_selector.py), `features:58`, `ChatRelevanceSelector:78`, `load_chat_selector:133`; [train_chat_selector.py](../../scripts/train_chat_selector.py), `main:45`; [v2 trainer](../../scripts/train_chat_selector_v2.py), `main:61` | A separate learned linear relevance scorer over eight engineered lexical/position features, trained with evidence-turn BCE and development threshold selection. These are trainable retrieval weights, not an LM tokenizer or generative backbone. |
| [chat_foundation.py](../../src/toruk_lm/chat_foundation.py), `PretrainedChatBackend:156`, `_fit:229`, `reply_with_metrics:243` | External pretrained Qwen/other backbone loaded in float32 and used for its own tokenizer, language knowledge and generation. Toruk may change selected text; the backbone weights do not become a Toruk architecture through that selection. |
| [chat_runtime.py](../../src/toruk_lm/chat_runtime.py), `OrdinaryChatBackend:62`; [inference_worker.py](../../src/toruk_lm/inference_worker.py), `model_worker:14`, `ProcessBackend:77` | Ordinary-checkpoint chat is explicitly a smoke fixture; the worker separately chooses ordinary, pretrained or Ollama backends and enforces a process boundary. The proposed research model must not be attached to these production paths. |
| [evidence_first_policy.py](../../scripts/evidence_first_policy.py), `make_view:78`, `answer:406`; [source-faithful harness](../../scripts/source_faithful_development_v1.py) | Deterministic source parsing, coverage, copying and abstention after retrieval. This is an answer policy around evidence, with no trainable LM parameters. It is excluded from the proposed architecture. |

The [owned-LM result](owned-lm-v1-results.md) already records a failed aggregate
quality/efficiency gate for the mean-slot next-token model; availability of
trainable memory is not evidence that it works well. Only published historical
findings inform this decision, not a new inspection of held-out case files.
Likewise, do not present the existing conditional integrated model as a successful
general LM. No old checkpoint is a starting weight for the proposed fits.

## 2. Nearest primary research and three feasible candidates

This is a targeted primary-source review, checked 12 November 2026, not an
exhaustive priority search. No IEEE, global novelty or paper-ready contribution
is claimed. Existing methods already establish the broad ideas below; their
benchmark results do not establish performance on this repository or CPU.

| Exact primary source | Already known; implication for Toruk |
|---|---|
| Dai et al., **Transformer-XL: Attentive Language Models beyond a Fixed-Length Context**, ACL 2019, [paper/DOI record](https://aclanthology.org/P19-1285/), section 3 | Segment recurrence caches previous hidden activations, with stopped gradients and relative positional treatment. Reusing past representations is established; Toruk's learned pooled slots are a different, lossy state, not a reproduction of Transformer-XL. |
| Rae et al., **Compressive Transformers for Long-Range Sequence Modelling**, [arXiv:1911.05507](https://arxiv.org/abs/1911.05507), section 3 | Keeps recent memories and compresses older activations, with auxiliary compression objectives. Multi-timescale compression and learned memory retention already exist; a compression ratio alone says nothing about factual preservation or total cost. |
| Bulatov, Kuratov and Burtsev, **Recurrent Memory Transformer**, NeurIPS 2022, [arXiv:2207.06881v2](https://arxiv.org/abs/2207.06881v2), section 3 | Learned memory tokens carry differentiable state between segments. Training a decoder to write/read recurrent latent slots is established; extra latent positions have compute cost. |
| Schlag, Irie and Schmidhuber, **Linear Transformers Are Secretly Fast Weight Programmers**, ICML 2021, PMLR 139:9355-9366, [paper](https://proceedings.mlr.press/v139/schlag21a.html), section 5, equations 20-25 | Content-addressed fast weights and learned-strength delta updates can replace an existing key/value association. The proposed update is an adaptation of this known mechanism, not a new memory rule. |
| Gu and Dao, **Mamba: Linear-Time Sequence Modeling with Selective State Spaces**, [arXiv:2312.00752v2](https://arxiv.org/abs/2312.00752v2), sections 3.2-3.3, Algorithm 2 | Input-dependent state-space parameters enable selective retention; efficient scan implementation matters. Published throughput depends on a different implementation/hardware regime; an unfused CPU reference cannot inherit those speed claims. |
| Yang, Kautz and Hatamizadeh, **Gated Delta Networks: Improving Mamba2 with Delta Rule**, ICLR 2025 camera-ready, [arXiv:2412.06464v3](https://arxiv.org/abs/2412.06464v3), sections 3-4 | Gated delta updates and hybrids with local attention have already been investigated. A local transformer plus associative state is not a new architectural category. This proposal omits the paper's global forgetting gate and optimized parallel algorithm. |
| Xu, Shi and Choi, **RECOMP: Improving Retrieval-Augmented LMs with Compression and Selective Augmentation**, [arXiv:2310.04408](https://arxiv.org/abs/2310.04408), sections 2-3 and 6 | Learned extractive/abstractive retrieval compression reduces appended text, sometimes returning no augmentation. That is a retrieval/compression path, not evidence that a small custom LM acquired language or certified absence. Compressor cost and factual loss still matter. |

Exactly three architecture candidates are considered:

**A. Segment delta associative memory — chosen.** Carry one float32 matrix
`S[16,16]` across 32-byte segments. Token hidden vectors produce learned keys,
values and write strengths; sequential error-correcting outer-product updates
replace the current global mean writer. Per-layer learned query projections read
this matrix into hidden activations; the existing byte head decodes next tokens.
All parameters learn from next-token targets. Persistent matrix cost is 1024
tensor bytes, independent of segment count. The concrete algebra is below.

**B. Four-token recurrent memory transformer — not chosen.** Carry
`M[4,32]` (512 float32 bytes). For each segment, process
`[M_old, x_1..x_n, W_1..W_4]`, where W are learned write-token embeddings.
Use causal attention: real tokens cannot attend to the suffix; suffix states
become `M_new`. Learn the transformer, embeddings and token head end to end;
decode bytes from real-token logits only. Unlike the current shared mean, each
write token can attend differently to segment details. It is CPU-implementable
with existing attention, but adds eight latent positions per full segment and
needs a carefully tested mask. It is closely related to the cited RMT, and is
not a default fallback if A fails.

**C. Small selective diagonal state-space decoder — not chosen.** Carry
`h[layer,channel,state]` with two layers, 32 channels, eight states/channel:
2048 float32 bytes. For token embedding x, learn negative diagonal
`A=-exp(a)`, input-dependent positive `Delta=softplus(W_delta x+b)`, and
`B(x), C(x)`. Use zero-order-hold discretization elementwise:
`Abar=exp(Delta*A)`, `Bbar=((Abar-1)/A)*B(x)`, then
`h_new=Abar*h_old+Bbar*x`, `y=sum(C(x)*h_new)+D*x`.
Learn projections, A, D, residual mixing, embedding and byte head; decode one
next-byte distribution after each causal token update. A finite epsilon handles
small denominators numerically. This removes mean-pooling and local attention;
it is a selective-SSM reference, not a faithful optimized Mamba implementation.
Its unfused scan and different optimization dynamics make it a larger first
change than A. Kernel engineering is outside the CPU-first first milestone.

Retrieval compression is reviewed as the nearest external alternative and a
control, not a fourth proposed mechanism. Training another compressor in front
of Qwen would repeat the retrieval contribution boundary we need to resolve.

## 3. Chosen model: precise state, causality and learning

Reuse the byte embedding, two pre-norm local causal transformer layers, final
layer norm and untied 259-way head. Width 32, four heads, local segment length
32; all float32, zero dropout, no KV cache. Set the two FFN hidden widths to
203 for the parameter match below. This is a research-only configurable decoder,
not an edit to the existing archived classes or their checkpoint interpretation.

For segment s, hold `S_s` fixed while computing all current logits. In layer l,
after the existing causal block produces hidden x_t, compute:

```text
u_t = LayerNorm_read_l(x_t)
q_t = Wq_l u_t / max(norm(Wq_l u_t), 1e-6)       # 16 coordinates
r_t = transpose(S_s) q_t                         # 16 coordinates
x_t <- x_t + Wo_l r_t                            # 32 coordinates
logits_t = byte_head(final_layer_norm(x_t))       # after both layers
```

Wq is bias-free 32-to-16; Wo is bias-free 16-to-32. Normalize the query once,
not two separately evaluated projections. Use the final normalized causal
hidden vectors h_t to produce the next segment state, in source order:

```text
T = S_s
for every valid token t in the segment:
    k = (Wk h_t + bk) / max(norm(Wk h_t + bk), 1e-6)
    v = tanh(Wv h_t + bv)
    beta = sigmoid(w_beta h_t + b_beta)
    error = v - transpose(T) k
    T <- T + beta * outer(k, error)
S_(s+1) = T
```

Wk/Wv are 32-to-16 with biases; beta is one learned scalar per token. Start
each document with zero S. PAD has no read loss or write update; BOS is a real
causal input. Do not write target tokens that have not been consumed. All current
segment logits use S_s, never the completed T: a suffix token therefore cannot
change an earlier logit. Corrections are hoped to learn compatible keys for the
same entity/attribute; that alignment is not guaranteed or hard-coded. Key
collisions, noisy byte writes and forgetting remain falsifiable failure modes.

At inference, retain S, at most 32 local token IDs and a segment cursor. Ingest
complete historical segments in one forward each. For a partial segment, retain
the pre-segment S and recompute the growing local prefix; never commit its
provisional writer repeatedly. Commit each full segment once. Apply the same
segment schedule to the ordinary/recurrent comparators. A question follows the
history as ordinary input, with no forced flush merely because it is a question.
Reset at document boundaries; clone state for diagnostic questions. No global
session state, full-history callback, entity table, source copier or answer parser.

Train the local decoder, memory read/write maps, layer norms, embeddings and head
jointly through the entire bounded document. No detach between its segments;
detach/reset between documents. No address labels, source offsets, gold routing
or pretrained teacher. The inference-time S is a **fast activation state**,
not a separately fitted parameter or another optimizer running at test time.
The learned slow weights determine both state and next-token probabilities.
That direct learned state-to-logit path is the architecture experiment; changing
prompt wording or validating/copying answers after Qwen would not implement it.

Save under a new research format, e.g. `toruk-delta-segment-v1`, with architecture
and feature dimensions, tokenizer/source/data hashes, AdamW/RNG/cursor and exact
optimizer boundary. Reuse the strict validation principles, not an old format
tag. Checkpoints exclude live document state; any later session snapshot needs
its own checkpoint-bound format. Old ordinary, controlled, owned and integrated
loaders must continue rejecting incompatible files.

## 4. Matched controls and minimal future training path

The following is a **prospective development plan**, not a registration or
authorization to create data now. Before any future fit, freeze its source,
data/labels, scoring, decode, order, identities, budgets and gates. Do not use
the source-faithful 12 cases, stopped 48-case design, old held-out sets or old
published failures as new training/evaluation examples. Use a new development-only
generator with no held-out writer or loader. Author/review labels before fitting.

Propose 256 training documents and 32 disjoint development histories, no held-out
split. Four balanced development strata of eight: local/insufficient evidence,
distant binding, corrections, and preservation amid related distractors. Four
local questions have no requested fact and require the single-byte unknown
symbol `?`. For the other 24, queried evidence lies beyond the 32-byte local window;
balance gaps near 64/128/256/384 bytes where category constraints permit. Include
different facts with colliding surface terms and independent entity/attribute
pairs; finite short values of 1-4 bytes keep initial language acquisition small.
No synthetic accuracy is a conversational qualification or an absence certificate.
Training and development IDs/texts differ, but share a declared grammar and value
inventory; report that IID limitation. Do not choose documents after seeing outputs.

Use ByteTokenizer unchanged, document input/target length at most 512 including
special-token accounting, prefix at most 504, answer plus EOS at most eight.
Six fresh fits per seed, all on the **same canonical documents, target IDs,
target weights, deterministic document order and optimizer schedule**:

| Condition | Configuration and role | Trainable parameters, algebraic estimate | Persistent neural state |
|---|---|---:|---:|
| O0 | Existing ordinary, width 32, two layers, FFN 128; small diagnostic | 43,072 | 0 |
| O-match | Existing `ordinary_matched`, width 38/two heads, two layers, FFN 152 | 56,620 | 0 |
| R4 | Existing recurrent/owned full path, width 32, FFN 128, four slots | 56,064 | 512 bytes |
| R8 | Same recurrent algebra with eight slots; equal-state-size control | 56,320 | 1024 bytes |
| D | Proposed delta model, width 32, FFN 203, rank 16 | 56,087 | 1024 bytes |
| Lex-O | Same decoder/configuration as O-match, trained with the lexical query-context path below | 56,620 | No neural history state; raw history retained |

All main controls except the explicitly smaller O0 are within 1% of D's
parameter count and below 57,000. FFN expansion is actual active capacity, not
unused padding. R4 deliberately has half D's state; R8 prevents attributing a
larger-state advantage to the delta update. FFN allocation and width differ:
even a pass supports this whole configuration, not proof that the delta equation
alone caused the gain. Read/write removals establish dependence on memory,
not global optimality of this writer. No compare-with-Qwen quality claim.

For auditing the counts, a width-d, FFN-f, L-layer ordinary decoder has
`P=2*259*d+C*d+2*d+L*(4*d*d+(2*d+1)*f+9*d)` parameters.
D adds `L*(2*d*16+2*d) + 2*(d*16+16) + (d+1) = 3265` at d=32,L=2.
The implementation must verify these estimates before any fit. A discrepancy
requires resolving the design before freeze, not padding parameters or adjusting
the budget after outcomes.

Lex-O uses the existing lexical-v1 term-overlap/tie-break rule on the original
record/turn boundaries, with the same history H and question Q available to every
condition. Fit selected whole records plus Q into 32 native byte positions,
preserving Q; no answer-based selection, dependency oracle or field parser.
If none fit, use Q only and log the omission. It may retain/index H, but cannot
access any extra conversation or gold. Its raw-history/index storage and all
scanning/sorting/tokenization must be charged; 1024 bytes of delta state is
actually larger than these tiny histories' raw bytes, so claim no storage saving.

During training, every condition scores the same canonical history/question/answer
next-token targets once. Lex-O additionally re-encodes its selected prefix at the
known question boundary (without duplicate losses), resetting its local context
before scoring the question/answer suffix. Use this identical inference procedure
at development time. All other conditions continue their original stream. This
matches target/data budgets and gives retrieval its own trained decoder rather
than an inference-only prompt distribution shift. Extra Lex-O context encodings
are real extra compute, not extra labeled targets. Do not use the gold answer or
its length to select evidence. No external answering backbone participates in
any cell: the same byte-LM family supplies all answers.

Proposed fixed training schedule: seeds 113 and 227; 256 AdamW steps, batch two
complete documents, learning rate .003, betas (.9,.999), epsilon 1e-8 and weight
decay .01, gradient clip 1.0, one CPU thread, deterministic float32. Freeze the
exact optimizer implementation/version at registration. No
curriculum, sweep, early checkpoint selection, external pretraining or distillation.
Initialize common-shaped base tensors from the same seed where possible; record
the remaining shape-dependent initialization. Full-document NLL provides the
ordinary language-training signal; no new answer wrapper is trained. Use final
step checkpoints only. Report answer-suffix NLL separately because filler can
dominate overall NLL. Training-only numerical smoke/profile work is charged and
cannot select a more favorable mechanism or decode setting.

Evaluate greedy argmax with PAD/BOS suppressed, ordinary EOS stopping and eight
new-token cap. Primary ordinary inference uses the **same segment-reset schedule**
as recurrent inference, not the legacy rolling-window path that previously had a
train/inference mismatch. No per-case repair, forced-answer tokens, output strip,
Unicode normalization or answer validation. Score exact byte IDs before EOS;
malformed UTF-8 and unclosed/budget-exhausted answers fail. Do not reuse the old
`.strip()` scorer. Also evaluate D with reads disabled and with writes disabled,
using the same fitted checkpoint, explicitly labeled diagnostic ablations.

Arithmetic for a future freeze: 6 variants x 2 seeds = **12 fits**; main answers
6 x 2 x 32 = 384; two D ablations x 2 seeds x 32 = 128; one first-case replay
for each of 16 condition/seed workers = 16. Total **528 development requests**,
not 528 independent cases. Cases, scores and state/logit traces must agree on
replay. Freeze condition order and reverse it for the second seed; do not pool
seeds to hide a failed one. No data or request from this plan exists today.

## 5. Resource estimate and what must be measured

These are arithmetic estimates and proposed safety ceilings, **not measured
feasibility**. The published owned-LM timings concern a different, shorter
workload/runtime and do not size this delta writer. No Qwen weights or downloads
are needed. The 1024-byte state is neither 1024 language tokens nor a free prompt.

For one length-32 segment, ignore lower-order norms/nonlinearities and count a
multiply-add as two FLOPs. The candidate backbone estimate per real position is
`2*L*(4*d^2+2*d*f+2*C*d)+2*d*259 = 93,120` at d=32,f=203,C=32,L=2.
Read projections, matrix reads and output projections add about 5,120; writing
keys/values/beta, reading the old association and applying the rank-one update
add about 3,136, plus approximately 300 scalar/normalization operations:
roughly **0.102 million forward FLOPs per consumed/recomputed position**.
Full-segment hidden computation and sequential writer costs are both included.
This is a shape-based estimate; exp/sigmoid, masks, framework dispatch and memory
traffic are not faithfully summarized by that scalar total.

At 256 steps x 2 documents x 512 positions, each fit sees at most **262,144
canonical target positions**; 12 fits at most **3,145,728**, not 12 different
training corpora. A rough forward-plus-backward factor of three gives about
**9.6e11 FLOPs** if every fit cost as much per position as D. This is an order
estimate, not a bound for every comparator: separately account Lex-O prefix
re-encodings, checkpoint validation/profile work, different model shapes and
optimizer work. A script must sum the actual shapes/positions per condition.

Persistent D state is 1 KiB plus at most 32 token IDs/cursor; an int64 token
buffer adds at most 256 bytes, excluding Python/container overhead. At 56,087
parameters, float32 weights, gradients and two Adam moments occupy approximately
0.86 MiB, before step tensors, optimizer metadata and workspaces. Unrolling
512 positions retains many state-update intermediates: roughly tens of MiB
of graph/activations at batch two is a planning allowance, not 1 KiB training
memory. Anticipate hundreds of MiB for the Python/Torch process; provision a
**2 GiB process-tree private-memory ceiling**, not a claimed observed peak.
Twelve optimizer checkpoints should be on the order of 12 MiB plus metadata;
set **256 MiB logical disk** for this new run, inputs, frozen sources and logs,
excluding the installed runtime. Stop if these estimates prove inadequate.

Proposed wall/CPU ceilings, both in seconds with sequential one-thread workers:

| Work | Arithmetic | Ceiling for each resource |
|---|---|---:|
| Each complete training fit, including cold setup/checkpoint | Fixed | 180 |
| All twelve fits | 12 x 180 | 2160 |
| Each dev request, including prefill/retrieval/decoding and teacher-forced scoring | Fixed | 1.5 |
| Each evaluation worker, 32 cases plus replay | 15 setup + 33 x 1.5 | 64.5 |
| All sixteen evaluation workers | 16 x 64.5 | 1032 |
| Disjoint preparation, integrity/profile/audit/controller work | Fixed | 120 |
| Entire proposed development work | 2160 + 1032 + 120 | **3312 (55.2 minutes)** |

Include failed, interrupted, profile and replay work. Monitor memory/disk/CPU
and wall continuously; stop on a resource overrun or unobserved monitoring gap
over five seconds. The first implementation must expose numerical/cost problems
before a future training registration. Do not substitute measured nice-case
latency for these ceilings, shrink the comparator set, or extend caps after a
failed run. If the plan is unaffordable, stop rather than silently reducing its
quality comparison.

Report separate quantities for each seed, variant and ablation:

| Measure | Required definition |
|---|---|
| Factual answer accuracy | Exact bytes on 32 unique development questions; per-stratum counts, errors, stale corrections, cross-attribute substitutions, unsupported non-unknown outputs on the four absent cases; no inference from NLL alone. |
| Long-range retention | Exact accuracy on the 24 beyond-window cases, binned by byte gap and number of intervening segments; correction and preservation separate. Also answer-suffix NLL and no-read/no-write deterioration. |
| Executed tokens/positions | Unique input byte/special IDs, generated IDs including EOS, re-encoded prefixes and every decoder forward position. Count padding, recomputation, memory read/write calls and latent scalar operations separately. Ordinary and D can consume the same unique bytes even with very different work. |
| FLOPs and CPU | Shape-based per-op MAC/FLOP ledger with convention; full process-tree CPU seconds including writer/reader/retrieval/tokenization/controller. Unsupported profiler operators are declared, not counted zero. No published hardware speed figure is reused. |
| Memory | Tensor state, local token buffer, retained raw retrieval history/index, parameters/optimizer and sampled/OS process-tree private peaks separately. A zero/unavailable OS field is unknown, not zero RAM. |
| Wall | Cold setup, complete history prefill, per-request median/p95, generation, retrieval, serialization/teardown, disjoint shared and total. Allocate shared work equally over the sixteen evaluation workers for the inference gate, while counting it only once in overall project totals. Overlapping components are not added twice. |
| Training | Targets, extra context positions, gradient-active parameters, steps, all 12 fits' CPU/wall/FLOPs, profile, checkpoints and disk. Report both one-query cost and amortized cost only for an explicitly fixed query count. |

Do not claim fewer executed input tokens merely because history is latent:
D still encodes every history byte, reads S in each layer, writes every valid
token, and recomputes partial prefixes during decoding. Its raw local context
is bounded, not its cumulative input processing. Partial-prefix provisional
writes must be included even if not committed. Any later KV-cache optimization
must be applied or controlled across models in a separately reviewed design.

The matched FFN allocation can make D's nominal FLOPs higher than R4's, and
unfused sequential delta operations can be slower on CPU. The hypothesis of
lower measured CPU is consequently uncertain. Do not relabel a retention-only
gain as computational efficiency. Conversely, early EOS on a wrong answer is
not an efficiency success: accuracy/protection gates apply first. Preserve raw
lengths and report a fixed-length, training-only numeric timing diagnostic under
the shared allowance to expose length-dependent timing artifacts.

## 6. Falsifiable hypothesis, go/no-go and stop

**Hypothesis:** within a 32-byte local window and approximately 56k learned
parameters, token-level delta writing preserves distant requested bindings and
corrections better than the current mean-slot state, with at least a 10% measured
end-to-end CPU/wall reduction relative to R4. It must also beat the parameter-
matched ordinary and lexical controls in accuracy. This is a proposed synthetic
development hypothesis, not an expectation of success or an established result.

A future frozen development run advances only to another design review if
**all** of the following hold at **each** seed:

1. D scores at least **24/32** exact and at least **four more correct** than
   every main quality control O-match, R4, R8 and Lex-O. No weaker baseline may
   replace a stronger one. If lexical is at ceiling, the line has no positive
   accuracy result under this gate; do not relax the hurdle.
2. At least **18/24** beyond-window answers correct and four more than each
   main control on that same subset. Corrections and preservation individually
   cannot regress versus any main control. Zero unsupported non-unknown answers
   on the four absent cases. All gold/case identities and replay invariants hold.
3. Disabling either read or write reduces D's beyond-window exact count by at
   least **two of 24**. Report both ablations; they do not isolate delta writing
   from every other possible writer or prove general reasoning.
4. At least **10% lower total charged inference CPU and cold wall** than R4,
   including setup and equal shared-cost allocation, not just a cheap read
   kernel. D's charged CPU and wall must also be **no greater than Lex-O's**;
   otherwise do not claim it beats the practical retrieval alternative. Report
   the ordinary and R8 costs too; do not claim fewer FLOPs without that ledger.
5. D training CPU and wall are each at most **1.5x R4**, all allocated parameter
   and state caps hold, and all fits/checks fit the fixed overall ceilings.
   Report training cost even if inference amortization is unfavorable. An
   inference gain is not a lifetime saving until a declared break-even analysis
   includes training; no unbounded future-query assumption.

All gates are conjunctive. A category failure, seed failure, parameter mismatch,
insufficient fit, timeout, nonfinite gradient/state, wrong-boundary resume,
future-token leakage, cross-document state leak, unexpected data access or
replay failure is a no-go. Stop immediately on integrity/resource failure;
otherwise stop after the fixed fits and development requests. Preserve partial
costs, raw IDs, states/hashes, failures and negative conclusions. No quality-
driven retry, alternate decoder, larger state, extra training, gate relaxation
or held-out evaluation. If it cannot fit the budget or cannot beat these controls,
**recommend stopping this delta-memory line**, not automatically trying B or C.

Two seeds on 32 authored development cases cannot establish generalization,
stable CPU speed, conversational competence, a novel contribution or publication
readiness. A pass would justify only a separately reviewed next development
decision; all historical negative results remain negative.

## 7. ONE next implementation milestone

**M1: implement an isolated segment-delta module and numerical contract tests,
with a parameter/work ledger; no training fit or generated text.** It should
expose `initial_state`, causal segment forward and one-time state commit, plus
strict format/config validation. Tests must prove suffix-token noninterference,
one commit per complete segment, inert padding, reset/clone isolation, exact
same-key replacement in a hand-constructed tensor example, finite gradients
from later token loss through earlier memory, and the stated parameter/state
counts. Numerical checks use synthetic tensors, not a new study dataset. A
training-only shape/timing preflight may be proposed for separate authorization
after that code review; it cannot select gates or inspect development answers.

Do not wire M1 into chat, reuse an archived format tag, or create/train the
prospective development set as part of M1. This task delivers **only this ADR**.
The training and evaluation path above is a bounded plan to review after M1,
not permission to execute it now.
