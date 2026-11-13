# Custom LM decision v2: bounded segment delta memory

13 November 2026. Development only. This supersedes no historical finding and
leaves the pre-existing untracked v1 draft byte-unchanged. The current user
request authorizes a bounded prototype and development study beyond that draft.

## Inspection and contribution boundary

Root is `D:/Toruk`, branch `main`, HEAD
`ab6d3a65538b5f33d17efe4f45189906f1394a38`, identical to the locally recorded
`origin/main`. Starting status: `## main...origin/main` and only
`?? docs/research/toruk-custom-lm-architecture-decision-v1.md`. No fetch: this
local experiment needs no upstream input and preserves the inspected revision;
remote freshness is unknown. No commits, pushes, deployment or held-out access.

Inspected README, architecture, owned-LM design/results, source-faithful negative
development result, evidence-first rehearsal, model/training/tokenizer/inference
sources and verification scripts. Source locations refer to this starting HEAD:

| Source | What actually exists |
| --- | --- |
| `src/toruk_lm/model.py:11,32,58,85,99` | `ModelConfig`, pre-norm causal `DecoderBlock`, `CausalLM`, token CE and rolling recent-context generation. Learned byte/position embeddings, attention, GELU FFN, final norm and untied head. No persistent neural state. Parameters at width d, L layers, context C: `12 L d^2+(520+C+13L)d`. |
| `src/toruk_lm/recurrent.py:13,34,71` | `RecurrentLM`: per-layer slot cross-attention; after logits, masked segment mean and old slots feed shared sigmoid gate/tanh proposal with learned slot offsets: `M'= (1-g)M+g*tanh(W[mean(h),M]+b+slot)`. State K by d, zero at document start. `Session` explicitly consumes, commits, clones and resets. |
| `src/toruk_lm/owned_lm.py:18,50,108,116,129,151` | `OwnedMemoryLM` preserves that recurrent algebra and exposes read/write removals. `document_loss` scores every byte/EOS target with full-document BPTT, reset per document. `OwnedSession` ingests full segments once and recomputes uncommitted partial prefixes during greedy decoding. Thus a trainable Toruk LM already exists, independently of chat. |
| `src/toruk_lm/owned_training.py:70,90,154,284` | Deterministic document order, AdamW, finite gradients, clipping; optimizer-boundary format `toruk-owned-next-token-v1`, optimizer/RNG/config/tokenizer/data/runtime identity, strict resume. Existing evaluation strips whitespace, unsuitable for the new raw-byte scorer. |
| `src/toruk_lm/engine.py:50,57,93,111,195` | Ordinary window training and strict `toruk-ordinary-v1` checkpoint path, independent of owned/controlled formats. |
| `src/toruk_lm/tokenizer.py:6` | Unchanged `ByteTokenizer`: 259 IDs, PAD/BOS/EOS 0/1/2, UTF-8 byte+3, fixed SHA identity. Inspect raw IDs for exact scoring; decode replaces malformed UTF-8. |
| `src/toruk_lm/integrated_memory.py:50,94,107,119` | Existing conditional GRU record encoder, supervised learned slot addressing/overwrite and autoregressive byte answer decoder. This is already another neural memory prototype; v2 does not rename it. |
| `src/toruk_lm/chat_foundation.py:106,156,229,243` | M6 recurrent summaries rank original turns; separately `PretrainedChatBackend` loads Qwen/other external weights and its own tokenizer, fits a 512-token prompt and generates answers. Those pretrained weights supply conversational ability. Historical M6 identity is not reproducible. |
| `src/toruk_lm/chat_selector.py:58,78,133` | Eight engineered relevance features with trainable logistic weights: text selection, not next-token language learning. |
| `scripts/evidence_first_policy.py:78,406` | Deterministic parsing, source copying, coverage and abstention after selection; no trainable LM. It remains separate, with its known-fact regression and failed selector-superiority gate preserved. |

The earlier owned LM, integrated LM, selector, Qwen and source-faithful negative
results remain negative. This study imports no old case file or checkpoint.

## Three candidates and nearest primary work

Targeted primary-source search and reads on 13 November 2026; no worldwide,
IEEE, exhaustive novelty or publication-readiness assertion.

1. **Segment delta associative memory (selected).** Carry `S in R^(8x8)`.
   Decoder segment hidden h yields normalized `k=normalize(Wk h+bk)`,
   `v=tanh(Wv h+bv)`, `beta=sigmoid(wb h+bb)`. In token order,
   `T <- T + beta*k*(v - T^T k)^T`, starting T=S; commit T after segment
   logits. Each decoder layer reads `S^T normalize(Wq LN(x))` through Wo.
   Queries read the entering S only, so later segment tokens cannot influence
   earlier logits. Learn reader/writer, all decoder weights, embeddings and head
   from ordinary next-token CE. No labels/addresses/routing in state updates.
   Width 16, one layer, four heads, local C=24, active FFN width 116: 14,277
   parameters (verify before training), state 256 float32 bytes. Additional
   compute per token is `O(d*r+r^2)` read/write; sequential unfused writes may
   cost more CPU than pooling. Full-document BPTT stores intermediates; its
   training memory is not the 256-byte inference state.
2. **Recurrent memory tokens.** Carry four 16-vectors; process
   `[old memory, segment, four learned write tokens]` with causal attention;
   boundary memory is the suffix hidden vectors. Next-token CE on real tokens;
   learn embeddings/attention/FFN/head/write tokens. Autoregressive inference
   repeats the same segment process. Adds eight attention positions, state
   256 bytes, attention work `O((C+8)^2 d)` and training activations. Close to
   [Recurrent Memory Transformer](https://arxiv.org/abs/2207.06881), which already
   carries learned memory tokens between segments. Not chosen: more masking
   changes, and no reason to presume it cheaper here.
3. **Selective diagonal state space.** At each token carry h[16,4], with
   learned `A=-exp(a)`, `dt=softplus(Wdt x+b)`, input-dependent B,C;
   `h'=exp(dt*A)h+((exp(dt*A)-1)/A)*B(x)*x`,
   `y=sum(C(x)*h')+D*x`. Boundary state is the final token h. Learn these maps,
   embeddings and head using next-token CE; inference scans one token at a time.
   256-byte state per layer; `O(d*n)` transition plus learned projections.
   [Mamba](https://arxiv.org/abs/2312.00752) already makes state-space parameters
   input-dependent; its optimized scan and hardware performance do not transfer
   to a Python CPU loop. Not chosen: a larger decoder/optimization change.

The selected delta update adapts known fast-weight replacement from
[Schlag, Irie and Schmidhuber, ICML 2021](https://proceedings.mlr.press/v139/schlag21a.html).
It is not a new memory rule. [Gated Delta Networks](https://arxiv.org/abs/2412.06464)
already combines delta updates, forgetting gates and local-attention hybrids;
our reference omits global forgetting and optimized parallel kernels.
[Compressive Transformer](https://arxiv.org/abs/1911.05507) compresses old
activations and trains auxiliary compression objectives; this tiny design has
neither a separate compressed cache nor an auxiliary reconstruction objective.
[RECOMP](https://arxiv.org/abs/2310.04408) trains compressors for retrieved text
fed to an external LM. We instead change the neural state-to-logit computation,
consume every input byte and train the decoder from scratch. No retrieved text
or pretrained backbone participates in the candidate.

## Isolation, hypothesis and first gate

Reuse existing `CausalLM`/`OwnedMemoryLM` unchanged for controls. Implement a new
research module and strict new checkpoint format; no production imports. Match
tokenizer, canonical training examples/targets, steps, optimizer and segment
schedule, approximately 14k active parameters (within 3%) and 256-byte neural
state for the two recurrent configurations. The delta FFN expansion buys active
capacity, not padding. This compares complete configurations, not the writer
equation in isolation. Read/write ablations test memory dependence separately.

**Hypothesis:** at both fixed seeds, delta gains at least four exact answers on
24 fresh development cases over both ordinary and current recurrent controls,
without category/unknown regression, and reduces complete inference CPU and
wall by at least 10% against recurrent. Overall byte NLL may worsen by at most
5%; training CPU and wall may increase by at most 50%. Any failed conjunct
rejects advancement. These are feasibility margins, not statistical confidence.
Precise gates, cases, order and caps must be registered before model training.

**Phase 1 PASS:** the state update is isolated, has a direct gradient path to
next-token logits, and has runnable existing matched controls. CPU feasibility
is provisional until a disposable random-tensor runtime rehearsal. Stop before
training if that rehearsal cannot support a small fixed budget. The later
[development protocol](segment-delta-dev-v1-protocol.md) records that gate.

Retain at most 24 token IDs, entering state and cursor during inference. Recompute
partial prefixes from the entering state; commit a full segment only once.
Reset at each document, clone explicitly, and backpropagate across segments
within each document. Corrections have no hard-coded key or overwrite guarantee:
learned collisions and failure to associate fields are expected failure modes.
Checkpoint only drained optimizer boundaries, with weights, optimizer/RNG,
document cursor, data/tokenizer/runtime/source/protocol identity; never silently
reinterpret an archived checkpoint or serialize a live inference session.
