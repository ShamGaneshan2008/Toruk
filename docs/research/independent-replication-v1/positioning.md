# Research positioning and search record

Search date: **4 November 2026, Asia/Calcutta**. This is a targeted primary-source
comparison, not an exhaustive systematic review. No IEEE Xplore absence claim,
priority claim or claim of first invention is made. Third-party results below
are author-reported and were **not replicated on Toruk's backbone or hardware**.

Search queries used:

1. `site.arxiv.org recurrent memory transformer 2022 2207.06881`
2. `site.aclanthology.org LongMem 2023 memorizing transformers 2022`
3. `site.aclanthology.org LLMLingua-2 2024 LongMemEval 2025`
4. `site.arxiv.org "LongMemEval"`
5. `site.aclanthology.org/2024.findings-acl.57 LLMLingua-2`
6. `site.arxiv.org "SimpleMem" "2026"`
7. `site.arxiv.org "Mem0" "2025"`
8. `site.arxiv.org "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"`
9. `site.aclanthology.org "Lost in the Middle"`
10. `site.proceedings.mlr.press "A Human-Inspired Reading Agent"`

Primary paper pages and the Mem0/SimpleMem full texts were opened. Search-engine
snippets were not treated as authoritative when versions disagreed: SimpleMem
v3 uses online synthesis and intent-aware retrieval, whereas the older indexed
abstract described recursive consolidation. The matrix follows the opened v3.
The ReadAgent search also surfaced EARM; its original arXiv page was opened and
checked directly, rather than relying on the third-party result that linked it.

| Approach; publication/version date | Implemented architecture | Training requirement | Evaluation setting | Reported resource measurement and comparison limit |
|---|---|---|---|---|
| [RAG](https://arxiv.org/abs/2005.11401v4); first 2020-05-22, v4 2021-04-12; NeurIPS 2020 | Dense Wikipedia passage index, neural retriever and sequence generator; passage selection per sequence or token | Fine-tuned retrieval/generation system | Knowledge-intensive NLP and open-domain QA | External index and retrieval work exist; no compatible Toruk total-cost measurement extracted |
| [Recurrent Memory Transformer](https://arxiv.org/abs/2207.06881v2); first 2022-07-14, v2 2022-12-08; NeurIPS 2022 | Special memory tokens carry learned state between transformer segments | Train the model to use recurrent memory tokens | Language modeling and long-dependency tasks | Studies memory-size/performance tradeoffs; no shared-hardware Toruk latency figure |
| [Memorizing Transformers](https://arxiv.org/abs/2203.08913); 2022-03-16; ICLR 2022 | Approximate nearest-neighbor access to stored attention key/value representations | Memory-augmented LM training; new test-time entries do not require weight updates | Web, books, mathematical text, code and formal proofs | Memory capacity studied up to 262K tokens; this is a growing retrieval memory, not Toruk's selected-turn budget |
| [LongMem](https://arxiv.org/abs/2306.07174); 2023-06-12; NeurIPS 2023 | Frozen backbone memory encoder plus trained residual retrieval/reading side network | Memory-adaptation training | Long-context modeling, ChapterBreak and in-context learning | Demonstrates cached histories up to 65K tokens; no matched 512-token/Qwen cost comparison |
| [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/); TACL 2024, month unspecified | Evaluation varies the location of relevant evidence; not a memory implementation | No new Toruk-like component required by the evaluation | Multi-document QA and key/value retrieval | Measures position-dependent quality; it does not establish a memory efficiency advantage |
| [LLMLingua-2](https://aclanthology.org/2024.findings-acl.57/); ACL Findings, August 2024 | Bidirectional encoder classifies tokens for extractive prompt compression | LLM-distilled supervision and encoder training | MeetingBank, LongBench, ZeroSCROLLS and reasoning tasks | Reports 3–6× faster compression and 1.6–2.9× end-to-end acceleration under its settings; not transferable timings for Toruk |
| [ReadAgent](https://proceedings.mlr.press/v235/lee24c.html); ICML, 21–27 July 2024 | Prompted episode grouping, gist-memory creation and lookup of original passages | Prompting with pretrained LLMs | QuALITY, NarrativeQA and QMSum | Reports 3.5–20× effective-context extension; that is not an equivalent latency or total-compute saving |
| [LongMemEval](https://arxiv.org/abs/2410.10813v2); first 2024-10-14, v2 2025-03-04; ICLR 2025 | Benchmark plus indexing/retrieval/reading design framework | Benchmark itself requires no trained component | 500 curated questions: extraction, multi-session/temporal reasoning, updates and abstention | Full paper provides roughly 115K-token and 1.5M-token settings; this study does not run those workloads |
| [Mem0](https://arxiv.org/html/2504.19413v1); 2025-04-28 | LLM-driven extraction/update and retrieval of persistent facts; optional graph representation | Uses pretrained LLMs for memory operations, rather than Toruk's logistic turn scorer | LoCoMo conversational QA | Authors report 91% lower p95 latency and >90% token savings against full context; §4.5 separately discusses memory construction overhead |
| [SimpleMem](https://arxiv.org/html/2601.02553v3); first 2026-01-05, v3 2026-01-29 | Structured compression, online semantic synthesis and intent-aware retrieval planning | LLM-based memory processing; no decoder training performed by this Toruk study | LoCoMo and long-term memory evaluations | Reports up to 30× inference-token reduction and 26.4% average F1 improvement in LoCoMo; these are author-reported, unreplicated figures |
| [LongMemEval-V2](https://arxiv.org/abs/2605.12493); 2026-05-12 | Benchmark for reusable environment experience from web-agent trajectories | Benchmark, not a single memory architecture | 451 curated questions about state, workflows, gotchas and premises | Author [project page](https://xiaowu0162.github.io/longmemeval-v2/) describes scaling to 115M tokens; it differs from this bounded text-dialogue study |
| [EARM](https://arxiv.org/abs/2608.22767); 2026-08-24 | Stores sparse query–memory LLM relevance scores; causal matrix completion estimates unobserved scores for reranking | Online learning of retrieval experience and selective LLM scoring | Long-term conversational memory | Reports effective reranking with direct LLM scores for 17.5% of candidates; no matched Toruk token/latency comparison |
| Toruk conversational system in this package | Eight-feature learned turn ranking; top two earlier user turns plus three recent turns; optional verbatim-source envelope; frozen Qwen decoder | Historical selector fit: seed 173, 180 Adam steps; no new fit here | 12 published controlled and 24 separately authored scenarios, 512-token final prompt | Measures full request time, CPU time, all tokenizer/fitting positions, model tokens and process RSS; historical training, energy and FLOPs remain unmeasured |

Toruk's difference is narrowly **small supervised turn ranking and bounded raw
source presentation in an existing pretrained chat path**. It does not implement
RMT's recurrent latent state, LongMem's side network, LLMLingua-2's token
compression, or Mem0/SimpleMem's persistent memory writing. Its provenance hashes
establish which text was available, not that the decoder copied or interpreted
it correctly. This is an engineering and evaluation distinction, not a novelty
or superiority claim.
In particular, Toruk does not accumulate EARM's query–memory scoring experience
or implement ReadAgent's gist construction and interactive lookup.

No published systems above were rerun as experimental baselines here. The actual
simple baseline is lexical-v1 retrieval under the same local decoder and prompt
budget. Cross-paper accuracy, token ratios and latency are not pooled or ranked.
Evidence for Toruk's own claims is in the local claim ledger and raw artifacts.

Cost-scope detail: Mem0 §3.2 defines its token metric over retrieved context and
its answer latency over retrieval plus generation; §4.5 separately discusses
memory construction. Those savings must not be read as a measured lifecycle
training/construction/energy saving. Toruk likewise reports its startup and
offline work separately rather than calling a short answer prompt total cost.
