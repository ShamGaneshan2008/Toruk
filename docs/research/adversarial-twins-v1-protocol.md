# Adversarial counterfactual-twins challenge v1

Written 7 November 2026 before development or heldout inference. Starting HEAD:
`80713ec897323d8d17990dbe5bc8d1257a4daccf`, clean worktree. Previous copy-gap
study failed, with all methods at zero exact accuracy. No advantage was established.

## Single objection and hypothesis

The strongest remaining positive-looking owned-model count (17/96 vs 15/96)
could reflect shared answer priors rather than evidence-dependent recall. A
constant favourite value can earn credit in the old finite vocabulary. Its
ability cannot be inferred from lower language-model loss, and an all-zero
fixed-alignment diagnostic cannot settle it.

Hypothesis: a memory-answer benefit disappears when success requires correctly
answering both members of a matched counterfactual pair and comparison against
the parameter-matched ordinary control. Freeze all model weights, memory/selector
mechanisms and greedy decode. Use complete-line, training-style prompts with
varied segment alignment as a fairness control, not a tuned prompt solution.
This is one challenge, not a search over prompts or mechanisms.

## Models and construction

Existing owned-LM seeds 31/47; unchanged memory-on is the prespecified primary
Toruk method. Retain the already-frozen query-read-off intervention, ordinary,
and near parameter-matched ordinary as declared comparators. The best method
cannot be selected after evaluation. No external Qwen backbone participates.
Parent config/identity checks are unchanged. A fresh checkout recreates the parent
using the original bounded primary study; this challenge fits no weights.

For each known world, choose two different equal-length values. Colours use
blue/gold/lime (four ASCII bytes; red excluded for length matching); exact strings
use six random ASCII bytes. The two arms differ only in the evidence value,
with expected values swapped accordingly. Both answers must match exactly.
A context-independent constant answer cannot pass a pair. Each world has local
and distant placements with identical total length/filler/query. Four to eight
complete weather-note lines provide the gap; no truncation, fixed 352-token
prefix, new instruction wording or appended answer hints. Unknown controls have
only a visit record and target `?`.

Development seed 11801: two worlds per known kind plus two unknown worlds,
20 prompts total. Heldout seed 13801: ten worlds per known kind plus four unknown
worlds, 88 prompts. Both use local/distant placements; known placements have two
arms. Thus 160 development and 704 heldout generated answers across four methods
and two fitted seeds. Exact values and complete prompts must be disjoint between
splits; new prompts cannot duplicate original training prefixes. Colour inventory,
entities and grammar are shared. Independent sampling does not mean independent
investigators, new natural language, or unseen-template generalization.

Both datasets, code/config/protocol and six parent checkpoints are hash-frozen
before development. Development checks execution only. No mechanism/threshold,
prompt or decoding changes after inspecting its quality. Run heldout once regardless
of development quality. Started phases cannot be retried for better answers.

## Metrics and numerical criteria

Primary: proportion of distant colour worlds with **both arms exactly correct**,
separately at each fitted seed. Memory-on must score >=50% and improve by >=10
percentage points over parameter-matched ordinary at both seeds. Also require:
local colour-pair accuracy no more than five points lower; distant exact-pair
accuracy not lower; unknown false-assertion count not higher than the matched
control. Every condition is required. Retain individual-arm exact scores, all
outputs and all declared comparator results, even on failure.

Secondary, never a replacement for generated answers: conditional likelihood of
the correct versus swapped value bytes, after generation in a separate session.
Use the same PAD/BOS suppression and score each supplied value byte; do not score
EOS. A pair flips preference only if each arm prefers its own evidence value by
>1e-6 summed log-probability. Record per-byte log probabilities and all scoring
work/time. This can reveal conditioning despite overgeneration, but cannot turn
an incorrect generated answer into a correct one or establish useful chat.

Keep the three claims separate: (1) learned language patterns/evidence sensitivity,
(2) answer benefit from memory versus a strong control, (3) full-system savings
without quality loss. Claim (3) additionally requires the primary quality gate,
full evaluation CPU and wall time <=95% of the matched baseline, and sampled
controller+children peak RSS no higher, at both seeds. These are evaluation-workflow
costs, including offline scoring; they do not directly measure online serving cost.

Paper readiness: failed primary gate -> CENTRAL CLAIM UNSUPPORTED. A passed
primary gate alone -> MORE EVIDENCE NEEDED, because this small synthetic challenge
cannot close independent adjudication/population/hardware uncertainty. No automatic
READY FOR DRAFT REVIEW from this experiment alone.

## Resource and cost accounting

CPU float32, one Torch thread, greedy EOS-stopped generation, at most 16 tokens;
each prefix plus output <=384 positions. Both phases capped at 240 seconds each,
including eight sequential fresh worker processes per phase. No research training,
paid service, external model or fallback. Maximum 864 generated answers; at most
1,536 scored target alternatives (32 dev +160 heldout alternatives per method/seed).

Record generation input/output/work, memory commits, reader/writer-linear timing,
selector work (zero), generation wall/CPU and worker peak/RSS. Offline likelihood
has separate time/work counters. Full worker cost includes imports, model loading,
data/answer logging and scoring; add controller monitoring CPU. Sample controller
and recursive child RSS every 20 ms. Record the sampled maximum, not a guaranteed
OS high-water mark. The outer check.py/IDE harness is excluded. Phase wall includes
shared orchestration/audit work too. Counter positions are not FLOPs, and no energy
or training-amortization saving is claimed. Method order rotates by fitted seed.
Record sampled descendant CPU, including launchers, and the worker's final lifetime
CPU counter; add controller CPU. Phase records also expose shared controller CPU.
Short sampling gaps and final bookkeeping can still prevent exact exit-time CPU
accounting; these limits must remain visible in any cost claim.

Retain negative/ambiguous results and report all serious objections still open.
Do not adjust the Toruk mechanism, add canned replies or tune on heldout answers.
