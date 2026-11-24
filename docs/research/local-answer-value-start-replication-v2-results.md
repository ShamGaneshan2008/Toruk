# Value-start replication v2: crossed initialization and shuffle results

24 November 2026. Registered decision: **STOP_DEVELOPMENT_FAILURE**. Measurement integrity: **PASS**. This is an objective replication, not a memory study.

## Preservation and registered design

Git root D:/Toruk, branch main, HEAD 91f2e2b8e6b171c1b1f4fb27898f37f17b6b93ed; local origin/main matches (0/0). No commit, push or deployment. Value-start v1 is preserved in that reviewed commit, including STOP_DEVELOPMENT_FAILURE, its search-scope exception, raw outputs, independent audit and seals. The unchanged v1 verifier passed outside sandbox read restrictions:737 protected files,337 paired-batch files,65 old ignored checkpoints,24 scientific seals. Its388-entry review inventory additionally binds all eight v1 weights. Initial sandbox access errors produced324 apparent Git deletions; readable Git reports no actual tracked changes. No historical files or permissions were repaired.

[Precondition](../../artifacts/local-answer-value-start-replication-v2/precondition.json), [starting state](../../artifacts/local-answer-value-start-replication-v2/starting-state.json). The v1 scope incident remains disclosed; it cannot be recast as zero unrelated artifact access. V2 uses only named permitted development material; no held-out input or external model generated a research answer.

Initialization seeds 601/947 crossed with shuffle seeds 1301/1709, ordinary/recurrent, uniform/first16: 16 fresh fits,8 matched objective pairs. Initial hashes match within initialization/model across objectives AND shuffle seeds; schedules match within shuffle across initializations/models/objectives and differ across the two shuffle seeds.

New entities bek,dov,ral,sun are used in BOTH splits, because the old four entities' entity/value combinations were exhausted by earlier train+development. This is a procedural replication on a renamed task, not an identical-data reproduction. Train96 documents/24 canonical cores; dev24 fresh canonical combinations,8/category. Train uses two rotated values/entity; dev the other two, with shared answer vocabulary and both templates. Frozen overlap checks against original training/development and v1 development/known diagnostics found zero canonical overlap. This says nothing about uninspected held-out material.

Original byte tokenizer, context32, ordinary14058/recurrent14416 parameters; float32 deterministic CPU, one thread.1536 AdamW steps/fit, batch8, same optimizer and city-shuffled dense8x64 work. Each document128 presentations,692224 valid targets and786432 padded positions/fit. First16 weights only the first answer token16; all suffix/EOS targets stay1. Weighted mass876544; uniform692224. No extra model forward for weighting. Final checkpoints only, no retries/resume.

Greedy OwnedSession, cap8, PAD/BOS-only suppression, EOS2. Exact scorer requires unaltered native gold bytes followed by EOS; no trimming, insertion or repair. Value-body accuracy is a separate diagnostic. Every raw continuation, first-token vector, teacher loss, request cost, training trace and checkpoint is retained. New weights remain local/ignored and are not recoverable from Git metadata alone.

[Protocol](local-answer-value-start-replication-v2-protocol.md). Final plan SHA256: `d7a5ade0068dd2cf9aee39c972c35bc080d851c6490ab20caf6546ec79a63762`. Registration SHA256: `964d13a265a75a76b70b577873165b1a9347b720d57a5ce516bae453566e916d`.

The initial plan.json/source snapshots are preserved as a preflight draft. Typing annotations and metadata source bindings were corrected before the one rehearsal or any fit/answer; plan-final.json/sources-final bind the operative source. Data, seed matrix, schedules, objectives, gates and caps did not change. Draft lint/type failures and unmeasured editing cost are in draft-history.json. No sealed evidence was altered.

## Per-cell accuracy against frozen gates

Training eligibility requires ALL8 candidates exact96/EOS96/no first errors, malformed/repetition, plus ALL8 controls exact>=90/EOS96/zero malformed/repetition. Control mastery remains96 and is reported separately. If eligibility fails, both arms' development are NOT_RUN. Development candidate floors:>=22/24,city>=7,code>=7,unknown8,EOS24,zero malformed/repetition,known context gain>=8. Reliable improvement also requires STRICTLY positive exact gain in EACH8 matched pairs and no category/EOS regression. Aggregate gains cannot rescue a tie/regression.

| Init | Shuffle | Model | Objective | Train /96 | Train city/code/unknown | Train EOS/malformed/repetition | Dev /24 | Dev city/code/unknown | Dev EOS/malformed/repetition | Context gain |
| ---: | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: |
| 601 | 1301 | ordinary | uniform | 96 | 32/32/32 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 14 |
| 601 | 1301 | ordinary | first16 | 96 | 32/32/32 | 96/0/0 | 23 | 7/8/8 | 24/0/0 | 13 |
| 601 | 1301 | recurrent | uniform | 96 | 32/32/32 | 96/0/0 | 20 | 5/7/8 | 24/0/0 | 9 |
| 601 | 1301 | recurrent | first16 | 96 | 32/32/32 | 96/0/0 | 21 | 5/8/8 | 23/2/0 | 12 |
| 601 | 1709 | ordinary | uniform | 96 | 32/32/32 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 14 |
| 601 | 1709 | ordinary | first16 | 96 | 32/32/32 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 13 |
| 601 | 1709 | recurrent | uniform | 96 | 32/32/32 | 96/0/0 | 20 | 5/7/8 | 24/0/0 | 10 |
| 601 | 1709 | recurrent | first16 | 96 | 32/32/32 | 96/0/0 | 21 | 5/8/8 | 24/1/0 | 13 |
| 947 | 1301 | ordinary | uniform | 96 | 32/32/32 | 96/0/0 | 18 | 2/8/8 | 24/0/0 | 9 |
| 947 | 1301 | ordinary | first16 | 96 | 32/32/32 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 16 |
| 947 | 1301 | recurrent | uniform | 96 | 32/32/32 | 96/0/0 | 23 | 7/8/8 | 24/1/0 | 13 |
| 947 | 1301 | recurrent | first16 | 96 | 32/32/32 | 96/0/0 | 23 | 7/8/8 | 24/0/0 | 13 |
| 947 | 1709 | ordinary | uniform | 96 | 32/32/32 | 96/0/0 | 18 | 2/8/8 | 24/0/0 | 10 |
| 947 | 1709 | ordinary | first16 | 96 | 32/32/32 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 15 |
| 947 | 1709 | recurrent | uniform | 96 | 32/32/32 | 96/0/0 | 19 | 4/7/8 | 24/1/0 | 9 |
| 947 | 1709 | recurrent | first16 | 96 | 32/32/32 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 14 |

Global training eligibility: **True**. Candidate mastery: **True**. Control eligibility: **True**. Development evaluated: **True**.

| Crossed seeds | Model | Training first16-minus-uniform exact | Development exact delta |
| --- | --- | ---: | ---: |
| i601-s1301 | ordinary | 0 | -1 |
| i601-s1301 | recurrent | 0 | 1 |
| i601-s1709 | ordinary | 0 | 0 |
| i601-s1709 | recurrent | 0 | 1 |
| i947-s1301 | ordinary | 0 | 6 |
| i947-s1301 | recurrent | 0 | 0 |
| i947-s1709 | ordinary | 0 | 6 |
| i947-s1709 | recurrent | 0 | 5 |

Consistent objective improvement: **False**. A training-only effect does not establish fresh-combination accuracy. Missing development results are not scored as zero or inferred failures. Any development regressions/ties remain failed registered improvement gates.

## Objective effect, failures and seed sensitivity

Aggregate exact: uniform 166/192 versus first16 184/192. These are repeated model/case observations on24 distinct development cases, not192 independent examples. EOS totals uniform 192/192 versus first16 191/192; malformed counts2 versus3; repetition counts0 versus0.

| Model | Uniform exact /96 | First16 exact /96 | Gain |
| --- | ---: | ---: | ---: |
| ordinary | 84 | 95 | 11 |
| recurrent | 82 | 89 | 7 |

| Factor | Level | Uniform exact /96 | First16 exact /96 | Gain |
| --- | ---: | ---: | ---: | ---: |
| initialization_seed | 601 | 88 | 89 | 1 |
| initialization_seed | 947 | 78 | 95 | 17 |
| shuffle_seed | 1301 | 85 | 91 | 6 |
| shuffle_seed | 1709 | 81 | 93 | 12 |

Pairs: 5 improved,2 tied,1 regressed. Both models have positive aggregate objective gains, but the effect is not consistent across initialization/order. Ordinary601 regresses/ties while ordinary947 improves under both orders; recurrent947's gain differs across shuffle seeds. This is seed-sensitive evidence, not a uniformly reliable intervention. It does not identify the internal optimization mechanism or a benefit specifically caused by memory.

First16 candidate failures (all raw native continuations retained):

| Crossed cell | Case | Gold | Raw generated IDs | EOS | Gold rank | Gold-minus-top |
| --- | --- | --- | --- | --- | ---: | ---: |
| i601-s1301-ordinary-first16 | v2-dev-012 | la | `[118, 114, 2]` | True | 2 | -0.540195 |
| i601-s1301-recurrent-first16 | v2-dev-012 | la | `[66, 2]` | True | 8 | -6.150173 |
| i601-s1301-recurrent-first16 | v2-dev-013 | mi | `[13, 120, 2]` | True | 2 | -0.081824 |
| i601-s1301-recurrent-first16 | v2-dev-018 | mi | `[93, 36, 108, 113, 49, 66, 119, 124]` | False | 5 | -1.660897 |
| i601-s1709-recurrent-first16 | v2-dev-012 | la | `[66, 2]` | True | 10 | -5.792510 |
| i601-s1709-recurrent-first16 | v2-dev-013 | mi | `[13, 120, 2]` | True | 5 | -2.647539 |
| i601-s1709-recurrent-first16 | v2-dev-018 | mi | `[111, 100, 2]` | True | 15 | -5.589559 |
| i947-s1301-recurrent-first16 | v2-dev-012 | la | `[112, 108, 2]` | True | 2 | -1.096484 |

Both recurrent601 candidates fail city>=7 (5/8 each) and format gates; shuffle1301 also has an EOS failure. Ordinary601/shuffle1301 loses one previously correct city answer. No repetition is recorded under the fixed one/two-ID-block definition. All candidate exact errors begin at the first answer byte; one also fails termination. Higher aggregate accuracy cannot override these failures or the two tied pairs.

## Complete scoped costs and retained attempts

Seconds below are complete kernel Job lifetimes, including controllers, descendants, cold imports/setup/checkpoint I/O, monitoring/sealing where enclosed, and exit. Parent totals already include nested worker totals.

| Scope | CPU s | Wall s | Peak committed bytes | Status |
| --- | ---: | ---: | ---: | --- |
| Preparation including contracts/rehearsal | 13.750000 | 28.779271 | 698224640 | PASS |
| Registered budget | 595.953125 | 488.008649 | 727769088 | PASS |
| Independent saved-only audit | 1.515625 | 1.578365 | 36589568 | PASS |
| Repository verification | 31.968750 | 35.067960 | 762753024 | PASS |

Non-overlapping measured scope sum: CPU643.187500,wall553.434245 seconds. Audit and repository verification are separate from registered scientific cost; they perform zero model forwards. Initial v1 access checks/read-only precondition and preservation checks outside Jobs have unmeasured costs.

The single seed902407 random-data rehearsal used zero optimizer updates and no study examples:CPU3.312500,wall6.044464; selected common fit cap70 before fitting. It is already inside preparation, excluded from scores and not added twice. All70-second fit/30-second observation/2-second request/1800-second CPU AND wall overall caps,2GiB commit,128MiB output and5-second monitoring-gap limits were verified. All jobs closed with0 active processes. No weak seed was retried.

Registered peak output35491050 bytes,maximum gap0.133993s,250 process lifetimes,0 forcibly terminated. Registered outer observer CPU-to-receipt73.937500s is outside that Job and is NOT its complete lifetime. Source editing,preflight,registration and final reporting outside Jobs are unmeasured. No complete project cost or total-efficiency claim is available.

| Cell | Cold fit CPU/wall | Training observation CPU/wall | Dev + question-only CPU/wall | Fit peak commit bytes |
| --- | --- | --- | --- | ---: |
| i601-s1301-ordinary-uniform | 14.812500/15.674244 | 3.796875/4.421616 | 3.453125/4.145492 | 680050688 |
| i601-s1301-ordinary-first16 | 14.796875/15.448225 | 3.750000/4.311702 | 3.734375/4.163917 | 680226816 |
| i601-s1301-recurrent-uniform | 22.640625/23.288775 | 4.140625/4.776679 | 3.671875/4.300460 | 680656896 |
| i601-s1301-recurrent-first16 | 22.546875/23.138725 | 4.125000/4.865490 | 3.687500/4.366264 | 680349696 |
| i601-s1709-ordinary-uniform | 15.437500/15.908973 | 3.781250/4.406287 | 3.609375/4.169039 | 681062400 |
| i601-s1709-ordinary-first16 | 15.296875/15.967005 | 3.703125/4.403328 | 3.703125/4.279980 | 680603648 |
| i601-s1709-recurrent-uniform | 23.265625/23.891703 | 4.593750/5.147842 | 3.687500/4.409366 | 679510016 |
| i601-s1709-recurrent-first16 | 23.296875/24.003190 | 4.359375/4.922588 | 3.765625/4.450662 | 680734720 |
| i947-s1301-ordinary-uniform | 15.781250/16.713604 | 3.609375/4.356769 | 3.640625/4.155415 | 680607744 |
| i947-s1301-ordinary-first16 | 17.062500/17.798865 | 4.109375/4.894396 | 3.609375/4.248262 | 681013248 |
| i947-s1301-recurrent-uniform | 26.046875/26.823731 | 4.484375/5.295422 | 3.765625/4.507551 | 680558592 |
| i947-s1301-recurrent-first16 | 26.062500/26.856450 | 4.750000/5.484919 | 3.671875/4.459858 | 680144896 |
| i947-s1709-ordinary-uniform | 17.453125/18.375939 | 4.187500/4.752663 | 3.562500/4.108725 | 679763968 |
| i947-s1709-ordinary-first16 | 17.218750/17.853778 | 4.546875/5.185348 | 3.562500/4.234449 | 680202240 |
| i947-s1709-recurrent-uniform | 25.796875/26.587466 | 4.406250/5.112763 | 3.656250/4.370667 | 680431616 |
| i947-s1709-recurrent-first16 | 25.312500/26.009531 | 4.296875/4.854400 | 3.718750/4.373330 | 680779776 |

[Registered complete receipt](../../artifacts/local-answer-value-start-replication-v2/registered/budget/cost.json). Scientific sealed directories are immutable; audit/report outputs live outside them.

## Raw evidence, independent integrity and checks

| Cell | Raw training | Raw development | Checkpoint identity |
| --- | --- | --- | --- |
| i601-s1301-ordinary-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1301-ordinary-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1301-ordinary-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1301-ordinary-uniform/checkpoint-meta.json) |
| i601-s1301-ordinary-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1301-ordinary-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1301-ordinary-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1301-ordinary-first16/checkpoint-meta.json) |
| i601-s1301-recurrent-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1301-recurrent-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1301-recurrent-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1301-recurrent-uniform/checkpoint-meta.json) |
| i601-s1301-recurrent-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1301-recurrent-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1301-recurrent-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1301-recurrent-first16/checkpoint-meta.json) |
| i601-s1709-ordinary-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1709-ordinary-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1709-ordinary-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1709-ordinary-uniform/checkpoint-meta.json) |
| i601-s1709-ordinary-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1709-ordinary-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1709-ordinary-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1709-ordinary-first16/checkpoint-meta.json) |
| i601-s1709-recurrent-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1709-recurrent-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1709-recurrent-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1709-recurrent-uniform/checkpoint-meta.json) |
| i601-s1709-recurrent-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i601-s1709-recurrent-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i601-s1709-recurrent-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i601-s1709-recurrent-first16/checkpoint-meta.json) |
| i947-s1301-ordinary-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1301-ordinary-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1301-ordinary-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1301-ordinary-uniform/checkpoint-meta.json) |
| i947-s1301-ordinary-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1301-ordinary-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1301-ordinary-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1301-ordinary-first16/checkpoint-meta.json) |
| i947-s1301-recurrent-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1301-recurrent-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1301-recurrent-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1301-recurrent-uniform/checkpoint-meta.json) |
| i947-s1301-recurrent-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1301-recurrent-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1301-recurrent-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1301-recurrent-first16/checkpoint-meta.json) |
| i947-s1709-ordinary-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1709-ordinary-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1709-ordinary-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1709-ordinary-uniform/checkpoint-meta.json) |
| i947-s1709-ordinary-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1709-ordinary-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1709-ordinary-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1709-ordinary-first16/checkpoint-meta.json) |
| i947-s1709-recurrent-uniform | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1709-recurrent-uniform/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1709-recurrent-uniform/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1709-recurrent-uniform/checkpoint-meta.json) |
| i947-s1709-recurrent-first16 | [train](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/evaluate-i947-s1709-recurrent-first16/predictions-main.jsonl) | [dev](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/development-i947-s1709-recurrent-first16/predictions-main.jsonl) | [checkpoint metadata](../../artifacts/local-answer-value-start-replication-v2/registered/execution/stages/fit-i947-s1709-recurrent-first16/checkpoint-meta.json) |

[Independent audit](../../artifacts/local-answer-value-start-replication-v2/independent-audit.json) and [all failed first-token records](../../artifacts/local-answer-value-start-replication-v2/failure-index.json). The independent audit and final read-only checks reconstruct every exact/value/EOS/format/repetition score,first-vector argmax/rank/probabilities/margins,teacher NLL,replay,all 24576 optimizer steps,targets/exposures,initialization and schedule independence,48 scientific stage seals, root/budget seals,kernel monitor closure,and v1 payload preservation. Its model-forward count is0. Original v1's negative decision and older paired-batch integrity failure remain unchanged.

34 pre-fit contracts passed:24 native accounting/sealing tests and10 numerical/data/independent-seed/gate tests. No research update in those tests. Post-run repository lint/format,focused typing,frozen sources,dependency checks and git diff --check are recorded in verification/checks.json. Hosted CI:NOT_RUN. Full research smoke/verify.py:NOT_RUN, because it installs/trains/generates unrelated material. Native accounting is Windows-specific.

Offline reproduction (no model forwards or generation):

~~~powershell
.\.venv\Scripts\python.exe -I -S -B scripts/audit_value_start_replication_v2.py
.\.venv\Scripts\python.exe -B artifacts/local-answer-value-start-replication-v2/verify_report.py
git diff --check
~~~

Do not rerun prepare/resources/register/launch or workers. The attempt is consumed; all partial/failure receipts and initial draft/type issues are retained.

Final post-report checks additionally verified all1952 stored first-vector
probabilities and stricter entity/value non-overlap,all16 accuracy rows,54 links,
and the unchanged draft-to-final data/design bindings. Readable outside-sandbox
`git diff --check` and cached checks passed with zero tracked/staged edits;
sandbox Git access warnings about old private fixture trees are not new deletions.
The34 contracts'24 native test cases are preserved in100 copied fixture files
under `retained-accounting-tests/`,including intentional STOP/mutation cases.
The initial outside-context copy saw zero private fixture files; that attempt
receipt is retained. Copying from the original sandbox context succeeded without
changing source fixtures or any scientific seal. These are engineering fixtures,
not extra research attempts. Final review/inventory metadata records their hashes.

Registered budget observer seal SHA256:
`e635e1602c46cd28f841a2f39cbc0074cae9188a2584a5872f29f91dac0bb6d5`.

## Limitations and one next action

Only2 initialization x2 shuffle seeds/model,one small synthetic grammar,shared finite answer vocabulary,new training entity names,and reused known initialization seeds. This development study estimates no held-out performance or population-wide reliability. Across-model widths and actual CPU differ. Any benefit shared by ordinary/recurrent is an objective effect in this design,not a recurrent-memory advantage. No delayed context,real conversation or total-efficiency test occurred.

**Recommended next action:** stop treating first-token x16 as a reliable default under this design; preserve the crossed negative/seed-sensitive result and do not launch a memory comparison.

All new work remains uncommitted. Historical sources,reports,seals and local checkpoints were preserved. No production chat,commit,push or deployment.
