# Recall protocol v2: strict template separation

V1 is retained as diagnostic evidence: it reused some record/question templates
and duplicated one code world. Its nominal heldout results do not establish
template generalization. V2 corrects that flaw without changing the intervention,
backbone, decoding, token budgets, task counts or frozen V1 scoring function.

The source envelope was selected solely from V1 development. No V1 heldout result
may change it. V2 seals new training examples, development and heldout worlds
before inference. All record and question wording families differ across all
three splits. World-specific arbitrary codes prevent duplicate histories. The
long-gap weather scaffolding is shared; that is not a task-bearing template.
There is no training/fitting in this milestone. Frozen existing selector weights
come from historical data, not these new splits.

Run old selector, new envelope, recent and lexical on the same V2 development
worlds, then V2 heldout once. Do not adapt to either result. All limits, lexical
scoring caveats, diagnostics and reporting requirements from recall-v1-protocol.md
apply. New data/code bytes and the V1 scorer/protocol are bound before inference.
Scoring limitations discovered in V1 are retained and annotated, not repaired
using test responses. This is 12 synthetic cases per split, not broad qualification.
