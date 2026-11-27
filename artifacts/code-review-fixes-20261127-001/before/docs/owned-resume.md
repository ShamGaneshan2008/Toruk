# Owned-LM resume integrity v1

The `toruk_lm.owned_resume` adapter adds strict checkpoint validation and a
training/resume CLI for new owned-LM work. It delegates numerical optimization
to the existing trainer. The checkpoint format, tokenizer, model computation,
optimizer schedule, and hash-bound historical sources are unchanged.

The original `toruk_lm.owned_training` API and `python -m toruk_lm.owned_lm`
commands remain available for archived reproduction. They have the historical
validation weakness: optimizer entries that are absent are not checked, and
serialized optimizer settings can override the recorded options. Use the new
adapter for new resumable training; this change does not silently patch those
legacy entry points or waive their source identity checks.

## Usage

The config and document files use the existing owned-LM schemas. `--steps` is
the absolute total number of optimizer updates. Always choose a fresh output.

```powershell
.\.venv\Scripts\python.exe -m toruk_lm.owned_resume train --config configs/owned-lm-smoke-v1.json --data path/to/train.json --checkpoint path/to/fresh.pt --variant memory_on --steps 2 --seed 23
.\.venv\Scripts\python.exe -m toruk_lm.owned_resume validate --data path/to/train.json --checkpoint path/to/fresh.pt
.\.venv\Scripts\python.exe -m toruk_lm.owned_resume train --config configs/owned-lm-smoke-v1.json --data path/to/train.json --checkpoint path/to/continued.pt --variant memory_on --steps 4 --seed 23 --resume path/to/fresh.pt
```

In Python, `owned_resume.train` accepts the same arguments as
`owned_training.train`. `validate_resume(checkpoint, training_documents)` returns
a versioned validation report. CLI validation exits 0 on success and 2 on invalid
inputs. Validation performs zero model forwards and optimizer updates, preserves
the caller's CPU Torch RNG stream, and writes no files.

## Validation contract

- Preserve the original format, source, tokenizer, model and RNG checks.
- Require valid typed options, the exact training dataset identity, and completed
  optimizer progress. Reconstruct total byte/EOS targets from the deterministic
  document schedule.
- Compare complete AdamW parameter groups against the configured optimizer,
  including parameter order, learning rate, betas, epsilon and weight decay.
- Require exactly the moments for parameters that participate in training. Check
  their raw shapes, dtypes, finite values and scalar update counters before those
  values can be used for a resumed update. Serialized dtype corruption cannot be
  hidden by AdamW's casting during loading.
- Allow inactive recurrent parameters in memory-off mode and inactive writers
  when documents fit in one segment; do not require fabricated moments.
- Refuse existing checkpoints, metrics, partial files or adapter receipts. Failed
  input validation creates no output directory and performs no optimizer update.

Successful training also writes an exclusive `<checkpoint stem>.resume.json`
receipt containing the contract version, checkpoint hash, source/adapter hashes,
configuration, seed/options, dataset identity, progress, current Python/PyTorch
environment, and any validated parent checkpoint. The existing checkpoint and
training metrics remain in the original format. Receipts describe validation;
they are not signed evidence or a replacement for a study's frozen registration.

## Limits and acceptance

The legacy loader requires every stored parameter counter to equal the global
optimizer step. It cannot reload checkpoints with intermittent writer updates
caused by mixing short and multi-segment batches. The adapter rejects that
schedule before training rather than creating an unloadable checkpoint. A new
numerical trainer/checkpoint version is required to extend that old contract.

The original checkpoint does not identify its complete creation environment.
The receipt records the adapter's current environment; it does not establish
cross-version or cross-platform bitwise reproducibility. Inputs must remain
immutable during validation/training; concurrent checkpoint replacement is not
supported. OS/I/O failures after training begins can retain partial outputs,
which must be preserved and investigated rather than overwritten.

Acceptance requires corrupt-state rejection before training, exact uninterrupted
versus resumed model/optimizer/RNG/target parity on the same runtime, successful
legacy-checkpoint validation without identity waivers, passing existing tests,
and unchanged historical source bytes. Tests use disposable synthetic documents,
seed 23, tiny float32 CPU models, one thread, and one to three optimizer steps.
These are software checks, not factual-accuracy, memory, reasoning or efficiency
experiments. The next research milestone remains prospective qualification of
a reliable source-conditioned local-answer baseline on fresh development data.

Validation commands and actual results are retained under
`artifacts/owned-resume-integrity-v1-20261127-001/`; no historical experiment is
retried or relabeled by this engineering work.
