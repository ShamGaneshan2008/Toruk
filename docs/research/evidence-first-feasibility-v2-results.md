# Synthesis audit and separate disposable feasibility-v2 results

11 November 2026. Research-only and uncommitted. Only the small disposable
feasibility-v2 check was registered and run. The 48-case study remains
unregistered and unrun; no benchmark cases or held-out inputs were created or
inspected. Production chat, original LM controls, the answer policy, v1-v5
evidence and rehearsal-001 remain unchanged.

## Four frozen synthesis rejections

The saved request asks for an ordered combination of two source-linked values:

- CinderLoom's north reading: `17 23 31 47 59 61 73 89`.
- TidalForge's south reading: `19 29 37 43 53 67 79 97`.

Every rejected output was exactly `19 29 37 43 53 67 79 97`. Native decoding
agrees with the saved bytes. Both source spans were present, with complete
parsed scope coverage and valid provenance. The first premise is missing from
the generated answer; a different separator, whitespace handling, offsets or
EOS decoding did not cause the rejection.

| Frozen output | Observed behavior | Cause of rejection | Implementation defect demonstrated |
|---|---|---|---|
| Toruk proposed, pass 1 | Returns the south reading only | Required north premise omitted | No |
| Lexical proposed, pass 1 | Returns the south reading only | Required north premise omitted | No |
| Toruk proposed, pass 2 | Returns the south reading only | Required north premise omitted | No |
| Lexical proposed, pass 2 | Returns the south reading only | Required north premise omitted | No |

The returned value is a supported individual fact, but it is insufficient for
the two-premise request. The frozen contract requires both exact values in
order, joined by one of its four declared separators. The implementation
correctly applies that contract and returns `UNKNOWN`. No policy fix or prompt
change was justified. The
[per-output audit](../../artifacts/evidence-first-prototype/feasibility-v2/rehearsal-001-synthesis-audit.json)
retains the spans, values, decoded bytes, missing premise indices and cause.

New [disposable source-linked tests](../../tests/test_evidence_first_feasibility_v2.py)
use OpalRelay's flux and JadeRotor's offset with different values and units.
They accept all four valid two-premise forms, preserve both original UTF-8
slices and reject an added safety claim, changed value, reversed order or either
single-premise answer. These test the unchanged general validator. They do not
add special handling for the four saved answers.

## Separate registration and workload

The [protocol](evidence-first-feasibility-v2-protocol.md) and
[registration](../../artifacts/evidence-first-prototype/feasibility-v2/registration.json)
were frozen before inference. Two new disposable 32/48-turn inputs were crossed
with Toruk and lexical over two reversed-order passes, plus a first-case replay
per selector/pass: **2 x 2 x 2 + 4 = 12 requests**, in four sequential cold
workers with three requests each. No gold answers, scorer or oracle routes.

Both selectors use the identical unchanged policy and original research
selection/fitting/prompt code. There is no full-history verification lookup.
Fitted inputs were **475 or 485 tokens**, with both explicitly scoped premises
retained. The new diagnostic decoder sets
`min_new_tokens = max_new_tokens = 64`, suppressing early EOS while selecting
tokens greedily. It does not force particular answer tokens. All 12 calls
executed exactly **64 generated IDs and 64 backbone forwards**, with prefill
plus 63 cached positions. CPU float32, two Torch threads and seed 81751 remain
pinned; each worker loaded the backbone cold.

This termination setting belongs only to the new resource diagnostic. It
changes neither production decoding nor the old LM controls and supplies no
quality or efficiency comparison. All 12 forced continuations failed the
unchanged bounded synthesis contract and were returned as `UNKNOWN`. The new
source-linked unit tests establish acceptance of valid bounded combinations;
the forced-length run does not establish natural LM synthesis quality.

Independent hard ceilings were registered at 60 wall/120 CPU seconds per
request, 240/480 per worker and 960/1920 across four workers, with 6 GiB private
memory and 3 GiB logical disk. The old 14 wall/27 CPU proposal was frozen as
an assessment threshold, rather than a safety ceiling for this new check.
No ceiling or contribution gate changed after outputs were observed.

## Measured costs and request-cap assessment

The [summary](../../artifacts/evidence-first-prototype/feasibility-v2/summary.json)
records **12 requests / 12 LM calls**, **5,760 executed input tokens** and
**768 output tokens**, including four replays. There were no retries, unknown
token counts, safety failures, provenance failures or replay/native-decode
disagreements. All 12 requests exercised the 64-step workload.

Maximum request wall time was **12.7341427 seconds**; maximum request CPU was
**25.1875 seconds**. **Zero requests exceeded the earlier 14/27 proposal.**
Those observations assess the cap on this finite stress workload; they do not
guarantee every future 64-token request will fit it.

| Nonoverlapping cost scope | Wall seconds | Process-tree CPU seconds |
|---|---:|---:|
| Toruk, pass 1, three requests | 46.409 | 96.844 |
| Lexical, pass 1, three requests | 43.895 | 91.625 |
| Lexical, pass 2, three requests | 43.516 | 92.281 |
| Toruk, pass 2, three requests | 41.177 | 86.516 |
| Four cold workers | **174.997** | **367.266** |
| Disjoint registration/preparation/controller/audit | **8.116** | **7.031** |
| Instrumented v2 total | **183.113** | **374.297** |

Registration/preparation alone cost **4.433 wall / 3.891 CPU seconds**, with no
generations. Worker setup cost 33.785 wall/50.578 CPU seconds; whole requests
cost 136.175/273.000, including LM generation at 135.480/270.750. Selection
cost 0.572/1.859; prompt tokenization cost 0.104/0.375. Parsing/routing/support
validation recorded 0.007711 wall seconds and zero quantized CPU; manifest
construction recorded 0.002996 wall seconds and zero quantized CPU. Zero
recorded phase CPU is below measurement resolution, not zero work. These
components overlap and must not be added to the cold/shared totals again.
Payload tokenization, monitoring, serialization, launch and teardown work are
retained in component or lifecycle receipts.

CPU scope is the instrumented controller and worker process tree. The outer
registration and execution command receipts record 4.926 and 179.208 wall
seconds, **184.134 combined**, including external launch/receipt overhead.
These intervals overlap the instrumented v2 total and are not another additive
cost. Final summary/seal writing is outside the instrumented timing boundary
and within those outer command intervals.

Peak combined private memory was **4,119,744,512 bytes (3.837 GiB)**. The sampled
new-run runtime/source/input/output disk footprint peaked at **1,001,300,376
bytes**. A final complete inventory also includes the old protected files read
for integrity auditing: **1,002,141,083 bytes**, below the 3 GiB ceiling. The
largest observed monitor gap was **0.088 seconds**. Per-request sampled memory,
end readings and stage peak bounds are retained with each worker's cost file.

Across rehearsal-001 and v2, disjoint instrumented cost is **52 requests / 36 LM
calls**, **11,440 input / 1,012 output tokens**, **334.714 wall / 661.219 CPU
seconds**. The separate final preservation check cost 0.024850 wall/0.031250
CPU seconds (0.189 seconds for its outer command); other engineering-test
receipts remain separate from experimental costs.

## Proposed fixed caps from the registered formula

Pool maxima across rehearsal-001 and v2. The maximum non-request cold-worker
residuals are **10.7059738 wall / 25.296875 CPU seconds**. Use twice the maxima,
rounded up, and retain the larger shared allowance after scaling v2's two-case
shared cost to 48. This formula was fixed before inference.

| Future resource proposal only | Calculation | Seconds |
|---|---|---:|
| Request wall | ceil(2 x 12.7341427) | **26** |
| Request CPU | ceil(2 x 25.1875) | **51** |
| Cell/pass wall, 49 requests | ceil(2 x 10.7059738) + 49 x 26 | **1296** |
| Cell/pass CPU, 49 requests | ceil(2 x 25.296875) + 49 x 51 | **2550** |
| Shared wall allowance | max(127, ceil(48 x 8.1160078787)) | **390** |
| Shared CPU allowance | max(94, ceil(48 x 7.03125)) | **338** |
| Overall wall | 8 x 1296 + 390 | **10758** |
| Overall CPU | 8 x 2550 + 338 | **20738** |

Keep **6 GiB private memory / 3 GiB disk including inputs**. These are resource
proposals for future review, not permission to register the 48-case study.
The older proposal was not exceeded in v2; the larger new proposal follows the
predeclared pooled-maxima/headroom formula. No quality gates were evaluated or
relaxed, and no future benchmark requests were executed.

## Tests, preservation and status

- **67 focused tests passed**, including 16 new source-linked synthesis,
  decoder-length, registration-boundary and cap-arithmetic tests. Ruff lint and
  formatting checks passed for the new code before registration.
- An offline preservation check verified **103 protected file hashes**,
  including rehearsal-001, its bound policy/harness/tests and both prior
  research reports. No old frozen byte changed. It also verified **31 sealed
  v2 outputs**, without generating answers. See the
  [preservation receipt](../../artifacts/evidence-first-prototype/verification-v2/preservation-audit.json).
- Registration, execution and test commands/logs are in
  [verification-v2](../../artifacts/evidence-first-prototype/verification-v2/).
  Each v2 request retains prompts/native IDs, fitted source bytes and manifests,
  source-linked policy decisions, forward-work counts and full resource costs.

This turn adds only the v2 protocol, results report, stress harness, new tests
and separate v2/verification artifacts. Earlier untracked prototype files remain
uncommitted and unchanged. No tracked file changed; no commit or push occurred.
