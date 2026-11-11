# Decision draft: evidence-first answers

10 November 2026. **Initial status: review only; no implementation or experiment authorized.**
Confirmed Git root `D:/Toruk`, clean `main` at
`0f01e7c79732be494a18b1cfd349bc92abe5aee9` before this document. Propose an
answer policy after retrieval: copy a supported source slice, abstain when
support is not established, or use the LM for synthesis. Keep production unchanged.
No novelty or improvement is claimed.

11 November 2026 authorization: the user subsequently authorized a bounded,
research-only prototype, focused tests and exactly the separately specified
40-request disposable feasibility rehearsal. This supersedes the initial
review-only restriction for that work. It does not authorize the registered
48-case benchmark, production changes, training, a full-history lookup, commit
or push. The decision and contribution gates remain unregistered.

## What the evidence establishes

[V3](qwen-long-history-v3-results.md) repaired five retrieval omissions and
raised ungated Toruk from 1/7 to 5/7; lexical scored 7/7 on the same adapted
questions. [V4](qwen-long-history-dev-v4-results.md) and its
[failure evidence](../../artifacts/qwen-long-history-dev-v4/audit.json) confirm
two generation errors with unchanged evidence and no fit eviction: returning a
ledger ID despite retaining its meeting point, and substituting a seal marking
for an absent password. Lexical's extra archive line adds no requested fact;
its success does not establish a general padding fix.

[V5](qwen-development-v5-results.md) and its
[saved results/raw-arm evidence](../../artifacts/qwen-development-v5/attempt-002/results.json)
reproduce original Toruk/lexical 5/7 versus 7/7. Field instructions yield 5/7 versus 4/7;
silent checking yields 5/7 versus 5/7, repairing Toruk's abstention while losing exact
spacing. Both candidates fail their decision gates. Retention and stronger
instructions are insufficient; these reused development observations do not
validate a new architecture.

## Proposed answer contract

1. **Retain provenance.** Facts reference immutable message bytes, history/revision
   hash, original turn ID, role, chronology and UTF-8 byte interval `[start,end)`.
   Entity, attribute, polarity, units and temporal qualifiers are interpreted
   metadata, never replacements for source text. Corrections link to affected
   assertions while preserving unrelated fields. Unclear scope or conflicting
   authority stays unresolved. Record selection omissions separately from fit eviction.
2. **Bind the request.** Direct answering requires one supported entity/attribute
   binding satisfying the question's constraints. An identifier or related field
   cannot substitute. Initially declare a limited relation grammar and expose
   unsupported phrasing. Gold bindings, offsets and route labels are evaluator-only.
3. **Copy bytes.** Return the validated original slice, with provenance separate
   from the payload. No LM rewriting, trimming, Unicode normalization, whitespace
   collapse or added citation text. Invalid offsets, ambiguous quote boundaries
   and conflicting values prohibit direct copying.
4. **Separate support states.** Distinguish supported, absent-in-complete-scope,
   coverage-incomplete and ambiguous/conflicting. Absence needs a declared finite
   scope, complete coverage and supported parsing. Missing from selected turns
   does not mean missing from history; another attribute is not positive support.
   Otherwise return `UNKNOWN` or seek clarification, logging the reason. A missed
   known fact still loses full-history accuracy. Charge any additional search.
5. **Synthesize with the LM.** Multi-source combinations, comparisons and
   explanations without a single answer slice use the same bounded LM over
   source-linked evidence. Missing premises require abstention. Audit support
   for each generated claim: valid citation IDs alone do not establish entailment.
   Quoted instructions remain untrusted source data.

## Comparison and contribution boundary

| Approach | Existing mechanism and proposed difference |
|---|---|
| Current Toruk selector | Recurrent turn ranking by cosine; the v3 research gate admits overlapping older user turns, keeps two plus three recent turns, and fits to 512 tokens before LM answering. This is selection, not a verified requested-fact answer policy. The gate is not a production default. |
| Lexical-v1 | Query-term ranking retains two older user turns plus three recent turns before the same LM. Apply the answer policy equally to this stronger local control; wrapper gains would not establish learned-selector value. |
| [RECOMP](https://arxiv.org/html/2310.04408v1) | Trained extractive sentence selection or abstractive compression precedes LM answering; an empty compression skips unhelpful augmentation. Extraction/selectivity already exist. Empty augmentation does not certify requested-fact absence; this proposal adds a final source-slice/scoped-abstention contract. |
| [Self-RAG](https://arxiv.org/html/2310.11511v1) | A trained generator uses retrieval and critique reflection tokens to adapt retrieval and assess evidence/generation. V5's prompted silent check is not Self-RAG. Explicit span/routing contracts would still require semantic validation here. |

The existing research [source envelope](../../src/toruk_lm/source_spans.py)
already retains quoted turns. Provenance, extraction and selective generation
are not new claims. A possible contribution to investigate is a jointly audited,
correction-aware policy for copying, scoped abstention and synthesis with a small
decoder and complete costs. Distinctness needs broader prior-art review; parsing,
reference resolution, routing reliability, synthesis support and net savings
remain unproven. Provenance is not factual truth. The papers are conceptual
comparisons, not matched Qwen experiments or local performance evidence.

## Fresh development benchmark and gates

**Define now; create/register/run only after separate approval.** Use 48 new
32-to-48-turn conversations: six each for entity/attribute binding, literal copying,
missing facts with related distractors, corrections/preservation, resolved or
ambiguous references, retrieval-coverage stress, multi-source synthesis, and
conflict/negation/source-instruction traps. Include three counterfactual pairs
per category, Unicode/whitespace and paraphrases; use fresh wording, domains and
values rather than renamed old questions. Compare overlap only with observed
development material. Never consult existing held-out cases. Independently
review full-history answers, acceptable abstentions, offsets and synthesis premises.

### Evidence access and coverage

Freeze the following byte boundary before creating the registered cases. Let
`H` be the ordered immutable UTF-8 content bytes of every conversation turn,
including the final question `Q`; role/turn/revision metadata accompanies them.
The last three turns **include Q**, so the two older user-turn slots add at most
four historical source turns, not five. `E_T` and `E_L` are the exact original
historical message intervals surviving the respective selector and whole-turn
512-token fit. Never truncate or silently normalize an interval. The common
fitter uses the frozen original LM prompt/template and reserves Q and the same
instruction overhead; the proposed path cannot recover pre-fit sources. Its
synthesis call uses that same prompt and fitted evidence. Pairwise source and
prompt hashes must agree before answering.

`M` is a content-free coverage manifest: history/revision hash, ordered turn IDs,
roles, chronology, byte lengths and intervals, and selected/fitted/evicted flags.
It contains no extracted facts, terms, scores, summaries, gold offsets or route
labels. Metadata and Q may identify a declared scope; hashes are for integrity,
not a channel for recovering omitted text.

| Cell | Selector/fitter may read | Answer policy and any answering LM may read | Additional history lookup |
|---|---|---|---|
| T-LM: v3 Toruk + original LM | H; the recurrent ranker streams every historical turn, with lexical admission for older user turns; fitting/tokenization may inspect H | Q + E_T + M and frozen instructions; LM receives Q + E_T via the fixed renderer, with no omitted content | None |
| T-P: v3 Toruk + proposed path | Exactly the same H access, selector and fit as T-LM | Router, parser, validator and copier: Q + E_T + M; synthesis LM: the identical Q + E_T prompt available to T-LM | None |
| L-LM: lexical-v1 + original LM | H is available to the fitter; lexical ranking reads Q and older user content and retains the last three turns; fitting/tokenization may inspect H | Q + E_L + M and frozen instructions; LM receives Q + E_L via the fixed renderer, with no omitted content | None |
| L-P: lexical-v1 + proposed path | Exactly the same H access, selector and fit as L-LM | Router, parser, validator and copier: Q + E_L + M; synthesis LM: the identical Q + E_L prompt available to L-LM | None |

Selectors may return only turn IDs to the answer path. Keep ranker state,
candidate text, overlap traces and any pre-fit token buffers outside the answer
interface; retain diagnostic traces only for later audit. A validator can
re-slice only intervals already in E, not arbitrary offsets into H. After
selection/fitting, only the evaluator may inspect H and evaluator annotations,
and only after outputs are sealed. Apply
the same manifest construction and source-integrity checks to both controls;
no semantic preprocessing of H may supply answer hints to either policy.

Bind a finite scope from the question and frozen scope grammar, before testing
for absence. Default history scope is every historical turn, across all roles;
do not narrow it to selected turns or only user turns because those are easier
to cover. Explicit requests limited to named turns or a finite chronology
interval may establish a narrower scope from Q and M. Completeness means the
union of E intervals covers **every content byte** in that declared scope,
with matching revision, roles and chronology. Supported parsing must handle
every in-scope assertion and relevant correction/reference, including any
required antecedent outside the interval. Only then can a complete negative
scan establish `absent-in-complete-scope`. Lack of a match alone is insufficient.

An uncovered or unparsed interval, unsupported grammar or unavailable required
antecedent gives `coverage-incomplete`. Complete parsing with unresolved
binding/authority gives `ambiguous/conflicting`, not certified absence.
Use `UNKNOWN` or clarification as contracted, and log
scope, coverage, parsing status and reason separately from the payload. Claims
of the latest value or complete correction history likewise require coverage
of their declared temporal scope. A 32-to-48-turn full-history absence usually
cannot be certified from at most four historical turns: report that limitation.
A missed known fact still fails full-history accuracy; correctly guessing
`UNKNOWN` on an absent case does not certify complete coverage. Score payload
accuracy and support-state/coverage correctness separately; a false absence
certificate fails the support/integrity gate even if the payload matches gold.

**No extra full-history lookup is permitted in this four-cell design.** The
initial selection scan is not a semantic absence check. If a later design needs
a full-history verification scan, it requires a new review and registration:
give the matched LM control the same retrieved bytes and scope result before
answering, under the same input fit/budget; if those bytes do not fit, declare
incomplete coverage rather than secretly supplying them to the proposed path.
Log each lookup separately (scope, bytes, returned intervals, calls, tokenizer
and executed LM input/output tokens, process-tree CPU and wall time), including
failed/replayed calls, and include it in cell and overall totals. Apply the
same access rule to both selectors for their direct comparison. Gains against
a control without that access would be evidence-access gains, not answer-policy
or learned-selector gains.

### Registration, request arithmetic and disposable rehearsal

Before registered inference, freeze data hashes, grammar/router, scorer,
prompts, model identities, numeric caps and order. Preserve pinned Qwen, CPU
float32/two threads, seed 81751, greedy decoding, 512-token LM input and 64-token
answer budget, including copied payloads. No oracle routes, extra evidence,
new training or hidden classifier work. Each request uses at most one answering
LM call (zero on copy/abstention); no LM helpers or retry calls are allowed.
Load the backbone in every cold worker, even if all routes bypass generation.
Charge parsing, selection, coverage checks, lookup, validation, tokenization,
setup, all helpers and generation. Report non-LM scan bytes and tokenizer work
separately from executed LM tokens; reading text is not free just because the
backbone does not consume it.

| Work | Arithmetic | Treatment |
|---|---|---|
| Registered scored requests | 48 cases x 4 cells x 2 passes = 384 | 48 unique case outcomes per cell; pass two is a determinism/timing repeat, not another 48 independent observations |
| Registered replays | 1 first-case replay x 4 cells x 2 passes = 8 | Charged, unscored; compare exact output, support state, provenance, routes and scores |
| Registered total | 384 + 8 = **392 requests**, 49 per cell/pass in 8 cold workers | At most 392 answering LM calls; proposed copy/abstention reduces calls, not requests |
| Disposable rehearsal, only after separate approval | 4 different disposable cases x 4 cells x 2 passes + 8 first-case replays = **40 requests**, 5 per cell/pass in 8 cold workers | At most 40 answering LM calls; excluded from all registered scores, baselines and savings |
| Combined future work | 392 + 40 = **432 requests** in 16 cold workers | Report rehearsal cost separately and also include it in total study cost; no requests are authorized by this draft |

Freeze pass-one cell order T-LM, L-LM, T-P, L-P, then reverse it in pass two;
use the same frozen case order within each worker and replay its first case at
the end. Run workers sequentially. Count executed input/output tokens, failures
and replays in each pass, and report both pass totals. Include controller and
worker descendants in CPU and cold wall accounting; do not add request times
again to cold-stage totals. Record shared preparation/audit and controller work
outside those stages separately and include it once in overall resource cost.

The old caps (240 wall/480 CPU seconds per cell/pass, 1920 wall/3840 CPU seconds
across eight stages) imply only 240/49 = **4.90 wall seconds/request** and
480/49 = **9.80 CPU seconds/request**, before cold setup. They do not budget for
every request reaching the old 30-second limit: 49 x 30 = **1470 wall seconds**
per stage and 392 x 30 = **11,760 wall seconds (196 minutes)** overall, before
setup. At two fully occupied CPU threads that would be approximately 2940 CPU
seconds/stage and 23,520 CPU seconds overall, not a process-tree CPU guarantee.
The original v5 Toruk eight-request cold stage took 37.754 wall / 68.797 CPU
seconds; that observed short-answer workload does not establish feasibility
for 49 requests, longer synthesis or the new parser. Retire the old time totals
as unvalidated proposals, not measured feasible caps.

Before case creation/registration, a separately approved **single disposable
runtime rehearsal** must use four synthetic cases with different wording,
domains and values from both development evidence and the future benchmark.
Cover short copy, missing/ambiguous support, correction/coverage processing,
and near-budget multi-source synthesis; include 32- and 48-turn histories and
near-512-token inputs. Freeze the candidate policies and harness first. Use
the rehearsal only for resource measurement, not accuracy scoring, selecting
policies, changing grammar/prompts/gates, choosing registered cases or claiming
an improvement. Discard its case content and outputs from benchmark inputs;
retain an integrity hash and a separate resource receipt. Never inspect held-out
data. No rehearsal cases or generations are created by this revision.

Predeclare rehearsal safety ceilings: 30 wall seconds/request, 240 wall/480 CPU
seconds per five-request cold worker, 1920 wall/3840 CPU seconds across eight
workers, 6 GiB private memory and 3 GiB disk including inputs. Record all setup,
controller, preparation/audit and failed work as well; these stage ceilings are
not the entire project budget. Stop on a ceiling or existing integrity/stop
condition; do not rerun or raise it within this proposal. Such a failure leaves
feasibility unestablished and requires a new review.

If it completes, use this fixed sizing rule rather than favorable timing or
quality results. Let `r_w/r_c` be the largest observed whole-request wall/CPU
cost across all rehearsal cells, passes and replays, and `s_w/s_c` the largest
non-request cold-stage wall/CPU cost. Set numeric registered request caps
`R_w = ceil(2*r_w)` and `R_c = ceil(2*r_c)` seconds; set each cell/pass cap to
`W = ceil(2*s_w) + 49*R_w` wall and `C = ceil(2*s_c) + 49*R_c` CPU seconds.
This allows all 49 requests to reach their caps and includes setup headroom.
For nonoverlapping shared preparation/audit/controller work, freeze separate
numeric allowances `A_w/A_c` from twice the rehearsal per-case costs scaled
from 4 to 48 cases, rounded up. Overall registered caps are **8*W + A_w wall**
and **8*C + A_c CPU** seconds. Keep 6 GiB private memory and 3 GiB disk including
shared inputs; check rehearsal peaks and projected 48-case input/log storage
fit those fixed ceilings. Record the resulting numeric cap sheet before
registration; if unaffordable or unsupported by the rehearsal, stop rather
than shrink the benchmark or tune the gates.
No cap may change after registration or after seeing benchmark outcomes.

Report actual rehearsal requests, LM calls, input/output tokens, scan bytes,
setup and total CPU/wall, peak private memory/disk and failures separately,
then report registered and combined costs without double counting. The
rehearsal establishes resource sizing only, not quality or efficiency evidence.

### Fixed contribution and decision gates

Report the answer-policy result and learned-selector result independently.
All thresholds below are chosen targets, not forecasts; freeze them before
rehearsal and registration and never relax them after results. A pass permits
only another development review. Score the same 48 cases under a frozen rubric;
do not pool passes, pick a favorable pass, or count replays as extra cases.

For each selector s in {T, L}, policy gate `P_s` requires **every** row below
against its own original LM control. Retain the stronger-control quality hurdle
as well; equal wrapper gains cannot by themselves establish selector value.

| Policy gate | Requirement for each proposed cell |
|---|---|
| Accuracy | At least 44/48; no newly wrong case versus its own LM control; at least three more correct cases than its own control **and** the stronger of T-LM/L-LM. A ceiling control means no quality evidence, not a relaxed threshold. |
| Failure protection | Copy, missing-fact abstention and correction/preservation each 6/6; zero unsupported answers on annotated ambiguity/conflict cases; synthesis at least 5/6 without paired-control regression. Full-history omissions remain errors. Report every case/category/route and coverage state. |
| Provenance/support | Every direct answer exactly re-slices its revision; all synthesis premises have valid evidence and generated claims are supported. Absence certificates satisfy the declared scope/coverage test. Human-review generated support under a frozen rubric, not solely with the answering LM. |
| Tokens | At least 20% fewer aggregate executed LM input+output tokens versus its own control in each pass, including helpers/replays. Report input/output separately, route counts, answer bytes and equivalent answer BPE; copied text does not imply zero total work. |
| CPU/wall | At least 10% lower total process-tree CPU **and** cold wall time versus its own control in each pass, including setup. Report request median/p95 and setup separately. Token savings alone cannot pass. |
| Resources/integrity | Deterministic replay, cross-pass output/support/route/score agreement and matched source hashes; satisfy the rehearsal-sized, numerically frozen request/stage/overall caps, 6 GiB private memory and 3 GiB disk including inputs. Charge failures; no unlogged evidence or hidden work. |

The learned-selector gate `S` additionally requires **both P_T and P_L**, then a
direct **T-P versus L-P** comparison: T-P must have at least **three more correct
cases**, **no newly wrong case**, at least **20% fewer executed LM tokens**, and
at least **10% lower process-tree CPU and cold wall time in each pass**, all
costs/replays included. Preserve the same category, provenance and support
protections. Publish the paired case wins/losses and cost differences for
T-P versus T-LM, L-P versus L-LM, and T-P versus L-P, even when a gate fails.
This isolates evidence selection under the same proposed policy; it supports
only this frozen v3 selector configuration, not learning in general.

| Frozen outcome | Permitted conclusion |
|---|---|
| P_T and P_L pass; S fails (including a tie or lexical advantage) | Shared answer-wrapper evidence only; reject a learned-selector advantage and do not advance that claim. |
| P_T and P_L and S pass | Evidence for both the shared answer policy and incremental value of this Toruk selector under that policy; advance only to another development review. |
| Only P_L passes | Policy evidence on lexical only; reject the proposed Toruk configuration and selector claim. |
| Only P_T passes | Conditional policy evidence on Toruk only; no shared-wrapper or selector claim. Direct superiority alone cannot override failed P_L or establish S. |
| Neither P_T nor P_L passes | Reject both the proposed answer-policy advance and selector claim, even if an isolated metric or direct comparison improves. |
| Any leakage, provenance/support corruption or resource/stop failure | Halt as below; no positive contribution claim from an incomplete or invalid run. |

**Stop:** immediately halt on provenance corruption, unsupported direct answers,
leakage or resource failure; otherwise stop after the two registered passes.
Any failed gate rejects that configuration. Preserve results and attribute
selection, binding, copying, abstention and synthesis failures. No repair, extra
candidate, favorable rerun, raised cap or held-out test under that registration.
Even a pass supports only another development review, not deployment, novelty,
generalization or stable efficiency.

### Bounded prototype boundary

The isolated prototype lives in `scripts/evidence_first_policy.py`; neither
production chat nor the existing selectors import it. A shared research adapter
in `scripts/evidence_first_rehearsal.py` applies it after the original research
envelope and whole-turn fit, for either selector. The LM controls retain their
original prompt, selected/fitted bytes, generation configuration and output
handling. The router has no history reference or source lookup callback.

The initial grammar accepts literal user declarations of the form
`Entity's field is "value".`, explicit `Correction: ...`, and negative
`Entity's field is not "value".` declarations. Identifiers/field names are ASCII
words, digits, spaces, underscores and hyphens with an initial letter; literal
values preserve UTF-8 bytes, including spaces and tabs. Embedded quotes,
multiline values, arbitrary prose, pronouns and non-user factual authority are
unsupported, never silently ignored for absence. Blank lines and the exact
inert `No assertion.` line are recognized. Every other unparsed source byte
within the declared scope forces `coverage-incomplete`.

Requests are `What is Entity's field?`, `Copy Entity's field.`, or
`Combine Entity's field and Entity's field.`, optionally prefixed by
`In turns m0,m1: ` with explicit chronological turn IDs. Default scope is all
historical turns. A missing correction antecedent is incomplete; conflicting
unmarked values, negative-only bindings and unresolved references abstain.
Temporal qualifiers and compound/exclusion constraints are explicitly outside
this grammar; they cannot be rebound as unknown literal attribute names to
claim absence. Units inside literal values are preserved, never converted.
Explicit corrections replace only their bound field and log superseded spans.
All positive answers conservatively require complete parsed scope coverage too.

Synthesis is limited to an ordered combination of two supported literal
premises, with one call to the unchanged bounded LM prompt. The validator
accepts only their exact concatenation with `; `, ` and `, `, ` or a newline;
every additional claim, changed value, reversed premise or unsupported citation
abstains. This is a bounded support check, not an open-ended entailment model.
Missing premises never call the LM. No benchmark answer strings occur in policy
code. Tests use synthetic stubs, not Qwen generations; the only Qwen generation
work authorized here is the 40-request disposable rehearsal. The required
repository verification pipeline retains its existing smoke tests separately.

The rehearsal freezes source/input/asset hashes before generation, retains a
copy of this decision, runs eight single-use cold workers with five requests
each, and records costs without accuracy scoring. Its inputs and outputs are
excluded from the future registered benchmark. Its measured report and cap
proposal are separate from the fixed contribution gates above.

This document does not register the 48-case study. Frozen v1-v5 evidence and
production behavior remain unchanged; the prototype remains uncommitted.
