# Memory research assessment

Rechecked 2026-10-24 (Asia/Calcutta), source commit
`a2e1884efe9f122bec00fa55cb50a57bf811fe57`. Primary arXiv metadata and versioned
method sections were inspected, with proceedings where accessible. Bibliographic
facts below are separated from our interpretation of overlap. This is a scoped
review, not an exhaustive originality search or an index-coverage assessment.

Toruk is an **empirical investigation of bounded memory and local update-effect
prediction**. The recurrent model and predictor execute, but useful generated
correction/preservation and learned decision benefit remain unsupported. The
pilot estimates retain-versus-write answer NLL at one final-history boundary,
not arbitrary long-horizon update value. Earlier writes still occur. See
[actual implementation](m3-implementation.md), [pilot protocol](m6-validation-protocol.md),
[negative results](m6-results.md) and [claim audit](claims-audit.md).

## Verified bibliography

Dates distinguish initial preprint year from inspected revision/publication.
For entries marked arXiv, that status is verified; a peer-reviewed venue is
**unverified here**, not asserted absent. No IEEE Xplore search was conducted.

| Work and exact title | Authors (as listed by primary source) | Verified year / status and inspected version |
| --- | --- | --- |
| [Recurrent Memory Transformer](https://arxiv.org/abs/2207.06881) | Aydar Bulatov, Yuri Kuratov, Mikhail S. Burtsev | 2022; [NeurIPS 2022 proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/hash/47e288629a6996a17ce50b90a056a0e1-Abstract.html); arXiv v2, 2022-12-08. Proceedings transliterate Kuratov as Yury. |
| [Titans: Learning to Memorize at Test Time](https://arxiv.org/abs/2501.00663) | Ali Behrouz, Peilin Zhong, Vahab Mirrokni | arXiv v1, submitted 2024-12-31 (identifier begins 2501); venue unverified here |
| [Gated Delta Networks: Improving Mamba2 with Delta Rule](https://arxiv.org/abs/2412.06464) | Songlin Yang, Jan Kautz, Ali Hatamizadeh | Initial preprint 2024; inspected v3, 2025-03-06, author metadata says ICLR 2025 camera ready; OpenReview venue page blocked by browser verification |
| [Learning What to Remember: Long-horizon Counterfactual Memory Optimization](https://arxiv.org/abs/2609.37930) (MGPO) | Jiaming Tang, Mingyan Liu, Armin Sarabi | arXiv v1, 2026-09-29; venue unverified here |
| [Adapting Context Compression for Long-Horizon Agents with Counterfactual Continuations](https://arxiv.org/abs/2609.36526) (PAIR) | Guanghui Min, Liang Wu, Mingjia Shi, Yinhan He, Mayank Darbari, Liangjie Hong, Chen Chen | arXiv v1, 2026-09-29; venue unverified here |
| [Compressive Transformers for Long-Range Sequence Modelling](https://arxiv.org/abs/1911.05507) | Jack W. Rae, Anna Potapenko, Siddhant M. Jayakumar, Timothy P. Lillicrap | arXiv v1, 2019-11-13; venue unverified here; attempted OpenReview access failed |
| [MEMORYLLM: Towards Self-Updatable Large Language Models](https://arxiv.org/abs/2402.04624) | Yu Wang, Yifan Gao, Xiusi Chen, Haoming Jiang, Shiyang Li, Jingfeng Yang, Qingyu Yin, Zheng Li, Xian Li, Bing Yin, Jingbo Shang, Julian McAuley | 2024; [ICML 2024, PMLR 235](https://proceedings.mlr.press/v235/wang24s.html); arXiv v2, 2024-05-26 |
| [Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning](https://arxiv.org/abs/2508.19828) | Sikuan Yan, Xiufeng Yang, Zuchao Huang, Ercong Nie, Zifeng Ding, Zonggen Li, Xiaowen Ma, Jinhe Bi, Kristian Kersting, Jeff Z. Pan, Hinrich Schütze, Volker Tresp, Yunpu Ma | Initial preprint 2025; inspected arXiv v5, 2026-01-14; venue unverified here |
| [Supersede: Diagnosing and Training the Memory-Update Gap in LLM Agents](https://arxiv.org/abs/2606.27472) | Vedant Patel | arXiv v1, 2026-06-25; venue unverified here |
| [Reclaim Evaluation: A Lossy Memory Is Worse Than an Empty One](https://arxiv.org/abs/2606.25449) | Alex Kwon | Initial preprint 2026; inspected arXiv v5, 2026-07-21; venue unverified here |

The MEMORYLLM citation is Wang et al.'s self-updatable latent-memory paper;
similarly named feed-forward-memory papers are different works. Do not merge
their authors, venues or mechanisms by title keyword.

## Mechanism comparison

The verified-mechanism column paraphrases primary method sections. Shared ground
and differences are **our interpretation**, relative to the implemented Toruk
pilot. No peer method was run as a Toruk baseline, and peer-paper scores cannot
rank Toruk because tasks, training, scale and cost accounting differ.

| Work | Verified mechanism | Shared ground with Toruk | Specific difference | Evidence or citation |
| --- | --- | --- | --- | --- |
| RMT | Recurrent read/write memory tokens; task gradients propagate across segments | Bounded neural segment state and delayed gradient credit | Toruk reads slots through added cross-attention and forms a gated proposal; neither recurrence nor gradients are new | [v2 §3](https://arxiv.org/html/2207.06881v2#S3) |
| Titans | Fast neural-memory weights updated by associative-loss gradients, momentum and forgetting | Adaptive retention alongside local attention | Toruk learns a feed-forward slot writer and offline local-effect estimator, not test-time gradient updates to associative weights | [v1 §3.1](https://arxiv.org/html/2501.00663v1#S3.SS1) |
| Gated DeltaNet | Data-dependent matrix decay plus delta-rule key/value updates | Selective state updates and forgetting | Toruk's writer lacks the matrix online-regression update; a different state interface does not imply benefit | [v3 §3.1](https://arxiv.org/html/2412.06464v3#S3.SS1) |
| MGPO | Paired pre/post-rewrite utility on shared downstream targets; reuse-horizon gains train a textual writer | Counterfactual downstream credit for memory changes | Toruk regresses one-boundary answer-NLL differences from internal features; it does not implement MGPO's reuse-horizon credit objective | [v1 §§2.1–2.4](https://arxiv.org/html/2609.37930v1#S2) |
| PAIR | Same restored agent/environment boundary, pre/post-compression continuations with further compression disabled; prompt adaptation | Local paired interventions and harmful-update diagnosis | Toruk estimates retain/write NLL on fixed answer probes, not agent terminal reward/interaction burden or compression-prompt optimization | [v1 §§3.2,4](https://arxiv.org/html/2609.36526v1#S3.SS2) |
| Compressive Transformer | Recent activations plus compressed older activations; compression reconstruction losses | Learned bounded representation of earlier context | Toruk uses gated slots rather than a recent/compressed activation hierarchy and has no attention-reconstruction objective | [v1 §3](https://arxiv.org/html/1911.05507v1#S3) |
| MEMORYLLM | Layerwise latent-memory pool self-updates; random dropping maintains size | Internal latent memory, knowledge updates and retention | Toruk uses its segment writer/retain intervention rather than this pool-replacement mechanism | [v2 §3](https://arxiv.org/html/2402.04624v2#S3) |
| Memory-R1 | RL trains structured external-memory operations and an answer agent | Learned update selection using downstream correctness | Toruk fits paired continuous NLL effects, not RL over textual ADD/UPDATE/DELETE/NOOP operations | [v5 §3](https://arxiv.org/html/2508.19828v5#S3) |
| Supersede | Bounded textual notes; current-versus-stale answer rewards train a memory policy | Correcting changed facts and evaluating stale answers | Toruk trains synthetic correction/preservation losses over internal memory, not conversational note maintenance with GRPO | [v1 method/evaluation](https://arxiv.org/html/2606.27472v1) |
| Reclaim Evaluation | Fixed-budget memory conditions vary retained source versus conclusion; corrections scored for exact recovery | Correction after lossy memory and controlled retention comparisons | Toruk does not isolate source recoverability at a positive-learning regime; zero primary accuracy cannot identify this effect | [v5 §3](https://arxiv.org/html/2606.25449v5#S3) |

Submission-history sources: [RMT](https://arxiv.org/abs/2207.06881),
[Titans](https://arxiv.org/abs/2501.00663),
[Gated DeltaNet](https://arxiv.org/abs/2412.06464),
[MGPO](https://arxiv.org/abs/2609.37930),
[PAIR](https://arxiv.org/abs/2609.36526).

## Narrowed research question

Can an estimator over bounded internal state improve update selection once the
models demonstrably learn the factual task? The current pilot does not establish
this: all generated known-fact primary scores are zero, and predictor validation
decisions fall back to retain. Positive task-learning controls, useful ranking,
calibration, independent training seeds and complete resource accounting remain
needed. [M6 results](m6-results.md), [M7 limits](m7-results.md).

The next proposed step is an explicit training-role generated-answer diagnostic,
with split guards preserved, before another research run. The existing evaluator
accepts validation data only; do not bypass it. This is future work, not an
experiment or positive result from this review.

Paired counterfactual supervision, recurrence, gating, knowledge updating and
correction evaluation have close precedents above. Internal-feature amortization
is a candidate experimental distinction, not established novelty or superiority.
Literature coverage and venue verification remain incomplete as marked; no absence
from any publication index, publication acceptance or priority claim is made.
