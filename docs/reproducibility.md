# Reproducibility commands

Use Python 3.11 or later in a fresh virtual environment. Python 3.14.6 and
PyTorch 2.14.1+cpu were exercised on Windows; the Ubuntu CI runtime is 3.12.
Do not infer bitwise parity across library versions or operating systems.

```sh
python -m venv .venv
# Activate the environment using the command appropriate for your shell.
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ".[dev]"
python -m pip check
python -m toruk_lm --help
python -m toruk_lm diagnose
python -m toruk_lm validate-config --config configs/reproduce-smoke-v1.json
python -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output artifacts/my-smoke
python scripts/verify.py
```

Every output directory must be fresh. `reproduce` validates the entire config,
then generates synthetic data, trains small ordinary/recurrent models, saves and
reloads checkpoints, checks resumed weights and RNG against uninterrupted
training, checks recurrent session cloning/reset, generates answers, and scores
raw outputs. The smoke run is an execution check; its scores are not evidence of
useful memory. Its config freezes seeds and budgets. Unknown fields and changes
to the v1 protocol are rejected; a different experiment needs a new protocol.

On the audited i5-12450H CPU, 16.8 GB RAM machine, the initial smoke took 6.50 s
including process startup, with a cumulative process peak of 313,282,560 bytes.
This is one observation, not a hardware minimum or a timing guarantee. No GPU or
external dataset is needed. `seconds` is a between-stage budget; use an external
process timeout as well (the check wrapper defaults to 120 seconds).

```sh
python scripts/check.py my-smoke -- python -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output artifacts/my-recorded-smoke
python -m build --no-isolation
```

Use unique check labels: `scripts/check.py` writes logs and machine-readable
command/source/result records under `artifacts/checks/` and refuses to overwrite
existing labels. `verify.py` uses a fresh timestamp prefix by default. Local CI allows 300 s
for cold type checking and tests; ordinary commands retain the 120 s cap.
Prior evidence must be preserved before reusing any historical label.

The bounded historical primary pilot is described by
`configs/reproduce-primary-v1.json`. It is a negative, single-training-seed
validation study, not a final-test experiment. Owner-held checkpoints, source
archives and frozen protocols are needed for exact historical replay; they are
not included in Git. There is no authorized checkpoint download location.

```sh
python -m toruk_lm validate-config --config configs/reproduce-primary-v1.json
python -m toruk_lm reproduce --config configs/reproduce-primary-v1.json --output artifacts/my-primary
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

The synthetic data manifests define document/world splits and checksums. Only
train/validation data are loaded for model fitting/scoring by research commands.
Unit tests separately inspect test records and oracle labels, including cases
identical to the registered deterministic split. No final-test model score or
wholly unseen-test claim is made. The project currently has no
LICENSE file; no new code/data redistribution permission is granted here. Obtain
an owner-approved license and artifact transfer before an external release.
