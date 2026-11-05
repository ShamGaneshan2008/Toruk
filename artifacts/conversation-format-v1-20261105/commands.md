# Exact executed command argument arrays

The JSON arrays below preserve arguments without shell re-escaping. Each evidence record also has timestamps, source hashes and exits.

Top-level complete verification commands:

.venv\Scripts\python.exe scripts/verify.py --output-dir artifacts\conversation-format-v1-20261105\verification
.venv\Scripts\python.exe scripts/verify.py --output-dir artifacts\conversation-format-v1-20261105\verification-final

checks/bounded-training

[".\\.venv\\Scripts\\python.exe", "scripts/conversation_format_study.py", "train"]

checks/chat-integration

[".\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q", "tests/test_chat.py", "tests/test_inference_server.py", "tests/test_web_integration.py", "tests/test_conversation_data.py", "tests/test_owned_lm.py", "tests/test_conversation_format_study.py"]

checks/controlled-cli-recheck

[".\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q", "tests/test_comparisons.py::test_tiny_real_cli_comparison_pipeline_and_generated_outputs", "--showlocals"]

checks/diagnostic-equality

[".\\.venv\\Scripts\\python.exe", "-c", "import json; from pathlib import Path; from toruk_lm.owned_training import write_json; root=Path('artifacts/conversation-format-v1-20261105'); a=json.loads(Path('artifacts/conversation-readiness-v1-20261104/registered/diagnostics.json').read_text(encoding='utf-8')); b=json.loads((root/'reproduced/diagnostics.json').read_text(encoding='utf-8')); keys=('case','origin','model_id','raw_answer','scores'); equal=[[r[k] for k in keys] for r in a['rows']]==[[r[k] for k in keys] for r in b['rows']]; assert equal; write_json(root/'diagnostic-equality.json',dict(status='PASS',answers=50,fields=keys)); print('PASS: 50/50 readiness answers, identities and scores reproduced')"]

checks/diagnostic-replay

[".\\.venv\\Scripts\\python.exe", "scripts/conversation_readiness.py", "evaluate", "--output", "artifacts/conversation-format-v1-20261105/reproduced", "--backbone-dir", "artifacts/qwen-chat-001/backbone"]

checks/environment

[".\\.venv\\Scripts\\python.exe", "-c", "import json,platform,torch; print(json.dumps(dict(platform=platform.platform(),processor=platform.processor(),python=platform.python_version(),torch=torch.__version__)))"]

checks/final-diff

["git", "diff", "--check"]

checks/final-format

[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]

checks/final-integration

[".\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q", "tests/test_inference_server.py", "tests/test_web_integration.py", "tests/test_conversation_format_study.py"]

checks/final-lint

[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "."]

checks/frozen-evaluation

[".\\.venv\\Scripts\\python.exe", "scripts/conversation_format_study.py", "evaluate"]

checks/historical-replay

[".\\.venv\\Scripts\\python.exe", "scripts/replay_owned_readiness.py", "--reference", "artifacts/owned-lm-v1-20261104/primary", "--output", "artifacts/conversation-format-v1-20261105/historical-replay"]

checks/node-check

["npm.cmd", "--prefix", "web/vercel", "run", "check"]

checks/node-tests-utf8

["npm.cmd", "--prefix", "web/vercel", "test"]

checks/node-tests

["npm.cmd", "--prefix", "web/vercel", "test"]

checks/prepare

[".\\.venv\\Scripts\\python.exe", "scripts/conversation_readiness.py", "prepare", "--output", "artifacts/conversation-format-v1-20261105/reproduced"]

checks/registration

[".\\.venv\\Scripts\\python.exe", "scripts/conversation_format_study.py", "register"]

verification/build

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\package"]

verification/conversation-data

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/conversation_readiness.py", "validate", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\conversation-data"]

verification/diagnose

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "diagnose"]

verification/diff-check

["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--check"]

verification/format

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]

verification/frozen-sources

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/check_frozen_sources.py"]

verification/help

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "--help"]

verification/import

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-c", "import toruk_lm; print(toruk_lm.__version__)"]

verification/independent-cases

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/independent_replication.py", "validate-cases", "--run", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\independent-cases"]

verification/install-local

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."]

verification/lint

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "."]

verification/owned-lm-generate

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm.owned_lm", "generate", "--checkpoint", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\owned-lm-smoke\\models\\23-memory_on\\checkpoint.pt", "--prompt", "Experimental CPU smoke", "--max-new-tokens", "4"]

verification/owned-lm-smoke

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/study_owned_lm.py", "--config", "configs/owned-lm-smoke-v1.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\owned-lm-smoke"]

verification/package

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "check"]

verification/reproduce

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/foundation.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\pipeline"]

verification/research-config

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate-config", "--config", "configs/reproduce-smoke-v1.json"]

verification/research-smoke

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/reproduce-smoke-v1.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\research-smoke"]

verification/staged-diff-check

["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--cached", "--check"]

verification/summarize

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "summarize", "--run", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\pipeline", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\tables"]

verification/tests

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q"]

verification/types-linux

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy", "--platform", "linux"]

verification/types

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy"]

verification/validate

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate", "--manifest", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\pipeline\\data\\manifest.json", "--config", "configs/foundation.json", "--checkpoint", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification\\pipeline\\train\\checkpoint.pt"]

verification-final/build

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\package"]

verification-final/conversation-data

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/conversation_readiness.py", "validate", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\conversation-data"]

verification-final/diagnose

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "diagnose"]

verification-final/diff-check

["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--check"]

verification-final/format

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]

verification-final/frozen-sources

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/check_frozen_sources.py"]

verification-final/help

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "--help"]

verification-final/import

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-c", "import toruk_lm; print(toruk_lm.__version__)"]

verification-final/independent-cases

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/independent_replication.py", "validate-cases", "--run", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\independent-cases"]

verification-final/install-local

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."]

verification-final/lint

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "."]

verification-final/owned-lm-generate

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm.owned_lm", "generate", "--checkpoint", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\owned-lm-smoke\\models\\23-memory_on\\checkpoint.pt", "--prompt", "Experimental CPU smoke", "--max-new-tokens", "4"]

verification-final/owned-lm-smoke

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/study_owned_lm.py", "--config", "configs/owned-lm-smoke-v1.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\owned-lm-smoke"]

verification-final/package

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "check"]

verification-final/reproduce

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/foundation.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\pipeline"]

verification-final/research-config

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate-config", "--config", "configs/reproduce-smoke-v1.json"]

verification-final/research-smoke

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/reproduce-smoke-v1.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\research-smoke"]

verification-final/staged-diff-check

["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--cached", "--check"]

verification-final/summarize

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "summarize", "--run", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\pipeline", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\tables"]

verification-final/tests

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q"]

verification-final/types-linux

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy", "--platform", "linux"]

verification-final/types

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy"]

verification-final/validate

["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate", "--manifest", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\pipeline\\data\\manifest.json", "--config", "configs/foundation.json", "--checkpoint", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\conversation-format-v1-20261105\\verification-final\\pipeline\\train\\checkpoint.pt"]

