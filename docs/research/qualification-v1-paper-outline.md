# Paper outline only: bounded memory qualification and failed template transfer

This is an outline for documenting evidence, not a publication-ready manuscript.
Do not claim architectural novelty, index absence, venue suitability or a win.
Results belong to small conditional byte decoders, not a conversational Toruk LM.

1. **Problem.** Retain distant facts, apply corrections, preserve unrelated facts
   and abstain when unsupported under bounded state. Distinguish selected prompt
   length from all history reads and neural update cost.
2. **Related-work questions.** How does segment recurrence compare with fixed
   learned slots? Transformer-XL uses segment recurrence and relative position
   representations ([Dai et al., 2019](https://arxiv.org/abs/1901.02860)). How
   does direct learned state differ from recurrent memory tokens? RMT trains
   memory tokens passed between segments
   ([Bulatov et al., 2022](https://arxiv.org/abs/2207.06881)). How does a bounded
   internal state differ from external retrieval? Memorizing Transformers use
   approximate nearest-neighbor lookup over stored representations
   ([Wu et al., 2022](https://arxiv.org/abs/2203.08913)). How should evidence
   position be controlled? Lost in the Middle measures sensitivity to evidence
   position in QA and key-value retrieval
   ([Liu et al., 2023](https://arxiv.org/abs/2307.03172)). These primary author
   records were searched and opened on 3 November 2026. This is a starting
   bibliography, not a comprehensive related-work or IEEE Xplore review.
3. **Method.** Describe public interfaces, finite-symbol supervised addressing,
   conditional byte generation, fixed state and suffix. Reference private
   implementation notes without copying them into public release artifacts.
   Clearly distinguish ordinary LM, controlled recurrent LM, chat selector,
   integrated prototype and third-party pretrained chat backbone.
4. **Baselines.** Shared ordinary decoder weights for recent, lexical and external
   selector comparisons; separately trained integrated decoder at matched step
   budget. Disclose different effective capacities and selector distribution
   shift. Missing historical M6 weights are unavailable, not substituted.
5. **Experiments.** Frozen qualification protocol; 2 historical training seeds,
   3 fresh final seeds, 7 categories, +0/+8/+32 irrelevant turns. Exact pair
   scoring for multi-fact worlds. State removal, correction bypass, destructive
   preservation intervention, capacity mask and selector-position ablation.
6. **Results.** Insert qualification report tables, raw failures and paired
   confidence intervals. Contrast historical v1 known-fact gains with weak
   absolute quality and unsupported-answer regressions. Separate prompt counts,
   all history scans, update workload and measured latency/RSS. Include failed
   quality gates and refrain from inferring benefit from all-abstention ties.
7. **Limitations.** Tiny synthetic domain, shared vocabulary, only two training
   seeds, historical supervised slot bias, overlapping task categories,
   inference-distribution-shift interventions, serial fresh-process measurements
   on a shared host, concurrent verification, sampled RSS limitations, no FLOP
   or energy profiling, no integration into pretrained chat. Three final seeds
   do not solve training-seed uncertainty or establish natural conversation.
8. **Reproducibility.** Link frozen protocol, raw outputs, scoring/evaluation code,
   source snapshot, exact commands/exit codes, package versions, checkpoint and
   data identities, local tests/build, failures and exact-commit remote CI.
   Explicitly preserve Git-ignored weights locally for transfer; a public Git
   clone alone does not contain these checkpoints.

Bounded next experiment (proposed, not run here): train the existing small
architecture on mixed record/query word orders under the same two-seed,
800-step CPU budget. On development only, require >=80% known-fact accuracy,
>=70% correction/preservation and <=5% unsupported answers before opening a new
final grammar. Measure router and decoder accuracy separately. If development
fails, stop and retain that negative result. Never tune on this qualification set.
