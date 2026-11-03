# Exact audit commands and results

The intentional alias rejection exits 1; it is a successful negative test, not an unexpected inference failure. Docker and host-package prerequisites are blocked. Source identities and full logs are in adjacent JSON records.

| Check | Exit | Interpretation | Exact argv |
|---|---:|---|---|
| alias-rejection-expected | 1 | EXPECTED REJECTION; exit 1 required | `[".\\.venv\\Scripts\\python.exe", "scripts/replay_routing_v2.py", "--sealed-run", "artifacts/routing-v2-20261103", "--inputs", "artifacts/current-state-audit-20261103/alias-binding-probe", "--output", "artifacts/current-state-audit-20261103/should-not-generate.json"]` |
| build | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "artifacts/current-state-audit-20261103/package"]` |
| chat-baseline-and-selector | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_chat_foundation.py", "--backbone-dir", "artifacts/qwen-chat-001/backbone", "--selector-checkpoint", "artifacts/chat-selector-v2-20261101/selector.json", "--output-dir", "artifacts/current-state-audit-20261103/chat-paired"]` |
| cli-diagnose | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "diagnose"]` |
| cli-help | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "--help"]` |
| controlled-cli-smoke | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/reproduce-smoke-v1.json", "--output", "artifacts/current-state-audit-20261103/controlled-smoke"]` |
| diff-check | 0 | PASS | `["git", "diff", "--check"]` |
| docker-engine | 1 | BLOCKED prerequisite | `["docker", "version", "--format", "{{json .Server}}"]` |
| final-format | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "scripts/replay_routing_v2.py", "scripts/replay_refusal_diagnostic.py", "tests/test_sealed_replay.py"]` |
| final-lint | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "scripts/replay_routing_v2.py", "scripts/replay_refusal_diagnostic.py", "tests/test_sealed_replay.py"]` |
| focused-format | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "scripts/replay_routing_v2.py", "scripts/replay_refusal_diagnostic.py", "tests/test_sealed_replay.py"]` |
| focused-lint | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "scripts/replay_routing_v2.py", "scripts/replay_refusal_diagnostic.py", "tests/test_sealed_replay.py"]` |
| focused-tests-final | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q", "tests/test_sealed_replay.py", "-p", "no:cacheprovider"]` |
| frozen-package-scoring | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "scripts/audit_routing_v2.py", "--run", "artifacts/routing-v2-20261103", "--manifest"]` |
| host-package-prerequisite | 2 | BLOCKED prerequisite | `[".\\.venv\\Scripts\\python.exe", "scripts/prepare_inference_package.py", "--output", "artifacts/current-state-audit-20261103/host-package", "--selector", "artifacts/m6-validation-001/recurrent/checkpoint.pt"]` |
| node-check | 0 | PASS | `["npm.cmd", "--prefix", "web/vercel", "run", "check"]` |
| node-tests | 0 | PASS | `["npm.cmd", "--prefix", "web/vercel", "test"]` |
| ordinary-generate | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "generate", "--checkpoint", "artifacts/foundation-001/train/checkpoint.pt", "--prompt", "A small research model", "--max-new-tokens", "12"]` |
| page-handlers | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_qualification_ui.py", "--output-dir", "artifacts/current-state-audit-20261103/page-handlers"]` |
| primary-result-replay | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "scripts/replay_routing_v2.py", "--sealed-run", "artifacts/routing-v2-20261103", "--loads", "0", "--output", "artifacts/current-state-audit-20261103/primary-replay.json"]` |
| python-tests | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q", "-p", "no:cacheprovider"]` |
| refusal-replay | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "scripts/replay_refusal_diagnostic.py", "--reference", "artifacts/chat-repetition-exact-20261101/full-history-matched.json", "--backbone-dir", "artifacts/chat-foundation-001/backbone", "--output", "artifacts/current-state-audit-20261103/refusal-replay.json"]` |
| replay-help | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "scripts/replay_routing_v2.py", "--help"]` |
| replay-types | 1 | Retained initial failure; superseded by passing combined check | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy", "--follow-imports", "silent", "scripts/replay_routing_v2.py", "scripts/replay_refusal_diagnostic.py"]` |
| repository-format | 1 | Known frozen-script failures retained | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]` |
| repository-lint | 1 | Known frozen-script failures retained | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", ".", "--output-format", "concise"]` |
| types-linux-with-replay | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy", "--platform", "linux", "--follow-imports", "silent", "src/toruk_lm", "scripts/replay_routing_v2.py", "scripts/replay_refusal_diagnostic.py"]` |
| types-with-replay | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy", "--follow-imports", "silent", "src/toruk_lm", "scripts/replay_routing_v2.py", "scripts/replay_refusal_diagnostic.py"]` |
| types | 0 | PASS | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy"]` |
