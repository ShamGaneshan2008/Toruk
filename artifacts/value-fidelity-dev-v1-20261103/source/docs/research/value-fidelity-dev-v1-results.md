# Value-fidelity development gate v1 — FAIL

The audit's recommended single milestone is complete as a bounded negative
experiment. Fixed training-time wording variation did **not** establish reliable
value fidelity in the existing routing-v2 architecture. Both preregistered
development gates fail, with lower accuracy than the unchanged old checkpoints.
No additional training, objective/architecture change, final qualification or
deployment milestone was started after this result.

[Protocol](value-fidelity-dev-v1-protocol.md),
[source/data/environment registration](../../artifacts/value-fidelity-dev-v1-20261103/registration.json),
[checkpoint seal](../../artifacts/value-fidelity-dev-v1-20261103/models.json),
[development worlds](../../artifacts/value-fidelity-dev-v1-20261103/development.json),
[raw generated answers](../../artifacts/value-fidelity-dev-v1-20261103/raw),
[full results/resources/commands](../../artifacts/value-fidelity-dev-v1-20261103/report.md),
[gates and uncertainty](../../artifacts/value-fidelity-dev-v1-20261103/summary.json), and
[individual regressions](../../artifacts/value-fidelity-dev-v1-20261103/examples.json)
retain the experiment. These are **development results**, not final-test evidence.

## Failure addressed and one coherent change

The completed current-state audit reproduced perfect top-1 routing but poor
value outputs: the earlier frozen study produced blue for revised facts and cat
for original facts, with only 14/120 known worlds correct at both seeds. That
motivated a training-only value-fidelity gate, not another model architecture or
a change to the pretrained conversational backbone.

The intervention adds fixed record/query word-order variation to original
training worlds. Model class, parameter allocation, routing, value/answer
computation, objectives, initial seeds, sampled-world sequence, optimizer and
800-step budgets are unchanged. A separate augmentation RNG preserves the world
sampling stream. Implementation details and order tables are in the private
Git-ignored architecture note. No scripted answer, runtime fact parser, extra
loss term or injected gold state was added.

Original training worlds are the only fitting data. Three fresh development
world seeds, 9101/9102/9103, generate 168 worlds in seven categories using two
previously untrained record/query order families. Those development families and
the training families exclude the previously scored final template. The finite
names/fields/value inventory is shared; this is not natural conversation or
unseen-entity generalization. Multi-fact worlds require both generated answers.

Source, protocol and development data were hashed before fitting. Both new
800-step checkpoints were sealed before development inference. Neither epoch
selection nor metric-guided retries occurred. Historical final artifacts were
integrity-checked only; no new final set was generated, and no final answers
were used for fitting or checkpoint selection.

## Matched before/after development results

Both versions below answer the **same fresh development worlds**. The older
14/120 final score is motivation, not the before score for this different set.
Values are training seeds 31 /47:

| Method | Exact worlds /168 | Known worlds /120 | Unsupported /48 |
|---|---:|---:|---:|
| Unchanged recent-context control | 46 /30 | 8 /6 | 10 /24 |
| Unchanged lexical control | 45 /36 | 7 /11 | 10 /23 |
| Old routing-v2 checkpoints | 113 /113 | 65 /65 | 0 /0 |
| Augmented training, same architecture | 98 /82 | 50 /34 | 0 /0 |
| Augmented checkpoint, state zeroed | 48 /48 | 0 /0 | 0 /0 |

| Gate criterion | Required at both seeds | Seed 31 | Seed 47 |
|---|---|---:|---:|
| Overall exact accuracy | >=80% | 58.3% FAIL | 48.8% FAIL |
| Known-world accuracy | >=80% | 41.7% FAIL | 28.3% FAIL |
| Correction | >=80% | 12/24 FAIL | 7/24 FAIL |
| Preservation | >=80% | 15/24 FAIL | 11/24 FAIL |
| Unsupported unknown/ambiguous answers | <=5% | 0/48 PASS | 0/48 PASS |
| Known accuracy decrease after state zeroing | >=50 percentage points | 41.7 pp FAIL | 28.3 pp FAIL |

Every known category regresses at both seeds. Old→augmented counts are:
correction 14→12 /14→7; preservation 18→15 /18→11; distant recall
16→10 /16→8; distraction 11→9 /11→6; multi-fact 6→4 /6→2.
Unknown and ambiguity each remain 24/24. No accuracy advantage is claimed.

Conditional paired-world bootstrap 95% intervals put the aggregate accuracy
difference versus old routing-v2 at **−20.8 to −6.25 percentage points**. The
interval preserves training-seed pairing and stratifies by development seed and
category; it conditions on two checkpoints, not a population of training seeds.

Real generated examples:

| Case | Query | Expected | Old | Augmented |
|---|---|---|---|---|
| Both seeds, `9101-correction-3` | `What Cyd's is color?` | cat | blue | cat |
| Seed 31, `9101-correction-2` | `is pet? Ada's What` | red | red | dog |
| Seed 47, same case | same | red | red | cat |
| Seed 31, `9101-correction-0` | `What Cyd's is pet?` | red | blue | green |
| Seed 47, same case | same | red | blue | cat |

The first is an individual gain; it does not outweigh regressions. Seed 31's
known-query outputs contain five value symbols; seed 47's contain only cat and
green. Increased output variety alone is not value fidelity. The independently
implemented offline raw-text oracle rescored all 1,920 answers /1,680 world
predictions with zero mismatches.

## Evidence, state use and cost

All 144 relevant known-query records are ingested by old and augmented memory
models. Only 41/144 contribute any local suffix bytes. Both memory versions route
all 192 queries and 1,854 record updates correctly at top 1, at each seed.
These diagnostics are offline and do not feed gold addresses to inference.
Ingestion and argmax routing do not prove faithful soft-state storage or value
decoding. State-zeroing removes all known matches, showing state influence, but
the retained-value success rate remains below the registered gate.

New fitting completed 1,600 optimizer steps /25,600 sampled world presentations
in **85.145 seconds** of optimizer loops. One Torch CPU thread, float32, no GPU,
paid jobs or downloads. Each parent training command finished in under 47 seconds,
within its 180-second/2-GiB cap. Sampled training peaks were
315,506,688 /315,625,472 bytes; high-water peaks 316,428,288 /316,440,576 bytes.
Training consumed 4,856,177 history token instances, 10,315,584 padded recurrent
positions and 7,710,096 additional routing embedding positions across both seeds.
These are work counters, not FLOPs or energy.

At development inference, old and augmented models both select 22,088 prompt
tokens over 192 answers per seed and scan the full history. Old recurrent work is
55,908 positions per seed; augmented work is 55,925 /55,911, plus the same
36,731 routing embedding positions. Observed summed latency is old
2,213 /2,354 ms and augmented 2,136 /2,134 ms. Sampled inference RSS is about
207 MiB. Quality regresses, and shared-host timing/RSS are observations rather
than controlled benchmarks; no efficiency or quality-preserving token claim.

Final answer CE in sampled training batches is 0.235 /0.250 nats. That is
consistent with incomplete fit of the harder rendering mixture, but it does not
identify a unique optimizer, value-encoder, soft-state or decoder cause. The
milestone does not extend the training budget to seek a favorable result.

## Identities, checks and reproduction

The model format remains `toruk-pooled-router-v2`; the new metadata identifies
training recipe `value-fidelity-dev-v1`. Checkpoints are separate local ignored
files at `artifacts/value-fidelity-dev-v1-20261103/train/augmented-{31,47}.pt`.

```text
Code/config registration SHA256: 795ceecaf550e3e0bb6128aa96a23e84c759a9521e710bf60d28d70b7af02098
Development dataset SHA256: 278411d24527a65926df0d4c78bd62a9f979b6da09508e07295393adc45caff4
Augmented seed31 SHA256: 9e23717095fef05073cdacd55ce61b65ffbe8efea5406b46032bbd4ff6944a97
Augmented seed47 SHA256: 6ece706f9c2fa0bb3cbec0037f0abe073fc1e8b1146d2e2af120fe0516acf555
Tokenizer: ebf7d205ce6fc5e51a3109713ea3a0c29f01f7d309a8f2f5dca7a9863ea970d7
```

Registration binds the exact source, training data and original baseline/model
checkpoints. Model seal and every evaluation bind actual development data and
consumed model files. The copied-run input-binding fix remains enforced.

Python tests: **174 passed**, including six new rendering/role/gate tests.
Type checks, focused lint/format, CLI checks, Node syntax/tests, real local chat,
fresh package build and final diff checks are recorded in the command ledger.
Repository-wide Ruff/format retain failures in the same three frozen selector
scripts; their bytes remain unchanged. Ordinary Node tests have 13 passes and
one optional live-handler skip, covered by a separate enabled live suite. Page
handlers use a DOM harness with real proxy/inference; interactive browsing was
not tested. The independent scorer's exit 0 verifies scoring, not the model gate.

The local chat regression still uses pinned pretrained Qwen2.5-0.5B-Instruct and
the old trained JSON chat selector. It does not load either new research checkpoint.
Both modes answer LIME42 and report their actual identities; outage handling
passes. Those checks do not convert a failed synthetic development gate into a
conversational or public-release success.

Base HEAD and origin/main remain
`f7862c0789ed772c1068832962eba176a4fbcd1b` with no divergence.
[Actions run 41653980796](https://github.com/ShamGaneshan2008/Toruk/actions/runs/41653980796)
has web success and Python failure at Ruff; later Python checks were skipped.
New local work is **NOT_RUN remotely**. No commit, push or deployment was made.
Pre-existing uncommitted audit work, private notes, old weights and frozen raw
results are retained. No private design file or model weight is added to public
README content or package builds.

Exact Windows PowerShell reproduction, with the recorded environment and original
locally retained weights, using a fresh directory:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
$run = 'artifacts/value-fidelity-dev-v1-replay'
& $py scripts/value_fidelity_dev.py register --run $run
if ($LASTEXITCODE -ne 0) { throw 'Registration failed' }
& $py scripts/value_fidelity_dev.py run --run $run
if ($LASTEXITCODE -ne 0) { throw 'Experiment execution failed' }
& $py scripts/audit_value_fidelity_dev.py --run $run
& $py -m pytest -q tests/test_value_fidelity_dev.py -p no:cacheprovider
```

Execution success is distinct from `summary.json`'s milestone verdict. The driver
retains negative results and refuses overwrites or registered input drift. Its
saved subprocess timeouts/RSS caps enforce the bounded plan. Passing a future
development gate would only justify a separately registered untouched final
study; that study is not started here. The remaining blocker is reliable value
learning across wording variations within the bounded existing architecture.
