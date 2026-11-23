# Monitor sealing v2: observer-owned finalization

23 November 2026. Harness-only follow-up to paired-batch v1. No research
checkpoint is used in the tests, no model is constructed or fitted, and no
paired-batch worker is rerun. The new harness remains uncommitted.

## Evidence preservation and diagnosis

Evidence commit:392e002caa203d17a837fde7e759187e59a81301.
It preserves335 files and the v1 failures without changing the original seals.
Training mastery failed; development was NOT RUN. Ordinary947 paired90/96 versus
city-shuffled92/96. Independent verification is not a full registered PASS.
Twelve checkpoint hashes/sizes are committed; weights remain ignored and local.

The defect is in scripts/paired_batch_dev.py observations(): it writes
observation-seal.json inside the worker, including resources.jsonl. The parent
lifetime_job.watch() still owns and appends that journal until the worker exits.
The worker's controller-final receipt and the observer's final cost also belong
after worker observation writing. All12 v1 stale journal digests match exact
prefixes, but their original seal validation still fails. No v1 bytes are repaired.

## New lifecycle

scripts/lifetime_job_v2.py adds a separate API and schema:
toruk-observer-owned-seal-v2. It reuses the unchanged Windows kernel Job accounting
in lifetime_job.py; it changes ownership and timing of sealing, not model behavior.

1. The observer calls watch_and_seal() with a fresh output directory.
2. Existing watch() starts the suspended process in its Job, monitors descendants,
   and on normal exit, failure, timeout or interruption drains the entire Job.
3. watch() closes its stdout/monitor streams and all process/Job handles, records
   final kernel counters, and writes/closes cost.json before returning.
4. Only then does the observer validate complete lifetimes and zero active
   processes, take two matching file snapshots, and exclusively write/fsync/close
   observer-seal-v2.json.
5. Read-only verification checks the final receipt, exact file membership,
   sizes and SHA-256. A caller may also supply the returned seal digest to detect
   mutation of the seal itself. The digest should be retained in a higher-level
   immutable inventory.

No worker is responsible for the observer seal. There is no monitor writer after
watch() returns. The output directory must be observer-owned, without unrelated
external writers. Paths must stay inside the checkout; symlinks/junctions and
unreadable output directories are refused.

A failed/timeout/interrupted workload retains partial output and its final cost.
Its snapshot can verify while workload_status remains STOP. Verification of
retained bytes does not convert workload failure into success. Missing/incomplete
receipts cannot be sealed. If sealing itself fails or is interrupted, partial
seal/output bytes remain and observer-sealing-failure-v2.json records the failure;
verification refuses such a run. Existing output directories and seals cannot be
overwritten or resealed. Nothing is automatically repaired or deleted.

## API and CLI

New drivers call the observer API, not a worker callback:

~~~python
from lifetime_job_v2 import watch_and_seal, verify_seal

# command is a list of arguments; directory must be fresh and below root.
result = watch_and_seal(command, directory, root, seconds=5)
verify_seal(directory, expected_seal_sha256=result.seal_sha256)
# Check result.cost["status"] separately before accepting workload success.
~~~

The CLI accepts run/verify. Put the child command after --. The same exit
convention preserves STOP as a nonzero run result. This addition does not
retrofit or authorize rerunning frozen v1. Future study drivers must explicitly
adopt the v2 observer call.

## Disposable validation

24 focused tests passed (17 v2 tests plus7 existing process-accounting tests):
normal exit; failed and abrupt exit; timeout and observer interruption with
descendant cleanup; a late descendant stdout/payload write after its parent
exits; stable hashes after sealing; same-size payload mutation; monitor/receipt
mutation; added/deleted disposable files; trusted seal-digest mismatch;
overwrite refusal; missing and unclosed receipts; interruption during seal
publication; and both CLI paths. No research checkpoint/model input is involved.

The test Job completed in2.406250 CPU/6.992946 wall seconds,0 active descendants,
57860096-byte peak Job commit. All negative fixtures and partial records remain.
Some fixtures intentionally contain invalidated seals to prove mutation detection;
their preserved state should not be described as successful workloads.

Focused mypy checking, repository Ruff lint/format and git diff --check are
recorded with the validation artifacts. New sources/tests and this note are
uncommitted. Existing v1 source, payloads, journals, cost receipts, gates and seals
remain unchanged. No held-out data, production-chat change, deployment or push.

See [validation checks](../../artifacts/local-answer-monitor-sealing-v2-20261123/checks.json)
and [test log](../../artifacts/local-answer-monitor-sealing-v2-20261123/tests-execution-001/output.log).
Use a fresh --basetemp if independently repeating the disposable tests; do not
reuse the preserved validation directories.
