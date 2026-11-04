# Exact recall, gist recall and vague references — 4 November 2026

This milestone is a bounded **negative/inconclusive research result**, not a
completed memory capability. The existing conversational ranker preserves raw
turns, but the pretrained decoder can change exact strings, reuse obsolete facts,
or guess a referent even with evidence present. One source-transcript intervention
was implemented and frozen. Development gains in the initial diagnostic did not
establish a reliable improvement on fresh wording.

## Scope, inspection and protocol correction

Base commit: `091a36b075ae7c81b31954a14409f5402083d5e7`; initial working tree
clean. README, current architecture/private implementation notes, latest audit,
value-fidelity negative result, inference/selector code and actual local
checkpoints were inspected. Historical frozen evaluations, checkpoints and loaders
remain unchanged. No new weights, backbone, training, commit, push or deployment.

The conversational path was chosen because it can run the same actual backbone
for all methods. The integrated byte-decoder experiments are a different system;
their value-collapse failures are motivation, not comparable scores here. The
existing v2 ranker has prior evaluation evidence but has **not passed** useful
quality qualification. Calling it a qualified memory model would be incorrect.

[V1 protocol](recall-v1-protocol.md) and
[V1 registration](../../artifacts/recall-v1-20261104/registration.json) were sealed
before development inference. Its 12-case diagnostic reused some task-bearing
wording across splits and duplicated a code history. Those defects were found
during review; **V1 is not template-held-out evidence**. Its original data,
scorer, source hashes, before/after outputs and nominal heldout run are retained.

[V2 protocol](recall-v2-protocol.md) corrects those defects using newly generated
world-specific values and disjoint task-bearing record/question templates across
training examples, development and heldout. A normalization-based test checks
separation after entities/values are removed. Shared weather-gap scaffolding
remains; this is synthetic wording transfer, not unseen-domain qualification.
Training examples are not fitted. V2 seals all input bytes before inference;
development completes before heldout opens. The V1 development-selected
intervention and frozen scorer are unchanged. There is no heldout-driven tuning.

Each split has six exact-string cases, two gist cases, two clear references, one
ambiguous reference and one missing-evidence case, with 18 distraction pairs.
Cases include explicit corrections and an unrelated launch correction after which
the original code must remain valid. Exact code, date and punctuation-sensitive
motto answers require whole-string equality after outer whitespace removal.
Gist uses frozen concept/synonym groups; vague references and clarification are
scored separately. Raw answers expose the limits of this lexical rubric.

## One intervention and identities

In the complete V1 before run, old ranker and lexical selection each failed five
cases with required evidence retained: quotation, correction, gist, revised gist,
and ambiguity. This reproducible failure group motivated evidence presentation,
not retriever training. See the sealed
[decision](../../artifacts/recall-v1-20261104/intervention.md).

The new research backend renders the old selected sources as a single
chronological transcript with role/span labels and generic instructions for
corrections, exact copying and clarification. It changes both serialization and
those instructions as one evidence-envelope intervention; the study cannot
attribute effects to individual wording components. It does not parse facts,
retrieve evaluation answers, remove obsolete values, or enforce abstention.
Source content remains verbatim. Final 512-token fitting can still evict it.

All methods use Qwen/Qwen2.5-0.5B-Instruct revision
`7ae557604adf67be50417f59c2c2f167def9a775`, actual weight SHA256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
Greedy temperature 0, top-p 1, 48 output tokens and the same 512-token prompt cap
and system instructions apply. No model sees reference labels. Methods are
recent BASELINE, deterministic lexical-v1, old trained chat-selector-v2, and that
same ranker with the new envelope. Old selector SHA256:
`abd9d2d1c20edb3ad5cf3282f8a26fca49fb44d508d4ba2ada5ebc9c666b7548`.
New identity combines source-module bytes with the old checkpoint hash; raw rows
record the full identity. Frozen seals bind actual model/tokenizer/runtime files.

## Comparisons and raw evidence

The generated [V2 comparison table](../../artifacts/recall-v2-20261104/table.md),
[summary and resource counters](../../artifacts/recall-v2-20261104/summary.json),
[development answers](../../artifacts/recall-v2-20261104/development.jsonl), and
[heldout answers](../../artifacts/recall-v2-20261104/heldout.jsonl) are the strict
comparison. The [V1 table](../../artifacts/recall-v1-20261104/table.md) preserves
the diagnostic and failed transfer. V1 old outputs reproduce exactly across
before and matched development reruns (36/36 answers).

V1 development old→new was 7→8/12: exact 4→5/6, gist 0→1/2, clear 2→2/2,
ambiguous 0→0/1, missing 1→0/1. V1 nominal heldout was 7→7/12: exact 4→4,
gist 0→1, clear 2→2, ambiguous 0→0, missing 1→0. Strict V2 development was
7→6/12. These are descriptive counts on tiny cases, with no population confidence
or general capability claim. Final V2 counts and detailed costs follow in the
linked generated table and accounting file.

Strict V2 primary results (frozen lexical rubric):

| Split / method | Exact /6 | Gist /2 | Clear /2 | Ambiguous /1 | Missing /1 | All /12 | Unsupported proxy |
|---|---:|---:|---:|---:|---:|---:|---:|
| Development / recent | 0 | 0 | 0 | 0 | 1 | 1 | 1 |
| Development / lexical | 4 | 0 | 1 | 0 | 1 | 6 | 2 |
| Development / old | 4 | 1 | 1 | 0 | 1 | 7 | 2 |
| Development / new | 3 | 1 | 1 | 0 | 1 | 6 | 3 |
| Heldout / recent | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| Heldout / lexical | 2 | 1 | 1 | 0 | 0 | 4 | 2 |
| Heldout / old | 2 | 1 | 1 | 0 | 0 | 4 | 2 |
| Heldout / new | 2 | 1 | 1 | 0 | 0 | 4 | 2 |

The new development regression is an extra exact-code formatting error. Heldout
scores tie by every task category; no primary aggregate or category gain survives.

| Strict heldout failure | Recent | Lexical | Old | New |
|---|---:|---:|---:|---:|
| Exact cases failed /6 | 6 | 4 | 4 | 4 |
| Gist cases failed /2 | 2 | 1 | 1 | 1 |
| Clear reference failed /2 | 2 | 1 | 1 | 1 |
| Ambiguous reference failed /1 | 1 | 1 | 1 | 1 |
| Missing-evidence rubric failed /1 | 1 | 1 | 1 | 1 |
| Evidence-loss diagnosis | 11 | 5 | 5 | 5 |
| Generation despite retained evidence | 1 | 3 | 3 | 3 |

Actual V2 heldout examples: the correct unlock source `H/4: 9_x!` is lost in
preservation; new answers the launch date `2043-03-11`. For the motto source
`Wait?  Five turns.`, new outputs `"Wait? Five turns."`, again losing a space and
adding quotes. Old and new both correctly answer the corrected code `H/3: 9_x!`.
For ambiguous “it,” new answers `clouds drift east`, incorrectly binding weather
text to the requested unlock string. These are answer failures, not memory wins.

Real V1 development examples (literal output strings):

| Case | Required/source | Old answer | New answer |
|---|---|---|---|
| Exact code | `DV:4_q!` | `DV:4_q!` | `DV:4_q!` |
| Exact motto | `Pause:  two steps!` (two spaces) | `"Pause: two steps ahead!"` | `"Pause: two steps!"` |
| Correction | `DV:4_q!`, replacing `DV-OLD` | `DV-OLD` | `DV:4_q!` |
| Revised gist | queue while offline, retry after reconnecting | `Cobalt deletes messages while offline.` | `Cobalt queues messages while offline and retries after reconnection.` |
| Ambiguous “it” | Cobalt and Saffron both plausible; clarify | `It uses the access code DV:4_q!` | `The access code used by Project Saffron is DV-OLD.` |

The new missing-evidence response begins `I'm sorry, but I don't have enough
context to provide an accurate answer to your question.` The frozen matcher
misses this uncertainty phrase and marks failure/unsupported. That is a **rubric
false negative**, not proof of a factual guess. Scores remain unchanged; no
posthoc human annotation is substituted into the primary metric. Conversely,
concept presence does not guarantee every claim in a gist response is supported.
The unsupported column is an obsolete/candidate-value and unsafe-abstention proxy,
not a complete semantic hallucination audit.

To make that distinction concrete, a separate
[posthoc assertion review](../../artifacts/recall-v2-20261104/assertion-review.json)
annotates all 48 strict heldout answers, including its rule and rationale per row.
This is subjective manual **assistant** review, not independent human validation,
and does not replace any frozen score. It flags unsupported world assertions in
7/12 recent, 7/12 lexical, 6/12 old and 4/12 new answers. In particular, lexical
and old invent a **24-hour retention policy** while passing the gist rubric.
That primary gist pass is not evidence of fully faithful meaning. Missing-case
refusals and the new explicit lack-of-information response assert no private
combination, despite failing the narrow clarification matcher. A new independently
frozen semantic rubric would be needed before treating these annotations as a
confirmatory quality improvement.

## Failure attribution and resource accounting

Raw rows save exact histories/questions, pre/post-fit selection IDs, selected
content plus SHA256, actual prompt token IDs, answer, identities, scores, latency
and process RSS. The tokenizer-only reporter independently verifies selected
content against original turns and actual decoded prompts, and recomputes the
frozen rubric. It does not independently adjudicate semantics.

Lost gold evidence is assigned before generation-despite-evidence. A reference
paraphrase in V2 development loses the task-bearing source: weather turns share
the word “project,” while the fact uses “credential.” Both old and new fail.
For ambiguity with both candidates present, guessing is an answer-generation
reference failure, not evidence of selector resolution. No compression damage is
observed: selectors and envelope preserve source bytes. Changed quote bytes are
generated by the language model. Conservative `evidence_retained` requires every
marked source turn, so a correct preservation answer may coexist with a false
whole-world retention flag when an unrelated marked launch turn was dropped.

Bounds are 64 messages /16 KiB UTF-8 content in, eight selected source turns /
4 KiB selected content, 512 rendered prompt tokens and 48 output tokens. Content
limits exclude model weights, Python objects, tokenizer buffers and envelope
overhead. Source budgets reject rather than truncate. There is no durable span
database, cross-request state or learned compressed gist state. SHA256/turn IDs
trace available evidence, not a proof that a generated answer is byte-correct.

[V1 work](../../artifacts/recall-v1-20261104/work.json) and
[V2 work](../../artifacts/recall-v2-20261104/work.json) include full-history
tokenization positions, every repeated fit attempt and its tokens, model prefill
tokens, output tokens and logical scanned content bytes. Selector timings measure
actual ranking and bound-validation work; scanned bytes count logical input, not
every regex/encoding read. The envelope adds a validation pass and formatting
work. It does not reduce the old ranker's full-history scan. Diagnostic selection
and fitting probes repeat work outside request timings; stage wall time includes
them. Tokenizer-only accounting is additional offline audit cost, not inference.
Checkpoint/model startup, energy and FLOPs are not included in per-request totals.
Process RSS high water is cumulative, not a per-method allocation delta.

For the V1 nominal heldout, old→new selected prompts grow 1,856→2,607 tokens,
full-history tokenization grows 8,006→10,171 positions, and observed summed
request latency grows 25.53→33.01 seconds for the same 7/12 rubric score.
Lexical uses 2,045 prompt tokens; recent uses 5,944 and 48,968 fitting-token
positions. All request/probe/stage counters remain in summaries. Shared-host CPU
timings overlap some verification work, use fixed method order and are **not**
a controlled speed benchmark. No quality-preserving total-resource advantage.

Strict V2 heldout full-history accounting, summed over 12 requests per method:

| Method | History tokenization | Fit-token positions / attempts | Model prompt tokens | Output tokens | Logical scan bytes | Request seconds |
|---|---:|---:|---:|---:|---:|---:|
| Recent | 8,138 | 50,782 /87 | 5,886 | 167 | 0 selector scan | 57.25 |
| Lexical | 8,138 | 2,152 /12 | 2,152 | 207 | 20,451 | 40.50 |
| Old | 8,138 | 1,816 /12 | 1,816 | 191 | 20,451 | 33.94 |
| New | 10,304 | 2,552 /12 | 2,552 | 221 | 20,451 | 41.23 |

Zero selector scan for recent excludes its full-history tokenization and repeated
fitting. Old→new prompt cost rises 40.5%, full-history tokenization 26.6%, with
unchanged 4/12 primary accuracy. Maximum selected source content is 350 bytes
for lexical/old/new, below 4 KiB. Process cumulative high-water RSS is
2,469,519,360 bytes (about 2.30 GiB), dominated by the shared backbone/runtime.
V2 parent development/heldout commands take 181.41/184.55 seconds including
startup, probes and writing. V1 before/development/heldout and V2 together generate
228 answers; all raw outputs remain available. No fitting/training cost is added.

## Engineering, CI and reproduction

Raw commands, exact argv, exits, source fingerprints and logs are under
[checks](../../artifacts/recall-v1-20261104/checks/); final accounting consolidates
them. Final full Python suite: **183 passed**, exit 0; nine new focused tests
also pass. Strict runtime mypy passes on 29 source files for Windows and Linux;
the research-driver invocation checks 33 files with the stated suppressions.
Node syntax exits 0, ordinary Node tests have 13 passes/one optional live skip,
and the separately enabled live page suite has two passes/no skips.
Python CLI ordinary/recurrent smoke, checkpoint resume, validation and
summarization pass. Source tests cover exact spans, correction ordering, unrelated
facts, clear/ambiguous candidates, missing evidence, input/storage limits,
checkpoint compatibility, template separation, drift rejection and overwrite
refusal. Local Node syntax/tests, real chat and page handlers pass. The latter use
a DOM harness, with real proxy/inference; an interactive browser was not run.
The browser/server path is unchanged and does not load the research envelope.

| Check group | Final exit code / outcome |
|---|---|
| V1/V2 inference and scoring verification | 0; execution only, quality negative |
| Full Python suite / focused new tests | 0; 183 /9 passed |
| Focused lint /format | 0 /0 |
| Full repository lint /format | 1 /1; historical frozen-script findings retained |
| Strict runtime types Windows /Linux | 0 /0; 29 files |
| Research types with documented suppressions | 0; unsuppressed initial run 1 |
| Node syntax /tests /live page handlers | 0 /0 /0 |
| Local chat, CLI and integration smoke | 0 |
| pip check /fresh package build /installed wheel import and CLI | 0 /0 /0 |
| git diff --check | 0 |

Full repository lint/format fail on the three existing frozen selector scripts;
they remain unchanged. Changed code's focused lint/format passes. Six E501 lines
in the sealed V1 driver are explicitly ignored to preserve its registered prompt
bytes. Runtime mypy passes strictly; research-driver checking suppresses
`import-untyped` for psutil and `misc` for intentional backend class substitution.
The initial unsuppressed three-error log is retained. An initial Node check wrapper
hit Windows cp1252 printing after tests passed; a UTF-8 rerun passes. Default
package output failed on an existing dist archive's Windows access permissions;
a fresh output directory succeeds. These failures are preserved, not erased.

For base HEAD, fresh [Actions run 41679017878](https://github.com/ShamGaneshan2008/Toruk/actions/runs/41679017878)
has web success, Python failure at Ruff, subsequent Python format/types/tests/build
skipped. [Remote evidence](../../artifacts/recall-v1-20261104/remote-ci.json)
distinguishes the exact base SHA from new uncommitted work, which is **NOT_RUN
remotely**. Local passes are not remote CI success. No paid job or deployment.

PowerShell reproduction (use fresh output directories; locally retained pinned
weights and installed chat/dev dependencies are required):

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
$run = 'artifacts/recall-v2-replay'
& $py scripts/recall_v2.py register --run $run
if ($LASTEXITCODE -ne 0) { throw 'Registration failed' }
& $py scripts/recall_v2.py development --run $run
if ($LASTEXITCODE -ne 0) { throw 'Development execution failed' }
& $py scripts/recall_v2.py heldout --run $run
if ($LASTEXITCODE -ne 0) { throw 'Heldout execution failed' }
& $py scripts/report_recall.py --run $run
& $py -m pytest -q -p no:cacheprovider
& $py -m ruff check src/toruk_lm/source_spans.py scripts/recall*.py scripts/report_recall.py tests/test_recall*.py tests/test_source_spans.py
& $py -m mypy
& $py -m mypy --platform linux
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
& $py scripts/smoke_chat_foundation.py --backbone-dir artifacts/qwen-chat-001/backbone --selector-checkpoint artifacts/chat-selector-v2-20261101/selector.json --output-dir artifacts/recall-chat-replay
& $py scripts/smoke_qualification_ui.py --output-dir artifacts/recall-page-replay
& $py -m pip check
& $py -m build --no-isolation --outdir artifacts/recall-package-replay
git diff --check
```

Execution exit 0 means the experiment ran, not that quality passed. There is no
preregistered release-quality threshold in this small diagnostic. Original V1
replay requires the original registered source layout; V2 is the corrected study.

## Separate verdicts

| Question | Verdict |
|---|---|
| Exact recall | **Not established.** Literal source retention works within bounds; generated strings can still change quotes, spaces, values and formatting. |
| Gist recall | **Limited synthetic successes; inconclusive generally.** No compressed-gist sufficiency experiment or guarantee of all factual claims. |
| Vague references | **Not established.** Some single-candidate cases work; paraphrase retrieval and genuine ambiguity still fail. Clarification is permitted but not enforced. |
| Token efficiency | **Not established.** Full history is still processed; envelope adds prompt and formatting cost, without a reliable quality advantage. |

Implementation files are `src/toruk_lm/source_spans.py`, four new research scripts
and four focused test files. Documentation includes both versioned protocols,
this report, the public architecture/README and the new explanation notebook.
Private implementation notes are updated in ignored
`docs/internal/recall-v1-architecture.md`; they are not added to public packages.
Both artifact directories retain raw inputs, seals, outputs, costs and failures.
The final accounting file records exact changed paths, Git status and final
command exits. No historical artifact or checkpoint was rewritten.

The subsequent [fixed-budget follow-up](rank-budget-v1-results.md), starting at
`84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`, reproduces all 96 V2 prompts,
answers and deterministic resource counters exactly before testing one cutoff
ablation. Correctness rises 4/12 to 8/12 on the same published heldout questions,
but the unsupported proxy rises 2/12 to 3/12 and a correction answer becomes
obsolete. Its preregistered success criterion fails. Original V1/V2 evidence and
scores above remain unchanged; the candidate is research-only.

See [final command ledger and Git status](../../artifacts/recall-v2-20261104/final-accounting.md)
and its [machine-readable record](../../artifacts/recall-v2-20261104/final-accounting.json).
The working tree contains three modified tracked files plus the new code, tests,
documentation and evidence directories. Private notes remain ignored. No commit
or push was made; new work has no remote CI run.
