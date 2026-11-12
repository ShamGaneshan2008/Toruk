# Source-faithful answer development v1

12 November 2026. A new, bounded development protocol, authorized separately
from the unchanged evidence-first 48-case decision. That older study remains
unregistered and unrun; this is neither its continuation nor a relabeling of it.
No held-out data, selector training, production changes, commit or push.

The hypothesis is limited to exact UTF-8 source copying, requested
entity/attribute binding, explicit corrections with unrelated-field preservation,
and scoped absence versus incomplete coverage. Synthesis is excluded. Its
failed feasibility remains a limitation: four rehearsal-001 answers omitted a
premise; all 12 forced 64-token v2 continuations were abstained. This study
cannot establish synthesis readiness, general language understanding or deployment
readiness. The existing narrow literal grammar and policy bytes remain unchanged.

## Inputs, freeze and access

Create exactly 12 new authored development conversations, three in each of four
categories, alternating 32/48 turns. Use fresh domains and values, not renamed
old inputs; compare only with observed disposable material, never held-out data.
Include Unicode/whitespace literals, same-entity and same-attribute distractors,
unmarked conflicting values, corrections and preserved fields, complete scoped
absence, missing full-history evidence and unsupported parsing. Inert filler is
deliberately synthetic. These cases are public development fixtures, not an
independent generalization benchmark or 12 statistical replications of a population.

Before any generation, `freeze` writes single-use input and evaluator-label files,
this protocol, source ZIP, source/asset hashes, dependency versions, model identity,
decoding, caps, gates and exact request schedule to `registration.json`. Labels
are manually specified from the authored sources, not obtained from the answer
policy, selector or LM. Labels retain full-scope payloads, byte offsets, requested
bindings, scope, parsing limitations and correction links. Structural label
validation and tokenizer-only checks are permitted before freeze. No pilot model
outputs, routes or outcome-based case selection. Workers never load labels;
evaluation begins only after raw answers are sealed. Freeze/run each have a
single-use marker; no retries, repairs or replacement candidates after inference.

Let H be all ordered message bytes, Q the final question, E the original
whole-turn intervals surviving selection and the shared 512-token fit, and M
content-free revision/role/chronology/length/selection/fit metadata.

| Cell | Selection and fitting access | Answer access | Answer behavior |
|---|---|---|---|
| T-LM | H, unchanged v3 research Toruk plus lexical admission | Q + E_T via original research envelope; M for audit | Original LM, including original output stripping |
| T-P | Identical H access, selector and fit | Q + E_T + M only | Existing shared policy, copy or abstain; no LM |
| L-LM | H, unchanged lexical-v1 | Q + E_L via original research envelope; M for audit | Original LM and output stripping |
| L-P | Identical H access, selector and fit | Q + E_L + M only | The exact same policy as T-P |

Paired cells must have identical fitted bytes, manifests and native prompt IDs.
The parser/copier cannot access H, ranker state, labels or a history callback.
No additional lookup or semantic full-history scan supplies answer hints. Hashing
and tokenizing H during selection are logged and charged, not called free work.
The evaluator may examine H and labels only after output sealing.

Explicit question scope is fixed independently of which turns survive. Default
scope is every historical turn. Certified absence requires complete byte coverage
AND supported parsing of every in-scope interval, including correction antecedents.
Omitted or unparsed bytes yield coverage-incomplete, even with a plausible retained
value. Unmarked conflicting values yield ambiguous/conflicting. Positive copying
also requires complete parsed scope. Source role, chronology, revision/hash and
UTF-8 offsets accompany exact payload bytes separately. Corrections replace only
the requested field and retain links to superseded spans; unrelated fields survive.
No trimming, Unicode normalization or citation text is allowed in copied payloads.

## Execution, arithmetic and fixed caps

12 x 4 x 2 = 96 scored executions, plus one first-case replay per cell/pass =
8 unscored charged replays: **104 requests**, 13 per cold worker, eight sequential
workers. There are 12 unique outcomes per cell; repeats are determinism/timing
checks. First pass: T-LM, L-LM, T-P, L-P; second: L-P, T-P, L-LM, T-LM. Case order
is frozen as written; replay the first case last. No shuffling after outputs.
At most 52 original-control LM calls; proposed cells must make zero calls.
Every worker loads the backbone, including copy/abstention workers.

Use the exact Qwen model and selector assets from preserved feasibility records,
identified by SHA256 and backbone manifest. CPU float32, two Torch threads,
seed 81751, deterministic greedy decoding, one beam, no sampling, repetition
penalty 1, cache enabled, ordinary EOS termination, max_new_tokens 64. Input cap
512; copied payload cap 64 native tokens. No forced-length diagnostic decoding.

Freeze request caps **26 wall / 51 CPU seconds**, derived from the earlier
pooled feasibility sizing proposal, without selecting new favorable timings.
Cold worker caps are **360 wall / 714 CPU seconds**: 22 + 13 x 26 and
51 + 13 x 51, including setup/residual headroom. Eight workers have **2880 wall /
5712 CPU seconds**; disjoint preparation/controller/audit shared allowance is
**120/120**, giving **3000 wall / 5832 CPU seconds overall**. Combined private
memory cap 6 GiB; logical disk cap 3 GiB including unique runtime assets,
frozen sources/inputs and run files, excluding installed runtime/OS/build caches.
Monitor every 50 ms; stop if a monitoring gap exceeds five seconds. Prevent sleep.

Charge registration, cold setup, selection, fitting, all tokenization, parsing,
coverage/provenance validation, copying, generation, failed work, replays, controller,
monitoring and final audit. Record native prompt/generated IDs, raw and published
bytes, source manifests, omissions versus fit evictions, scan bytes, tokenizer
positions, phase costs and whole-request/process-tree CPU/wall. Retain sampled
memory/disk peaks and conservative stage bounds for unsampled fast requests.
Components overlap; only cold stages plus disjoint shared work are additive.
Report external command/test costs separately. Allocate shared cost equally over
eight cell/pass stages for efficiency gates, without adding it to totals again.

Immediately stop on cap failure, source/asset drift, malformed provenance,
unsupported copied bytes, false absence certificate, paired evidence/prompt drift,
unexpected helper/call, leakage, replay or cross-pass disagreement. Save partial
rows and interrupted unknown token counts explicitly. Ordinary wrong LM answers
are scored failures, not infrastructure failures. A stop makes contribution gates
fail/unestablished. Do not raise caps, relax gates, repair the policy or retry.

## Frozen scoring and contribution gates

Exact payload accuracy compares UTF-8 bytes with the full-declared-scope gold;
no trimming, normalization, substring credit or scorer LM. A missed known fact
loses accuracy even when safe abstention is correct for the fitted evidence.
Separately score all four support states against the labels and actual coverage.
A correct UNKNOWN payload does not certify absence. Check exact source spans,
requested binding, correction chains and preservation. A true supported single
source fact with the wrong entity/field is incorrect. Controls have no support
certificate and receive payload scores only; do not invent one for them.

For each proposed selector cell, its policy gate requires ALL of:

- At least **10/12** exact payloads and **2/3 in each category** in both passes.
- No case correct in its own LM control becomes incorrect; at least **two more
  correct cases** than its own LM control AND the stronger of the two LM controls.
- **12/12 correct support states**, exact source/binding/provenance and correction
  checks; zero false absence, invalid copy or unsupported published claim.
- At least **20% fewer executed LM input+output tokens**, **10% less cold plus
  equally allocated shared CPU** and **10% less wall** than its own control in
  EACH pass, including replays, setup and every failed call. No favorable pooling.
- All integrity/resource/replay checks pass. No category or gate may be dropped.

Report T-P vs T-LM, L-P vs L-LM, AND T-P vs L-P directly. The learned-selector
gate additionally requires both policy gates, at least **two more correct** for
T-P than L-P, no L-P-correct case lost, all category/protection checks, and the same
20% token/10% CPU/10% wall savings against L-P in both passes. Zero-token lexical
cost admits no strict token saving; zero versus zero cannot pass that hurdle.

Both policy gates with a failed selector gate support only the shared policy on
these development fixtures. A single policy gate supports only that combination,
not a selector contribution. Passing the additional direct gate supports a bounded
selector result. If neither policy gate passes, reject both policy adoption and
selector contribution under this protocol; record any narrow mechanism success
without calling it readiness. No pass authorizes production or revives the stopped
48-case study. Freeze these thresholds before outcomes and never change them.

## Reporting and verification

Seal raw outputs before scoring, then retain scores, failures, per-case and per-pass
comparisons, complete cost receipts, output hashes and a clear pass/fail report.
Report synthesis failure, grammar/scope limitations, authored-label dependence,
small synthetic workload, noisy timing and any incomplete coverage or cap stop.
Run focused tests, both existing portable evidence verifiers, `scripts/verify.py`
and `git diff --check`. Repository smoke fixtures are separate engineering checks,
not additional study cases or Qwen study calls. Keep original decisions, prototype,
feasibility reports, production code and v1-v5 evidence byte-unchanged. Leave all
new work uncommitted for review.
