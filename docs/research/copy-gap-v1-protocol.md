# Copy-gap v1: one query-read-gate experiment

7 November 2026. Written before development or heldout inference. Prior verdict:
**CLAIM NOT SUPPORTED**, starting HEAD `1976ea8aa3ceb66137033bee38d5191525bec4d7`,
with the previous closure changes dirty and preserved. This protocol extends the
closure's recommended fixed-checkpoint matched-content distance diagnostic with
exactly one intervention, as requested by the negative-verdict decision gate.

## Hypothesis and intervention

The closure's leading uncertainty is whether poor copying is already present
locally or is mainly caused by distance. Local accuracy was poor and exact copying
failed, so distance alone is an insufficient explanation. A testable mechanism
hypothesis is that learned memory reads interfere with rendering a value at the
query. Disable memory reads in the query/answer phase; retain history processing,
writer operations, checkpoints and greedy decoding. Do not fit any new weights.

`query_read_off` uses the **same** memory-on checkpoint and the existing
`OwnedSession.read` switch. History is consumed normally. At the explicit query
boundary, switch `read` to false and consume the question and generated answer.
Writer operations remain enabled. History-state hashes and history-reader counts
must exactly match unchanged memory-on. Query/answer reader calls must be zero.
Because the runtime recomputes its current local segment, this gates reads for
the entire query-containing segment, including its preceding partial history.
It is a phase/segment intervention, not a tokenwise attention mask. Any later
state change is a consequence of this single read intervention.

All methods use the same two-phase history/query API, which adds a partial-segment
history forward pass relative to the old monolithic API. Tests require unchanged
memory-on generated IDs to match the legacy API. This extra pass is included in
all new work and timing measurements, not hidden as free preprocessing.

## Frozen models, baselines and limits

Use the completed owned-LM primary checkpoints at fitted seeds **31 and 47**:
unchanged memory-on, query-read-off, ordinary, and near parameter-matched ordinary.
Query-read-off shares memory-on weights; ordinary controls retain their own
matched-token fits. Model/tokenizer/checkpoint identities and source files are
sealed at registration after the existing primary reproduction validator passes.
The earlier negative gate must still fail. No external pretrained backbone,
selector, answer parser, lookup table, fallback model or chat-default change.

Float32 CPU, one Torch thread, greedy decoding, PAD/BOS suppressed, EOS stopping,
16 generated tokens. Model context remains 32. Total prefix is **351 ASCII bytes**,
352 tokens including BOS; prefix plus generation stays <=384 positions. Local
evidence gap is 0; distant gaps are **32/64/128/256 bytes** from the end of the
evidence record to the start of the fixed query. Byte and token gaps coincide
for this ASCII fixture. The instruction, evidence, question, filler bytes and
total length are constant within a world; only the record's position changes.
Filler may be truncated at a byte boundary, an artificial-format limitation.

These are controlled gap placements, not natural conversations or capacity
extrapolation beyond the model's bounded document setting. The causal intervention
is record position, not growing total input length. Values close to the query
can fit in the recent local window; distant values cannot.

## Development and heldout

Versioned config: `configs/copy-gap-probe-v1.json`. Data is authored synthetic text
using the old tag/question/filler vocabulary. Kinds: known colour value, six-byte
punctuation-sensitive exact string, and absent-evidence unknown control (`?`).
Unknown controls contain an irrelevant visit record and no tag fact. No case has
a correction; no correction or natural-language gist claim is tested.

- Development generator seed **8151**, four worlds per kind: 12 worlds, 60
  placements, 480 generated answers across four methods and two fitted seeds.
- Heldout generator seed **9151**, twelve worlds per kind: 36 worlds, 180
  placements, 1,440 generated answers.
- Both datasets are generated and hashed at registration. Exact-string values
  must be disjoint across development and heldout. Colour inventory, entity names
  and grammar are shared. Novel exact strings are not promised to occur in the
  original training inventory: this is zero-shot copying, not IID training recall.
- Development verifies execution, pairing and bounds only. No thresholds, prompts,
  mechanism, weights or decoding may change in response to development quality.
  Run heldout once even if development quality is poor. A started phase cannot
  be retried to improve answers; interrupted raw evidence remains visible.

Generation receives only history and query. Expected answers enter scoring after
generation. Each case starts fresh state. All gaps of a world are paired and
share an expected value; they must not be treated as independent worlds.

## Primary metric and all-required numerical decision

Primary: local (gap=0) exact-string accuracy of query-read-off minus unchanged
memory-on, **at each fitted seed separately**. All criteria below must pass:

1. Local exact-string gain >=10 percentage points and absolute accuracy >=50%.
2. Distant colour and distant exact-string accuracy each decline by <=5 points
   versus unchanged memory-on, pooling the four distant placements within kind.
3. Local colour accuracy declines by <=5 points.
4. Unknown-control false assertions do not increase (nonempty answer other than `?`).
5. Total generation forward positions are <=105% of unchanged memory-on.

Require both fitted seeds to pass every condition. All ordinary baseline results
are reported even if their quality is better. Passing would support this narrow
interference intervention, not general memory superiority or total-efficiency
benefit. Empty/incorrect known answers, first-token correctness and per-gap scores
are diagnostic; no substring credit or posthoc primary-metric replacement.

## Full work, measurement and resource cap

Retain every prompt component, gold, generated ID/text, exact score, unknown false
assertion proxy, prefix/output token count, forward positions, reader calls,
writer-linear calls, committed updates, state bytes and wall/CPU times. Hooks time
the attention-reader and writer-linear modules only; norms, nonlinearities and
hook overhead are not falsely labelled complete memory overhead. Full generation
latency includes all operations. Selector work is zero. Counters are not FLOPs.

Each method/seed/phase uses a fresh sequential subprocess and records model-load
time and process peak/RSS, including imports and model loading. Peak measurement
availability is explicit; CPU power/energy are not measured. Method order rotates
by seed. Timing is one run on one host; no statistically reliable speed claim.

Cap each complete phase at **180 seconds**, including all eight subprocesses;
parent deadline terminates an over-budget worker and records failure. Maximum
experimental inference: 360 seconds, 1,920 answers. No training in this experiment.
For a fresh checkout only, recreate the original parent via its separate bounded
600-second primary config and 630-second wrapper. That is prerequisite restoration,
not a second research hypothesis. Original parent validation must then pass.

If the intervention fails, preserve its negative result and diagnose the observed
local/distant pattern. Do not attempt another mechanism or tune this heldout set.
