# Segment delta development v1: diagnosis of the shared zero

20 November 2026. Development only. **The saved LMs fail to produce the answer
format or terminate, rather than producing 144 correct main-model answers that
the scorer loses.** All six main cells return unrelated eight-byte continuations
on all 24 cases. The lexical control has a handwritten lookup/copy procedure and
constructs EOS explicitly; it bypasses the learned behavior that fails here.

The strongest supported explanation is failure to acquire the common answering
task under this training setup. The small exposure and predominantly non-answer
objective are plausible contributors, not experimentally isolated causes. There
is no verified tokenizer, checkpoint-loading, label-order, or scorer defect.
The exact-answer floor cannot identify a relative memory-architecture effect.

## Scope and repository receipt

Confirmed working directory and Git root: `D:\Toruk` (`D:/Toruk` from Git).
Branch: `main`. HEAD: `febb3c5ebc8acf36bf60746515084d8e009bb231`.
Initial `git status --short` was empty. This is the diagnosis starting revision;
the historical study began at `ab6d3a65538b5f33d17efe4f45189906f1394a38`.
Only this report and the new read-only
[diagnostic script](../../scripts/diagnose_segment_delta_dev.py) are additions.
Changes are left uncommitted.

Read the unchanged [protocol](segment-delta-dev-v1-protocol.md),
[results](segment-delta-dev-v1-results.md),
[commit review](segment-delta-dev-v1-commit-review.md), and the frozen run sources
and artifacts linked below. No retraining, new forward passes, answer generation,
held-out file access, scorer/gate edits, or production-chat edits were performed.
Checkpoint inspection includes strict loading, without model execution.

## Evidence and integrity

The [registration](../../artifacts/segment-delta-dev-v1/registration.json) hashes to
`bb828757efe6f4073d7d1c74405aa7c73120e11fcfdfff6c09b8a95812e1d2dd`;
the [implementation lock](../../artifacts/segment-delta-dev-v1/implementation-lock.json)
hashes to `8711afee882f4e4837e4048a878447c1d1706220ca72faa7ed5270c07e878984`.
The new check verifies these exact seals, all registered data hashes, protocol
and implementation snapshots, all eleven prediction seals and first-case
replays, training traces, and optional strict checkpoint loads. The existing
read-only review also passes against HEAD, including all six checkpoint payloads
and the frozen no-go/cost arithmetic. Historical evidence remains unchanged.

The audit inputs are [train](../../artifacts/segment-delta-dev-v1/train.json),
[development prefixes](../../artifacts/segment-delta-dev-v1/inputs.json),
[development evaluator labels](../../artifacts/segment-delta-dev-v1/labels-evaluator-only.json),
[development prose](../../artifacts/segment-delta-dev-v1/dev-prose.json),
[manifest](../../artifacts/segment-delta-dev-v1/data-manifest.json), and
[summary](../../artifacts/segment-delta-dev-v1/summary.json).
Frozen executable sources:
[data/scorer](../../artifacts/segment-delta-dev-v1/implementation-sources/scripts/segment_delta_data.py),
[worker/lexical control](../../artifacts/segment-delta-dev-v1/implementation-sources/scripts/segment_delta_study.py),
[training/loader](../../artifacts/segment-delta-dev-v1/implementation-sources/src/toruk_lm/segment_delta_training.py),
[stream/loss/decoder](../../artifacts/segment-delta-dev-v1/implementation-sources/src/toruk_lm/segment_delta.py),
[tokenizer](../../artifacts/segment-delta-dev-v1/implementation-sources/src/toruk_lm/tokenizer.py).

## Failure taxonomy and counts

The unit is a saved scored prediction, excluding the deterministic replay:
144 main predictions plus 96 delta ablation predictions = 240. The ten first-case
LM replays add no independent cases and repeat the same classification. Lexical
has 24 scored predictions plus one replay and was run once, without a fit seed.

These are observable output categories, not claims about inaccessible internal
memory:

- **M: repetitive or malformed generation.** Output is neither a complete answer
  from the declared inventory nor a whole leading gold answer. Here every such
  output is an eight-byte fragment without EOS. This includes prose fragments,
  broken query fragments, and loops; repetition is not required for M.
- **P: answer present but rejected.** The output starts with the entire gold
  value followed by whitespace (or ends immediately), but violates exact closure.
  The two observed instances are `la hum t`, gold `la`. This is a surface-prefix
  observation, not proof of retrieval: the same cells start with `la` on several
  questions whose answers differ.
- **Missing fact:** a known-answer case lacks the required source assignment.
  The independent last-assignment check finds none. Four intentionally unknown
  cases correctly have no assignment and require `?`; those are not missing-data
  failures.
- **Wrong field / wrong value:** a complete, closed answer demonstrably selects
  another field or another value. None is observed. Shared value inventories also
  prevent inferring a field source from an incidental substring.
- **Refusal/empty:** explicit refusal, no output, or EOS alone. None is observed.
  Unknown cases contain unsupported continuations, not abstentions.

Primary labels are exclusive; P takes precedence over M. Wrong-value labels
require a complete answer, so `la hums.` on gold `tu` remains M. Classifying such
fragments as factual substitutions would invent a successful answer parser.

| Seed | Model/cell | M | P | Missing fact | Wrong field | Wrong value | Refusal/empty | Exact | EOS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 113 | ordinary | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 113 | recurrent | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 113 | delta | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 113 | delta no-read | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 113 | delta no-write | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 227 | ordinary | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 227 | recurrent | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 227 | delta | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 227 | delta no-read | 23 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 227 | delta no-write | 23 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Total LM | | 238 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Separate lexical | no seed | 0 | 0 | 0 | 0 | 0 | 0 | 24 | 24 |

All LM cells score 0/4 in each of distant, correction, related-field, unknown,
exact-copy, and local. Failure labels are M for all four cases in each category,
except seed227 no-read/no-write distant: 3 M + 1 P each. All 40 unknown LM
predictions fail to emit `?` followed by EOS.

## Representative raw evidence

The first saved input is exactly:

```text
zim city=la
wind d000 hums. rain falls. rain
zim city?=
```

For gold `la`, the required IDs are `[111,100,2]`. Saved main outputs include:

| Cell/case | Generated IDs | Decoded bytes | Interpretation |
| --- | --- | --- | --- |
| [delta113 f000](../../artifacts/segment-delta-dev-v1/stages/generate-113-delta-full/predictions.jsonl) | `[119,124,64,119,124,64,119,124]` | `ty=ty=ty` | Broken query/assignment loop; no answer or EOS |
| [ordinary113 f000](../../artifacts/segment-delta-dev-v1/stages/generate-113-ordinary-full/predictions.jsonl) | `[111,118,35,117,100,111,100,108]` | `ls ralai` | Malformed text; interior `la` is not an answer |
| [recurrent113 f000](../../artifacts/segment-delta-dev-v1/stages/generate-113-recurrent-full/predictions.jsonl) | `[119,124,64,119,124,64,35,119]` | `ty=ty= t` | Loop then fragment |
| [delta227 f000](../../artifacts/segment-delta-dev-v1/stages/generate-227-delta-full/predictions.jsonl) | `[118,35,105,100,111,111,118,49]` | `s falls.` | Filler-like continuation, not an answer |
| [ordinary227 f000](../../artifacts/segment-delta-dev-v1/stages/generate-227-ordinary-full/predictions.jsonl) | `[105,100,111,111,111,111,118,49]` | `falllls.` | Malformed filler with repeated letters |
| [recurrent227 f000](../../artifacts/segment-delta-dev-v1/stages/generate-227-recurrent-full/predictions.jsonl) | `[108,113,35,105,100,111,118,49]` | `in fals.` | Malformed filler |
| [delta227 no-read f000](../../artifacts/segment-delta-dev-v1/stages/generate-227-delta-no-read/predictions.jsonl) | `[111,100,35,107,120,112,35,119]` | `la hum t` | P: correct leading value, extra text and no EOS |
| [lexical f000](../../artifacts/segment-delta-dev-v1/stages/lexical/predictions.jsonl) | `[111,100,2]` | `la` + EOS | Exact |

All 240 LM outputs are valid ASCII bytes, exactly eight generated IDs, and
`budget_exhausted=true`; none contains EOS, PAD, or BOS. They are not Unicode
replacement/decoding artifacts. Every gold answer plus EOS needs only 2–4 IDs;
the cap8 can hold every required answer. Increasing it cannot repair an already
wrong initial continuation; the saved evidence does not predict later tokens.

Nine LM outputs contain gold bytes somewhere, counting both ablations. Only the
two P outputs have a whole leading gold value. The other seven are incidental
substrings such as `la` inside `ralai`, `laity=fa`, `lain ral`, or `alllals.`,
and `?` inside the copied query fragment `n city?=`. Three such interior matches
occur in main cells. No main output starts with a whole gold value followed by
an answer boundary. Substring scoring would award malformed fragments and would change
the task; it was not used to revise any score or gate.

## Audit of the shared path

### Train/development separation

The 160 training documents are 128 factual + 32 prose; development is 24 factual
+ 8 prose. IDs and complete texts are disjoint; frozen data hashes pass. The
training loader accepts only `split=train`. Each of the 20 known development
labels agrees with the last matching assignment in its history; the four other
labels are `?`. No input-label reorder is present in raw prediction/loss rows.

This is synthetic IID separation, not unseen-entity or unseen-value testing:
the same four names, four city values, four punctuation-sensitive codes, fields,
and grammar recur. Split-specific `tNNN`/`dNNN` filler nonces make complete texts
different. All nine possible answer strings occur in training. That limited
separation does not explain missing labels, but it limits generalization claims.

Generation code reads prefixes and the saved checkpoint, without opening the
evaluator label file. Loss workers subsequently read gold and teacher-force
`prefix + gold`; they never replace generated IDs. This is verified in the
sealed source and recorded stage structure, not an OS-level file-access trace.

### Tokenizer, prompt, loss targets, and segment boundaries

The tokenizer has no fitted vocabulary: 259 IDs, PAD0/BOS1/EOS2, UTF-8 byte+3.
For every raw prediction, saved native input IDs exactly equal BOS plus the
saved prefix bytes. Training uses BOS + complete document + EOS, shifted by one
target. The final training question `name field?=value` and development prefix
`name field?=` agree; there is no missing chat template, role marker, instruction
token, or alternate tokenizer required by this model. It has no pretrained
instruction-following weights.

`document_loss` and `ResearchSession` both start at BOS, partition into the same
nonoverlapping 24-ID segments, reset positions within each segment, and reset
document memory between cases. The inference stream continues through the
question without a flush. A full segment commits once; partial-prefix updates
are discarded/recomputed from entering state. Source inspection shows the same
target shift in training and teacher-forced evaluation. The evaluator's
`answer_start=len(prefix.encode())` correctly starts at the first gold-byte
target, and includes the final EOS; it does not skip the first answer byte.

**A benchmark-design limitation is directly visible:** distance<=24 does not
ensure the evidence fits the ordinary model's current segment. At the first
answer, the local cases have these exact visible contexts (JSON escapes):

| Case | Evidence-end to query-end bytes | Input length including BOS mod24 | Context producing first-answer logits |
| --- | ---: | ---: | --- |
| dev-f005 | 10 | 8 | `"m city?="` |
| dev-f011 | 10 | 16 | `"ty=so\nuvo city?="` |
| dev-f017 | 10 | 0 | `"l\nuvo city=la\nuvo city?="` |
| dev-f023 | 10 | 8 | `"x city?="` |

Only f017 contains the entire assignment and query together. For f011 the value
is visible but the entity and start of the field are truncated. f005/f023 expose
no assignment at all. At phase0, the first answer is predicted by the previous
full segment, then ordinary loses that context on the next consumed byte.
For exact-copy f016, the first-answer local context is just `=` (phase1), even
though the full query is in the saved input. Recurrent/delta can in principle
use entering state; ordinary cannot. Thus even the local subset is not a clean
four-case test of ordinary copying. This follows the registered schedule and
does not establish an implementation mismatch. The full-evidence f017 still
fails in all three main models at both seeds; no reliable basic answer behavior
is demonstrated even on that case.

### Checkpoints and training exposure

All six local `.pt` files are present and match saved SHA256/byte metadata.
The strict loader succeeds for each: correct format, variant, seed/config,
tokenizer, source/data/runtime identities, drained boundary, next step128,
cursor256, exact consumed targets, finite tensors, complete optimizer moments
at step128, and exact equality of loaded weights to saved tensors. Generation
workers hash-check the checkpoint before loading and check variant/seed/progress.
This rules out a detectable wrong-cell, stale-step, partial, incompatible, or
random-weight reload in the saved loading path. It does not reconstruct a
historical process's RAM or provide new generation evidence.

The machine-readable training logs are `checkpoint.trace.jsonl` and
`training.json`; all six `output.log` files are empty, not additional loss traces.
The full parameter count has gradients in the saved training statistics. Trace
steps, example IDs and target counts match across all three models at each seed.
Each fit has 128 updates x2 documents =256 presentations of all160 unique
documents: one full pass plus96 documents of a second pass (1.6 passes).

| Seed/model | Trace | Checkpoint metadata | First16 mean NLL | Last16 mean NLL | Last update NLL |
| --- | --- | --- | ---: | ---: | ---: |
| 113 ordinary | [trace](../../artifacts/segment-delta-dev-v1/stages/train-113-ordinary/checkpoint.trace.jsonl) | [metadata](../../artifacts/segment-delta-dev-v1/stages/train-113-ordinary/checkpoint-meta.json) | 5.1723 | 1.1095 | 0.9931 |
| 113 recurrent | [trace](../../artifacts/segment-delta-dev-v1/stages/train-113-recurrent/checkpoint.trace.jsonl) | [metadata](../../artifacts/segment-delta-dev-v1/stages/train-113-recurrent/checkpoint-meta.json) | 5.3060 | 1.2614 | 1.1994 |
| 113 delta | [trace](../../artifacts/segment-delta-dev-v1/stages/train-113-delta/checkpoint.trace.jsonl) | [metadata](../../artifacts/segment-delta-dev-v1/stages/train-113-delta/checkpoint-meta.json) | 5.2242 | 1.1520 | 1.1235 |
| 227 ordinary | [trace](../../artifacts/segment-delta-dev-v1/stages/train-227-ordinary/checkpoint.trace.jsonl) | [metadata](../../artifacts/segment-delta-dev-v1/stages/train-227-ordinary/checkpoint-meta.json) | 5.2666 | 1.2493 | 1.0404 |
| 227 recurrent | [trace](../../artifacts/segment-delta-dev-v1/stages/train-227-recurrent/checkpoint.trace.jsonl) | [metadata](../../artifacts/segment-delta-dev-v1/stages/train-227-recurrent/checkpoint-meta.json) | 5.1477 | 1.3424 | 1.0315 |
| 227 delta | [trace](../../artifacts/segment-delta-dev-v1/stages/train-227-delta/checkpoint.trace.jsonl) | [metadata](../../artifacts/segment-delta-dev-v1/stages/train-227-delta/checkpoint-meta.json) | 5.1204 | 1.2314 | 0.9827 |

These are means of logged minibatch objectives with different document mixtures,
not repeated evaluation of a fixed training set. All traces are finite and
decline substantially; they do not show absent optimization or numerical
divergence. They fluctuate, and do not establish convergence or answer mastery.
The script emits all eight consecutive16-step means for reproducibility.

Uniform next-token CE gives almost all weight to history, filler, source
assignments and prose:

| Exposure per fit | Seed113 | Seed227 |
| --- | ---: | ---: |
| All byte/EOS targets | 26,523 | 25,926 |
| Factual / prose presentations | 207 / 49 | 205 / 51 |
| Answer suffix targets including EOS | 620 (2.34%) | 617 (2.38%) |
| EOS targets across all documents | 256 (0.97%) | 256 (0.99%) |

In the unique160-document file, factual answers plus their EOS contribute
384/16,493 targets (2.33%). There is no extra answer weight, answer-only stage,
or local-answer competence prerequisite. EOS is supervised; its absence in
generation is not caused by omitting EOS labels.

Saved development losses expose what the full-document average hides:

| Seed/model | Full factual NLL | Answer suffix NLL | Prose NLL |
| --- | ---: | ---: | ---: |
| 113 ordinary | 0.9818 | 3.7727 | 2.1367 |
| 113 recurrent | 1.0990 | 3.6014 | 2.3603 |
| 113 delta | 1.0124 | 3.5633 | 2.2005 |
| 227 ordinary | 1.0072 | 3.9014 | 2.3141 |
| 227 recurrent | 1.0813 | 3.8635 | 2.4618 |
| 227 delta | 0.9943 | 3.7610 | 2.2080 |

Each loss worker records 2,740 factual targets but only72 answer/EOS targets;
separate prose has548. These are teacher-forced losses, not free-generation
accuracy. Lower NLL on repeated filler can coexist with all wrong answers.
Suffix aggregates do not reveal individual first-byte/EOS ranks, or whether
training-set questions were ever answered correctly; those logits/predictions
were not saved. No such missing measurements were manufactured for this audit.

### Decoding and scorer behavior

The sealed decoder uses greedy argmax, suppresses only PAD/BOS, leaves EOS
eligible, and stops on EOS or eight IDs. Returned IDs show the failure before
display decoding. There is no forced-answer vocabulary, beam search, sampling,
or postprocessing. Per-request caps did not interrupt these predictions.

The frozen scorer compares the full ID sequence to UTF-8 gold bytes+3 then EOS.
The new audit executes that frozen function and reproduces every saved
correctness boolean. Simple static scorer checks confirm `[111,100,2]` passes
for `la`; missing EOS, leading space, and extra output fail. These are checks
of a pure scorer, not generated replacement answers. Gold lengths, native IDs,
label order, and lexical success all agree. No tokenizer/scorer disagreement or
plausible correctly framed main answer hidden by exact matching is found.

All predictions also lack EOS, so this is a universal closure failure plus
wrong content in every main output. The evidence cannot partition that into
independent causal shares. More tokens, trimming, or accepting interior gold
substrings would not establish that the LMs learned the requested task.

### Why lexical succeeds

The frozen lexical function splits history into lines, overlaps the query's two
alphanumeric terms with each line, breaks ties by recency, and copies the RHS of
`=` only when both terms match; otherwise it returns `?`. It then directly
constructs byte IDs and EOS. The synthetic grammar is designed so this selects
the latest correct entity/field, avoids distractors, handles absent fields, and
preserves punctuation. Its raw predictions reproduce24/24 with the same scorer.

It keeps/scans full raw history (up to164 history bytes here), while the LMs must
learn an answer decoder and, for older segments, a useful bounded state. Lexical
is evidence that labels and grammar are soluble, not a matched learned baseline,
a tokenizer check sufficient on its own, or evidence for neural retention.

## Verified findings versus hypotheses

| Claim | Evidence status |
| --- | --- |
| All main models emit malformed eight-byte non-EOS fragments; no exact answers | Directly verified from144 saved main predictions |
| The same failure extends to ablations; only two whole leading gold values occur | Directly verified from96 ablation predictions; both are P, not exact |
| Weights were optimized and valid final checkpoints load strictly | Finite decreasing traces, saved gradients/moments/progress, hashes and strict reload |
| The loss budget is dominated by non-answer targets | Direct target accounting; answer/EOS share approximately2.3% |
| Segment phase prevents a clean four-case ordinary local-copy control | Direct saved-prefix slicing and sealed stream schedule |
| Training under this setup did not yield usable task behavior | Direct result; applies to these configurations and fixed budget |
| Insufficient exposure, sparse answer supervision, or capacity caused the common failure | Supported hypotheses; no budget/objective/capacity intervention was run |
| Filler patterns dominate learned greedy behavior | Consistent with raw fragments and loss distribution; model-internal causal account unverified |
| A longer fit, different objective, or larger model would succeed | Unknown |
| An evaluation bug explains the shared zero | No verified defect found; cannot exclude all unobserved historical faults |
| Delta cannot retain facts under any setup | Unsupported by this experiment |

## Can this benchmark compare architectures?

It can enforce the registered feasibility decision: every quality gate fails
and delta also fails the fixed cost advantages. It cannot meaningfully rank
factual retention when every main/ablation cell is at the exact-answer floor,
including local tasks. Removing read/write changes NLL, but loses zero exact
answers; the no-read/no-write outputs and loss summaries are identical within
each seed, consistent with zero entering state when writing is disabled.
This is no positive memory-dependence result.

Teacher-forced NLL and measured costs remain descriptive whole-configuration
comparisons; width/FFN differences and the shared segment schedule limit causal
architecture attribution. Delta's smaller answer NLL at a seed does not become
an answer-accuracy gain. The known cold cost ratios still reject the v1 gates:
delta/recurrent inference CPU1.099/1.026, wall1.055/1.018; training CPU1.759/1.691,
wall1.636/1.635 (seeds113/227). Nothing in this diagnosis upgrades that no-go.

## Offline reproduction and checks

Run from Windows PowerShell in the existing environment; no installation,
network call, historical run controller, training, or generation is needed:

```powershell
Set-Location D:\Toruk
git rev-parse --show-toplevel
git rev-parse HEAD
git status --short
.\.venv\Scripts\python.exe -B scripts/diagnose_segment_delta_dev.py --checkpoints --cases
.\.venv\Scripts\python.exe -B artifacts/segment-delta-dev-v1-commit-review-001/review.py --revision HEAD --inspect-checkpoints
.\.venv\Scripts\python.exe -m ruff check scripts/diagnose_segment_delta_dev.py
.\.venv\Scripts\python.exe -m ruff format --check scripts/diagnose_segment_delta_dev.py
git diff --check
```

`--cases` prints every raw saved ID sequence, decoded string, primary failure,
incidental gold-substring flag, first-answer segment context, and source path/line.
`--checkpoints` hashes and strictly reloads the six existing local checkpoints;
it constructs model/optimizer objects but does no forward or optimizer step.
Omit that flag on a checkout lacking the git-ignored checkpoint bytes; that
reduced audit cannot claim strict checkpoint verification. The script writes
only stdout. `-B` suppresses Python bytecode writes.

The existing review command checks historical committed evidence. New diagnostic
classification, data/scorer assertions, strict reloads, lint/format, and whitespace
checks pass locally. This is a scoped offline audit, not a full suite or hosted CI
claim. Original tests that fit models or generate fixture answers were not rerun.
For an untracked new file, also check whitespace with
`git diff --no-index --check -- NUL <new-file>` for each of the two additions.
Those comparisons returned1 for added content and emitted no whitespace errors;
the Python file also produced Git's normal LF-to-CRLF working-copy notice.
The regular `git diff --check` returned0. A separate table/link check verified
all240 displayed prediction strings and labels, all eight representative ID
arrays, and all47 local links against their saved sources.

## Complete per-prediction classification

Each cell below is **M unless explicitly marked P**. Strings are JSON quoted to
preserve whitespace and `\n`; no output is repaired. Within each linked raw file,
f000 through f023 are lines1–24, and line25 is the f000 replay. The script's
`--cases` output also carries native IDs and source line numbers.

### Seed113

Raw files: [ordinary](../../artifacts/segment-delta-dev-v1/stages/generate-113-ordinary-full/predictions.jsonl),
[recurrent](../../artifacts/segment-delta-dev-v1/stages/generate-113-recurrent-full/predictions.jsonl),
[delta](../../artifacts/segment-delta-dev-v1/stages/generate-113-delta-full/predictions.jsonl),
[no-read](../../artifacts/segment-delta-dev-v1/stages/generate-113-delta-no-read/predictions.jsonl),
[no-write](../../artifacts/segment-delta-dev-v1/stages/generate-113-delta-no-write/predictions.jsonl).

| Case | Category | Gold | Ordinary | Recurrent | Delta | Delta no-read | Delta no-write |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev-f000 | distant | `la` | `"ls ralai"` | `"ty=ty= t"` | `"ty=ty=ty"` | `"ty=tyls."` | `"ty=tyls."` |
| dev-f001 | correction | `tu` | `"ls ralai"` | `"l=lin t0"` | `"ty=ty=ty"` | `"lllalls."` | `"lllalls."` |
| dev-f002 | related_field | `so` | `"ls ralai"` | `"l=lin t0"` | `"ty=ty=ty"` | `"lllalls."` | `"lllalls."` |
| dev-f003 | unknown | `?` | `"ls ralai"` | `"l=lin t0"` | `"ty=tyls."` | `"lllalls."` | `"lllalls."` |
| dev-f004 | exact_copy | `R-7` | `"m rals. "` | `"ls. rain"` | `"lllllls."` | `"llllls. "` | `"llllls. "` |
| dev-f005 | local | `tu` | `"ls ralai"` | `"ty=ty= t"` | `"ty=ty=ty"` | `"ty=tyls."` | `"ty=tyls."` |
| dev-f006 | distant | `la` | `"m ty=m h"` | `"tyin rai"` | `" rain fa"` | `" rain fa"` | `" rain fa"` |
| dev-f007 | correction | `tu` | `"m ty=m h"` | `"tyin rai"` | `" rain fa"` | `" rain fa"` | `" rain fa"` |
| dev-f008 | related_field | `tu` | `"m ty=ls."` | `"tyin rai"` | `"ty= fain"` | `"tyin ral"` | `"tyin ral"` |
| dev-f009 | unknown | `?` | `"m ty=m h"` | `"tyin rai"` | `"tyin rai"` | `" rain fa"` | `" rain fa"` |
| dev-f010 | exact_copy | `Q_2` | `"l ain he"` | `" rain fa"` | `" rain fa"` | `" t0y=lin"` | `" t0y=lin"` |
| dev-f011 | local | `so` | `"m ty=m h"` | `"tyin rai"` | `"ty?== fa"` | `" rain fa"` | `" rain fa"` |
| dev-f012 | distant | `mi` | `"lls. rai"` | `"n city?="` | `"lls. rai"` | `"lls. rai"` | `"lls. rai"` |
| dev-f013 | correction | `tu` | `"lls. rai"` | `"n city?="` | `"lls. rai"` | `"lls. rai"` | `"lls. rai"` |
| dev-f014 | related_field | `la` | `"lls. rai"` | `"n city?="` | `"lls. rai"` | `"lls. rai"` | `"lls. rai"` |
| dev-f015 | unknown | `?` | `"lls. rai"` | `"n city?="` | `"lls. rai"` | `"lls. rai"` | `"lls. rai"` |
| dev-f016 | exact_copy | `V:4` | `"ls. rain"` | `"nd c rai"` | `"ls. rain"` | `"ls. rain"` | `"ls. rain"` |
| dev-f017 | local | `la` | `"lls. rai"` | `"n city?="` | `"nd fa ra"` | `"nd huy=l"` | `"nd huy=l"` |
| dev-f018 | distant | `mi` | `"ls ralai"` | `"l=lin t0"` | `"ty=ty=ty"` | `"lllalls."` | `"lllalls."` |
| dev-f019 | correction | `tu` | `"ls ralai"` | `"l=lin t0"` | `"ty=ty=ty"` | `"lllalls."` | `"lllalls."` |
| dev-f020 | related_field | `tu` | `"ls ralai"` | `"l=lin t0"` | `"ty=ty=ty"` | `"lllalls."` | `"lllalls."` |
| dev-f021 | unknown | `?` | `"ls ralai"` | `"ty=ty= t"` | `"ty=ty=ty"` | `"ty=tyls."` | `"ty=tyls."` |
| dev-f022 | exact_copy | `Z!6` | `"m ralain"` | `"ls. rain"` | `"ty=ty=ty"` | `"llalls. "` | `"llalls. "` |
| dev-f023 | local | `so` | `"ls ralai"` | `"l=lin t0"` | `"ty=tyls."` | `"lllalls."` | `"lllalls."` |

### Seed227

Raw files: [ordinary](../../artifacts/segment-delta-dev-v1/stages/generate-227-ordinary-full/predictions.jsonl),
[recurrent](../../artifacts/segment-delta-dev-v1/stages/generate-227-recurrent-full/predictions.jsonl),
[delta](../../artifacts/segment-delta-dev-v1/stages/generate-227-delta-full/predictions.jsonl),
[no-read](../../artifacts/segment-delta-dev-v1/stages/generate-227-delta-no-read/predictions.jsonl),
[no-write](../../artifacts/segment-delta-dev-v1/stages/generate-227-delta-no-write/predictions.jsonl).

| Case | Category | Gold | Ordinary | Recurrent | Delta | Delta no-read | Delta no-write |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev-f000 | distant | `la` | `"falllls."` | `"in fals."` | `"s falls."` | `"la hum t"` **P** | `"la hum t"` **P** |
| dev-f001 | correction | `tu` | `"falllls."` | `"in fals."` | `"s falls."` | `"la hums."` | `"la hums."` |
| dev-f002 | related_field | `so` | `"\nwin  fa"` | `"in fals."` | `"s. fals."` | `"la hum t"` | `"la hum t"` |
| dev-f003 | unknown | `?` | `"falllls."` | `"in fals."` | `"s. fals."` | `"la hums."` | `"la hums."` |
| dev-f004 | exact_copy | `R-7` | `" allls. "` | `"r fain f"` | `"fallls. "` | `"humod t0"` | `"humod t0"` |
| dev-f005 | local | `tu` | `"falllls."` | `"in fals."` | `"in fals."` | `"la hum t"` | `"la hum t"` |
| dev-f006 | distant | `la` | `"rain als"` | `"laity=fa"` | `"s. ty=fa"` | `"lain ral"` | `"lain ral"` |
| dev-f007 | correction | `tu` | `"rain als"` | `"laity=fa"` | `"s. ty=fa"` | `"lain ral"` | `"lain ral"` |
| dev-f008 | related_field | `tu` | `"rain ait"` | `"laity=fa"` | `"s. ty=fa"` | `"laity=fa"` | `"laity=fa"` |
| dev-f009 | unknown | `?` | `"rain ait"` | `"laity=fa"` | `"s. ty=fa"` | `"lain ral"` | `"lain ral"` |
| dev-f010 | exact_copy | `Q_2` | `"ain alll"` | `"rain fal"` | `"s. raifa"` | `"lity=lal"` | `"lity=lal"` |
| dev-f011 | local | `so` | `" rain fa"` | `"laity=fa"` | `"s. ty=fa"` | `"lain ral"` | `"lain ral"` |
| dev-f012 | distant | `mi` | `"lls. rai"` | `"lls. rai"` | `"s. r rai"` | `"alllals."` | `"alllals."` |
| dev-f013 | correction | `tu` | `"lls. rai"` | `"lls. rai"` | `"s. r rai"` | `"lls. rai"` | `"lls. rai"` |
| dev-f014 | related_field | `la` | `"lls. rai"` | `"lls. rai"` | `"s. r rai"` | `"alllals."` | `"alllals."` |
| dev-f015 | unknown | `?` | `"lls. rai"` | `"lls. rai"` | `"s. r rai"` | `"alllals."` | `"alllals."` |
| dev-f016 | exact_copy | `V:4` | `"ls. rain"` | `"ain city"` | `"s. tyain"` | `"ain city"` | `"ain city"` |
| dev-f017 | local | `la` | `"lls. rai"` | `"lls. rai"` | `"s. r rai"` | `"lls. rai"` | `"lls. rai"` |
| dev-f018 | distant | `mi` | `"falllls."` | `"in fals."` | `"s falls."` | `"la hums."` | `"la hums."` |
| dev-f019 | correction | `tu` | `"falllls."` | `"in fals."` | `"s falls."` | `"la hums."` | `"la hums."` |
| dev-f020 | related_field | `tu` | `"falllls."` | `"in fals."` | `"s falls."` | `"la hums."` | `"la hums."` |
| dev-f021 | unknown | `?` | `"falllls."` | `"in fals."` | `"s falls."` | `"la hum t"` | `"la hum t"` |
| dev-f022 | exact_copy | `Z!6` | `"llalls. "` | `"r falain"` | `"n ty=s. "` | `"humod ty"` | `"humod ty"` |
| dev-f023 | local | `so` | `"falllls."` | `"in fals."` | `"s falls."` | `"la hums."` | `"la hums."` |

## Decision

**Change the training setup under a new protocol.** Preserve v1's failed gates
and stop this version. The common answer/termination failure, approximately2.3%
answer-target share, continuing loss improvement, and lack of a verified
evaluation defect support testing whether these LMs can learn the basic task
before comparing long-distance memory. The saved results do not establish that
more training will help, or that all custom LMs should be abandoned.

A new registration would need a separate, bounded basic-competence stage with
predeclared checks for local copying, `?`, exact punctuation and EOS, using
segment placements that actually expose the entire assignment/query. It should
specify answer supervision and exposure before any fit, set an independent
stop rule if basic competence fails, and permit a memory comparison only after
that prerequisite passes. Keep history/prose losses separately visible so an
answer-focused objective cannot hide language loss. These are requirements for
a future experiment, not changed gates, a selected new budget, or permission to
run it here. No new protocol or training was executed in this diagnosis.
