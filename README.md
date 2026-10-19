# Toruk-LM

`toruk_lm` is the Python package for the Toruk-LM research model family.
This working tree implements the **ordinary causal LM foundation**. M2's
controlled-world benchmark and M3's recurrent memory are **not implemented**.
The initial repository contained only a PyCharm starter, so the requested M3
work stopped at its earliest unmet dependency, as required by the task.

Implemented: byte tokenizer, causal decoder, shifted/masked next-token loss,
deterministic CPU training, checkpoint reload/resume, local-context greedy
generation, text-loss evaluation, raw continuations, and a real CLI pipeline.
No effect predictor or protected revisions exist.

## Install and verify

Python 3.11+ is required. On Windows use `.venv\Scripts\python.exe` after creating
the environment; on Unix use `.venv/bin/python`. The commands below use `python`
from that environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[dev]'
python -m pip check
python -m toruk_lm --help
python -m toruk_lm diagnose
python -m ruff check .
python -m ruff format --check src tests scripts
python -m mypy
python -m pytest -q
python -m build --no-isolation
```

`python scripts/verify.py` runs these local CI equivalents with a 120-second
timeout per command and retains command/revision/output records in `artifacts/checks`.

`toruk` and `python -m toruk_lm` are equivalent entry points. Torch may warn about
optional NumPy being absent; this implementation does not require NumPy.

## Reproduce the bounded foundation experiment

Use fresh output directories; commands reject overwriting dataset/training runs.
The retained run is `artifacts/foundation-001`; use `artifacts/reproduction` here.
This is an ordinary-text smoke experiment, not a recurrent-memory comparison.

```powershell
python -m toruk_lm make-fixture --output artifacts/reproduction/data --documents 60 --seed 17
python -m toruk_lm train --train artifacts/reproduction/data/train.jsonl --validation artifacts/reproduction/data/validation.jsonl --output artifacts/reproduction/profile --steps 2
python -m toruk_lm train --train artifacts/reproduction/data/train.jsonl --validation artifacts/reproduction/data/validation.jsonl --output artifacts/reproduction/train --steps 80
python -m toruk_lm evaluate --checkpoint artifacts/reproduction/train/checkpoint.pt --data artifacts/reproduction/data/validation.jsonl --output artifacts/reproduction/eval --max-new-tokens 32
python -m toruk_lm generate --checkpoint artifacts/reproduction/train/checkpoint.pt --prompt 'Field journal 0011. The fox lives near the' --max-new-tokens 32
```

Cap: two profiling steps followed by 80 training steps, batch size 4, context 64,
width 32, two layers, four heads, float32, one CPU thread. Each recorded command
uses a 120-second subprocess timeout via `scripts/check.py`; no unattended job.
The two-step profile precedes budget selection. Fixed AdamW learning rate 0.003,
training seed 23, fixture seed 17. The fixture has 48 train, 6 validation and 6
test documents. The pilot never evaluates the final test split.

For exact same-runtime CPU resume, train to a smaller absolute step total, then:

```powershell
python -m toruk_lm train --train artifacts/reproduction/data/train.jsonl --validation artifacts/reproduction/data/validation.jsonl --output artifacts/reproduction/resumed --steps 100 --resume artifacts/reproduction/train/checkpoint.pt
```

Keep all model/training flags identical to the saved run. Checkpoints support
completed optimizer-step boundaries of independent ordinary-LM windows. The
`--steps` value is the new absolute total. Changed data/configuration/tokenizer
and unsupported formats are rejected. Recurrent mid-document resume and
cross-process inference sessions do not exist.

See [architecture](docs/architecture.md), [proposed memory contract](docs/research/m3-memory-contract.md),
[milestone status](docs/milestones.md), and [experiment registry](docs/experiments.md)
for measured results, limitations, check evidence, and remaining dependencies.
