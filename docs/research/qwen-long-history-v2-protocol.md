# Qwen long-history v2: development rehearsal and proposed registration

This is a separate bounded attempt, not a repair of qwen-long-history-v1.
V1 is BLOCKED with zero held-out cases completed in every arm. Preserve all its
files, elapsed time, failed preflight and unknown accounting. Historical M6 is
unchanged. Only development rehearsal is authorized in this stage of work.
The final proposal and hashes will be written to proposed-freeze.json after
rehearsal; no held-out execution command is implemented by this new controller.

## Evidence-based diagnosis, before new inference

V1 execution-v2 TORUK stage cost: 1255.8010113 wall seconds, 25.0625 recorded
CPU seconds, including 3.734375 controller CPU seconds. This is the entire cold
stage, not one selection call. One saved request completed in 3.2966687 wall /
7.046875 CPU seconds; its selector used 0.2159237 wall / 0.859375 CPU seconds,
2806 byte positions and 65 recurrent forwards. Generation used 3.0603819 wall /
6.109375 CPU seconds. Progress shows the next correction request was active.
Its partial work has no completed row and remains charged at stage level.

Saved Windows Power-Troubleshooter sleep/wake timestamps span 1250.159606
seconds. Kernel-Power reports System Idle; a clock resynchronization reports
1240.753 seconds. These are different clock observations, not interchangeable
stopwatches. They support suspension as the dominant elapsed-time cause, not
1255 seconds of selector computation. No exact awake-time or unsaved second-call
duration can be reconstructed. CPU is multicore process time, not elapsed time;
the terminated worker lacks final lifetime CPU, so sampled CPU can undercount.
Never subtract sleep from v1 or change its failed resource prerequisite.

## Fixed identities, questions, mechanisms, scoring

Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`; safetensors SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
Every model/tokenizer file must match the D-drive qualification registration.
Successor selector SHA-256
`f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49`.
This is the existing recurrent/cosine selector, not historical M6 or the v2
logistic selector. No training, ranking, cutoff or evidence-envelope change.

Use the exact hash-bound D-drive v1 worker and dependencies (Python 3.12.14,
Torch 2.15.0+cpu, Transformers 5.22.2, Tokenizers 0.23.3, Safetensors 0.8.0,
Psutil 7.2.2). Bind all consumed sources and paths, and verify before execution.
All four arms share original role/content, qualification system instruction,
native Qwen template and chronological Reference/Question/Answer envelope.
Full includes all turns (766-828 original input tokens, native window 32768
including 64 reserved output positions). Recent/lexical-v1/TORUK fit whole turns
to 512 prompt tokens including wrappers. Record proposed and final indices,
source text, prompt messages/IDs, output IDs, answer, frozen score and errors.
CPU float32, two Torch threads, seed 81751, greedy, one beam, repetition penalty
1, KV cache, temperature request 0, top-p 1, 64 generated-token maximum.

Intentionally inherit the seven v1 development cases and the 28 v1 held-out cases
byte for byte. This is a new execution attempt on an untouched held-out set,
not independent data or a new generalization replication. Development is already
observed and is used for runtime validation only. No quality-based tuning or
case/scorer edits. Four held-out cases each: distant facts, corrections,
distractors, exact strings, preservation, references and missing information;
22 known / six UNKNOWN, including two ambiguous references. Full and bounded
arms receive identical questions. Recheck IDs, known values and normalized
questions between splits and against all recorded prior JSON/JSONL sources.
Explicitly disclose the intentional v1/v2 identity overlap. Exclude v1 copies
only from the independence assertion; never hide them. Retain scan file hashes,
skips and literal/semantic/pretraining limitations. No held-out generation or
scoring is permitted during this task. Hash/overlap checking labels is offline.

Reuse the exact v1/qualification scorer. Literal whole-answer comparison
preserves internal spaces; report exact copying and preservation independently.
UNKNOWN/ambiguous matching, negation, competing values and stale/unsupported
proxies remain fixed. Preserve raw failures; no post-hoc scorer repairs.

## Bounded rehearsal and limit selection

Seal this document, config, controller, tests, input sources and diagnosis before
inference. Fresh output namespace in the writable C-drive checkout; D-drive
inputs remain read-only. Run four sequential fresh workers in full, lexical,
TORUK, recent order, seven development cases plus first-case replay per arm.
No quality filtering. Each arm must complete with deterministic replay and zero
execution/resource/interruption errors to propose held-out readiness.

Predeclared rehearsal caps: 180 wall seconds / 360 CPU seconds per arm;
720 cumulative wall / 1440 cumulative CPU seconds; 30 wall seconds per request;
6 GiB worker-tree private memory; 3 GiB new study plus fixed model/checkpoint
inputs, excluding environment. All selection/fitting/generation/serialization,
startup, hash checking, controller monitoring and failed/partial work is charged.
Rehearsal stops at the first failure. No automatic stage or model retry.

Derive held-out limits without looking at held-out answers. For each arm,
proposed wall cap is twice (observed eight-request cold stage wall plus 20 times
the maximum observed request wall), floored at 120 seconds, rounded UP to 30.
CPU analog floors at 240 and rounds UP to 60. This conservatively scales from
8 to 28 requests using the slowest development request plus 2x headroom; it
does not guarantee unseen lengths/output behavior. Reject any proposal above
600 wall / 1200 CPU seconds per arm rather than silently enlarging it.
Proposed cumulative caps equal actual charged rehearsal totals plus the SUM
of all four held-out arm caps, separately for wall and CPU. Keep the same request,
memory and disk caps. Seal observed extrema, derivation, exact limits, all raw
development outputs and sources in proposed-freeze.json before any held-out work.
Stop for user review here; this proposal does not authorize held-out generation.

## Interruptions, sleep, timeout, retry and accounting rules

Acquire and verify Windows SetThreadExecutionState(ES_CONTINUOUS |
ES_SYSTEM_REQUIRED) on the controller thread before launching any worker.
Restore ES_CONTINUOUS in finally; no persistent/global power-policy change.
Failure to acquire is BLOCKED. This prevents idle sleep, not user-forced sleep,
power loss or all scheduling interruptions.

Record UTC, perf-counter/monotonic elapsed, Windows unbiased interrupt time
(excludes sleep), CPU, process-tree memory, active request and heartbeat gap.
Sample approximately every 50 ms; flush heartbeat JSONL at least every second.
Use the larger of UTC and perf-counter elapsed for charged stage wall, with
no subtraction. A monitor gap above five seconds OR elapsed minus unbiased
awake time above two seconds invalidates the attempt as an interruption.
These conservative diagnostics need not prove sleep; retain uncertainty and
Windows events when available. Treat clocks moving backwards as invalid.
Caps remain real elapsed-time caps and include suspension. Watchdogs cannot
run while the host sleeps; terminate immediately when execution resumes.

On timeout, interruption, identity mismatch, monitor exception or cancellation:
terminate all known worker descendants, wait, preserve raw/partial files, write
failure, last active request, start/end clocks, sampling coverage and known
CPU/memory. Never manufacture missing answers as zeros or omit them from the
completion denominator. No worker/request/held-out retries. At most five
progress-file PermissionError reads 10 ms apart; log every read retry and charge
the delay. Interrupted output is append-preserved, never overwritten or resumed.
Power loss can prevent finalization: a durable started marker without completion
means INVALID/INCOMPLETE, not PASS; salvage heartbeats read-only and report CPU
as a lower bound. Any future retry needs a separate approved registration and
retains/charges the failed attempt; no fresh budget by changing a directory name.

CPU: controller process time plus sampled descendant maxima, supplemented by
worker final lifetime CPU where available. Missing final telemetry is disclosed
as incomplete, never exact. Record sampled RSS/private peaks, sum of observed
per-process OS lifetime peaks (may overestimate simultaneous tree peak), worker
OS peaks, cold setup, request, selection, fitting and generation separately.
RSS can double-count shared pages; 50 ms sampling can miss short peaks.
Do not infer total resource efficiency from selected-prompt tokens.

No new training. Carry forward measured successor profile/training once:
14.578125 CPU / 17.6733196 wall seconds, amortized over planned N=28 held-out
queries (0.520647 CPU / 0.631190 wall seconds/query). Original training peak RAM
is unknown. N=1000 is arithmetic sensitivity only. Primary per-arm total is this
v2 arm's rehearsal including replay + held-out cold stage + all failed/partial
attempts; TORUK adds training/profile. Shared preparation/checking overhead is
reported separately and allocated equally in a secondary total. Also disclose
all v1 sunk work separately: its incomplete CPU prevents an exact all-history
efficiency claim. Never discount host sleep in either ledger.

## Held-out plan and registered success criteria

Future authorized run order: TORUK, recent, full, lexical. One pass each over
the exact 28 questions; exclusive start/output guards and sealed dev/input
hash verification. No held-out worker may start until a separate execution
authorization and reviewed proposed-freeze identity are present. Current
controller exposes only prepare, rehearse and freeze-proposal actions.

Primary comparator is lexical. Report paired wins/losses, per-category and known
accuracy, exact-copy/preservation, evidence omission, downstream generation
failures, unsupported/stale proxies and errors. Preserve every question, prompt,
source, answer and score. Use 10000 paired case bootstrap draws, seed 82951,
for a descriptive 95% percentile interval on TORUK-minus-lexical accuracy;
include exact discordant counts and two-sided exact McNemar p-value. Synthetic
shared templates/small sample limit population inference. No positive claim if
the interval includes zero; distinguish that uncertainty from numerical gates.

Carry forward all v1 conjunctive numerical gates: all four arms complete within
caps; full AND TORUK >=17/28 overall and >=14/22 known; TORUK loses at most one
overall case (five percentage points) and at most one case per category versus
each other arm; no increased stale/unsupported proxy versus any arm; complete
charged CPU AND wall at least 10% lower than both lexical and recent. Report
every gate separately. Runtime rehearsal success is not a quality/efficiency PASS.
No hosted CI, deployment, commit, push or publication is authorized here.
