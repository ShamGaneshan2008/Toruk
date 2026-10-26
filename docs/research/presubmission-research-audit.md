# Toruk pre-submission research audit

Internal skeptical review, 2026-10-25 (Asia/Calcutta). **Overall: Ready to draft
with explicit evidence gaps.** This permits an honest internal paper about a
bounded prototype, reproducibility and failed known-fact learning. It does not
establish a publishable memory advantage or readiness to submit that claim.

Repository root `C:/Users/susee/VScode Project/Toruk`; branch `main`; full commit
`e944caeca2415de12e5694682507941e1f815b3a`. At entry, the adviser review,
meeting rehearsal and their check/evidence files were untracked. They were
preserved. This audit adds only this report and new audit records. Older documents
refer to their own dated base commits and must not be read as current Git or CI
status ([entry snapshot](../../artifacts/presubmission-20261025-evidence/pre-edit-state.json)).

## Sources and verification boundary

The latest [adviser review](adviser-review.md), [meeting rehearsal](adviser-meeting-rehearsal.md),
[seven-paper related-work audit](../internal/m8/related-work.md), [M8 synthesis/audit](../internal/m8/audit.md),
[internal draft](../internal/m8/paper-draft.md), [public reproduction guide](../reproducibility.md)
and [internal handoff](../internal/m8/reproduction.md) exist. **Missing:** a
decision memo and a separately named evidence-synthesis report. The M8 audit is
the closest existing synthesis. There is no single current project specification;
the [architecture note](../architecture.md), [historical M3 design](m3-memory-contract.md),
[implemented M3 deviations](m3-implementation.md) and frozen [M6](m6-validation-protocol.md)/[M7](m7-protocol.md)
protocols together define the current scope. The historical M4/M5 prerequisite
notes are dated gate reports, superseded by the M6 implementation
([milestones](../milestones.md)).

The current [source/evidence inventory](../../artifacts/presubmission-20261025-evidence/inventory.json)
finds **34/34 source files and 276/276 evidence entries** matching the retained
[M8 seal](../../artifacts/m8-handoff/manifest.json). Fresh independent rescoring
passed for **281 historical manifest entries, 59 evaluations, 1,416 answers**;
every row includes its protocol, source package, bound checkpoint and raw
prediction identity ([fresh audit](../../artifacts/presubmission-20261025-evidence/rescore/audit.json),
[rows](../../artifacts/presubmission-20261025-evidence/rescore/results.csv),
[command log](../../artifacts/checks/presubmission-20261025-evidence.log)).
Both [versioned configs](../../configs/reproduce-primary-v1.json) and
[smoke config](../../configs/reproduce-smoke-v1.json) passed current validation.
Stored replay comparisons passed again: [M6 14/14, 336 answers](../../artifacts/presubmission-20261025-evidence/m6-parity/comparison.json),
[template cell 24/24](../../artifacts/presubmission-20261025-evidence/template-parity/comparison.json),
[load cell 24/24](../../artifacts/presubmission-20261025-evidence/load-parity/comparison.json).
These last checks compare previously generated outputs; this audit ran **no new
model inference or training**. The other 43 M7 evaluations were rescored from
sealed predictions, not regenerated in this task or the M8 replay.

## Scientific argument: where the chain holds

| Link | Status | Review finding |
| --- | --- | --- |
| Research question | **Verified** as a narrow question | The [frozen M6 protocol](../../artifacts/m6-validation-001/protocol.json) asks whether a final-write effect predictor improves generated corrected/preserved answers over simpler policies. Its separate broad goal is useful bounded memory; keep these scopes distinct. |
| Hypothesis | **Partially verified** as a testable hypothesis | The [M6 falsification rule](../../artifacts/m6-validation-001/protocol.json) names no joint gain or a correction/preservation tradeoff. A precise future success threshold and matched total-resource budget are absent. The pilot is a negative result, but failure of all controls to learn prevents an informative mechanism test. |
| Method | **Verified** for the bounded prototype | The [decoder](../../src/toruk_lm/model.py), [four-slot recurrent read/write path](../../src/toruk_lm/recurrent.py), [revision loss/training](../../src/toruk_lm/controlled.py), [paired-label generator](../../src/toruk_lm/effect_training.py) and [runtime predictor](../../src/toruk_lm/effect_predictor.py) implement the M6 description. The old M3 proposal specified eight slots and two-segment TBPTT; the actual pilot uses four slots and whole bounded-document backpropagation ([deviation record](m3-implementation.md)). No protected revision, general sequential controller or mid-document resume is implemented. |
| Experiment design | **Partially verified** | Frozen seeds, worlds, answer budget, negative-result retention and validation-only roles are recorded in the [M6 protocol](../../artifacts/m6-validation-001/protocol.json) and [M7 protocols](../../artifacts/m7-templates-001/protocol.json). Ordinary/recurrent worlds and step budgets align, but model parameters, FLOPs, branch/predictor training and total inference costs do not. M7 reuses four anchors; its template and load contrasts change more than one property. |
| Measurements | **Verified** for stored observations | The [fresh table](../../artifacts/presubmission-20261025-evidence/rescore/tables.md) reports 14 M6 and 45 M7 evaluations, each 24 generated answers. Known-fact macro accuracy is zero throughout. M7's two data seeds both sit at the floor, with descriptive sample SD zero; only training seed 23 exists. Teacher-forced CE, coverage and resource counters are separately recorded. |
| Conclusion | **Partially verified** for a negative pilot; **blocked** for a positive mechanism claim | The evidence supports “the tested configurations did not generate correct known-fact answers.” It does not identify whether memory, training duration, data difficulty, optimization or decoding caused failure. The learned M7 predictor fell back on all 32 final decisions, so its deployed MLP was not tested on those cases. Useful recall, revision, transfer, capacity onset and efficiency remain unsupported ([M7 analysis](m7-results.md), [fallback rows](../../artifacts/presubmission-20261025-evidence/rescore/audit.json)). |

**Leakage audit.** The [world generator](../../src/toruk_lm/worlds.py) assigns
split/world identities before events, uses a separate backward oracle to check
the forward truth table, and exposes only history plus current question through
`ObservedPrompt`. [Tests](../../tests/test_worlds.py) check split separation,
fingerprints, oracle agreement and no-gold projection. [M7 evaluation-only
manifests](../../artifacts/m7-templates-001/data/control/manifest.json) forbid
fitting. Those safeguards are real but limited: the same tests inspect generated
test labels, including deterministic cases matching the registered seed-17 split.
There is **no retained final-test model score**, but the split is **not wholly
unseen** ([M8 disclosure](../internal/m8/audit.md)). No retained program record
can establish absence of all outside inspection. A future confirmatory test needs
a newly frozen split and access record.

**Metric and uncertainty audit.** The four-group macro generated-answer measure
corresponds to corrected/preserved facts; [scoring code](../../src/toruk_lm/worlds.py)
and [independent rescorer](../../src/toruk_lm/reproducibility.py) check raw
answers against offline truth. Overall exact accuracy also counts unknown and
ambiguous probes. The ordinary model's 33.3% overall result comes only from `?`
and zero attempted-answer coverage ([M6 raw answers](../../artifacts/m6-validation-001/ordinary-write/predictions.json),
[M6 metrics](../../artifacts/m6-validation-001/ordinary-write/metrics.json)).
M7 has 1,080 answers but only four reused semantic anchors; answer count is not
an independent sample size. No training-seed variance or justified population
confidence interval can be inferred. M7's preregistered 50% control gate for
degradation/capacity onset was never met ([M7 protocol](m7-protocol.md)).

**Resources and failure retention.** The original M6 [cost record](../../artifacts/m6-validation-001/summary.json)
reports 100 LM steps including profiles, 101,256 training forward positions,
32 paired branches, 200 predictor steps, 87.341 seconds of driver time and a
352,514,048-byte cumulative process peak. The [registered check](../../artifacts/checks/m6-registered-pilot.json)
records full process time; the [failed tiny pilot](../../artifacts/m6-failed-tiny-001/stages.json)
and [M8 limitations](../internal/m8/limitations.md) retain other failed work.
[M7 study records](../../artifacts/m7-templates-001/summary.json) and
[load records](../../artifacts/m7-load-001/summary.json) retain subsequent inference
work. Those are recorded CPU observations; they are not a complete CPU-hour total,
per-model allocation measure or matched-resource efficiency result. A 512-byte
four-slot state ([M6 training table](m6-results.md)) does not imply fewer history
tokens read. Passing software tests or replay parity establishes execution and
traceability, not the scientific hypothesis.

**Related-work scope.** The [latest local review](../internal/m8/related-work.md)
audits seven specified versions. [RMT v2](https://arxiv.org/html/2207.06881v2)
already uses bounded continuous segment memory;
[Titans v1](https://arxiv.org/html/2501.00663v1) and
[Gated Delta Networks v3](https://arxiv.org/html/2412.06464v3) study adaptive
memory updates. [MGPO v1](https://arxiv.org/html/2609.37930v1) and
[PAIR v1](https://arxiv.org/html/2609.36526v1) directly overlap with paired
downstream memory credit. [Compressive Transformer v1](https://arxiv.org/html/1911.05507v1)
and [ICAE v4](https://arxiv.org/html/2307.06945v4) cover compressed prior
representations and learned continuous slots. The sources support a possible
Toruk setting distinction—an amortized internal-state estimator for one final
write—without establishing its value or originality. There is no head-to-head
experiment with these papers and no exhaustive originality search. No claim is
made about inclusion in any publication index.

## Claim-by-claim evidence matrix

“Reproducible?” distinguishes local rescoring/replay from full retraining or
independent external replication. Verdicts assess the **proposed wording**;
the last column supplies safer wording when needed.

| Proposed paper claim | Evidence and exact location | Reproducible? | Main caveat | Verdict and narrower wording |
| --- | --- | --- | --- | --- |
| A small causal LM and bounded recurrent state are implemented | [Model](../../src/toruk_lm/model.py), [memory](../../src/toruk_lm/recurrent.py), [M6 bound configurations](../../artifacts/presubmission-20261025-evidence/rescore/audit.json) | Source/checkpoint identities verified locally | Execution is not useful recall | **supported** — “We implemented and tested a bounded prototype.” |
| Correction/preservation training terms and ablations execute | [Loss code](../../src/toruk_lm/controlled.py), [protocol](../../artifacts/m6-validation-001/protocol.json), [raw evaluation rows](../../artifacts/presubmission-20261025-evidence/rescore/results.csv) | Stored results rescored; historical tests recorded | Objective contribution unidentifiable at floor | **supported** for implementation only. |
| A final-write effect model is trained from paired future-answer labels | [Label/fit code](../../src/toruk_lm/effect_training.py), [training labels](../../artifacts/m6-validation-001/revision-labels-train/labels.json), [predictor metrics](../../artifacts/m6-validation-001/revision-effect-model/metrics.json), [runtime](../../src/toruk_lm/effect_predictor.py) | Checkpoint/label bindings audited; fit not newly repeated | One boundary per world; M7 support mismatch | **supported** for pipeline execution; no learned decision benefit follows. |
| The ordinary foundation reaches 1.2481 nats per byte/EOS on its fixture | [Foundation metrics](../../artifacts/foundation-001/eval/metrics.json), [fixture manifest](../../artifacts/foundation-001/data/manifest.json) | Retained fixture/metrics; not rerun here | Repetitive smoke text, not factual QA | **supported** as a scoped pipeline diagnostic. |
| M6 evaluates 14 configurations / 336 answers | [Frozen protocol](../../artifacts/m6-validation-001/protocol.json), [fresh result rows](../../artifacts/presubmission-20261025-evidence/rescore/results.csv), [parity check](../../artifacts/presubmission-20261025-evidence/m6-parity/comparison.json) | Stored answers rescored; archived inference parity 336/336 | Single training seed, validation only | **supported** — call it a pilot. |
| M7 evaluates 45 cell/method combinations / 1,080 answers | [Template protocol](../../artifacts/m7-templates-001/protocol.json), [load protocol](../../artifacts/m7-load-001/protocol.json), [fresh rows](../../artifacts/presubmission-20261025-evidence/rescore/results.csv) | All rescored; two cells/48 answers have archived replay parity | Four anchors reused; 43 cells not regenerated in M8 | **supported** for stored exploratory evaluations. |
| Known-fact macro accuracy is zero in every M6/M7 evaluation | [Fresh generated table](../../artifacts/presubmission-20261025-evidence/rescore/tables.md), [raw prediction identities](../../artifacts/presubmission-20261025-evidence/rescore/audit.json) | Yes, independent rescoring; selected replay parity | Does not isolate why learning failed | **supported** as a negative observed result. |
| Ordinary overall accuracy is 33.3% | [Ordinary predictions](../../artifacts/m6-validation-001/ordinary-write/predictions.json), [metrics](../../artifacts/m6-validation-001/ordinary-write/metrics.json) | Rescored | All credit is `?`; answer coverage zero | **supported** only with abstention qualification. |
| The learned predictor improves deployed answers or decisions | [M6 effect policy metrics](../../artifacts/m6-validation-001/revision-effect-eval/metrics.json), [M7 fallback rows](../../artifacts/presubmission-20261025-evidence/rescore/audit.json) | Stored diagnostics checkable | Revision predictor falls back 4/4 in M6 and 32/32 in M7; validation regret exceeds heuristic | **unsupported** — “No deployed predictor benefit was demonstrated.” |
| Predictor calibration and ranking are reliable | [Four-label diagnostics](../../artifacts/m6-validation-001/revision-effect-eval/metrics.json), [M6 results](m6-results.md) | Metrics retained | Four validation labels; 50% sign ranking and all fallback | **unsupported** — report raw diagnostics without reliability language. |
| Revision preserves unrelated facts and incorporates corrections | [Four-group scores](../../artifacts/presubmission-20261025-evidence/rescore/tables.md), [failure examples](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json) | Stored answers rescored | Every known-fact group is at zero | **unsupported** — “Revision objective runs; successful behavior was not observed.” |
| An obsolete-value answer proves stale-memory retrieval | [Raw example](../../artifacts/m7-templates-001/control/revision-predictor/predictions.json), [analysis](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json) | Raw text checkable | Wrong outputs and failed unrelated controls prevent causal attribution | **unsupported** — “Some outputs match earlier values.” |
| M7 demonstrates transfer across templates/load | [M7 protocols](m7-protocol.md), [results](m7-results.md), [fresh rows](../../artifacts/presubmission-20261025-evidence/rescore/results.csv) | Saved outputs rescored | Zero-to-zero; rendering changes length; authority cues change | **unsupported** — “Failure persisted under these specified shifts.” |
| A memory capacity/degradation boundary is measured | [M7 gate](../../artifacts/m7-templates-001/protocol.json), [per-cell analyses](../../artifacts/m7-load-001/control/revision-predictor/analysis.json) | Inputs/strata retained | Control below preregistered 50% gate | **unsupported** — “2/4/8 slots and finite input ranges were exercised; onset is unidentifiable.” |
| Baselines are fair at equal total resources | [M6 protocol matching field](../../artifacts/m6-validation-001/protocol.json), [model/cost table](m6-results.md), [cost record](../../artifacts/m6-validation-001/summary.json) | Budgets visible | Equal steps/worlds do not match FLOPs, parameters or label costs | **unsupported** — “Worlds, probes and optimizer steps were matched.” |
| The system improves time or memory efficiency | [Cost summary](../../artifacts/m6-validation-001/summary.json), [M7 measured costs](m7-results.md) | Scoped observations retained | No matched total-cost or robust speed comparison | **unsupported** — report state bytes, tokens read and process time separately. |
| The original test split was untouched | [Test inspection](../../tests/test_worlds.py), [M8 disclosure](../internal/m8/audit.md) | Access visible in source; no final model score recorded | Deterministic test labels were inspected | **unsupported** — “No retained final-test model score; prior label exposure disclosed.” |
| Full historical results reproduce from a fresh environment | [Reproduction guide](../reproducibility.md), [M8 handoff](../internal/m8/reproduction.md), [stored parity checks](../../artifacts/presubmission-20261025-evidence/m6-parity/comparison.json) | Rescoring and selected inference replay yes; full retraining and independent setup unverified | Checkpoints local/ignored; full M7 regeneration and fresh dependency provisioning absent | **partially supported** — specify each reproduced operation. |
| Resource use is completely accounted for | [M6 cost record](../../artifacts/m6-validation-001/summary.json), [failed pilot](../../artifacts/m6-failed-tiny-001/stages.json), [M7 resources](m7-results.md) | Recorded scopes auditable | Test work, historical tuning and total CPU-hours incomplete | **partially supported** — “Measured pilot costs and omissions are reported.” |
| The method has a demonstrated original or superior technical contribution | [Seven-paper audit](../internal/m8/related-work.md), [candidate estimator](../../src/toruk_lm/effect_predictor.py), [results](../../artifacts/presubmission-20261025-evidence/rescore/tables.md) | Paper versions and local implementation inspectable | Direct conceptual overlap; no demonstrated benefit or direct literature baselines | **unsupported** — describe the tested setting and prior overlap. |
| Current HEAD has passing remote CI | [Workflow](../../.github/workflows/ci.yml), [retained older-run record](../../artifacts/m8-review/remote-ci.json) | No live current-HEAD run inspected here | Older record is for `34d3037310050bd8e5dd2e52c2566c2fd9a21b78`, not this HEAD | **unverified** — “Current-HEAD GitHub Actions status was not checked.” |
| Software checks establish the research hypothesis | [Historical 34-test log](../../artifacts/checks/m8-ci-final-tests.log), [current scientific table](../../artifacts/presubmission-20261025-evidence/rescore/tables.md) | Historical test record; no fresh suite in this doc task | Tests cover execution/invariants, not positive answer accuracy | **unsupported** — keep software and scientific claims separate. |
| Synthetic-data provenance and permission are resolved for release | [Generator](../../src/toruk_lm/worlds.py), [data manifest](../../artifacts/m6-validation-001/data/manifest.json), [reproduction guide](../reproducibility.md), [license inventory](../../artifacts/presubmission-20261025-evidence/inventory.json) | Local data generation is traceable | No project LICENSE or approved public checkpoint transfer | **partially supported** for provenance; external redistribution permission is **unverified**. |

## Readiness by area

| Area | Rating | Evidence and remaining condition |
| --- | --- | --- |
| Research question and scope | **Ready** | [M6 question/falsification](m6-validation-protocol.md) is narrow; frame this as a bounded pilot. |
| Implementation description | **Ready** | Code matches the [implemented M3](m3-implementation.md) and [M6 protocol](m6-validation-protocol.md) when historical M3 proposal is labeled as such. |
| Experimental design | **Needs work** | Frozen validation and exploratory protocols exist, but controls fail the learning gate; future confirmatory split/design is absent ([M7 protocol](m7-protocol.md)). |
| Baseline fairness | **Blocked** for an advantage claim | [M6 matching/costs](m6-results.md) omit total-resource equality and literature baselines. |
| Statistical and seed reporting | **Blocked** for generalization claims | One training seed, two M7 data seeds and shared worlds; [per-seed analysis](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json) cannot support training-seed inference. |
| Reproducibility | **Needs work** | [Rescoring](../../artifacts/presubmission-20261025-evidence/rescore/audit.json) and selected [replay parity](../../artifacts/presubmission-20261025-evidence/m6-parity/comparison.json) pass; full retraining, complete M7 inference regeneration, fresh dependency install and independent reproduction remain outstanding ([handoff](../internal/m8/reproduction.md)). |
| Related-work coverage | **Needs work** | Seven primary versions are scoped and overlap disclosed ([audit](../internal/m8/related-work.md)); wider search and direct comparative experiments are missing. |
| Error and limitation analysis | **Ready** for the negative pilot | [M6](m6-results.md), [M7](m7-results.md) and [M8 limits](../internal/m8/limitations.md) retain null results, malformed answers, fallback and confounding. Causal failure attribution remains open. |
| Research ethics and data provenance | **Needs work** | Synthetic worlds are locally generated ([source](../../src/toruk_lm/worlds.py)); test-label exposure and missing release license/transfer approval must remain disclosed ([M8 audit](../internal/m8/audit.md)). |
| Figures, tables and artifact traceability | **Needs work** | [Machine-generated table](../../artifacts/presubmission-20261025-evidence/rescore/tables.md) has row-level identities; no publication-quality figure set or independently portable artifact bundle is verified. |

The ready items support **an internal failure/reproducibility draft with explicit
gaps**. A paper centered on improved factual memory is blocked by zero known-fact
accuracy and universal M7 predictor fallback. The existing [internal draft](../internal/m8/paper-draft.md)
already uses a negative framing; its historical CI/base statements require
refreshing before reuse. Drafting is separate from external release or submission.

## Prioritized closure plan

Only **one new experiment** is recommended: the control-learning diagnostic in
action 2. No experiment is run in this audit; timing estimates are omitted because
the archived primary/replay times vary substantially across runs and machines
([M8 resource record](../internal/m8/audit.md)).

| Order | Gap resolved and smallest credible item | Required inputs/resources | Measurable completion criterion | New experiment? |
| --- | --- | --- | --- | --- |
| 1 | Freeze a new diagnostic protocol before seeing results: ordinary and recurrent controls on easy in-window known facts, then reserved delayed facts, with generated-answer scoring and a control-learning gate. Keep it distinct from immutable v1 reproduction configs. | Existing [world/oracle code](../../src/toruk_lm/worlds.py), [train/eval code](../../src/toruk_lm/controlled.py), [config versioning rule](../reproducibility.md); adviser-approved question and CPU cap. | New versioned protocol records train/validation identities, no test-label reuse, seeds, optimizer steps/timeout, model sizes, answer budget/decoding, metric, acceptance threshold, stopping rule and full-cost fields **before** execution. | No |
| 2 | Run that single bounded control-learning diagnostic and inspect training and reserved-validation generated answers. It asks whether controls can learn this benchmark at all; it does not retest the policy hypothesis. | Frozen protocol from action 1, local CPU/time budget, fresh paths, raw predictions and manifests. | Both controls' predeclared train/validation known-fact accuracy, coverage, loss, seeds, variability and cost are reported, with PASS/FAIL against the frozen gate; every failed run retained. If both fail, diagnose targets/objective/decoding before policy work. | **Yes — the only recommended next experiment** |
| 3 | Define the later method-comparison standard, without running it yet: equal total training and inference resource accounting, independent training seeds, and a fresh test/access policy. | Outcome of action 2, [M6 cost ledger](../../artifacts/m6-validation-001/summary.json), [test exposure](../../tests/test_worlds.py), adviser choice of resource budget. | Written acceptance rules for controls, predictor coverage, seed reporting, matched cost, new final-test freeze and no outcome-based retry; any later run requires separate approval/protocol. | No |
| 4 | Make the internal negative draft and handoff self-consistent. Replace stale base/CI descriptions, keep every negative row and limitation, and label rescoring versus inference replay versus retraining. | [Existing draft](../internal/m8/paper-draft.md), [this audit](presubmission-research-audit.md), [fresh table](../../artifacts/presubmission-20261025-evidence/rescore/tables.md), owner decisions for license/metadata before any external transfer. | Claim-to-row citation review passes; artifact availability and missing decision memo are explicit; no positive effect or remote-CI assertion lacks direct evidence. | No |

Preregistration for action 2 must also specify what to do with a failed control
gate: report it and stop policy interpretation. Training-set success is only an
overfit diagnostic; reserved-validation success is required before testing delayed
memory. A later positive method claim would need a *separate* frozen comparison
with multiple training seeds, matched total resources, nonfallback predictor
coverage, and a fresh confirmatory test. That later study is **not recommended for
execution now**.

## Internal paper outline, with gaps visible

- **Title options:** “A Reproducibility and Failure Study of Bounded Neural Memory
  Updates”; “When a Bounded Memory Pilot Does Not Learn Known Facts.”
- **Abstract structure:** question and bounded setting; implemented decoder,
  slots and paired effect estimator; frozen M6/M7 design; verified zero known-fact
  scores and fallback; reproduction scope; limits. Placeholders for any broader
  mechanism or external claim: **[evidence needed]**. No positive-result abstract.
- **Introduction:** why correction must preserve unrelated facts; separate broad
  motivation from the narrow final-write hypothesis ([question](m6-validation-protocol.md)).
- **Related work:** segment recurrence/compression; adaptive updates; paired
  downstream credit; clearly separate Toruk's candidate setting from demonstrated
  contribution ([seven-paper audit](../internal/m8/related-work.md)).
- **Method:** decoder/tokenizer, slot read/write, correction objective, paired
  labels, runtime support fallback and one-boundary scope ([source anchors](../architecture.md)).
- **Experimental setup:** frozen seeds/splits, synthetic worlds, baselines,
  generated-answer primary metric, unequal total budgets, test-label exposure
  ([M6](m6-validation-protocol.md), [M7](m7-protocol.md)).
- **Results and errors:** generated [fresh table](../../artifacts/presubmission-20261025-evidence/rescore/tables.md),
  zero learning, abstention, malformed outputs, fallback, historical costs and
  precise rescore/replay provenance. Mechanism-specific gains: **[evidence needed]**.
- **Limitations and conclusion:** single training seed, four reused M7 anchors,
  synthetic domain, no resource-matched advantage, local ignored checkpoints,
  incomplete reproduction and license/transfer decisions. Conclude with an
  inspectable negative pilot and the control-learning gate, not demonstrated
  useful memory ([M8 limits](../internal/m8/limitations.md)).

## Validation and CI distinction

Local checks for **this** audit: historical source/evidence seal matching;
independent rescore; both frozen-config validations; stored-output parity for
336 M6 and 48 selected M7 answers; local link/Markdown whitespace validation;
`git diff --check`. Exact results and commands are in the
[check records](../../artifacts/presubmission-20261025-evidence/check-summary.json).
The repository has no dedicated Markdown checker in
[local verification](../../scripts/verify.py), [package configuration](../../pyproject.toml)
or [workflow](../../.github/workflows/ci.yml). Since this task changes no code or
experiment configuration, the full software suite was not rerun. The retained
[M8 test log](../../artifacts/checks/m8-ci-final-tests.log) reports 34 tests at
the historical M8 source identity; it is prior local evidence, not a new check.
No live GitHub Actions run was inspected. The [older remote record](../../artifacts/m8-review/remote-ci.json)
lists a failure for commit `34d3037310050bd8e5dd2e52c2566c2fd9a21b78`;
it does not determine the status of current HEAD
`e944caeca2415de12e5694682507941e1f815b3a`.
