# Qwen long-history v2: diagnosis, development rehearsal and frozen proposal

9 November 2026. **Development runtime gate: PASS. Held-out evaluation: NOT RUN.**
This is a proposed execution protocol, not a selector quality or efficiency PASS.
Toruk's development accuracy is 1/7 against lexical's 7/7. No improvement is
established, and no mechanism, data, scorer or success gate was changed after
these answers. Work stops before any held-out generation.

## Checkouts and preservation

Current directory/Git root: `C:/Users/susee/VS_CODE_PROJECT/Toruk`, initially clean,
commit `25d4ec09e01397b43b9b16ad08faeca7cdb22eb0`. The scientific inputs and
uncommitted predecessor work remain in the separate `D:/Toruk` checkout at the
same commit. No D-drive file was copied over a C-drive source file or edited.
New code, protocol and evidence have distinct v2 paths in the writable C checkout.

The [new v1 status record](../../artifacts/qwen-long-history-v2/attempt-003/v1-status-and-diagnosis.json)
records **BLOCKED and zero held-out cases per arm**. The original v1 report,
protocol, checkpoints, raw answers, costs and failed attempts are unchanged.
Preservation verifies 6,538 readable D-drive files by SHA-256, including all
consumed scientific inputs, and six permission-denied old package archives by
unchanged size/mtime only. Their contents are not claimed hash-verified.
See `preservation-before.json`, `preservation-after.json` and `offline-audit.json`.

## V1 diagnosis, completed before v2 inference

The 1,255.8010113 seconds belongs to the whole cold TORUK development stage,
not one selector call. Recorded stage CPU is 25.0625 seconds, including 3.734375
controller seconds. Its sole completed request took 3.2966687 wall / 7.046875
CPU seconds. Selection was 0.2159237 wall / 0.859375 CPU seconds; generation was
3.0603819 wall / 6.109375 CPU seconds. The saved progress file identifies the
next correction request as active when the stage was terminated.

Saved Windows events show System Idle sleep from 15:35:16.4072437Z to
15:56:06.5668497Z on 8 November (21:05:16 to 21:26:06 IST), a 1,250.159606-second
span. A separate hardware-clock resynchronization records 1,240.753 seconds.
These are different clock observations. They establish suspension as the dominant
elapsed-time cause but do not recover an exact awake duration or the unfinished
second request's selection/generation split. Multicore CPU time is not wall
time, and the killed worker lacks final lifetime telemetry, so sampled CPU can
undercount. No sleep subtraction, reconstructed adjusted score or v1 PASS occurs.

## Protocol and exact identities

The [v2 protocol](qwen-long-history-v2-protocol.md),
[config](../../configs/qwen-long-history-v2.json), controller, tests and inputs
were sealed before candidate inference. After one successful four-arm rehearsal,
the limits and raw-output hashes were sealed in
[proposed-freeze.json](../../artifacts/qwen-long-history-v2/attempt-003/proposed-freeze.json).
Its SHA-256 is:

```text
84f23a07cd78935536b4586885bfb9d20bc78ae7d964a6a2d1ffffc8ccc4fec7
```

Backbone: Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, raw weights SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
All model/tokenizer files match the qualification registration. Selector:
the existing successor recurrent/cosine checkpoint, SHA-256
`f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49`.
This is not missing historical M6 or the trained logistic v2 selector.

Actual workers reuse the exact D-drive v1 worker/source and Python 3.12.14,
Torch 2.15.0+cpu, Transformers 5.22.2, Tokenizers 0.23.3, Safetensors 0.8.0,
Psutil 7.2.2. CPU float32/two threads, seed 81751, greedy generation, 64 output
tokens, one beam, repetition penalty 1 and cache enabled. Every arm uses the
same qualification instruction, question, native template and evidence envelope.
Full retains all turns; recent/lexical-v1/TORUK fit whole turns to 512 tokens.
Original evidence indices/text and raw prompt/output IDs remain available.

There is no new training. Rehearsal deliberately reuses the seven observed v1
development cases for timing and technical validation only. The unchanged v1
28-case held-out dataset remains ungenerated: 22 known and six UNKNOWN answers,
including ambiguous references, with four cases in each of seven categories.
The overlap recheck passed against 5,162 prior records from 132 JSON/JSONL files.
V1/v2 identity overlap is intentional and disclosed; this is not an independent
dataset replication or proof of semantic/pretraining separation. Held-out data
is hash-bound through a manifest; no held-out cases are copied into the rehearsal
worker directory. Its full-prompt IDs contain development IDs only.

## Observed development work

Each arm ran seven cases plus one charged, unscored first-case replay. All
replays matched exactly. No worker, request, memory, disk, elapsed or interruption
failure occurred. The process-scoped sleep request was acquired and restored.
The offline audit re-created every prompt with the pinned tokenizer, decoded
the stored output IDs, rechecked selected evidence and frozen scores, and
verified all registered inputs/outputs without generation.

| Arm | Correct | Exact copy | Preservation | Prompt/output tokens including replay | Stage CPU s | Stage wall s | Sampled private peak GiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full | 5/7 | 0/1 | 1/1 | 6307 / 41 | 109.781 | 90.190 | 3.805 |
| Recent | 1/7 | 0/1 | 0/1 | 4088 / 27 | 70.438 | 34.729 | 3.781 |
| Lexical | 7/7 | 1/1 | 1/1 | 1404 / 97 | 61.375 | 30.323 | 3.787 |
| TORUK | 1/7 | 0/1 | 0/1 | 1196 / 58 | 49.547 | 26.099 | 3.795 |

| Arm | Selection CPU / wall s | Generation CPU / wall s |
|---|---:|---:|
| Full | 0 / 0.00031 | 76.203 / 39.157 |
| Recent | 0 / 0.00032 | 49.484 / 24.661 |
| Lexical | 0 / 0.00163 | 41.047 / 20.420 |
| TORUK | 2.219 / 1.52157 | 27.703 / 14.058 |

Zero recorded lexical CPU is below timer resolution, not zero computation.
Stage totals include startup, integrity checks, fitting, tokenization, selection,
generation, monitoring and output work. Row subtotals exclude cold startup.
The four stages sum to 181.341771 wall / 291.140625 CPU seconds. Controller
lifecycle wall is 182.034484 seconds, including interstage work; its CPU overlaps
stage CPU and must not be added twice. Preparation, offline audit and general
verification are separate shared-cost records, not prompt-token savings.

Two technical preflights failed before any model worker: preservation inventory
could not read old package archives; then the precise Windows clock export was
looked up in Kernel32 instead of KernelBase. Failed logs, versions and corrections
remain in attempts 001/002 and preparation-amendment-1/2.json. No scientific
input or resource policy changed, and no model request was retried. Failed
preparation wall is recorded; its CPU was not captured, so an exact all-inclusive
preparation CPU total is unavailable. Successful preparation and wrappers have
separate measured timings. Neither failure consumes or rewrites v1's budget.

The fixed order and cold filesystem/import effects, especially the first full
worker, limit timing interpretation. The seven synthetic development cases are
already observed, small and correlated by scaffolding. TORUK loses six paired
development cases to lexical and wins none. Its only correct case is missing
information; all six known cases fail. Prompt-token/cost reductions with this
quality loss do not establish a useful tradeoff. There is no held-out uncertainty
estimate, exact-copy result or preservation result yet.

Historical training/profile cost remains 14.578125 CPU / 17.6733196 wall seconds,
charged once to TORUK in a future 28-query comparison (0.520647 / 0.631190 seconds
per planned query). Training peak RAM is unknown. The N=1000 sensitivity is
arithmetic only. Retain v1 sunk costs separately, including sleep and incomplete
CPU; no all-history efficiency claim can be reconstructed from them.

## Proposed frozen execution limits and stop boundary

Rehearsal caps were set before inference: 180 wall / 360 CPU seconds per arm,
720 wall / 1440 CPU seconds cumulative. All passed. The predeclared 2x scaling
rule uses each observed cold eight-request stage plus twenty slowest-request
durations to propose the 28-request stage, rounding upward:

| Arm | Slowest development request wall s | Proposed stage wall s | Proposed stage CPU s |
|---|---:|---:|---:|
| Full | 6.027 | 450 | 720 |
| Recent | 4.561 | 270 | 540 |
| Lexical | 4.464 | 240 | 540 |
| TORUK | 3.919 | 210 | 420 |

Proposed cumulative caps, including actual rehearsal stages, are
**1351.341771 wall / 2511.140625 CPU seconds**. Retain 30-second request,
6 GiB worker-tree private memory and 3 GiB study/input disk caps. These are new
v2 limits, not changes to v1. Development behavior cannot guarantee every unseen
output length or host condition will fit; an overrun must remain a failed attempt.

Interruptions retain real elapsed time. Record UTC/perf/unbiased-awake clocks,
CPU/memory/active request and durable heartbeats; a >5-second monitor gap or
>2-second elapsed/awake divergence invalidates an attempt. Terminate known child
trees on failure/resume, preserve all partial work, and never silently retry.
Allow only five logged 10-ms progress-file read retries. Abrupt termination or
power loss with no completion record is INVALID/INCOMPLETE; known CPU is a lower
bound. A later attempt requires a new reviewed registration and retains costs.

The proposed primary comparison is TORUK versus lexical, with unchanged v1
numerical gates: full and TORUK >=17/28 overall and >=14/22 known; at most one
overall/category regression against every comparator; no increased stale or
unsupported proxy; all arms complete within caps; at least 10% lower complete
CPU AND wall versus lexical and recent. Add paired counts, a predeclared
10,000-draw paired bootstrap interval and exact McNemar analysis as uncertainty,
without treating this small synthetic sample as population proof.

The proposal explicitly says **held-out NOT AUTHORIZED, zero completed per arm**.
The new controller has no held-out action. No review approval, held-out scoring,
commit, push, deployment or publication occurred. Recommended next action:
review the sealed proposal and poor development quality before deciding whether
to authorize a separate four-arm held-out execution.

## Evidence and engineering verification

Raw development outputs/costs/heartbeats:
[attempt-003/rehearsal](../../artifacts/qwen-long-history-v2/attempt-003/rehearsal).
Offline audit:
[offline-audit.json](../../artifacts/qwen-long-history-v2/attempt-003/offline-audit.json).
Exact commands:
[commands.md](../../artifacts/qwen-long-history-v2/commands.md).
Source snapshots and frozen inputs are in attempt-003/v2-source.zip and
rehearsal/registration.json; failed preflights remain alongside them.

Local `scripts/verify.py` returned 0: all 26 stages PASS, 283 Python tests passed
in 148.32 seconds, and Node passed 20 tests with one opt-in live test skipped.
Lint, formatting, default/Linux package types, dependency/import/CLI checks,
frozen sources, data validators, tiny existing fixture smokes, source/wheel build
and staged/unstaged `git diff --check` passed. These are local checks; no hosted
run covers this new work. Earlier preflight failures remain separate records.

Nine focused controller contracts pass, covering actual Windows clock access,
sleep detection, time accounting, drift/overwrite refusal, conservative limits,
read retries, stop-on-failure/power restoration and rejection of a held-out CLI
action. Ruff and explicit controller Mypy pass. General local scripts/verify.py
evidence is under verification/, with its final status in verification-summary.json.
This uses the C-drive environment, separate from pinned D-drive model workers.
Its existing tiny fixture training is engineering validation, not selector/Qwen
training or this study's held-out evaluation. No hosted CI covers the new files.

Files added: v2 protocol and this report, v2 config, controller, nine contract
tests, and artifacts/qwen-long-history-v2 (registration, snapshots, diagnosis,
overlap, raw rehearsal, proposed freeze, offline audit and check records).
Existing tracked source and D-drive uncommitted work are preserved.
