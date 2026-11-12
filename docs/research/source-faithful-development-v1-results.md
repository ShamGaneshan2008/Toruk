# Source-faithful answer development v1 results

12 November 2026. **Both answer-policy gates FAIL; learned-selector gate FAIL.**
The bounded development run completed once without a runtime, resource or
integrity failure. Its narrow copying/support mechanisms worked on these
fixtures, but the frozen no-regression requirement did not. This does not
authorize policy adoption or establish a learned-selector advantage.

The initial checkout was clean `main` at
`bf0f7482f21687db9788d2bfc4555cca5b0dd879`, root `D:/Toruk`. The original
48-case decision was neither edited, relabeled, registered nor run. Its gates,
the prototype, both earlier feasibility reports, production chat and v1-v5
evidence remain byte-unchanged. No held-out input or new selector training.

## Frozen development protocol

The separate [protocol](source-faithful-development-v1-protocol.md) covers only
single-source byte copying, entity/attribute binding, explicit corrections and
preservation, and scoped absence versus incomplete coverage. Synthesis remains
excluded and **not ready**: four rehearsal-001 outputs omitted a premise; all
12 forced 64-token v2 continuations were abstained. These failed feasibility
results remain limitations, not successes reclassified by the new hypothesis.

The [registration](../../artifacts/source-faithful-development-v1/registration.json)
was sealed before any study generation at SHA256
`60712c360bc5bf113a4473fccb81b485524f6617b60be4b48b3a05889bbe3cf6`.
It pins 12 fresh authored 32/48-turn development cases, separate source-linked
labels and byte offsets, scorer/policy/harness/tests, source ZIP, exact request
order, gates, resources, dependency versions and model/selector hashes.
The [inputs](../../artifacts/source-faithful-development-v1/inputs.json) contain
no labels; workers never load the
[evaluator labels](../../artifacts/source-faithful-development-v1/labels-evaluator-only.json).
Labels were manually authored and structurally checked, without independent
human review. Comparison for overlap used only earlier observed disposable inputs.

The unchanged backbone is Qwen/Qwen2.5-0.5B-Instruct, revision
`7ae557604adf67be50417f59c2c2f167def9a775`, model SHA256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
CPU float32, two Torch threads, seed 81751, deterministic greedy decoding,
ordinary EOS, maximum 64 new tokens and 512-token input were frozen. No
forced-length diagnostic decoding. The selectors, original LM prompts/output
handling, common whole-turn fit and answer policy are unchanged existing bytes.

There were **12 x 4 x 2 + 8 = 104 requests**, including eight unscored replays,
in eight sequential cold workers. Pass two reversed cell order. Every worker
loaded the backbone, even if it bypassed generation. Both selectors used the
same policy. Control-policy pairs had identical selected/fitted sources,
manifests and native prompt IDs. No full-history lookup supplied additional
answer evidence. All raw outputs were sealed before scoring.

One **pre-registration engineering failure** is retained in
[freeze.log](../../artifacts/source-faithful-development-v1-checks/freeze.log):
the first freeze command used the wrong historical v2 input filename. It wrote
no registration, cases, labels or model outputs; the created directory was
verified empty before removal. The path was corrected before the successful
freeze, without changing cases, labels, gates or caps. This failed command cost
1.6611733 outer wall seconds; its CPU was not instrumented and is unknown.
There was no inference retry, repair after results, replacement case or raised cap.

## Quality and contribution decisions

These are 12 unique case outcomes per cell; pass two reproduced them exactly.
Replays and passes do not enlarge the sample. Exact payload accuracy uses
UTF-8 bytes without trimming, normalization, substring credit or an LM scorer.
Support-state and source/correction checks are scored separately; LM controls
receive no invented support certificate.

| Cell | Exact payloads | Copy / binding / correction / coverage, each out of 3 | Support states and provenance |
|---|---:|---|---|
| T-LM | 8/12 | 0 / 2 / 3 / 3 | No certificate |
| L-LM | 7/12 | 0 / 2 / 3 / 2 | No certificate |
| T-P | 11/12 | 3 / 3 / 3 / 2 | 12/12 each |
| L-P | 11/12 | 3 / 3 / 3 / 2 | 12/12 each |

Both proposed cells satisfy the frozen 10/12 accuracy, 2/3 category, two-case
gain over own and stronger controls, support/provenance and efficiency hurdles.
**Both fail no-regression** on `sf1-11-satinviaduct`. Its question uses default
full-history scope; the requested `west arch 386` span is retained. Other scope
bytes are omitted by both selectors, so the conservative positive-coverage rule
returns `UNKNOWN` with `coverage-incomplete`. Both controls return the correct
value. This is a real payload regression under the full-scope scorer, despite
correct support-state behavior. The requested fact itself was not evicted or
missed. No full-history scan or post-result scope narrowing repairs this failure.

| Frozen comparison, same in both passes | Policy-correct/control-wrong wins | Losses | Decision |
|---|---|---|---|
| T-P vs T-LM | Cases 01, 02, 03, 06 | Case 11 | P_T FAIL |
| L-P vs L-LM | Cases 01, 02, 03, 06, 12 | Case 11 | P_L FAIL |
| T-P vs L-P | None | None | Selector gate FAIL |

Cases 01-03 preserve literal tabs, repeated/edge spaces and decomposed Unicode;
the controls return only fragments. Case 06 correctly abstains on two unmarked
conflicting values. Cases 04-05 bind the requested entity/field amid related
distractors. Cases 07-09 return a corrected value, preserve an unrelated field
and retain a two-step correction chain. Case 10 certifies absence only in its
fully covered, parsed explicit scope. Case 12 has an unsupported source line:
both policy cells return coverage-incomplete; lexical LM instead substitutes
the collar value for the missing key. UNKNOWN on this case does not certify absence.
The [sealed results](../../artifacts/source-faithful-development-v1/results.json)
retain every case score and every gate boolean for both passes.

T-P and L-P have identical payloads, support states and correction/source
outcomes, though their fitted contexts differ. Both execute zero LM tokens;
zero versus zero cannot satisfy the frozen strict selector token-saving gate.
Toruk's policy requests also cost more than lexical's. There is no selector
contribution or extra-evidence explanation for the shared mechanism gains.
Because neither complete policy gate passes, the registered decision is to
**reject policy adoption and selector contribution under v1**. The copying and
support observations do not override that decision or revive the 48-case study.

## Requests and complete measured study costs

All 104 request receipts are in
[the run directory](../../artifacts/source-faithful-development-v1/), under
`pass-N/CELL/requests.jsonl`. They retain raw and published payloads, native
IDs, source spans/revision hashes, coverage/parse reasons, correction chains,
selection omissions versus fit evictions, tokens and component/request costs.
Worker setup/lifecycle, controller/tree costs and sampled/bounded resources
are retained separately. The
[raw-output seal](../../artifacts/source-faithful-development-v1/raw-output-seal.json)
predates label evaluation; the
[final seal](../../artifacts/source-faithful-development-v1/output-sha256.json)
also covers scores and totals. There are no missing/unknown study token counts,
failed requests, extra lookups or unlogged LM helpers.

| Cell, both passes including replays | Requests / LM calls | LM input / output | Cold wall seconds | Tree CPU seconds |
|---|---:|---:|---:|---:|
| T-LM | 26 / 26 | 2958 / 116 | 58.271 | 116.109 |
| L-LM | 26 / 26 | 3218 / 128 | 57.195 | 117.906 |
| T-P | 26 / 0 | 0 / 0 | 20.079 | 33.703 |
| L-P | 26 / 0 | 0 / 0 | 18.515 | 30.688 |
| Eight cold stages | 104 / 52 | 6176 / 244 | **154.060** | **298.406** |
| Disjoint registration/controller/audit | No additional calls | 0 / 0 | **10.853** | **9.875** |
| Instrumented study total | **104 / 52** | **6176 / 244** | **164.913** | **308.281** |

The control-policy efficiency gates allocate shared cost equally across eight
stages, as frozen. T-P saves 63.27%/61.94% wall and 68.90%/70.09% CPU in passes
one/two; L-P saves 65.56%/63.53% wall and 73.66%/71.23% CPU. Executed LM token
savings are 100% for both, with nonzero selection/setup/parsing costs charged.
These finite-workload savings do not rescue the failed quality gate or establish
stable efficiency. Totals include replays, never count the components again.

| Overlapping component observation | Wall seconds | CPU seconds |
|---|---:|---:|
| Cold worker setup | 64.7040274 | 94.328125 |
| Whole requests | 78.3253449 | 157.593750 |
| LM generation, within requests | 74.3000202 | 148.921875 |
| Selection | 3.6049484 | 7.359375 |
| Prompt tokenization | 0.3190763 | 0.937500 |
| Fit including its tokenization | 0.0695650 | 0.250000 |
| Manifest construction | 0.0244543 | 0.093750 |
| Parsing/routing/copy/support validation, excluding payload tokenization | 0.0181804 | 0.015625 |
| Payload tokenization | 0.0141438 | 0.078125 |

Phase CPU is quantized; zero in a receipt is not free work. Launch, imports,
monitoring, serialization and teardown are charged in lifecycle/shared totals,
even outside individual phase timers. History input volumes totaled 62,672
message-content bytes across all requests; fitted source bytes totaled 10,136.
These are boundary volumes, not hardware counts of repeated algorithm reads. Prompt tokenizer
work was 208 calls / 43,104 positions, distinct from executed LM tokens. Total
published payload was 876 bytes / 440 equivalent native BPE tokens. There were
36 copies and 16 policy abstentions including replays, with four absent, four
conflicting and eight coverage-incomplete states. No fit eviction occurred.

Maximum request cost was **2.0560589 wall / 4.0625 CPU seconds**. Per-cell request
wall median/p95 across both passes and replays: T-LM 1.604051/1.925397,
L-LM 1.555583/1.856061, T-P 0.065380/0.085357, L-P 0.003200/0.019599 seconds;
p95 uses the nearest-rank convention. These short prompts were 98-145 tokens,
and the longest generated output was eight tokens. This run does not retest
near-512 inputs or prove every 64-token request completes within the cap.

Peak combined private memory was **4,126,953,472 bytes**; sampled logical disk
was **1,002,484,976 bytes**, including unique runtime assets, source/input/run
files but excluding installed runtime/OS. A final complete inventory additionally
includes protected earlier audit inputs: **1,005,126,949 bytes / 302 files**,
below 3 GiB; see the separate
[footprint receipt](../../artifacts/source-faithful-development-v1-checks/complete-study-footprint.json).
The sampled value alone is not a complete disk inventory. The maximum monitoring gap was
0.121075 seconds. Eighty-two requests were sampled while active; 22 fast
requests retain end readings and conservative stage-peak bounds. OS private
peaks constrain stage memory too. No fabricated zero request peaks.

All frozen caps remain unchanged: request 26 wall/51 CPU, worker 360/714,
eight stages 2880/5712, shared 120/120, overall **3000/5832 seconds**, private
memory **6 GiB**, disk **3 GiB**. No new cap proposal was fitted to these outputs.

The successful freeze/execution outer command intervals were 4.8310842 and
160.5685889 seconds, **165.3996731** combined. They overlap the instrumented
study, include external launch/final serialization, and must not be added to it.
The failed pre-freeze command's 1.6611733 seconds is separate, giving
167.0608464 outer command seconds for these three commands; its unknown CPU
prevents an exact all-attempt CPU total. Engineering tests, portable/native
audits and repository verification have separate command receipts under
[checks](../../artifacts/source-faithful-development-v1-checks/), outside study
costs. The complete registered study CPU and every generation remain accounted.

## Verification and limits

- Before the successful freeze, **85 focused tests passed**, including 18 new
  boundary/scorer/gate tests and the existing 67 policy/integration/v2 tests.
  Lint and formatting passed. No policy or executable study source changed
  after registration or in response to outputs.
- The native saved-output audit passed for **104 rows / 36 exact copies** and
  verified **189 protected earlier files**, without model generations.
- A separate post-study offline audit reconstructed fitted sources and original
  prompts, replayed **52 policy decisions / 96 case scores**, and reconciled
  the frozen schedule, resource allocation, contribution decisions and output
  seals. This audit uses the published tokenizer and no model weights/generations;
  its code and receipt are retained separately from the frozen scorer.
- Both preserved-evidence verifiers passed after the study: legacy **816 files /
  1848 hash checks / 205 saved rows**, and prototype **188 files / 52 saved rows**,
  retaining the original synthesis failures and unchanged old decision gates.
- `scripts/verify.py` passed **all 26 checks**, including **479 Python tests**,
  web **20 passed / one opt-in skip**, lint/format, Windows/Linux types,
  frozen sources, packaging/build and existing repository smoke fixtures.
  Its outer engineering-check interval was **357.689361 wall seconds**, separate
  from study cost. Pytest emitted the inherited cache-directory permissions
  warning; no test failed. The focused run used a separate writable cache.
- `git diff --check` passed. Separate no-index checks also found no whitespace
  errors in the four new code/test/protocol/report files, which ordinary Git
  diff does not inspect while untracked. No tracked diff or staged file exists.
  Final status is `main` at the original commit with only the two new artifact
  directories, two new documents, harness and test untracked.

The complete saved review record adds the
[harness](../../scripts/source_faithful_development_v1.py),
[tests](../../tests/test_source_faithful_development_v1.py), this report/protocol,
58 frozen run/result files and the check receipts/logs. A final review inventory
binds the new files separately; it does not rewrite either experimental seal.
The [copied repository receipts](../../artifacts/source-faithful-development-v1-checks/repository/)
are exact copies of top-level JSON/log files. Generated build archives, fixture
models/data, caches and workspaces remain under ignored `.readiness`, `build`,
package metadata or tool caches and are excluded from the review record. External
backbone/selector weights, installed libraries and OS files are identified where
needed but not copied. The retained `source.zip` contains sources and labels,
not runtime weights. No original exclusion list or portable record was modified.

The study is small, synthetic and authored around a deliberately narrow grammar.
Its explicit scopes usually cover only one or two recent user turns; it does
not validate general prose, non-user authority, reference resolution, long-range
retrieval, semantic absence or unseen tasks. Conservative full-scope coverage
caused an observed accuracy regression. No independent human label review or
held-out validation was performed. Neither aggregate gains nor deterministic
repeats establish generalization, novelty, learned-selector value, synthesis
readiness, stable efficiency or production safety. All new work remains
uncommitted for review; no push occurred.
