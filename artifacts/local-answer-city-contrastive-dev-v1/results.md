# City contrastive loss development v1 — measured result

Scientific gate: **FAIL**. Decision: **STOP_DEVELOPMENT_FAILURE**. Measurement integrity: **PASS**.

One controlled objective intervention: first16 CE plus 0.1 times the mean city confuser softplus with margin 2. Control: unchanged v2 first16 CE. Two initialization seeds (601/947) cross two independent shuffle seeds (1301/1709), ordinary/recurrent, control/contrast. No historical checkpoint is used as a training initialization.

The 96 training documents and 24 development cases are byte-identical to v2. These development cases were already diagnosed; results are adaptive development evidence, not independent generalization. Held-out data remains unopened. Production chat and pretrained backbones are unchanged. No memory or efficiency advantage is claimed.

## Frozen identities and execution

Starting Git HEAD: `916efdd4b63dd63fab08ffabb8ab6e8313dc4bf2`. The working tree already contained the entity-dropout study, resume-integrity adapter and completed v2 diagnosis. Existing edits, frozen sources, raw evidence and ignored weights were preserved. No pull, reset, commit, push, release or deployment.

Protocol/source/data/gates/caps froze before preparation. The single random rehearsal used seed 927113, no study examples and zero optimizer updates. Registration binds its seal and the 34 passing contract/measurement tests. Every registered scientific cell was attempted at most once; no cap, coefficient, seed or gate was changed.

Independent auditor verified 24576 recorded updates and 48 scientific stage seals. It reconstructs native outcomes, vectors, teacher losses, training/auxiliary arithmetic, controls, schedule exposure, token accounting, complete Job costs and the final gates without importing Torch or the training runner.

## Per-cell scores

Each tuple is exact / EOS / malformed / wrong-first / repetition. Training denominator is 96; development denominator is 24. NOT_RUN means not evaluated, never zero accuracy.

| Initialization/shuffle | Model | Arm | Training | Development | Dev city/code/unknown |
| --- | --- | --- | --- | --- | --- |
| i601-s1301 | ordinary | control | 96/96/0/0/0 | 23/24/0/1/0 | 7/8/8 |
| i601-s1301 | ordinary | contrast | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i601-s1301 | recurrent | contrast | 96/96/0/0/0 | 22/24/0/2/0 | 7/7/8 |
| i601-s1301 | recurrent | control | 96/96/0/0/0 | 21/23/2/3/0 | 5/8/8 |
| i601-s1709 | ordinary | contrast | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i601-s1709 | ordinary | control | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i601-s1709 | recurrent | control | 96/96/0/0/0 | 21/24/1/3/0 | 5/8/8 |
| i601-s1709 | recurrent | contrast | 96/96/0/0/0 | 21/24/2/3/0 | 5/8/8 |
| i947-s1301 | ordinary | control | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i947-s1301 | ordinary | contrast | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i947-s1301 | recurrent | contrast | 96/96/0/0/0 | 23/24/0/1/0 | 8/7/8 |
| i947-s1301 | recurrent | control | 96/96/0/0/0 | 23/24/0/1/0 | 7/8/8 |
| i947-s1709 | ordinary | contrast | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i947-s1709 | ordinary | control | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i947-s1709 | recurrent | control | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |
| i947-s1709 | recurrent | contrast | 96/96/0/0/0 | 24/24/0/0/0 | 8/8/8 |

## Matched development gates

| Cell | Exact gain | Newly wrong cases | Fixed cases | Pair gate | Candidate floor |
| --- | ---: | --- | --- | --- | --- |
| i601-s1301-ordinary | +1 | none | v2-dev-012 | True | True |
| i601-s1301-recurrent | +1 | v2-dev-014 | v2-dev-013, v2-dev-018 | False | True |
| i601-s1709-ordinary | +0 | none | none | True | True |
| i601-s1709-recurrent | +0 | none | none | False | False |
| i947-s1301-ordinary | +0 | none | none | True | True |
| i947-s1301-recurrent | +0 | v2-dev-002 | v2-dev-012 | False | True |
| i947-s1709-ordinary | +0 | none | none | True | True |
| i947-s1709-recurrent | +0 | none | none | True | True |

Every previously correct control case must remain correct; every non-ceiling control must improve. A perfect-control tie supplies no improvement evidence. Every candidate must pass exact/category/EOS/format/context-gain floors, both models need positive total gain, and recurrent601 city first NLL must decrease under both shuffles. Aggregates cannot override a failed conjunct.

Recurrent city first NLL i601-s1301: control 1.360309804, contrast 0.901612565; gate True.
Recurrent city first NLL i601-s1709: control 2.018933994, contrast 1.764630205; gate True.

## Complete scoped costs

Parent Job totals already include nested stages; never add them twice. These costs include controllers, cold imports, I/O, descendants, observations and enclosed sealing. Outer observers, editing, registration and reporting outside measured Jobs have unknown full-lifetime cost; no complete-project efficiency claim follows.

| Scope | CPU seconds | Wall seconds | Peak committed bytes | Status |
| --- | ---: | ---: | ---: | --- |
| preparation/budget | 13.187500 | 15.831126 | 695369728 | PASS |
| registered/budget | 518.468750 | 447.199112 | 723910656 | PASS |

| Cell | Fit CPU/wall seconds | Train observation CPU/wall | Dev CPU/wall |
| --- | --- | --- | --- |
| i601-s1301-ordinary-control | 14.265625/15.008713 | 3.750000/4.320593 | 3.468750/4.245888 |
| i601-s1301-ordinary-contrast | 14.984375/15.574400 | 3.781250/4.447817 | 3.531250/4.161730 |
| i601-s1301-recurrent-contrast | 21.437500/21.966567 | 4.078125/4.734311 | 3.828125/4.379322 |
| i601-s1301-recurrent-control | 20.812500/21.492611 | 4.046875/4.713346 | 3.765625/4.526720 |
| i601-s1709-ordinary-contrast | 14.718750/15.507668 | 3.578125/4.327076 | 3.765625/4.321194 |
| i601-s1709-ordinary-control | 14.578125/15.385270 | 3.765625/4.327005 | 3.531250/4.250281 |
| i601-s1709-recurrent-control | 20.718750/21.340575 | 4.078125/4.725807 | 3.656250/4.410859 |
| i601-s1709-recurrent-contrast | 21.375000/22.136876 | 4.109375/4.733339 | 3.828125/4.391190 |
| i947-s1301-ordinary-control | 14.343750/14.936993 | 3.562500/4.347993 | 3.640625/4.252053 |
| i947-s1301-ordinary-contrast | 15.015625/15.688871 | 3.781250/4.359980 | 3.546875/4.178244 |
| i947-s1301-recurrent-contrast | 21.328125/22.005497 | 4.000000/4.784111 | 3.812500/4.406457 |
| i947-s1301-recurrent-control | 20.968750/21.524148 | 3.906250/4.766043 | 3.687500/4.315572 |
| i947-s1709-ordinary-contrast | 15.546875/16.101009 | 3.500000/4.374792 | 3.515625/4.216019 |
| i947-s1709-ordinary-control | 15.109375/15.978921 | 3.843750/4.589655 | 3.421875/4.173791 |
| i947-s1709-recurrent-control | 21.156250/21.954215 | 4.046875/4.781204 | 3.703125/4.283035 |
| i947-s1709-recurrent-contrast | 21.843750/22.453399 | 4.234375/4.865576 | 3.859375/4.398441 |

All completed fits use 692,224 valid byte/EOS targets, 786,432 padded positions and CE weighted mass 876,544. Each logs 4,096 city contrastive contributions, including control diagnostics. Each observation's `token-costs.json` retains request counts, tokens and forward positions; raw predictions, vectors and teacher rows retain per-request CPU/wall costs and replay records.

## Remaining candidate mistakes

| Cell | Case | Expected | Actual | EOS | Malformed | Wrong first |
| --- | --- | --- | --- | --- | --- | --- |
| i601-s1301-recurrent-contrast (dev) | v2-dev-012 | `"la"` | `"?"` | True | False | True |
| i601-s1301-recurrent-contrast (dev) | v2-dev-014 | `"R-7"` | `"V:4"` | True | False | True |
| i601-s1709-recurrent-contrast (dev) | v2-dev-012 | `"la"` | `"?"` | True | False | True |
| i601-s1709-recurrent-contrast (dev) | v2-dev-013 | `"mi"` | `"nZ!6"` | True | True | True |
| i601-s1709-recurrent-contrast (dev) | v2-dev-018 | `"mi"` | `"R2:4"` | True | True | True |
| i947-s1301-recurrent-contrast (dev) | v2-dev-002 | `"V:4"` | `"Q_2"` | True | False | True |

## Evidence and limitations

Frozen design: `plan-final.json`, `registration.json`, `sources/`, protocol and copied inputs. Execution: `registered/execution/stages/` contains every checkpoint, training trace, native answer, vector, teacher loss, token ledger, failure and observer seal. `independent-audit.json` is saved-only verification; `verification/` retains actual repository check commands/results.

This is one intervention, two initialization and two shuffle seeds, one small grammar and a reused development set. Model widths differ; this is not an isolated memory-mechanism or equal-FLOPs comparison. Passing software checks does not establish improved accuracy, reliable transfer or efficiency.

Recommended next action: preserve this failed attempt and perform a saved-only diagnosis of its remaining or introduced errors before considering another intervention.
