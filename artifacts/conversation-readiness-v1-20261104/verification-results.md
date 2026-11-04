# Local conversational-readiness verification

Repository verification: 23/23 commands PASS. Python: 222 passed in 142.25 s. Node: 13 passed, 1 existing live-browser skip.
Final Ruff checks: 124 files formatted. Mypy: 34 runtime files; final runtime/driver check: 37 files. Hosted CI: NOT OBSERVED.
The first build ran before the report was created and warned that its documentation glob was empty. The final package rebuild contains the report, data module and report script; membership verified.
Conversational pilot: NOT_RUN; training readiness: BLOCKED; product integration: BLOCKED. These research gates are separate from successful check execution.
Initial development Ruff line-length complaints were corrected before final checks.

| Check | Status | Seconds | Exact command |
|---|---|---:|---|
| verification/build | PASS | 4.360 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m build --no-isolation --outdir C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\package` |
| verification/conversation-data | PASS | 2.235 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/conversation_readiness.py validate --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\conversation-data` |
| verification/diagnose | PASS | 2.298 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm diagnose` |
| verification/diff-check | PASS | 0.059 | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --check` |
| verification/format | PASS | 0.098 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff format --check src tests scripts` |
| verification/frozen-sources | PASS | 0.079 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/check_frozen_sources.py` |
| verification/help | PASS | 2.305 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm --help` |
| verification/import | PASS | 0.042 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -c "import toruk_lm; print(toruk_lm.__version__)"` |
| verification/independent-cases | PASS | 2.441 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/independent_replication.py validate-cases --run C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\independent-cases` |
| verification/install-local | PASS | 2.871 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .` |
| verification/lint | PASS | 0.107 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff check .` |
| verification/owned-lm-generate | PASS | 3.809 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm.owned_lm generate --checkpoint C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\owned-lm-smoke\models\23-memory_on\checkpoint.pt --prompt "Experimental CPU smoke" --max-new-tokens 4` |
| verification/owned-lm-smoke | PASS | 5.560 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/study_owned_lm.py --config configs/owned-lm-smoke-v1.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\owned-lm-smoke` |
| verification/package | PASS | 0.644 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip check` |
| verification/reproduce | PASS | 4.063 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/foundation.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\pipeline` |
| verification/research-config | PASS | 2.215 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate-config --config configs/reproduce-smoke-v1.json` |
| verification/research-smoke | PASS | 4.861 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\research-smoke` |
| verification/staged-diff-check | PASS | 0.047 | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --cached --check` |
| verification/summarize | PASS | 3.976 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm summarize --run C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\pipeline --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\tables` |
| verification/tests | PASS | 143.539 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pytest -q` |
| verification/types-linux | PASS | 46.317 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy --platform linux` |
| verification/types | PASS | 1.715 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy` |
| verification/validate | PASS | 2.365 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate --manifest C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\pipeline\data\manifest.json --config configs/foundation.json --checkpoint C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\conversation-readiness-v1-20261104\verification\pipeline\train\checkpoint.pt` |
| checks/diagnostics | PASS | 55.330 | `.\.venv\Scripts\python.exe scripts/conversation_readiness.py evaluate --output artifacts/conversation-readiness-v1-20261104/registered --backbone-dir artifacts/qwen-chat-001/backbone` |
| checks/final-format | PASS | 0.101 | `.\.venv\Scripts\python.exe -m ruff format --check src tests scripts` |
| checks/final-lint | PASS | 0.100 | `.\.venv\Scripts\python.exe -m ruff check .` |
| checks/final-package | PASS | 4.263 | `.\.venv\Scripts\python.exe -m build --no-isolation --outdir artifacts/conversation-readiness-v1-20261104/verification/package/final` |
| checks/final-types | PASS | 1.623 | `.\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/conversation_readiness.py scripts/replay_owned_readiness.py scripts/report_conversation_readiness.py` |
| checks/node-check | PASS | 1.009 | `npm.cmd --prefix web/vercel run check` |
| checks/node-tests | PASS | 0.986 | `npm.cmd --prefix web/vercel test` |
| checks/prepare | PASS | 4.242 | `.\.venv\Scripts\python.exe scripts/conversation_readiness.py prepare --output artifacts/conversation-readiness-v1-20261104/registered` |
| checks/prerequisite-replay | PASS | 17.213 | `.\.venv\Scripts\python.exe scripts/replay_owned_readiness.py --reference artifacts/owned-lm-v1-20261104/primary --output artifacts/conversation-readiness-v1-20261104/replay` |

Final git diff --check: PASS.
