# Executed v2 preparation, development rehearsal and offline verification

Working directory and Git root: `C:/Users/susee/VS_CODE_PROJECT/Toruk`.
Read-only scientific inputs and pinned worker runtime: `D:/Toruk`.
Starting commit in both checkouts: `25d4ec09e01397b43b9b16ad08faeca7cdb22eb0`.
D-drive uncommitted files were not imported over C-drive files or edited.

The new controller has only `prepare`, `rehearse`, and `freeze-proposal` actions.
There is no authorized held-out invocation in this record.

Actual candidate sequence, run through `scripts/check.py` wrappers in `checks/`:

```powershell
# attempt-001: inventory preflight failed on an unreadable old package archive.
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v2.py prepare --run artifacts/qwen-long-history-v2/attempt-001
# attempt-002: registration succeeded; controller clock preflight failed BEFORE any worker.
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v2.py prepare --run artifacts/qwen-long-history-v2/attempt-002
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v2.py rehearse --run artifacts/qwen-long-history-v2/attempt-002
# attempt-003: corrected preflight, then exactly one development pass per arm plus replay.
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v2.py prepare --run artifacts/qwen-long-history-v2/attempt-003
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v2.py rehearse --run artifacts/qwen-long-history-v2/attempt-003
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 scripts/qwen_long_history_v2.py freeze-proposal --run artifacts/qwen-long-history-v2/attempt-003
# Offline: reconstruct/tokenize saved development prompts, decode stored IDs and recheck scores.
D:/Toruk/.venv/Scripts/python.exe -B -X utf8 artifacts/qwen-long-history-v2/audit_rehearsal.py
```

Do not repeat these commands against the existing paths. Exclusive output guards
reject overwrites. The two preflight failures and amendments are preserved; neither
launched a model worker or generated a held-out answer. No candidate retry followed
the successful four-arm rehearsal. No old v1 question was rerun as v1: the v2
development data is explicitly declared carryover for a separate timing rehearsal.

New-controller checks (exact arguments, source hashes, logs and durations in checks/):

```powershell
./.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/test_qwen_long_history_v2.py
./.venv/Scripts/python.exe -B -m ruff check scripts/qwen_long_history_v2.py tests/test_qwen_long_history_v2.py
./.venv/Scripts/python.exe -B -m ruff format --check scripts/qwen_long_history_v2.py tests/test_qwen_long_history_v2.py
./.venv/Scripts/python.exe -B -m mypy --follow-imports=silent scripts/qwen_long_history_v2.py
./.venv/Scripts/python.exe -B -X utf8 scripts/verify.py --prefix qwen-v2 --output-dir artifacts/qwen-long-history-v2/verification
```

The C-drive general verifier uses its existing Torch 2.14.1 / Transformers 5.20.2
environment. The actual Qwen workers and offline tokenizer audit use the frozen
D-drive Torch 2.15.0 / Transformers 5.22.2 environment. Do not conflate them.
General verification includes existing tiny fixture training, not new selector or
Qwen training and not access to this comparison's held-out set. Its costs and
outputs are separate from the arm ledger. No hosted CI was launched.

The proposal digest is
`84f23a07cd78935536b4586885bfb9d20bc78ae7d964a6a2d1ffffc8ccc4fec7`.
It binds original inputs and completed rehearsal outputs and explicitly records
held-out execution as unauthorized with zero completed cases. Later offline audit,
engineering checks and reports are supplemental evidence, not changes to that seal.
