# Integrated memory v1: implemented mechanism, failed transfer

This is a separate, small Toruk-trained conditional byte LM with a bounded neural
state read directly by its answer decoder. It is not a fine-tuned Qwen/Llama,
the previous external selector, or a completed conversational Toruk model.
No paid compute, model download, deployment, commit or push was performed.

[Protocol](integrated-memory-v1-protocol.md),
[sealed identities](../../artifacts/integrated-memory-v1-20261102/freeze.json),
[configuration/environment](../../artifacts/integrated-memory-v1-20261102/run-config.json),
[raw final predictions](../../artifacts/integrated-memory-v1-20261102/final), and
[post-evaluation analysis](../../artifacts/integrated-memory-v1-20261102/analysis.json)
retain the positive implementation checks and negative research result.

| Question | Verdict |
| --- | --- |
| A. Implemented and reproducible? | Yes on this CPU runtime: learned state affects generated answers, reload/stream continuation and optimizer-boundary resume are tested. Full retraining parity is recorded separately. |
| B. Better factual answers? | Known-fact matches increase from 3/64 to 9/64 and 4/64 to 14/64, but remain poor. Overall exact accuracy changes from 22/96 to 23/96 and 34/96 to 25/96. No robust useful-memory claim. |
| C. Corrections without damaging unrelated facts? | Not established. Integrated preservation is 0/16 and 1/16; unsupported answers increase in both seeds. |
| D. Lower total cost at preserved quality? | No. More forwarded token positions, higher full-history latency and no measured peak-memory reduction. |
| E. Paper-level evidence? | No. Finite trained symbols, two training seeds, one final data seed, severe template-transfer failure and weak answer quality. |
| F. Is chat using this model? | No. The chat server still uses a separate pretrained Qwen/Ollama backbone, optionally with an external selector. This prototype has a separate research CLI and checkpoint format. |

## Foundation gate and design decision

The original M6 weights are absent; they were not replaced or relabeled. The
ordinary historical smoke checkpoints are byte continuation models, not instruct
chat models. Qwen and Ollama Llama supply the existing chatbot's pretrained
language ability. The chat ranker is a separately Toruk-trained logistic selector.

The v2 selector SHA-256 is
`abd9d2d1c20edb3ad5cf3282f8a26fca49fb44d508d4ba2ada5ebc9c666b7548`.
It uses weighted evidence-turn BCE on eight lexical/position features, scans all
supplied history, and selects at most two old user turns plus three recent turns
before prompt fitting. Its saved train/dev evidence F1 is 0.571/0.857. Historical
final evidence retention was 24/24 known cases, yet answers were 22/28 versus
26/28 for matched recent context. It is not qualified as an improved memory.

Fresh [retraining and audit](../../artifacts/integrated-memory-v1-20261102/foundation/audit.json)
reproduced threshold and all 252 selection decisions. Parameters differ by at
most 7.153e-7 on the current Torch CPU runtime; byte-exact old-checkpoint training
is not claimed. Fresh timing/peak-memory metadata also changes checkpoint bytes.
The old SHA remains unchanged.

The measured `final-conflict-00` failure retained obsolete Nashik and replacement
Ranchi, then answered Nashik; recent context answered Ranchi. A development
diagnostic also co-exposes superseded and valid evidence. Evidence inclusion
therefore does not ensure correction handling. The new experiment tests learned
overwrite and direct state-to-decoder read instead of adding a larger selector.

Runtime receives raw UTF-8 records and questions only. There is no symbolic fact
parser, gold-answer input, scripted answer lookup, or reference-answer decoding.
Write/read address labels are **additional offline supervision** for six fixed
entity/attribute combinations. Dense state and the autoregressive byte decoder
are learned. This strong finite-slot inductive bias is not open-ended semantic
memory. Detailed implementation notes are in the local private architecture file
`docs/internal/integrated-memory-v1.md`.

## Pilot, matching and limits

The model has 70,208 allocated parameters, width 48, six 48-float slots (1,152
state tensor bytes), and a 96-token local suffix. The suffix is stored as Python
integer tokens, so actual host storage exceeds 96 bytes. Record/question limits
are 64 byte tokens, generation is greedy with 12 tokens including possible EOS,
and study histories contain at most 16 records. Streaming tests consume 100
records without growing state or suffix. Questions do not mutate history.

Both methods start from the same seed, allocated architecture, training examples,
batches, objectives and Adam 0.003 / batch 16 / 800-step budget. Ordinary context
zeros the memory read. Some memory weights are consequently inactive in its
answer computation; identical allocated parameters do not imply equal effective
capacity, FLOPs or cost. Both receive the same address supervision during
training; inference never receives those labels. This is answer likelihood
training on a synthetic fixture, not ordinary-language pretraining.

There are 384/96/96 train/dev/final worlds, seeds 4101/5101/6101, with disjoint
world IDs, histories and template/question families. Three names, two attributes
and six arbitrary value symbols are shared across splits. Values intentionally
do not enforce real-world type semantics: an attribute named `pet` can take the
symbol `blue`. This prevents attribute type from revealing the answer but limits
any natural-language interpretation. Final worlds were never used for fitting
or development selection. Two training seeds reuse the same final cases; 192
seed-case predictions are not 192 independent worlds.

The 80-step pilot scored 32/96 development cases, all unknown/uncertain cases,
and zero known facts. It is retained. At 800 steps, seed 31 scored 384/384 on
training; zeroing state reduced this to 128/384, with zero known facts correct.
Development scores were 51/96 and 59/96; both preservation scores were 0/16.
The planned 800-step budget was retained without additional tuning. Source,
protocol, all split identities and all four checkpoints were sealed before final
answer generation. Python source hashes canonicalize LF; other hashes bind raw
bytes. Old experimental files and results were not edited.

## Frozen final answers

All methods use the same 96 final questions and greedy byte decoding. The old
selector is an **unqualified diagnostic** feeding selected raw records into the
ordinary decoder under the same 96-token suffix cap. Its selection distribution
differs from that decoder's recent-context training; it is not a reproduction
of the historical pretrained-Llama result. Zero-state reuses the integrated
decoder after discarding state at answer time, a distribution-shift ablation.

| Seed | Method | Exact /96 | Known /64 | Unsupported /32 |
| --- | --- | ---: | ---: | ---: |
| 31 | Ordinary | 22 | 3 | 13 |
| 31 | Integrated | 23 | 9 | 18 |
| 31 | External selector diagnostic | 29 | 4 | 7 |
| 31 | Integrated, state zeroed | 32 | 0 | 0 |
| 47 | Ordinary | 34 | 4 | 2 |
| 47 | Integrated | 25 | 14 | 21 |
| 47 | External selector diagnostic | 34 | 4 | 2 |
| 47 | Integrated, state zeroed | 32 | 0 | 0 |

| Category, 16 cases each | Ordinary 31 | Integrated 31 | Ordinary 47 | Integrated 47 |
| --- | ---: | ---: | ---: | ---: |
| Correction | 1 | 2 | 0 | 3 |
| Preservation | 0 | 0 | 0 | 1 |
| Long recall | 1 | 3 | 0 | 5 |
| Local fact | 1 | 4 | 4 | 5 |
| Unknown | 8 | 7 | 15 | 9 |
| Conflicting unconfirmed claims | 11 | 7 | 15 | 2 |

`?` is the sole correct absent-evidence answer. The conflicting-claims category
has no authoritative fact; it differs from the older selector experiment's
explicit-replacement `conflict` category. The 32/96 zero-state result is pure
abstention, not factual recall. Known-fact gains of 6 and 10 are descriptive;
very low absolute correctness and unsupported-answer regressions prevent a
general answer-quality claim.

Selected actual generated answers (full histories are in the split JSONL):

| Seed / case | Expected | Ordinary | Integrated |
| --- | --- | --- | --- |
| 31 / `final-correction-002` | `red` | `?` | `red` |
| 31 / `final-correction-003` | `red` | `red` | `?` |
| 31 / `final-preservation-000` | `blue` | `dog` | `?` |
| 31 / `final-unknown-001` | `?` | `?` | `blue` |
| 47 / `final-local-002` | `cat` | `cat` | `blue` |

The first two ask which color belongs to Ada and Cyd, respectively. The
preservation and unknown examples ask which pet belongs to Ada and Cyd.
These are model-generated byte sequences, not substituted scorer strings.

## Total work and resources

Each method ingests/scans 22,098 history byte tokens. Ordinary and integrated
selected prompts total 11,728 tokens; integration does not reduce this input.
The external diagnostic selects 9,304 tokens but still scans the full history.
Integrated memory additionally encodes 21,127 update tokens and updates 971
records. Slot matrix operations are additional work beyond token-position counts.

| Seed / method | Forwarded positions | Full-history answer time, sum ms | Peak process bytes | Optimizer-loop seconds |
| --- | ---: | ---: | ---: | ---: |
| 31 ordinary | 12,015 | 348.8 | 210,432,000 | 49.334 |
| 31 integrated | 33,223 | 1,088.3 | 212,750,336 | 38.245 |
| 47 ordinary | 11,957 | 341.0 | 211,251,200 | 34.001 |
| 47 integrated | 33,208 | 1,112.9 | 213,041,152 | 39.148 |

The external diagnostic takes 299.4/308.1 ms and 9,576/9,534 forwarded positions.
Integrated is about 2.8 times the forwarded positions and 3.1/3.3 times the
measured answer time. Total forward positions are an explicit workload proxy,
not FLOPs, energy, or full attention/slot operation counts. Timings include
history consumption and answer generation, not process/model startup; exact
parent command wall times are in check JSON. Evaluation processes also ran on
a shared host, so these are observations rather than controlled benchmarks.

Four main optimizer loops consumed 160.73 seconds total: 3,200 optimizer steps
and 51,200 sampled case presentations. Training peaks range
from 309,719,040 to 310,620,160 process bytes. Pilot, tests, diagnostics and full
retraining replay add work and are retained separately. Runtime is Python 3.12.14,
Torch 2.14.1+cpu, one Torch training thread, 12 logical host CPUs and about 25.1 GB
physical RAM (12.7 GB available at the initial probe). CUDA is unavailable in this
Torch build. `nvidia-smi` was absent and hardware WMI access was denied; current
physical GPU identity was not verified. No GPU or paid training was used.

Process peak RSS includes Python/Torch, checkpoint loading and allocator effects;
it is not incremental state memory. Tensor state is fixed at 1,152 bytes, plus
the bounded suffix and runtime overhead. Smaller state alone establishes no
total-resource benefit.

## Failure diagnosis and next experiment

Post-evaluation argmax diagnostics score address routing without regenerating
answers or injecting gold state. Read addresses match 20/96 and 29/96 queries;
write addresses match 129/971 and 350/971 records. The model fits familiar
training wording but fails to route unseen wording reliably. This identifies a
representation/transfer problem; it does not prove that stale-state overwrite
alone caused every failed answer.

The next specific experiment is a new version with mixed record/query word
orders during training, an explicit held-out grammar family, and separate
router-versus-decoder development measurements under the same CPU budget.
Verify correction and unrelated-preservation learnability before opening a new
final split. Do not reuse these final worlds to tune that model. Unseen entity
inventory and longer/capacity studies remain later prerequisites.

## Engineering evidence, CI and reproduction

All exact commands, exit codes, source identities and logs are retained in
[checks](../../artifacts/integrated-memory-v1-20261102/checks). Local Python tests:
149 passed. Windows and Linux mypy each pass on 27 source files. Node syntax
checks pass; Node tests have 13 passes and one optional live-browser skip.
CLI help/diagnose, dependency checks and package build pass. New/changed runtime,
test and analysis code passes focused lint/format. Repository-wide Ruff exits 1
with the 49 existing findings in three frozen v2 research scripts; full format
check exits 1 for the same three files. Their hash-bound bytes remain unchanged.
An initial incorrectly ordered `scripts/check.py` invocation exited 1 before
training; its evidence is retained under `foundation/initial-wrapper-failure-*`.

A full independent 800-step seed-31 retraining reproduced **all model parameters,
the loss curve and Torch RNG exactly** on this runtime; serialized file hashes
differ because new timing and memory metadata are recorded. See
[training parity](../../artifacts/integrated-memory-v1-20261102/reproduction/parity.json).
An isolated wheel installation reproduced the generated token IDs of six sealed
final cases exactly, using the installed runtime rather than the editable checkout:
[installed parity](../../artifacts/integrated-memory-v1-20261102/reproduction/installed-parity.json).
The wheel install also passed the preserved ordinary/recurrent CLI/resume smoke.

| Local command family (full argv in check JSON) | Exit code |
| --- | ---: |
| `$py -m pytest -q -p no:cacheprovider` | 0 (149 passed) |
| `$py -m mypy` and `$py -m mypy --platform linux` with recorded cache paths | 0 each |
| `$py -m ruff check src tests scripts/analyze_integrated_memory.py scripts/download_chat_backbone.py scripts/smoke_chat_foundation.py` | 0 |
| `$py -m ruff format --check` on the same paths | 0 |
| `$py -m ruff check . --output-format concise` | 1 (49 frozen-script findings) |
| `$py -m ruff format --check src tests scripts` | 1 (three frozen scripts) |
| `$py -m build --no-isolation --outdir .../package-final` | 0 |
| `$py scripts/check_wheel.py` with recorded wheel/sdist/output/config arguments | 0 |
| `$py -m pip check`, main/study CLI help, main CLI diagnose | 0 each |
| `npm.cmd --prefix web/vercel run check` and `npm.cmd --prefix web/vercel test` | 0 each |
| Eight sealed `integrated_study evaluate` calls and full training replay | 0 each |
| `git diff --check` | 0 |

The [check summary](../../artifacts/integrated-memory-v1-20261102/checks-summary.json)
retains each full command, source identity record location, status and exit code.

The exact base commit is `9163780930ea91c09d596e3e6284dc9e96f67109` on `main`.
[GitHub Actions run 41472041835](https://github.com/ShamGaneshan2008/Toruk/actions/runs/41472041835)
failed web syntax checking and Python Ruff; subsequent tests/types/build were
skipped. [Remote evidence](../../artifacts/integrated-memory-v1-20261102/remote-ci.json)
distinguishes this committed merge from the current local, uncommitted work,
which is **NOT_RUN remotely**. Local checks are not remote CI.

Checkpoint SHA-256 values (all use the new `toruk-integrated-lm-v1` format):

```text
ordinary-31   27042916257f812f4f84676524050abf715c522c6dfa3398cd0a02769f3dd233
integrated-31 12ab8faa7e31f02e8973dbe56ffb2f70b0efdebb73da1b09b58a562c38866cb6
ordinary-47   3f7f417d65f9e4553dfc1a503de5d2a6f95a5ad932162b34209dd823ac78423a
integrated-47 e073857e21cb2aad44e8b08e4bb2e167ab3d5e3f8f9e65aac3e0f9f9fd48017e
```

Weights are saved locally under `artifacts/integrated-memory-v1-20261102/train`.
The existing Git rule ignores `artifacts/**/*.pt`; retain/copy those files along
with the JSON, raw answers and source archive when transferring this experiment.
Private architecture notes stay Git-ignored. Pre-existing merge repair edits and
check artifacts remain in the working tree. No checkpoint was overwritten.

Files added/changed for this milestone: `src/toruk_lm/integrated_memory.py`
(runtime and new checkpoint/state formats), `src/toruk_lm/integrated_study.py`
(data, training, scoring, seal and CLI), `scripts/analyze_integrated_memory.py`
(post-evaluation diagnostics), `tests/test_integrated_memory.py` (11 tests),
the public protocol/results, private architecture note, README, MANIFEST.in and
`.gitattributes`. The experiment directory contains datasets, weights, source
snapshot, predictions, checks and resource records. The [Git status snapshot](../../artifacts/integrated-memory-v1-20261102/git-status.txt)
records the combined dirty working tree, including prior authorized work.

Exact Windows PowerShell reproduction, from the repository root, using fresh
output paths and the recorded environment:

```powershell
$py = '.\.venv\Scripts\python.exe'
$run = 'artifacts/integrated-memory-v1-replay'
$selector = 'artifacts/chat-selector-v2-20261101/selector.json'
& $py -m toruk_lm.integrated_study data --output "$run/data"
foreach ($seed in @(31,47)) {
  foreach ($variant in @('ordinary','integrated')) {
    & $py -m toruk_lm.integrated_study train --data "$run/data" --output "$run/train/$variant-$seed.pt" --variant $variant --seed $seed --steps 800
    if ($LASTEXITCODE -ne 0) { throw 'Training failed' }
  }
}
$weights = @("$run/train/ordinary-31.pt", "$run/train/integrated-31.pt", "$run/train/ordinary-47.pt", "$run/train/integrated-47.pt")
& $py -m toruk_lm.integrated_study freeze --data "$run/data" --checkpoints $weights --selector $selector --protocol docs/research/integrated-memory-v1-protocol.md --output "$run/freeze.json"
foreach ($seed in @(31,47)) {
  foreach ($mode in @('ordinary','integrated','external','zero')) {
    $variant = if ($mode -in @('ordinary','external')) { 'ordinary' } else { 'integrated' }
    $extra = if ($mode -eq 'external') { @('--selector',$selector) } elseif ($mode -eq 'zero') { @('--zero-state') } else { @() }
    & $py -m toruk_lm.integrated_study evaluate --data "$run/data" --checkpoint "$run/train/$variant-$seed.pt" --split final --freeze "$run/freeze.json" --output "$run/final/$mode-$seed.json" @extra
    if ($LASTEXITCODE -ne 0) { throw 'Evaluation failed' }
  }
}
```

To replay the **existing** sealed checkpoint without retraining, use a fresh
output filename, its original `data`/`freeze.json`, and one listed checkpoint.
Source changes cause freeze verification to refuse the replay; the retained
`source/` archive permits restoring the sealed kernels in an isolated checkout.
Exact training parity is scoped to this CPU/software runtime, not promised
across different Torch versions or devices.
