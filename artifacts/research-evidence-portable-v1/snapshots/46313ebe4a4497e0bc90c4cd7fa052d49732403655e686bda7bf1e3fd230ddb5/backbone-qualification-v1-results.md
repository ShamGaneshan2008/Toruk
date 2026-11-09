# Answer backbone qualification v1 - 8 November 2026

**Registered gate: PASS for Qwen, FAIL for SmolLM.** Qwen2.5-0.5B-Instruct
scores exactly 18/30 overall and 15/25 on known facts, meeting both 60% floors
within the new local budget. This qualifies an external generator on one small
plain-context set. Exact copying is 0/5 and preservation is 1/5 for Qwen;
conversation reliability, longer-context quality and selector superiority remain
unestablished. Production chat defaults/status are unchanged.

## Checkout, preservation and environment

Work ran in `D:\Toruk`, branch `main`, starting commit
`25d4ec09e01397b43b9b16ad08faeca7cdb22eb0`. Starting status:

```text
## main...origin/main
 M .gitattributes
 M .gitignore
 M README.md
 M docs/architecture.md
 M docs/experiments.md
 M docs/reproducibility.md
 M pyproject.toml
?? .idea/Toruk.iml
?? .idea/inspectionProfiles/
?? .idea/misc.xml
?? .idea/modules.xml
?? .idea/vcs.xml
?? artifacts/m6-successor-v1/
?? configs/m6-successor-v1-execution.json
?? configs/m6-successor-v1.json
?? docs/research/m6-successor-v1-protocol.md
?? docs/research/m6-successor-v1-results.md
?? scripts/m6_successor.py
?? tests/test_m6_successor.py
```

The starting diff, staged diff (empty), untracked inventory, `.idea` hashes,
all previous successor file/source hashes and exact original shared-document
bytes are retained in `artifacts/backbone-qualification-v1/starting-state.json`
and `initial-files/`. Ending HEAD/branch and preservation checks are in
`final-state.json`. No branch creation, commit, push, deployment, publication,
candidate training or paid jobs were performed. Historical M6 remains **NOT REPRODUCIBLE**;
its expected raw-checkpoint hash
`479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`
was never changed or assigned to these models.

The existing documented `.venv` from the successor work was reused. No new
packages or model downloads were needed. Python 3.12.14; Torch 2.15.0+cpu;
Transformers 5.22.2; Tokenizers 0.23.3; Safetensors 0.8.0; Psutil 7.2.2;
Node 24.15.0/npm 11.12.1. `environment.json` and `requirements-lock.txt`
record this session. Host: Windows 11, Ryzen 5 5600G, 6 cores/12 logical CPUs,
25,116,758,016 RAM bytes, about 13 GB available and 713 GB free disk at setup.
CPU float32 with two Torch threads; no accelerator used.

## Saved-output diagnosis of the successor result

No old question was rerun or supplied to a new candidate. Existing saved raw
answers, selected contexts and reviewed labels were inspected offline.
`prior-diagnosis.json` retains every case and source identity. The historical
frozen scores remain recent 0/24, lexical 7/24, TORUK 5/24.

| Exclusive primary cause | Recent | Lexical | TORUK |
|---|---:|---:|---:|
| Correct by frozen rubric | 0 | 7 | 5 |
| Relevant evidence omitted | 20 | 0 | 5 |
| Generator failed with task context present | 1 | 17 | 11 |
| Valid missing-information abstention rejected | 3 | 0 | 3 |

Known evidence was retained in 0/20, 20/20 and 15/20 cases respectively.
The cause table assigns omission before assessing downstream generation; omission
and a wrong factual assertion can coexist. A separate answer-content review
identifies 9, 1 and 3 genuinely wrong factual assertions respectively (recent:
eight wrong towns plus one unsupported country; TORUK includes two stale towns).
There are also 12, 16 and 13 irrelevant/non-answer replies, respectively;
these are failures, not automatically fabricated facts. No invented locker-key
value was observed. The old missing-response proxy is not a false-fact count.

Representative raw cases:

- Lexical `heldout-distant-3`: evidence Busan; answer "The destination town
  belonging to record H9C1324B91E is Hanoi, Vietnam." Evidence present, wrong answer.
- Lexical preservation/exact cases repeatedly answer "Weather entry received."
  despite retained evidence. Reference cases give irrelevant AI refusals.
- Recent `heldout-missing-1`: "The locker key for record H5C8DC22FD7 is not known."
  This valid abstention fails the old frozen rubric.
- TORUK `heldout-correction-1`: selects obsolete evidence and answers Bremen
  rather than corrected Lusaka. This is a selector failure upstream of generation.

The preexisting, separate abstention review would give 3/24, 7/24 and 8/24;
these are **post-hoc analysis only**, not replacement frozen scores. Toruk owns
selection/prompt fitting and the rubric; the pretrained SmolLM supplies language
and factual generation. This new milestone isolates that external generator.

## Registered inputs and limits

[Protocol](backbone-qualification-v1-protocol.md),
[config](../../configs/backbone-qualification-v1.json) and
`artifacts/backbone-qualification-v1/registration.json` were sealed before
candidate inference. Registration SHA-256:
`39d7ecd167451314e840867735c695709764d14d7be7e54700b76dcd25e2481d`.
An initial tokenizer-only preflight needed an explicit `return_dict=False`
for the installed Transformers API; its failed evidence/partial files are
preserved under `checks/registration.*` and `preflight-attempt-1/`. No model
had run, and no data, scoring or budget changed. Earlier static-check failures
are also retained; passing final checks supersede those engineering attempts.

| Alias | Model | Pinned model/tokenizer revision | Weights SHA-256 |
|---|---|---|---|
| smollm | HuggingFaceTB/SmolLM2-135M-Instruct | `12fd25f77366fa6b3b4b768ec3050bf629380bac` | `5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c` |
| qwen | Qwen/Qwen2.5-0.5B-Instruct | `7ae557604adf67be50417f59c2c2f167def9a775` | `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe` |

Both are Apache-2.0 per the pinned
[SmolLM card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/blob/12fd25f77366fa6b3b4b768ec3050bf629380bac/README.md)
and [Qwen license](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/7ae557604adf67be50417f59c2c2f167def9a775/LICENSE).
SmolLM's existing successor files were read only. Qwen was copied from the
verified existing C-drive cache; `input-provenance.json` records both paths.
Registration binds every model/tokenizer/config file, source, tests, protocol,
dataset, dependency version and actual native-template prompt IDs. Weights are
safetensors; neither model is a Toruk-trained checkpoint.

New owned synthetic records use six task categories: binding, corrections,
preservation, exact quotations, clear references and missing information.
Development has 12 questions (seed 81711); untouched held-out has 30 (seed
81731), five per category, including 25 known and five unknown cases. IDs,
known expected values and normalized question templates do not overlap between
these splits or the old 24-case set. Templates/answer pools differ by split.
The old JSON is read only by the offline overlap check, never generation.
Generic instruction/header sharing is disclosed. No training or model-generated
data. This does not prove semantic or pretraining independence.

Both candidates receive byte-identical role/content messages: one explicit
common system instruction plus one full reference/question user message.
Native chat wrappers differ. Tokenizer-only checks preserved the entire source;
SmolLM prompts span 105-136 tokens and Qwen 94-123, all below 512. No selector,
compression, omitted evidence, persistent memory or hidden fallback.
Greedy decoding, seed 81751, 64 output tokens, temperature request 0, top-p 1,
one beam, repetition penalty 1 and KV cache. Common generation configuration
replaces model-specific sampling defaults; native EOS/pad remain appropriate.

The new budget is **6 GiB worker-tree private memory, 3 GiB study/input disk,
300 s per candidate/split, 30 s per request and 900 summed evaluation seconds**.
This is explicitly a different qualification budget; the successor's 3 GiB
limit is unchanged. A 50 ms process-tree watchdog includes Windows venv
launchers/descendants; OS worker lifetime memory peaks are checked too.
Development runs both once plus a first-case exact replay, then freezes outputs.
Held-out runs both once in reverse order. No development quality filtering or
post-result tuning. Gate: all 30 complete within caps, at least 18/30 overall
AND 15/25 known. Lowest held-out CPU selects among fixed-gate qualifiers.

## Frozen results and full measured work

| Measure | SmolLM | Qwen |
|---|---:|---:|
| Development correct | 3/12 | 11/12 |
| Held-out correct | 15/30 (50%) | 18/30 (60%) |
| Known facts | 15/25 (60%) | 15/25 (60%) |
| Binding | 3/5 | 5/5 |
| Correction | 5/5 | 4/5 |
| Preservation | 2/5 | 1/5 |
| Exact copying | 0/5 | 0/5 |
| Clear reference | 5/5 | 5/5 |
| Correct missing-information abstentions | 0/5 | 3/5 |
| All explicit abstentions | 0 | 4 (one unnecessary) |
| Manually reviewed false-assertion rows | 11 | 6 |
| Held-out prompt / generated tokens | 3,810 / 752 | 3,427 / 128 |
| Held-out prompt + generated tokens | 4,562 | 3,555 |
| Mean / median / maximum request seconds | 1.377 / 1.321 / 2.210 | 1.407 / 1.275 / 2.421 |
| Online request CPU seconds | 83.109 | 84.594 |
| Complete held-out wall / CPU seconds | 49.380 / 102.531 | 52.017 / 109.219 |
| Sampled held-out worker-tree RSS / private GiB | 0.875 / 1.320 | 2.273 / 3.784 |
| OS worker lifetime private peak GiB | 1.322 | 3.793 |
| Both development + held-out wall / CPU seconds | 75.713 / 153.406 | 78.771 / 162.953 |
| Registered gate | FAIL | PASS |

CPU includes controller integrity verification, worker startup/hash checks,
loading, tokenization, prompt fit, generation, scoring and monitoring, plus
sampled launcher CPU. Request timing is the backend reply call, not just decoder
forward time. Raw worker memory and setup times are in `execution-audit.json`.
The largest development worker OS private peak is 3.830 GiB. The cap concerns
worker trees, not whole-PC RAM or the small controller. Sampling has 50 ms
resolution; final worker CPU/lifetime peaks reduce missed-exit/peak effects.
No accelerator FLOPs, energy or selector-comparison speedup is claimed.

Across both candidates and both splits (including charged development replays):
154.484 wall seconds, 316.359 CPU seconds, 10,320 prompt tokens and 1,262
output tokens. Study plus both model inputs occupied 1,272,007,582 bytes
before general engineering verification. All caps passed. Environment setup,
registration, documentation, general tests and the separate integration smoke
are outside timed evaluation; their commands/durations are retained separately.
Selector work and persistent memory are zero. Qwen's lower token count does
not make it cheaper: its measured CPU and peak memory are higher.

`results.json`, four `*-answers.jsonl` files and `*-cost.json`/`*-worker.json`
retain raw answers, exact messages, input/output token IDs, per-case frozen
scores, effective generation settings, selected IDs and costs. `source.zip`
is the sealed as-run source/data; `execution-audit.json` independently checks
input parity, complete evidence, score/token sums, replay and resource caps.
`qualified-backbone.json` freezes Qwen's selected identity and settings.

## Raw failures and scoring limits

All new questions retain their complete evidence, so failures are downstream
of selection. Qwen's 12 failures are six wrong field values (four flavors and
two unsupported access phrases answered SOFT), five literal mutations (for
example `QH[AHISIXC] 8z` instead of `QH[AHISIXC]  | 8z`), and one unnecessary
UNKNOWN despite a corrected Monday. Its three valid UNKNOWN answers are credited.
These are generator failures, not evidence omissions or false abstention rejections.

SmolLM's 15 frozen failures include nine wrong requested values, five accurate
quotations wrapped in extra prose (whole-answer exact-copy failure), and one
truthful copying of both source bindings rejected by the conservative
competing-value rule. Two credited flavor answers additionally repeat an obsolete
file class SOFT. Thus the separate review finds 11 false-assertion rows,
including those two frozen-scored successes. The primary wrong-listed-value
proxy (2 vs 0) and missing-response proxy (5 vs 2) are not exhaustive semantic
false-assertion metrics. `heldout-review.json` retains each interpretation;
primary scores and gate outcomes are not edited.

The gate is an empirical floor on this fixed small set, passed without margin.
It is not a confidence bound or proof of general conversation quality. There
is no registered per-category floor; exact copying/preservation remain poor.
Development and held-out use different templates, explaining why strong Qwen
development performance does not establish robust held-out behavior.

## Files and verification

New runner `scripts/qualify_answer_backbone.py`, nine contract tests in
`tests/test_backbone_qualification.py`, versioned config, protocol/results and
this evidence directory. Shared README, architecture, experiment registry,
reproducibility guide, ignore and attributes files receive append-only notes;
existing successor and IDE files are preserved. Production model source and
chat defaults are unchanged. Full command evidence lives in `checks/` and
`verification/`; see `commands.md` for Windows reproduction.

`scripts/verify.py` completed all 26 stages: 25 PASS, Python tests FAIL
(288 passed, one existing HTTP-contract failure). It returned 1; this is retained,
not described as a clean script pass. The failing fixture expected six browser
requests but observed one; a connection-reset trace was recorded. The same test
passed alone in 2.87 s without source changes. A fresh full-suite confirmation
passed **289/289 in 135.81 s** (137.13 s wrapper), with no source changes.
The initial failure and successful confirmation are both retained in
`verification-summary.json`; the initial script return code remains 1. No candidate generation was repeated.

Other local checks passed: Node syntax and 20 tests (one standalone live test
skipped, separately exercised by Python/integration), Ruff lint and formatting,
Windows/Linux Mypy, frozen-source identity, package dependency/import/CLI checks,
data validation, bounded existing owned-LM train/resume/ablation smoke, ordinary
and research CLI pipelines, wheel/sdist build, unstaged and staged diff checks.
Those small existing training fixtures are engineering verification, not candidate
training or evidence for this quality result. An explicit Mypy command covering
the new runner and existing package passed (36 files); the new nine contracts
cover leakage, identical generator input projection, deterministic case creation,
scoring/abstentions/exact text, dual quality gates, replay charging, descendant
resource accounting and identity drift/overwrite prevention.

The real local Qwen page/proxy/server smoke passed, including status identity,
BASELINE response and outage handling. It uses an existing non-successor fixture
and production default instructions, so it adds no primary benchmark score.
No interactive browser was exercised. General verification source/check identities
and durations are retained in each wrapper JSON and raw log.

Observed hosted CI: [CPU foundation run 42465162288](https://github.com/ShamGaneshan2008/Toruk/actions/runs/42465162288)
succeeded for the starting commit only. Its Ubuntu Python 3.12 and Node 22 jobs
cover static/unit/HTTP-contract/CLI/smoke/build checks; Windows covers the bounded
owned-LM reproduction in a path with spaces. It does not download/run these
qualification backbones. No hosted run covers these uncommitted changes.

## One next step

Register a new matched long-history experiment using the frozen Qwen identity,
common instructions/decoding, identical fresh questions and a plain-full-evidence
oracle arm alongside recent-context, transparent lexical retrieval and the
separately identified successor selector. Use new development/training/held-out
records and templates, no old or qualification held-out reuse, and freeze numerical
quality/regression and total CPU/memory limits before selector work. Include exact
copying, preservation, corrections, distant facts, distractors, vague references,
unknowns and refusal carryover; charge indexing/selection and setup as well as
backbone generation. Reject an advantage claim if oracle quality or joint
accuracy/cost gates fail. This comparison was not run in this milestone.
The immediate blocker is generalization beyond short synthetic references,
particularly the 0/5 exact-copy and 1/5 preservation strata.
