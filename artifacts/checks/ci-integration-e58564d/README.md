# CI and integration check: e58564d

Starting commit: e58564dc1a4f75ad7b9b8e425b35fc20c3a9d751. Starting working tree: clean. No source or workflow edits.

Hosted CPU foundation run #22: SUCCESS for this exact commit; Python check and web jobs both succeeded.
[Observed hosted run](https://github.com/ShamGaneshan2008/Toruk/actions/runs/41872392347). Job/step evidence: hosted.json.

Local scripts/verify.py: 23/23 PASS. Python: 222 passed in 148.68 seconds.
Default Node suite: 13 passed / 1 skipped. Local live-stack run: 14 passed / 0 skipped.
Live coverage: actual page handlers in a DOM harness, real Node HTTP proxy, real Python inference worker and pinned local external Qwen backbone. BASELINE and TORUK lexical-v2 paths; nine inference requests. Interactive browser automation was not run.
All temporary localhost service processes were stopped in the test runner finally block. No training, deploy, commit, push or workflow dispatch was performed, except the bounded existing model-training smoke checks explicitly included in verify.py.

Coverage gap: hosted workflow does not start the live stack or set TORUK_LIVE_WEB_URL, so its live integration test is skipped. Local live success does not mean CI exercises that path. The workflow has test/build jobs, with no deployment step.

| Local check | Status | Exact command |
|---|---|---|
| [build](build.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m build --no-isolation --outdir C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\package` |
| [conversation-data](conversation-data.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/conversation_readiness.py validate --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\conversation-data` |
| [diagnose](diagnose.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm diagnose` |
| [diff-check](diff-check.log) | PASS | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --check` |
| [format](format.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff format --check src tests scripts` |
| [frozen-sources](frozen-sources.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/check_frozen_sources.py` |
| [help](help.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm --help` |
| [import](import.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -c "import toruk_lm; print(toruk_lm.__version__)"` |
| [independent-cases](independent-cases.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/independent_replication.py validate-cases --run C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\independent-cases` |
| [install-local](install-local.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .` |
| [lint](lint.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff check .` |
| [live-integration](live-integration.log) | PASS | `.\.venv\Scripts\python.exe artifacts/checks/ci-integration-e58564d/run_live.py` |
| [node-check](node-check.log) | PASS | `npm.cmd --prefix web/vercel run check` |
| [node-tests](node-tests.log) | PASS | `npm.cmd --prefix web/vercel test` |
| [owned-lm-generate](owned-lm-generate.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm.owned_lm generate --checkpoint C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\owned-lm-smoke\models\23-memory_on\checkpoint.pt --prompt "Experimental CPU smoke" --max-new-tokens 4` |
| [owned-lm-smoke](owned-lm-smoke.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe scripts/study_owned_lm.py --config configs/owned-lm-smoke-v1.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\owned-lm-smoke` |
| [package](package.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip check` |
| [reproduce](reproduce.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/foundation.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\pipeline` |
| [research-config](research-config.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate-config --config configs/reproduce-smoke-v1.json` |
| [research-smoke](research-smoke.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\research-smoke` |
| [staged-diff-check](staged-diff-check.log) | PASS | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --cached --check` |
| [summarize](summarize.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm summarize --run C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\pipeline --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\tables` |
| [tests](tests.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pytest -q` |
| [types-linux](types-linux.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy --platform linux` |
| [types](types.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy` |
| [validate](validate.log) | PASS | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate --manifest C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\pipeline\data\manifest.json --config configs/foundation.json --checkpoint C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\checks\ci-integration-e58564d\pipeline\train\checkpoint.pt` |
