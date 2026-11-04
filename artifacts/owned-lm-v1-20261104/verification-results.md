# Local verification results

All 22 repository verification commands passed; hosted CI NOT OBSERVED.

| Check | Status | Seconds | Exact command |
|---|---|---:|---|
| verification/build | PASS | 4.255 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m build --no-isolation --outdir C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\package` |
| verification/diagnose | PASS | 2.170 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm diagnose` |
| verification/diff-check | PASS | 0.069 | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --check` |
| verification/format | PASS | 0.095 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff format --check src tests scripts` |
| verification/frozen-sources | PASS | 0.071 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/check_frozen_sources.py` |
| verification/help | PASS | 2.167 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm --help` |
| verification/import | PASS | 0.040 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -c "import toruk_lm; print(toruk_lm.__version__)"` |
| verification/independent-cases | PASS | 2.187 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/independent_replication.py validate-cases --run C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\independent-cases` |
| verification/install-local | PASS | 2.817 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .` |
| verification/lint | PASS | 0.097 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff check .` |
| verification/owned-lm-generate | PASS | 3.750 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm.owned_lm generate --checkpoint C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\owned-lm-smoke\models\23-memory_on\checkpoint.pt --prompt "Experimental CPU smoke" --max-new-tokens 4` |
| verification/owned-lm-smoke | PASS | 5.168 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/study_owned_lm.py --config configs/owned-lm-smoke-v1.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\owned-lm-smoke` |
| verification/package | PASS | 0.623 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip check` |
| verification/reproduce | PASS | 4.065 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/foundation.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\pipeline` |
| verification/research-config | PASS | 2.142 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate-config --config configs/reproduce-smoke-v1.json` |
| verification/research-smoke | PASS | 5.018 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\research-smoke` |
| verification/staged-diff-check | PASS | 0.033 | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --cached --check` |
| verification/summarize | PASS | 3.860 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm summarize --run C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\pipeline --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\tables` |
| verification/tests | PASS | 138.546 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pytest -q` |
| verification/types-linux | PASS | 46.868 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy --platform linux` |
| verification/types | PASS | 1.641 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy` |
| verification/validate | PASS | 2.178 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate --manifest C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\pipeline\data\manifest.json --config configs/foundation.json --checkpoint C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\owned-lm-v1-20261104\verification\pipeline\train\checkpoint.pt` |
| checks/chat-audit | PASS | 8.819 | `.\.venv\Scripts\python.exe scripts/independent_replication.py audit --run artifacts/owned-lm-v1-20261104/chat-replay` |
| checks/chat-controlled | PASS | 282.848 | `.\.venv\Scripts\python.exe scripts/independent_replication.py evaluate --run artifacts/owned-lm-v1-20261104/chat-replay --suite controlled` |
| checks/chat-independent | PASS | 519.067 | `.\.venv\Scripts\python.exe scripts/independent_replication.py evaluate --run artifacts/owned-lm-v1-20261104/chat-replay --suite independent` |
| checks/chat-register | PASS | 4.794 | `.\.venv\Scripts\python.exe scripts/independent_replication.py register --run artifacts/owned-lm-v1-20261104/chat-replay --phase1 artifacts/independent-replication-20261104/phase1` |
| checks/initial-routing-replay | FAIL | 2.081 | `.\.venv\Scripts\python.exe scripts/replay_routing_v2.py --sealed-run artifacts/routing-v2-20261103 --output artifacts/owned-lm-v1-20261104/initial-routing.json --loads 0` |
| checks/initial-value-audit | FAIL | 2.101 | `.\.venv\Scripts\python.exe scripts/audit_value_fidelity_dev.py --run artifacts/value-fidelity-dev-v1-20261103` |
| checks/node-check-cmd | PASS | 0.990 | `npm.cmd --prefix web/vercel run check` |
| checks/node-check | FAIL | 0.008 | `npm --prefix web/vercel run check` |
| checks/node-tests-cmd | PASS | 0.939 | `npm.cmd --prefix web/vercel test` |
| checks/node-tests | FAIL | 0.006 | `npm --prefix web/vercel test` |
| checks/owned-audit | PASS | 2.388 | `.\.venv\Scripts\python.exe scripts/audit_owned_lm.py --run artifacts/owned-lm-v1-20261104/primary --chat-reference artifacts/independent-replication-20261104/evaluation --chat-replay artifacts/owned-lm-v1-20261104/chat-replay` |
| checks/owned-cli-evaluate | PASS | 4.259 | `.\.venv\Scripts\python.exe -m toruk_lm.owned_lm evaluate --checkpoint artifacts/owned-lm-v1-20261104/cli/resumed.pt --data artifacts/owned-lm-v1-20261104/primary/data/dev.json --split dev --output artifacts/owned-lm-v1-20261104/cli/dev.json --max-new-tokens 4` |
| checks/owned-cli-resume | PASS | 4.001 | `.\.venv\Scripts\python.exe -m toruk_lm.owned_lm train --checkpoint artifacts/owned-lm-v1-20261104/cli/resumed.pt --config configs/owned-lm-smoke-v1.json --data artifacts/owned-lm-v1-20261104/primary/data/train.json --steps 2 --resume artifacts/owned-lm-v1-20261104/cli/first.pt` |
| checks/owned-cli-train | PASS | 3.917 | `.\.venv\Scripts\python.exe -m toruk_lm.owned_lm train --checkpoint artifacts/owned-lm-v1-20261104/cli/first.pt --config configs/owned-lm-smoke-v1.json --data artifacts/owned-lm-v1-20261104/primary/data/train.json --steps 1` |
| checks/owned-primary | PASS | 82.750 | `.\.venv\Scripts\python.exe scripts/study_owned_lm.py --config configs/owned-lm-primary-v1.json --output artifacts/owned-lm-v1-20261104/primary` |
| checks/owned-smoke-development | PASS | 6.299 | `.\.venv\Scripts\python.exe scripts/study_owned_lm.py --config configs/owned-lm-smoke-v1.json --output artifacts/owned-lm-v1-20261104/smoke` |
| checks/restored-owned-replay | PASS | 44.753 | `.\.venv\Scripts\python.exe scripts/replay_owned_prerequisites.py --output artifacts/owned-lm-v1-20261104/prerequisite-replay` |

Python: 215 passed in 137.26 s. Node: 13 passed, 1 existing skip.
Ruff: 119 Python files formatted; mypy: 33 runtime files, plus a separate 36-file runtime/driver check.
The initial historical audits failed strictly on archived pyproject.toml identity. The isolated restoration passed.
Initial npm wrapper commands failed with WinError 2; npm.cmd reruns passed.
Development lint/import-path issues were corrected before final verification.
Owned-LM quality gates failed as reported; successful command execution is not a quality pass.
The primary study and held-out answers were not rerun after inspecting their results.

Final owned-driver-types: **PASS**, 47.763 s.
`.\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/study_owned_lm.py scripts/audit_owned_lm.py scripts/report_owned_lm.py`

Final owned-final-audit: **PASS**, 2.331 s.
`.\.venv\Scripts\python.exe scripts/audit_owned_lm.py --run artifacts/owned-lm-v1-20261104/primary --chat-reference artifacts/independent-replication-20261104/evaluation --chat-replay artifacts/owned-lm-v1-20261104/chat-replay`

Final final-diff-check: **PASS**, 0.070 s.
`git diff --check`
