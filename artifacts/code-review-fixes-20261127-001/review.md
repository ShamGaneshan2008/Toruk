Review completed on 2026-11-27 in D:/Toruk. Branch main; HEAD and local
origin/main are both 916efdd4b63dd63fab08ffabb8ab6e8313dc4bf2. The final
readable Git status has no tracked or staged changes and retains the existing
untracked studies, diagnosis and adapter. All changes remain uncommitted.
The exact status and whitespace-check output are in git-final.json.

The review found and fixed these software defects in the opt-in resume adapter:

1. Negative finite AdamW second moments passed validation. A subsequent square
   root could produce NaNs. Reject these values before any resumed update.
2. The legacy loader silently cast corrupted model tensor dtypes. Compare the
   raw checkpoint dtype/layout with the expected model and reject differences.
   Reject a non-float32 global default before constructing the adapter model.
3. Missing document IDs could fail after training had begun; duplicate and invalid
   IDs were accepted. Validate nonempty unique string IDs before calling the
   numerical trainer or creating output directories.
4. The frozen study auditor did not completely reconcile vector/teacher token
   ledgers or enforce native scalar types. Add a separate read-only reviewer
   that retains the original audit, checks all observation ledgers and costs,
   and rejects inconsistent IDs, EOS placement, decoded answers and replay flags.
   No frozen study code or evidence was changed.

Seven targeted regression cases failed against the original adapter before the
fixes. The original failure output is retained in regressions-before.log/json.
Eight adapter regression tests and nineteen saved-record reviewer tests were
added. Valid resume behavior remains covered by the existing exact-resume tests.
The independent reviewer initially failed under Python -I because its sibling
auditor was not on sys.path. That CLI defect was corrected; both attempts remain
in offline-study-review.log/json and offline-study-review-002.log/json.

The exact active files changed by this review are:

- src/toruk_lm/owned_resume.py
- tests/test_owned_resume.py
- docs/owned-resume.md
- scripts/check_city_contrastive_evidence.py (new)
- tests/test_research_observation_review.py (new)

This artifact directory additionally contains the original eight reviewed files
under before/, the starting hashes, disposable test outputs, build products,
check logs and receipts, a read-only preservation verifier and this report.
Legacy owned_training.py, production chat, historical studies and frozen city
protocol/runner/auditor/tests were preserved.

| Final validation | Result | Evidence |
| --- | --- | --- |
| Focused pytest: resume, owned LM, reviewer, city, v2, both lifetime supervisors | PASS: 135 tests | final-tests.log/json |
| Ruff check of repository | PASS | lint.log/json |
| Ruff format check: src, tests, scripts | PASS: 219 files | format.log/json |
| Mypy configured source targets, Windows | PASS: 39 files | types.log/json |
| Mypy configured source targets, Linux target | PASS: 39 files | types-linux.log/json |
| Mypy new read-only reviewer | PASS | reviewer-types.log/json |
| Wheel and sdist build, no isolation | PASS | build.log/json; package/ |
| Import adapter from safely extracted built wheel with Python -I | PASS | package-import.json |
| Independent saved-record audit, Python -I -S -B | PASS: 32 observations, 48 seals, zero model forwards | offline-study-review-002.log/json |
| Frozen evidence preservation | PASS | preservation.log/json |
| git diff --check and git diff --cached --check | PASS | git-final.json |
| Review file trailing-whitespace/newline checks | PASS | preservation.log/json |
| Entire repository pytest and hosted CI | SKIPPED: scoped review; no unrelated scientific fits or held-out evaluations | Focused selection above |

Preservation verification confirmed every byte/hash in the 711-file city artifact
inventory, including all 16 checkpoints; all 25 registered city source hashes;
all 770 historical v2 inventory entries; and the eight archived original files.
Three active adapter files were intentionally updated, so the older whole-live-
workspace delivery comparison is not a current-source acceptance gate. Its
inventory and receipt remain unchanged. The immutable city experiment's own
registered source hashes still match exactly.

Reproduce the offline review without models or held-out access:

```powershell
.venv/Scripts/python.exe -I -S -B scripts/check_city_contrastive_evidence.py
.venv/Scripts/python.exe -B artifacts/code-review-fixes-20261127-001/verify_review.py
```

The scientific decision remains FAIL / STOP_DEVELOPMENT_FAILURE. Software tests
and stronger accounting do not repair the observed development regressions or
prove improved accuracy, memory, reasoning or efficiency. No registered cell
was retried, no new study answers were generated, and held-out data was unopened.
Disposable unit tests exercise training/resume only on synthetic fixtures.

Recommended next action: use the saved city-study teacher losses and first-token
vectors to diagnose the two newly introduced code-answer regressions, without
fitting models or generating answers. Require a supported, separately registered
hypothesis before another controlled training study; do not reuse these consumed
cells or relax their failed no-regression gates.
