# Owned conversation framing pilot — 5 November 2026

**Framing improves; useful conversation does not. Integration FAIL.** One fixed
data-only experiment improves valid owned response framing from 0/24 to 20/24
and EOS termination from 1/24 to 21/24 against the historical checkpoint. It
remains 0/24 on answers, including every instruction/factual/recall category.
No new chat option, default change, deployment, commit or push is made.

## Starting evidence and diagnosis

Starting HEAD `265f88137f41b5a646ec56c232b4bd1b49dadd38`. The tree was dirty:
CI, `.gitignore`, check runner, inference server, server/check tests, Node proxy,
browser state and Node tests were modified; a repository-review artifact directory
and `tests/test_web_integration.py` were untracked. They are preserved, not
attributed to this pilot. Exact status/diff snapshots are in
`artifacts/conversation-format-v1-20261105/starting-status.txt` and
`starting-diff.patch`.

The latest conversational report records **NOT_RUN**, not completed training.
Before implementation, fresh checkpoint inference reproduced **768/768 answers
across 16 owned conditions**, and fresh readiness inference reproduced **50/50
owned/external answers, identities and scores**. The latter includes the 25
frozen histories per model and the full recorded refusal conversation. Historical
replay wrapper time: 22.235 s; readiness inference wrapper: 67.333 s. The new
readiness data audit again found inherited `Note 10: sun.` overlapping reserved
answer `10`. The old checkpoint is never used to initialize either new fit.

The selected weakness is assistant-response completion. The old checkpoint
produces malformed synthetic-note continuations on 24 accepted prompts, all
reaching the original 16-token cap; one full-history request fails the 512-byte
interface limit. Category exact counts are instruction 0/3, contextual factual
0/3, corrections 0/3, distant 0/3, exact strings 0/3, arithmetic 0/3, uncertainty
0/3, refusal/math 0/4. There are nine unique outputs across 24 responses, despite
zero within-response repeated word trigrams. Three unknown replies include
ungrounded `is red` fragments. Raw examples and category totals are retained in
`reproduced/raw-output-table.md` and `reproduced/aggregates.json`.

Attribution: note-to-role formatting is a training-distribution mismatch; the
untrained conversational behavior also fails instruction following. The long
history error is an inference-interface limit. These failures cannot establish
that the recurrent state itself caused failed factual recall. The short cap and
raw-versus-JSON-content scoring are diagnostic limitations. The experiment
changes only training data, holds architecture/optimizer fixed, and fixes the
new cap/scorer before fitting to make that narrow hypothesis testable.

## Frozen experiment and provenance

The [protocol](conversation-format-v1-protocol.md) was recorded before experiment
implementation or fitting; `registration.json` binds its hash, runner, data and
runtime hashes. One candidate, one control, one seed (31), no sweep or held-out
retries. Both start from random weights in the existing memory-on architecture:
56,064 parameters, local context 32, four width-32 memory slots (512 tensor bytes).
Candidate uses the existing 64 synthetic conversations; control uses 190 clean
synthetic-note documents (the prior 191-document filtered corpus loses one more
document containing reserved `18`). Neither uses new external training data.
Original synthetic-data provenance is copied into registration, including source
manifest hash. No third-party license is added and no project license is inferred.

Development is the existing 16 conversations, reported without model selection.
Primary is 24 sealed unseen-value renamings of the existing templates, not
independently authored templates. Regression is the published 25 histories;
these are acknowledged as previously exposed diagnostic cases. Canonical split
and complete-answer overlap audits pass before fitting; neither new fit inherits
exposed weights. The old checkpoint remains an explicitly exposed historical
baseline. Both new fits use 512 AdamW steps, batch two, LR .003, float32 CPU, one
thread. Candidate saves at 256 and resumes to 512 with the existing strict
dataset/config/optimizer/RNG contract. No runtime/checkpoint contract is relaxed.

Final weights are frozen before evaluation, which is guarded against duplicate
attempts. There are 374 raw evaluated responses: 80 owned development, 120 owned
primary, 125 owned regression, and 49 external reference. Qwen uses pinned local
weights and native chat formatting, two threads, BASELINE/no selector. All
conditions greedily decode at a fixed 32-native-token cap, owned UTF-8 bytes versus
external BPE. This unequal pretraining/size/tokenizer comparison is a capability
reference, not matched-compute architectural evidence. The original 16-token
diagnostic reproduction remains separate.

## Measured comparison

Primary held-out, all conditions on the same 24 histories:

| Condition | Content exact | Valid owned framing | EOS | Unknown unsupported proxy | Request wall s | Prompt / output tokens |
|---|---:|---:|---:|---:|---:|---:|
| Previous owned checkpoint | 0/24 | 0/24 | 1/24 | 3/3 | 1.2674 | 3300 / 755 |
| New note-data control | 0/24 | 0/24 | 0/24 | 3/3 | 1.3177 | 3300 / 768 |
| New conversation candidate | 0/24 | 20/24 | 21/24 | 3/3 | .7893 | 3300 / 417 |
| Candidate without memory reads | 0/24 | 19/24 | 19/24 | 3/3 | .5629 | 3300 / 428 |
| Candidate without memory updates | 0/24 | 16/24 | 16/24 | 3/3 | .8001 | 3300 / 470 |
| External pretrained Qwen | 20/24 | Native content | Unavailable | 0/3 | 34.9088 | 2990 / 128 |

All owned conditions score 0/3 in each primary category. Qwen scores 3/3 on
instruction following, contextual facts, distant recall, exact strings, arithmetic
and uncertainty; 0/3 corrections (all stale); 2/3 strict refusal/math. The third
refusal answer is semantically correct prose: `The sum of 9 plus 9 is 18.`
Post-hoc semantic review therefore gives Qwen 21/24, distinct from frozen exact
20/24. No semantic adjustment changes the experiment gates.

Selected raw candidate continuations (quotes/newlines are actual role transport):

| Category | Expected | Candidate raw | Interpretation |
|---|---|---|---|
| Instruction | `Hvalueinstruction0` | `"Tvalueinstruction6"\n` | Memorized training value |
| Contextual fact | `Hvaluefactual0` | `"Tvaluefactual3"\n` | Unsupported wrong label |
| Correction | `Hvaluecorrection0` | `"Tvaluecorrection3"\n` | Wrong label, not stale source value |
| Distant | `Hvaluedistant0` | `"Tvaluedistant2"\n` | Training-value substitution |
| Exact string | `H/Q-0_x!` | `"T/Q-6_x!"\n` | Copy failure |
| Arithmetic | `18` | `"4"\n` | Memorized training answer |
| Unknown | `Unavailable.` | `"ep:"oprsoty pd"Tpersontionly d ` | Malformed, not a clear factual assertion |

The three candidate unknown replies are malformed fragments: **3/3 unsupported
proxy failures; semantic false-assertion count is indeterminate**, not three
human-rated factual hallucinations. Qwen makes zero false assertions on these
unknown questions. On regression Qwen's three `Unknown` replies also make zero
false assertions despite three punctuation-sensitive proxy failures. This
distinction prevents the strict proxy being misreported as semantic fact scoring.
Candidate's three primary fact-label answers are incorrect, interpretable label
assertions; this is not a global hallucination estimate. Complete raw outputs,
IDs, errors, CPU and token counters are in `outputs-*.json`; full markdown tables
are in `raw-primary.md`, `raw-regression.md` and `raw-development.md`.

Regression: historical/control/candidate content exact all **0/25**, candidate
framing **20/25**, EOS **21/25**, versus historical 0/25 for both. All owned
conditions reject the full 660-byte refusal history visibly. The candidate's
short refusal/math continuation is `"Tpistant:"4"\n`; no general recovery from
refusal is established. Qwen answers the full recorded history
`The sum of 5 and 5 is 10.`, and is 13/25 strict, 18/25 under the separately
labeled prior semantic equivalences. Its correction and distant scores are
1/3 each. This is not evidence of a persistent external refusal-carryover bug.

Repetition: candidate has 12 unique primary responses versus historical/control
11; regression has nine versus historical nine/control twelve. All have zero
repeated word trigrams except no-read, with one primary repeat. Zero trigram
repetition at this cap is not general language quality. No condition generates
invalid UTF-8. Development candidate framing/EOS is 14/16, content 0/16.
The reduction from twelve control responses to nine candidate responses on
regression is greater cross-prompt collapse, despite passing the narrower
predeclared within-response trigram gate. Candidate training also takes 8.7%
more wall time than the newly trained control. Neither regression is hidden by
the positive framing result.

## Resources, gates and limitations

Candidate training: **157,008 targets, 25.361 s wall / 25.281 s CPU**, observed
actual-process high water **303,816,704 bytes**. Control: **155,783 targets,
23.329 s wall / 23.250 s CPU**, **301,391,872 bytes**. Total optimized targets
**312,791**, training wall **48.689 s**; outer training orchestration **58.979 s**.
All three checkpoint files together are **2,212,769 bytes**. No paid training,
GPU or API is used. Local runtime is the cost proxy; energy, FLOPs and dollar
savings are unmeasured. Old checkpoint training is inherited, not charged as new
optimization. Repository checks run additional small smoke training separately.

Frozen evaluation takes **95.566 s** inside the process / **98.577 s** wrapper.
Primary owned actual forwarded positions: historical 15,671; control 15,972;
candidate 10,492; no-read 10,708; no-update 11,221. State reads/updates and repeated
local forwarding are included. Qwen's internal position work and EOS termination
are unavailable through this interface, not zero. Native prompt/output metrics
are retained. Latency includes prompt processing, generation and identity hashing;
not every fitting/tokenization counter is instrumented. Process peaks are
cumulative within evaluation, not isolated per-condition incremental allocations;
external peak is 2,446,229,504 bytes. Different output lengths contribute to
latency differences; zero correct owned answers precludes a useful efficiency claim.

Caps were respected by observed training targets/time/OS high-water measurements.
**Enforcement deviation:** parent-only RSS sampling in the subprocess supervisor
can miss the Windows venv launcher's real child. Actual-process OS peak readings
are retained in training JSON and are below 512 MiB, but the experiment did not
enforce RSS at every optimizer boundary as the protocol intended. Deadline checks
do occur each optimizer boundary; request resource checks and outer timeouts are
active. These are not OS memory hard limits. This issue is disclosed rather than
changing sealed sources or rerunning held-out evaluation.

Predeclared framing/regression gate: **PASS against both controls**, primary and
published regression. Absolute valid-framing gains are 83.3 and 80 percentage
points; primary EOS gain is 83.3 points over historical and 87.5 over control.
Content exact does not regress from its zero floor; unknown/UTF-8/trigram limits
pass. This is a narrow formatting result, not factual learning.

**Chat integration FAIL** on both suites: 0% accuracy, failed per-category gates,
unsupported unknown fragments, <95% EOS and the full-history input error. No
candidate is exposed in API/UI. Existing working chat continues to identify its
pretrained backbone and any selector; experimental files identify the owned model
by checkpoint SHA. Read/update ablations show an effect on syntax completion,
not useful factual memory. Single seed, shared templates and tiny synthetic data
limit generalization; no repeated tuning or general-purpose chatbot claim follows.

The post-evaluation release audit explicitly checks zero refusal errors in
addition to the sealed runner's quality/framing checks. The runner had only
enforced the weaker per-category accuracy threshold for that item. This reporting
correction leaves both FAIL decisions unchanged; evaluated sources and raw
answers remain sealed. A regression test rejects a single refusal error even
when other quality checks pass.

## Reproduction and verification

Exact executed argument arrays, source hashes, timestamps, exits and logs are in
`artifacts/conversation-format-v1-20261105/checks/*.json`; the bounded trainer
subcommands are in `training-processes.json`. Use a fresh run directory for each
reproduction (register/train/evaluate all require the same `--run`):

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
& $py scripts/replay_owned_readiness.py --reference artifacts/owned-lm-v1-20261104/primary --output artifacts/framing-fresh/historical-replay
& $py scripts/conversation_readiness.py prepare --output artifacts/framing-fresh/reproduced
& $py scripts/conversation_readiness.py evaluate --output artifacts/framing-fresh/reproduced --backbone-dir artifacts/qwen-chat-001/backbone
& $py scripts/conversation_format_study.py register --run artifacts/framing-fresh
& $py scripts/conversation_format_study.py train --run artifacts/framing-fresh
& $py scripts/conversation_format_study.py evaluate --run artifacts/framing-fresh
& $py scripts/report_conversation_format.py --run artifacts/framing-fresh
& $py scripts/verify.py --output-dir artifacts/framing-fresh/verification
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
git diff --check
```

Verification results are indexed in the evidence package's
`verification-results.md`. The full local verify includes CLI help/diagnose,
frozen sources, Python tests, lint, formatting, native/Linux type checks, build,
data validation and bounded train/resume/reproduction smoke. Focused chat/model
integration: 43 passed; final server/integration/release-audit check: 20 passed.
The final full Python suite passes **232 tests**. Node: 18 passed, one standalone live test skipped;
Python's real Node/Python integration exercises that path. One initial Node
wrapper print failed on Windows cp1252 after successful test execution; rerunning
with explicit UTF-8 passed. No failed training/evaluation attempt was discarded.
GitHub Actions coverage was inspected locally: Python/Node suites, frozen sources,
data/owned smoke and package checks are present. This new full pilot requires
local weights and is not added to hosted CI. **No hosted CI run was observed.**

Files added: study/report scripts, framing scorer/release-audit tests, frozen protocol/results,
and evidence package. Updated: README, architecture, experiment index and the
source-distribution documentation manifest. The owned model runtime, trainer,
data generator, checkpoint formats and chat defaults are untouched.
One minimal inference-server lint cleanup replaces redundant explicit UTF-8
encoding on the expected authorization bytes with the equivalent default; it
preserves the pre-existing Unicode-safe authorization change and is rechecked.

The first full verification attempt retained three failures: the inherited
server lint issue, an extra documentation EOF blank line, and the historical
controlled-pilot test. The last failed because the server cleanup changed the
package fingerprint while that test was running: its saved metrics contain
both old and new source hashes. Its isolated rerun passes. A second full verify
runs against stable implementation sources; the original failures are retained
under `verification/`, with the final run under `verification-final/`.

**One next milestone:** a fresh development-only copy-generalization experiment
with varied synthetic value strings and assistant-target loss, holding this
architecture fixed, to test whether the decoder can use supplied values instead
of memorizing the training-value inventory. Seal new held-out data only after
that development gate; do not tune against this pilot's answers.
