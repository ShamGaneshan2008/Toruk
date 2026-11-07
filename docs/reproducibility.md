# Reproducibility handoff

## Selected completed experiment: owned next-token LM v1

The current two-device target is the [completed owned-LM study](research/owned-lm-v1-results.md),
not the historical M6 replay described later. Its claim is negative: on 48 synthetic
IID held-out questions at seeds 31 and 47, memory-on scored 17/96 versus ordinary
14/96 and parameter-matched ordinary 15/96. The predeclared accuracy/efficiency
criterion failed. Regeneration does not create a new independent test set.

Use `configs/owned-lm-primary-v1.json`: 192/24/48 train/dev/held-out documents,
generator seeds 3201/4201/5201, eight fits of 256 steps, float32, one CPU thread,
32 local positions and four memory slots. No external backbone, downloaded
checkpoint, private transcript, CUDA device, or machine-specific directory is
required. The run creates all eight `toruk-owned-next-token-v1` checkpoints below
its own output directory. The 512-byte recurrent state is not total process RAM.
It also runs a two-step training profile and a separate partial/resumed fit.

Prerequisites: Git, 64-bit Python 3.12, Node.js 22+ for the broader verification,
network access for installing dependencies, and local disk for CPU PyTorch and
generated artifacts. The recorded runtime is Python 3.12.14 / Torch 2.14.1+cpu;
the Torch pin is in `configs/owned-reproduction-requirements-v1.txt`. Other Python,
Torch, OS and CPU combinations are unqualified until they pass the validator.
The original primary run took 80.26 s; the config enforces a 600-second study
budget. A slower device may exhaust that budget and must report failure. Do not
increase the registered budget silently. Allow several GB for environment setup;
this is planning headroom, not a measured minimum. No GPU or paid job is needed.

From the repository root in **each device's fresh checkout**, use these PowerShell
commands. The environment and output paths deliberately contain spaces. Choose
fresh names on a repeat; preserve previous evidence. `Need-Zero` checks native
exit codes because PowerShell does not automatically stop on them.

```powershell
$ErrorActionPreference = 'Stop'
function Need-Zero { if ($LASTEXITCODE -ne 0) { throw "Command failed: $LASTEXITCODE" } }
git branch --show-current; Need-Zero
git rev-parse HEAD; Need-Zero
git status --short; Need-Zero
python -m venv '.readiness/Device Env'; Need-Zero
$python = (Resolve-Path '.readiness/Device Env/Scripts/python.exe').Path
& $python -m pip install 'setuptools==78.1.0'; Need-Zero
& $python -m pip install -r configs/owned-reproduction-requirements-v1.txt --index-url https://download.pytorch.org/whl/cpu; Need-Zero
& $python -m pip install --no-build-isolation -e '.[dev,chat]'; Need-Zero
& $python -m pip check; Need-Zero
& $python -m toruk_lm diagnose; Need-Zero
& $python -m pip freeze | Out-File -Encoding utf8 '.readiness/device-environment.txt'

# Fast execution/validation check: not a research-quality result.
& $python scripts/check.py --timeout 90 --output-dir '.readiness/Device Checks' smoke -- $python scripts/study_owned_lm.py --config configs/owned-lm-smoke-v1.json --output '.readiness/Owned Smoke'; Need-Zero
& $python scripts/check.py --output-dir '.readiness/Device Checks' smoke-validate -- $python scripts/validate_owned_reproduction.py --config configs/owned-lm-smoke-v1.json --run '.readiness/Owned Smoke'; Need-Zero

# Full registered research run: bounded, opt-in, and separate from routine CI.
& $python scripts/check.py --timeout 630 --output-dir '.readiness/Device Checks' primary -- $python scripts/study_owned_lm.py --config configs/owned-lm-primary-v1.json --output '.readiness/Owned Primary'; Need-Zero
& $python scripts/check.py --output-dir '.readiness/Device Checks' primary-validate -- $python scripts/validate_owned_reproduction.py --config configs/owned-lm-primary-v1.json --run '.readiness/Owned Primary' --reference artifacts/owned-lm-v1-20261104/primary; Need-Zero
& $python scripts/report_owned_lm.py --run '.readiness/Owned Primary'; Need-Zero
Get-Content '.readiness/Owned Primary/table.md'

# Full engineering verification includes Python, Node and HTTP integration.
& $python scripts/verify.py --output-dir '.readiness/Device Verification'; Need-Zero
git diff --check; Need-Zero
```

Expected primary outputs: `registration.json`, `data/{manifest,train,dev,heldout}.json`,
eight `models/<seed>-<variant>/checkpoint.pt` plus training metadata,
`freeze.json`, sixteen `heldout/*.json` files with 768 raw answers, `summary.json`,
and the report's `table.md`, `aggregates.json`, `failed-cases.json`.
`summary.criterion.passed` must remain false for reproduction of the recorded
negative result; successful execution does not imply scientific success.

The validator uses `configs/owned-reproduction-v1.json`. It checks canonical
dataset hashes against regeneration, normalized-LF source identities, the exact
study config, local checkpoint SHA256 and training lineage, protocol/model/mode,
token decoding, scoring, summary consistency and the original numerical criterion.
For the primary run it also checks the sealed tracked raw reference files. The
reference needs **no historical checkpoint**. New checkpoint serialization bytes
need not equal historical bytes; each new evaluation must bind its own weights.
Raw generated IDs, answers, category scores and deterministic work must match
exactly. NLL and per-document loss permit `abs_tol=1e-5, rel_tol=1e-5`; same-run
rescoring uses `abs_tol=1e-12`. These are conservative engineering bounds,
not a measured cross-device numerical guarantee. A token change fails even if
aggregate accuracy ties. Time, CPU time and RSS are reported without equality
gates. Never widen tolerances or edit reference answers to force a pass.
LF/CRLF text conversion is accepted for config/driver bindings; other byte changes
are rejected. Canonical JSON hashing keeps the recorded reference portable.

All three datasets are generated by `owned_data.py` from authored synthetic
templates, with canonical JSON hashes recorded in registration. The full split
hashes are listed in the completed-study report. No third-party text corpus or
pretrained model license enters this experiment. This repository has no LICENSE
file; no permission for external redistribution is established by this guide.
Torch and its dependencies retain their own installed distribution notices.
Generated `.pt` files under `artifacts/` and everything in `.readiness/` are ignored;
review `git status` before sharing anything. No original weights need distribution.

Routine Linux CI runs the small owned study and the new validator alongside
existing Python/Node checks. A Windows job runs the same smoke from a checkout
whose path contains spaces. Neither job trains the primary 256-step study.
Local runs do not establish that these uncommitted workflow edits passed hosted CI.
The separate internal execution record is `docs/internal/two-device-reproduction.md`.

## Research claim closure audit

The optional `scripts/research_claim_closure.py` binds the published primary
study, regenerates its evidence using the existing driver, validates raw outputs,
and reports its negative joint-claim verdict. It adds paired question-block
bootstrap intervals and descriptive length bins as explicitly posthoc analyses.
It does not create independent test data or change the original scoring gate.

After environment setup above, use fresh output names:

```powershell
$py = (Resolve-Path '.readiness/Device Env/Scripts/python.exe').Path
$package = '.readiness/Claim Closure'
& $py scripts/research_claim_closure.py freeze --package $package; Need-Zero
& $py scripts/check.py --timeout 630 --output-dir "$package/checks" reproduce -- $py scripts/study_owned_lm.py --config configs/owned-lm-primary-v1.json --output "$package/primary"; Need-Zero
& $py scripts/check.py --output-dir "$package/checks" analyze -- $py scripts/research_claim_closure.py analyze --package $package --run "$package/primary"; Need-Zero
```

`registration.json` binds inputs before regeneration. `analysis/results.json`
contains gates, checkpoint identities, costs, coverage gaps and uncertainty;
`analysis/per-case.jsonl` and `.csv` retain every regenerated answer and work
counter. A positive-looking subgroup cannot override the original failed gate.
No hosted CI job runs this full primary regeneration; routine tests cover the
audit's pairing and integrity checks. The broader source/metric limitations
and two-device qualification limits above still apply.

## Copy-gap query-read-gate experiment

The [frozen protocol](research/copy-gap-v1-protocol.md) defines a single inference
intervention, unchanged frozen weights and matched evidence gaps. Its registered
quality gate failed: local exact copying was 0/12 per fitted seed with and without
the gate. All ordinary controls also failed. No heldout-driven second mechanism
was attempted. The experiment adds no model training or external backbone.

With the environment above installed, use fresh names in PowerShell. If the
original parent weights are missing, the first command reconstructs them with
the unchanged, separately bounded primary study. Existing validated parents can
be supplied directly to `freeze` instead; no undocumented checkpoint is needed.

```powershell
$py = (Resolve-Path '.readiness/Device Env/Scripts/python.exe').Path
$checks = '.readiness/Copy Gap Checks'
$parent = '.readiness/Parent Primary'
$probe = '.readiness/Copy Gap'
# Optional prerequisite reconstruction; omit only when using a validated parent.
& $py scripts/check.py --timeout 630 --output-dir $checks parent -- $py scripts/study_owned_lm.py --config configs/owned-lm-primary-v1.json --output $parent; Need-Zero
& $py scripts/check.py --output-dir $checks freeze -- $py scripts/copy_gap_probe.py freeze --package $probe --parent $parent; Need-Zero
& $py scripts/check.py --timeout 195 --output-dir $checks dev -- $py scripts/copy_gap_probe.py run --package $probe --phase dev; Need-Zero
& $py scripts/check.py --timeout 195 --output-dir $checks heldout -- $py scripts/copy_gap_probe.py run --package $probe --phase heldout; Need-Zero
& $py scripts/copy_gap_probe.py audit --package $probe --phase heldout; Need-Zero
```

`freeze` verifies the parent against the versioned reproduction contract and seals
new config/source/checkpoint/dataset hashes before inference. `dev` and `heldout`
have independent 180-second caps, including eight fresh method/seed processes per
phase. A started phase cannot be retried. Keep partial failures rather than
overwriting them. Development quality cannot change thresholds or mechanism.
The final test is a single pass; `audit` only rechecks saved evidence.

Each phase saves eight raw JSONL files, process/resource logs, commands,
`results.json` and `complete.json`. An exit code of zero means successful execution
and integrity checks; inspect `results.json.passed` for the scientific decision.
The experiment is outside routine CI; unit tests cover intervention equivalence,
gap/length matching, unchanged weights and phase guards. No broad accuracy or
full-system efficiency claim follows from this failed fixed-format probe.

## Adversarial counterfactual-twin review

The [registered challenge](research/adversarial-twins-v1-protocol.md) freezes all
models and tests two equal-length source values in otherwise identical prompts.
It reports exact generated answers separately from offline value likelihood.
The primary both-arms-correct gate failed at both fitted seeds; no mechanism was
changed after development or heldout evaluation. This full challenge is outside CI.

After the environment and optional parent reconstruction described above, use
fresh names in PowerShell and check each native exit code with `Need-Zero`:

```powershell
$py = (Resolve-Path '.readiness/Device Env/Scripts/python.exe').Path
$parent = '.readiness/Parent Primary'
$review = '.readiness/Adversarial Twins'
$checks = '.readiness/Adversarial Checks'
& $py scripts/check.py --output-dir $checks freeze -- $py scripts/adversarial_twins.py freeze --package $review --parent $parent; Need-Zero
& $py scripts/check.py --timeout 255 --output-dir $checks dev -- $py scripts/adversarial_twins.py run --package $review --phase dev; Need-Zero
& $py scripts/check.py --timeout 255 --output-dir $checks heldout -- $py scripts/adversarial_twins.py run --package $review --phase heldout; Need-Zero
& $py scripts/adversarial_twins.py audit --package $review --phase heldout; Need-Zero
```

Registration seals protocol, code, datasets and parent checkpoints after the
original reproduction validator passes. Each phase has a 240-second cap and
cannot be restarted after it begins. A zero exit code means execution/integrity,
not scientific success. Inspect `heldout/results.json` and the prespecified
`quality_passed` / `joint_passed` fields. Raw replies, both candidate likelihoods,
generation/scoring work and fresh worker/monitoring costs are retained. Process-tree
RSS is sampled every 20 ms, not a guaranteed physical-memory high-water mark.

## Historical foundation handoff

There are two different targets: **a clean-checkout execution smoke** that needs
no owner artifacts, and **historical research replay** that needs original weights
and matching archived source. Passing the smoke does not establish useful memory,
research reproducibility, or paper/release readiness.

## Environment and setup

Use Python 3.11 or later in a fresh virtual environment; Python 3.12 is the
recommended starting point and the Ubuntu CI runtime. The 2026-10-24 handoff
smoke exercised Python 3.12.14 and PyTorch 2.14.1+cpu on Windows 11. Earlier
Windows checks also exercised Python 3.14.6.
Do not infer bitwise parity across library versions or operating systems.

Run from the repository root. Record `git rev-parse HEAD` and `git status -sb`
before execution; preserve any existing work. The handoff source commit was
`2966f63c4787f61f724d4f4338a2dd2fff519504`; this guide records verification
against that code. Git, Python, disk space for a virtual
environment and CPU PyTorch, and initial network access are prerequisites.

Windows PowerShell (no activation or execution-policy change required):

```powershell
python -m venv .venv
$python = (Resolve-Path .venv/Scripts/python.exe).Path
& $python -m pip install 'setuptools==78.1.0'
& $python -m pip install 'torch==2.14.1+cpu' --index-url https://download.pytorch.org/whl/cpu
& $python -m pip install --no-build-isolation -e '.[dev]'
& $python -m pip check
& $python -m toruk_lm diagnose
```

POSIX shell:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'setuptools==78.1.0'
python -m pip install 'torch==2.14.1+cpu' --index-url https://download.pytorch.org/whl/cpu
python -m pip install --no-build-isolation -e '.[dev]'
python -m pip check
python -m toruk_lm diagnose
```

These pin the exercised Torch/build backend, **not a complete environment lock**.
[pyproject.toml](../pyproject.toml) declares broad runtime/dev ranges; transitive
and development dependencies can change. Save `python -m pip freeze --all`, the
Python version and `diagnose` output with your run (use `& $python` on PowerShell).
For stricter replay obtain a compatible complete lock/wheel set and verify its
checksums; do not treat a Windows lock as portable. If the specified CPU wheel
is unavailable for your Python/platform, report that requirement as BLOCKED
rather than silently substituting a GPU build. Installation/download time and
virtual-environment disk footprint are not measured or included in the run cap.
Once installed, the smoke needs no network, external data or downloaded weights.

## Bounded smoke command

Use an unused output directory and check label. PowerShell, continuing above:

```powershell
& $python -m toruk_lm validate-config --config configs/reproduce-smoke-v1.json
& $python scripts/check.py --timeout 120 smoke-handoff -- $python -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output artifacts/handoff-smoke
```

POSIX shell, in the activated environment:

```sh
python -m toruk_lm validate-config --config configs/reproduce-smoke-v1.json
python scripts/check.py --timeout 120 smoke-handoff -- python -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output artifacts/handoff-smoke
```

The outer wrapper gives the command a 120-second timeout; the frozen
[smoke config](../configs/reproduce-smoke-v1.json) has a 110-second between-stage
budget. Never reuse an existing label/output or delete old evidence to rerun:
choose new literal names. Wrapper options must come **before** the label.
No large or paid job is required.

Every output directory must be fresh. `reproduce` validates the entire config,
then generates synthetic data, trains small ordinary/recurrent models, saves and
reloads checkpoints, checks resumed weights and RNG against uninterrupted
training, checks recurrent session cloning/reset, generates answers, and scores
raw outputs. The smoke run is an execution check; its scores are not evidence of
useful memory. Its config freezes seeds and budgets. Unknown fields and changes
to the v1 protocol are rejected; a different experiment needs a new protocol.

The code uses a width-8, two-head, one-layer decoder with context 64, seed 23,
fixture seed 17, two worlds per split, two training steps and at most two generated
tokens per answer. Each model runs uninterrupted training and a separate
one-step-plus-resume path; this is more work than two optimizer updates in total.
See [implementation](../src/toruk_lm/reproducibility.py) and
[generator](../src/toruk_lm/worlds.py). Train/validation roles are checked and
entities separated; validation supplies generated-answer scores. Test bytes
are generated/hashed but no model scores test worlds. Gold labels are used only
in training/offline scoring, not as generation inputs.

Expected files under `artifacts/handoff-smoke/`:

| Files | Purpose |
| --- | --- |
| `config.json`, `stages.json`, `summary.json`, `manifest.json` | Frozen settings, completed stages, overall status/resource observations and file hashes |
| `data/manifest.json`, `data/train.jsonl`, `data/validation.jsonl`, `data/test.jsonl` | Generator/seed/split identities and synthetic worlds |
| `ordinary-full/`, `ordinary-part/`, `ordinary-resume/` and recurrent equivalents | Training metrics and checkpoints for full/partial/resumed paths |
| `ordinary-eval/predictions.json`, `recurrent-eval/predictions.json` and adjacent `metrics.json` | Raw generated IDs/text, gold labels and stratified metrics |

The wrapper additionally writes `artifacts/checks/smoke-handoff.json` and `.log`,
including exact argv, base Git commit and source hashes, exit code, wall time and
stderr. Retain these with your environment record. Source exports without `.git`
have a null base commit; record the export's originating commit separately.

## Validate the result

Require exit code zero, summary `status: PASS`, both model `resume: PASS`,
and all stages PASS. There should be 12 generated answers per model (24 total),
covering six groups on two validation worlds. Checkpoint hashes bind evaluations
to the resumed weights. The smoke internally checks exact full/resumed weights
and RNG equality, session clone/reset, and rescoring against saved raw answers.

This additional read-only check verifies manifest hashes and derives stored
metrics again from predictions using the repository scorer; it performs no
training or model loading. Run in the repository root, using `& $python -c`
instead of `python -c` on PowerShell:

```sh
python -c "from pathlib import Path; from toruk_lm.reproducibility import verify_files,score_directory; from toruk_lm.worlds import load_worlds; p=Path('artifacts/handoff-smoke'); n=verify_files(p); rows=load_worlds(p/'data/validation.jsonl','validation'); scores={v:score_directory(p/(v+'-eval'),rows,2)['exact_accuracy'] for v in ('ordinary','recurrent')}; print('PASS: hashes',n,'exact_accuracy',scores)"
```

The handoff run on 2026-10-24 recorded zero exact accuracy in all groups for both
models, 5.07 s including startup, 2.50 s inside the pipeline, and cumulative process
peak 285,790,208 bytes. It used a tracked-source export and an existing installed
CPU environment, **not a fresh dependency download/install**. These are measured
observations, not hardware minima, maximums or accuracy acceptance thresholds.
Zero smoke accuracy does not reproduce the full scientific pilot.

Use exact equality for hashes, same-run saved-output rescoring and same-runtime
resume checks. No cross-platform numerical tolerance or bitwise guarantee has
been validated: record any changed scores rather than silently applying a
tolerance. Timing/peak measurements naturally vary and are not equality gates.
Python/Torch versions, CPU kernels, OS, dependency resolution and source line
endings may change results/fingerprints. Preserve original bytes for archival
identity checks; do not normalize/restamp files to force a pass. The exercised
environment emitted Torch's optional missing-NumPy warning; it was retained in
logs and did not prevent the smoke. This does not waive other warnings/failures.

For broader engineering checks, separately run `python scripts/verify.py`
(PowerShell: `& $python scripts/verify.py`) and `python -m build --no-isolation`.
Those are not part of the single 120-second smoke budget.

Use unique check labels: `scripts/check.py` writes logs and machine-readable
command/source/result records under `artifacts/checks/` and refuses to overwrite
existing labels. `verify.py` uses a fresh timestamp prefix by default. Local CI allows 300 s
for cold type checking and tests; ordinary commands retain the 120 s cap.
Prior evidence must be preserved before reusing any historical label.

## Research reproduction and current blockers

The bounded historical primary pilot is described by
`configs/reproduce-primary-v1.json`. It is a negative, single-training-seed
validation study, not a final-test experiment. Owner-held checkpoints, source
archives and frozen protocols are needed for exact historical replay; they are
not included in Git. There is no authorized checkpoint download location.

After the smoke, these are separate, optional commands (PowerShell uses
`& $python` in place of `python`):

```sh
python -m toruk_lm validate-config --config configs/reproduce-primary-v1.json
python scripts/check.py --timeout 120 primary-handoff -- python -m toruk_lm reproduce --config configs/reproduce-primary-v1.json --output artifacts/my-primary
python -m toruk_lm audit-evidence --parent artifacts/m6-validation-001 --handoff artifacts/m6-handoff --studies artifacts/m7-templates-001 artifacts/m7-load-001 --output artifacts/my-tables
```

Profile first using the smoke run and inspect the retained hardware/cost records.
The original primary pilot took 90.94 s including startup and peaked at 352.5 MB;
there is no promise it fits the 110 s stage budget on another machine. A new
primary run trains from scratch; it is not an exact replay of original weights.
`audit-evidence` verifies artifact/data/model identities and derives `results.csv`,
`tables.md` and `audit.json` from stored predictions. It performs no new inference.
`compare-replay` requires exact generated-token and score parity between two run
directories; time measurements are intentionally excluded.

**Historical replay/audit is currently BLOCKED from a clean checkout.** The M6
manifest lists 12 absent checkpoint files: eight study models, two predictors and
two profiling models. No authorized download exists. The historical audit also
requires matching inference/scoring source; the current source fails its archived
identity check (`M6 inference/scoring source mismatch`). The source archive alone
does not supply the weights. Do not remove the gate or fabricate missing files.
Stored predictions/metrics can be inspected, but the documented strict audit
cannot be represented as a successful clean-checkout replay at present. A fresh
primary run is a new single-seed run, not recovery of original weights or an
independent-seed confirmation. M7 studies require the historical prerequisites;
their replay is not covered by smoke success.

The synthetic data manifests define document/world splits and checksums. Only
train/validation data are loaded for model fitting/scoring by research commands.
Unit tests separately inspect test records and oracle labels, including cases
identical to the registered deterministic split. No final-test model score or
wholly unseen-test claim is made. The project currently has no
LICENSE file; no new code/data redistribution permission is granted here. Obtain
an owner-approved license and artifact transfer before an external release.
