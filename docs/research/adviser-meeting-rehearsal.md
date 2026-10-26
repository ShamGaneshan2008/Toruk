# Toruk adviser meeting rehearsal

**Internal preparation for Sham; not a publication or completed-study claim.**
Prepared 2026-10-25, Asia/Calcutta. Speaking times are targets; rehearse aloud.

Repository `C:/Users/susee/VScode Project/Toruk`; branch `main`; full commit
`e944caeca2415de12e5694682507941e1f815b3a`. At entry, the adviser review and its
evidence/check records were untracked; they are preserved. This task adds only
meeting notes and evidence records. No code, experiment configuration or README
changes, new training, or new inference.

## Source and evidence check

Read the [latest adviser package](adviser-review.md),
[latest related-work audit](../internal/m8/related-work.md),
[M8 evidence audit](../internal/m8/audit.md), [public reproduction guide](../reproducibility.md)
and [internal reproduction handoff](../internal/m8/reproduction.md).
**Missing:** a decision memo and a separately named evidence-synthesis report.
The M8 audit is the closest synthesis, not a substitute decision memo. Historical
documents' old commit, dirty-tree and CI statements are dated observations.

For this rehearsal, `audit-evidence` freshly verified artifact identities and
rescored saved predictions: **PASS, 59 evaluations / 1,416 answers**. This does
not regenerate answers or retrain checkpoints. Use the
[fresh table](../../artifacts/rehearsal-20261025-evidence/tables.md),
[row-level provenance/configurations](../../artifacts/rehearsal-20261025-evidence/audit.json),
[command/source record](../../artifacts/checks/rehearsal-20261025-evidence.json)
and [log](../../artifacts/checks/rehearsal-20261025-evidence.log).
Source-file hashes, input-document inventory and validation outcomes are in the
[rehearsal verification record](../../artifacts/rehearsal-20261025-evidence/rehearsal-verification.json).

## A. Two-minute explanation

Imagine reading a long record about someone. It first says they live in one
city and work as a botanist. Later they move. You want a system to remember the
new city while keeping the occupation. That is an illustration of our goal,
not a result from Toruk.

Toruk investigates that problem when a language model has only a small amount
of internal memory. It is a research prototype around a small causal language
model. It adds fixed memory slots and a mechanism that proposes updates as the
model reads. It also implements a small predictor intended to judge whether one
proposed update will help later answers.

We evaluate it using artificial records where we can calculate the correct
answers independently. We ask about corrected facts, facts that should stay the
same, and things the record does not establish. We compare the memory versions
with an ordinary model and simpler update rules. We score answers the models
actually generate, separately from their training-style losses.

The available evidence is negative. Every stored comparison scores zero on the
known-fact measure. The ordinary model gets some overall answers right by saying
“unknown” every time. The learned update predictor also falls back on every
final decision in the follow-up studies. So we have an implemented, traceable
experiment, but no demonstrated memory benefit. I would like advice on the
smallest learning diagnostic to run before extending the memory experiments.

Speaker evidence: implementation and protocols in B; measured results in B and C.
Avoid describing the illustration as a tested natural-language task.

## B. Five-minute technical explanation

**Question and hypothesis.** The broad goal is selective retention, correction
and preservation under bounded state. The narrower hypothesis is that an
amortized predictor of a final memory write's downstream effect can improve
corrected/preserved generated answers over a simple observed-state heuristic
at acceptable total cost. This is an unvalidated hypothesis. The
[M6 protocol](../../artifacts/m6-validation-001/protocol.json) explicitly names
failure to improve jointly, or a correction/preservation tradeoff, as falsification.

**Model and memory.** The primary pilot uses a byte-level causal decoder with
context 64, width 32, four heads and two layers. Four continuous slots carry
state between segments. Each layer reads previous memory through cross-attention;
a hidden-state summary and old memory produce a gated next state after current
segment logits. Training propagates gradients through the whole bounded document.
The separate MLP uses old/proposed state and the current summary, with offline
paired retain/write answer-loss supervision. The tested policy intervention is
only the final-history write; earlier writes still occur. Out-of-support inputs
suppress that write before MLP execution. Sources:
[decoder](../../src/toruk_lm/model.py), [memory/session](../../src/toruk_lm/recurrent.py),
[training/evaluation](../../src/toruk_lm/controlled.py),
[paired labels](../../src/toruk_lm/effect_training.py),
[predictor](../../src/toruk_lm/effect_predictor.py).

**Design.** M6 is validation only: four synthetic worlds per split, data seed 17,
one training seed (23), twelve steps per main model, CPU float32 and one thread.
M7 reuses frozen checkpoints without fitting on four new semantic anchors from
data seeds 117/118. Three template cells and five load cells reuse those anchors.
The questions remain familiar. Sources: [M6 protocol](../../artifacts/m6-validation-001/protocol.json),
[world generator/oracle](../../src/toruk_lm/worlds.py),
[template protocol](../../artifacts/m7-templates-001/protocol.json),
[load protocol](../../artifacts/m7-load-001/protocol.json).

**Comparisons and metrics.** Controls include ordinary and width-40 ordinary
models, recurrent and revision models, heuristic/retain/reset/random policies,
objective ablations and 2/4/8 slots. World/step budgets match; parameters, FLOPs
and total costs do not. Primary accuracy averages four known-fact groups:
corrected, unchanged name, unrelated date and unrelated number. Overall exact
accuracy also includes unknown/ambiguous questions. Coverage and teacher-forced
cross-entropy are separate diagnostics. Answers use greedy decoding with a
16-token cap and first-line exact matching. See the [M6 protocol](../../artifacts/m6-validation-001/protocol.json),
[evaluation implementation](../../src/toruk_lm/controlled.py) and
[rescorer](../../src/toruk_lm/reproducibility.py).

**Results.** Fresh rescoring confirms fourteen M6 evaluations (336 answers) and
forty-five M7 evaluations (1,080 answers), all at zero known-fact macro accuracy.
Each evaluation has 24 answers, sixteen on known facts. Ordinary overall accuracy
is 33.3%, with zero attempted-answer coverage. M7 revision-predictor fallbacks
total 32/32 final decisions. Per-data-seed primary scores and descriptive SD are
zero; training-seed uncertainty cannot be estimated. These are repeated questions
and interventions on a few worlds, not independent answer-sized samples.
Sources: [fresh rows](../../artifacts/rehearsal-20261025-evidence/results.csv),
[provenance/fallback counts](../../artifacts/rehearsal-20261025-evidence/audit.json),
[per-seed analysis example](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json).

**Limits and interpretation.** Basic benchmark learning failed. We cannot identify
a memory-capacity boundary or component benefit at that floor. Synthetic data,
short training, one training seed and unmatched total resources prevent broader
claims. Rendering shifts also change length; load shifts change authority cues.
Unit tests expose deterministic test labels, although no final-test model score
is recorded. More training might help, but its role has not been isolated.
Sources: [M7 limitations](m7-results.md), [test exposure](../../tests/test_worlds.py),
[M8 audit](../internal/m8/audit.md). My proposed next action is the diagnostic
in E, not a claim that the hypothesis is already validated or conclusively rejected.

## C. Evidence-backed slide outline

This is an outline, not a generated deck. Each row gives a message to say aloud.

| Slide | Key message | Supporting source to open |
| --- | --- | --- |
| 1. Toruk: bounded memory under corrections | Can a model revise one fact while retaining others with fixed internal state? This is the research question. | [Adviser package](adviser-review.md), [memory contract](m3-memory-contract.md) |
| 2. Why retention and revision interact | A correction should change the targeted fact and preserve valid facts. Use the city/occupation example as an illustration; real-world effectiveness is **evidence needed**. | [Benchmark semantics](m2-controlled-worlds.md), [oracle](../../src/toruk_lm/worlds.py) |
| 3. Implemented approach | Causal decoder, recurrent slots, gated writer and separately supervised final-write predictor; a prototype, without demonstrated gain. | [Memory](../../src/toruk_lm/recurrent.py), [predictor](../../src/toruk_lm/effect_predictor.py), [labels](../../src/toruk_lm/effect_training.py) |
| 4. Experimental setup | M6: four validation worlds, 12 steps, seed 23. M7: frozen checkpoints, four new anchors, template/load interventions. | [M6 protocol](../../artifacts/m6-validation-001/protocol.json), [templates](../../artifacts/m7-templates-001/protocol.json), [load](../../artifacts/m7-load-001/protocol.json) |
| 5. Baselines and metrics | Known-fact accuracy is primary; abstention-inclusive accuracy and CE are different. Baselines have unequal total resources. | [Frozen comparisons](../../artifacts/m6-validation-001/protocol.json), [scoring](../../src/toruk_lm/worlds.py), [bound configurations](../../artifacts/rehearsal-20261025-evidence/audit.json) |
| 6. Main result | All 59 evaluations have 0% known-fact macro accuracy. The 1,416 answers are stored outputs freshly rescored, not new inference. | [Fresh table](../../artifacts/rehearsal-20261025-evidence/tables.md), [audit log](../../artifacts/checks/rehearsal-20261025-evidence.log) |
| 7. Failure cases | A revision answer is `gold` when truth is `green`; other answers are malformed. A stale-value match alone does not prove stale-memory retrieval. The predictor falls back throughout M7. | [Raw example](../../artifacts/m7-templates-001/control/revision-predictor/predictions.json), [failure analysis](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json), [fallback rows](../../artifacts/rehearsal-20261025-evidence/audit.json) |
| 8. Related work and overlap | Recurrence, selective updates and paired memory credit already exist. The internal-state estimator is a candidate experimental distinction. | [Latest audit](../internal/m8/related-work.md), primary sources in D2 |
| 9. Limits of the evidence | One training seed, synthetic/familiar tasks, shared worlds, unmatched compute and exposed test labels. Independent replication is **evidence needed**. | [M6 summary](../../artifacts/m6-validation-001/summary.json), [M7 limits](m7-results.md), [test source](../../tests/test_worlds.py), [reproduction handoff](../internal/m8/reproduction.md) |
| 10. Decision for the adviser | Establish whether controls can learn generated known facts before another policy study. New protocol, budget and diagnostic outcome are **evidence needed**. | [Learning floor](../../artifacts/rehearsal-20261025-evidence/tables.md), [existing falsification rule](../../artifacts/m6-validation-001/protocol.json), proposal in E |

## D. Adviser question practice

1. **What is the exact contribution?**
   “An implemented bounded-memory/update-prediction prototype and a traceable
   negative pilot. I have not demonstrated a new memory capability.” Point to
   [implementation](../../src/toruk_lm/recurrent.py) and [fresh results](../../artifacts/rehearsal-20261025-evidence/tables.md).
   Distinguish an engineering deliverable from an established research advance.

2. **How is this different from the closest related work?**
   “RMT already carries continuous memory between segments. MGPO and PAIR overlap
   directly with counterfactual memory credit. Our candidate distinction is a
   small estimator over internal neural state for a final write, rather than
   a textual-memory writer or compression-prompt optimizer; its value is unproven.”
   Use [RMT v2, section 3](https://arxiv.org/html/2207.06881v2),
   [MGPO v1, section 2](https://arxiv.org/html/2609.37930v1),
   [PAIR v1, sections 3–4](https://arxiv.org/html/2609.36526v1),
   [local seven-paper audit](../internal/m8/related-work.md) and
   [Toruk predictor](../../src/toruk_lm/effect_predictor.py).
   These version-specific sources were checked in the adviser review; this
   rehearsal adds no exhaustive literature or index search. Titans/Gated DeltaNet
   also cover adaptive updates; Compressive Transformer/ICAE cover compression
   in that audit. No head-to-head benchmark is recorded.

3. **Are the baselines fair?**
   “Only in limited respects: worlds, steps and probes are controlled. The
   width-40 ordinary sensitivity approximates parameter matching, but total
   compute, parameter counts and label/predictor costs are unequal.” Show
   [protocol](../../artifacts/m6-validation-001/protocol.json) and
   [cost/parameter table](m6-results.md). Ask which resource constraint should
   define the next comparison; do not call current comparisons compute-matched.

4. **Could data leakage explain the result?**
   “Gold answers are offline, and runtime projection excludes gold/oracle fields.
   M7 manifests mark evaluation-only data. However, unit tests inspect deterministic
   test labels, including registered cases; I cannot call the test wholly unseen.”
   Show [runtime projection/tests](../../tests/test_worlds.py),
   [M7 data manifest](../../artifacts/m7-templates-001/data/control/manifest.json)
   and [disclosure](../internal/m8/audit.md).
   No positive gain needs explaining, but zero scores do not prove absence of
   leakage. A future confirmatory test needs a new freeze and access policy.

5. **How robust are results across seeds?**
   “There is one training seed, 23. Two M7 data seeds both score zero, with zero
   descriptive SD. That does not estimate training robustness or supply a
   population confidence interval.” Show [protocol](../../artifacts/m7-templates-001/protocol.json)
   and [per-seed results](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json).
   Independent training-seed replication is missing.

6. **Does this generalize beyond synthetic tasks?**
   “There is no evidence of natural-text or second-domain transfer. The held-out
   worlds use familiar question types; rendering also changes length, and load
   changes authority cues. All known-fact results stay at zero.” Refer to
   [M7 design](m7-results.md). Successful transfer remains unverified.

7. **What does it cost?**
   “The historical M6 pilot recorded 100 LM steps including profiles, 101,256
   training positions, 32 label branches and 200 predictor steps. Its driver
   took 87.341 seconds and cumulative process peak was 352,514,048 bytes.” Show
   [raw cost summary](../../artifacts/m6-validation-001/summary.json).
   These are historical CPU observations, not current timings or per-model
   allocations. Failed pilots and test work add cost; complete CPU-hours and
   total-resource matching are missing. Small state does not imply less input read.

8. **What result would falsify your hypothesis?**
   “The registered pilot names no joint improvement over the heuristic, or a
   correction/preservation tradeoff. Current data show no gain. Because all
   known-fact baselines fail and the deployed predictor falls back, they do not
   isolate the predictor's merits.” Open [falsification rule](../../artifacts/m6-validation-001/protocol.json).
   Before another test, freeze a control-learning gate and measurable acceptance
   rule. Do not reinterpret the present null result as support.

9. **What cannot be claimed yet?**
   “Useful memory, reliable correction/preservation, calibrated deployed prediction,
   transfer, capacity onset, efficiency, originality and superiority are unsupported.
   Current-HEAD remote CI and independent external replication are unverified.”
   Show [scores](../../artifacts/rehearsal-20261025-evidence/tables.md) and
   [reproduction limits](../internal/m8/reproduction.md).
   No IEEE Xplore inclusion/exclusion is asserted; that index was not searched
   for this rehearsal. Old CI records do not establish current-commit status.

10. **What is the next smallest experiment that changes the conclusion?**
    “I propose a tiny control-learning diagnostic before another policy comparison,
    as described below. Can the ordinary/recurrent controls generate known facts
    at all under a predeclared bounded budget?” This follows from the
    [observed floor](../../artifacts/rehearsal-20261025-evidence/tables.md),
    not evidence that extra training will solve it. The new protocol and result
    are **evidence needed**; no such experiment was run for this preparation.

## E. Honest status and next steps

| Claim | Status and basis |
| --- | --- |
| Stored negative results and artifact/configuration traceability | **Supported:** fresh integrity/rescoring audit above; all known-fact scores zero. |
| Prototype execution and reproducibility | **Partially supported:** source and bound artifacts exist; retained smoke/replay records are described in the [handoff](../internal/m8/reproduction.md). This rehearsal only rescored outputs; full retraining and complete independent reproduction remain missing. |
| Useful memory, revision/preservation benefit, calibrated deployed decisions, transfer, capacity boundary, resource advantage | **Unsupported** by the scored results, universal M7 fallback and limited protocol. |
| Established technical originality or superiority | **Unsupported:** substantial prior-work overlap; no demonstrated benefit or direct paper-baseline comparison. |
| Independent replication, fully fresh dependency provisioning, current-HEAD GitHub Actions | **Unverified:** no new evidence of these in this task. |

**Most important limitation:** known-fact learning is at zero even in controls.
That blocks a useful comparison of memory-management choices; universal deployed
fallback further prevents attributing decisions to the learned estimator.

**One recommended next action (proposal, not an executed experiment):** freeze a
small control-learning diagnostic. Use ordinary and recurrent-write controls on
a tiny training-only set with a separately reserved validation set; start with
an easy in-window known-fact question to distinguish answer learning from long-delay
retention. Freeze scoring, seed, step/time caps and a success threshold before
running. Report training-set generated accuracy as an overfit diagnostic, never
as generalization. If both controls fail, inspect token targets, objective and
decoding before adding policy complexity. If they learn, proceed to a separately
frozen delayed-recall validation comparison. Budget/threshold selection and all
diagnostic outcomes are **evidence needed**. This would change the narrow conclusion
about basic learnability, not establish the effect predictor's contribution.
Do not alter the historical v1 reproduction configs to disguise a new study
([versioning rule](../reproducibility.md)).

**Materials Sham should open:**

- [Adviser review](adviser-review.md) and this rehearsal for the narrative.
- [Fresh result table](../../artifacts/rehearsal-20261025-evidence/tables.md) and
  [audit/provenance](../../artifacts/rehearsal-20261025-evidence/audit.json).
- [M6 protocol](../../artifacts/m6-validation-001/protocol.json) and
  [cost summary](../../artifacts/m6-validation-001/summary.json).
- [Raw failure example](../../artifacts/m7-templates-001/control/revision-predictor/predictions.json)
  with its [analysis](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json).
- [Latest related-work audit](../internal/m8/related-work.md) and
  [reproduction guide](../reproducibility.md). Internal M8 documents and checkpoints
  are local/ignored artifacts; a checkout alone does not include them.
