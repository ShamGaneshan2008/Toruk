# Toruk-owned next-token LM v1: bounded synthetic result

4 November 2026. **Engineering identity passes; the declared quality/efficiency
criterion fails. This model is not ready for conversational use.** The model
trains from scratch and its recurrent tensors directly affect next-token logits;
no pretrained chat backbone or text selector participates in this path. It reuses
the existing recurrent core, so this is an implementation/evaluation milestone,
not a new memory algorithm. See the [design fixed before coding](owned-lm-v1-design.md).

## Repository and prerequisite evidence

Starting HEAD: `84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca`, with previous milestone
changes already dirty. Exact initial status is retained in
`artifacts/owned-lm-v1-20261104/start.json`. During this session external commits
`f2171b9e3deca4966633bc1025a44cebb29a0951` and
`3fcf787470d64d445d621cdd5f76bd491c53b476` appeared. These were preserved; this
agent did not commit. The primary registration records the latter HEAD plus exact
runtime, driver, configuration, design and dataset identities. A commit alone
does not identify the dirty implementation.

Verified existing paths: ordinary CausalLM; recurrent research LM; integrated and
pooled-router conditional research models; trained chat selector; separate local
Qwen instruct chat backbone; controlled long-gap QA; and independent chat
replication. Earlier negative findings are not treated as successful research.

The original routing replay and value-fidelity audit initially failed their
strict `pyproject.toml` binding. Expected SHA256:
`73f3439c08e19baae10b4f8794a7140e0cc2e2eccedbb6b2f40f29923dcb4b61`;
current `4227d013fcbb64d3c520c6fb2419fba628e4b02f17a46859110cdb7294a8acb1`.
All other registered runtime/data/checkpoint inputs matched. The new
`replay_owned_prerequisites.py` uses the exact archived metadata **only in an
isolated copied workspace** and refuses any other source mismatch. Original
files, checkpoints and seals remain intact. It reproduced 2,304 routing answers
and 1,920 value-fidelity answers, zero deterministic mismatches, no fitting.
The old quality gates still fail. Complete provenance, commands and original
failed checks are retained in `prerequisite-replay/replay.json` and `checks/`.

The latest chat comparison was also rerun: 144 independent plus 72 controlled
answers, including all three ablations. All 216 match the old selected sources,
prompt/generated IDs, answers, correctness and token work exactly; only measured
time/memory are excluded from deterministic equality. Controlled recent/lexical/
Toruk remain 0/12, 4/12, 8/12; independent remain 3/24, 6/24, 9/24. The previous
independent quality/total-cost gate remains failed. Fresh inference commands took
519.07 s and 282.85 s; the 216-row audit passed. This prerequisite evidence was
restored before starting the new architectural comparison.

## Implemented model and protocol

`owned_lm.py` reuses `RecurrentLM`: fixed byte/special vocabulary 259, learned
token/segment-position embeddings, two pre-norm causal transformer layers,
width 32/four heads, 32 local positions, untied output. Four 32-float slots
cross-attend into each decoder layer. After segment logits, mean hidden state
and old slots feed shared tanh proposal/sigmoid gates plus slot offsets. From
zero initialization, recurrent values stay within [-1,1]. State is 512 tensor
bytes; local tokens are bounded by 32. Read and update removals correspond to
real code operations. There is no symbolic retrieval or protected correction.

All byte/EOS next-token targets are trained, including cross-segment boundary
targets, without answer-span/address supervision. Full-document BPTT spans at
most 384 targets. Each document/question creates fresh zero state; no evaluation
case inherits another case's answers. Atomic optimizer-boundary checkpoints save
model, AdamW, RNG, deterministic document cursor, config, tokenizer, dataset and
runtime identities under `toruk-owned-next-token-v1`. Resume rejects changed
settings/data/runtime. Old and new checkpoint types reject one another. The
experimental CLI explicitly reports its model identity and lack of conversational
qualification. Existing chat/browser paths and their weights remain unchanged.

The three splits contain 192/24/48 documents, generated from seeds 3201/4201/5201.
Their canonical JSON SHA256 values are:

| Split | SHA256 | Unique document targets |
|---|---|---:|
| Train | `1b4904b9675af60549e27ad91f03fdaa05c88201d0e9281107863903938cf54d` | 29,222 |
| Development | `6e2e05d75e3a19c0595ba1032f745ab7c6161b90c39f24fec0715468194c498b` | 3,796 |
| Held-out | `219cf601e3d4767222757fa315239802a5baccb0fc9dbd1a1e3842077bee3032` | 7,289 |

The six balanced categories are distant fact, correction, preservation amid a
distractor, punctuation-sensitive exact string, local fact and insufficient
evidence (`?`). Each distant case separates the queried evidence from the answer
by more than one local window. IDs and complete texts are disjoint across splits;
grammar, names and value inventory are shared. This is synthetic IID testing,
not independent-source or unseen-entity generalization. Gold labels enter training
text naturally but never the generation input. Unit tests change evaluation gold
while proving identical generated tokens. Development precedes checkpoint freeze;
each primary held-out condition is scored once, without quality-driven retries.
The execution smoke shares the generator and some examples with the primary
study; it is not an independent blind quality evaluation. It triggered no
quality-driven model, threshold or criterion changes. Its later checkpoint
validation hardening changed no model algebra or scoring rule.

All four fits per seed use the same ordered documents, target counts, 256 AdamW
steps, batch of two complete documents, learning rate .003, float32, deterministic
algorithms and one CPU thread. Seeds 31/47 consume 78,190/78,000 targets per fit.
The 56,620-parameter ordinary width-38/two-head control is within 1% of the
56,064-parameter recurrent model. The width-32 ordinary core has 43,072 parameters;
memory-off allocates 56,064 but only the same 43,072 core parameters receive
gradients. Thus allocation and effective compute are reported separately.
This is matched-token training with an additional parameter control, not a
matched-total-compute advantage claim.

The predeclared criterion requires, at **both seeds**, memory-on NLL at least
.05 nats below ordinary, memory-off and parameter-matched ordinary; distant plus
correction exact accuracy at least 10 percentage points higher; no correction/
preservation regression or increase in unsupported unknown answers. Removing
read or update must each worsen NLL by .01 averaged over seeds. Every condition
is required. The registration hashes the design containing these thresholds.

## Held-out answers and loss

Each row pools the same 48 questions evaluated at two training seeds (96 model
answers, not 96 independent questions). NLL is nonoverlapping-window byte/EOS
teacher-forced loss; its corresponding perplexity is byte-based, not word-based.
Greedy generation has 16-token cap, EOS stopping, PAD/BOS suppression; scoring
uses exact equality after stripping outer whitespace. No substring credit.

| Condition | Params allocated / active | NLL seed 31 / 47 | Byte PPL 31 / 47 | Exact | Distant | Correction | Preservation | Exact strings | Local | Unknown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A ordinary | 43,072 / 43,072 | .5318 / .5300 | 1.7019 / 1.6989 | 14/96 | 3/16 | 2/16 | 3/16 | 0/16 | 2/16 | 4/16 |
| B memory off | 56,064 / 43,072 | .5318 / .5300 | 1.7019 / 1.6989 | 14/96 | 3/16 | 2/16 | 3/16 | 0/16 | 2/16 | 4/16 |
| C memory on | 56,064 / 56,064 | .5198 / .5220 | 1.6817 / 1.6853 | 17/96 | 4/16 | 3/16 | 4/16 | 0/16 | 2/16 | 4/16 |
| Parameter-matched ordinary | 56,620 / 56,620 | .4973 / .4998 | 1.6442 / 1.6484 | 15/96 | 4/16 | 1/16 | 1/16 | 0/16 | 4/16 | 5/16 |
| C without read | same C checkpoint | .5618 / .5595 | 1.7539 / 1.7498 | 11/96 | 3/16 | 3/16 | 2/16 | 0/16 | 2/16 | 1/16 |
| C without update | same C checkpoint | .5635 / .5614 | 1.7568 / 1.7532 | 12/96 | 3/16 | 3/16 | 2/16 | 0/16 | 3/16 | 1/16 |

A/B match exactly. C reduces NLL versus A/B by only .01192/.00802, short of .05,
and has worse NLL than parameter-matched ordinary by .02256/.02218. C's 31-seed
distant+correction score equals A/B (4/16); its 47-seed 3/16 exceeds A/B 1/16 but
does not exceed matched ordinary 4/16. C makes 8/8 unsupported unknown assertions
at seed 31 versus matched ordinary 5/8, a regression. Read/update removals worsen
mean NLL by .03979/.04158 and pass their mechanistic thresholds. **Overall FAIL.**

The existing ordinary rolling-context generator is also run unchanged: ordinary
4/96 exact, parameter-matched ordinary 0/96. This exposes the generation-window
distribution shift: training uses position-reset segments, whereas rolling
generation restarts its positions for every recent window. The stronger context
availability does not guarantee stronger performance here. The rolling rows'
recorded NLL still uses the common segment loss, not rolling teacher-forced loss.
No comparison hides the segment-runtime choice or treats rolling's low accuracy
as proof of a recurrent advantage.

## Failures, costs and interpretation

| Condition | Wrong nonempty outputs | Unsupported unknown /16 | Stale corrections /16 | Budget cap reached /96 | Empty / invalid UTF8 |
|---|---:|---:|---:|---:|---:|
| A / B | 82 | 12 | 1 | 7 | 0 / 0 |
| C | 79 | 12 | 1 | 8 | 0 / 0 |
| Matched ordinary | 81 | 11 | 2 | 15 | 0 / 0 |
| C no read | 85 | 15 | 1 | 38 | 0 / 0 |
| C no update | 84 | 15 | 1 | 39 | 0 / 0 |

Wrong nonempty strings include malformed continuations; they are not all
interpretable factual assertions. The unsupported column measures explicit
nonempty responses on questions with no evidence, excluding `?`. This is a
bounded synthetic proxy, not a human-annotated natural-language hallucination rate.
Examples from seed 31 (all 79 C failures saved in `primary/failed-cases.json`):

| Case | Expected | Generated | Failure |
|---|---|---|---|
| distant-2 | `blue` | `gold\n` | Wrong distant value |
| correction-1 | `gold` | `tag? gold\n` | Continuation includes an extra prefix |
| exact-0 | `z+3=Q` | `reed\n` | Exact string lost |
| unknown-0 | `?` | `ld\n` | Unsupported malformed answer |

Windows 11, Python 3.12.14, Torch 2.14.1+cpu, one thread, no GPU/API billing.
Times are observed locally, not portable estimates. Generation includes history
prefill, repeated uncached local forwarding and memory operations. The same
14,148 prompt byte/special tokens feed each two-seed condition. No selector or
separate memory model is called. Tensor state excludes framework/weights/graphs.

| Condition | Train targets | Train wall / CPU s | Held-out generation s | NLL scoring s | Generation positions | Generated tokens | State bytes | Process peak bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 156,190 | 12.935 / 12.875 | .790 | .372 | 23,762 | 650 | 0 | 306,688,000 |
| B | 156,190 | 12.679 / 12.672 | .910 | .416 | 23,762 | 650 | 512 inactive | 306,823,168 |
| C | 156,190 | 23.102 / 23.094 | 1.667 | .799 | 23,453 | 643 | 512 | 307,306,496 |
| Matched ordinary | 156,190 | 13.263 / 13.219 | .843 | .395 | 23,630 | 668 | 0 | 306,741,248 |
| C no read | reuses C | — | 1.406 | .474 | 29,375 | 983 | 512 | 307,625,984 |
| C no update | reuses C | — | 1.773 | .618 | 29,278 | 981 | 512 | 307,625,984 |

C training takes 1.79x A's time and 1.82x B's; generation takes 2.11x A's and
1.83x B's. The A-to-C held-out generation difference is .877 s over 96 answers,
about 9.14 ms per answer, including changed output lengths; it is not an isolated
kernel benchmark. C commits state 404 times across these answers. Partial
segments also compute provisional updates that are discarded until a complete
segment; measured latency includes this work. Removing reads still updates
memory; removing updates still pays read cost. Ablations are not claimed as
speed-only optimizations. Process peaks are cumulative OS high-water marks from
one study process, not isolated per-condition incremental allocations. The
whole observed process peak is 307,625,984 bytes (about 293.4 MiB).
On platforms without the Windows OS peak field, this helper records zero for
unavailable peak measurement; that sentinel must not be interpreted as zero RAM.

The primary study took **80.260 s wall / 79.750 s CPU**, covering all eight fits,
development, held-out conditions/ablations/rolling diagnostics, training-only
profile, checkpoint resume check and artifact work. Main training consumes
624,760 targets, plus 1,216 for the two-step profile and duplicate resume exercise
(625,976 total optimized targets in this registered study). Those profile/resume
costs are in the total, not charged repeatedly to each ablation. Development
evaluations have separate raw costs under `primary/dev`. Full prerequisite
commands and execution/testing smoke costs are additional, recorded separately
under `checks` and `verification`; they are not amortized away or included in the
80.260 s architectural study. No dollar savings, FLOPs or energy were measured.

There are only two training seeds and 48 shared questions. Repetitive prose
dominates next-token loss, so lower NLL does not imply evidence retention.
Very low exact recall, complete exact-string failure, lack of independent-source
testing, small data/model budgets, order effects in cumulative resource readings,
and segment/rolling distribution shift limit interpretation. The execution smoke
is an engineering check, not additional quality evidence. Mechanistic ablations
are inference interventions, not separately retrained ablation architectures.

## Reproduce locally or in CI

Run from repository root. Fresh output directories are mandatory. Checkpoints are
local ignored `.pt` files with SHA256s in `freeze.json`; rerunning bounded training
regenerates them. Exact numeric replay is supported on the recorded CPU runtime;
cross-version bitwise equality is not promised.

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$py = '.\.venv\Scripts\python.exe'
& $py scripts/replay_owned_prerequisites.py --output artifacts/owned-prerequisite-fresh
& $py scripts/independent_replication.py register --run artifacts/owned-chat-fresh --phase1 artifacts/independent-replication-20261104/phase1
& $py scripts/independent_replication.py evaluate --run artifacts/owned-chat-fresh --suite independent
& $py scripts/independent_replication.py evaluate --run artifacts/owned-chat-fresh --suite controlled
& $py scripts/independent_replication.py audit --run artifacts/owned-chat-fresh
& $py scripts/study_owned_lm.py --config configs/owned-lm-primary-v1.json --output artifacts/owned-primary-fresh
& $py scripts/audit_owned_lm.py --run artifacts/owned-primary-fresh --chat-reference artifacts/independent-replication-20261104/evaluation --chat-replay artifacts/owned-chat-fresh
& $py scripts/report_owned_lm.py --run artifacts/owned-primary-fresh
& $py -m toruk_lm.owned_lm generate --checkpoint artifacts/owned-primary-fresh/models/31-memory_on/checkpoint.pt --prompt 'Experimental only' --max-new-tokens 16
& $py scripts/verify.py --output-dir artifacts/owned-verification-fresh
npm.cmd --prefix web/vercel run check
npm.cmd --prefix web/vercel test
```

These are the same commands/configurations used here, with fresh directory names.
Exact executed argument arrays, source hashes, exit codes, timings and logs are
saved in `artifacts/owned-lm-v1-20261104/checks/*.json` and `verification/*.json`.
The new CLI `train` and `evaluate` were exercised on train/dev only, including
`--resume`, with their exact commands in `checks/owned-cli-*.json`. A two-step
smaller model was used for those interface checks, not the table above.

CI's CPU workflow now invokes `study_owned_lm.py --config configs/owned-lm-smoke-v1.json`
and an explicitly experimental generation command. This trains/resumes/scores
small CPU checkpoints, exercises actual read/update ablations, and requires no
backbone download. The local verification script invokes the same path. Hosted
GitHub Actions for these edits was **not observed**.

## Verification and remaining blocker

Files delivered in this milestone (including the prerequisite helper that an
external commit captured during this session):

- Runtime: `src/toruk_lm/owned_lm.py`, `owned_data.py`, `owned_training.py`.
- Experiments/audit: `scripts/replay_owned_prerequisites.py`, `study_owned_lm.py`,
  `audit_owned_lm.py`, `report_owned_lm.py`; two `configs/owned-lm-*-v1.json` files.
- Regression/CI: `tests/test_owned_lm.py`, `scripts/verify.py`,
  `.github/workflows/ci.yml`, `MANIFEST.in`, `.gitignore`.
- Documentation: this report, `owned-lm-v1-design.md`, `docs/architecture.md`,
  `docs/experiments.md`, `README.md`.
- Evidence: `artifacts/owned-lm-v1-20261104/`, with raw per-question results,
  checkpoints, registrations, freezes, manifests, command logs and status snapshots.

The historical decoder/recurrent/selector/chat source files were read but not
edited; the new full recurrent forward path delegates to the existing core.

Local verification results and complete retained evidence are listed in
`artifacts/owned-lm-v1-20261104/verification-results.md`. Initial historical
metadata failures were repaired as above. Initial Node wrapper invocations with
`npm` failed on Windows (`WinError 2`); explicit `npm.cmd` checks passed.
Development-only lint/type issues were corrected; one standalone script mypy
invocation initially lacked the package source path, then passed with
`mypy src/toruk_lm scripts/study_owned_lm.py scripts/audit_owned_lm.py scripts/report_owned_lm.py`.

Meaningful tests verify original recurrent algebra, causal masking, direct state
effects on logits, writer/read gradients through the next segment, bounded and
chunk-invariant state, explicit reset, independent document loss, each target
counted once, exact optimizer/RNG resume, incompatible/corrupted checkpoints,
parameter matching, split separation and generation's exclusion of gold answers.

Supported: **Toruk-owned experimental next-token LM**, complete bounded CPU path,
learned memory participating in token prediction. Unsupported: useful general
chatbot, reliable factual memory/revision/copying, lower total compute cost,
independent natural-data generalization or a research breakthrough. The single
highest-priority blocker is learning reliable distant evidence and exact copying
at a cost justified against the parameter-matched ordinary model. A future
development-only investigation needs fresh held-out data; this test set must not
be tuned against and reused as confirmatory evidence.
