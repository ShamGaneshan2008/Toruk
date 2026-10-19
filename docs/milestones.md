# Milestone status

Initial audit: branch `main`, clean tree, base
`334fe510780bda7b622ae7821a970c40d9f7dd2a`. Only tracked files were the PyCharm
starter `main.py` and `.idea/.gitignore`. No README, AGENTS.md, package,
configurations, specs, milestones, experiments, tests or workflows existed.
Ancestor AGENTS.md locations were checked; none were present. `main.py` is kept.

| Dependency | Actual status |
| --- | --- |
| Ordinary causal LM foundation (M1 prerequisite) | Implemented in this working tree; see checks and experiment registry for verification |
| Controlled-world generator, independent oracle, task evaluation (M2 prerequisite) | Missing; earliest remaining dependency |
| M3 recurrent-memory LM | BLOCKED at prerequisite gate; proposed contract only, no memory code or measured comparison |
| M4 paired-branch effect predictor | Not started |
| Protected revisions | Not started |

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
