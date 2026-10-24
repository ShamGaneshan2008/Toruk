# Reproducibility handoff

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
