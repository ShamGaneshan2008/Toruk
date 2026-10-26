# Minimal next-token language-model demo — 2026-10-26

**DEMO VALIDATED for the frozen four-byte synthetic pattern.** This establishes that Toruk's ordinary next-token model can learn this small held-out pattern. It does not establish general language ability, factual answering, or useful behavior on natural text.

## Repository and preregistration

- Root `C:\Users\susee\VScode Project\Toruk`; branch `main`; HEAD `add917398efa061cc67b1b10aff3853acf3c526c`. At start, tracked files were clean and many earlier artifacts/research notes were untracked. Several older artifact directories could not be listed by Git because of access restrictions. Existing work was preserved; no reset, clean, stash, commit, push, or publication.
- The earlier [capability check](language-model-capability-check.md) found no reproduced model-path defect, but its two CLI parity tests had timed out in a restricted environment. With working virtual-environment access, both passed (2/2, 85.56 s) **before** this experiment. Thus the demo used the existing tokenizer, shifted targets, trainer, checkpoint loader, greedy decoder, and evaluator unchanged.
- The [frozen protocol](../../artifacts/minimal-lm-demo-001/protocol.md) and [config](../../configs/minimal-lm-demo-v1.json) were written before data generation, baseline scoring, or training. One initial `scripts/check.py` invocation placed its options after the positional label, failed with `FileNotFoundError` in 0.027 s, and launched no training; its evidence remains in `artifacts/checks/demo-train.{json,log}`. The corrected wrapper ran the original, unchanged 120-step protocol once.

## Design and exact commands

Eight train documents contain `"abc " * n + "a"` for n=8..15; two held-out validation documents use n=16..17. Train and validation JSONL have different IDs and full texts (598 and 200 bytes respectively). The shared four-byte rule is intentional; whole validation documents were not used in updates. The train and validation SHA-256 values are `27d83355cf36eb6aa77fbe000bfa6de096d38d845e96c03e219bf1c211e88ca1` and `2f3e846bbfb42cc12eeee001aa2364d89a8223ccdfc27be987ec1969f2d2ce86`. The checkpoint embeds both hashes. `engine.train` checks distinct IDs and exact texts. No test examples were created or used.

Tokenizer: fixed UTF-8 bytes, 259 IDs. Model: causal decoder, context 32, width 16, two heads, one layer, **12,112 parameters**. Seed 23, AdamW learning rate 0.003, batch four, 120 updates, one CPU thread. Python 3.14.6 and Torch 2.14.1+cpu. Training was wrapped in a hard 180-second timeout; it completed in 8.63 s, with 1.25 s reported inside the optimizer loop. CPU peak memory was **not measured or enforced**; the intended 1 GiB operational ceiling in the protocol therefore remains unverified. The checkpoint is 175,638 bytes.

Data were generated with this command from the repository root. The exact measurement implementation is [measure.py](../../artifacts/minimal-lm-demo-001/measure.py).

```powershell
$demo = 'artifacts/minimal-lm-demo-001'; New-Item -ItemType Directory -Force -Path "$demo/data" | Out-Null; foreach ($split in @('train','validation')) { if ($split -eq 'train') { $sizes = 8..15 } else { $sizes = 16..17 }; $lines = foreach ($n in $sizes) { @{id = "$split-$n"; text = ('abc ' * $n) + 'a'} | ConvertTo-Json -Compress }; [System.IO.File]::WriteAllText((Join-Path (Resolve-Path "$demo/data") "$split.jsonl"), (($lines -join "`n") + "`n"), [System.Text.UTF8Encoding]::new($false)) }
```

The remaining exact commands were:

```powershell
.\.venv\Scripts\python.exe artifacts/minimal-lm-demo-001/measure.py baseline
.\.venv\Scripts\python.exe scripts/check.py --timeout 180 --output-dir artifacts/minimal-lm-demo-001 demo-train -- .\.venv\Scripts\python.exe -m toruk_lm train --train artifacts/minimal-lm-demo-001/data/train.jsonl --validation artifacts/minimal-lm-demo-001/data/validation.jsonl --config configs/minimal-lm-demo-v1.json --output artifacts/minimal-lm-demo-001/train --steps 120
.\.venv\Scripts\python.exe artifacts/minimal-lm-demo-001/measure.py trained
.\.venv\Scripts\python.exe scripts/check.py --timeout 90 --output-dir artifacts/minimal-lm-demo-001 demo-evaluate -- .\.venv\Scripts\python.exe -m toruk_lm evaluate --checkpoint artifacts/minimal-lm-demo-001/train/checkpoint.pt --data artifacts/minimal-lm-demo-001/data/validation.jsonl --output artifacts/minimal-lm-demo-001/eval --max-new-tokens 16
.\.venv\Scripts\python.exe scripts/check.py --timeout 90 --output-dir artifacts/minimal-lm-demo-001 demo-generate -- .\.venv\Scripts\python.exe -m toruk_lm generate --checkpoint artifacts/minimal-lm-demo-001/train/checkpoint.pt --prompt 'abc ' --max-new-tokens 16
```

## Results

| Measurement | Untrained | Trained |
| --- | ---: | ---: |
| Train loss, nats/token (384 targets) | 5.60532 | 0.10674 |
| Train perplexity | 271.868 | 1.11265 |
| Train top-1 accuracy | 0% | 97.92% |
| Held-out loss, nats/token (136 targets) | 5.63331 | **0.09159** |
| Held-out perplexity | 279.587 | **1.09592** |
| Held-out top-1 accuracy | 0% | **98.53%** |

The constant most-frequent training-target token (ID 100, `a`) gets **25.74%** held-out top-1 accuracy. The trained held-out loss is 1.63% of the untrained baseline, below the registered 50% threshold; top-1 accuracy exceeds 80%. From prompt `abc `, the trained greedy 16-token continuation is exactly `abc abc abc abc `, meeting the registered sample criterion. The untrained sample was non-pattern text. CLI evaluation independently returned the same held-out loss and 136 target count; CLI `generate` returned the same 16 token IDs. The checkpoint SHA-256 is `e00a0f0b58233bc6013622e964c68eb9672db158bff80f0efdfceb5483e8b545`; its `next_step` is 120. Raw baseline/trained JSON, CLI outputs, checkpoint, config and logs are under [the demo artifact](../../artifacts/minimal-lm-demo-001/).

## Local checks and limits

- `.\.venv\Scripts\python.exe -m pytest -q tests/test_foundation.py::test_real_cli_pipeline tests/test_worlds.py::test_real_controlled_world_cli_train_reload_and_answer_without_gold`: **2 passed** before training. `.\.venv\Scripts\python.exe -m pytest -q tests/test_foundation.py tests/test_worlds.py`: **15 passed** afterward.
- `.\.venv\Scripts\python.exe scripts/verify.py --prefix minimal-lm-demo --output-dir artifacts/minimal-lm-demo-001/verification`: **nonzero**. Its full suite passed **86/86**; install, package, import, help, diagnose, lint, format, foundation reproduction/validation/summary, research config/smoke, build, and diff checks passed. The `types` and `types-linux` checks failed while mypy 1.20.2 parsed NumPy 2.5.4's Python 3.12 `type` alias syntax under the project's configured Python 3.11 target. This is a reproducible environment/typing compatibility failure, not a model or demo inference failure. Diagnostic `.\.venv\Scripts\python.exe -m mypy --python-version 3.14 --platform linux` passed all 17 source files; it does not replace the documented gate.
- `git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check`: passed. It covers tracked diffs; the new config, report and artifact files are untracked. No GitHub Actions status was checked or claimed for this commit.

This corpus has only four repeating ordinary bytes and is intentionally easy. Validation shares the pattern and many prefixes with training; only whole sequence lengths differ. The demonstration supports learning that rule on held-out documents, not generalization to natural prose or the controlled factual benchmark. Single seed, no uncertainty estimate, and no measured training peak RAM.

**Next step:** repair the Python 3.11 mypy/NumPy-stub compatibility in the verification environment, then design a separate frozen, bounded natural-text evaluation before making any broader LM capability claim.
