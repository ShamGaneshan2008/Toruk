# Portable Qwen development v4 evidence

This directory preserves the offline development audit described by commit
`bd46549158139ef9ef93f10b9387aaf0c595b0b8`. It adds no selector variant,
model generation, training, held-out evaluation or quality improvement.
Toruk remains 5/7 versus lexical retrieval's 7/7.

## Included evidence and dependencies

The portable set contains the original, byte-identical `baseline.json`,
`audit.json` and `verification-summary.json`; all original top-level JSON/log
receipts in `checks/` and `verification/`, including failed preflights; four
hash-matching historical source snapshots; this documentation; a local byte
preservation attributes file; and `verify.py` with `portable-manifest.json`.
New portable-verification receipts are stored in `portable-checks/`.
The manifest lists every included payload and its SHA-256. It excludes itself
and the newly emitted verification receipts to avoid circular hashes; Git
records those files. This is a repository-relative evidence addition, not a
standalone model/environment bundle. Existing tracked v1–v3 and portable-v1
files remain dependencies and are not duplicated or modified.

The original baseline's 472 hashes and the audit's 19 consumed-input hashes
all match the isolated checkout at packaging. Replaying the saved development
audit reproduces all substantive output fields, including the two generation
failure diagnoses. Only newly measured audit CPU/wall time is excluded from
that comparison. The original timings remain untouched in `audit.json`.

## Historical source hashes and paths

The original check receipts and verification summary predate the review commit.
Their original `head`, `uncommitted`, absolute paths and source hashes describe
that earlier state, not the current commit. In particular, the committed test
uses the tracked portable manifest instead of a local baseline receipt, and
the report was updated for the review commit. The audit script also received
an annotation-only correction during the original checks. Their earlier
source hashes must not be replaced with current-file hashes.

Four earlier source versions were reconstructed from the documented edits and
retained only after their complete bytes matched the recorded SHA-256 exactly:

| SHA-256 | Snapshot |
|---|---|
| `c1b689ba5944b3b6ac4b383472f36ef5cf9968b71611c2e9f7d93166324499ce` | Initial check-wrapper audit source |
| `e9422fa2431de74a787a8128cd2a58af1e89f962a038532c3f3c3ce69d03d49a` | Successful audit source before annotation correction |
| `bf341ec452bcefef6d9b6fead1547238f50fb2471226c39da1520ed2c5e62c36` | Tests before the review-commit portability edit |
| `935486d16a4d4ccf4dfb88c53f6e5e416d84e497b4fe448ef9faa6095372f6bc` | Report before the review-commit wording edit |

These are exact hash-verified reconstructions, not a claim that source copies
were saved at the original check time. The verifier resolves current bytes,
then exact newline variants, then these snapshots. Newline restoration is
accepted only when the entire saved hash matches; it never changes originals.
This supports Windows and LF-only Git exports while retaining the recorded
CRLF identities. Every source substitution is listed in the new verification
receipt. Original receipt fingerprints over their full source maps are also
checked. Relocated preflight log paths resolve through `receipt_logs` in the
new manifest; machine-specific path strings in old receipts remain unchanged.

## Omitted generated files

The minimal set deliberately omits generated engineering outputs under
`verification/{conversation-data,independent-cases,owned-lm-smoke,pipeline,research-smoke,tables}/`
and the two build files below. The manifest inventories their local sizes and
newly observed hashes without parsing their data. None is a consumed Qwen audit
input or baseline binding. Their original engineering receipts and logs remain
included. Exclusion does not establish that full fixture/build outputs can be
reproduced byte-for-byte; those smokes are separate from this development audit.

| File under `verification/package/` | Local state at packaging | Needed for development audit replay/verification? |
|---|---|---|
| `toruk_lm-0.1.0-py3-none-any.whl` | Present locally, absent from prior commit; deliberately omitted here | No: generated installable wheel |
| `toruk_lm-0.1.0.tar.gz` | Present locally, absent from prior commit; deliberately omitted here | No: generated source distribution |

Thus neither is missing from this isolated working tree. Both will be absent
from a fresh checkout of the portable commit by design. `verify.py --staged`
exports only the Git index and verifies without either file or the generated
fixture directories. No omitted build is treated as a missing required input.
The historical build log records success but contains no original binary
hashes. Newly observed packaging hashes are not retroactive proof of original
build binary identity. The local files are left in place and no build is rerun.

## Verify without opening held-out evaluation

With the existing development/chat dependencies installed, run from the
repository root (use `python` on an appropriately configured environment):

```powershell
.\.venv\Scripts\python.exe artifacts/qwen-long-history-dev-v4/verify.py
.\.venv\Scripts\python.exe artifacts/qwen-long-history-dev-v4/verify.py --staged
git diff --check
```

The verifier checks all included payload hashes, required repository/input
hashes, historical receipt source maps/fingerprints/logs and summary totals.
It materializes exact input bytes into a new disposable scratch directory,
then calls the existing v4 audit API to check native prompts/output decoding,
sources, scorer decisions, token counts, costs and saved replay consistency.
The API preserves the historical baseline identity; the original CLI's
HEAD-equals-baseline guard cannot be used after the audit is committed.

Inherited held-out files covered by the baseline are hashed/copied as opaque
bytes, never parsed or scored. No broad portable-v1 answer verifier is invoked,
since that verifier also rescores other studies' held-out answers. No model
weights are loaded and no generation or held-out execution action is exposed.
The staged export and replay scratch directories are separate from both
existing checkouts. Neither checkout is deleted or modified by verification.
