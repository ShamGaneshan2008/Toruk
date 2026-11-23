# Paired-batch v1 evidence preservation

23 November 2026. Preservation only; zero new training, model forwards or answers.

The original v1 training mastery gate failed. Development was NOT RUN.
Seed947 ordinary scored90/96 with paired batches versus92/96 with the matched
city-shuffled schedule (original schedule80/96). Pairing corrected all16 original
errors but introduced six regressions, versus four for city shuffling.
No memory advantage or generalization result follows.

**The registered integrity audit FAILED:** workers sealed resources.jsonl before
the parent monitor finished appending. All12 original observation seals, final
journals, raw outputs, source snapshots, receipts and failed-audit logs are
preserved unchanged. Every stale monitor digest matches an exact complete-line
prefix of its final journal. Independent verification reproduces1152 scored
answers and384 vectors, with72 other sealed payload hashes matching.
**Independent verification does not turn the registered integrity failure into
a full PASS.** Its exit2 and the registered auditor's exit1 remain failures.

The scoped evidence commit includes the original protocol/report, runner/tests,
all337 inventoried files except12 ignored checkpoint weights, the inventory
itself, and this preservation record. The24 disposable process-test records are
retained because they document the original accounting/stop contracts.
All12 checkpoint paths, sizes and hashes are committed as evidence; weight
bytes stay local and Git-ignored, following the existing handoff constraint.
A fresh checkout without those local weights cannot complete weight-hash checks.

Historical HEAD, uncommitted-state and as-run source assertions in the frozen
records describe their creation time. They are not rewritten for this commit.
The completed earlier checkpoint handoff is verified unchanged and stays local.
A new artifact-local .gitattributes permits the existing frozen pyproject.toml
snapshot's blank EOF in Git whitespace checks; no snapshot bytes are changed.

See [v1 results](local-answer-paired-batch-dev-v1-results.md),
[original inventory](../../artifacts/local-answer-paired-batch-dev-v1/artifact-inventory.json)
and [preservation review](../../artifacts/local-answer-paired-batch-v1-preservation-20261123/review.json).
The subsequent observer-owned sealing-v2 harness is separate, uncommitted work.
It does not repair or replace any v1 seal or authorize another v1 run.
