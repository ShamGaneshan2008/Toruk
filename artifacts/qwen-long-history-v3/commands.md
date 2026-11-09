# Executed v3 development commands and scope

Root: `C:/Users/susee/VS_CODE_PROJECT/Toruk`. D-drive source, checkpoint and model
inputs stay read-only. Initial HEAD 25d4ec09; external advancement to 3e996267 is
recorded separately. The assistant issued no commit, push, reset, checkout or
deployment command.

Before any candidate answer, static contracts, gate/package types, v2 sealed
hashes and per-case development diagnosis were checked. Early lint/type failures
were fixed before registration and retained in checks/. No scientific source
was changed after candidate inference began.

Executed once each (exact wrapped commands, sources, durations and logs in checks/):

```powershell
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v3.py prepare --run artifacts/qwen-long-history-v3/attempt-001
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v3.py development --run artifacts/qwen-long-history-v3/attempt-001
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/report_qwen_long_history_v3.py --run artifacts/qwen-long-history-v3/attempt-001
```

The development controller creates three separate fresh workers: BEFORE, LEXICAL,
AFTER. Each performs seven original development cases plus first-case replay,
24 Qwen generations in total. Selection traces are written for all three arms.
There is no held-out command, copied held-out case file, model retry, second gate
variant or new training. Output creation is exclusive; do not repeat against
these paths. Only the offline report tokenizes saved prompts and decodes saved
output IDs; it never calls generation.

Workers use the pinned D-drive runtime. The new gate is loaded by its registered
absolute file path; D-drive module classes are adapted only inside each new
worker process. Production defaults and old source files are not edited.
The shim in worker-source/scripts/qwen_long_history.py preserves the old worker
interface so the exact v2 monitoring code can supervise the new development run.

General C-drive checks are separate from timed Qwen comparison:

```powershell
./.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/test_qwen_long_history_v3.py tests/test_qwen_long_history_v2.py
./.venv/Scripts/python.exe -B -m ruff check .
./.venv/Scripts/python.exe -B -m ruff format --check src tests scripts
./.venv/Scripts/python.exe -B -m mypy src/toruk_lm scripts/qwen_long_history_v3.py
./.venv/Scripts/python.exe -B -X utf8 artifacts/qwen-long-history-v3/verify_with_power.py
git diff --check
```

The wrapper holds/restores a process-scoped system-required request and runs
scripts/verify.py with prefix qwen-v3 and fresh verification/ output. Its tiny
existing owned/foundation/research fixture training is engineering validation,
not v3 selector/Qwen training or Qwen held-out inference. This C-drive check
runtime is distinct from the pinned D-drive model runtime. No hosted CI was
launched. The report uses frozen scores and reports the new PLAIN regression;
no post-output scoring, prompt, gating or cap change followed it.
