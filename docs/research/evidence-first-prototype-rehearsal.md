# Evidence-first bounded prototype and disposable runtime rehearsal

11 November 2026. Research-only, uncommitted prototype. This is not the
registered 48-case study and provides no accuracy, selector or savings claim.
The [decision and its fixed gates](evidence-first-answer-path-decision.md)
remain unregistered. Production chat, existing selectors, LM controls and
v1-v5 evidence were not edited.

## Implementation and boundary

- [Policy](../../scripts/evidence_first_policy.py): immutable source/coverage
  manifests, UTF-8 intervals, literal requested-field binding, correction links,
  four support states, direct copying and a bounded synthesis validator.
- [Research adapter and harness](../../scripts/evidence_first_rehearsal.py):
  the same policy for Toruk and lexical after their unchanged selection/fit;
  original research LM prompts and control output handling remain intact.
- [Policy tests](../../tests/test_evidence_first_policy.py) and
  [integration/resource tests](../../tests/test_evidence_first_rehearsal.py)
  use synthetic fixtures and fake decoder outputs, not Qwen generations.

Coverage was defined and tested first: absence needs complete raw-byte coverage
and supported parsing of every declared in-scope interval. Omitted or unparsed
bytes force `coverage-incomplete`, including when another retained line contains
a plausible answer. Explicit scope comes from the question, never from which
turns happen to survive. Missing correction antecedents are incomplete;
conflicting, negative-only or unresolved bindings abstain. Source roles,
chronology, revision hashes and byte offsets accompany copied values. Parsing
and copying receive only fitted bytes and metadata, with no history callback.

The declared grammar is deliberately narrow; arbitrary prose, unsupported
constraints, multiline/embedded-quote literals and general reference resolution
remain outside it. Positive answers also conservatively require complete parsed
scope coverage. Synthesis supports only an ordered combination of two literal
premises; all additional generated claims or changed values return `UNKNOWN`.
This is not general semantic parsing or open-ended entailment validation.

## Rehearsal execution and integrity

Exactly **4 disposable cases x 4 cells x 2 passes + 8 replays = 40 requests**
ran in eight sequential cold workers, five requests each. Pass two reversed
cell order. There were four distinct 32/48-turn synthetic conversations with
new domains/values and no gold answers, scorer or oracle route labels. They
exercised literal copying, missing/unparsed coverage, corrections and a
two-premise LM workload with **481/491 fitted input tokens**. The inputs and
outputs are excluded from any future registered benchmark.

The [single-use freeze](../../artifacts/evidence-first-prototype/rehearsal-001/rehearsal-freeze.json)
pins sources, disposable inputs, runtime dependencies and the same Qwen/selector
asset bytes as v5. Its [source archive](../../artifacts/evidence-first-prototype/rehearsal-001/source.zip)
includes the decision as it stood at freeze time. No policy code was changed
after freezing or in response to outputs. Each worker loaded the backbone,
including copy/abstention workers, using CPU float32, two Torch threads, seed
81751, deterministic greedy decoding, 512-token input and 64-token answer caps.

All 40 request receipts and eight setup/worker/resource receipts are under
[rehearsal-001](../../artifacts/evidence-first-prototype/rehearsal-001/).
Each `pass-N/CELL/requests.jsonl` records fitted source bytes and manifests,
selection omissions versus fit evictions, prompts/native IDs, generated IDs,
policy/provenance, parsing/validation and tokenization costs, LM costs, answer
bytes/BPE and request CPU/wall. Each `pass-N-CELL-cost.json` records cold
process-tree costs and per-request memory/disk observations or bounds.

Replay, cross-pass and paired-control prompt/source checks passed. There were
**no runtime, resource, provenance or replay failures**, no retries and no
unlogged/unknown LM token counts. The four generated synthesis outputs failed
the frozen support-format validator and were returned as `UNKNOWN`; no
unsupported synthesis payload was released. These are integrity observations,
not accuracy scores or grounds to tune the policy. No full-history lookup,
new selector training, held-out input or registered benchmark request occurred.

## Measured resource costs

The [summary](../../artifacts/evidence-first-prototype/rehearsal-001/summary.json)
records **24 LM calls**, **5,680 executed input tokens** and **244 output tokens**,
including all replays. The 16 bypassed generations still incur selection,
fitting, parsing, validation, tokenization and setup costs.

| Cell, both passes including replays | Requests / LM calls | LM input / output tokens | Cold wall seconds | Process-tree CPU seconds |
|---|---:|---:|---:|---:|
| Toruk original LM | 10 / 10 | 1818 / 70 | 42.635 | 83.047 |
| Lexical original LM | 10 / 10 | 1918 / 78 | 41.540 | 82.078 |
| Toruk proposed policy | 10 / 2 | 962 / 48 | 31.358 | 59.672 |
| Lexical proposed policy | 10 / 2 | 982 / 48 | 30.804 | 58.234 |
| Eight cold stages | 40 / 24 | 5680 / 244 | **146.337** | **283.031** |
| Disjoint shared preparation/controller/audit | Included above request count | No extra LM calls | **5.264** | **3.891** |
| Instrumented total | 40 / 24 | 5680 / 244 | **151.601** | **286.922** |

Cold CPU includes the controller and sampled worker descendants, reconciled
with final worker lifetime CPU. The outer
[command receipt](../../artifacts/evidence-first-prototype/verification-20261111/disposable-rehearsal.json)
records **152.052 wall seconds**, including external launch/receipt overhead.
Its wall interval overlaps the instrumented total and must not be added again.
CPU scope is the instrumented controller/worker tree, not the outer check tool.

| Component observation, summed over relevant workers/requests | Wall seconds | CPU seconds |
|---|---:|---:|
| Preparation, included in shared costs | 4.983 | 3.641 |
| Worker setup, included in cold stages | 63.513 | 91.766 |
| Whole requests, included in cold stages | 72.491 | 147.375 |
| LM generation, included in requests | 70.736 | 141.953 |
| Selection, included in requests | 1.486 | 4.125 |
| Prompt tokenization, included in requests/fitting | 0.222 | 1.125 |
| Parsing/routing/copying/support validation, excluding LM/payload tokenization | 0.010 | 0.078 |
| Manifest construction | 0.011 | 0 recorded |
| Final integrity audit, included in shared costs | 0.020 | 0.016 |

These components overlap and are not an additive bill. Small CPU measurements
are quantized; zero recorded phase CPU is not zero work. Launch, monitoring,
serialization and teardown are charged in cold-stage/shared totals even when
they lie outside request/component timers. Payload tokenization and the
overlapping fit/policy timers are separately retained in each request receipt.

Peak combined private memory was **4,714,446,848 bytes (4.391 GiB)**. Peak logical
disk was **1,001,614,252 bytes (0.933 GiB)**, including unique model/checkpoint
assets, frozen inputs/sources and run files; installed runtime/OS files are
outside that disk scope. Maximum observed monitor gap was **0.097 seconds**.
Thirty-three requests were sampled while active; seven fast requests retain
end-memory readings and conservative whole-stage peak bounds rather than a
fabricated zero peak. OS private-memory peaks also constrain the stage totals.

The longest observed request was **6.8403467 wall / 13.484375 CPU seconds**.
The longest generated output was **24 tokens**, so this rehearsal does not
demonstrate every possible 64-token request completing within the proposed cap.
Any later cap overrun must halt; it cannot justify raising a registered cap.

## Fixed-cap proposal from the predeclared rule

Use the maxima across every cell, pass and replay, without selecting favorable
timings. The largest non-request stage residuals were **10.3079241 wall** and
**19.484375 CPU seconds**. Shared costs scale by twice 48/4, as frozen.

| Proposed cap | Calculation | Seconds |
|---|---|---:|
| Request wall | ceil(2 x 6.8403467) | **14** |
| Request CPU | ceil(2 x 13.484375) | **27** |
| Cell/pass wall, 49 requests | ceil(2 x 10.3079241) + 49 x 14 | **707** |
| Cell/pass CPU, 49 requests | ceil(2 x 19.484375) + 49 x 27 | **1362** |
| Shared wall allowance | ceil(2 x 5.2638192676 x 48/4) | **127** |
| Shared CPU allowance | ceil(2 x 3.890625 x 48/4) | **94** |
| Overall registered wall | 8 x 707 + 127 | **5783** |
| Overall registered CPU | 8 x 1362 + 94 | **10990** |

Keep **6 GiB private memory** and **3 GiB disk**, including shared inputs.
The conservative projected 48-case disk footprint is **1,010,818,516 bytes**;
it is an extrapolation, not created benchmark data. Both fixed ceilings fit the
observed/projected rehearsal footprint. These caps are proposals only; nothing
was registered or run under them. Rehearsal cost remains separate from any
future benchmark, and must also be reported in combined project cost.

## Verification and remaining limits

- Coverage-first unit run: 9 passed; final focused unit/integration suite:
  **51 passed**. A misplaced test import and lint findings from intermediate
  development were corrected before freeze. No final focused failure remains.
- `scripts/verify.py` completed with **no failed checks**: 424 Python tests
  collected during that run passed, web tests were 20 passed/one opt-in skip,
  and package, frozen-source, lint/format, Windows/Linux types and existing
  repository smoke/build checks passed. The final five constraint tests and
  the updated policy were covered by the final 51-test focused run before
  freeze. The inherited pytest cache directory emitted a permissions warning;
  tests passed, and the focused run used a writable separate cache.
- Portable evidence verification passed: **816 files**, **1,848 recorded hash
  checks**, **205 saved rows**, with native prompt/decode verification and no
  held-out generation. The receipts are in
  [verification-20261111](../../artifacts/evidence-first-prototype/verification-20261111/).
- A separate offline native audit checked all **40 new saved rows**, all **12
  direct copies**, paired sources/prompts and source-freeze hashes without model
  generations. It sealed 55 rehearsal files in
  [output-sha256.json](../../artifacts/evidence-first-prototype/rehearsal-001/output-sha256.json).
  Its separate engineering-check command took 4.016 wall seconds, outside the
  rehearsal totals; see the
  [audit receipt](../../artifacts/evidence-first-prototype/verification-20261111/final-native-audit.json).
- The requested repository verification pipeline's tiny training/generation
  smoke fixtures are separate engineering checks, not Qwen rehearsal requests
  or new evidence-first study cases. No registered 48-case cases were created.

No accuracy gate was evaluated. This rehearsal does not validate general
parsing, synthesis quality, learned-selector value or stable efficiency. The
policy remains a bounded review prototype, with resource caps proposed from
this one measured workload and all contribution/stop gates unchanged.
