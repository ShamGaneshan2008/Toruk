# Research claims audit

2026-10-24; reviewed on `main` at
`a2e1884efe9f122bec00fa55cb50a57bf811fe57`.
Verdicts concern the wording and its scope, not whether the general research
idea is impossible. A question or planned goal is not an achieved capability.

The source inventory includes the current README, architecture, implemented M3
contract, historical design drafts, actual M6/M7 protocols/results and reproduction
guide. Internal adviser, synthesis and decision reports were also available;
they are earlier snapshots of commit `2966f63`, whose source code is unchanged
by the intervening documentation commit. This page links repository sources
available in a clean checkout; it does not require private report access.

## Claim-to-evidence table

| Current claim and location | Evidence available | Verdict | Safer wording |
| --- | --- | --- | --- |
| Remember relevant facts, revise changed facts and preserve unrelated ones — [README overview/research focus](../../README.md) | Benchmark/prototype exists; [M6 known-fact scores](m6-results.md) are zero | **Supported as a research question**, unsupported as an achieved capability | Toruk investigates whether bounded memory can support these behaviors; current pilot does not demonstrate them. |
| Prototype includes memory, effect prediction and correction/preservation training — [README overview](../../README.md) | [Recurrent model](../../src/toruk_lm/recurrent.py), [predictor](../../src/toruk_lm/effect_predictor.py), [actual loss protocol](m6-validation-protocol.md) | **Supported** for implemented paths | Implemented research components execute; that is separate from useful recall or learned policy benefit. |
| Fixed memory rather than a growing archive — [M3 implementation](m3-implementation.md) | Bounded slot tensor/session in [recurrent.py](../../src/toruk_lm/recurrent.py); [recorded state sizes](../../artifacts/m6-validation-001/summary.json) | **Supported** for recurrent state, partially supported if interpreted as total memory | State storage is fixed for a configuration; model, optimizer, activations, current buffers and full input processing still cost resources. |
| Delayed or future-effect prediction — [older related-work wording](related-work.md), [M4 historical draft](m4-effect-predictor.md) | Actual labels are paired answer NLL at the final-history write; [M6 protocol](m6-validation-protocol.md) supersedes the draft | **Partially supported** | Local retain/write answer-NLL effect estimation at one boundary; not demonstrated long-horizon credit or a controller over all updates. |
| Runtime predictor excludes future/gold inputs — [M6 protocol](m6-validation-protocol.md) | [Feature interface](../../src/toruk_lm/effect_predictor.py) accepts previous/proposed memory and current hidden summary; [offline labels](../../src/toruk_lm/effect_training.py) are separate | **Supported** for the inspected interface; no global leakage proof | Offline outcome labels train an estimator whose runtime features exclude explicit gold/future labels. |
| Useful predictor ranking/calibration is a target — [related-work question](related-work.md) | [Recurrent](../../artifacts/m6-validation-001/recurrent-effect-eval/metrics.json) and [revision diagnostics](../../artifacts/m6-validation-001/revision-effect-eval/metrics.json): four validation labels each, 50% sign accuracy, all retain fallbacks | **Unsupported as an achieved result** | Calibration and useful deployed ranking remain unestablished; low error on tiny NLL effects alone is insufficient. |
| No generated known-fact advantage in the pilot — [M6 results](m6-results.md) | Fourteen evaluations have zero primary; [ordinary raw answers](../../artifacts/m6-validation-001/ordinary-write/predictions.json), [revision raw answers](../../artifacts/m6-validation-001/revision-predictor/predictions.json), [summary](../../artifacts/m6-validation-001/summary.json) | **Supported** as a saved negative result | Under this short single-training-seed protocol, no tested method generated correct corrected/preserved known facts. This does not establish architectural impossibility. |
| Ordinary overall accuracy 33.3% — [M6 table](m6-results.md) | [Ordinary metrics](../../artifacts/m6-validation-001/ordinary-write/metrics.json) and raw outputs: 8/24 correct, all answers `?` | **Supported** as overall score; unsupported as known-fact retrieval | The score comes entirely from unknown/ambiguous probes; primary accuracy and attempted-answer coverage are zero. |
| Held-out studies ran; successful generalization/capacity is unestablished — [README status](../../README.md), [M7 results](m7-results.md) | [Template](../../artifacts/m7-templates-001/summary.json) and [load](../../artifacts/m7-load-001/summary.json) records: all primary scores zero; failed control gate | **Supported**; robustness/capacity benefit unsupported | Exploratory interventions preserve the failure observation; zero change from zero is not successful transfer or a capacity estimate. |
| Histories beyond the local window and varying fact loads were tested — [M7 results](m7-results.md) | [Saved M7 analysis](../../artifacts/m7-analysis.json) describes input ranges and repeated anchors | **Supported as input coverage**, unsupported as successful context use | Tested input length/distance does not establish how much information is usefully retained. |
| Resource advantages remain unestablished — [README resource principles](../../README.md) | [Training/cost summary](../../artifacts/m6-validation-001/summary.json): different parameters/forwarded positions; extra label/fitting cost | **Supported limitation**; equal-update equal-compute interpretation unsupported | Compare complete measured budgets prospectively; state bytes or equal optimizer steps do not establish token, latency or total-memory savings. |
| Per-method latency and small predictor timing — [M6 results](m6-results.md) | [Raw metrics](../../artifacts/m6-validation-001/recurrent-effect-eval/metrics.json); recorded one-run durations exclude some stages | **Supported as historical observations**, unsupported as speed advantage | Report each timing boundary and omitted work; no statistically established end-to-end speedup. |
| Smoke PASS and bounded resource observations — [reproduction guide](../reproducibility.md) | CLI code records stage/run/checkpoint hashes; handoff run used an existing CPU environment and tracked-source export | **Partially supported for clean-machine reproducibility** | Bounded execution passed in the recorded environment; a fresh dependency installation and portable environment lock remain unverified. Smoke is not research replication. |
| Historical M6/M7 can be replayed with retained files — [M7 commands](m7-protocol.md) | [M6 manifest](../../artifacts/m6-validation-001/manifest.json) references absent weights; source identity gate; [current guide](../reproducibility.md) documents blockers | **Unverified** for original-weight replay here | Saved-output integrity/rescoring is distinct from model replay; matching source plus original weights are required. |
| Original generation/scoring kernels are unchanged — architecture wording before this audit | Archived versus current identity mismatch is documented in [reproduction guide](../reproducibility.md) | **Unsupported as a current-state statement** | Historical study required matching kernels; today's exact archival replay is blocked. Architecture wording corrected in this audit. |
| Internal-feature amortization is a candidate distinction — [related work](related-work.md) | Different estimand/representation/training from cited methods; no matched peer experiments; all-fallback pilot | **Unverified as novelty**, supported as a description of a comparison to investigate | A candidate experimental distinction, not an established contribution, priority or superiority claim. |
| Foundation/pipeline verification implies completed research — potential reading of [README status](../../README.md) | README explicitly labels memory prototype and research comparisons partial; [M6/M7 limitations](m7-results.md) remain | **Unsupported inference**; not an explicit success claim in the README | Engineering execution is supported on tested paths; central research hypothesis, generalization and paper readiness remain open. |

Quantitative statements above refer to saved records, not fresh inference in
this audit. One training seed and reused M7 anchors do not supply independent
replication or population confidence. The final test is not model-scored; unit
tests inspect deterministic test labels, so it is not wholly unseen by development.
[Split disclosure](../reproducibility.md). No scientific artifact was changed.

## Substantive wording changes and reasons

- `related-work.md`: replace design-only/future-tense framing with implemented
  local-boundary pilot status. The predictor now exists, but its intended utility
  has not been demonstrated.
- State MGPO/PAIR overlap directly and separate their reuse-horizon or terminal-
  continuation estimands from Toruk's fixed-probe NLL label. The earlier broad
  future-effect wording could suggest a longer horizon than the executed study.
- Add full verified bibliographic identities/status, versioned mechanisms and
  the additional compression/latent-memory/RL/correction papers already present
  in the internal synthesis. Names alone do not establish which work was cited.
- Keep the public README unchanged: it already distinguishes goals, prototype
  execution and unsupported advantages without exposing additional method detail.
- `architecture.md`: replace the unqualified unchanged-kernel assertion with
  historical integrity requirements and the current replay blockers. Preserve
  frozen protocols, result tables and historical reports as recorded.

## Responsible positioning and next decision

Toruk can report an implemented bounded-memory prototype and a traceable negative
single-seed synthetic pilot. It cannot report useful correction/preservation,
reliable learned update selection, comparative efficiency, successful transfer or
established originality. Recurrent memory, adaptive updates and counterfactual
credit have close [primary-source precedents](related-work.md).

Before stronger claims, review an explicit training-role generated-answer
diagnostic that preserves existing split guards, then preregister a bounded
positive-control check. No such run or new experiment is part of this audit.
Literature coverage remains scoped; venue details marked unverified need checking
before formal citation. No IEEE Xplore/index-absence claim was investigated or made.
