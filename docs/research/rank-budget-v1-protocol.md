# Rank-budget hypothesis, 4 November 2026

Starting commit: `84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`, clean tracked
working tree. First reproduce recall V2 from its recorded configuration, without
changing its source, weights, questions, prompt rendering or scorer. Compare all
96 development/heldout prompts and answers with the archive. If reproduction
fails, repair that prerequisite and stop; do not run the candidate mechanism.

The recorded envelope's heldout failures comprise five lost-evidence and three
generation-despite-evidence cases. Development identifies a concrete cutoff
problem: a revised policy scores 0.1857 and a credential source 0.0994 against a
0.2 absolute retention threshold. Both fit the two-source ranking budget. This
does not explain all missing evidence; ranking errors and the two-source capacity
limit can remain.

Hypothesis: using the frozen learned ranker's top two earlier user turns without
its absolute confidence cutoff will recover useful low-scoring evidence at lower
end-to-end cost per correct answer. Keep original ranking, chronological order,
three recent turns, source envelope, source/input/prompt budgets and backbone.
This changes one selection decision only. It can admit irrelevant or obsolete
turns; regressions must remain visible. No new domain vocabulary, answer rules,
training, fallback model, or changes to any baseline.

Numerical heldout success criterion, specified before mechanism edits: at least
6/12 correct versus the envelope's recorded 4/12; unsupported proxy at most 2/12;
summed full-request milliseconds per correct answer at most 90% of the reproduced
envelope value. Every condition must pass. These are tiny-set descriptive gates,
not statistical significance or a general accuracy/cost claim. Report raw token
work and memory even if latency improves. Local inference has no paid API charge;
energy, FLOPs and electricity cost are unmeasured. Do not invent a dollar cost.

Run development once with recent, lexical, old learned selector and candidate.
Freeze the mechanism and all experiment inputs; then evaluate the same fixed V2
heldout questions once, with no answer-driven edits or retries. V2 heldout has
already been published: this is a fixed-test follow-up, not a new unseen test or
independent qualification. Preserve the lexical scoring limitations and annotate
false assertions separately as subjective review if needed. Cases have 18
intervening distraction pairs; they do not test an increasing context-length curve.

Report correctness, unsupported proxy, exact/gist/reference categories, distant
evidence retention, tokenization and fitting work, model input/output tokens,
selector time, full request and stage wall time, cumulative process peak RSS,
and maximum source bytes. Include every regression. Stage and request time do
not include all startup/offline reporting work; command-wall logs measure the
full subprocess. Keep these accounting scopes explicit.

Do not change the browser's default selector. The candidate remains research-only
unless broader qualification establishes a useful benefit. No deployment, push,
or expensive training is authorized.
