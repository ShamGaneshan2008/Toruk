# Value-start supervision development v1: results

23 November 2026. Registered decision: **STOP_DEVELOPMENT_FAILURE**. Measurement integrity: **PASS** for the new sealed execution. All four weighted models mastered training, but two seed-601 development cells regressed against their matched uniform controls and the ordinary seed-601 city floor failed. Reliable generalizable improvement and readiness for another memory architecture study were not established.

An instruction-scope exception occurred before freezing: a native-shell quoted search broadened beyond its intended source file to repository-wide text. Which unrelated artifacts it scanned cannot be certified. The objective, data, seeds and gates were already drafted; no findings from that search were used to change them. No held-out evaluation ran and no held-out data were experimental inputs. This is **not** a claim of zero held-out or unrelated artifact search access. See [incident record](../../artifacts/local-answer-value-start-dev-v1/search-scope-incident.json).

## Git and preservation

Git root was verified as D:/Toruk. Starting branch main, HEAD 7cdded09b0255dd20379b96cd67e83d05ab65f8a, clean working tree, ahead 2 of origin/main. The requested v2 harness was already committed at that HEAD; there were no uncommitted harness edits to preserve or repair. Ending branch/HEAD are unchanged. Ending origin/main matches HEAD (0 ahead, 0 behind); its reflog records 'update by push'. This task issued neither fetch nor push; the actor behind the reference update is unknown.

New study work remains uncommitted: this report, protocol, scripts/value_start_dev.py, tests/test_value_start_dev.py and artifacts/local-answer-value-start-dev-v1/. No staged changes or tracked-file modifications. Eight new checkpoints are ignored and local; they will not transfer through Git. The [review inventory](../../artifacts/local-answer-value-start-dev-v1/review-inventory.json) binds new payloads by bytes/SHA-256, including these weights; caches and disposable negative-fixture trees are retained locally but explicitly excluded from that inventory. The inventory excludes itself and the final QA/anchor files to avoid a circular hash. No production-chat changes, deployment or historical result rewrites.

The independent audit rehashed 737 protected existing files, including all **337** original paired-batch inventory entries and 65 enumerated ignored checkpoints. All remained byte-identical, including the completed checkpoint handoff. Enumeration could not inspect inaccessible historical test-cache directories, so the checkpoint inventory is not an exhaustive claim about those caches. See [starting state](../../artifacts/local-answer-value-start-dev-v1/starting-state.json), [ending state](../../artifacts/local-answer-value-start-dev-v1/ending-state.json) and [preservation baseline](../../artifacts/local-answer-value-start-dev-v1/preservation-before.json).

## Measurement readiness and saved diagnosis

All 24 disposable-process tests passed: normal exit, descendants, workload failure, timeout, interruption, late writes, incomplete publication and post-seal mutation. watch_and_seal calls watch synchronously; watch drains the Job tree, closes streams/monitor output and writes final cost receipts before returning. Only then does v2 snapshot and publish observer seals. No path was identified that permits a valid PASS seal while monitoring is unfinished. STOP workloads retain their STOP receipts; failed publication leaves partial records that verification rejects. External post-seal mutation is detected by verification rather than physically prevented. No v2 edits were required.

Original paired-batch-v1 registered integrity remains **FAIL**: its monitor logs grew after worker seals. Those seals and its failure report were not modified. Independent saved-evidence checks do not retroactively turn it into PASS.

Saved logits, raw predictions, exact expanded schedules and all 12 old checkpoint identities were inspected without model construction, new forwards or generation. Checkpoints had finite tensors and 1536-step optimizer progress; arms shared initialization within each seed/model. Ordinary seed947 had 80/96 original, 92/96 city-shuffled and 90/96 paired. Both city schedules corrected all 16 original errors, but introduced four and six previously correct t-byte errors respectively. Their saved failures were losing token preferences rather than near ties or EOS failures. Other model/seed cells were96/96. Matching exposure and checkpoint identity rule out a stale/wrong checkpoint explanation; they do not identify why optimization selected a competing byte. Initialization and shuffle effects across seeds remain confounded. The first-token probe established checkpoint preferences, not a training cause.

## Frozen intervention and decision gates

Hypothesis: upweighting the first answer byte after '?=' improves answer-value discrimination under the strongest archived city-shuffled schedule, while preserving suffix/EOS behavior and fresh-combination accuracy. Uniform CE is the control; first16 changes only that token's weight from1 to16, normalized by weighted token mass. It uses the same logits and adds no model forward.

-  Seeds601/947, ordinary CausalLM (14,058 parameters) and recurrent OwnedMemoryLM (14,416), eight fresh fits. Across architectures parameters differ by about2.55%; no equal-FLOPs/time claim. Within model/seed, both objectives share initial weights, data, optimizer, updates and dense token work.
-  Exact96 training documents (32 city,32 code,32 unknown);24 development cases (8/category), disjoint entity/value combinations with shared syntax/vocabulary. This small development set is not an independent final evaluation.
-  Each fit:1536 updates, batch8,128 exposures/document,12,288 presentations,692,224 valid targets,786,432 padded positions. Candidate weighted target mass876,544. CPUfloat32, one Torch thread, deterministic, AdamW lr.003, betas(.9,.999), eps1e-8, decay.01, clip1; no resumption, seed selection or retry.
-  Original Toruk byte tokenizer259 IDs; native greedy OwnedSession budget8, PAD/BOS suppressed, EOS2. Answers were supplied only by the custom trained weights. No Qwen, SmolLM, pretrained/API provider, retrieval answer or parser/rule answer.
-  Candidate training mastery: each of four cells96/96 full exact andEOS, zero first-byte errors, malformed values or repetition. Controls' mastery is also96; their separately declared development eligibility floor is>=90/96,EOS96, zero malformed/repetition, inherited from the original local-answer protocol. Thus control92 is eligible but **not mastered**. Global eligibility requires all candidate mastery and all control floors; otherwise both arms' development must be NOT_RUN.
-  Training improvement also requires positive ordinary947 exact gain and no candidate training regression.
-  Each candidate development cell: exact>=22/24, city>=7/8, code>=7/8, unknown8/8, EOS24/24, zero malformed/repetition, and >=8 known-answer gain over equal-width assignment-masked question-only neural outputs. Robust improvement additionally requires no per-cell exact/EOS regression versus uniform and positive aggregate known-fact gain.
-  All training/development/source-dependence and integrity/resource gates must pass before another separately registered memory study is justified. No memory/efficiency advantage follows from training accuracy.

Design and cap-sizing rule were frozen before the disposable rehearsal. Final common fit caps70 CPU and wall seconds were registered before any fit; evaluation/development30 seconds each, request2, complete study1500 CPU and wall seconds,2GiB Job commit,128MiB generated scientific output and max monitor gap5 seconds. The single attempt marker was consumed once; no gates or caps changed.

Plan SHA-256: 2c64a590523d4717bdd24b9d5ade925f1657bbccf6c160e097b050e8396b5e66.

Registration SHA-256: 80a531c9de8bf1eb5651c39bf28520e11cd798d82d2d4353a11858cfabd72a16.

Source commit: 7cdded09b0255dd20379b96cd67e83d05ab65f8a plus the frozen, hashed uncommitted study source snapshots. [Protocol](local-answer-value-start-dev-v1-protocol.md), [plan](../../artifacts/local-answer-value-start-dev-v1/plan.json), [registration](../../artifacts/local-answer-value-start-dev-v1/registration.json) bind exact datasets, schedules, code, tokenizer, decoding, scorer, order, hyperparameters and gates.

## Per-cell outcomes

Full exact includes the entire native value followed by EOS. Value-only correctness is a separate diagnostic; it equals full exact in every observed cell. EOS was96/96 for every training cell and24/24 for every development cell. Malformed and repetition counts were zero throughout. Every incorrect answer had a wrong first byte.

| Seed | Model | Objective | Train exact /96 | Train wrong first | Dev exact /24 | Dev wrong first | Dev city/code/unknown /8 | Known context gain |
|---|---|---|---:|---:|---:|---:|---|---:|
| 601 | ordinary | uniform | 96 | 0 | 23 | 1 | 7/8/8 | 13 |
| 601 | ordinary | first16 | 96 | 0 | 22 | 2 | 6/8/8 | 12 |
| 601 | recurrent | uniform | 96 | 0 | 24 | 0 | 8/8/8 | 15 |
| 601 | recurrent | first16 | 96 | 0 | 23 | 1 | 7/8/8 | 15 |
| 947 | ordinary | uniform | 92 | 4 | 16 | 8 | 1/7/8 | 8 |
| 947 | ordinary | first16 | 96 | 0 | 23 | 1 | 7/8/8 | 15 |
| 947 | recurrent | uniform | 96 | 0 | 22 | 2 | 7/7/8 | 14 |
| 947 | recurrent | first16 | 96 | 0 | 24 | 0 | 8/8/8 | 15 |

Training eligibility passed: all candidate cells96/96; ordinary947 improved92->96 while other cells stayed96. All controls met the prospectively registered90 floor, so development ran once for all eight checkpoints. Question-only inputs were generated once as registered source-dependence diagnostics; no outputs were used to tune.

Across four evaluations of the same24 development cases, uniform totalled85/96 and first16 92/96 (+7: city+5,code+2). These are repeated model/case observations, not96 independent development examples. Both601 cells lost one exact answer. Ordinary601 city6/8 failed its>=7 floor despite total22/24. Therefore candidate development floors=false, no-regression=false, generalizable_improvement=false, memory_study_justified=false. The registered decision is STOP_DEVELOPMENT_FAILURE; no held-out evaluation followed.

## Candidate wrong-first examples

| Seed/model | Case | Gold | Generated body | Gold rank | Gold minus top logit |
|---|---|---|---|---:|---:|
| 601 ordinary | dev-007 | la | ? | 3 | -2.053555489 |
| 601 ordinary | dev-013 | mi | so | 2 | -1.348668098 |
| 601 recurrent | dev-013 | mi | tu | 13 | -7.409210443 |
| 947 ordinary | dev-019 | so | la | 2 | -0.002157211 |

dev-013 contains city zim=mi followed by city zim?=: ordinary601 chose so and recurrent601 chose tu. These are new regressions from correct uniform answers. Ordinary601 dev-007 pex=la returned '?' (a wrong abstention in the allowed vocabulary), shared with its uniform control. Ordinary947 dev-019 nax=so returned la with a small but non-tied margin. No candidate recurrent947 errors. Full prefixes, native IDs, all259 logits, teacher NLLs and replay/parity checks are retained. The remaining failure class is value selection at the first byte, with correct termination; this observation still does not establish the optimization mechanism.

## Costs and stop accounting

Seconds below are complete kernel Job workloads and descendants, including controller/inner monitoring where enclosed. Nested receipts are not added twice.

| Non-overlapping scope | CPU s | Wall s |
|---|---:|---:|
| phase1-tests | 2.687500 | 6.827604 |
| diagnosis-execution | 2.156250 | 2.517944 |
| diagnosis-supplement-execution | 0.296875 | 0.412788 |
| preparation/budget | 8.843750 | 9.961709 |
| registered/budget | 232.125000 | 219.455505 |
| independent-audit-execution | 0.968750 | 1.020448 |
| verification/execution | 1.765625 | 2.843533 |
| Measured scope sum | 248.843750 | 243.039529 |

Preparation already includes the rehearsal (3.203125 CPU,4.085892 wall seconds) and8 numerical/data/gate tests. Rehearsal used different random cases/seed900503, three forward/backward iterations per model/objective, zero optimizer updates, unchanged weights and empty optimizer state; excluded from the scientific comparison. Its prespecified bound rounded to70 seconds before fitting.

Registered-budget cost232.125 CPU/219.455505 wall seconds includes all8 fits,8 training observations,8 development/question-only observations and enclosed observation/sealing work. Peak Job commit725,405,696 bytes (~691.8MiB), peak scientific output17,389,792 bytes, maximum monitoring gap0.115750s;78 process lifetimes,0 active,0 forcibly terminated. Every stage stayed under its frozen caps.

| Seed/model/objective | Fit CPU/wall s | Train observation CPU/wall s | Dev + question-only CPU/wall s |
|---|---:|---:|---:|
| 601/ordinary/uniform | 14.203125/14.909684 | 3.625000/4.247217 | 3.562500/4.204763 |
| 601/ordinary/first16 | 14.296875/14.907817 | 3.718750/4.343736 | 3.453125/4.084317 |
| 601/recurrent/uniform | 20.578125/21.377061 | 4.156250/4.737059 | 3.484375/4.156258 |
| 601/recurrent/first16 | 20.828125/21.476598 | 4.109375/4.705584 | 3.640625/4.319133 |
| 947/ordinary/uniform | 14.359375/14.880901 | 3.703125/4.350902 | 3.328125/4.061137 |
| 947/ordinary/first16 | 14.656250/15.293444 | 3.750000/4.316385 | 3.218750/4.065986 |
| 947/recurrent/uniform | 20.437500/21.172717 | 3.953125/4.709069 | 3.578125/4.244907 |
| 947/recurrent/first16 | 21.109375/21.703621 | 4.078125/4.753234 | 3.734375/4.233966 |

All scientific attempts completed; no fit failed or was silently retried. Preserved pre-fit failures include initial typing/lint corrections and a diagnostic directory/root guard rejection before worker creation; the corrected read-only diagnosis launched once. Initial editing/type-check/setup and rejected CLI costs were outside complete Jobs and are unmeasured. Negative disposable tests intentionally retain failed, interrupted and mutated records. All scientific checkpoints, raw predictions, traces, request receipts, costs and stop decisions are retained.

The measured sum excludes outermost observers' full lifetimes and editing/reporting work outside Jobs. The registered outer observer reports16.03125 CPU seconds only up to its receipt, not its complete lifetime. Named Job totals are complete for those scopes; complete project-wide cost is unavailable. No efficiency claim is made.

## Independent audit and local validation

[Saved-only independent verifier](../../artifacts/local-answer-value-start-dev-v1/verify_saved.py) reconstructs scoring and gates from raw IDs/logits, without torch, new forwards, training or generation. It verified24 scientific stage seals plus execution/budget/prerequisite seals,8 checkpoint byte hashes,12,288 schedule/optimizer steps, exposure/target accounting, first-vector argmax/ranks/margins/replays, exact value/EOS/error counts, masked-input source dependence, stop decisions and raw monitor/final receipt consistency. It rescored768 training,192 development and192 question-only case outputs (replay observations additionally retained). All receipts showed complete lifetimes and0 active descendants. Quality failure is separate from new measurement-integrity PASS.

Trusted root execution observer-seal SHA-256:44e89742b87280e7798b08feae6c6e0ec8b3c418dc14782ef2f3d45509f42949. Registered budget seal:05ff8950e0ba0403481d7127ffda11f2b9eb736b2cba53856c51e730905961cf. [Audit](../../artifacts/local-answer-value-start-dev-v1/independent-audit.json) records all cells, costs, preservation checks and the scope exception. Reports/audits are outside sealed scientific directories.

Repeat offline verification from D:/Toruk with the existing Python runtime (no packages, training or answers needed):

~~~powershell
python -I -S -B artifacts/local-answer-value-start-dev-v1/verify_saved.py
~~~

Local checks passed:

- 24 disposable process tests: python -B -m pytest -q -p no:cacheprovider tests/test_lifetime_job_v2.py tests/test_lifetime_job.py (6.25s pytest time).
- 8 new numerical/data/gate tests: python -B -m pytest -q -p no:cacheprovider tests/test_value_start_dev.py (4.10s pytest time); zero research optimizer updates.
- python -B -m ruff check --no-cache .
- python -B -m ruff format --check --no-cache src tests scripts
- With MYPYPATH=D:/Toruk/src: python -B -m mypy --follow-imports=silent --cache-dir artifacts/local-answer-value-start-dev-v1/preflight-mypy scripts/value_start_dev.py
- python -B scripts/check_frozen_sources.py; python -B -m pip check
- git diff --check; git diff --cached --check (also manual whitespace validation of new untracked text).

Hosted CI: **NOT_RUN**, work remains uncommitted/unpushed. Complete verify.py: NOT_RUN because it installs/trains/generates unrelated outputs. The older portable verifier was not repaired or claimed to pass; its historical .gitattributes dependency drift is separate from this study's frozen source/independent integrity checks. Windows Job-based accounting is host-specific; this is a small synthetic development study, not broad factual-chat validation.

## One recommended next research step

Preregister a crossed initialization-seed/shuffle-seed replication of these frozen uniform versus first16 objectives on the strong schedule and fresh development combinations. This separates the currently confounded seed effects and tests whether the observed gains survive seed changes before revisiting memory architecture. Do not tune on these24 cases.
