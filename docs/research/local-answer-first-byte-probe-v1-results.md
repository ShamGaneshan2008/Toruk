# Local-answer first-byte margin/parity probe v1: results

21 November 2026. **The immediate failure is explained by reproducible losing
first-token margins in ordinary947.** All16 previously failed city training
cases rank gold second, losing by0.209651..1.035193 logits; none is near-tied at
the frozen1e-4 threshold. All three passing checkpoints rank gold first on the
identical inputs. This establishes the inference decision, not why training
learned these weights or whether a paired curriculum would repair them.

## Preservation and registration

Confirmed Git root `D:/Toruk`, branch `main`, initial/final HEAD
`743c29ff1b1dc5c86b81de48888a4753860ef0f8`. Initial status was clean. The requested
seven-file diagnostic/auditor/evidence/proposal bundle was already preserved in
that exact scoped commit before this turn; its six-entry inventory and document
verifier passed. No duplicate commit was made and nothing was pushed. Its parent
`bb27b57d82f0185c9cc4f100b3afffd2d3e9f020` preserves local-answer-dev-v1.

The [new protocol](local-answer-first-byte-probe-v1-protocol.md) implements the
[committed proposal](local-answer-first-byte-v1-next-study-proposal.md).
[Registration](../../artifacts/local-answer-first-byte-probe-v1/registration.json)
SHA256 is `b244089a172bf7933fe53ee1558b2e8ac1c393c03e837e22e884dee052863213`.
Its sources/snapshots, all32 saved city TRAINING prefixes and labels, checkpoint
hashes, expected byte/token IDs, positions, measurements,260-row order and caps
were frozen and printed before any model forward. The exclusive run marker and
original hashes are retained. One attempt; no retries, failures or cap increases.

The four checkpoint identities are below; full SHA256, bytes and paths are in
registration. Each is the original final1536-step checkpoint, strictly loaded;
no selection, training, backward pass, optimizer construction/update or answer
generation occurred. Checking saved optimizer step metadata does not construct
an optimizer. All eight workers retained identical before/after model and
Python/Torch RNG hashes, with gradient fields absent. CPU float32, one thread,
deterministic algorithms, eval/no_grad, original runtime/tokenizer/configuration.

| Cell | Parameters | Checkpoint SHA256 prefix |
| --- | ---: | --- |
| ordinary601 | 14058 | `0c6fb762abd5448e` |
| recurrent601 | 14416 | `d3fce91dba46a01e` |
| recurrent947 | 14416 | `9de9dc4cfa3701f7` |
| ordinary947 | 14058 | `ae8a6eb269473f8d` |

## Native-input and numerical parity

All132 prefix records (32 per checkpoint plus one replay each) reproduced the
original saved first-token IDs, and all four replays were bit-identical. Prefix
workers saved raw259-logit vectors before selection and never opened the gold
evaluator file. All four prefix stages were sealed before the teacher stages.
All128 teacher-forced records passed max-absolute-logit difference<=1e-5 **and
identical argmax**; observed maximum was `5.9604644775390625e-06`. There was no
predicted-token feedback or multi-token continuation. Teacher CE uses saved gold
bytes and EOS; it is not a newly generated answer or EOS-completion test.

Saved evaluation prefixes, frozen prefixes, recomputed UTF-8/native IDs and raw
probe inputs matched byte for byte on every case:53 bytes plus BOS =54 IDs;
`?=` boundary IDs66,64; first gold native index54; causal y/logit index53,
local segment index21. Full teacher documents matched saved training documents,
including gold; x=full IDs[:-1], y=full IDs[1:], answer mask y53..55. The first
32 IDs form one segment; all supplied fact/query bytes occupy the next22. The
teacher path uses the original `make_batch`/`forward_batch`, while the prefix
path uses original `OwnedSession.consume` with fresh state. This checks parity
at the answer-start position on these inputs; it does not establish parity for
all possible positions or eliminate every batching-related training hypothesis.

Independent CE reconstruction from the first raw vector differed by at most
`1.0702192305700464e-06`. Summed three-token teacher CE differed from saved v1
suffix loss by at most `7.031485438346863e-08` (a descriptive consistency check,
not a new or revised gate). No scorer, decoding rule or earlier score changed.

## Margins and comparison on identical inputs

Rank is1-based among eligible IDs2..258, descending logit with lower-ID ties.
Full259-ID and eligible257-ID probabilities are both retained in
[all260 measurements](../../artifacts/local-answer-first-byte-probe-v1/measurements.jsonl).
The table below uses signed gold-minus-best-OTHER-eligible-token margin:
negative means gold loses; positive means gold wins. For a correct prediction,
gold-minus-predicted is zero; the positive comparison here is its runner-up
margin. This derived signed comparison never substitutes for the frozen fields.

| Checkpoint | First-token matches /32 | Expected ranks | Signed margin range, all32 | Near-tied decisions |
| --- | ---: | --- | --- | ---: |
| ordinary601 | 32 | 1 | +3.969618..+6.374795 | 0 |
| recurrent601 | 32 | 1 | +3.488597..+7.221270 | 0 |
| recurrent947 | 32 | 1 | +3.029385..+6.804997 | 0 |
| ordinary947 | 16 | 1 or2 | -1.035193..+1.086103 | 0 |

Every row below is one of the16 original failures. `E/P` are expected/predicted
token IDs; gold rank is2 in ordinary947 and1 in all three controls. The three
control columns are signed margins on that SAME case. Values are rounded to six
decimals here; raw vectors and annotations preserve precision. `P(gold)` uses
eligible probabilities; in ordinary947 failures it ranges0.257582..0.436186.

| Case | E/P | 947 ordinary | P(gold) | 601 ordinary | 601 recurrent | 947 recurrent |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| train-004 | 112/111 | -0.460455 | 0.379223 | 6.262449 | 3.943689 | 3.613377 |
| train-005 | 112/111 | -0.460455 | 0.379223 | 6.262449 | 3.938153 | 4.351760 |
| train-006 | 112/111 | -0.591506 | 0.346095 | 5.790627 | 4.738674 | 5.293284 |
| train-007 | 112/111 | -0.591506 | 0.346095 | 5.790627 | 4.592803 | 4.848364 |
| train-024 | 112/118 | -0.366704 | 0.393528 | 4.845117 | 6.295790 | 6.426854 |
| train-025 | 112/118 | -0.366704 | 0.393528 | 4.845117 | 6.279029 | 6.477918 |
| train-026 | 112/118 | -0.209651 | 0.436186 | 4.986749 | 7.041953 | 6.804997 |
| train-027 | 112/118 | -0.209651 | 0.436186 | 4.986749 | 6.926322 | 6.726317 |
| train-048 | 118/119 | -1.035193 | 0.257582 | 4.218665 | 4.366664 | 4.120077 |
| train-049 | 118/119 | -1.035193 | 0.257582 | 4.218665 | 4.303305 | 4.077819 |
| train-050 | 118/119 | -0.681203 | 0.330695 | 4.046978 | 4.907777 | 4.841232 |
| train-051 | 118/119 | -0.681203 | 0.330695 | 4.046978 | 4.843441 | 4.778303 |
| train-076 | 111/119 | -0.467586 | 0.375934 | 4.413606 | 4.260631 | 5.307487 |
| train-077 | 111/119 | -0.467586 | 0.375934 | 4.413606 | 4.237102 | 5.312192 |
| train-078 | 111/119 | -0.559057 | 0.358990 | 6.374795 | 4.994903 | 3.677984 |
| train-079 | 111/119 | -0.559057 | 0.358990 | 6.374795 | 5.003296 | 3.700063 |

Expected `m` byte109/token112 loses to `l`108/111 or `s`115/118; expected
`s`115/118 loses to `t`116/119; expected `l`108/111 loses to `t`116/119.
The four formerly malformed `lo` continuations are train-004..007; this probe
reproduces their first `l` only. Their later characters/EOS are saved v1 evidence,
not regenerated. Entity-pair duplicates in ordinary are expected: their varying
note ID is outside the local segment that ordinary reads at this position.

Representative exact saved prefix for train-004:

```text
note t004; rain. rain. rain. r
uvo city=mi
uvo city?=
```

That supplied `mi` is present locally. The expected first ID112 ranks second,
0.46045494079589844 below ID111. This is a learned first-byte score error at the
verified boundary, not evidence of missing supplied context or a scorer rejecting
a correctly emitted first byte. There are no near-tied wrong-gold or runner-up
decisions across either phase. Even the smallest failed margin exceeds the
largest measured path difference by over35000 times.

## Complete costs and frozen gates

[Outer Job receipt](../../artifacts/local-answer-first-byte-probe-v1/execution/cost.json)
accounts for complete controller/contract/worker and descendant process lifetimes,
including cold imports, hash/load checks, teardown, I/O and in-run analysis.
After exit:0 active,52 total processes,0 terminated, PASS.

| Measure | Observed | Frozen cap |
| --- | ---: | ---: |
| Complete outer CPU (user23.03125 + kernel7.15625) | 30.1875 s | 200 s |
| Complete outer wall | 44.734275 s | 200 s |
| Peak Job committed memory | 696156160 bytes | 2147483648 bytes |
| Peak logical run disk during probe | 2378294 bytes | 134217728 bytes |
| Maximum monitoring gap | 0.1417874 s | 5 s |
| Maximum worker CPU | 3.890625 s | 20 s |
| Maximum worker wall | 15.513894 s | 20 s |
| Maximum request CPU / wall | 0.015625 /0.396932 s | 2 /2 s |
| Complete preparation/controller CPU / wall residual | 3.671875 /1.839691 s | 40 /40 s |

Residual = complete outer totals minus eight nested worker Job totals; contracts
and all inner observers remain charged. Nested totals are subsets and are never
added to the outer total. The run summary's earlier controller self-report is
diagnostic; this final reconciliation includes process exit. Outermost observer
CPU-to-receipt is3.0625 s, outside the Job; its complete lifetime and total project
implementation/review cost are not measured. Post-run offline verification is
separate from this registered probe: its
[Job receipt](../../artifacts/local-answer-first-byte-probe-v1/verification/execution/cost.json)
is PASS,1.390625 complete CPU seconds,4.188711 wall seconds,0 active/24 total
processes,182366208-byte peak Job commit; observer CPU-to-receipt0.09375 s.

| Worker, in actual order | Complete CPU s | Complete wall s |
| --- | ---: | ---: |
| prefix-601-ordinary | 3.890625 | 15.513894 |
| prefix-601-recurrent | 3.171875 | 4.124835 |
| prefix-947-recurrent | 3.296875 | 3.885466 |
| prefix-947-ordinary | 3.375000 | 3.907820 |
| teacher-601-ordinary | 3.265625 | 3.906579 |
| teacher-601-recurrent | 3.156250 | 3.866293 |
| teacher-947-recurrent | 3.203125 | 3.835757 |
| teacher-947-ordinary | 3.156250 | 3.853940 |

All frozen integrity, reproduction, replay, numerical-parity, lifetime and cap
gates passed. This does **not** pass the earlier training gate: ordinary947
remains80/96 exact with4 malformed outputs; the other three remain96/96.
Local-answer-dev-v1 development and controls were not run. Earlier
answer-trainability-dev-v1's unknown complete-lifetime CPU remains unknown.
No earlier record, score, STOP receipt or failed gate was revised.

## Evidence, checks and limitations

[Independent audit](../../artifacts/local-answer-first-byte-probe-v1/audit.json),
[raw prefix vectors](../../artifacts/local-answer-first-byte-probe-v1/stages/prefix-947-ordinary/vectors.jsonl),
[raw teacher vectors](../../artifacts/local-answer-first-byte-probe-v1/stages/teacher-947-ordinary/vectors.jsonl),
[128 parity results](../../artifacts/local-answer-first-byte-probe-v1/parity.json),
[summary](../../artifacts/local-answer-first-byte-probe-v1/summary.json), and
[execution log](../../artifacts/local-answer-first-byte-probe-v1/execution/output.log)
are retained. The same vector/selection/request-cost/seal/invariant files for
the other three cells are under `stages/{prefix,teacher}-{seed}-{model}/`.
Every259-logit vector,260 derived measurements, per-request cost and all ten
Job receipts (contracts, eight workers, enclosing execution) are preserved.
The final `inventory.json` binds every new non-ignored file except its own
self-reference; its verifier also checks unchanged HEAD and unstaged status.

Before freezing/forwarding, six zero-forward contracts passed: saved inputs and
plan; synthetic ranks/probabilities/suppression; ties; nonfinite preservation;
registration-before-loading; forbidden training/generation calls. Post-run audit
independently recomputes every rank, margin, probability, argmax and parity from
raw vectors and verifies hashes, native inputs, masks, invariants, complete costs
and unchanged earlier gates. Focused document checks, frozen-source verification,
repository Ruff lint/format, package dependency check and `git diff --check` are
recorded with the offline verification receipts. Full pytest and research smoke
commands are intentionally excluded because they train or generate. No held-out,
development or production-chat execution occurs.

Repeatable **offline, zero-forward** commands from `D:\Toruk`:

```powershell
.\.venv\Scripts\python.exe -B artifacts/local-answer-first-byte-probe-v1/verify_saved.py
.\.venv\Scripts\python.exe -B artifacts/local-answer-first-byte-probe-v1/verify_documents.py
.\.venv\Scripts\python.exe -B artifacts/local-answer-first-byte-probe-v1/verify_inventory.py
.\.venv\Scripts\python.exe -B artifacts/local-answer-first-byte-v1/verify_document.py
.\.venv\Scripts\python.exe -B scripts/check_frozen_sources.py
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check src tests scripts
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

The original execution command is retained in `execution/cost.json`. Do not rerun
`first_byte_probe.py run` or any worker; this registration is consumed. Inputs
and checkpoints were fixed before measurement, so no case/checkpoint selection
was informed by these margins.32 city training examples and two existing seeds
do not estimate development generalization, EOS completion, or an architecture
advantage. Most importantly, parity/reproduction exclude a measured answer-start
path discrepancy on these cases, but leave initialization, minibatch ordering,
mixed-task interference and the benefit of pairing as untested training causes.

**Next action:** separately register a matched-exposure training-discrimination
intervention if continuing this line. The present probe ends here; it does not
change or execute the proposed curriculum, authorize development evaluation or
justify a memory comparison. All probe files remain uncommitted. Final Git
status has five untracked entries: the new artifact directory, protocol,
results report, `scripts/first_byte_probe.py` and `tests/test_first_byte_probe.py`;
no tracked modifications or staged files. HEAD/branch are unchanged.
