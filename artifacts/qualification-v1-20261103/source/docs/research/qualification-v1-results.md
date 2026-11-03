# Independent memory qualification v1: useful benefit fails

On 3 November 2026, nine methods were evaluated at two existing training seeds
and three fresh evaluation seeds. The frozen protocol preceded generation.
There are 168 distinct worlds, repeated at +0/+8/+32 irrelevant-turn loads;
multi-fact worlds generate two answers and require both to match. All 18 fresh
evaluation subprocesses completed, producing 9,072 world predictions and 10,368
generated answers. No fitting or epoch selection used these final worlds.

[Frozen protocol](qualification-v1-protocol.md),
[freeze and environment](../../artifacts/qualification-v1-20261103/freeze.json),
[full evidence report](../../artifacts/qualification-v1-20261103/report.md),
[raw answers](../../artifacts/qualification-v1-20261103/raw),
[summary and uncertainty](../../artifacts/qualification-v1-20261103/summary.json),
[verdicts](../../artifacts/qualification-v1-20261103/verdicts.json),
[failure examples](../../artifacts/qualification-v1-20261103/examples.json),
and [paper outline only](qualification-v1-paper-outline.md) form the review package.

## Gate 1: components and reproduction

| Component | What exists and what it does |
|---|---|
| Ordinary Toruk LM | `toruk-ordinary-v1` weights exist at `artifacts/foundation-001/train/checkpoint.pt`; byte continuation, not instruct chat. The separate historical minimal-demo checkpoint is missing. |
| Controlled recurrent model | Implemented and runnable with newly generated smoke weights; the evaluated M6 recurrent checkpoint is missing. Smoke weights do not restore historical M6 evidence. |
| Chat selectors | Separately trained v1/v2 JSON rankers exist; v2 hash begins `abd9d2d1c20e`. They select raw turns, not generate language or implement integrated memory. |
| Integrated model | Four real `toruk-integrated-lm-v1` checkpoints exist, ordinary/integrated at seeds 31/47, 800 training steps each. Prior failure was poor transfer, not a missing implementation/checkpoint. |
| Chat backbone | Pinned pretrained Qwen2.5-0.5B-Instruct weights exist. Ollama/Llama is a separately configurable path, not evaluated in this new qualification. |
| Chat UI wiring | Local page → Node proxy → Python inference server/worker → pretrained backbone, optionally with an explicitly configured selector. The integrated prototype uses its separate research CLI and is not connected to chat. |

The [inventory](../../artifacts/qualification-v1-20261103/inventory.json) records
actual local existence, formats and full weight hashes. Freeze verification
checks the previous integrated milestone's source, data, protocol, selector and
checkpoint identities before creating this experiment and again before each
new evaluation. Its archived full-training parity remains historical evidence;
this run adds frozen-checkpoint inference, not a second claim of retraining.
M6/M7 exact model replay remains blocked by missing original weights and archived
kernel mismatch; old generated outputs can be rescored separately. V2 selection
decision replay was previously reproduced, while byte-exact training parity was
not. No component was silently replaced or promoted to qualified memory.

## Outcomes

At ordinary history load, recent context scores 33/168 at both training seeds;
lexical selection scores 32/168 and 31/168; learned external selection scores
33/168 and 31/168; integrated memory scores 48/168 and 34/168. All methods fail
the prespecified minimum quality gate. The integrated seed-31 result contains
**zero correct known worlds**: its 48 correct worlds are abstentions. Seed 47
gets 31/120 known worlds correct but makes 45/48 unsupported unknown/ambiguous
answers, versus recent context's 27/48. Zeroing integrated state produces 48/168
by abstaining throughout at both seeds. This is not useful factual memory.

| Claim | Verdict | Evidence |
|---|---|---|
| Frozen integrated mechanism exists and runs | PASS | Old seal validates; all new checkpoint evaluations complete; existing state/resume tests pass. |
| Minimum useful factual quality | FAIL | Integrated known accuracy is 0/120 and 31/120; all seven-category quality gates fail. |
| Repeatable useful gain over simple baselines | FAIL | Quality gate fails, training seeds behave differently, and abstention-only control scores better overall. Descriptive aggregate differences and conditional intervals remain in the report. |
| Correction with unrelated preservation and safe abstention | FAIL | Seed 31 has no known recall; seed 47 has 45/48 unsupported answers. Multi-fact exact score is 0/24 at ordinary load for both integrated seeds. |
| Fewer selected prompt tokens | PASS for external selector only, descriptive | Learned selector uses 16,091 tokens versus recent 21,900, summed over 192 answers. Integrated uses the same 21,900 as recent context. |
| Lower total computation or quality-preserving cost | FAIL for the measured candidates | Integrated forwards 53,451/53,910 positions versus recent 22,492/22,621. All quality gates fail. Position counts are a workload proxy, not FLOPs. |
| Controlled latency or memory advantage | INCONCLUSIVE | Sampled RSS is approximately 208–209 MiB across methods; shared-host timing overlaps verification. Integrated observed latency is higher, but this is not an isolated performance benchmark. |
| Population training-seed or conversational generalization | INCONCLUSIVE | Only two historical training seeds; finite shared entity/value vocabulary; no conversational integrated decoder. |
| Paper readiness / novelty / publishability | INCONCLUSIVE | Outline and limited primary-source bibliography only; negative synthetic evidence and incomplete literature/venue review. |

The complete table covers **every** baseline and ablation, with per-seed accuracy,
unknown behavior, selected tokens, all scanned history, forwarded positions,
latency and sampled memory. It also includes category, load and paired bootstrap
tables. Bootstrap intervals preserve paired worlds and both trained checkpoints;
they condition on those two checkpoints and do not estimate training-population
uncertainty. Stress loads reuse worlds, so they are not new independent samples.

No-correction bypasses only explicit `Amend ` state updates; preservation ablation
clears state before every write; half-capacity masks half the slots while keeping
all allocated parameters. These inference interventions shift the trained
distribution and do not establish a training-level causal mechanism. The learned
external selector is also an unqualified diagnostic under the tiny decoder,
not a matched reproduction of its historical Llama chat result.

The prior milestone diagnosed unseen-wording routing failure. This qualification
adds severe seed sensitivity between factual attempts and broad abstention;
destructive or zero-state interventions can improve aggregate exact score while
eliminating known recall. The bounded proposed follow-up in the outline tests
mixed grammar training and development router/decoder quality before any new
final set is opened. It was not run or tuned on this qualification's answers.

## Checks, failures, and limits

Python tests: 153 pass, including four qualification guard tests. Windows and
Linux mypy pass on all 27 runtime source files. CLI help/diagnose, package
dependencies, ordinary reproduction/validation/summary and controlled resume
smoke pass. Node syntax and ordinary Node tests pass (13 passes, one optional
live-handler skip); the separately enabled live-handler run passes both tests
with no skips and retains six real responses. Its correction probe nevertheless
answers `The current date is Tuesday.` after a meeting update to Friday; this
is a quality failure despite passing integration assertions. Real Qwen HTTP
smoke passes: answer `LIME42`, selector-unavailable
mode rejected, backend outage returns 503. This verifies integration, not broad
chat quality. Page handlers run in a DOM harness; an interactive browser session
was not tested.

Repository-wide Ruff exits 1 with 49 findings in three frozen selector research
scripts; format exits 1 for the same three files. Those hash-bound scripts remain
unchanged. Focused checks cover current runtime/tests and new qualification tools.
The default build exits 1 because the existing `dist` archive cannot be replaced;
a build into a fresh package directory exits 0. All failures are retained.

The analysis child saved valid UTF-8 summary/table files and exited 0; its parent
check command then exited 1 printing replacement characters under Windows cp1252.
This is a reporting failure, not a failed or repeated experiment. Its recorded
child exit code is 0. Subsequent reporting commands set `PYTHONIOENCODING=utf-8`.

The [exact command ledger](../../artifacts/qualification-v1-20261103/commands.json)
and detailed report retain commands, exit codes, logs and source identities.
The frozen evaluator checks all identities before generation. Source snapshots,
checkpoint/data hashes and environment versions accompany raw output; original
training time/peak records are copied without counting ablations as new training.
Checkpoint/model startup is excluded from per-answer latency but included in
process wall time and sampled RSS. All history is rescanned for each generated
answer, including both multi-fact answers. RSS is sampled every 5 ms, includes
framework/loading overhead, and can miss short peaks. Fixed state size is not
total process-memory savings. No FLOPs, energy or GPU-cost claim is made.

Remote `main`, local `HEAD` and cached `origin/main` are all
`9163780930ea91c09d596e3e6284dc9e96f67109`; ahead/behind is 0/0.
[GitHub Actions run 41472041835](https://github.com/ShamGaneshan2008/Toruk/actions/runs/41472041835)
is completed/failure: web syntax and Python Ruff failed, downstream tests/types/
build were skipped. The [fresh GitHub response](../../artifacts/qualification-v1-20261103/remote-ci.json)
binds both jobs to that SHA. Current local changes are **NOT_RUN remotely**.
No commit, push, force-push, download, deployment or paid computation was made.
Existing dirty work and branch histories remain preserved; private notes and
weights remain Git-ignored. Git alone is insufficient to transfer the ignored
checkpoints; preserve them locally with their recorded hashes.

To reproduce frozen inference from this checkout, use the recorded environment:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
& $py scripts/qualify_memory.py freeze --run artifacts/qualification-v1-replay
& $py scripts/qualify_memory.py run --run artifacts/qualification-v1-replay
& $py scripts/qualify_memory.py analyze --run artifacts/qualification-v1-replay
& $py scripts/package_qualification.py --run artifacts/qualification-v1-replay
```

Use a fresh directory. The evaluator refuses frozen-source drift and output
overwrites. Old sealed sources are archived for an isolated reconstruction;
byte-identical execution across different Torch/platform versions is not promised.
