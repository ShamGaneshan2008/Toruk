# Milestone status

Initial audit: branch `main`, clean tree, base
`334fe510780bda7b622ae7821a970c40d9f7dd2a`. Only tracked files were the PyCharm
starter `main.py` and `.idea/.gitignore`. No README, AGENTS.md, package,
configurations, specs, milestones, experiments, tests or workflows existed.
Ancestor AGENTS.md locations were checked; none were present. `main.py` is kept.

| Dependency | Actual status |
| --- | --- |
| Ordinary causal LM foundation (M1 prerequisite) | Implemented in this working tree; see checks and experiment registry for verification |
| Controlled-world generator, independent oracle, task evaluation (M2 prerequisite) | Implemented v1 during M6 prerequisite recovery; independent oracle, frozen worlds, generated-answer CLI and tests |
| M3 recurrent-memory LM | Implemented bounded one-lane training, state/session isolation and drained-document resume; useful-memory benefit not established |
| M4 paired-branch effect predictor | Implemented and pilot executed; 50% sign ranking on four validation labels, all runtime decisions out of support; learned value unestablished |
| M5 correction and preservation | Implemented separate objectives and final-write prediction; pilot known-fact correction/preservation accuracy 0%; research hypothesis unestablished |
| M6 controlled comparisons | PARTIAL: 14 validation configurations completed; all 0% primary accuracy; one seed, final test closed, exact resource matching outstanding |
| M7 generalization/capacity | PARTIAL: M6 replay 14/14 exact; 45 exploratory held-out evaluations completed, all 0% known-fact accuracy; capacity onset unidentifiable |
| M8 reproducibility and research audit | PARTIAL: sealed evidence rescored; M6 and two selected M7 cells replayed; internal draft prepared; full reruns, release permissions and independent replication outstanding |
| Protected revisions | Not started |

The following foundation handoff and audit sections are historical; the recovery
and registered pilot are recorded in the final section.

The explicit dependency rule in the task prevents building memory experiments
on this initially absent baseline. This handoff completes the earliest ordinary
LM foundation, then stops before M2/M3 rather than inventing prior-stage evidence.

Remaining M3 work: validate M2's world/event generator against an independently
implemented oracle, split documents, add autoregressive task scoring and a
trained ordinary baseline; then implement the proposed state/read/write contract,
ordered document lanes, TBPTT, streaming sessions and branching, safe memory
resume, architectural tests, and a matched-budget validation-only comparison.
Measure delayed/corrected/unchanged/distractor/density/unknown tasks, evidence
distance, coverage, parameters/state bytes, memory and full-history timing.

Before M4: M1/M2 must pass; all M3 causal/gradient/reset/session/resume tests must
pass; retain reproducible raw validation predictions for a fair ordinary/memory
comparison and reset-memory ablation with its distribution-shift caveat. A null
benefit may be reported but requires update/gradient/order/scoring/training
diagnostics. Then define paired branches and future-outcome labels without
oracle leakage. No claimed Toruk novelty follows from a recurrent baseline.

## 2026-10-20 M4 prerequisite re-audit

At `a025f0148965089b24a69344a13cd8a6447afef9` on `main`, the source, tests,
public commands and artifacts still contain only the ordinary LM. Fresh local
checks passed (9 tests), and a bounded foundation reproduction retained raw
validation outputs. Exact-commit remote CPU foundation CI also passed. This does
not verify recurrent memory: there is no writer/state/session/TBPTT code, M2
oracle or memory comparison. No M3 correctness fix or M4 implementation is claimed.

See [audit and reproduction](research/m4-prerequisite-audit.md),
[conditional M4 protocol](research/m4-effect-predictor.md), and
[primary-paper assessment](research/related-work.md). The new documents/evidence
are local edits; no commit or push was performed for this task. The next required
work remains M2 followed by M3 verification, before paired predictor training.

## 2026-10-20 M5 prerequisite gate

The source/configuration/test/workflow hashes still match the verified M4 audit.
No M4 branch pipeline, predictor or recurrent baseline exists. M5 therefore stops
at the explicit prerequisite gate; no correction/preservation experiment or
milestone completion is claimed. Prior local foundation checks and exact-commit
remote results are reused as such, not reported as M5 results. See the
[M5 audit](research/m5-prerequisite-audit.md) and
`artifacts/m5-prerequisite-audit.json`. Existing edits remain uncommitted/unpushed.

## 2026-10-20 prerequisite recovery and bounded M6 execution

The preceding audit sections describe the pre-implementation tree. Subsequent
M6 work implemented controlled worlds/oracle, recurrent state/session/training/
resume, paired labels/predictor and explicit correction/preservation losses.
A 14-result validation pilot completed under a 120-second process timeout but
did not learn corrected or preserved known facts. No mechanism or training
extension was added after observing registered results. See
[results](research/m6-results.md), [protocol](research/m6-validation-protocol.md),
and `artifacts/m6-validation-001/{protocol,stages,summary,manifest}.json`.
Local 24-test/lint/format/type/package checks pass; new code is NOT_RUN remotely.
No final test, commit, push, paid compute or M6 completion claim.

## 2026-10-20 M7 frozen-checkpoint failure studies

Verified M6 source/artifact identities and replayed all fourteen comparisons with
exact generated-token/score parity (336 answers). Executed unseen-rendering and
length/density studies: 45 evaluations, 1,080 answers, two data seeds, one frozen
training seed. All known-fact accuracies remain zero; revision predictor falls
back 32/32 times. Tested 649–1,066 tokens, 6–20 known facts and 2/4/8 slots;
degradation/capacity onset is unidentifiable at the learning floor. No tuning,
training or final-test scoring. **M7 PARTIAL**, with narrow failure observations
and runnable held-out infrastructure, not successful generalization.

Local 28 tests (zero skips), lint/format/types/package/build/CLI checks pass.
Exact-HEAD historical remote foundation CI passes; current edits NOT_RUN remotely.
See [frozen protocol](research/m7-protocol.md), [results and M8 gaps](research/m7-results.md),
`artifacts/m7-analysis.json` and `artifacts/m7-handoff`. Prior edits/runs preserved;
no commit, push, branch creation or paid compute.

## 2026-10-21 M8 audit

The current base is `34d3037310050bd8e5dd2e52c2566c2fd9a21b78` on `main`.
Earlier references to an unpushed M7 tree and older HEAD are historical.
M6/M7 remain partial negative research studies. M8 independently rescored 1,416
retained answers and reproduced all 336 M6 answers plus 48 selected M7 answers
exactly. No useful-memory, generalization, novelty or efficiency claim follows.
The remaining M7 cells and primary retraining were not rerun in this audit.
Current local tests pass (34 tests); exact-HEAD remote CI failed Linux types,
and the preserved local platform fix remains unpushed. See the reproducibility
guide for supported public commands; detailed M8 review and draft stay local.
