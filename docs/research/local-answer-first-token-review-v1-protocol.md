# First-token margin review v1: saved-vector derivation protocol

22 November 2026. Zero new model forwards, training, gradients, checkpoint writes
or answer generation. This version fills reporting gaps in a completed study;
it is not a replacement inference run or a retrospective preregistration.

The single permitted 260-record probe already ran under
`artifacts/local-answer-first-byte-probe-v1/registration.json`, SHA256
`b244089a172bf7933fe53ee1558b2e8ac1c393c03e837e22e884dee052863213`.
Its complete raw evidence and protocol are committed at
`56af6eddf1467e52bd6e248b196b81f40d99b183`; the diagnosis is committed at
`743c29ff1b1dc5c86b81de48888a4753860ef0f8`. Do not repeat any probe worker,
change its registration, run marker, vectors, scorer, thresholds or receipts.

Before deriving new fields, freeze this document, the standard-library auditor,
its four contracts, and the single future intervention proposal in a new
`artifacts/local-answer-first-token-review-v1/registration.json`. Bind original
inventory/registration bytes and all four checkpoint bytes. An exclusive create
prevents replacing this registration or derivation. The source probe's 132 prefix
and 128 teacher rows, including four prefix replays, determine exact output order.
These are 260 DERIVED records, not 260 additional forward passes. All original
evidence hashes must verify before derivation; missing weights/inputs are STOP.

For each record attach checkpoint path/SHA256, source vector file hash and line,
case/checkpoint/phase/replay identity, prefix UTF-8 SHA256, native input-ID hash,
expected byte/ID, canonical entity/source-field/value/query-field tuple, template,
original archived first ID, and saved request/cold-worker accounting references.
Native input-ID hash = SHA256 of ASCII compact JSON integer array with no newline.
Prefix hashes cover exactly the original UTF-8 bytes; teacher input hashes cover
the saved teacher x IDs (including supplied gold bytes, excluding final EOS).

Recompute descending eligible IDs2..258 with lower-ID ties; retain full259-ID
and eligible257-ID probabilities. Define E=gold ID, T=each checkpoint's top ID,
and R=ordinary947's ARCHIVED first ID on this SAME case, only when R differs
from E. Record z(E)-z(T), z(E)-z(R), and z(E)-best OTHER eligible logit. R and
its margin are null on the 16 city cases where ordinary947 was already correct;
do not invent an error or substitute a runner-up. The same R applies to all four
checkpoints and both paths on a failed case. In passing checkpoints E=T, so
expected-minus-top is exactly zero while expected-minus-observed-error is
positive. Do not confuse it with the best-other margin in the prior report.

The observed-error margins and provenance joins are **post-hoc derivatives** of
saved full vectors. They were not additional predeclared fields in the original
probe. No new logits, prompts, examples, labels or v1 accuracy scores are made.
Source logits are saved float32 values represented as JSON numbers; recomputation
uses Python float64, matching the original offline metric calculations.

Independent saved-vector audit checks all original native bytes/IDs, y53/local21,
mask53..55, checkpoint hashes, raw seals, replays, invariants and complete Job
receipts. Original parity requires max absolute vector difference <=1e-5 AND
same top ID; near-tie threshold is unchanged at1e-4. Verify all derived top IDs
against archived first IDs. Preserve any new derivation/check failure separately,
never overwrite a failed attempt or retry inference.

Report all16 cases across all four cells, and group the 32 unique city prefixes
per cell by expected byte, predicted byte and canonical entity/value. Exclude
replays and teacher duplicates from grouped counts; retain all260 derived rows.
Explain missing `m` selections explicitly. State what remains unknown about
initialization, shuffle and optimization. No architecture or memory claim.

Original enclosing Job CPU<=200 seconds AND wall<=200 seconds remains the
inference budget. Retain its full lifetime cost, memory and separate outer
observer snapshot. Saved per-request costs include checks, forward/consume,
vector I/O and selection/parity. Isolated model-forward-only CPU/wall was not
recorded; report null rather than inventing precision. The complete cold/outer
receipts include loading, setup, teardown and all failed process work.

New derivation/testing/static checks run as a separately named complete Windows
Job, capped at60 CPU AND wall seconds,2GiB commit,128MiB logical output, max
observation gap5s. Editing and freeze outside that Job have unmeasured costs;
do not call its receipt a complete project lifetime. No model import is needed.
Preserve new command logs, status, costs and failures. Existing review inventory's
historical HEAD/uncommitted assertions are as-of-run statements, not applicable
to today's committed tree; verify its byte hashes and preservation commit instead.

The chosen next action, if original parity passes and margins discriminate,
is exactly the [paired-batch proposal](local-answer-paired-batch-v1-proposal.md).
It is a frozen design proposal only; no outcome authorizes its execution here.
Leave all new review work uncommitted. No push, held-out/development input access,
production-chat change or deployment.
