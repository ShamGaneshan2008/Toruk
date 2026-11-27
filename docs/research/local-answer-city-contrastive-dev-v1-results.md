# City contrastive loss development v1: failed reliability gate

27 November 2026. **FAIL — STOP_DEVELOPMENT_FAILURE. Measurement integrity PASS.**
The single registered attempt completed all 16 fits and 48 scientific stages.
No cell was retried, no gate or cap changed, and held-out data remained unopened.

The candidate adds only `0.1 * mean_city softplus(2 + z_confuser - z_gold)` to
v2 first16 CE. The matched control retains v2 first16 unchanged. Initialization
601/947 crosses shuffle 1301/1709 in both ordinary and recurrent models. Training
uses the original 96 documents, 1,536 updates, batch 8 and unchanged decoding.
All controls reproduced the old first16 final tensor hashes and native answers.

All 16 cells achieved training exact/EOS 96/96, with zero malformed, wrong-first
or repetitive answers. Development exact control → candidate:

| Initialization / shuffle | Ordinary /24 | Recurrent /24 |
| --- | ---: | ---: |
| 601 / 1301 | 23 → 24 | 21 → 22 |
| 601 / 1709 | 24 → 24 | 21 → 21 |
| 947 / 1301 | 24 → 24 | 23 → 23 |
| 947 / 1709 | 24 → 24 | 24 → 24 |

Aggregate 184/192 → 186/192 does not pass the frozen gates. Recurrent 601/1301
newly fails code case `v2-dev-014` (R-7 → V:4). Recurrent 947/1301 newly fails
`v2-dev-002` (V:4 → Q_2), offsetting its city correction. Recurrent 601/1709
remains at 21/24, city 5/8, with two malformed answers. These violate casewise
no-regression, positive non-ceiling gain and candidate-floor requirements.
The recurrent601 city first-NLL gate passes at both shuffle seeds but cannot
override those failures. All six remaining candidate mistakes start at the first
byte; all reach EOS. Their native outputs remain unmodified.

The independent auditor reconstructed 24,576 recorded updates, all native scores,
training and auxiliary arithmetic, control parity, token accounting, gates and
closed process-tree costs. It made zero model forwards and imported no model or
training runner. The original v2 negative decision remains unchanged.

| Non-overlapping measured scope | CPU seconds | Wall seconds |
| --- | ---: | ---: |
| Preparation, including contracts and zero-update rehearsal | 13.187500 | 15.831126 |
| Registered study, including nested stages | 518.468750 | 447.199112 |
| Independent saved-only audit | 3.953125 | 9.604017 |
| Repository verification | 126.390625 | 165.022248 |

Nested costs are already included in their parents. Registered peak commit is
723,910,656 bytes; peak logical output 46,445,277 bytes; maximum monitoring gap
0.104706 seconds; zero active processes and forced terminations at closure.
Outer observer, editing, preflight, registration and reporting lifetimes outside
these Jobs are not fully measured. No total-efficiency claim follows.

Validation: 34 pre-fit contracts and 44 post-run focused tests passed; Ruff
lint/format, default/Linux mypy, focused typing of both new scripts, frozen-source,
dependency and CLI checks passed. The first preflight typing failure was corrected
before source freeze; its log is preserved. Readable working/cached Git diff
checks passed. Full pytest and hosted CI were not run: the full suite includes
unrelated fits and held-out work. No production code, dependency or historical
source/evidence was changed; everything remains uncommitted.

Evidence:

- [Frozen protocol](local-answer-city-contrastive-dev-v1-protocol.md).
- [Complete per-cell outcomes, regressions and costs](../../artifacts/local-answer-city-contrastive-dev-v1/results.md).
- [Independent audit](../../artifacts/local-answer-city-contrastive-dev-v1/independent-audit.json).
- [Execution summary](../../artifacts/local-answer-city-contrastive-dev-v1/registered/execution/summary.json).
- [Plan](../../artifacts/local-answer-city-contrastive-dev-v1/plan-final.json) and
  [registration](../../artifacts/local-answer-city-contrastive-dev-v1/registration.json).
- [Repository checks](../../artifacts/local-answer-city-contrastive-dev-v1/verification/checks.json).

Plan SHA-256: `7cc2180d32f01afda1d2852e6d0bd92cff6f00b3a497482efc981e015f8d87ef`.
Registration: `36a855d22431712a83b85b92c8e03faecdb0b944312c0bb431bd8d2fa01e66f2`.
Registered budget seal: `743180ff274e83f9a86219dbe03d8fd8b019e73099f1b38a278bec5ac9631e1b`.

Limitations: one small grammar, two initialization and shuffle seeds, reused
diagnosed development cases, different model widths and unmeasured outer costs.
The 16 checkpoints remain local and ignored; metadata alone cannot recover their
bytes. These observations establish no independent generalization, memory or
chatbot advantage. The pretrained chat backbone is unchanged and uninvolved.

Recommended next action: preserve this failed attempt and perform a saved-only
diagnosis of the introduced code errors and persistent recurrent601 city errors
before considering another intervention. Do not extend or retry this study.
