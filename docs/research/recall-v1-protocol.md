# Exact, gist and vague-reference protocol v1

Registered before development inference. This is a bounded synthetic diagnostic,
not qualification of general conversation. No old final set is used for tuning.

Three disjoint splits use separate names, arbitrary values and question/record
wording families: training examples (not fitted), development (intervention
selection), and heldout (generated only after the intervention is frozen).
Each split has 12 worlds: exact code twice, quoted phrase, correction, unchanged
fact after unrelated correction, name/date, gist, revised gist, clear pronoun
twice, ambiguous pronoun, and missing evidence. Every world has 18 intervening
user/assistant distraction pairs. No world is a continuation of another.

Recent BASELINE, deterministic lexical-v1, and existing trained chat-selector-v2
use identical pinned local Qwen, system instructions, 512 prompt tokens, greedy
decoding (temperature 0, top-p 1), and 48 output tokens. V2 has prior evaluations,
but has **not** passed useful-quality qualification. Do not call it qualified.
The one new intervention must be chosen from reproducible development failures.
Re-evaluate all four on identical development and fresh heldout worlds. No retry,
training, model change, answer injection, or heldout-driven tuning is allowed.

Scoring is frozen with the generator before development: exact questions require
literal whole-output equality after outer whitespace removal, preserving case,
punctuation and internal whitespace. Gist requires each predefined semantic
concept group (one accepted synonym per group), excluding obsolete values.
Clear references require the correct object's value; ambiguous cases require an
explicit clarification/uncertainty phrase without asserting either candidate's
value. Missing cases require uncertainty without a candidate value. Score exact,
gist, referent resolution, clarification and unsupported assertions separately.
The lexical rubric is deliberately narrow; retain raw outputs for human review.
Unsupported means forbidden/obsolete value asserted, or an unqualified answer
on an ambiguous/missing case. It is a proxy, not a general hallucination detector.

Attribute failed cases first to lost gold evidence after actual prompt fitting;
then wrong candidate selection if a distractor record was retained; otherwise
to generation despite retained evidence. Compression damage is separately
checked by exact source-content equality: current chat selectors do not compress
text. These are observable diagnoses, not proof of the model's internal cause.

Limits: at most 64 messages, 16 KiB UTF-8 input; 512 final prompt tokens;
no persistent conversation state or unbounded source database. Additional selector
work must scan input once plus bounded ranking, retain at most eight source turns
and 4 KiB source content, with turn IDs and content hashes. Reject oversize input.
Report full input tokenization, scanned bytes, selector time, prompt fitting work,
selected/output tokens, total response time, process peak RSS and wall time.
Counters are work measures, not FLOPs/energy; selected-token savings alone do not
establish efficiency. Single-process CPU timings are descriptive.

Seal protocol, generator/scorer, runtime dependencies, split bytes, actual weights
and old selector before inference. Freeze intervention bytes after development
and before creating heldout data. Refuse existing output paths and input drift.
Keep incremental raw rows, failures, source provenance and command exit codes.
