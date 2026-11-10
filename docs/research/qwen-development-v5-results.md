# Qwen development v5: grounding and abstention instruction study

10 November 2026. **Neither candidate supports a behavior change.** Toruk stays
at 5/7 under both variants; lexical falls from 7/7 to 4/7 or 5/7. The silent
check fixes Toruk's unsupported answer but introduces an exact-copy failure.
Production behavior is unchanged. No held-out cases were parsed or evaluated.

Work began in `D:/Toruk` at
`0705a3da4d36d1857dde429ea82ec45007c4430d`, branch `main`, with a clean tree.
The v3 results, v4 audit and both portable-evidence READMEs were read first.
The two retained-evidence generation failures motivated this small, explicitly
adaptive development study. All seven existing development questions were used
for every condition; this is no independent evaluation or research win.

## Registration and matched execution

The [protocol](qwen-development-v5-protocol.md) and
[config](../../configs/qwen-development-v5.json) fix an original control and two
general candidates: requested-attribute grounding (`field`), and a silent
evidence check appended to the original (`check`). Neither contains case IDs,
expected answers, task-specific field names, examples or output repair. Both
include corrections, preservation, reference resolution, exact copy and missing
information, rather than optimizing only the two observed failures.

[Attempt-002 registration](../../artifacts/qwen-development-v5/attempt-002/registration.json)
sealed exact instructions, all seven cases, tokenizer-only full-prompt IDs,
source ZIP, dependencies, model assets and 596 pre-existing file hashes before
the first new generation. Registration UTC: `2026-11-10T14:49:10.953575Z`;
the hashes are in that receipt. The controller wrote its
exclusive start receipt before launching workers. Condition order was fixed:
original Toruk, original lexical, field lexical, field Toruk, check Toruk, check
lexical. Each fresh worker ran seven questions plus first-question replay:
48 generations, 42 scored, six charged replays.

Attempt-001 is preserved, with zero generations. An explicit script Mypy check
found type errors in the dynamic research adapters. Adding `cast(Any, ...)`
corrected static typing without changing runtime logic, candidates or design;
the source was registered again before inference. The failed and successful
receipts, both preparation costs and both exact source ZIPs remain available.
Initial manual formatting/lint issues were also corrected before registration.
There was no model retry or post-answer instruction revision.

Both selectors use the same frozen Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, weight SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
Toruk retains the v3 lexical admission gate and successor checkpoint SHA-256
`f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49`;
the comparator remains lexical-v1. These exact assets were absent from this
checkout and read from the earlier C-drive checkout after all original asset
hashes matched. Neither checkout's old files or weights were changed.

Only the system instruction changes. The reference/question/answer envelope,
original source bytes/order, native chat template, seed 81751, CPU float32/two
Torch threads, deterministic algorithms, greedy one-beam/cache decoding,
64-token answer cap, 512-token whole-turn fit and frozen scorer remain matched.
Versions: Python 3.12.14, Torch 2.15.0+cpu, Transformers 5.22.2. The model and
selectors receive only their original role/content projections, without labels.
The research-only adapters run in child workers; no runtime package source changed.

## Full development outcomes

| Instruction | Toruk accuracy | Lexical accuracy | Exact copy T / L | Preservation T / L | Registered support |
|---|---:|---:|---:|---:|---|
| Original | 5/7 | 7/7 | 1/1 / 1/1 | 1/1 / 1/1 | Control |
| Field | 5/7 | 4/7 | 1/1 / 0/1 | 1/1 / 1/1 | FAIL |
| Check | 5/7 | 5/7 | 0/1 / 0/1 | 1/1 / 1/1 | FAIL |

The original controls reproduce every saved v3 source selection, prompt ID,
answer, generated ID and score, including their replays. Every candidate keeps
the same selected/proposed original sources as its selector's v3 arm, with all
six known answer-bearing source sets retained and no fit evictions. Native
prompt IDs, output decoding, frozen scores and all deterministic replays audit
successfully. The technical gate passes; the development decision gates fail.

Literal raw answers below include the internal spaces. The longer original
Toruk distant answer is `delivery ledger LHD-4F9D48AA0B8B`; original lexical
answers `Delivery ledger LHD-4F9D48AA0B8B assigned the meeting point copper quay.`
Every answer, without table abbreviations, is retained in raw JSONL.

| Case | Original T / L | Field T / L | Check T / L |
|---|---|---|---|
| Distant | ledger ID / copper-quay sentence | `delivery` / `delivery` | `LHD-4F9D48AA0B8B` / same ID |
| Correction | correct linen-cabinet sentence / same | `linen cabinet` / same | `linen cabinet` / same |
| Distractor | `mulberry` / same | `mulberry` / same | `mulberry` / same |
| Exact copy | `DEV/PUTYAOKYO:  R-4!` / same | `DEV/PUTYAOKYO:  R-4!` / `DEV/PUTYAOKYO: R-4!` | `DEV/PUTYAOKYO: R-4!` / same |
| Preservation | `flower hyacinth` / same | `flower hyacinth` / same | `flower hyacinth` / same |
| Reference | `velvet depot` / same | `velvet depot` / same | `velvet depot` / same |
| Missing | `PLAIN` / `UNKNOWN` | `PLAIN` / `PLAIN` | `UNKNOWN` / `UNKNOWN` |

The exact original correction sentence in both controls is
`LHD-BC47D0CEDA8C is stored in the linen cabinet.` The required copied plate
contains **two spaces** after its colon; each shortened version has only one.

Field preserves Toruk's original five correct answers but fixes neither failure.
It makes lexical wrong on distant, literal and missing cases that lexical had
answered correctly. Check repairs Toruk's missing-information answer, retains
its distant error, and loses literal fidelity; lexical also loses distant and
literal correctness. Both preserve the flower and answer correction,
distractor and reference questions correctly.

Against matched lexical, field Toruk has one win, zero losses and six ties;
check has seven ties. That comparison reflects a degraded lexical comparator:
neither candidate improves Toruk accuracy, neither avoids new losses across
both selectors, and neither preserves exact copy in both. These are the
pre-registered reasons for rejecting both candidates. The seven-question
average alone would hide check's repair/regression exchange.

## Measured costs and failures

Seven scored questions, excluding replay. Request time includes full-history
tokenization, selection, fitting and generation. Raw rows additionally retain
each component's CPU/wall time and every per-case latency.

| Condition | Prompt / output tokens | Selector CPU / wall s | Generation CPU / wall s | Request CPU / wall s |
|---|---:|---:|---:|---:|
| Original Toruk | 1119 / 65 | 2.219 / 1.529 | 35.000 / 17.839 | 37.297 / 19.450 |
| Original lexical | 1231 / 72 | below resolution / 0.00171 | 35.172 / 17.536 | 35.344 / 17.587 |
| Field Toruk | 1455 / 34 | 2.047 / 0.867 | 29.953 / 15.009 | 32.109 / 15.930 |
| Field lexical | 1567 / 33 | below resolution / 0.00164 | 30.672 / 15.206 | 30.844 / 15.255 |
| Check Toruk | 1546 / 45 | 1.969 / 0.794 | 34.047 / 17.192 | 36.219 / 18.038 |
| Check lexical | 1658 / 45 | 0.016 / 0.00136 | 32.453 / 15.927 | 32.609 / 15.974 |

Complete cold stages below include setup, verification, controller and worker
tree, all eight requests and replay. A zero process CPU measurement is below
timer resolution, not zero work. Memory is the larger sampled/OS private peak.

| Condition | Prompt / output tokens including replay | Cold CPU / wall s | Private peak bytes |
|---|---:|---:|---:|
| Original Toruk | 1264 / 82 | 68.797 / 37.754 | 4,114,657,280 |
| Original lexical | 1404 / 97 | 63.438 / 32.091 | 4,081,340,416 |
| Field Toruk | 1648 / 36 | 55.000 / 28.402 | 4,109,373,440 |
| Field lexical | 1788 / 35 | 53.453 / 27.748 | 4,050,161,664 |
| Check Toruk | 1752 / 60 | 63.563 / 32.402 | 4,082,343,936 |
| Check lexical | 1892 / 60 | 57.375 / 29.438 | 4,084,338,688 |

All 48 generations completed once. No timeout, memory/disk cap, sleep,
monitor-gap, decoding, replay or worker-exit failure occurred. Fixed caps were
180 wall/360 CPU seconds per worker, 1080 wall/2160 CPU seconds in total,
30 seconds/request, 6 GiB private memory and 3 GiB disk including shared inputs.
Maximum observed monitor gap was 0.090 seconds; recorded disk peaked at
1,000,514,266 bytes. Idle-sleep prevention succeeded and was restored.

Totals: **361.625 CPU / 187.834 wall seconds** over the six cold stages;
controller lifecycle wall was 188.625 seconds. All requests including replay
used **9748 prompt / 370 output tokens**, versus 8576 / 294 for the 42 scored
requests. Their summed request CPU/wall times were 238.922 / 119.573 seconds
including replay and 204.422 / 102.233 seconds excluding it. These overlap with
cold-stage costs and must not be added again. Controller lifecycle CPU
(39.3125 seconds) also overlaps stage CPU.

Shared registration/preparation, separate from inference, cost 4.546875 CPU /
5.910584 wall seconds for abandoned attempt-001 and 4.140625 CPU / 4.860076 wall
seconds for attempt-002. The final scoring/native-token audit cost 3.953125
controller CPU / 4.486495 wall seconds. Wrapper and engineering-check wall costs
are recorded separately in check receipts. No new training occurred. Inherited
profile/training remains 14.578125 CPU / 17.6733196 wall seconds, with unknown
training peak RAM and no amortization claim. No monetary, energy or FLOPs cost
was measured. Broader engineering checks use their own tiny fixtures, separate
from this Qwen comparison.

Longer instructions add 48 native tokens per question for field and 61 for
check, equally in both selectors. Lower output lengths contribute to some lower
measured latency despite higher prompt cost. One fixed-order local run cannot
establish stable efficiency; cache/load effects and different output lengths
prevent an isolated selector or instruction speed claim. Sampled memory peaks
can miss transients; OS private peaks supplement them, while RSS can double-count
shared pages. Neither candidate qualifies as a quality or efficiency improvement.

## Verification, evidence and review state

The [development-only portable verifier](../../artifacts/qwen-development-v5/portable-verification.json)
passes: 80 evidence payloads, 472 old baseline hashes, 19 consumed inputs,
35 historical receipts, 26 historical stages and 667 source bindings. Its
native replay reproduces the v4 audit, with zero new generations or held-out
records parsed/scored. The broader portable-v1 verifier was deliberately not
invoked because the v4 portable README notes that it rescores other studies' held-out
answers. Frozen v1-v4 files remain byte-identical; 596 hashes also pass the v5
registration check after inference. The new artifacts do not repair old hashes.

Relevant tests pass: 82 contracts, including 34 new v5 cases. They cover sealed
full-set membership, generic/symmetric instructions, original envelope fidelity,
all-seven-case regression gates, exact-copy/preservation requirements, partial
run rejection, input drift/output-reuse rejection and frozen score/token/source
integrity. Explicit Mypy of the new runner plus package passes 37 source files;
source lint/format pass. `scripts/verify.py` returned 0 with all 26 stages PASS:
378 Python tests passed in 148.20 seconds; Node passed 20 with one opt-in live
test skipped. Package, frozen-source, CLI/data, native/Linux types, fixture,
build and staged/unstaged diff checks passed. A pre-existing unwritable pytest
cache emits a warning without affecting results. Final preservation and Git
checks, including whitespace checks of new untracked files, are retained in the
verification summary beside the raw evidence.
The first new-file whitespace wrapper misclassified Git's expected no-index
exit 1 as a failure; the corrected diagnostic-aware wrapper passes 183 files.
Both receipts are retained, and no file bytes were changed for that correction.

New review files are the v5 config, protocol, this report,
[research runner](../../scripts/qwen_development_v5.py),
[focused tests](../../tests/test_qwen_development_v5.py), and
[versioned evidence directory](../../artifacts/qwen-development-v5/README.md).
That directory contains both registrations/source snapshots, raw outputs,
resource/cost records, checks and evidence documentation. Four scoped
`.gitattributes` files preserve LF bytes for the new config, runner, tests and
documents; they affect only v5 paths and leave old frozen attribute rules intact.
Generated engineering
fixtures and installable packages stay local and ignored. Existing runtime,
selector, scorer, frozen research and production source files are unchanged.
All changes are left uncommitted for review; no commit, push or deployment was
performed. Final HEAD remains `0705a3d` on `main`, tracking `origin/main` without
reported ahead/behind. Git shows only the new v5 files/directories as untracked;
there are no tracked-file modifications or staged changes.
