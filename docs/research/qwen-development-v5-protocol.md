# Qwen development v5: registered instruction study

10 November 2026. Development only, starting at `0705a3d` in `D:/Toruk`.
Register this protocol, config, runner, tests, exact source snapshot, dependency
versions, input/model hashes and tokenizer-only prompt IDs before any generation.
An exclusive registration and start receipt prevent overwrite or rerunning.

The v3 results and v4 audit show evidence retained in both remaining failures:
an entity identifier substituted for a requested value, and an unrelated field
substituted for missing information. These motivate general evidence-grounding
and abstention instructions, without inserting case IDs, expected values,
domain-specific fields, examples or output repair. This is adaptive development
on all seven previously observed questions; no independent evidence is created.

## Fixed design

Three instruction conditions are fixed in `configs/qwen-development-v5.json`:
original control, requested-attribute grounding (`field`), and a silent evidence
check appended to the original (`check`). Apply each identically to both gated
v3 Toruk and unchanged lexical-v1. Each fresh, sequential worker evaluates all
seven original development cases, in original order, then replays the first
case for determinism (charged, excluded from accuracy). Six workers, 48 total
generations, 42 scored. Alternate selector order by condition as registered;
there is no randomized or repeated timing experiment.

Only the system instruction changes. Preserve reference/question/answer bytes,
native template, chronological original source text, selectors/checkpoint,
512-token whole-turn fit, Qwen revision and weights, CPU float32/two threads,
seed 81751, deterministic algorithms, greedy single-beam decoding with cache,
64 output tokens, and original scorer/answer stripping. Tokenizer-only preflight
registers full-prompt IDs for every condition. Metadata/labels are used only by
scoring and audit; selectors receive role/content turns and the model receives
only the envelope. Frozen v1-v4 files are hashed as opaque bytes, including
inherited held-out files; never parse or evaluate held-out cases. Runtime assets
may be read from the original local checkout only after matching registered
hashes, without modifying that checkout. No network or new training is needed.

Use the existing v2 process-tree monitor without changing its code. Identical
caps per worker: 180 wall/360 CPU seconds including cold setup, 30 seconds per
request, 6 GiB private memory, 3 GiB disk including shared model inputs. Six-stage
total: 1080 wall/2160 CPU seconds. Sample every 50 ms with one-second heartbeats,
five-second monitor-gap and two-second suspected-sleep bounds. Prevent idle
sleep for the run and restore afterwards. No inference retries; stop at a
technical failure, retain partial results and all costs. No post-answer candidate
revision, new candidate, resource increase or favorable rerun.

## Measures and decision

Retain raw answers, prompt/output IDs and token counts, proposed/fitted original
source indices/text, scores and failure labels, evidence retention, exact-copy,
preservation, abstention and unsupported/stale proxies. Record per-request
selection, fitting, generation and request CPU/wall time, work counters, cold
stage/process-tree CPU/wall, sampled/OS memory peaks, disk and monitor failures.
Report seven-case and replay-inclusive costs separately, plus shared preparation
and engineering verification costs; inherited profile/training costs remain
14.578125 CPU / 17.6733196 wall seconds, unknown training peak RAM. No dollars,
energy or FLOPs estimate without measurements. Raw timing has host/order/cache
effects; more prompt/output tokens are real costs, not a matched token count.

Technical validity requires all 48 requests, exact deterministic replays, frozen
hash preservation, unchanged source selections (no fit eviction), native prompt
and output reconstruction, unchanged frozen scores, and caps passing. Fresh
original controls must match v3 selected sources/prompt IDs/answers/output IDs.
Report any mismatch and do not relabel historical data as a fresh measurement.

For each candidate separately, development support requires technical validity,
Toruk accuracy above its fresh original control, no newly wrong case in either
selector relative to that selector's control, no Toruk case loss versus matched
lexical, all six answer-bearing source sets retained, and exact-copy and
preservation correct for both selectors. Report every condition, including
failures. Do not select on the two motivating questions alone. Even a pass is
only development support on seven adapted cases: no held-out/generalization,
learned superiority or stable efficiency claim. This study makes no production
behavior change; any later proposal needs separate review.

## Verification and reporting

Add focused contracts for symmetric instructions, general prompts, frozen
scoring, development membership, registration drift/reuse rejection, full-set
decision gates and raw-answer/token integrity. Run relevant tests,
`scripts/verify.py`, the v4 portable evidence verifier (its README explicitly
avoids the broader verifier that rescores historical held-out records), and
`git diff --check`. Add a v5 report with results, failures, costs, limitations,
evidence paths, files changed and final Git state. Leave all changes uncommitted.
