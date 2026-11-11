# Portable evidence-first prototype record

This record preserves rehearsal-001 and the separate feasibility-v2 resource
stress check. **Synthesis did not meet readiness:** four earlier outputs omitted
the first premise, and all 12 forced 64-token continuations were abstained.
Source-linked unit tests establish the bounded validator's behavior, not natural
LM synthesis readiness. The 48-case study remains **unregistered and unrun**.
No policy, learned-selector, stable-efficiency, novelty or deployment claim is
supported. Original decision/contribution/stop gates are unchanged.

The adjacent `manifest.json` lists every included file and SHA-256, repository
dependency, archived source resolution, declared omission and inspected local
artifact exclusion. Original registrations, seals, raw outputs, costs, failure
fields and verification receipts retain their original bytes and paths. The
two small `source.zip` files are frozen provenance archives, not generated
distribution packages: they preserve as-run source identities across checkout
line endings and source revisions. Historical reports' references to an
uncommitted prototype describe the state when those reports were written.

From the repository root, run:

```console
python scripts/verify_evidence_first_record.py verify
python scripts/verify_evidence_first_record.py verify --staged
```

The default check uses the repository's already published Qwen tokenizer under
`artifacts/research-evidence-portable-v1/tokenizers/qwen`, with Transformers
installed. No external model weights, original Windows directories, network,
model generation or training are needed. `--no-native` is a standard-library
hash/structural check and explicitly skips native token/decode, BPE budget and
full offline policy replay checks. `--root` can point to a different checkout.
The frozen experiment launchers preserve their original machine paths; this
portable verifier is the supported offline review entry point. Re-running
either frozen experiment is not authorized by preserving it.

Unchanged repository dependencies can have different Git checkout line endings.
The verifier may reconstruct LF/CRLF bytes for those dependencies only, accepting
them only if the complete bytes match the recorded SHA-256 exactly. It reports
the number of reconstructions. Original experiment files, archives, prototype
code, reports and all newly included files use strict byte comparisons without
this fallback. No file in the checkout is rewritten by verification.

Included are all 40 rehearsal-001 and 12 feasibility-v2 raw request rows, their
inputs, source/coverage manifests, native IDs, cold/shared/component costs,
setup/worker/progress records, original source archives, synthesis audit,
output seals, decision/protocols/reports, prototype code/tests, and original
top-level verification JSON/log receipts. Failures and abstentions are retained:
no failed synthesis output was removed. Runtime/integrity checks completed, but
that does not erase the synthesis readiness failure.

Excluded, with each actual file's path/hash/size/reason in `manifest.json`:

| Exclusion | Reason and retained record |
|---|---|
| Generated wheels/sdists and package directories | Rebuildable distribution outputs; original build log/receipt retained. Their binaries are not verified by this record. |
| Disposable conversation, independent-case and owned-LM smoke fixtures | Unrelated repository verification inputs/outputs; original check receipts retained. Inventory is byte/hash metadata only, not held-out case inspection. |
| Generated pipeline/research-smoke checkpoints, data, predictions and tables | Unrelated verification artifacts; original checks and their results retained. No benchmark data are added. |
| Caches, bytecode, temporary files and environments | Rebuildable local runtime state; no evidentiary role. Existing repository cache/environment ignores remain in effect. |
| External model/selector weights | Original hashes retained; not bundled or needed for offline output verification. No inference/reproduction claim for omitted weights. |
| External tokenizer/model support copies | Existing published tokenizer bytes are reused by hash where available; remaining external files are declared omissions. |
| Missing historical verification-source revisions | Original recorded hashes/receipts retained and each unresolved reference declared. A receipt is not proof that an unavailable historical source revision was reverified. Essential experiment bindings must resolve or be an explicitly omitted runtime asset. |

Excluded generated files remain local and ignored; they were not deleted.
Tracked production and v1-v5 evidence are unchanged. The portable inventory
never creates study cases or evaluates the original accuracy/contribution gates.
The recorded resource caps remain proposals only. Current preservation checks
are separate from the historical experiment costs, and no new model requests
were run to prepare this record.

The root `.gitattributes` remains byte-identical to the older portable evidence
manifest. Scoped attribute additions preserve existing v5 rules and apply only
to this prototype and the attribute files themselves. The root
`.gitignore` adds seven narrow generated-output exclusions; it is listed as
reviewed commit metadata outside the record's byte inventory, since Git may
convert its checkout line endings. Exact metadata/source bytes needed by
historical receipts are separately retained by hash where available.
