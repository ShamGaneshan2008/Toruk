# Memory research assessment

Reviewed 2026-10-20 (Asia/Calcutta). Primary full-text HTML papers and arXiv
submission histories were inspected, including method and evaluation sections.
Versions below are the latest exposed by those histories on this date. These
are comparisons to Toruk's proposed design, not implemented Toruk results.

| Paper and inspected version | Method and memory representation | Training signal and evaluation | Overlap and distinction to investigate |
| --- | --- | --- | --- |
| [Recurrent Memory Transformer](https://arxiv.org/html/2207.06881v2), v2, 2022-12-08, sections 3–5 | Carries a fixed set of learned continuous memory tokens between segments; separate read and write positions preserve decoder causality. | Task/LM losses; backpropagation through memory across segments. Copy/reverse, associative retrieval, equations, enwik8, WikiText-103 and long-text classification. | Establishes segment recurrence, bounded neural memory and delayed gradients. Toruk's proposed cross-attention/gated writer is a different interface, not evidence that recurrent memory is new. No Toruk comparison has been run. |
| [Titans](https://arxiv.org/html/2501.00663v1), v1, 2024-12-31, sections 3–5 | Neural associative memory stores history in fast MLP weights; online surprise gradients, momentum and adaptive forgetting; integrates with attention in several ways. | Inner-loop key/value regression and outer task training. LM, commonsense, needle retrieval, genomics and time series. | Learned retention and bounded neural memory overlap. Toruk proposes predicting downstream operation effects rather than adopting Titans' online associative optimization. This distinction is only a hypothesis. |
| [Gated Delta Networks](https://arxiv.org/html/2412.06464v3), v3, 2025-03-06, sections 3–4 | Matrix recurrent state combines data-dependent decay with targeted delta-rule key/value updates and chunkwise parallel training. | End-to-end LM training; online-regression interpretation of updates. LM, commonsense, synthetic retrieval/length extrapolation and real-world recall tasks; attention hybrids are also evaluated. | Adaptive forgetting, precise updates and saturation are established concerns. Toruk's proposed slot state is different, but gating alone cannot support a novelty claim. A separate future-effect estimator is a proposed experimental distinction. |
| [Learning What to Remember: Long-horizon Counterfactual Memory Optimization](https://arxiv.org/html/2609.37930v1), v1, 2026-09-29, sections 2–3 and appendix C | MGPO trains a bounded textual-memory writer with a frozen reader; compares adjacent memory states on common current/future targets and aggregates marginal utility across the reuse horizon. | Counterfactual memory gain supplies policy-optimization credit; document-level entity clustering/relation extraction on SciREX, transfer to AIPAN-10K and reader reuse. | Direct conceptual overlap with paired downstream labels and delayed credit. Toruk cannot claim these ideas as original. Predicting a bounded-horizon effect from deployable features over internal neural state, instead of directly optimizing a textual writer with measured counterfactual credit, is a possible distinction to test. |
| [Adapting Context Compression for Long-Horizon Agents with Counterfactual Continuations](https://arxiv.org/html/2609.36526v1), v1, 2026-09-29, sections 3–5 | PAIR restores the same agent/environment boundary and compares pre/post-compression continuations with a frozen agent and no subsequent compression; successive halving allocates rollout budget. Memory is structured textual context. | Continuation success and interaction burden localize harmful compressions; an optimizer adapts the compression prompt. AppWorld, OfficeBench and tau2-Bench Retail; mean success, cross-run reliability and steps. | Local interventions, paired rollouts and harmful-update detection overlap directly. Toruk proposes an amortized estimator over bounded internal state, not a structured prompt optimizer. Neither superiority nor originality follows from this change of setting. |

Submission-history sources: [RMT](https://arxiv.org/abs/2207.06881),
[Titans](https://arxiv.org/abs/2501.00663),
[Gated DeltaNet](https://arxiv.org/abs/2412.06464),
[MGPO](https://arxiv.org/abs/2609.37930),
[PAIR](https://arxiv.org/abs/2609.36526).

## Narrowed research question

After a verified recurrent baseline exists, can a small predictor using only
current observations and bounded neural state rank retain/write decisions on
held-out documents better than a simple observed-state heuristic, with useful
calibration and acceptable measured total cost? Paired counterfactual supervision
is prior art. Internal state and amortized prediction are candidate distinctions,
not demonstrated contributions. A null result is acceptable. The review covers
the five requested works, not an exhaustive originality search.
