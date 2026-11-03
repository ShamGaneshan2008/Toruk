# Qualification v1 detailed evidence

All quality gates failed. Treat fluency, abstention ties, and smaller prompt counts separately from useful memory. Frozen data: 168 worlds, three evaluation seeds; stress repeats at +8/+32 turns. Two training checkpoints per method.

| Method | Accuracy seed31/47 | Unsupported /48 seed31/47 | Selected tokens seed31/47 | Forward positions seed31/47 | Latency ms seed31/47 | Sampled RSS MiB seed31/47 | Accuracy 95% |
|---|---:|---:|---:|---:|---:|---:|---:|
| recent | 33.0 / 33.0 | 19.0 / 27.0 | 21900.0 / 21900.0 | 22492.0 / 22621.0 | 640.3 / 675.5 | 208.6 / 207.5 | 0.170–0.223 |
| lexical | 32.0 / 31.0 | 20.0 / 27.0 | 19573.0 / 19573.0 | 20163.0 / 20291.0 | 616.0 / 757.1 | 208.5 / 208.8 | 0.161–0.217 |
| learned | 33.0 / 31.0 | 19.0 / 28.0 | 16091.0 / 16091.0 | 16683.0 / 16806.0 | 652.2 / 701.9 | 209.0 / 209.3 | 0.164–0.220 |
| position | 32.0 / 35.0 | 19.0 / 27.0 | 19428.0 / 19428.0 | 20022.0 / 20156.0 | 635.1 / 841.9 | 208.6 / 208.6 | 0.170–0.229 |
| integrated | 48.0 / 34.0 | 0.0 / 45.0 | 21900.0 / 21900.0 | 53451.0 / 53910.0 | 2022.8 / 2495.3 | 208.9 / 208.6 | 0.220–0.271 |
| zero | 48.0 / 48.0 | 0.0 / 0.0 | 21900.0 / 21900.0 | 53451.0 / 53451.0 | 2079.1 / 2022.4 | 208.6 / 208.2 | 0.286–0.286 |
| no_correction | 48.0 / 31.0 | 0.0 / 44.0 | 21900.0 / 21900.0 | 49495.0 / 49948.0 | 2006.3 / 2757.8 | 207.9 / 208.8 | 0.208–0.262 |
| no_preservation | 48.0 / 48.0 | 0.0 / 0.0 | 21900.0 / 21900.0 | 53451.0 / 53454.0 | 2138.7 / 1996.6 | 208.9 / 208.4 | 0.286–0.286 |
| half_capacity | 48.0 / 35.0 | 0.0 / 32.0 | 21900.0 / 21900.0 | 53451.0 / 53787.0 | 2209.2 / 1891.7 | 209.1 / 208.7 | 0.223–0.274 |


Accuracy columns are exact world counts /168; unsupported counts are /48. For multi-fact worlds both answers must match. Selected/forward counts and latency are sums over 192 generated answers at load 0. RSS is the process peak sampled over all three loads, including loading; it cannot be attributed to load 0 alone.

## Categories and stress

| Method | Train seed | Added turns | Correct /168 | Known /120 | Unsupported /48 | Full scanned tokens | Selected tokens | Forward positions | Latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| half_capacity | 31 | 0 | 48 | 0 | 0 | 32751 | 21900 | 53451 | 2209.2 |
| half_capacity | 31 | 8 | 48 | 0 | 0 | 64245 | 21900 | 83409 | 3588.4 |
| half_capacity | 31 | 32 | 48 | 0 | 0 | 158988 | 21900 | 173544 | 7765.8 |
| half_capacity | 47 | 0 | 35 | 19 | 32 | 32751 | 21900 | 53787 | 1891.7 |
| half_capacity | 47 | 8 | 33 | 19 | 34 | 64245 | 21900 | 83759 | 3045.7 |
| half_capacity | 47 | 32 | 41 | 23 | 30 | 158988 | 21900 | 173889 | 6444.5 |
| integrated | 31 | 0 | 48 | 0 | 0 | 32751 | 21900 | 53451 | 2022.8 |
| integrated | 31 | 8 | 48 | 0 | 0 | 64245 | 21900 | 83409 | 3295.0 |
| integrated | 31 | 32 | 48 | 0 | 0 | 158988 | 21900 | 173548 | 7089.2 |
| integrated | 47 | 0 | 34 | 31 | 45 | 32751 | 21900 | 53910 | 2495.3 |
| integrated | 47 | 8 | 33 | 30 | 45 | 64245 | 21900 | 83876 | 4158.7 |
| integrated | 47 | 32 | 34 | 34 | 48 | 158988 | 21900 | 174024 | 8594.3 |
| learned | 31 | 0 | 33 | 4 | 19 | 32751 | 16091 | 16683 | 652.2 |
| learned | 31 | 8 | 44 | 7 | 11 | 64245 | 16074 | 16624 | 647.7 |
| learned | 31 | 32 | 42 | 8 | 14 | 158988 | 16173 | 16745 | 698.8 |
| learned | 47 | 0 | 31 | 11 | 28 | 32751 | 16091 | 16806 | 701.9 |
| learned | 47 | 8 | 33 | 12 | 27 | 64245 | 16074 | 16783 | 719.7 |
| learned | 47 | 32 | 41 | 17 | 24 | 158988 | 16173 | 16903 | 784.7 |
| lexical | 31 | 0 | 32 | 4 | 20 | 32751 | 19573 | 20163 | 616.0 |
| lexical | 31 | 8 | 42 | 6 | 12 | 64245 | 19538 | 20092 | 608.7 |
| lexical | 31 | 32 | 42 | 8 | 14 | 158988 | 19631 | 20205 | 616.3 |
| lexical | 47 | 0 | 31 | 10 | 27 | 32751 | 19573 | 20291 | 757.1 |
| lexical | 47 | 8 | 34 | 13 | 27 | 64245 | 19538 | 20250 | 743.7 |
| lexical | 47 | 32 | 42 | 17 | 23 | 158988 | 19631 | 20359 | 772.5 |
| no_correction | 31 | 0 | 48 | 0 | 0 | 32751 | 21900 | 49495 | 2006.3 |
| no_correction | 31 | 8 | 48 | 0 | 0 | 64245 | 21900 | 79453 | 3325.7 |
| no_correction | 31 | 32 | 48 | 0 | 0 | 158988 | 21900 | 169592 | 7304.1 |
| no_correction | 47 | 0 | 31 | 27 | 44 | 32751 | 21900 | 49948 | 2757.8 |
| no_correction | 47 | 8 | 28 | 25 | 45 | 64245 | 21900 | 79933 | 4534.3 |
| no_correction | 47 | 32 | 28 | 26 | 46 | 158988 | 21900 | 170044 | 9746.9 |
| no_preservation | 31 | 0 | 48 | 0 | 0 | 32751 | 21900 | 53451 | 2138.7 |
| no_preservation | 31 | 8 | 48 | 0 | 0 | 64245 | 21900 | 83409 | 3403.0 |
| no_preservation | 31 | 32 | 48 | 0 | 0 | 158988 | 21900 | 173544 | 7301.1 |
| no_preservation | 47 | 0 | 48 | 0 | 0 | 32751 | 21900 | 53454 | 1996.6 |
| no_preservation | 47 | 8 | 48 | 0 | 0 | 64245 | 21900 | 83412 | 3193.1 |
| no_preservation | 47 | 32 | 49 | 1 | 0 | 158988 | 21900 | 173557 | 6931.4 |
| position | 31 | 0 | 32 | 3 | 19 | 32751 | 19428 | 20022 | 635.1 |
| position | 31 | 8 | 41 | 5 | 12 | 64245 | 19445 | 20001 | 620.2 |
| position | 31 | 32 | 42 | 7 | 13 | 158988 | 19543 | 20119 | 632.1 |
| position | 47 | 0 | 35 | 14 | 27 | 32751 | 19428 | 20156 | 841.9 |
| position | 47 | 8 | 37 | 16 | 27 | 64245 | 19445 | 20163 | 831.1 |
| position | 47 | 32 | 36 | 11 | 23 | 158988 | 19543 | 20269 | 838.0 |
| recent | 31 | 0 | 33 | 4 | 19 | 32751 | 21900 | 22492 | 640.3 |
| recent | 31 | 8 | 40 | 5 | 13 | 64245 | 21900 | 22440 | 636.0 |
| recent | 31 | 32 | 42 | 6 | 12 | 158988 | 21900 | 22456 | 653.3 |
| recent | 47 | 0 | 33 | 12 | 27 | 32751 | 21900 | 22621 | 675.5 |
| recent | 47 | 8 | 37 | 16 | 27 | 64245 | 21900 | 22617 | 680.2 |
| recent | 47 | 32 | 36 | 12 | 24 | 158988 | 21900 | 22628 | 696.5 |
| zero | 31 | 0 | 48 | 0 | 0 | 32751 | 21900 | 53451 | 2079.1 |
| zero | 31 | 8 | 48 | 0 | 0 | 64245 | 21900 | 83409 | 3376.9 |
| zero | 31 | 32 | 48 | 0 | 0 | 158988 | 21900 | 173544 | 7226.9 |
| zero | 47 | 0 | 48 | 0 | 0 | 32751 | 21900 | 53451 | 2022.4 |
| zero | 47 | 8 | 48 | 0 | 0 | 64245 | 21900 | 83409 | 3296.1 |
| zero | 47 | 32 | 48 | 0 | 0 | 158988 | 21900 | 173544 | 7064.4 |

| Method | Seed | ambiguity | correction | distant | distraction | multi | preservation | unknown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| half_capacity | 31 | 24/24 | 0/24 | 0/24 | 0/24 | 0/24 | 0/24 | 24/24 |
| half_capacity | 47 | 10/24 | 2/24 | 7/24 | 3/24 | 0/24 | 7/24 | 6/24 |
| integrated | 31 | 24/24 | 0/24 | 0/24 | 0/24 | 0/24 | 0/24 | 24/24 |
| integrated | 47 | 2/24 | 5/24 | 9/24 | 8/24 | 0/24 | 9/24 | 1/24 |
| learned | 31 | 24/24 | 0/24 | 3/24 | 1/24 | 0/24 | 0/24 | 5/24 |
| learned | 47 | 18/24 | 2/24 | 6/24 | 1/24 | 0/24 | 2/24 | 2/24 |
| lexical | 31 | 23/24 | 0/24 | 3/24 | 1/24 | 0/24 | 0/24 | 5/24 |
| lexical | 47 | 19/24 | 2/24 | 5/24 | 1/24 | 0/24 | 2/24 | 2/24 |
| no_correction | 31 | 24/24 | 0/24 | 0/24 | 0/24 | 0/24 | 0/24 | 24/24 |
| no_correction | 47 | 3/24 | 3/24 | 9/24 | 5/24 | 1/24 | 9/24 | 1/24 |
| no_preservation | 31 | 24/24 | 0/24 | 0/24 | 0/24 | 0/24 | 0/24 | 24/24 |
| no_preservation | 47 | 24/24 | 0/24 | 0/24 | 0/24 | 0/24 | 0/24 | 24/24 |
| position | 31 | 24/24 | 1/24 | 2/24 | 0/24 | 0/24 | 0/24 | 5/24 |
| position | 47 | 19/24 | 3/24 | 6/24 | 3/24 | 0/24 | 2/24 | 2/24 |
| recent | 31 | 24/24 | 1/24 | 2/24 | 0/24 | 0/24 | 1/24 | 5/24 |
| recent | 47 | 19/24 | 1/24 | 6/24 | 3/24 | 0/24 | 2/24 | 2/24 |
| zero | 31 | 24/24 | 0/24 | 0/24 | 0/24 | 0/24 | 0/24 | 24/24 |
| zero | 47 | 24/24 | 0/24 | 0/24 | 0/24 | 0/24 | 0/24 | 24/24 |

## Paired uncertainty

Percentile 95% intervals for absolute accuracy differences; world clusters preserve training-seed pairing. Conditional on two trained models; no seed-population inference.

| Method | Versus recent | Versus lexical |
|---|---:|---:|
| half_capacity | 0.0119, 0.0893 | 0.0208, 0.0952 |
| integrated | 0.0089, 0.0863 | 0.0179, 0.0952 |
| learned | -0.0238, 0.0119 | -0.0089, 0.0149 |
| lexical | -0.0238, 0.0060 | 0.0000, 0.0000 |
| no_correction | -0.0030, 0.0774 | 0.0089, 0.0863 |
| no_preservation | 0.0625, 0.1161 | 0.0685, 0.1250 |
| position | -0.0060, 0.0119 | -0.0060, 0.0298 |
| recent | 0.0000, 0.0000 | -0.0060, 0.0238 |
| zero | 0.0625, 0.1161 | 0.0685, 0.1250 |

## Exact commands and exit codes

Freeze command (observed exit 0, before generation):

```powershell
.\.venv\Scripts\python.exe scripts/qualify_memory.py freeze --run artifacts/qualification-v1-20261103
```

Full source-identity records and logs accompany each command in commands.json.

| Check | Exit | Exact argv (JSON array) |
|---|---:|---|
| analysis | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "analyze", "--run", "artifacts/qualification-v1-20261103"]` |
| build-fresh | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "artifacts/qualification-v1-20261103/package"]` |
| chat-e2e | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_chat_foundation.py", "--backbone-dir", "artifacts/qwen-chat-001/backbone", "--baseline-only", "--output-dir", "artifacts/qualification-v1-20261103/chat-e2e"]` |
| final-build | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "artifacts/qualification-v1-20261103/package-final"]` |
| final-diff | 0 | `["git", "diff", "--check"]` |
| final-half_capacity-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "half_capacity", "--seed", "31"]` |
| final-half_capacity-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "half_capacity", "--seed", "47"]` |
| final-integrated-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "integrated", "--seed", "31"]` |
| final-integrated-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "integrated", "--seed", "47"]` |
| final-learned-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "learned", "--seed", "31"]` |
| final-learned-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "learned", "--seed", "47"]` |
| final-lexical-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "lexical", "--seed", "31"]` |
| final-lexical-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "lexical", "--seed", "47"]` |
| final-no_correction-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "no_correction", "--seed", "31"]` |
| final-no_correction-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "no_correction", "--seed", "47"]` |
| final-no_preservation-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "no_preservation", "--seed", "31"]` |
| final-no_preservation-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "no_preservation", "--seed", "47"]` |
| final-position-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "position", "--seed", "31"]` |
| final-position-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "position", "--seed", "47"]` |
| final-recent-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "recent", "--seed", "31"]` |
| final-recent-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "recent", "--seed", "47"]` |
| final-tools-format | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "scripts/package_qualification.py", "scripts/qualify_memory.py", "scripts/smoke_qualification_ui.py", "tests/test_qualification.py"]` |
| final-tools-lint | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "scripts/package_qualification.py", "scripts/qualify_memory.py", "scripts/smoke_qualification_ui.py", "tests/test_qualification.py"]` |
| final-zero-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "zero", "--seed", "31"]` |
| final-zero-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "scripts/qualify_memory.py", "evaluate", "--run", "artifacts\\qualification-v1-20261103", "--method", "zero", "--seed", "47"]` |
| focused-format | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts/qualify_memory.py", "scripts/package_qualification.py", "scripts/download_chat_backbone.py", "scripts/smoke_chat_foundation.py"]` |
| focused-lint | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "src", "tests", "scripts/qualify_memory.py", "scripts/package_qualification.py", "scripts/download_chat_backbone.py", "scripts/smoke_chat_foundation.py"]` |
| live-page-handlers | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_qualification_ui.py", "--output-dir", "artifacts/qualification-v1-20261103/live-page-handlers"]` |
| node-check | 0 | `["npm.cmd", "--prefix", "web/vercel", "run", "check"]` |
| node-tests | 0 | `["npm.cmd", "--prefix", "web/vercel", "test"]` |
| build | 1 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation"]` |
| diagnose | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "diagnose"]` |
| diff-check | 0 | `["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--check"]` |
| format | 1 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]` |
| help | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "--help"]` |
| import | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-c", "import toruk_lm; print(toruk_lm.__version__)"]` |
| install-local | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."]` |
| lint | 1 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "."]` |
| package | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pip", "check"]` |
| reproduce | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/foundation.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\qualification-v1-20261103\\verification\\pipeline"]` |
| research-config | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate-config", "--config", "configs/reproduce-smoke-v1.json"]` |
| research-smoke | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/reproduce-smoke-v1.json", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\qualification-v1-20261103\\verification\\research-smoke"]` |
| staged-diff-check | 0 | `["git", "-c", "safe.directory=C:/Users/susee/VS_CODE_PROJECT/Toruk", "diff", "--cached", "--check"]` |
| summarize | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "summarize", "--run", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\qualification-v1-20261103\\verification\\pipeline", "--output", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\qualification-v1-20261103\\verification\\tables"]` |
| tests | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q"]` |
| types-linux | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy", "--platform", "linux"]` |
| types | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "mypy"]` |
| validate | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate", "--manifest", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\qualification-v1-20261103\\verification\\pipeline\\data\\manifest.json", "--config", "configs/foundation.json", "--checkpoint", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\artifacts\\qualification-v1-20261103\\verification\\pipeline\\train\\checkpoint.pt"]` |

Training costs are copied verbatim into training-costs.json and are shared by inference ablations; do not count each ablation as a separately trained model. No optimizer steps were added for qualification. Raw outputs and original negative results remain intact.
