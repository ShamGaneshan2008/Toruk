# Core advantage audit — 8 November 2026

**Verdict: the joint accuracy/complete-compute advantage remains unestablished.
Fresh reproduction of the historical TORUK comparison is BLOCKED.** Its original
M6 selector weights are missing. No selector improvement, training experiment or
new held-out comparison was attempted. This follows the requested prerequisite
gate; a different selector would be a different experiment.

## Starting state and evidence

Branch `main`, commit `1d723b1ddf974e12014fdfe0ae4c6a99e68619b6`.
Initial `git status -sb`: `## main...origin/main`; tracked diff, staged diff and
untracked-file listing were empty. No existing work was overwritten. README,
architecture, experiment registry, latest chat launch/owned-model reports,
historical protocols and runtime/scorer/selector code were inspected first.
No commit, push, deployment, publication, paid compute or model download occurred.
Verification alone runs its existing tiny bounded smoke training fixtures.

Evidence root: [artifacts/core-advantage-20261108](../../artifacts/core-advantage-20261108/).
It contains starting state/environment, all 221 checkpoint paths and hashes,
raw historical/fresh answers, reconstructed source text and prompt token IDs,
latest archive rescoring, offline failure review, refusal replay and check logs.
The original archives were preserved. The new audit is separate from the frozen
evaluator and production chat code.

## Historical reproduction and prerequisite repair

The 20-question release result is **not the latest matched comparison**. It is
the October SmolLM/M6 comparison. The November 7 Qwen launch gate is newer and
has recent-context, lexical and trained-selector modes; its results are below.
These datasets, backbones, output budgets and selectors cannot be pooled.

Historical generator: external `HuggingFaceTB/SmolLM2-135M-Instruct`, revision
`12fd25f77366fa6b3b4b768ec3050bf629380bac`; weights SHA-256
`5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`.
Actual local weights match. Tokenizer JSON SHA-256:
`9ca9acddb6525a194ec8ac7a87f24fbba7232a9a15ffa1af0c1224fcd888e47c`.
All backbone-file hashes and the complete generation config are retained in
`historical-audit.json`. CPU float32, two Torch threads, 512 prompt tokens,
32 output tokens, greedy temperature 0/top-p 1 and the historical SmolLM chat
template were preserved. Unlike current Qwen, this SmolLM path adds no Toruk
system instruction. There is no random sampling seed; bootstrap seed is 23.

Toruk supplied turn selection, fitting and serving, **not the pretrained
language ability**. The historical selector is a frozen recurrent model, not
the available eight-feature JSON ranker. Expected path:
`artifacts/m6-validation-001/recurrent/checkpoint.pt`; expected SHA-256:
`479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`.
The path is absent and none of 221 `.pt` files under `artifacts/` matches.
Retained M6 metrics/config record seed 23, 12 training steps, four slots, width 32,
two layers, four heads and 64 local byte positions. Metadata cannot replace weights.

The first audit deliberately failed because the checkout fixture hash was
`178f1580f46ee1149d4158974ada184669d1945b20524d5f57531a230a9591e6`.
Replacing its 28 CRLF line endings with LF exactly restores the registered hash
`86e31ab8afccb0e7ab88817fc11b7be4585a7d261c3d99f93eef60540c63a0c6`.
The new auditor accepts only this hash-verified reconstruction and reports both
identities. It does not alter the checked-out fixture or accept changed content.
The exact recovered bytes are retained as `frozen-fixture.json` in the evidence
root for a later original-evaluator run after the correct selector is restored.
The initial failure is retained as `checks/historical-audit.{json,log}`.

Forty saved rows were rescored with the unchanged historical scorer. All selected
IDs were checked, source text reconstructed and all 40 selected prompt token
counts verified against the actual tokenizer. Prompt IDs here are reconstructed,
not claimed to have been saved during the original run. Fresh BASELINE inference
then reproduced **20/20 raw answers exactly**, including selected/output counts.

| System / evidence | Correct | Selected prompt | Output | Backbone tokens | Response sum s |
|---|---:|---:|---:|---:|---:|
| Historical BASELINE, rescored archive | 6/20 | 1,818 | 254 | 2,072 | 15.260 |
| Historical TORUK, rescored archive | 6/20 | 1,546 | 278 | 1,824 | 15.552 |
| Fresh BASELINE, actual inference | 6/20 | 1,818 | 254 | 2,072 | 18.357 |
| Fresh historical TORUK | BLOCKED | — | — | — | — |
| Improved TORUK | NOT_RUN | — | — | — | — |

The archive still supports the arithmetic **14.96% selected-prompt reduction**,
not a fresh paired reproduction. The original 35% token-saving and 60% quality
gates remain failed. Bootstrap descriptive interval: 1.35–27.28% token reduction,
0–0 percentage points quality difference. This tiny fixture cannot establish
population quality equivalence. Distant retrieval is 1/2, corrections 1/2 and
exact instruction output 1/2 per mode. The exact archive-key recall fails in both.
It is not a separate punctuation-sensitive exact-recall benchmark.

Historical full-input counts were 1,818 in **each** mode. TORUK scans history
through its own recurrent model in addition to the backbone prompt. Its 1,824
reported `total_tokens` excludes that selector computation. TORUK produced more
output and took 1.9% longer in the original measurement. Selector forward/token
work, separate selector CPU time, history/fitting tokenization work, per-mode
peak memory, FLOPs and energy are unavailable. The saved 1,475,166,208-byte Windows
private-memory observation is shared/cumulative, not a per-mode memory comparison.
Fresh BASELINE startup plus replay was 41.969 s; fresh peak memory was not sampled.
No complete-system efficiency result can be derived from these partial counters.

Current replay host: Windows 11 build 26100, AMD64 family 25/model 80, six physical
cores/twelve logical CPUs, 25,116,758,016 RAM bytes; CPU inference, no CUDA in Torch.
Exact marketing CPU name was not retrieved: the read-only CIM query was denied.
Python 3.12.14, Torch 2.14.1+cpu, Transformers 5.20.2, Safetensors 0.8.0,
Node 24.15.0. Original release protocol records Python 3.14.6 and Node 24.19.0;
this is answer reproduction across those environment differences, not a matched
hardware latency comparison. Original M6 training hardware metadata describes a
different Intel host and must not be attributed to the current replay.

## Failure diagnosis

All 28 wrong historical rows are individually classified with exact raw answers,
source IDs, source text and rationale in
[failure-review.json](../../artifacts/core-advantage-20261108/failure-review.json)
and [the readable table](../../artifacts/core-advantage-20261108/failure-review.md).
These are offline interpretive labels, not measurements of internal model causes.
Primary categories are exclusive; rubric limitations are separately tagged.

| Historical primary cause | BASELINE | TORUK |
|---|---:|---:|
| Relevant evidence omitted | 0 | 0 |
| Wrong evidence selected as the primary failure | 0 | 0 |
| Stale fact used | 1 | 1 |
| Vague reference resolved incorrectly, established from output | 0 | 0 |
| Evidence present but generator/rubric failed | 12 | 12 |
| Unsupported question answered as fact | 1 | 1 |

The generator/rubric group includes digit-only formatting and two reasonable
unknown-answer refusals per mode. It does not imply twelve false factual answers.
The frozen unsupported proxy is 3/20 per mode: two private-value refusals plus
one conflicting-season guess. Offline task-assertion review instead identifies
one unsupported drink preference, one obsolete deadline and one unsupported
season guess per mode. Neither private-value refusal invents the requested value.
This review does not audit every generic assistant-capability statement.

Representative actual cases:

- Distant exact key: source `CEDAR-19` is retained; both answer `I noted the archive key.`
- Correction: Thursday is retained; both answer `I will use the corrected day.`
- Preservation/stale fact: both answer `My hobby is playing chess. The deadline is Monday.`
  Friday was retained. The hobby is right but the appended deadline is obsolete.
- Vague reference: ORBIT is retained; both answer `I noted the codename.`
  A failed reply alone does not show which referent the model internally chose.
- Conflict: both notes are retained; both answer `My favorite season is spring.`
- Unknown: `I don't have the ability to provide information about your mother's
  maiden name` is a refusal, though outside the frozen permitted phrase list.

Fresh refusal replay also matches all three archived BASELINE requests/answers
and prompt counts. Fresh math gives `5 + 5 = 10.`; the full earlier refusal history
gives `I'm sorry for any confusion, but as a chatbot, I don't have the capability
to access or interact with online content.` at both 32 and 64 output budgets.
Historical TORUK refusal replay remains blocked. This is backbone/history
behavior, not evidence of a serving fault or persistent learned Toruk memory.

The historical 20-case set has no dedicated gist stratum. The separate, already
published [recall V2 archive](recall-results-20261104.md) covers six exact, two
gist, two clear-reference, one ambiguous-reference and one missing-evidence case
per split, with 18 distraction pairs. Its held-out recent/lexical/old-selector/
envelope scores are 0/4/4/4 of 12; gist is 0/1/1/1 of 2, exact is 0/2/2/2 of 6.
The report records invented 24-hour retention claims even in gist-rubric passes,
and a vague `it` answered with weather text. Those are **historical context**,
not newly reproduced inference or fresh held-out evidence in this audit.

## Latest three-system comparison: archive rescore only

The November 7 launch archive was located and independently rescored without
rerunning its model requests. All row scores, scored aggregates and **all 41
requests' cost totals** match. It has 26 identical static histories (25 regression
cases plus a greeting), eight generated-history final turns and three repetition
turns: 37 scored results. Four intermediate rollout turns consume work but are
not scored final questions. Generated histories can differ by method.

All three use Qwen/Qwen2.5-0.5B-Instruct at revision
`7ae557604adf67be50417f59c2c2f167def9a775`, SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`,
CPU float32/two threads, 512 prompt tokens and 64 greedy output tokens.
Trained v2 selector hash:
`abd9d2d1c20edb3ad5cf3282f8a26fca49fb44d508d4ba2ada5ebc9c666b7548`.
Lexical-v2 is transparent word-overlap retrieval with explicit correction links.
There is no summarizing model or persistent session memory in these selectors.

| Metric | Recent BASELINE | Lexical retrieval | TORUK trained v2 |
|---|---:|---:|---:|
| Frozen quality /37 | 25 | 27 | 25 |
| Static regression quality /25 | 14 | 16 | 15 |
| Distant recall /3 | 1 | 3 | 3 |
| Exact recall /3 | 3 | 3 | 3 |
| Correction /3 | 1 | 1 | 1 |
| Unsupported proxy, not false-assertion count | 4 | 4 | 4 |
| Full input tokens, all 41 requests | 5,614 | 5,617 | 5,600 |
| Selected prompt tokens, all requests | 5,614 | 4,978 | 4,894 |
| Output tokens, all requests | 379 | 382 | 359 |
| Backbone prompt + output | 5,993 | 5,360 | 5,253 |
| Selector ms / scanned bytes | 0 / 0 | 1.691 / 5,718 | 1.150 / 5,694 |
| History tokenization ms | 57.085 | 58.224 | 58.958 |
| Prompt fitting ms | 26.381 | 23.335 | 24.900 |
| Proxy request sum s | 96.839 | 92.170 | 91.427 |
| Inference-tree CPU s | 192.313 | 181.203 | 181.469 |
| Sampled tree RSS bytes | 2,682,904,576 | 2,662,109,184 | 2,663,260,160 |
| Sampled tree private bytes | 4,636,938,240 | 4,660,998,144 | 4,627,832,832 |

Costs include intermediate replies and history tokenization/selection/fitting;
CPU omits browser/proxy CPU and is not FLOPs or energy. Summed RSS can double-count
shared pages. Selector persistent state is zero bytes; that excludes weights,
transient history storage, Python objects and the backbone/KV cache. All three
quality gates fail. The generated histories and uncontrolled cache/host conditions
prevent a strict causal matched-compute conclusion from these totals.

Every wrong scored row is included in the new offline failure review: recent
10 generator/rubric + 2 stale; lexical 8 + 2; trained 10 + 2. Rubric false negatives
are 5/5/7 respectively (Unknown, number words and an impossibility paraphrase).
No selected-evidence omission was identified as the primary cause of these
wrong replies. Trained v2's apparent refusal regressions are correct number-word
answers missed by the frozen matcher; scores were not rewritten. Two corrections
per mode genuinely repeat obsolete values with the correction retained. These
limits prevent treating the four unsupported-proxy flags as four invented facts.

## Improvement gate and verification

Hypothesis, numerical optimization success criterion, regression limit, new
development split, untouched held-out split and mechanism freeze: **NOT_RUN**.
The missing historical selector fails the prerequisite before this stage. No
published questions were promoted into a fresh held-out set and no training
consumed them. Audit acceptance criteria were exact 20/20 BASELINE-answer parity,
40/40 saved-score and prompt-count parity, valid source provenance, and explicit
cost scope; those checks pass. These are reproducibility criteria, not an
accuracy/efficiency improvement hypothesis.

Fresh inference was bounded to 20 × 32-token BASELINE requests under a 180 s
wrapper and the three archived refusal requests under 120 s. Existing verification
has 420 s test, 300 s per type-check and 120 s other-stage timeouts. No model was
trained to replace the missing checkpoint.

Exact primary commands, from repository root (each `scripts/check.py` record
retains command arguments, source hashes, result, duration and complete output):

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 180 --output-dir artifacts/core-advantage-20261108/checks historical-audit-lf-recovery -- .\.venv\Scripts\python.exe scripts/audit_chat_advantage.py --output artifacts/core-advantage-20261108/historical-audit.json --replay-baseline artifacts/chat-foundation-001/backbone
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 120 --output-dir artifacts/core-advantage-20261108/checks refusal-replay -- .\.venv\Scripts\python.exe scripts/replay_refusal_diagnostic.py --reference artifacts/chat-repetition-exact-20261101/full-history-matched.json --backbone-dir artifacts/chat-foundation-001/backbone --output artifacts/core-advantage-20261108/refusal-replay.json
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 120 --output-dir artifacts/core-advantage-20261108/checks latest-archive-audit -- .\.venv\Scripts\python.exe scripts/audit_chat_advantage.py --output artifacts/core-advantage-20261108/latest-archive-audit.json --launch-dir artifacts/chat-launch-gate-20261107
.\.venv\Scripts\python.exe artifacts/core-advantage-20261108/build_diagnosis.py
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 120 --output-dir artifacts/core-advantage-20261108/checks audit-tests-expanded -- .\.venv\Scripts\python.exe -m pytest -q tests/test_chat_advantage_audit.py tests/test_chat_release_eval.py
.\.venv\Scripts\python.exe -X utf8 scripts/check.py --timeout 120 --output-dir artifacts/core-advantage-20261108/checks readiness-integration -- .\.venv\Scripts\python.exe scripts/smoke_chat_readiness.py --output-dir artifacts/core-advantage-20261108/readiness
.\.venv\Scripts\python.exe -X utf8 scripts/verify.py --prefix core --output-dir artifacts/core-advantage-20261108/verification
git diff --check
```

After restoring and hash-verifying the original checkpoint, the original paired
runner can use the recovered fixture and fresh output paths; this command was
**not run**, because the checkpoint is absent:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_chat_release_v2.py --fixture artifacts/core-advantage-20261108/frozen-fixture.json --backbone-dir artifacts/chat-foundation-001/backbone --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --output artifacts/core-advantage-20261108/fresh-paired.json --report artifacts/core-advantage-20261108/fresh-paired.md
```

The audit/rubric focused suite passed 13 tests. New checks reject changed
questions, inconsistent scores/token arithmetic, duplicate rows, unknown source
IDs and changed selector identity; they verify that only role/content reaches
the generator. Latest-archive tests count intermediate generation and check
matched static histories. Readiness integration passes both missing-model cases
through real Python/Node HTTP with visible 503 responses. Full verification
completed with exit 0 and **all 26 stages PASS**:

| Local verification | Result |
|---|---|
| Full Python suite, including HTTP integration | 270 passed in 158.52 s |
| Node syntax/tests | PASS; 20 passed, 1 opt-in live-page test skipped |
| Ruff lint/format | PASS; final changed-source checks also pass |
| Windows/default and Linux-target mypy | PASS, 35 source files each |
| CLI help/diagnose, package/import/install | PASS |
| Frozen sources, independent cases, conversation leakage gate | PASS |
| Owned/foundation/research smoke, resume/validation/generation | PASS |
| Source and wheel build | PASS |
| Working/staged `git diff --check` | PASS |

The test-stage source hashes match the final audit script and tests. Earlier
verification lint/format ran before the last auditor additions; the retained
`final-audit-static` and `final-audit-format` checks cover those final bytes.
Smoke-script completion is operational success: the owned smoke's scientific
criterion remains false. No skipped live-page test is represented as a visual
browser check. Per-stage commands/results/times are in `verification/core-*.json`
and the compact `verification-summary.json`.

GitHub Actions configuration was inspected: Node 22 syntax/tests; Ubuntu Python
3.12 lint/format, Windows/Linux mypy, pytest (including real page-handler → Node
proxy → Python HTTP fixture), frozen-source checks, data/leakage validation,
bounded smoke train/resume/reproduction and package build; Windows additionally
reproduces the owned smoke fixture from a path with spaces. Chat weights are not
downloaded in CI, so these jobs do not establish real-model accuracy. The GitHub
connector returned no PR-triggered runs for starting HEAD; its wrapper only
queries PR events/first page. Push/manual runs were not observed. Current local
uncommitted changes have not been exercised by hosted CI.

Changed files: new audit script and audit tests; this report; README,
architecture and experiment registry; `.gitattributes` to preserve new evidence
bytes; `.gitignore` for generated verification wheels; and the new evidence
directory. Production model/selector/scorer/default behavior is unchanged.

**Highest-priority blocker:** restore the exact original M6 selector with the
recorded SHA-256. Until then, fresh matched historical TORUK reproduction is
impossible, and the requested evidence-driven mechanism improvement stays gated.
