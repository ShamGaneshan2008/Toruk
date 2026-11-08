# Frozen M6 selector provenance — 8 November 2026

**Verdict: NOT FOUND in the searched material. Fresh frozen M6 reproduction:
BLOCKED.** The recorded hash identifies raw checkpoint bytes. It is not a package
hash, normalized representation or recoverable line-ending variant. No replacement
was trained, no expected hash changed, and no candidate was labeled original.
This does not prove the file is absent from an unconnected original device or backup.

## Starting state and preservation

The first read observed `main` at `1d723b1ddf974e12014fdfe0ae4c6a99e68619b6`.
`git status -sb` showed five modified tracked files (`.gitattributes`, `.gitignore`,
README, architecture and experiment registry), the core-advantage evidence/report,
and its new audit script/tests. While read-only searches ran, HEAD advanced
externally to `adb812faeae87ce9df199b8e2faff77f00a8bd61`, incorporating that work.
The pre-edit status at that commit was clean. No commit, reset, checkout, stash,
fetch, push, deployment or publication was performed by this investigation.

[starting-state.json](../../artifacts/m6-provenance-20261108/starting-state.json)
records both observations and hashes the previous core-advantage evidence files
before edits. That evidence directory, previous auditor/tests and report were
preserved. New evidence has its own directory:
[artifacts/m6-provenance-20261108](../../artifacts/m6-provenance-20261108/).

## Identity and what was hashed

Expected checkpoint SHA-256:

```text
479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d
```

Recorded path: `artifacts/m6-validation-001/recurrent/checkpoint.pt`.
Four current bindings agree: training `recurrent/metrics.json`, run
`manifest.json`, M6 handoff `manifest.json`, and chat-release `raw.json`.
The same binding appears in M6 evaluation/label files, M7 protocols/metrics,
later archived audits, chat-selector regression and deployment recipes.
The complete line search is retained in `references.json` (627 matching lines,
with unreadable-file diagnostics); `git-object-search.json` additionally identifies
58 distinct historical Git blobs mentioning the hash. These are references,
not 58 copies of the weights.

The archived creation command was:

```powershell
.\.venv\Scripts\python.exe -m toruk_lm controlled-pilot --output artifacts/m6-validation-001 --steps 12 --worlds 4 --answer-budget 16 --seconds 110
```

Its retained wrapper, `artifacts/checks/m6-registered-pilot.json`, records PASS,
start `2026-10-20T16:24:02.702951+00:00`, 90.9345702 s, and source identity.
This historical command was inspected, **not rerun**. The wrapper and exact
hashing/saving source excerpts are retained in `historical-creation.json`.

The M6 source archive is separately identified as:

```text
artifacts/m6-handoff/source.zip
def3d8be4f380f92bf2ae7e2a3ef4b8675f4576f08fd859258da3a2f9f53710d
```

Its bytes match the sealed handoff. Its `data.py`, `controlled.py` and
`comparisons.py` member hashes also match the handoff source manifest. They show:

```python
temporary = output / "checkpoint.pt.tmp"
torch.save(saved, temporary)
temporary.replace(output / "checkpoint.pt")
# The metrics and completed-run manifest both hash this resulting file.
checkpoint_sha256 = sha256_file(output / "checkpoint.pt")

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

The saved dictionary contains model and optimizer state, Python/Torch RNG state,
configuration, tokenizer identity, data identities, next step, checkpoint format,
resume boundary and package identity. The checkpoint digest covers **all serialized
bytes**, not only model tensors. The selector constructor independently uses
`hashlib.sha256(checkpoint.read_bytes())`; the chat evaluator's chunked binary
hash is equivalent. There is no text decoding, canonical JSON or newline conversion.

The separate package fingerprint is
`d59cb1e1ebc32f0affe9e87b2e5365b7212b8ae641c545a326d7c80493d1cd95`.
It hashes a JSON representation of source-file digests; it is not the checkpoint
identity. ZIP archives and individual members have their own different hashes.
The M7 source archive likewise has a distinct hash
`41933d7390f8cc75231bc937bd33e4526846a51aa7e3a75005a0a0c815151e04`.
Both source archives contain source files, **no `.pt` weights**.

Moving/renaming or byte-copying an existing checkpoint does not change its hash.
Reserializing it can change its bytes, including archive structure, metadata or
serialized source identity; equal tensors are not proof of the original file.
Line endings matter to text fixtures and source/package fingerprints. They
cannot be normalized in this binary checkpoint to justify changing its digest.
The CRLF issue recovered in the earlier evaluation fixture is a separate issue.

## Search coverage and candidates

| Location | Observed result |
|---|---|
| Current checkout, including ignored `.readiness` and private/local artifact directories | 547 checkpoint-like `.pt`, `.pth`, `.ckpt`, `.bin` or `.pt.tmp` files hashed; no match |
| Local archives and explicit Downloads/Desktop/Documents archive candidates | 103 archives inventoried; 10,283 members hashed during normal search; no match |
| Two initially unreadable package archives | Read-only approved retry hashed both; source distributions with no checkpoint members |
| Primary Git database | All 4,571 blobs / 126,773,443 payload bytes hashed, including unreachable and reflog-only objects; no match |
| Historical Git archives | 21 archive blobs / 1,668 members hashed; no match |
| Nested `.readiness` repositories | Two checkouts each have 4,419 already-hashed blobs; one empty-history probe adds one unique nonmatching blob |
| Reachable refs | `main`, two backup branches, `origin/main`; no local tags or stash |
| Git LFS | Installed system filters, but no repository LFS configuration/storage, LFS-managed files or pointer blobs |
| Documented `C:\Users\susee\VScode Project\Toruk` | Path does not exist on this device |
| Remote refs/releases | Only `main`; no tag refs or releases |
| Hosted artifacts | All 29 listed workflow runs inspected; every run's artifact listing is empty |
| Original Intel training device / other backups | Not connected; not searched remotely |

The file walk excludes environment/library directories (`.venv`, `venv`,
`review-env`, `site-packages`, `node_modules`, `__pycache__`) and handles `.git`
separately through object scanning. It does not follow directory symlinks.
Large or unrelated external archive members were listed without content hashing;
member lists, limits and exceptions are retained in `local-search.json`.
No whole-drive or deleted-file forensic recovery is claimed. The nested checkout
called “Two Device Checkout” is a local test copy, not a connection to the other device.

Raw archive and candidate hashes are in
[local-search.json](../../artifacts/m6-provenance-20261108/local-search.json),
[git-object-search.json](../../artifacts/m6-provenance-20261108/git-object-search.json),
`nested-git-search.json` and `restricted-package-search.json`. Representative
nonmatching files:

| Candidate | Actual SHA-256 |
|---|---|
| Ordinary foundation `artifacts/foundation-001/train/checkpoint.pt` | `0285d3fb6adc4e49a92b6c2f4f8226f607d8660d46d3a19d5fea33ca48065e94` |
| Prior audit's recurrent smoke `verification/research-smoke/recurrent-full/checkpoint.pt` | `33b835fd3eb2ef6874fbe3b730033930a7695e7b92c9999f876fed3bffe3e2e1` |
| Owned conversation candidate | `af3eecde26139c11e1dd7c40f89a3bd5510cbbabad762b6a049106c91ae22e66` |
| `.readiness/dist/toruk_lm-0.1.0.tar.gz` | `c309a722218a28d4187b7819fbf26542e0e7b4bedb619233ee690f8db80c3660` |
| `dist/toruk_lm-0.1.0.tar.gz` | `6e21b7b72b254b54af6d713356ed20f423e567daf53ea738890de17cdbe5e09c` |

Git `log --all` never records a checkpoint path as tracked. The first dated M6
evidence commit is `d64093c89f892816d29edc1e7f9a3ac00cf6aed3` on October 20;
`.pt` files were already ignored at its recorded base `a025f01`. This supports
an untransferred Git-ignored artifact explanation. It does not establish whether
the original is still on another device, was deleted, or was never backed up.
No matching bytes were recovered from dangling Git objects.

Direct GitHub artifact/tag collection calls unsupported by the connector were
retained as errors, then replaced by supported tag-ref and per-run artifact
queries. All 29 available runs fit the single 100-run page; the artifact wrapper
is first-page-only, but each returned an empty list. Deleted/expired historical
artifacts cannot be ruled out. No storage URL or artifact transfer reference for
the original weights was found in the inspected documentation/workflows.

## Reproduction outcome and conditional recovery

The new `scripts/verify_frozen_m6.py` cross-checks the four bindings and immutable
source archive. A missing or nonmatching candidate exits 2 **before deserialization**.
A hash-matching candidate must additionally pass the existing weights-only loader:
`toruk-controlled-v1`, drained-document boundary, byte tokenizer, recurrent model,
four slots, width 32, two layers/four heads, QA config, recorded train/validation
identities, 12 completed steps, 57,088 parameters and recorded package fingerprint.
It changes neither runtime selection nor the original expected identity.

The preflight here reports `MISSING`, reproduction `BLOCKED`, exit 2. The
original strict CLI was also run without changing its protocol:

```powershell
.\.venv\Scripts\python.exe -m toruk_lm verify-m6 --parent artifacts/m6-validation-001 --handoff artifacts/m6-handoff --output artifacts/m6-provenance-20261108/attempted-strict-replay --seconds 110
```

It exits 2 with **`M6 inference/scoring source mismatch`**, before inference.
Both blocked checks are retained as wrapper FAIL records with the expected
underlying exit 2, not represented as passing scientific reproductions.
Restoring this one selector would enable its isolated checks, but full M6 replay
also needs the other model/predictor files recorded in the original manifest.
Archived kernels must be verified and used in isolation; the source gate remains.

On **each device**, if an owner-held backup is located, use a fresh verifier
output before copying it. This is a conditional procedure; it was not performed:

```powershell
$source = 'D:\Toruk-backup\checkpoint.pt' # Actual existing owner-held backup
.\.venv\Scripts\python.exe scripts/verify_frozen_m6.py --checkpoint $source --output artifacts/recovered-m6-candidate.json
if ($LASTEXITCODE -ne 0) { throw 'Original identity/compatibility not verified' }
$destination = Join-Path (Get-Location).Path 'artifacts\m6-validation-001\recurrent\checkpoint.pt'
if (Test-Path -LiteralPath $destination) { throw 'Preserve the existing destination' }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
Copy-Item -LiteralPath $source -Destination $destination
.\.venv\Scripts\python.exe scripts/verify_frozen_m6.py --checkpoint $destination --output artifacts/restored-m6-candidate.json
if ($LASTEXITCODE -ne 0) { throw 'Copied checkpoint verification failed' }
```

Transfer the **same binary file** and verifier/source evidence by an owner-chosen
backup method, verify independently on both devices, retain the origin path,
transfer date, size and hash, and avoid `torch.save` or text transfer. This does
not authorize an upload. No canonical checkpoint, handoff hash or expected hash
should be overwritten to accommodate a candidate. Original M6 inference must use
the sealed source archive, original validation data/answer budget/policies and
compare generated IDs, answers and scores to the archived outputs. Reuse neither
current kernels by assumption nor a newly trained checkpoint as an original.

Archived M6/M7 outputs and the 6/20 SmolLM/TORUK result remain historical evidence.
The previous audit's fresh BASELINE parity and current bounded smoke tests are
separate reproducible work; neither is a fresh reproduction of original M6 weights.

## Newly versioned experiment plan — not executed

If original-device recovery also fails, register **`m6-successor-v1`** in a fresh
artifact namespace. Its purpose is a new controlled measurement, not restoration:

1. Freeze current source plus the patch, dependency versions, data generator,
   protocol and provenance schema. Declare random initialization and a new
   experiment/checkpoint identity; never assign the historical hash to its output.
2. Begin with the documented small architecture/budget: width 32, two layers,
   four slots, context 64, 12 optimizer steps, CPU, one thread, 110 s stage cap and
   3 GiB process-memory stop. Profile first; stop on a cap failure. This is a
   proposed bound; no successor training ran here.
3. Treat published M6/chat questions as regression data. Author and seal a separate
   development split and untouched held-out split, with disjoint values/templates
   and explicit leakage checks, before fitting or selecting a change.
4. Register matched recent-context, lexical-retrieval and new-selector comparisons
   with the same pinned backbone, prompt/output budgets and greedy decoding. Count
   full-history tokenization, selector/memory work, generation, CPU/wall latency and
   per-system peak memory, including setup turns and failed attempts.
5. Freeze after development, then evaluate held-out once. Proposed gates: baseline
   and candidate quality at least 60%; candidate no more than five percentage
   points worse; no increase in unsupported assertions; at least 10% lower total
   request CPU **and** wall time. Declare uncertainty and device-specific results;
   a prompt-token reduction alone cannot pass. Final registration must lock these
   gates before seeing new results.

Nothing in this plan changes the archived M6 protocol or upgrades its status.

## Checks and changed files

Exact commands/results are in `checks/*.json` and `verification/*.json` with
source identities and logs. Principal commands:

```powershell
.\.venv\Scripts\python.exe artifacts/m6-provenance-20261108/search_local.py
.\.venv\Scripts\python.exe artifacts/m6-provenance-20261108/search_git.py
.\.venv\Scripts\python.exe scripts/verify_frozen_m6.py --output artifacts/m6-provenance-20261108/frozen-selector-status.json
.\.venv\Scripts\python.exe -m pytest -q tests/test_frozen_m6_provenance.py tests/test_chat_advantage_audit.py tests/test_chat_release_eval.py
.\.venv\Scripts\python.exe -m mypy src/toruk_lm scripts/verify_frozen_m6.py
.\.venv\Scripts\python.exe -X utf8 scripts/verify.py --prefix m6-provenance --output-dir artifacts/m6-provenance-20261108/verification
git diff --check
```

The focused suite passes 17 tests, including raw-byte/path semantics, metadata
binding consistency, rejection of rewritten hashes, and refusal to deserialize
missing/different candidates. The initial standalone script-only mypy command
reported `import-untyped` because the installed package lacks `py.typed`; it is
retained. The source-inclusive command above is the relevant type check.
The source-inclusive command passes **36 source files**. Full `scripts/verify.py`
completed with exit 0, **26/26 stages PASS**:

| Local check | Result |
|---|---|
| Python suite, including page → Node → Python HTTP fixture integration | 274 passed in 164.27 s |
| Node syntax/tests | PASS; 20 passed, 1 opt-in live-page test skipped |
| Ruff lint/format | PASS; 144 Python files formatted |
| Default/Windows and Linux-target package mypy | PASS; 35 source files each |
| Source-inclusive new verifier mypy | PASS; 36 source files |
| CLI, install/import/package, frozen-source and data/leakage validation | PASS |
| Bounded owned/foundation/research smokes, resume/validation/generation | PASS |
| Source/wheel build and working/staged diff checks | PASS |

Verification trained only its existing tiny smoke fixtures in the new output
directory. It did not retrain M6. Smoke completion is operational success, not
an M6 research gate pass. The one skipped opt-in live-page test is not a browser
validation claim. The two expected blocked commands remain separate from these
passing checks. The final preservation check found **168 prior evidence files
unchanged**.

The existing GitHub Actions workflow was inspected: Node 22 syntax/tests,
Ubuntu Python 3.12 static checks, pytest/HTTP fixture integration, data/leakage
validation, bounded reproducibility smokes and package build; Windows additionally
checks smoke reproduction from a path with spaces. New pytest checks will be
collected by that suite when the new source is eventually included in a run.
Hosted [run 42462502160](https://github.com/ShamGaneshan2008/Toruk/actions/runs/42462502160)
was observed **completed/success** for `adb812faeae87ce9df199b8e2faff77f00a8bd61`.
It covers the externally committed prior audit, **not these new uncommitted
provenance changes**. The historical M6 evidence commit had no listed workflow
run. Neither hosted CI nor smoke checks recover the missing historical weights.

Changed files: the new candidate verifier, its four tests, this report,
reproducibility guide, experiment registry, evidence attributes/package ignore
rules and the new provenance evidence directory. Existing selector/model code,
frozen protocols, expected hashes and old evidence files were preserved.

**One next action:** run the exact candidate verifier against the owner-held
original training-device checkpoint/backup. That unconnected device is the
remaining recovery location with direct provenance to the historical run.
