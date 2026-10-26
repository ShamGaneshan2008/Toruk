# Toruk adviser review

Prepared 2026-10-25 (Asia/Calcutta). Discussion status: **ready for research-direction
review; evidence does not establish useful memory or revision**.

Repository: `C:/Users/susee/VScode Project/Toruk`, branch `main`, commit
`e944caeca2415de12e5694682507941e1f815b3a`. The working tree was clean before this
review. This package adds documentation and evidence checks only.

## 1. Research question and motivation

Can a language model with fixed internal memory remember relevant facts after
they leave its local context, replace a fact when corrected, and preserve other
facts? More narrowly, can a small predictor decide whether a proposed memory
write will help later answers better than a simple observed-state heuristic?
The problem is selective retention under finite storage: later information can
supersede one fact without invalidating everything else. These are objectives,
not demonstrated capabilities ([research design](m4-effect-predictor.md),
[memory contract](m3-memory-contract.md)).

## 2. Proposed contribution

The implemented approach combines bounded continuous memory, correction and
preservation objectives, and an estimator trained on paired retain/write
outcomes. The defensible current contribution is a traceable prototype and
failure analysis. Whether amortized prediction over internal neural state adds
value remains an experimental hypothesis; recurrence, gating, compression and
counterfactual credit are established ingredients (sources in section 5).

## 3. Method and protocol

| Component | Implemented method and exact source |
| --- | --- |
| Model | Byte-level causal decoder: context 64, width 32, four heads, two layers in the primary pilot; [model](../../src/toruk_lm/model.py), [tokenizer](../../src/toruk_lm/tokenizer.py), [frozen M6 settings](../../artifacts/m6-validation-001/protocol.json). |
| Memory | Four continuous slots by default, cross-attention reads, gated writes after segment logits; full bounded-document backpropagation. [Recurrent model/session](../../src/toruk_lm/recurrent.py), [training](../../src/toruk_lm/controlled.py). |
| Effect estimator | Small MLP uses previous/proposed state and current summary; offline paired branches supply downstream answer-NLL differences. Runtime support checks can suppress a write before running the MLP. Only the final-history decision is varied in these comparisons. [Labels/training](../../src/toruk_lm/effect_training.py), [runtime](../../src/toruk_lm/effect_predictor.py), [comparison driver](../../src/toruk_lm/comparisons.py). |
| Data | Locally generated synthetic worlds with authoritative updates, distractors, oracle answers, and unknown/ambiguous probes. M6 has four worlds per split, generator seed 17. [Generator/oracle/scoring](../../src/toruk_lm/worlds.py), [data manifest](../../artifacts/m6-validation-001/data/manifest.json). |
| Baselines | Ordinary decoder, width-40 ordinary sensitivity, recurrent writer, revision model, heuristic/retain/reset/random policies, objective ablations and 2/4/8 slots. Equal world/step budgets, **unequal parameters and total compute**. [Protocol](../../artifacts/m6-validation-001/protocol.json), [bound model configurations](../../artifacts/review-20261025-evidence/audit.json). |
| Metrics | Primary: unweighted mean of corrected, unchanged-name, unrelated-date and unrelated-number exact accuracies. Overall exact accuracy includes uncertain probes; coverage and teacher-forced CE are separate. Greedy generation, at most 16 tokens, first-line answers; gold is offline. [Evaluation](../../src/toruk_lm/controlled.py), [independent rescoring](../../src/toruk_lm/reproducibility.py). |
| Protocol | M6: 12 steps/model, training seed 23, CPU float32, one thread. M7: frozen checkpoints, no fitting, four reused semantic anchors from data seeds 117/118; three template cells and five load cells. [M6 protocol](m6-validation-protocol.md), [M7 template protocol](../../artifacts/m7-templates-001/protocol.json), [load protocol](../../artifacts/m7-load-001/protocol.json). |

## 4. Measured results

Fresh integrity checking and independent rescoring passed for **281 manifest
entries, 59 evaluations and 1,416 answers**. This review ran no new inference or
training. [Command/result log](../../artifacts/checks/review-20261025-evidence.log),
[source/command record](../../artifacts/checks/review-20261025-evidence.json).

| Study | Evaluations / generated answers | Known-fact macro accuracy | Evidence |
| --- | ---: | --- | --- |
| M6 validation | 14 / 336 | 0% for every configuration | [Regenerated rows with prediction/configuration identities](../../artifacts/review-20261025-evidence/results.csv), [raw ordinary answers](../../artifacts/m6-validation-001/ordinary-write/predictions.json) |
| M7 templates | 15 / 360 | 0% in every cell/method | [Regenerated table](../../artifacts/review-20261025-evidence/tables.md), [per-seed example](../../artifacts/m7-templates-001/control/revision-predictor/analysis.json) |
| M7 load | 30 / 720 | 0% in every cell/method | [Regenerated table](../../artifacts/review-20261025-evidence/tables.md), [per-seed example](../../artifacts/m7-load-001/control/revision-predictor/analysis.json) |

Each evaluation contains 24 answers, including 16 known-fact answers. Ordinary
overall accuracy is 33.3%, entirely from answering `?`, with zero attempted-answer
coverage. M7 revision-predictor decisions fall back on all 32 final boundaries;
the learned MLP therefore supplies no deployed decision evidence. M7 per-data-seed
primary means and descriptive sample SD are zero. There is only **one training
seed**, so training-seed variability is unavailable. The four reused M7 worlds
are not 1,080 independent observations.
All counts and scores are traceable through the [fresh audit rows](../../artifacts/review-20261025-evidence/audit.json)
and [M7 analyses](m7-results.md#actual-quality-and-uncertainty).

Interpretation: the benchmark-learning floor prevents identifying memory-policy,
objective or capacity benefits. It does not establish that bounded memory cannot
work. More training as a remedy is a hypothesis, not a measured diagnosis.

## 5. Closest audited work

The [latest local audit](../internal/m8/related-work.md) covers seven papers;
the [earlier public note](related-work.md) covers five. The following primary
sources were reopened on 2026-10-25; these are version-specific comparisons,
not an exhaustive search or a claim about the latest versions.

| Prior work | Verified overlap and Toruk distinction to test |
| --- | --- |
| [RMT v2, section 3](https://arxiv.org/html/2207.06881v2) | Continuous memory passed between segments and trained through recurrence. Toruk uses separate cross-attention and a gated slot writer rather than read/write tokens. |
| [Titans v1, section 3](https://arxiv.org/html/2501.00663v1); [Gated Delta Networks v3, section 3](https://arxiv.org/html/2412.06464v3) | Adaptive retention/forgetting and selective updates. Toruk's slot interpolation is neither Titans' fast-weight optimizer nor the gated delta-rule matrix update. |
| [MGPO v1, section 2](https://arxiv.org/html/2609.37930v1); [PAIR v1, sections 3–4](https://arxiv.org/html/2609.36526v1) | Direct overlap in downstream counterfactual memory credit and paired continuations. Toruk tests an amortized estimator for an internal-state write rather than optimizing a textual writer or compression prompt. |
| [Compressive Transformer](https://arxiv.org/abs/1911.05507); [ICAE v4](https://arxiv.org/abs/2307.06945v4) | Compressed older memories and learned continuous slots precede Toruk. The operation-effect estimator is the candidate distinction, with no demonstrated benefit. |

Toruk implementation references are in section 3. No head-to-head experiment with
these architectures is recorded in the [local audit](../internal/m8/related-work.md).
No IEEE Xplore or other index-absence claim is made; this review did not search
those indexes.

## 6. Limitations and missing evidence

- **Scale/generalization:** tiny synthetic records, short training, familiar
  questions, correlated worlds; template changes also change length and load
  changes alter authority cues. Natural-text/domain transfer is unmeasured
  ([M7 design/limits](m7-results.md#frozen-held-out-design)).
- **Fairness/compute:** approximate parameter sensitivity does not equal total
  resource matching. Label generation, predictor fitting, failures and test work
  add costs; complete training-token/CPU-hour accounting is missing. No efficiency
  advantage follows ([M6 costs](../../artifacts/m6-validation-001/summary.json),
  [M7 measured costs](m7-results.md#measured-costs)).
- **Test/reproduction:** no retained final-test model score; unit tests inspect
  deterministic test labels, so the split is not wholly unseen
  ([test source](../../tests/test_worlds.py)). Full primary retraining and complete
  M7 regeneration were not reproduced in M8; independent replication and fresh
  dependency provisioning remain unverified ([handoff](../internal/m8/reproduction.md)).
- **Document gaps:** no pre-existing adviser briefing, decision memo, or separately
  named evidence-synthesis report was found. The closest synthesis is the
  [M8 audit](../internal/m8/audit.md), alongside its [paper draft](../internal/m8/paper-draft.md).
  Their old branch/dirty-tree/CI descriptions are historical, not current status.
  [Review inventory and source comparison](../../artifacts/review-20261025-evidence/review-verification.json).
  Internal M8 documents and checkpoints exist locally but are ignored by Git;
  a checkout alone does not provide them ([ignore rules](../../.gitignore)).

## 7. Bounded reproduction and review checks

From the repository root, after the [documented environment setup](../reproducibility.md),
use a fresh label and output directory:

```powershell
.\.venv\Scripts\python.exe scripts/check.py adviser-smoke-001 -- .\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output artifacts/adviser-smoke-001
```

The wrapper caps the process at 120 seconds; the [versioned smoke config](../../configs/reproduce-smoke-v1.json)
sets a 110-second between-stage budget. This checks execution/resume, not the
research claim or historical primary weights. This review did not run the smoke
or retrain. For no-inference rescoring and archived replay, follow the
[public guide](../reproducibility.md) and [internal handoff](../internal/m8/reproduction.md).

Local review checks: evidence audit **PASS**; all 34 M8 sealed source files match;
current package fingerprint matches the prior final audit. No dedicated Markdown
check is configured in [verification script](../../scripts/verify.py) or
[workflow](../../.github/workflows/ci.yml). Link/whitespace results are recorded in
the [review check record](../../artifacts/review-20261025-evidence/document-checks.json).
No code or experiment configuration changed, so the full code-verification suite
was not rerun. **GitHub Actions for current HEAD: unverified**, not inspected live.
The [retained remote record](../../artifacts/m8-review/remote-ci.json) concerns older
commits and does not establish this HEAD's status.

## 8. Current claim decisions

| Claim | Decision |
| --- | --- |
| Stored negative results are traceable and rescore consistently | **Supported** by the fresh audit in section 4. |
| Prototype execution/reproduction | **Partially supported**: stored evidence and historical checks exist; complete retraining and independent replication are missing (sections 6–7). |
| Useful recall, correction/preservation gains, calibrated learned decisions, transfer, capacity or efficiency advantage | **Unsupported** by current results and protocol (sections 3–6). |
| Technical originality or superiority over audited papers | **Unsupported**; overlap is clear and the candidate distinction remains unvalidated (section 5). |
| Current remote CI or external replication success | **Unverified** (sections 6–7). |

## 9. Adviser questions

1. Should the next gate be reliable known-fact learning on the ordinary/recurrent
   controls before any further policy or capacity study?
2. Is amortized final-write effect prediction a useful distinction from MGPO/PAIR,
   or should the research question change?
3. Which baseline and total-resource matching rule would make a positive result
   scientifically persuasive?
4. Which independent training seeds, learning threshold and fresh held-out test
   should be frozen before further comparisons?
5. Should the near-term deliverable be a bounded failure-analysis report or a
   redesigned learning experiment?
