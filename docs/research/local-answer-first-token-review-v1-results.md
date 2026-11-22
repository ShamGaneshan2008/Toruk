# Frozen first-token study: saved-run review v1

22 November 2026. **Parity passes and first-token margins discriminate all16
failures.** Ordinary947 reproducibly prefers another byte, with gold rank2 and
gold-minus-top margins -1.035193..-0.209651. All three passing checkpoints rank
gold first on the same cases. This explains the observed token decision; it
does not identify initialization, data order or optimization causality.

## Workspace and preserved records

Confirmed Git root `D:/Toruk`, branch `main`, HEAD
`56af6eddf1467e52bd6e248b196b81f40d99b183`. Initial `git status -sb` was
`## main...origin/main`, with no changes. Local `origin/main` has the same SHA;
`git rev-list --left-right --count origin/main...HEAD` returns0/0. No fetch or
push was performed, so this describes the existing remote-tracking ref.

Diagnosis commit: `743c29ff1b1dc5c86b81de48888a4753860ef0f8`, exactly its six
inventoried files plus inventory. Probe commit: HEAD above, exactly127 inventoried
files plus inventory. Both are ancestors of HEAD; all133 inventory entries,
sizes, hashes and committed file sets verified. All four saved checkpoints are
present and match their full hashes. No diagnostic commit was duplicated.

The 260-record inference study requested here had already completed once and
was committed before this turn. Its registration/run marker forbid repeating
the workers. This review ran **zero new model forwards, training updates or
answer generations**. All new work is a versioned saved-vector derivation,
separate from the immutable probe and all earlier studies. The old inventory's
HEAD743/uncommitted assertions describe its creation time; the new auditor
verifies its preserved bytes/commit rather than applying those assertions to
today's committed tree. The archived inventory verifier was not edited.

Read the original local-answer protocol/results, first-byte diagnosis/proposal,
probe protocol/results, saved training predictions/labels/documents, checkpoint
metadata, tokenizer, prompt/data builder, make_batch/forward_batch, model/segment/
OwnedSession paths and exact scorer. No development or held-out input file was
opened. Original scores and failed gates remain unchanged.

## Frozen identities and completed measurements

| Identity | SHA256 |
| --- | --- |
| Original inference registration | `b244089a172bf7933fe53ee1558b2e8ac1c393c03e837e22e884dee052863213` |
| Original inference protocol bytes | `b15de6594fc8baefee96779c3034100e31cb998b2ea0a16b960ffc75c1974e42` |
| New saved-only review registration | `7b3e5cb4b63e3027ac9439dbacfb5a76f45a8817f49252f8f5e329eba26de7cb` |
| New review protocol bytes | `db967f7ac826b7e8536742222db1d634ab02d200f5b906b8bc49de502ab55df6` |
| One future intervention proposal | `fdf4af4cd2fa08cfe93685c9a41885facd21ac4f5faf57b3ca5ab7a23866c510` |

[Original registration](../../artifacts/local-answer-first-byte-probe-v1/registration.json),
[original protocol](local-answer-first-byte-probe-v1-protocol.md),
[new registration](../../artifacts/local-answer-first-token-review-v1/registration.json),
[review protocol](local-answer-first-token-review-v1-protocol.md).

The original pre-forward freeze binds exact32 city TRAINING cases, four final
1536-step checkpoint hashes/configurations, all260 planned records, full native
inputs and targets, tokenizer, positions, order, sources/runtime, measurements,
precision/threads/determinism, parity and200-second CPU AND wall caps. Four prefix
workers in order ordinary601,recurrent601,recurrent947,ordinary947 completed and
sealed132 vectors (32 cases plus replay each), before128 teacher rows in the same
cell order. All260/260 original records remain complete; all260/260 derived rows
now carry per-record checkpoint/input hashes and observed-error comparisons.

| Checkpoint | SHA256 | Parameters |
| --- | --- | ---: |
| ordinary601 | `0c6fb762abd5448e1222e617fa7902eaa2e179aa4cc72b02bcf3c44ee0bcd183` | 14058 |
| recurrent601 | `d3fce91dba46a01eae87675cf68807967a0561120975f5dbad71c3c5a5ee7e62` | 14416 |
| recurrent947 | `9de9dc4cfa3701f7cd48cc33160a6cd08e78e07bb4ea05c341b78453e1ab5bd4` | 14416 |
| ordinary947 | `ae8a6eb269473f8d4d8b7dc47f9bbcb28fd9b888aa52269762635c85dbdbafd8` | 14058 |

Saved strict loads checked seed/variant/config/progress and finite tensors. The
runtime was Python3.12.14,Torch2.15.0+cpu, deterministic float32 CPU, one thread,
eval/no_grad. Source/hash/runtime guards passed, and all eight workers retain
identical before/after parameter and Python/Torch RNG hashes with gradients absent.
Current verification hashes weights; it does not claim a new strict-load forward.

## Byte/token parity and what margins mean

All132 prefix argmax choices match the archived first token, all four replay
vectors are bit-identical, and all128 teacher/prefix comparisons pass <=1e-5
maximum absolute difference AND equal argmax. Observed max is
`5.9604644775390625e-06`. There is no recorded nonfinite, numerical/loading error,
retry, cap violation or partial inference attempt in this run.

Exact53-byte original prefixes plus BOS produce54 native IDs. Byte IDs are
byte+3; PAD0/BOS1 are the only suppressed IDs, EOS2 remains eligible. The prompt
ends `?=` IDs66,64. First answer is full native index54, causal y/logit53,
local segment21; answer mask53..55 covers two gold bytes and EOS. Probe prefixes
match original training/evaluation bytes and IDs, and teacher x/y match original
full documents with their original shift. All32 facts/queries fit in the22-token
second segment after BOS+31-byte prelude. No question-format substitution,
trimming, repaired EOS or alternate scorer explains these errors.

Let E be gold, T the top eligible token and R the ordinary947 archived WRONG
first token on that same case. Table values below are **z(E)-z(R)** in each
checkpoint. For ordinary947, R=T, so this is also expected-minus-top. For passing
checkpoints, E=T and expected-minus-top is exactly0, while expected-minus-R is
positive. These control margins differ from the previous report's gold-minus-
best-other margins; R need not be that checkpoint's runner-up. This is an
explicit post-hoc derivative of stored vectors, not a newly predeclared forward
measurement or a revision of the original record.

[All260 derived records](../../artifacts/local-answer-first-token-review-v1/records.jsonl)
save both margins, ranks, gold/top full259-ID and eligible257-ID probabilities,
raw-vector source hash/line, actual native-input hash, prefix UTF-8 hash, checkpoint
hash, original first ID/reproduction flag and saved timing references. Expected-
minus-R is null on ordinary947's previously correct cases, where no error exists.
Each case's same R is used for all four checkpoints and both phases.

## All16 failures across all four checkpoints

Gold ranks are2 in ordinary947 and1 in every control (48/48 passing comparisons).
`E/R` shows token IDs. Probabilities for every cell/record are in the linked rows
and [case summary](../../artifacts/local-answer-first-token-review-v1/summary.json).
Values below are rounded; full precision is retained. No wrong-gold or runner-up
near tie occurs at the unchanged1e-4 threshold across all260 original records.

| Case | E/R | ordinary947 | ordinary601 | recurrent601 | recurrent947 |
| --- | --- | ---: | ---: | ---: | ---: |
| train-004 | 112/111 | -0.460455 | 6.291219 | 3.943689 | 3.613377 |
| train-005 | 112/111 | -0.460455 | 6.291219 | 3.938153 | 4.371472 |
| train-006 | 112/111 | -0.591506 | 6.018297 | 4.738674 | 5.834682 |
| train-007 | 112/111 | -0.591506 | 6.018297 | 4.592803 | 4.848364 |
| train-024 | 112/118 | -0.366704 | 4.845117 | 6.295790 | 6.426854 |
| train-025 | 112/118 | -0.366704 | 4.845117 | 6.279029 | 6.477918 |
| train-026 | 112/118 | -0.209651 | 4.986749 | 7.088941 | 6.804997 |
| train-027 | 112/118 | -0.209651 | 4.986749 | 7.125516 | 6.726317 |
| train-048 | 118/119 | -1.035193 | 4.218665 | 4.366664 | 4.725971 |
| train-049 | 118/119 | -1.035193 | 4.218665 | 4.303305 | 4.689914 |
| train-050 | 118/119 | -0.681203 | 4.046978 | 4.907777 | 4.841232 |
| train-051 | 118/119 | -0.681203 | 4.046978 | 4.843441 | 4.778303 |
| train-076 | 111/119 | -0.467586 | 4.413606 | 4.260631 | 6.053588 |
| train-077 | 111/119 | -0.467586 | 4.413606 | 4.237102 | 5.983135 |
| train-078 | 111/119 | -0.559057 | 6.374795 | 4.994903 | 4.168622 |
| train-079 | 111/119 | -0.559057 | 6.374795 | 5.003296 | 4.149881 |

Expected `m` byte109/ID112 loses to `l`108/111 or `s`115/118; expected `s`115/118
and `l`108/111 lose to `t`116/119. Ordinary947 gold probabilities in the16 failures
range0.257582..0.436186 (eligible normalization). Rank2 with this nonzero mass
supports preference/discrimination error, not absence of the token from the
vocabulary or proof that training never learned it at any earlier step.

| Ordinary947 entity/value | Failed cases | Gold -> competing first byte | Count | z(E)-z(R) range |
| --- | --- | --- | ---: | --- |
| uvo/city/mi | 004..007 | m -> l | 4 | -0.591506..-0.460455 |
| pex/city/mi | 024..027 | m -> s | 4 | -0.366704..-0.209651 |
| zim/city/so | 048..051 | s -> t | 4 | -1.035193..-0.681203 |
| nax/city/la | 076..079 | l -> t | 4 | -0.559057..-0.467586 |

The other four entity/value groups pass4/4 each: uvo/la,pex/so,zim/tu,nax/tu.
Both templates and nonce variants fail in each affected group; these are eight
distinct ordinary local contexts, not16 independent mechanisms. All three passing
checkpoints get4/4 in each of all eight groups.

| Expected byte | City cases/cell | ordinary947 errors | Each passing checkpoint errors |
| --- | ---: | ---: | ---: |
| m | 8 | 8 | 0 |
| s | 8 | 4 | 0 |
| l | 8 | 4 | 0 |
| t | 8 | 0 | 0 |

Ordinary947 top counts over32 prefixes are l8,m0,s8,t16; every passing cell has
l8,m8,s8,t8. Wrong competing bytes are l4,s4,t8. Thus missing `m` selections are
reproduced exactly, including all eight expected-m cases. Four malformed `lo`
answers are the uvo/mi group in archived v1 outputs; all16 archived errors ended
in EOS. This review does not regenerate their suffixes or measure fresh EOS
completion.

Directly verified: the saved weights' top preferences, significant-to-threshold
losing margins, input/target/selection parity on these cases, and successful
resource closure. Unknown: when each preference arose, whether it was ever
correct earlier, effects of initialization versus shuffle (seed changes both),
and any causal effect of forced pairing. Existing trace evidence already shows
contrasts co-occurred, so missing contrast exposure is not a supported explanation.

## Costs, checks and limitations

| Scope | Complete CPU s | Wall s | Peak Job committed bytes | Closure/caps |
| --- | ---: | ---: | ---: | --- |
| Original single260-record probe | 30.187500 | 44.734275 | 696156160 | PASS200 CPU/200 wall;0 active/52 total |
| Newly run saved-only derivation/checks | 3.656250 | 6.976839 | 84705280 | PASS60 CPU/60 wall;0 active/54 total |

[Original cost](../../artifacts/local-answer-first-byte-probe-v1/execution/cost.json),
[new review cost](../../artifacts/local-answer-first-token-review-v1/execution/cost.json).
The original outer Job includes cold checkpoint loading/tokenization/setup,
contracts, controllers, workers/descendants, teardown and exit; user23.03125 +
kernel7.15625 =30.1875. Worker<=20,request<=2 and preparation/controller<=40
CPU/wall subcaps passed; peak disk2378294 bytes; max monitor gap0.1417874s.
No costs are added twice across parent/child Jobs. Original outer observer
CPU-to-receipt3.0625s is outside its Job, not a complete observer lifetime.
New review observer CPU-to-receipt0.1875s is separate; its Job user2.3125 +
kernel1.34375 =3.65625, peak disk722718 bytes, max gap0.0525267s,0 terminated.
Costs of source editing, preflight and registration outside the new Job are
unmeasured. Both costs are complete for their declared scopes, not the project.

Saved per-request times include input/mask checks, forward/consume, vector I/O
and selection/parity. Isolated forward-only times were NOT recorded; that field
is explicitly null in every derived row. It cannot be recovered by subtraction
or justify rerunning the consumed probe. Raw request costs, complete cold costs,
and successful finally/Job receipts are retained. No unsuccessful inference
attempt was discarded. Two pre-freeze draft lint checks found five then one
E501 errors; formatting/wrapping resolved them before freeze. Their status is
preserved in `preflight.json`; no training/forward failure occurred.

**Newly executed**, recorded in [checks](../../artifacts/local-answer-first-token-review-v1/checks.json):
10 focused zero-forward tests (six original, four new); committed inventory/
checkpoint/hash audits; 260-row derivative recheck; original training-only saved
audit; diagnosis/probe document verifiers; frozen sources; repository Ruff lint
and format (192 files); focused mypy (one changed standard-library script);
dependency check; and `git diff --check`. No full model test suite, model smoke,
held-out loader or hosted integration was run. Saved21-November inference costs,
six pre-forward contracts and older verification receipts are historical, not
new executions. Document/table/link checks and final inventory checks run after
report writing are separate read-only checks outside the new Job.

Read-only reproduction from `D:\Toruk`:

```powershell
.\.venv\Scripts\python.exe -B scripts/audit_first_token_margins.py audit
.\.venv\Scripts\python.exe -B artifacts/local-answer-first-token-review-v1/verify_report.py
.\.venv\Scripts\python.exe -B artifacts/local-answer-first-token-review-v1/verify_inventory.py
git diff --check
git status -sb
```

Do not repeat freeze/derive, original workers or `run_checks.py`; their output
files are exclusively created. The new audit rebuilds metrics from saved vectors
only. Original v1 remains80/96 in ordinary947,96/96 in each other cell, failed
training gate with development unrun. Earlier unknown complete-lifetime costs
remain unknown. No held-out cases, production chat, pushes or deployment changed.

## One next action

**Parity passes, margins discriminate failures: propose the one frozen
[paired city-batch intervention](local-answer-paired-batch-v1-proposal.md).**
Two ordinary947 fits, identical initialization/data/objective/1536 steps and
field timing; only within-city grouping differs. Both arms use identical city
slots and noncity batches; one forces same-entity contrasts, the other shuffles
city examples. Exact schedules must be frozen/tested in a future registration.
Stop after two fits or any cap/integrity failure; no extra steps, examples,
weighting or curriculum. If paired fails, reject sufficiency; if both pass,
forced pairing is not uniquely supported. No trial was launched here.

The targeted existing seed and tiny grammar do not support population,
generalization, architecture or memory claims. Keep memory comparisons deferred.
New files: saved-only auditor and four tests, review protocol/report, this single
proposal, and its new artifact directory. Final HEAD/main/origin relationship is
unchanged, with only these new untracked entries; no staged or tracked edits.
Existing committed study files were preserved and all new review work is left
uncommitted.
