# Monitor sealing v2 engineering commit review

23 November 2026. Review and disposable-process validation only. No model fit,
research checkpoint input, held-out data, paired-batch-v1 execution or push.

The engineering commit follows evidence commit
392e002caa203d17a837fde7e759187e59a81301. It includes the v2 harness, its tests,
lifecycle documentation, and reviewed validation records. Generated mypy caches
are excluded. Earlier v2 documents/inventories retain their as-of-run
'uncommitted' statements; the original record bytes are not rewritten.

The reviewed execution API calls watch() synchronously. Its descendants are
drained and its output/monitor streams and handles close; final cost.json is
written and closed before watch() returns. Only then does watch_and_seal()
validate closure and publish the seal. No normal, failed, timed-out or interrupted
execution branch through this API publishes workload PASS before monitoring
finishes. STOP snapshots retain STOP. Missing/incomplete receipts, seal errors
and interrupted publication are refused, preserving partial records and failure
markers. Direct seal_closed_run() assumes an observer-owned final receipt and
closed writers; it is not authentication for fabricated receipts or unrelated
external writers.

The original24 disposable tests are rerun under a fresh pytest-tmp-002 directory,
preserving pytest-tmp-001 and all prior validation artifacts. Focused mypy,
repository Ruff lint/format, staged inventory/byte checks and
git diff --cached --check are recorded in
[the commit review](../../artifacts/local-answer-monitor-sealing-v2-20261123/commit-review-002/final-review.json).
Artifact-local attributes permit blank EOF only in six intentional negative
fixtures (three prior, three repeated); their invalidated seal/log/receipt bytes
are preserved exactly, not repaired.

All337 original paired-batch inventory entries must remain byte-identical.
The v1 training and registered integrity gates remain failed; independent
verification is not a full v1 PASS. No v1 seals, gates or source files are altered.
