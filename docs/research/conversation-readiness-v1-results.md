# Conversational training readiness v1

4 November 2026. **Can Toruk's own model chat usefully yet? No evidence supports
that claim.** The unchanged owned checkpoint scores 0/25 on this diagnostic and
cannot ingest the full recorded refusal history through its current generation
interface. The conversational pilot is **NOT_RUN**, not a failed training run.
CPU compute is feasible; the requested data-exposure gate blocks this checkpoint.

## Starting state and reproduced evidence

Starting HEAD `337cba2c667419c7a3e0a244cecd040b375d7927`, clean working tree.
Exact snapshots and command evidence are in
`artifacts/conversation-readiness-v1-20261104/`. No prior prompt was accepted as
proof: local checkpoint files, runtime identities, training data fingerprints and
saved outputs were checked through fresh model inference.

`replay_owned_readiness.py` loads every saved primary checkpoint and reproduces
all 16 conditions / **768 answers exactly**, including loss, ablations, token
work and per-category correctness. Only time/memory fields are excluded from
equality. Replay takes **14.550 s** inside the process, **17.213 s** including the
recorded wrapper/imports; observed process high water is **296,800,256 bytes**.
No new optimization occurs during this replay.

| Prior condition, both seeds | NLL seed 31 / 47 | Exact /96 | Distant /16 | Corrections /16 | Exact strings /16 |
|---|---:|---:|---:|---:|---:|
| Ordinary / memory disabled | .5318 / .5300 | 14 | 3 | 2 | 0 |
| Memory enabled | .5198 / .5220 | 17 | 4 | 3 | 0 |
| Memory enabled, no read | .5618 / .5595 | 11 | 3 | 3 | 0 |
| Memory enabled, no update | .5635 / .5614 | 12 | 3 | 3 | 0 |
| Parameter-matched ordinary | .4973 / .4998 | 15 | 4 | 1 | 0 |

The diagnostic uses the predeclared seed-31 memory-enabled checkpoint:
**56,064 parameters**, 32 local byte positions, four 32-float memory slots
(512 state tensor bytes), 384-target training-document limit. Its inherited
training consumed **78,190 targets**, 256 optimizer steps, 11.816 s wall /
11.813 s CPU in the recorded original run. This training time is inherited,
not newly measured optimization. The new replay confirms loading and predictions.
Original tokenizer/model/runtime identities remain unchanged; original training
split hashes match the checkpoint. Original document reset, deterministic replay
and exact optimizer-boundary resume tests are rerun in local verification.

## Single prerequisite repaired: conversation data and exposure contract

There was no owned-LM conversation dataset/role contract or cross-stage
conversation-answer exposure gate. `conversation_data.py` now supplies that
offline prerequisite, under `toruk-json-role-lines-v1`:

```text
user:"Remember my label is EXAMPLE."
assistant:"Recorded."
user:"What is my label?"
assistant:
```

The last line is the generation prefix; a completed training record instead ends
with a JSON-string assistant response and newline. A role and JSON string occupy
each line. Content newlines/quotes are escaped, preventing content from creating
new role lines. Roles alternate; malformed/empty messages are rejected. Each
complete conversation is one document; the future trainer must invoke a fresh
document state, using the already-tested owned-model reset contract. No trainable
chat adapter or cross-dataset warm-start implementation is claimed here.

Data sources and permission:

- **64 train / 16 development / 24 synthetic test conversations:** original
  examples generated in this task under the user's explicit instruction to
  create small conversation examples. No external corpus, scraped text, private
  transcript download, or third-party dataset license is involved.
- **One additional test diagnostic:** the full 11-message `full_history_matched`
  history from `artifacts/current-state-audit-20261103/refusal-replay.json`, which
  the user explicitly requested including. It remains test-only, alongside a
  short three-turn refusal-to-math case derived from the repository probe.
  The source path and SHA256 are registered. No broader transcript collection
  or permission beyond this requested diagnostic is assumed.
- **Inherited pretraining data:** the already recorded owned-LM synthetic corpus,
  verified against the checkpoint's actual dataset fingerprint. It is audited,
  not silently relabeled as clean or conversational data.
- **External model:** the existing local, manifest-verified
  `Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf` weights are inference-only reference
  material, not a training-data source. No download or external training is run.

Cases cover exact instruction following, context-grounded short factual answers,
insufficient evidence, explicit correction, distant recall across distractor
turns, punctuation-sensitive strings, arithmetic and refusal carryover. The
factual category tests supplied facts, not broad world knowledge. Split-specific
names/value inventories and uncertainty wording avoid shared complete target
answers. This is small synthetic template-based testing, not independent-source
conversational generalization. Seeds are 7301/8301/9301; canonical message
deduplication, disjoint IDs and exact rendered-document checks are enforced.

| Split | Conversations | Canonical SHA256 |
|---|---:|---|
| Train | 64 | `8cc9056ec56c72e97f6038ff51effd7bf95a0f1ff47468fa80d2e17a97a6a5e7` |
| Development | 16 | `ed7a52fd875e083a3989248fe4df8b4c9877828f861b28d5ac7f7f7040b90c6c` |
| Test, including full diagnostic | 25 | `e2c080ce076391e9df4393bd0787ce4653ddd27a422dfcaaeaa0a1e3ba63ffe0` |

The new conversational training split contains **9,813 byte/EOS targets** and
zero reserved development/test answer matches. New examples do not contain any
held-out conversation or question/answer pair. Evidence may of course occur in a
test prompt: that is what recall is meant to use, not training contamination.

The stricter inherited-corpus check fails: `train-local-28` contains
**`Note 10: sun.`**, while the reserved refusal/math answer is **`10`**.
The audit matches complete answers as case-insensitive standalone text, excluding
substrings inside unrelated longer identifiers. It records the matching row.
This is an **incidental literal overlap, not proof of semantic QA leakage**, and
does not explain the model's poor chat outputs. However, the user's literal
requirement that no chat evaluation answer appear in training is not satisfied.
The report does not silently substitute a weaker question/answer-pair policy.

The pipeline emits a filtered **191-document / 29,083-target** pretraining corpus,
SHA256 `5a7c90b46a463d8be83d28ed976aece8c21150e5feb2e270d7ef5791f8e9643c`.
It removes the matching document without modifying the original files, seals,
weights or dataset labels. **Filtering a file cannot remove exposure from an
already-trained checkpoint.** `require_training_ready` rejects both the original
exposure and attempts to bind its weights to this new dataset fingerprint.
The new data/provenance contract is implemented; a clean starting checkpoint is
still absent. The user-directed not-ready branch stops here before pilot training.

## Resource caps and feasibility

`configs/conversation-readiness-v1.json` was written and registered before the
diagnostic inference. Conversational optimization is disabled: **0 targets,
0 training seconds**. No pilot checkpoint, weights-only transfer, interruption
or pilot resume run is claimed. Existing next-token resume correctly rejects a
changed dataset; a future transfer must explicitly distinguish weights-only
initialization from resuming optimizer/data progress.

| Resource | Registered diagnostic cap | Measured |
|---|---:|---:|
| Device | CPU; no paid job | Windows 11, Torch 2.14.1+cpu |
| CPU threads | Owned 1; preserved external implementation 2 | 1 / 2 |
| Evaluation wall | 180 s; outer command timeout 190 s | 50.706 s process / 55.330 s wrapper |
| Owned RSS | 512 MiB | 289,587,200-byte high water |
| External RSS | 4 GiB | 2,455,289,856-byte high water |
| Registered run disk | 64 MiB | 300,326 bytes after derived reports, before source archival |
| Output cap | 16 native tokens per response | Owned bytes; external BPE, not equal byte budgets |
| Conversational training | Disabled | 0 targets / no pilot |

Hardware reports AMD64 Family 25 Model 80 Stepping 0 (AuthenticAMD), 12 logical
CPUs; Python 3.12.14. CPU-only is the selected runtime, not a claim that no other
physical accelerator exists. Memory values are framework-inclusive process
high-water marks, cumulative within the diagnostic process. Caps are checked at
request boundaries with an outer wall timeout; this is not an OS memory sandbox.
The original owned generation prefix limit remains **512 bytes**, stricter than
the prepared diagnostic's 2,048-byte data cap. The full history is 660 formatted
bytes, so the owned call fails visibly rather than dropping history or invoking
another model. Qwen consumes all 11 turns (269 BPE prompt tokens).

A concrete future CPU pilot proposal is versioned but **not executed**: 128
steps, batch two complete documents, at most 98,304 targets, 60 s wall, 512 MiB
RSS and 16 MiB disk. The reproduced tiny model's throughput makes such an
execution pilot plausible; that does not establish meaningful conversational
learning. The first required step is regenerating the starting checkpoint from
the audited pretraining corpus, with separate declared bounds and lineage.

## Raw before-training comparison

The same 25 frozen message histories are submitted to the unchanged owned
checkpoint and the existing external backbone. Both decode greedily with a
16-native-token cap. Own input uses the new role-line contract; Qwen uses its
native chat template and existing system instructions. These are appropriate
interfaces but different tokenizers, pretraining, parameter counts and thread
counts. This is a capability diagnostic, not matched-compute architectural
evidence or a comparison between trained pilots.

Every prompt, raw output, model identity, metric, error and latency is retained in
`registered/data/test.json` and `registered/diagnostics.json`. The **complete
25-row raw table** is in
[raw-output-table.md](../../artifacts/conversation-readiness-v1-20261104/registered/raw-output-table.md).
Selected examples below are illustrative; all cases contribute to the scores.

| Case | Expected | Owned before: raw | External Qwen: raw | Trained owned pilot |
|---|---|---|---|---|
| instruction-0 | `Evalueinstruction0` | ` sun.\nNote 2: wi` | `Evaluating instruction 0` | NOT_RUN |
| factual-0 | `Evaluefactual0` | ` swer rain.\nNote` | `Evaluefactual0` | NOT_RUN |
| uncertainty-0 | `Unknown.` | ` is red.\nNote 2:` | `Unknown` | NOT_RUN |
| correction-0 | `Evaluecorrection0` | ` swiswer Answer ` | `Eoldcorrection0` | NOT_RUN |
| distant-0 | `Evaluedistant0` | ` r gold.\nNote 5:` | `Evaluatedistant0` | NOT_RUN |
| exact-0 | `E/Q-0_x!` | ` r gold.\nNote 5:` | `E/Q-0_x!` | NOT_RUN |
| math-0 | `10` | ` wer racind.\nNot` | `10` | NOT_RUN |
| short prior-refusal math | `10` | ` r rain.\nNote 5:` | `The sum of five plus five is ten.` | NOT_RUN |
| full recorded refusal/math | `10` | ERROR: 512-byte prefix limit | `The sum of 5 and 5 is 10.` | NOT_RUN |

| Measure | Owned before | External pretrained Qwen | Owned pilot |
|---|---:|---:|---|
| Fixed strict exact | 0/25 | 13/25 | NOT_RUN |
| Post-hoc semantic review | 0/25 | 18/25 | NOT_RUN |
| Instruction exact | 0/3 | 0/3 | NOT_RUN |
| Context factual exact | 0/3 | 3/3 | NOT_RUN |
| Arithmetic exact | 0/3 | 3/3 | NOT_RUN |
| Distant recall exact | 0/3 | 1/3 | NOT_RUN |
| Corrections exact | 0/3 | 1/3 (2 stale) | NOT_RUN |
| Exact strings | 0/3 | 3/3 | NOT_RUN |
| Uncertainty semantic | 0/3 | 3/3 | NOT_RUN |
| Refusal-history math semantic | 0/4 (one interface error) | 4/4 | NOT_RUN |
| False assertions on unknown cases | 3/3 ungrounded `is red` fragments | 0/3 | NOT_RUN |
| Within-response repeated word trigrams | 0 | 0 | NOT_RUN |
| Unique nonempty responses | 9 across 24 outputs | 19 across 25 | NOT_RUN |

The semantic review is explicitly **post-hoc**: `Unknown` expresses uncertainty
despite a punctuation mismatch, and the two full-sentence arithmetic answers are
correct despite violating a number-only format. The initially recorded
`false_assertion_proxy` and `refusal_carryover_error` fields are strict string
proxies, **not semantic judgments**: they flag those good external replies.
`posthoc-semantic-review.json` corrects that interpretation without changing
raw outputs, exact scores, thresholds, weights or the readiness decision.
False-assertion review is limited to the three insufficient-evidence questions;
it is not a global human-rated hallucination estimate. The owned replies are
mostly malformed continuations. Zero within-answer word repetition at this tiny
cap does not establish low repetition: only nine distinct owned outputs recur
across 24 different prompts. All 24 owned generations reach the token cap
without EOS; the remaining case is an interface error.

The external reference recovers arithmetic after refusals in this run; the old
reported carryover behavior is not assumed to persist across model identities or
settings. Two external correction errors and two misspelled distant codes remain
visible. These examples do not establish that either model is generally reliable.

## Token and compute accounting

| Diagnostic work | Owned before | External pretrained |
|---|---:|---:|
| Prompt tokens forwarded | 3,273 byte/special tokens over 24 accepted prompts | 3,256 native BPE prefill tokens over 25 |
| Output tokens | 384 | 140 |
| Actual owned transformer positions, including repeats | 10,425 | Not instrumented at this layer |
| Request wall total | .7767 s | 43.9844 s |
| Request CPU total | .7656 s | 88.2188 s |
| Mean over accepted requests | 32.36 ms | 1,759.38 ms |
| Extra selector/memory model calls | 0 | 0 |

The owned recurrent computation is included in its forward positions and time;
it still has 512 memory tensor bytes. External mode is BASELINE, with no Toruk
selector. Request CPU/wall includes tokenization, prompt fit and generation;
the existing API exposes native prompt/output token metrics but not all repeated
fitting tokenization counters. Those missing counters are not silently claimed
as zero or a complete tokenization-work total. The context-limit failure forwards
no owned tokens. Whole diagnostic time includes loading and artifact work, so it
exceeds summed request times. Prerequisite replay, data preparation and repository
verification have additional, separately retained costs. No dollar, FLOP or energy
savings were measured. Lower cost for a model giving zero correct answers is not
a useful efficiency result.

## Gates and integration

Before diagnosis, the versioned config fixed: at least 80% exact overall, at
least 60% in every category, no unsupported unknown answers, no refusal-carryover
errors, no invalid outputs, at least 95% clean termination, and an eligible
starting lineage plus a trained pilot. New conversation split/format gate:
**PASS**. Inherited literal-exposure gate: **FAIL**. Checkpoint loading and
historical replay: **PASS**. Owned before-training quality/reliability:
**FAIL**, including 0/25 exact and no clean terminations. Pilot gates:
**NOT_EVALUATED**, because no pilot ran. Product integration: **BLOCKED**.

There is no new API/UI mode, no default-backbone replacement and no hidden
fallback. Diagnostic rows distinguish `origin=toruk_owned` and
`origin=external_pretrained`, with checkpoint-derived and Qwen model identities.
Existing API/UI identity and proxy tests are rerun; no trained-pilot API/UI
identity claim is made for an option that does not exist. Existing chat backbone
paths, model code, weights and owned checkpoint formats remain unchanged.

## Commands, verification and files

From repository root, using fresh output directories (the actual run used
`artifacts/conversation-readiness-v1-20261104/`):

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
& $py scripts/replay_owned_readiness.py --reference artifacts/owned-lm-v1-20261104/primary --output artifacts/readiness-fresh/replay
& $py scripts/conversation_readiness.py prepare --output artifacts/readiness-fresh/registered
& $py scripts/conversation_readiness.py evaluate --output artifacts/readiness-fresh/registered --backbone-dir artifacts/qwen-chat-001/backbone
& $py scripts/report_conversation_readiness.py --run artifacts/readiness-fresh/registered
& $py -m pytest -q tests/test_conversation_data.py tests/test_owned_lm.py
& $py -m mypy src/toruk_lm scripts/conversation_readiness.py scripts/replay_owned_readiness.py
& $py scripts/verify.py --output-dir artifacts/readiness-fresh/verification
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
git diff --check
```

Exact executed commands, timestamps, source hashes, exits, times and logs are
retained under `checks/` and `verification/`; see the generated
`artifacts/conversation-readiness-v1-20261104/verification-results.md` index.
Development lint issues were corrected before final verification. No failed
training run was suppressed; there was no conversational training run at all.
Repository verification runs the pre-existing **nonconversational**, bounded
next-token training/resume smoke under its own config; that is not a chat pilot
or a violation of this run's zero conversational-target cap.

New tests cover role/newline injection, deterministic formatting/splits,
cross-split duplicate rejection, answer leakage in any training turn, inherited
incidental overlap, checkpoint/data binding, clean-corpus filtering, size limits
and test-only diagnostic preservation. Existing tests cover real state reset,
deterministic replay and checkpoint resume. A conversational pilot's deterministic
replay/resume is **not tested**, since no pilot checkpoint exists. GitHub Actions
now runs the download-free `conversation_readiness.py validate` data/guard smoke
in addition to the existing owned-LM smoke and Python/Node suites. Hosted CI for
these edits was **not observed**.

Files changed: `src/toruk_lm/conversation_data.py`;
`scripts/conversation_readiness.py`, `replay_owned_readiness.py`,
`report_conversation_readiness.py`, `verify.py`;
`configs/conversation-readiness-v1.json`; `tests/test_conversation_data.py`;
`.github/workflows/ci.yml`, `.gitignore`, `MANIFEST.in`; `README.md`,
`docs/architecture.md`, `docs/experiments.md`, this report, and new readiness
artifacts. An initial development preparation directory is retained separately
from the registered diagnostic; it was not used for scoring or training.

**Highest-priority next step:** regenerate and seal a starting owned checkpoint
from the filtered 191-document pretraining corpus, with its true new dataset
identity. Only then define weights-only conversational initialization and safe
resume on the new dataset before a separately bounded pilot. Reusing old weights
while changing their data fingerprint would not repair the requested guarantee.
Because these diagnostic test outputs have now been inspected, any later
confirmatory quality claim also needs a fresh held-out set.
