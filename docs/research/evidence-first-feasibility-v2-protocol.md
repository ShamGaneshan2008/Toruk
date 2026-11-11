# Separate disposable feasibility-v2 stress protocol

11 November 2026. Authorized resource check only. Do not create, register or run
the 48-case study. Rehearsal-001, v1-v5 evidence, the answer policy, original LM
controls and production chat remain unchanged. No training or held-out inputs.

## Frozen question and scope

Audit the four saved synthesis rejections from rehearsal-001 without generating
answers. Establish source spans, native decoded bytes and membership in the
already declared two-premise contract. A single returned premise is incomplete
synthesis, even when it is a true source value. Do not relax the contract or
change policy code unless a general implementation defect is demonstrated.
Add new source-linked tests using different disposable facts, with valid
two-premise combinations and unsupported claims/partial combinations.

Register this protocol and all executable/input/asset hashes before inference
in a separate `feasibility-v2/registration.json`. Its only cases are two new
disposable 32/48-turn conversations, each containing two literal premises in an
explicit complete scope. Tokenizer-only padding puts the fitted prompt near
512 tokens while retaining both premises. No gold, scoring or oracle routes.

## Twelve-request diagnostic

Two cases x {Toruk, lexical} x two reversed-order passes = eight requests,
plus a first-case replay per selector/pass = four, for **12 requests** in four
sequential cold workers (three requests each). First-pass order is Toruk then
lexical, reversed for pass two. Both use the identical frozen answer-policy
function, original selector and whole-turn fit with the original research
prompt. No full-history verification lookup or extra LM helper is allowed.

The new diagnostic decoder uses CPU float32, two Torch threads, seed 81751,
deterministic greedy token choice, and **min_new_tokens = max_new_tokens = 64**.
Suppressing early EOS forces 64 actual autoregressive steps; do not force
particular answer tokens or teacher-force source text. This intentionally
changes termination for a separately labeled resource stress test. It does
not alter the policy, old LM controls, production decoding or synthesis
contract, and cannot support quality or efficiency comparisons against them.
Require exactly 64 generated IDs and one LM call per completed request.
Unsupported continuations still abstain under the unchanged validator.

The earlier **14 wall / 27 CPU seconds** request proposal is an assessment
threshold, not this new check's safety ceiling. Record every exceedance. No
registered 48-case cap is changed: that study remains unregistered.

Freeze independent safety ceilings before inference: **60 wall / 120 CPU
seconds per request**, **240 wall / 480 CPU seconds per cold worker**, and
**960 wall / 1920 CPU seconds over four workers**. Retain **6 GiB combined
private memory / 3 GiB logical disk including runtime assets and inputs**.
Charge registration/preparation, all cold setup, selection, tokenization,
parsing/validation, LM work, replay, monitoring, teardown and audit separately
and in nonoverlapping totals. CPU covers the controller and worker tree.
Record sampled and OS private peaks, request end readings and conservative
bounds for unsampled intervals; zero recorded phase CPU is not zero work.
Use 50 ms monitoring, halt on a gap over five seconds, and prevent sleep.

Immediately stop on provenance corruption, unsupported published answers,
evidence/prompt drift, leakage, replay disagreement or a safety-ceiling
failure. Charge failed/interrupted work and mark unavailable token counts
unknown. No retry, favorable rerun, new candidate or raised ceiling under this
registration. An early stop or failure to exercise 64 steps leaves feasibility
unestablished. No repairs based on the generated stress answers.

## Predeclared cap proposal and reporting

Use the largest request and non-request cold-stage wall/CPU observations
across rehearsal-001 and v2, never favorable timing or output quality. Let R
be ceil(twice the maximum request cost) for each resource, and S be ceil(twice
the maximum non-request stage residual). Propose a uniform future cell/pass
allowance **S + 49*R**, and an overall allowance **8*(S + 49*R) + A**. For A,
take the larger of the old shared allowance and twice v2 shared cost scaled
from two disposable cases to 48, rounded up. Keep 6/3 GiB memory/disk ceilings.
These formulas propose caps only; they neither register nor run any of the
48 cases, and do not relax contribution or stop gates after results.

Report each old rejection's cause, new disposable synthesis test behavior,
64-step workload coverage, maximum request wall/CPU, old-cap exceedances, all
tokens/calls/requests, cold/shared/total costs, peaks, proposed caps, tests and
Git status. Keep the stress outputs out of any future benchmark. Preserve a
before/after hash inventory of rehearsal-001, its bound code/tests and reports;
retain the separate v2 registration, raw rows, costs and final output seal.
