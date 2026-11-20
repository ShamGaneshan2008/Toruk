# Local-answer accounting engineering record

20 November 2026. Windows-only development engineering, separate from the
immutable answer-trainability-v1 record at
`301dd9edbf12403aa97e5013247d5b1f33be0746`. No v1 controller, predictions, costs,
gates or reports were changed. Its complete-lifetime CPU remains UNKNOWN.

## What changed

The old run branch did not call its final self-receipt function. A polling
watcher therefore could not reconcile the controller's lifetime CPU, and some
short descendant lifetimes were also undercounted. Replacing a missing receipt
after exit would not recover those measurements and was not done.

NEW [lifetime_job.py](../../scripts/lifetime_job.py) creates the workload process
suspended, assigns it to an anonymous Windows kernel Job, then resumes it. All
descendants remain in the Job. After ActiveProcesses reaches0, the observer
queries final accumulated user/kernel CPU and peak Job committed private memory
before closing handles. These counters survive member-process exits. CPU is
measured over whole lifetimes rather than reconstructed from sample maxima.

The new [local controller](../../scripts/local_answer_dev.py) also wraps every
run/worker in a finally receipt containing status, error and CPU-to-receipt.
These self-reports are diagnostic; they are not the authority for lifetime CPU.
An os._exit without a self-report is still accounted by the parent Job. A caught
observer interruption or cap kill terminates and drains the complete Job tree
before saving cost/status. Kill-on-Job-close prevents abandoned child processes.

Every `cost.json` records complete_process_lifetimes, active/total process counts,
return code, stop reason, CPU split, wall, peak memory, disk, sample gap and exact
command. Kernel CPU is authoritative even with coarse polling. Normal completion
does not require a worker receipt to be found at a guessed path. Failed child
exit remains STOP, with complete lifetime accounting rather than a guessed zero.

## Measurement boundary

For the registered run, the enclosing Job contains the run controller, all
workers, launchers, transient descendants and inner stage observers. Stage Job
costs are subsets of that enclosing total, not additional costs. The outermost
observer is outside the measured Job; its CPU-to-receipt snapshot is separate
and is not described as its complete lifetime. Design/editing/analysis outside
the Job is not claimed free or included in a complete project total.

This boundary was declared before training. Complete registered workload CPU is
103.500000 seconds, including its controller and all65 process lifetimes, with
zero active descendants after closure. User CPU92.328125 + kernel11.171875;
wall104.515580. The enclosing [receipt](../../artifacts/local-answer-dev-v1/execution/cost.json)
is PASS and has a matching
[controller-final receipt](../../artifacts/local-answer-dev-v1/execution/controller-final.json).
The outer observer's6.453125 CPU-to-receipt seconds is reported separately.
This does not repair or reclassify v1's old unknown lifetime cost.

## Tests and retained failed executions

[Seven real-process tests](../../tests/test_lifetime_job.py) cover:

1. Successful controller, finally receipt and kernel closure.
2. Failed controller exit, finally receipt and complete CPU.
3. KeyboardInterrupt in the controller, retained failure metadata and closure.
4. Abrupt os._exit without a self-receipt, still complete kernel accounting.
5. Time-cap termination while descendants are alive; entire tree drained.
6. Observer interruption with a live tree; entire tree drained.
7. CPU-burning child outliving its parent, under400ms polling; final CPU retains
   its approximately200ms work even though sample-only accounting could miss it.

All passed. The two initial accounting suites and the pre-freeze combined
contracts retain21 individual scenario receipts outside disposable pytest caches:
[case index](../../artifacts/local-answer-accounting-v1/retained-test-cases/cases.json).
Six are successful scenarios;15 are intentionally failed/interrupted/capped
executions that the tests require to remain STOP. All21 have complete lifetimes
and zero active processes. Original stdout, raw resource traces and final records
are copied beside each cost. The initial normal-exit probe is also retained.
These are engineering fixtures, not model fits or factual predictions.

Combined pre-training contracts:11 passed (seven accounting and four static/
numeric local-answer contracts), complete Job CPU4.562500/wall5.954813 seconds,
peak681,668,608 bytes. The numeric rehearsal used no study inputs or optimizer
updates and passed its fixed projection. All receipts precede the new study
registration. Later29-test verification is separately recorded in the results.

Reproduce tests only in a FRESH workspace directory (Windows; no study rerun):

```powershell
Set-Location D:\Toruk
.\.venv\Scripts\python.exe -B scripts/lifetime_job.py --directory artifacts/local-answer-accounting-review/execution --root artifacts/local-answer-accounting-review --seconds 30 -- .venv/Scripts/python.exe -B -m pytest -q tests/test_lifetime_job.py --basetemp artifacts/local-answer-accounting-review/pytest-tmp -o cache_dir=artifacts/local-answer-accounting-review/pytest-cache
```

The implementation uses native Windows Jobs and the tests require a workspace
basetemp; no Linux execution support or unfiltered cross-platform suite pass is
claimed. A forcibly killed measurement observer cannot write a final JSON after
its own death; kill-on-close still bounds descendants, but no such case is
advertised as a valid receipt. The tested interruption path is caught and drained.
