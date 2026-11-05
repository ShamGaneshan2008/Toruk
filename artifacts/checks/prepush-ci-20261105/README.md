# Pre-push CI integration check - 5 November 2026

PASS locally. No source edits, commit or push in this check.

- CI=true focused Python tests: 26 passed, zero skipped; includes actual page handlers to Node proxy to Python HTTP fixture.
- Node tests: 18 passed, one standalone live test skipped; that live path is exercised by the passing Python integration fixture.
- Node syntax check and git diff --check: PASS.
- Current source identity matches the prior complete 23-stage verification: 232 Python tests plus lint, formatting, types, package and CLI/reproduction checks.
- Local runtime: Windows, Python 3.12.14, Node 24.15.0. Workflow targets Ubuntu, Python 3.12, Node 22; a hosted run for these uncommitted changes has not been observed.
- The workflow installs Node in the Python job; the integration test fails rather than skips when CI=true and Node is missing.
- tests/test_web_integration.py is currently untracked and must be included together with the workflow changes.

See the adjacent JSON records for exact commands and source identities, and the log files for raw results.
