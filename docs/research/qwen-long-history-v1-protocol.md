# Qwen long-history v1: registered protocol

This is a new selector experiment, separate from m6-successor-v1 and
backbone-qualification-v1. Historical M6 remains NOT REPRODUCIBLE. No old
questions are generated again. Existing successor/qualification outputs and
IDE files are preserved by byte hashes. No new training, model fallback,
selector tuning, deployment, publication, commit, push or paid job.

## Hypothesis and frozen identities

The implemented TORUK selector can keep answer accuracy within five percentage
points of full evidence/recent/lexical and reduce complete CPU AND wall work by
at least 10% against recent AND lexical under the quality/regression gates below.
The four arms are full, recent, lexical-v1 and TORUK. Lexical-v1 and TORUK use
the exact existing source mechanisms, not new evaluation-specific selection.

Qwen/Qwen2.5-0.5B-Instruct revision
7ae557604adf67be50417f59c2c2f167def9a775, raw safetensors SHA-256
fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe.
All tokenizer/model assets must match the sealed qualification registration.
The selected backbone identity, Apache-2.0 license and exact common system
instruction come from qualified-backbone.json. No extra production system
instruction. Same native template and Reference/Question/Answer envelope as
qualification; each reference contains verbatim chronological User:/Assistant:
transcript lines. Every arm uses the same rendering and final question; source
turn IDs, gold labels, required-evidence indices and alternatives are offline.

The existing successor toruk-controlled-v1 checkpoint is read only from
artifacts/m6-successor-v1/execution/train/checkpoint.pt, raw SHA-256
f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49.
It is a twelve-step controlled-world model, not conversationally supervised.
Its unchanged recurrent-summary/cosine selector reads all turns anew per query,
keeps two older ranked turns plus the latest three, and resets state per query.
It is not the lost historical M6 checkpoint and has no cross-query memory cache.
Lexical-v1 keeps two overlap-ranked older USER turns plus latest three. No lexical-v2.

CPU float32, two Torch threads, seed 81751; deterministic greedy generation,
64 answer tokens, request temperature 0/top-p 1, one beam, repetition penalty 1,
KV cache enabled. The effective common GenerationConfig and native EOS/pad are
retained and must match qualification settings in every arm.

## Fresh data and overlap

Owned synthetic conversation records, not model-generated data. Development:
7 cases, one/category, seed 82811. Held-out: 28 cases, four/category, seed 82831.
Seven categories: distant location, explicit correction, competing distractor,
exact quotation, preservation under an unrelated edit, vague reference and
missing password. Two of four held-out vague references are genuinely ambiguous
and require UNKNOWN; the other two have an explicit recent referent. Thus held-out
has 22 known answers and six UNKNOWN cases. Each history has 20 irrelevant log
pairs, and task evidence is distant. Vague-reference histories also contain an
unrelated early refusal. Literal values and reference entities differ by split;
task question templates and gold pools differ, with generic log scaffolding shared.

Before any candidate inference, recursively scan parsable JSON/JSONL <=5 MB
under configs/artifacts for prior case IDs, gold expected/value strings and
normalized questions. Exclude model assets, initial backups and this new run.
Retain searched file hashes, extracted-record count, skipped files and scanner
scope in leakage.json. Explicitly cover both previous study dev/held-out sets.
New splits must be disjoint in IDs, known gold values and normalized questions
from each other and scanned prior cases. UNKNOWN/instructions/scaffolding are
shared by design. Source archives and pretraining corpora are not exhaustively
searched; this is literal overlap prevention, not semantic independence proof.
No prior/new held-out case or answer is used to train or tune a selector/scorer.

## Context handling and fairness

All four arms start from the exact same original role/content turns and question.
Selectors receive only that projection. Each arm's selected original indices,
verbatim text, rendered messages and token IDs are retained. Never summarize,
rewrite evidence, append labels or inject a gold answer. Bounded recent starts
with all turns; lexical/TORUK first apply the existing selector. Each bounded
arm then drops oldest selected whole turns until the IDENTICAL rendered prompt,
including common system/question/native wrappers, fits 512 Qwen tokens. The
question and instruction are never dropped. This fit is research-only; production
chat source and its limits are unchanged.

Full uses ALL original turns, not curated relevant evidence or an answer-bearing
oracle subset. Actual input+output limit is min(model max_position_embeddings,
tokenizer model_max_length), from the pinned files; model config declares 32768.
Reserve 64 output positions. Tokenizer-only registration must verify every full
history fits and exceeds 512. If ANY full input overflows the actual window,
registration is BLOCKED for the whole fixed dataset: no silent truncation,
post-result exclusions or extra information. Worker overflow also fails the
attempt, retained as incomplete and unable to pass.

## Scoring, failure rules and success

Primary metric: frozen case-balanced answer accuracy, equal four cases/category.
Reuse the unchanged qualification rubric: known word-boundary value match with
no listed competing value, negation or abstention; literal whole-answer equality
outside outer whitespace; explicit missing/ambiguous abstention accepted,
mixed guesses/asserted code values rejected. Store exact-match separately for
ALL cases. Stale and unsupported-response proxies are not exhaustive semantic
false-assertion counts. Do not repair this rubric after inspecting outputs;
any concern goes in a separate raw-answer review, with primary scores unchanged.

All conditions are conjunctive:

- All four arms finish every held-out case with no errors or cap violation.
- Full AND TORUK overall at least 60% (17/28), known facts at least 60% (14/22).
- TORUK loses at most 5 percentage points (one case here) against EACH of full,
  recent and lexical; no category loses more than one of its four cases.
- TORUK has no additional stale or unsupported-response proxy flags versus any
  other arm. No new semantic scoring is substituted for this registered rule.
- TORUK complete charged CPU AND wall work are at least 10% lower than BOTH
  recent and lexical, using the 28-question workload defined below.

Report all individual gates, aggregate/per-category scores, paired regressions,
abstentions, evidence retention and raw outputs regardless of verdict. Incorrect
known answers are classified first as stale assertion if applicable, then required
evidence omission, then unnecessary abstention or generator failure with required
evidence present. UNKNOWN failures are unsupported/unresolved responses. These
are reproducible attribution labels, not internal reasoning proofs. Exact-copy
failures with quoted text retained are generator failures. Overflow, resource,
identity, replay or worker failures prevent passing; no favorable retries.

## Sequence, resource limits and complete cost

Register source/tests/config/data/model/tokenizer/selector/runtime hashes and
source.zip before inference. No answers are needed for registration. Development
order full, lexical, TORUK, recent; 7 cases plus first-case replay each. Validate
technical completion, selected prompts and exact deterministic replay; no accuracy
filtering or tuning. Freeze development output hashes and mechanism identity,
then held-out once per arm: TORUK, recent, full, lexical. Fresh sequential workers,
exclusive output/started files. Any failed development prerequisite blocks held-out.
Never amend selector/config/scorer after registration to improve a result.

Limits: 6 GiB worker-tree private memory, 3 GiB new study plus Qwen/selector input
disk (environment excluded), 300 s per arm/split, 30 s per question and 1200 summed
new evaluation seconds. These are explicit new-study limits, not amendments to
prior experiments. Watchdog samples venv launcher/descendants at 50 ms and kills
the entire tree on a violation. Check final worker OS private peaks too. Keep
partial/failed outputs. Controller CPU is included; controller memory/whole-PC
memory and energy are not claimed to be measured by the worker cap.

Per request retain prompt/generated tokens, full-history/fit tokenization BPE
positions, actual backbone forward positions/calls, lexical term calls/bytes,
selector forward BYTE positions/calls and memory updates, ephemeral state size,
selector/retrieval CPU/wall, generation CPU/wall and full request CPU/wall.
BPE positions, selector bytes and CPU seconds are separate units. No unitless
sum, FLOPs or energy claim. TORUK's nominal 512-byte recurrent state is not total
process memory; it rescans history and updates state per question, with no
persistent learned state across queries. Peak worker RSS/private and cold setup
are retained separately. Rendering, tokenization, integrity checks, loading,
selection, fitting, generation, scoring and serialization remain charged in
complete process/controller CPU and stage wall measurements.

No new training. Separately retain original one-time profile/training cost from
BOTH original and execution successor attempts (four saved stages, including the
technical rerun). Use final worker lifetime CPU plus original controller CPU;
early parent-only original memory readings cannot establish training peak RAM.
Do not relabel historical memory observations as valid. Charge that one-time
CPU/wall once to TORUK at workload N=28 held-out queries. Primary totals are new
development+replay+cold held-out stages for each arm, plus that original cost for
TORUK. Report per-question original-cost amortization and warm inference separately.
A sensitivity calculation for N=1000 spreads ONLY original training cost over
more questions, retaining the measured 28-query inference/development work; this
is an arithmetic illustration, not a measured larger workload or a revised gate.
Common existing Qwen pretraining/download/environment setup and engineering
verification are outside arm comparisons and identified separately. No omitted
new training or indexing cost can be advertised as a saving.


## Technical amendment 1, before any held-out generation

The first development controller encountered Windows PermissionError reading an
atomically replaced progress file. Its full-evidence worker finished but the
controller wrote no valid cost result. This preflight is INVALID, preserved in
artifacts/qwen-long-history-v1 with as-run source.zip and copied source/protocol
under preflight-attempt-1. No development answers were inspected for tuning and
no held-out generation occurred. This is a technical prerequisite correction,
not a favorable quality retry. The mechanism, data seeds/conversations, scoring,
model/prompt/decoding identities, numerical gates and budgets are unchanged.

The final runner retries only progress-file PermissionError up to five reads,
10 ms apart, and guarantees child-tree cleanup and failed-stage recording on
monitor exceptions. It never retries a model request. File-read delays are within
the stated approximate watchdog sampling resolution; caps are not increased.
Fresh registration/development/freeze/one held-out pass run in execution-v2/.
The failed preflight's wall/CPU/resources are retained separately and are not
advertised as a saving; a measured-work ledger will disclose its incomplete CPU
accounting. Primary comparators are the valid matched execution. If the final
technical development fails, held-out remains blocked. No further quality-driven
amendment or held-out retry is authorized by this protocol.

The overlap scan excludes the entire current study, including its invalid
preflight, rather than treating unchanged preflight inputs as a prior evaluation.
The same 132 prior source files remain covered. The watchdog counts the entire
study directory for disk and reserves 73.307 seconds against the unchanged
1200-second total for the invalid preflight (controller wall plus completed worker
wall, deliberately double-counting overlap as a conservative upper bound).
The saved failed-preflight worker CPU is known, but lost controller CPU is not;
this engineering cost uncertainty must be disclosed separately from valid arms.
