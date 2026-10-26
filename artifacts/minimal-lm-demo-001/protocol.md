# Frozen protocol — minimal next-token LM demo

Recorded before data generation, baseline measurement, or training on 2026-10-26.

- Source: deterministic local strings `"abc " * n + "a"`; train has eight documents with n=8..15; validation has two documents with n=16..17. No test data is used. IDs and full texts differ across splits; the repeated four-byte rule is deliberately shared. Exact-text and ID separation are checked by `engine.train`. The full held-out documents are never passed to training updates.
- Tokenizer: `toruk-utf8-byte-v1`, 259 IDs (PAD 0, BOS 1, EOS 2, bytes +3).
- Model: ordinary causal decoder, context 32, width 16, two heads, one layer, 12,112 parameters. CPU, one Torch thread. Python 3.14.6, Torch 2.14.1+cpu.
- Optimization: seed 23, AdamW, batch four windows, learning rate 0.003, exactly 120 updates, no resume and no retry. Hard wall-time limit 180 seconds for training. Expected model/optimizer data below 1 GiB RAM; abort rather than enlarge the run if this bound is exceeded. No GPU.
- Baseline: same seeded untrained model evaluated on both splits. Also report the constant most-frequent training-target token as a simple accuracy baseline. Its identity is selected from training targets only.
- Metrics: train and validation mean next-token cross-entropy in nats (including EOS), perplexity, teacher-forced top-1 token accuracy, and a greedy 16-token sample from `"abc "`. Validation is measured once after the 120-step run. The sample succeeds if its decoded first 16 bytes equal `"abc abc abc abc "`.
- Success criteria, all required: validation loss at most half of seeded untrained validation loss; validation top-1 token accuracy at least 80%; sample matches the stated 16-byte sequence. The claim is only learning this synthetic four-byte next-token rule, not general language ability.
- Planned artifact path: `artifacts/minimal-lm-demo-001/`. Existing Toruk `train`, `evaluate`, `generate`, and checkpoint load paths are used. Data, SHA-256 hashes, exact commands/logs, checkpoint metadata, and measurements are retained here.
