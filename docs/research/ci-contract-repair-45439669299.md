# CPU foundation integration contract repair — 2026-11-26

The 28 failures in [run 45439669299](https://github.com/ShamGaneshan2008/Toruk/actions/runs/45439669299)
were reproduced on unchanged commit `31da24ea2c876b75f63ae537f499f73df86129e9`.
They concern platform execution, local-only inputs, historical provenance and
initialization reproducibility. No research gate, score, expected hash, checkpoint,
sealed output, production chat implementation or frozen test was changed.

Git root: `D:/Toruk`; branch: `main`; initial HEAD and `origin/main`:
`31da24ea2c876b75f63ae537f499f73df86129e9` (0 ahead / 0 behind), initially clean.
The user subsequently authorized **one temporary CI-only branch push**. Commit
`412bb58ffeb334bc8bae36ecdacda3c57b81985d` contains eleven repair files on
`ci/repair-cpu-foundation-45439669299-20261126`. An isolated index and `commit-tree`
preserved main, the real index and all working changes. Main was not pushed;
no release or deployment was made. This report and local diagnostic logs remain
uncommitted. See the [exact CI packet](../../artifacts/ci-contract-repair-45439669299-20261126/ci-commit.json).

## Every original failure

The [28-row table](../../artifacts/ci-contract-repair-45439669299-20261126/failure-table.md)
and [machine-readable classification](../../artifacts/ci-contract-repair-45439669299-20261126/failure-classification.json)
identify every parametrized test, original exception and repaired contract.
The [original log](../../artifacts/ci-contract-repair-45439669299-20261126/original-ubuntu-job.log)
contains 28 failed / 529 passed / 1 skipped in 114.47s. Re-running the unchanged
job produced the identical 28 node IDs, 529 passed / 1 skipped in 73.61s:
[reproduction log](../../artifacts/ci-contract-repair-45439669299-20261126/reproduced-ubuntu-job.log),
job `139824029804`. The offline summarizer asserts exact failure-set equality.

| Original failure group | Count | Repair and remaining limitation |
| --- | ---: | --- |
| `test_first_byte_probe` requires ignored checkpoints | 1 | Explicit missing-input skip in a clone; committed 260-record input/plan contract still runs. Separate strict offline hash CLI returns 2 for missing inputs and 1 for a mismatch. It never creates or loads substitute weights. |
| Windows Job controller imports `msvcrt` | 8 | Seven v1 cases and interrupted v2 seal publication run unchanged on Windows; Ubuntu explicitly skips native execution. |
| `lifetime_job_v2` fixtures outside checkout | 16 | Fresh pytest temporary directory inside the checkout preserves the production confinement guard. Two portable missing/unclosed-receipt tests run unchanged on both OSes; native process creation runs on Windows. |
| Archived initialization hash differs on Linux | 1 | Preserve archived expected values. Run exact archival assertion only with the recorded runtime identity; test current-runtime determinism separately and collect both normal/scalar dispatch diagnostics on both hosted OSes. |
| Historical `.gitattributes` compared with live file | 1 | Verify the unchanged manifest digest against the original publication Git blob or a hash-bound snapshot in a shallow clone. Check effective current Git attributes separately. |
| `ctypes.windll` rehearsal fixture | 1 | Run unchanged Windows fixture in the Windows matrix; explicit skip on Ubuntu. |

The selection adapter is [tests/conftest.py](../../tests/conftest.py). It adds
explicit skips, without rewriting frozen tests or reporting a skipped scientific
reproduction as passed. Both existing portable rejection cases and eight new
[portable sealing cases](../../tests/test_lifetime_sealing_portable.py) execute
on Ubuntu. The latter use clearly labelled synthetic receipt-schema fixtures to
exercise real membership/hash/publication checks; they provide **no Linux kernel
process-accounting claim**. Native successful, failed, interrupted, abrupt and
descendant lifetime cases execute in the full Windows pytest job.

## Historical provenance and missing weights

The portable bundle manifest records baseline
`b304091bd16a12be7204d207ed7d82e51e5ba9a6`, but its attributes digest belongs to
publication commit `e3c143ab0095faeb36ecc693c7e1cea09e1f7d24`.
The baseline attributes have SHA256
`50c517ae1f94ad2e6a376c72d05399e6ba4f4d388ea6938de7bcb015ce32b31a`;
the manifest-bound publication attributes have SHA256
`e3c9979c8b004038b145d85d10cc196d51c27bc7fc061b04a32db96ce6e12c41`.
The latter is Git blob `1082dfd5470565f6af6fe5b3f1438daa535cd6c9`.
No recorded digest was changed. [Provenance](../../artifacts/ci-contract-repair-45439669299-20261126/historical/attributes-provenance.json)
and the [exact snapshot](../../artifacts/ci-contract-repair-45439669299-20261126/historical/attributes-e3c9979.txt)
are separate new evidence. A present but wrong Git blob fails immediately; fallback
is limited to the known absent publication object and checks the original digest.
Tests reject a tampered snapshot and a wrong available Git blob. Current effective
attributes are checked independently with `git check-attr`.

Only the active v4 audit adapter calls this historical resolver. The older frozen
`verify_portable_research_evidence.py` remains byte-identical, including its former
live-attributes assumption; this repair does not claim that archived standalone
command was changed. Root `.gitattributes`, `pyproject.toml` and historical test
sources are unchanged. Windows CI disables checkout newline conversion before
checkout so frozen source snapshots retain canonical Git bytes.

The four probe checkpoints are optional clone inputs, not optional hash checks
when present. [Local exact hash results](../../artifacts/ci-contract-repair-45439669299-20261126/local-checkpoint-hashes.json)
are PASS for all four original weights. The registration itself has a pinned
SHA256 and tampering fails. Missing inputs are explicitly distinguished from PASS.
A disposable depth-one clone contained none of these checkpoints and successfully
tested the snapshot fallback without creating replacement weights.

## Initialization investigation

The original Windows seed-601 ordinary initialization has recorded SHA256
`4af341e6f6938f0d7127f16fbd35bd571463877336b173d722e4907affb6b22b`.
Both unchanged Ubuntu attempts produced
`55eb0e94969e5551c859b04338811e88a7d55854af0d3ad8b334a82dc40e0a07`.
These are distinct runtimes: archived Windows Python 3.12.14 versus hosted Linux
Python 3.12.16; the same `torch 2.15.0+cpu` version string does not identify the
same OS build or CPU dispatch. The archival assertion remains intact and passed
on the original local runtime.

[Diagnostic implementation](../../scripts/diagnose_initialization_contract.py)
creates ordinary/recurrent models for seeds 601 and 947 twice per process. It
records RNG state before/after initialization, every tensor's shape/dtype/hash
and first four values, PyTorch build, CPU capability and runtime. It verifies
same-runtime repeatability and parameter counts. It performs zero forwards,
optimizer updates, checkpoint loads or answer generations. A separately recorded
`ATEN_CPU_CAPABILITY=default` run probes CPU dispatch without changing research
initialization or CI defaults. The [saved comparison](../../artifacts/ci-contract-repair-45439669299-20261126/initialization-comparison.json)
and six complete diagnostic JSON records establish:

- Every current-runtime initialization repeated exactly, with the expected parameter count.
- Hosted Windows reproduced all four original local initialization hashes, despite
  different Python/Windows versions. Hosted Ubuntu reproduced the original Linux
  hash difference for all four cells. Both reported AVX512 by default.
- All four cells have identical RNG state hashes before and after construction
  across OSes. Tensor shapes/dtypes agree but initialized tensor bytes differ.
  For seed-601 ordinary, nine tensors differ. For example, one attention value is
  `0.21359065175056458` on Linux and `0.21359068155288696` on Windows.
- Scalar dispatch changes every model hash within each OS, with unchanged RNG
  state hashes, but scalar Windows and scalar Linux still disagree in all four
  cells. CPU dispatch alone does **not** explain the cross-OS discrepancy.
- Build strings differ: GCC 13.3 / MKL 2024.2 on Linux versus MSVC 194234444 /
  MKL 2026.2 on Windows. These are measured differences, not proof that a
  particular compiler/library is the cause.

The most supported finding is runtime-dependent initialization arithmetic, with
equal RNG boundary states and repeatable local results. This does not identify
the exact kernel/rounding operation or prove identical random draws at every
intermediate operation. That mechanism remains unresolved. No byte-identical
cross-runtime claim or replacement expected hash was introduced. The archival
test skips on hosted Windows because its recorded runtime identity differs;
the independent diagnostics nevertheless measured the original four hashes.

## Local checks and preserved failed attempts

| Check | Result |
| --- | --- |
| Original Windows focused baseline | 25 failures / 38 passes, 39.37s: checkout-confinement errors and historical attributes; retained [log](../../artifacts/ci-contract-repair-45439669299-20261126/baseline-windows.log) |
| First repair verification | 1 failure / 42 passes / 39 fixture errors: inaccessible existing cache parent and temporary edit of a manifest-bound verifier; retained [log](../../artifacts/ci-contract-repair-45439669299-20261126/focused-windows.log). Fixed by a fresh owned artifacts cache parent and restoring the verifier's exact HEAD bytes. |
| Corrected focused Windows verification | 82 passed, 12.88s; [log](../../artifacts/ci-contract-repair-45439669299-20261126/focused-windows-002.log). One additional registration-tamper test was subsequently covered by both full runs. |
| Full Windows suite with local checkpoints | **578 passed**, 154.95s; [log](../../artifacts/ci-contract-repair-45439669299-20261126/full-windows.log), [JUnit](../../artifacts/ci-contract-repair-45439669299-20261126/full-windows.xml) |
| Fresh shallow clone plus exact repair overlay | **577 passed / 1 explicit missing-checkpoint skip**, 175.63s; [log](../../artifacts/ci-contract-repair-45439669299-20261126/fresh-windows.log), [JUnit](../../artifacts/ci-contract-repair-45439669299-20261126/fresh-windows.xml) |
| Ruff lint / formatting | PASS; 208 files already formatted |
| mypy default / Linux target | PASS / PASS; 38 source files each |
| Focused mypy on four repair/adapter scripts | PASS with `MYPYPATH=D:/Toruk/src`; initial invocation without source path reported two untyped editable-package imports, corrected by resolving repository source explicitly |
| Dependency check / frozen source check | PASS / PASS (3 frozen sources) |
| Package build | sdist and wheel PASS; [log](../../artifacts/ci-contract-repair-45439669299-20261126/package-build.log) |
| Web syntax / tests | PASS; 20 passed / 1 optional live integration skipped. Used `npm.cmd` after PowerShell policy blocked the `npm.ps1` wrapper. |
| Preserved value-start v1 independent audit | PASS; `STOP_DEVELOPMENT_FAILURE` unchanged, 737 protected files, 65 ignored checkpoints; [receipt](../../artifacts/ci-contract-repair-45439669299-20261126/preserved-v1-audit.log) |
| Preserved value-start v2 independent audit | PASS; `STOP_DEVELOPMENT_FAILURE` unchanged, 48 scientific seals, 24576 recorded updates verified, 388 original v1 files unchanged; [receipt](../../artifacts/ci-contract-repair-45439669299-20261126/preserved-v2-audit.log) |

Historical value-start v1 evidence commit:
`91f2e2b8e6b171c1b1f4fb27898f37f17b6b93ed`. Its search-scope exception and the
earlier paired-batch integrity failure remain recorded. These read-only audits
performed zero new model forwards. No held-out cases were opened for diagnosis.
The sandbox sometimes reports permission-denied old private fixtures as deleted;
read-only Git outside that context verified there are no actual historical
deletions. Existing outputs were not removed to fix this environment issue.

## Reproducible local checks

From `D:/Toruk`, with the existing dependencies (no downloads required):

```powershell
.venv/Scripts/python.exe scripts/check_local_research_checkpoints.py
.venv/Scripts/python.exe -m pytest -q -ra
.venv/Scripts/python.exe scripts/check_frozen_sources.py
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check src tests scripts
.venv/Scripts/python.exe -m mypy
.venv/Scripts/python.exe -m mypy --platform linux
$env:MYPYPATH = 'D:/Toruk/src'
.venv/Scripts/python.exe -m mypy --follow-imports=silent scripts/ci_contracts.py scripts/check_local_research_checkpoints.py scripts/diagnose_initialization_contract.py scripts/audit_qwen_development_v4.py
.venv/Scripts/python.exe -m pip check
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
.venv/Scripts/python.exe -I -S -B artifacts/local-answer-value-start-dev-v1/verify_saved.py
.venv/Scripts/python.exe -I -S -B scripts/audit_value_start_replication_v2.py
.venv/Scripts/python.exe artifacts/ci-contract-repair-45439669299-20261126/summarize_failures.py
git diff --check
git diff --cached --check
```

The diagnostic `--output` path must be new; it refuses overwrite. The fresh-clone
helper also refuses an existing destination. Do not re-run research launchers or
the CI smoke studies into their existing output directories. CI's synthetic
training/generation smoke jobs use new disposable outputs, not historical weights.

## Hosted matrix and final status

[New run 45798618132](https://github.com/ShamGaneshan2008/Toruk/actions/runs/45798618132)
tests the exact scoped commit above and completed **SUCCESS** on its first attempt.

| Hosted job | Result | Saved evidence |
| --- | --- | --- |
| Ubuntu `check` / `139835664770` | PASS: 552 passed / 26 explicit skips, 99.73s; Ruff, formatting, both mypy targets, dependency and frozen-source checks, validation/synthetic smoke jobs and sdist/wheel build all passed | [Full log](../../artifacts/ci-contract-repair-45439669299-20261126/hosted-ubuntu-job.log) |
| `windows-reproduction` / `139835664450` | PASS: 576 passed / 2 explicit skips, 116.89s; all native Job/ctypes tests and owned-model smoke/validation passed, checkout path contains spaces | [Full log](../../artifacts/ci-contract-repair-45439669299-20261126/hosted-windows-job.log) |
| `web` / `139835664853` | PASS: syntax and Node tests | [Full log](../../artifacts/ci-contract-repair-45439669299-20261126/hosted-web-job.log) |

Ubuntu skips comprise 23 newly explicit native Windows cases, the existing
Windows awake-clock test, the optional local-checkpoint reproduction and the
archival runtime reproduction. Windows skips only the latter two. Portable
sealing cases actually ran on Ubuntu. Missing-input skips do not certify
checkpoint reproduction; local exact hashes and the original-runtime assertion
are separate passing evidence. Uploaded CI artifacts contain diagnostic JSON and
JUnit receipts. [Final job/step metadata](../../artifacts/ci-contract-repair-45439669299-20261126/hosted-jobs-final.json)
and [run receipt](../../artifacts/ci-contract-repair-45439669299-20261126/hosted-run-final.json)
preserve the successful conclusions.

Final Git: main and `origin/main` remain at the original HEAD, 0 ahead / 0 behind;
real index empty. Two tracked files modified (workflow and active v4 audit
adapter); new repair scripts/tests, this report and the evidence directory are
uncommitted on main. The temporary remote CI branch contains only the eleven
reviewable repair files. Historical sources, studies and production chat have no
tracked changes. Both working and cached `git diff --check` passed; a separate
isolated-index check covers the new source and documentation files as well.
Raw diagnostic logs retain their recorded whitespace. No second push occurred.

Recommended next action: review and merge the scoped CI
contract repair. Continue to preserve the negative research decisions; this
engineering validation provides no architecture or chatbot-quality claim.
