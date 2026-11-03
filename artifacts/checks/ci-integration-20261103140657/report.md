# CI integration test ? 3 November 2026

Overall: FAIL. GitHub Actions triggers and runs, but its tested committed source fails. Current local changes remain uncommitted and NOT_RUN remotely.

Remote run: https://github.com/ShamGaneshan2008/Toruk/actions/runs/41472041835

Commit: 9163780930ea91c09d596e3e6284dc9e96f67109. Both remote jobs failed. Web syntax fails on committed merge markers in web/vercel/lib/proxy.js:83; Python Ruff reports 527 errors including merge-marker parser errors. Subsequent remote tests, types and build were skipped.

The current working tree has no conflict markers in runtime/tests/scripts/web; local syntax repair predates this test. No source or workflow files were edited by this test.

Local Python: 160 tests pass; both mypy targets pass on 28 source files; CLI/dependencies/reproduction/resume checks pass. Node: syntax passes; 13 tests pass and one optional live-handler test is skipped.

Local verification runner exits 1: repository Ruff has 49 findings in three frozen selector scripts, format reports the same three files, and the default build cannot replace an existing dist archive (WinError 5). Building into a fresh directory passes; the original failure is retained.

Local runtime is Python 3.12.14 / Node 24.15.0 on Windows. Remote workflow uses Python 3.12 / Node 22 on Linux; local results are not an exact Linux/Node-22 runner reproduction.

No deployment job is defined in .github/workflows/ci.yml. Deployment integration was not tested. No workflow was dispatched, commit created, push made or deployment performed.

## Exact checks

| Check | Exit | Command (argv JSON) |
|---|---:|---|
| build-fresh | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "artifacts/checks/ci-integration-20261103140657/package"]` |
| build | 1 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation"]` |
| diagnose | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "diagnose"]` |
| diff-check | 0 | `["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--check"]` |
| format | 1 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]` |
| help | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "--help"]` |
| import | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-c", "import toruk_lm; print(toruk_lm.__version__)"]` |
| install-local | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."]` |
| lint | 1 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "."]` |
| node-check | 0 | `["npm.cmd", "--prefix", "web/vercel", "run", "check"]` |
| node-tests | 0 | `["npm.cmd", "--prefix", "web/vercel", "test"]` |
| package | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "check"]` |
| reproduce | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/foundation.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\checks\\ci-integration-20261103140657\\pipeline"]` |
| research-config | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate-config", "--config", "configs/reproduce-smoke-v1.json"]` |
| research-smoke | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/reproduce-smoke-v1.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\checks\\ci-integration-20261103140657\\research-smoke"]` |
| staged-diff-check | 0 | `["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--cached", "--check"]` |
| summarize | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "summarize", "--run", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\checks\\ci-integration-20261103140657\\pipeline", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\checks\\ci-integration-20261103140657\\tables"]` |
| tests | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q"]` |
| types-linux | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy", "--platform", "linux"]` |
| types | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy"]` |
| validate | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate", "--manifest", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\checks\\ci-integration-20261103140657\\pipeline\\data\\manifest.json", "--config", "configs/foundation.json", "--checkpoint", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\checks\\ci-integration-20261103140657\\pipeline\\train\\checkpoint.pt"]` |

Source identities, timings and full logs accompany each JSON record. remote-ci.json preserves exact remote job/step statuses.
