# Path A routing v2: routing improves, useful factual memory still fails

**Path A was selected.** Qualification v1 failed the useful-memory and
quality-preserving efficiency gates. Its conditional aggregate-accuracy result
did not qualify Path B. This milestone changes one Toruk-owned routing mechanism,
retains old weights and baselines, and tests new worlds and word-order templates.
It does not change the pretrained chatbot backbone or prepare a deployment.

[Preregistered protocol](routing-v2-protocol.md),
[registration/configuration/environment](../../artifacts/routing-v2-20261103/registration.json),
[pre-inference freeze](../../artifacts/routing-v2-20261103/freeze.json),
[raw answers](../../artifacts/routing-v2-20261103/raw),
[full tables and exact commands](../../artifacts/routing-v2-20261103/report.md),
[summary/uncertainty](../../artifacts/routing-v2-20261103/summary.json),
[individual gains/regressions](../../artifacts/routing-v2-20261103/examples.json), and
[saved-output collapse diagnostic](../../artifacts/routing-v2-20261103/output-collapse.json)
retain the mixed and negative results. Previous integrated/qualification artifacts
are unchanged. No result was overwritten or final set edited after inference.

## Diagnosis and bounded intervention

Qualification seed 31 recalled no known worlds, while seed 47 recalled 31/120
but produced unsupported answers on 45/48 unknown/ambiguous cases. Earlier
unseen-wording routing diagnostics were poor. We therefore registered one change
to make the learned address representation insensitive to word order, leaving
value/answer computation, data, objectives, initial seed, parameter allocation,
optimizer, sampling and training budget fixed. The two complete models are newly
trained; their decoder weights differ as a consequence of end-to-end training.
It would be incorrect to call these identical decoder weights. Implementation
details remain in the Git-ignored private architecture note.

The expected effect and possible regressions were written before implementation.
Exactly two 800-step runs completed. Original development scores were 59/96 and
68/96, below useful quality. These failures were retained without changing the
budget, objective, epochs, data or parameters. New final data/checkpoint/source
identities were then frozen before final answer generation.

## Held-out results and regressions

The new set has 168 distinct worlds: 3 evaluation seeds, 7 categories, 8 worlds
per category/seed. Each is repeated at +0/+8/+32 irrelevant writes. Multi-fact
worlds require both independently generated answers to match. Twelve evaluation
cells completed, retaining 6,048 world predictions and 6,912 generated answers.
An independent raw-text oracle and token-output rescorer found **zero scoring
mismatches**. Labels never enter runtime inference.

Results below are ordinary-load world counts, with training seeds 31 / 47:

| Method | Correct /168 | Known /120 | Unsupported /48 |
|---|---:|---:|---:|
| Unchanged recent context | 30 / 25 | 7 / 8 | 25 / 31 |
| Unchanged deterministic lexical selector | 35 / 25 | 9 / 8 | 22 / 31 |
| Unchanged learned external selector diagnostic | 35 / 27 | 9 / 8 | 22 / 29 |
| Old integrated v1 | 23 / 39 | 6 / 21 | 31 / 30 |
| New routing v2 | 62 / 62 | 14 / 14 | 0 / 0 |
| New v2 with state zeroed | 48 / 48 | 0 / 0 | 0 / 0 |

| Target diagnostic | Old seed 31 | New seed 31 | Old seed 47 | New seed 47 |
|---|---:|---:|---:|---:|
| Correct query routes /192 | 97 | 192 | 86 | 192 |
| Correct record routes /1,584 | 667 | 1,584 | 1,266 | 1,584 |

The narrow routing target **passes** at both seeds. The targeted factual-transfer
criterion **fails**: known accuracy increases by eight worlds for seed 31 but
decreases by seven for seed 47. At seed 47, correction falls 8→4/24,
preservation 5→3/24, and distraction 6→3/24. Multi-fact accuracy remains 0/24
for both new seeds. All methods fail the preregistered useful-quality gate.
The full report lists every category and stress-load regression.

Posthoc saved-output inspection exposes a narrower failure: at both seeds,
all 72 known queries about revised facts answer **blue**, and all 72 about
original facts answer **cat**, despite varied expected values. Thus 14/120 known
world matches do not establish reliable value recall. Top-1 routing correctness
does not establish faithful soft-state storage/readout or value decoding. The
remaining failure cannot be uniquely assigned to value encoding, soft-state
contamination, query conditioning or the answer decoder from these data alone.
No further change was selected or trained on this final set.

Examples are actual generated strings, not substituted answers:

| Seed/world | Query | Expected | Old | New |
|---|---|---|---|---|
| 31 / `8101-correction-0` | `color? Ben's is What` | blue | ? | blue |
| 31 / `8101-preservation-3` | `pet? Cyd's is What` | green | green | cat |
| 47 / `8101-correction-4` | `color? Cyd's is What` | cat | cat | blue |
| Both / `8101-correction-2` | `pet? Cyd's is What` | dog | green / owl | blue |

The new overall accuracy is 36.9%, with a conditional paired-world-bootstrap
95% interval of 33.3–40.5%. Its difference versus old integrated v1 is
+14.0 to +22.9 percentage points. These aggregate gains are dominated by safe
abstention and coexist with poor recall and regressions. Intervals condition on
the two trained checkpoints; they do not estimate training-population uncertainty.
Stress loads reuse worlds and are not additional independent samples.

## Separating errors and measurement limits

**Selectors:** recent/lexical/learned controls use the same historical ordinary
decoder weights at each seed. The external learned selector is a distribution-
shift diagnostic, not a reproduction of its pretrained-Llama chat comparison.
Selected IDs and suffix-contributing IDs are retained per answer; reduced prompt
length may remove evidence. Full-history integrated ingestion is distinct from
semantic state retention. The full report gives evidence exposure and ingestion
denominators; partial suffix bytes do not prove complete evidence understanding.

**Model:** the integrated methods receive all raw history. Routing improves but
generated values collapse, so selector omission alone cannot explain the new
failure. State-zeroed v2 removes even the limited known matches; state influence
is verified, while useful learned factual recall remains unqualified.

**Scorer:** primary scoring requires exact generated UTF-8 equality and `?` for
unknown/ambiguous evidence. A separate raw-text parser reconstructs authoritative
facts from the final records and checks all saved strings/IDs, correctness and
unsupported flags; it is offline and never provides an answer to the model.

**Data design:** held-out word orders reuse the training character vocabulary
and finite names/values. This particularly tests the registered routing invariance;
it is not evidence of semantic or unseen-entity generalization. Correction and
distraction use overlapping task structures. Multi-fact is paired independent
queries, not open-ended compositional dialogue. Attribute values are arbitrary
symbols (for example, pet can equal blue). The separate local-chat correction
probe asks “Which day is it now?”, which is ambiguous between meeting day and
current weekday; its answer cannot by itself diagnose meeting-memory failure.
These limitations are disclosed without changing frozen data or historical reports.

## Total work, compute, identities

New fitting used 1,600 optimizer steps, 25,600 sampled case presentations and
91.075 seconds in optimizer loops, one Torch CPU thread. Sampled training peaks
were 315,412,480 / 314,699,776 bytes; process high-water peaks were
316,342,272 / 315,637,760 bytes. Parent wall times and diagnostic costs remain
in the command records. No paid compute, downloads or GPU training occurred.

At ordinary load, new v2 selects the same 22,100 prompt tokens as recent context,
summed over 192 answers. It forwards 51,261 recurrent positions, versus
22,784 / 22,780 for recent, and additionally processes 32,085 routing embedding
positions. Its observed full-history answer latency totals 2,026 / 2,012 ms,
versus recent 661 / 693 ms. All methods read/scan the full supplied history.
The report includes every method's tokens, scans, workload, latency and sampled
RSS at every load. Fixed state remains 1,152 bytes; this is not process memory.

Evaluation cells ran serially before engineering verification. The host is
shared and no OS isolation, FLOP/energy accounting or deployment price study was
performed. RSS includes framework/loading/offline diagnostics and can miss peaks
between 5 ms samples. Extra routing work is counted separately rather than
pretended free or equated to recurrent compute.

Exact identities:

```text
Base commit: 9163780930ea91c09d596e3e6284dc9e96f67109 (local source is uncommitted)
Code/config registration SHA256: 1b08d16c8bbae94215e48cbba9949fb6778f1c526ef20c0bff90f5447c8abd0c
Final freeze SHA256: 5447ad46027dcefc3621d160d9dbb0f930847f875e7a05328919f58fedbc265d
Final data SHA256: a468cadb45cb6ec9d915cc46ae74419081c3035b5585fed00775d8cc40ab7884
Training manifest SHA256: b6264bb32d8b66224de1f1f2d33985f753799a132cf6d44ba1a01c71a1884566
Byte tokenizer: ebf7d205ce6fc5e51a3109713ea3a0c29f01f7d309a8f2f5dca7a9863ea970d7
New seed31 checkpoint: 062580f974a108c9888c08a23342221e4f7212784ecf2f7a3de71f7212b72036
New seed47 checkpoint: 12b5eaa4897bf5a1727dfc3464f92abd4f9ad9298a06e3a9e42d45095dc3e493
```

The registration binds every source file, training split, old checkpoint, selector
and protocol identity. New format `toruk-pooled-router-v2` is distinct from
`toruk-integrated-lm-v1`. Model/optimizer weights remain locally Git-ignored.
Chat remains pinned Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, weights SHA256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`;
its pretrained language ability is separate from the JSON selector and integrated
research decoder. No chat wiring or pretrained weights were changed.

## Checks and eight separate gates

Python: **160 tests pass**, including seven focused routing tests. Windows and
Linux mypy pass on 28 source files. CLI help/diagnose, dependency integrity,
ordinary reproduction/validation/summary and controlled resume smoke pass.
Focused lint/format pass. Repository-wide Ruff exits **1** with 49 existing
findings in three frozen selector scripts; full format exits **1** for those
same files. They remain unchanged. Fresh-directory wheel/sdist build and
`git diff --check` are recorded in the final package.

Node syntax and ordinary tests pass (13 passes; one optional live-handler skip).
The separately enabled live page-handler suite passes both tests with no skips,
using real Qwen inference. The HTTP smoke returns LIME42, rejects unconfigured
TORUK mode and reports 503 after backend shutdown. This tests a DOM harness and
actual proxy/model, not an interactive browser or broad chat quality. All exact
commands and exit codes are in the report and commands.json.

| Gate | Verdict | Reason |
|---|---|---|
| Useful conversational answers | INCONCLUSIVE | Separate Qwen smoke provides examples, not a qualified conversation study; integrated decoder is synthetic and not in chat. |
| Toruk-owned useful learned memory | FAIL | Real trained state/routing exists, but only 14/120 known worlds correct and value outputs collapse. |
| Fewer selected tokens at preserved quality | FAIL | New integrated prompts are unchanged; minimum quality fails. |
| Lower total resource cost | FAIL | Additional full-history updates/routing work and higher observed latency; no qualified cost advantage. |
| Generalization | FAIL for useful factual transfer | Perfect routes on a narrow word-order family coexist with poor decoding and a seed-47 known-fact regression. |
| Research-paper readiness | FAIL | Useful-quality prerequisites remain unmet; no novelty or venue claim. |
| Protected preview readiness | FAIL | Path A has no qualified integrated chat candidate, release gate or prepared inference-host budget. |
| Public chatbot readiness | FAIL | No qualified public release candidate or deployment. |

A bounded future experiment could retain v2 routing and test whether the value
path learns to preserve arbitrary values under training-only word-order variation,
with a fresh development gate and a new unopened final grammar. It is proposed
only; this milestone does not apply a second mechanism change or tune on this set.

## Windows PowerShell reproduction and Git

From this checkout with its recorded environment and original ignored weights:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
$run = 'artifacts/routing-v2-replay'
& $py scripts/study_routing_v2.py register --run $run
foreach ($seed in @(31,47)) {
  & $py scripts/study_routing_v2.py train --run $run --seed $seed
  if ($LASTEXITCODE -ne 0) { throw 'Training failed' }
  & $py scripts/study_routing_v2.py development --run $run --seed $seed
  if ($LASTEXITCODE -ne 0) { throw 'Development check failed' }
}
& $py scripts/study_routing_v2.py freeze --run $run
& $py scripts/study_routing_v2.py run --run $run
& $py scripts/study_routing_v2.py analyze --run $run
& $py scripts/audit_routing_v2.py --run $run
```

Use fresh output paths. Final inference rejects source/data/checkpoint drift and
overwrites. Archived source allows isolated reconstruction; cross-platform or
cross-version byte-exact training is not promised. Saved checkpoint hashes include
timing/RSS metadata and may differ even with equal learned parameters. Transferring
Git alone omits ignored weights, which must be retained with their identities.

Remote main, cached origin/main and local HEAD are the same base commit (0/0
ahead/behind). [Actions run 41472041835](https://github.com/ShamGaneshan2008/Toruk/actions/runs/41472041835)
remains completed/failure: web syntax and Ruff failed, downstream tests/types/build
were skipped. [Fresh exact-SHA remote evidence](../../artifacts/routing-v2-20261103/remote-ci.json)
is retained. Current local work is **NOT_RUN remotely**. Existing dirty files,
history and negatives are preserved. No commit, pull, push, force-push, deployment
or publication occurred. Initial/final Git status is saved in the package.
