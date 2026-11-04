# Final local accounting

Base HEAD: `091a36b075ae7c81b31954a14409f5402083d5e7`. Initial tree clean; no commit/push/deployment.

New work: NOT_RUN remotely. Base Actions run 41679017878: web success, Python Ruff failure.

Full Python: 183 passed. New focused: nine passed. Source/runtime seals preserved.

| Label | Exit | Seconds | Exact command |
|---|---:|---:|---|
| build | 1 | 2.866 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m build --no-isolation` |
| chat-e2e | 0 | 23.860 | `.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --backbone-dir artifacts/qwen-chat-001/backbone --selector-checkpoint artifacts/chat-selector-v2-20261101/selector.json --output-dir artifacts/recall-v1-20261104/chat-e2e` |
| development | 0 | 198.958 | `.\.venv\Scripts\python.exe scripts/recall_after.py development --run artifacts/recall-v1-20261104` |
| diagnose | 0 | 2.975 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm diagnose` |
| diff-check | 0 | 0.074 | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --check` |
| final-diff | 0 | 0.053 | `git diff --check` |
| final-focused-format | 0 | 0.122 | `.\.venv\Scripts\python.exe -m ruff format --check src/toruk_lm/source_spans.py scripts/recall_study.py scripts/recall_after.py scripts/recall_v2.py scripts/report_recall.py tests/test_source_spans.py tests/test_recall_protocol.py tests/test_recall_templates.py` |
| final-format | 0 | 0.094 | `.\.venv\Scripts\python.exe -m ruff format --check src/toruk_lm/source_spans.py scripts/recall_study.py scripts/recall_after.py scripts/recall_v2.py scripts/report_recall.py tests/test_source_spans.py tests/test_recall_protocol.py tests/test_recall_templates.py tests/test_recall_seals.py` |
| final-lint | 0 | 0.100 | `.\.venv\Scripts\python.exe -m ruff check src/toruk_lm/source_spans.py scripts/recall_study.py scripts/recall_after.py scripts/recall_v2.py scripts/report_recall.py tests/test_source_spans.py tests/test_recall_protocol.py tests/test_recall_templates.py tests/test_recall_seals.py` |
| final-package-build | 0 | 3.753 | `.\.venv\Scripts\python.exe -m build --no-isolation --outdir artifacts/recall-v2-20261104/package` |
| final-pip-check | 0 | 0.606 | `.\.venv\Scripts\python.exe -m pip check` |
| final-recall-tests | 0 | 3.065 | `.\.venv\Scripts\python.exe -m pytest -q tests/test_source_spans.py tests/test_recall_protocol.py tests/test_recall_templates.py tests/test_recall_seals.py -p no:cacheprovider` |
| final-repo-format | 1 | 0.097 | `.\.venv\Scripts\python.exe -m ruff format --check src tests scripts` |
| final-repo-lint | 1 | 0.112 | `.\.venv\Scripts\python.exe -m ruff check .` |
| final-tests | 0 | 153.786 | `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` |
| final-types-linux | 0 | 45.446 | `.\.venv\Scripts\python.exe -m mypy --platform linux` |
| final-types | 1 | 76.243 | `.\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/recall_study.py scripts/recall_after.py scripts/recall_v2.py scripts/report_recall.py` |
| focused-lint | 0 | 0.157 | `.\.venv\Scripts\python.exe -m ruff check src/toruk_lm/source_spans.py scripts/recall_study.py scripts/recall_after.py scripts/report_recall.py tests/test_source_spans.py tests/test_recall_protocol.py` |
| focused | 0 | 4.344 | `.\.venv\Scripts\python.exe -m pytest -q tests/test_source_spans.py tests/test_recall_protocol.py tests/test_chat_foundation.py tests/test_chat_selector.py tests/test_chat_selector_v2.py -p no:cacheprovider` |
| format | 1 | 0.140 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff format --check src tests scripts` |
| freeze | 0 | 3.186 | `.\.venv\Scripts\python.exe scripts/recall_after.py freeze --run artifacts/recall-v1-20261104` |
| fresh-build | 0 | 5.263 | `.\.venv\Scripts\python.exe -m build --no-isolation --outdir artifacts/recall-v1-20261104/package` |
| heldout | 0 | 165.109 | `.\.venv\Scripts\python.exe scripts/recall_after.py heldout --run artifacts/recall-v1-20261104` |
| help | 0 | 2.982 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm --help` |
| import | 0 | 0.053 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -c import toruk_lm; print(toruk_lm.__version__)` |
| install-local | 0 | 4.783 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .` |
| installed-package | 0 | 5.468 | `.\.venv\Scripts\python.exe artifacts/recall-v2-20261104/package_audit.py` |
| lint | 1 | 0.172 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m ruff check .` |
| node-check | 0 | 5.278 | `npm.cmd --prefix web/vercel run check` |
| node-tests-utf8 | 0 | 1.286 | `npm.cmd --prefix web/vercel test` |
| node-tests | 0 | 1.329 | `npm.cmd --prefix web/vercel test` |
| package | 0 | 1.084 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pip check` |
| page-handlers | 0 | 33.333 | `.\.venv\Scripts\python.exe scripts/smoke_qualification_ui.py --output-dir artifacts/recall-v1-20261104/page-handlers` |
| report-v1 | 0 | 10.333 | `.\.venv\Scripts\python.exe scripts/report_recall.py --run artifacts/recall-v1-20261104` |
| report-v2 | 0 | 7.937 | `.\.venv\Scripts\python.exe scripts/report_recall.py --run artifacts/recall-v2-20261104` |
| reproduce | 0 | 4.494 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/foundation.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\recall-v1-20261104\checks\pipeline` |
| research-config | 0 | 2.282 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate-config --config configs/reproduce-smoke-v1.json` |
| research-smoke | 0 | 5.233 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm reproduce --config configs/reproduce-smoke-v1.json --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\recall-v1-20261104\checks\research-smoke` |
| research-types | 0 | 59.756 | `.\.venv\Scripts\python.exe -m mypy --disable-error-code misc --disable-error-code import-untyped src/toruk_lm scripts/recall_study.py scripts/recall_after.py scripts/recall_v2.py scripts/report_recall.py` |
| runtime-types | 0 | 1.568 | `.\.venv\Scripts\python.exe -m mypy` |
| staged-diff-check | 0 | 0.051 | `git -c safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk diff --cached --check` |
| summarize | 0 | 4.169 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm summarize --run C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\recall-v1-20261104\checks\pipeline --output C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\recall-v1-20261104\checks\tables` |
| tests | 0 | 206.314 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m pytest -q` |
| types-linux | 0 | 45.055 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy --platform linux` |
| types | 0 | 83.212 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m mypy` |
| v2-development | 0 | 181.412 | `.\.venv\Scripts\python.exe scripts/recall_v2.py development --run artifacts/recall-v2-20261104` |
| v2-heldout | 0 | 184.549 | `.\.venv\Scripts\python.exe scripts/recall_v2.py heldout --run artifacts/recall-v2-20261104` |
| v2-registration | 0 | 2.980 | `.\.venv\Scripts\python.exe scripts/recall_v2.py register --run artifacts/recall-v2-20261104` |
| validate | 0 | 2.270 | `C:\Users\susee\VS_CODE_PROJECT\Toruk\.venv\Scripts\python.exe -m toruk_lm validate --manifest C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\recall-v1-20261104\checks\pipeline\data\manifest.json --config configs/foundation.json --checkpoint C:\Users\susee\VS_CODE_PROJECT\Toruk\artifacts\recall-v1-20261104\checks\pipeline\train\checkpoint.pt` |

The first Node test wrapper exited 1 while printing Unicode to cp1252 after the child tests exited 0. Its retained child record shows 0; node-tests-utf8 verifies a clean wrapper exit 0. Initial formatter/linter diagnostics were retained in the interactive command transcript; the registered original runner remains byte-sealed.

## Exact Git status

```text
 M README.md
 M docs/architecture.md
 M pyproject.toml
?? artifacts/recall-v1-20261104/before-cost.json
?? artifacts/recall-v1-20261104/before.jsonl
?? artifacts/recall-v1-20261104/chat-e2e/backend-integration.log
?? artifacts/recall-v1-20261104/chat-e2e/results.json
?? artifacts/recall-v1-20261104/chat-e2e/web-integration.log
?? artifacts/recall-v1-20261104/checks/build.json
?? artifacts/recall-v1-20261104/checks/build.log
?? artifacts/recall-v1-20261104/checks/chat-e2e.json
?? artifacts/recall-v1-20261104/checks/chat-e2e.log
?? artifacts/recall-v1-20261104/checks/development.json
?? artifacts/recall-v1-20261104/checks/development.log
?? artifacts/recall-v1-20261104/checks/diagnose.json
?? artifacts/recall-v1-20261104/checks/diagnose.log
?? artifacts/recall-v1-20261104/checks/diff-check.json
?? artifacts/recall-v1-20261104/checks/diff-check.log
?? artifacts/recall-v1-20261104/checks/final-diff.json
?? artifacts/recall-v1-20261104/checks/final-diff.log
?? artifacts/recall-v1-20261104/checks/final-focused-format.json
?? artifacts/recall-v1-20261104/checks/final-focused-format.log
?? artifacts/recall-v1-20261104/checks/final-format.json
?? artifacts/recall-v1-20261104/checks/final-format.log
?? artifacts/recall-v1-20261104/checks/final-lint.json
?? artifacts/recall-v1-20261104/checks/final-lint.log
?? artifacts/recall-v1-20261104/checks/final-package-build.json
?? artifacts/recall-v1-20261104/checks/final-package-build.log
?? artifacts/recall-v1-20261104/checks/final-pip-check.json
?? artifacts/recall-v1-20261104/checks/final-pip-check.log
?? artifacts/recall-v1-20261104/checks/final-recall-tests.json
?? artifacts/recall-v1-20261104/checks/final-recall-tests.log
?? artifacts/recall-v1-20261104/checks/final-repo-format.json
?? artifacts/recall-v1-20261104/checks/final-repo-format.log
?? artifacts/recall-v1-20261104/checks/final-repo-lint.json
?? artifacts/recall-v1-20261104/checks/final-repo-lint.log
?? artifacts/recall-v1-20261104/checks/final-tests.json
?? artifacts/recall-v1-20261104/checks/final-tests.log
?? artifacts/recall-v1-20261104/checks/final-types-linux.json
?? artifacts/recall-v1-20261104/checks/final-types-linux.log
?? artifacts/recall-v1-20261104/checks/final-types.json
?? artifacts/recall-v1-20261104/checks/final-types.log
?? artifacts/recall-v1-20261104/checks/focused-lint.json
?? artifacts/recall-v1-20261104/checks/focused-lint.log
?? artifacts/recall-v1-20261104/checks/focused.json
?? artifacts/recall-v1-20261104/checks/focused.log
?? artifacts/recall-v1-20261104/checks/format.json
?? artifacts/recall-v1-20261104/checks/format.log
?? artifacts/recall-v1-20261104/checks/freeze.json
?? artifacts/recall-v1-20261104/checks/freeze.log
?? artifacts/recall-v1-20261104/checks/fresh-build.json
?? artifacts/recall-v1-20261104/checks/fresh-build.log
?? artifacts/recall-v1-20261104/checks/heldout.json
?? artifacts/recall-v1-20261104/checks/heldout.log
?? artifacts/recall-v1-20261104/checks/help.json
?? artifacts/recall-v1-20261104/checks/help.log
?? artifacts/recall-v1-20261104/checks/import.json
?? artifacts/recall-v1-20261104/checks/import.log
?? artifacts/recall-v1-20261104/checks/install-local.json
?? artifacts/recall-v1-20261104/checks/install-local.log
?? artifacts/recall-v1-20261104/checks/installed-package.json
?? artifacts/recall-v1-20261104/checks/installed-package.log
?? artifacts/recall-v1-20261104/checks/lint.json
?? artifacts/recall-v1-20261104/checks/lint.log
?? artifacts/recall-v1-20261104/checks/node-check.json
?? artifacts/recall-v1-20261104/checks/node-check.log
?? artifacts/recall-v1-20261104/checks/node-tests-utf8.json
?? artifacts/recall-v1-20261104/checks/node-tests-utf8.log
?? artifacts/recall-v1-20261104/checks/node-tests.json
?? artifacts/recall-v1-20261104/checks/node-tests.log
?? artifacts/recall-v1-20261104/checks/package.json
?? artifacts/recall-v1-20261104/checks/package.log
?? artifacts/recall-v1-20261104/checks/page-handlers.json
?? artifacts/recall-v1-20261104/checks/page-handlers.log
?? artifacts/recall-v1-20261104/checks/pipeline/config.json
?? artifacts/recall-v1-20261104/checks/pipeline/data/manifest.json
?? artifacts/recall-v1-20261104/checks/pipeline/data/test.jsonl
?? artifacts/recall-v1-20261104/checks/pipeline/data/train.jsonl
?? artifacts/recall-v1-20261104/checks/pipeline/data/validation.jsonl
?? artifacts/recall-v1-20261104/checks/pipeline/eval/metrics.json
?? artifacts/recall-v1-20261104/checks/pipeline/eval/predictions.json
?? artifacts/recall-v1-20261104/checks/pipeline/generation.json
?? artifacts/recall-v1-20261104/checks/pipeline/manifest.json
?? artifacts/recall-v1-20261104/checks/pipeline/summary/metrics.json
?? artifacts/recall-v1-20261104/checks/pipeline/summary/table.csv
?? artifacts/recall-v1-20261104/checks/pipeline/summary/table.md
?? artifacts/recall-v1-20261104/checks/pipeline/train/config.json
?? artifacts/recall-v1-20261104/checks/pipeline/train/metrics.json
?? artifacts/recall-v1-20261104/checks/report-v1.json
?? artifacts/recall-v1-20261104/checks/report-v1.log
?? artifacts/recall-v1-20261104/checks/report-v2.json
?? artifacts/recall-v1-20261104/checks/report-v2.log
?? artifacts/recall-v1-20261104/checks/reproduce.json
?? artifacts/recall-v1-20261104/checks/reproduce.log
?? artifacts/recall-v1-20261104/checks/research-config.json
?? artifacts/recall-v1-20261104/checks/research-config.log
?? artifacts/recall-v1-20261104/checks/research-smoke.json
?? artifacts/recall-v1-20261104/checks/research-smoke.log
?? artifacts/recall-v1-20261104/checks/research-smoke/config.json
?? artifacts/recall-v1-20261104/checks/research-smoke/data/manifest.json
?? artifacts/recall-v1-20261104/checks/research-smoke/data/test.jsonl
?? artifacts/recall-v1-20261104/checks/research-smoke/data/train.jsonl
?? artifacts/recall-v1-20261104/checks/research-smoke/data/train_lm.jsonl
?? artifacts/recall-v1-20261104/checks/research-smoke/data/validation.jsonl
?? artifacts/recall-v1-20261104/checks/research-smoke/data/validation_lm.jsonl
?? artifacts/recall-v1-20261104/checks/research-smoke/manifest.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-eval/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-eval/predictions.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-full/config.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-full/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-part/config.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-part/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-resume/config.json
?? artifacts/recall-v1-20261104/checks/research-smoke/ordinary-resume/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-eval/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-eval/predictions.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-full/config.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-full/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-part/config.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-part/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-resume/config.json
?? artifacts/recall-v1-20261104/checks/research-smoke/recurrent-resume/metrics.json
?? artifacts/recall-v1-20261104/checks/research-smoke/stages.json
?? artifacts/recall-v1-20261104/checks/research-smoke/summary.json
?? artifacts/recall-v1-20261104/checks/research-types.json
?? artifacts/recall-v1-20261104/checks/research-types.log
?? artifacts/recall-v1-20261104/checks/runtime-types.json
?? artifacts/recall-v1-20261104/checks/runtime-types.log
?? artifacts/recall-v1-20261104/checks/staged-diff-check.json
?? artifacts/recall-v1-20261104/checks/staged-diff-check.log
?? artifacts/recall-v1-20261104/checks/summarize.json
?? artifacts/recall-v1-20261104/checks/summarize.log
?? artifacts/recall-v1-20261104/checks/tables/metrics.json
?? artifacts/recall-v1-20261104/checks/tables/table.csv
?? artifacts/recall-v1-20261104/checks/tables/table.md
?? artifacts/recall-v1-20261104/checks/tests.json
?? artifacts/recall-v1-20261104/checks/tests.log
?? artifacts/recall-v1-20261104/checks/types-linux.json
?? artifacts/recall-v1-20261104/checks/types-linux.log
?? artifacts/recall-v1-20261104/checks/types.json
?? artifacts/recall-v1-20261104/checks/types.log
?? artifacts/recall-v1-20261104/checks/v2-development.json
?? artifacts/recall-v1-20261104/checks/v2-development.log
?? artifacts/recall-v1-20261104/checks/v2-heldout.json
?? artifacts/recall-v1-20261104/checks/v2-heldout.log
?? artifacts/recall-v1-20261104/checks/v2-registration.json
?? artifacts/recall-v1-20261104/checks/v2-registration.log
?? artifacts/recall-v1-20261104/checks/validate.json
?? artifacts/recall-v1-20261104/checks/validate.log
?? artifacts/recall-v1-20261104/commands-interim.json
?? artifacts/recall-v1-20261104/development-cost.json
?? artifacts/recall-v1-20261104/development.json
?? artifacts/recall-v1-20261104/development.jsonl
?? artifacts/recall-v1-20261104/execution-seal.json
?? artifacts/recall-v1-20261104/heldout-cost.json
?? artifacts/recall-v1-20261104/heldout.json
?? artifacts/recall-v1-20261104/heldout.jsonl
?? artifacts/recall-v1-20261104/intervention.json
?? artifacts/recall-v1-20261104/intervention.md
?? artifacts/recall-v1-20261104/package/toruk_lm-0.1.0-py3-none-any.whl
?? artifacts/recall-v1-20261104/package/toruk_lm-0.1.0.tar.gz
?? artifacts/recall-v1-20261104/page-handlers/backend.log
?? artifacts/recall-v1-20261104/page-handlers/page-handlers.log
?? artifacts/recall-v1-20261104/page-handlers/proxy.log
?? artifacts/recall-v1-20261104/registration.json
?? artifacts/recall-v1-20261104/remote-ci.json
?? artifacts/recall-v1-20261104/summary.json
?? artifacts/recall-v1-20261104/table.md
?? artifacts/recall-v1-20261104/training.json
?? artifacts/recall-v1-20261104/work.json
?? artifacts/recall-v2-20261104/assertion-review.json
?? artifacts/recall-v2-20261104/commands.json
?? artifacts/recall-v2-20261104/development-cost.json
?? artifacts/recall-v2-20261104/development.json
?? artifacts/recall-v2-20261104/development.jsonl
?? artifacts/recall-v2-20261104/final-accounting.json
?? artifacts/recall-v2-20261104/final-accounting.md
?? artifacts/recall-v2-20261104/git-status.txt
?? artifacts/recall-v2-20261104/heldout-cost.json
?? artifacts/recall-v2-20261104/heldout.json
?? artifacts/recall-v2-20261104/heldout.jsonl
?? artifacts/recall-v2-20261104/intervention.json
?? artifacts/recall-v2-20261104/outputs-seal.json
?? artifacts/recall-v2-20261104/package-audit.json
?? artifacts/recall-v2-20261104/package/toruk_lm-0.1.0-py3-none-any.whl
?? artifacts/recall-v2-20261104/package/toruk_lm-0.1.0.tar.gz
?? artifacts/recall-v2-20261104/package_audit.py
?? artifacts/recall-v2-20261104/registration.json
?? artifacts/recall-v2-20261104/summary.json
?? artifacts/recall-v2-20261104/table.md
?? artifacts/recall-v2-20261104/training.json
?? artifacts/recall-v2-20261104/versions.json
?? artifacts/recall-v2-20261104/work.json
?? docs/research/recall-results-20261104.md
?? docs/research/recall-v1-protocol.md
?? docs/research/recall-v2-protocol.md
?? docs/toruk-explanation.ipynb
?? scripts/recall_after.py
?? scripts/recall_study.py
?? scripts/recall_v2.py
?? scripts/report_recall.py
?? src/toruk_lm/source_spans.py
?? tests/test_recall_protocol.py
?? tests/test_recall_seals.py
?? tests/test_recall_templates.py
?? tests/test_source_spans.py
```

Private note updated locally (ignored): docs/internal/recall-v1-architecture.md. Generated wheel-install verification workspace was removed after successful audit; package builds and audit evidence remain.

Full argv/source fingerprints are in the per-command JSON files. outputs-seal.json hashes raw datasets, results and cost summaries. No remote success is inferred from local checks.
