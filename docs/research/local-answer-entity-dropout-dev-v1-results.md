# Local-answer entity dropout dev v1 — results

26 November 2026. Development only. Decision: **STOP_DEVELOPMENT_FAILURE**.
Measurement integrity: **PASS**. No memory/architecture advantage is inferred.

## Starting state and preservation

Git root D:/Toruk, branch main, HEAD and origin/main both `916efdd4b63dd63fab08ffabb8ab6e8313dc4bf2`, initially clean. No pull/reset/commit/push. All historical studies and ignored weights preserved; the old inaccessible preparation fixture was left untouched. Independent v2 audit passes with its STOP_DEVELOPMENT_FAILURE unchanged. The new audit checks all 770 reviewed v2 payloads.

## Saved-output diagnosis reproduced before model work

[Raw 34-failure table](../../artifacts/local-answer-entity-dropout-dev-v1/saved-v2-failures.md), [complete saved diagnosis](../../artifacts/local-answer-entity-dropout-dev-v1/saved-v2-diagnosis.json). The original independent v2 auditor reconstructed all 48 stage seals, 24576 recorded updates, native prompts/scores and logit preferences without a model forward.

All16 original cells mastered training96/96. Across development, uniform had26 errors and first16 had8. All34 begin with a wrong first byte, gold rank>1 and negative gold-minus-top margin.22 return an entity's training value. Five are malformed;one also fails EOS. None repeats by the registered criterion. Templates A/B account for21/13 errors out of equal-sized template groups; templates and canonical case difficulty are confounded, so this is not an isolated template effect. Three errors share the question-only first byte; source use is partial,not absent. Required facts are present in every failed prompt. No correct complete answer was rejected. Every saved argmax matches the generator's first token; inference/scoring/measurement defects were not found.

V2 reliability failures: ordinary i601-s1301 regressed24->23;ordinary i601-s1709 tied24;recurrent i947-s1301 tied23. Recurrent i601-s1301 and i601-s1709 first16 each scored21/24 with city5/8 and malformed output;the former also had EOS23/24. Candidate failures are v2-dev-012 (ral city=la) in four cells;v2-dev-013 (city ral=mi) in both recurrent601 cells;v2-dev-018 (sun city=mi) in both recurrent601 cells. The first-byte preferences explain emitted choices,not how optimization created them. Entity/value shortcuts are a testable hypothesis rather than a verified mechanism.

| V2 cell | Exact /24 | City/code/unknown | Wrong first | EOS | Malformed |
| --- | ---: | --- | ---: | ---: | ---: |
| i601-s1301-ordinary-first16 | 23 | 7/8/8 | 1 | 24 | 0 |
| i601-s1301-ordinary-uniform | 24 | 8/8/8 | 0 | 24 | 0 |
| i601-s1301-recurrent-first16 | 21 | 5/8/8 | 3 | 23 | 2 |
| i601-s1301-recurrent-uniform | 20 | 5/7/8 | 4 | 24 | 0 |
| i601-s1709-ordinary-first16 | 24 | 8/8/8 | 0 | 24 | 0 |
| i601-s1709-ordinary-uniform | 24 | 8/8/8 | 0 | 24 | 0 |
| i601-s1709-recurrent-first16 | 21 | 5/8/8 | 3 | 24 | 1 |
| i601-s1709-recurrent-uniform | 20 | 5/7/8 | 4 | 24 | 0 |
| i947-s1301-ordinary-first16 | 24 | 8/8/8 | 0 | 24 | 0 |
| i947-s1301-ordinary-uniform | 18 | 2/8/8 | 6 | 24 | 0 |
| i947-s1301-recurrent-first16 | 23 | 7/8/8 | 1 | 24 | 0 |
| i947-s1301-recurrent-uniform | 23 | 7/8/8 | 1 | 24 | 1 |
| i947-s1709-ordinary-first16 | 24 | 8/8/8 | 0 | 24 | 0 |
| i947-s1709-ordinary-uniform | 18 | 2/8/8 | 6 | 24 | 0 |
| i947-s1709-recurrent-first16 | 24 | 8/8/8 | 0 | 24 | 0 |
| i947-s1709-recurrent-uniform | 19 | 4/7/8 | 5 | 24 | 1 |

## Frozen intervention and control

[Protocol](local-answer-entity-dropout-dev-v1-protocol.md); [registration](../../artifacts/local-answer-entity-dropout-dev-v1/registration.json); [plan](../../artifacts/local-answer-entity-dropout-dev-v1/plan.json). Plan SHA256 `798ad53e4b1999d38ffe3db77f34e5ed195cf7253c4db2628ee914b52db07cb0`;registration SHA256 `c20f606d1340fdbb73a11809a963bbb4b1c06cc6cb2bef49f1da7ad709a7c82d`.

One training-only intervention: both entity mentions become three-byte `ref` in 64/128 presentations/document, with exact deterministic parity scheduling;the other64 retain original names. Uniform CE in both arms. Identical initialization601/947 crossed with shuffle1301/1709,models,1536 steps,batch8,optimizer,city schedule,byte lengths and token work. Fresh uniform controls must reproduce v2 final tensor hashes and every native train/dev continuation. Candidate dropout never changes development prompts. The train/dev canonical overlap remains0 even after adding anonymous training views. Development reuses the24 diagnosed v2 cases:adaptive exploratory evidence,not a new validation sample. Historical first16 was not selected as the primary control.

Caps were frozen before model work:fit90s,observation40s,request2s,registered1800 CPU AND wall seconds,2GiB commit,128MiB output,max gap5s. All32 prerequisite contracts passed. The single seed918733 random rehearsal made0 updates,used0 study examples,and projected 68s for both models. No cap increased,no fit retried. Source and protocol bytes were frozen before rehearsal;pre-fit formatting/type issues were corrected before the freeze (long lines/import order and two missing/inferred annotations).

The training gate requires all16 original-input training scores96/96,full EOS and zero malformed/repetition/wrong-first. Development can open only after that. Candidate floors are>=22/24,city>=7,code>=7,unknown8,EOS24,zero malformed/repetition,context gain>=8. No paired exact/category/EOS regression;every non-ceiling control must improve,positive model totals,and recurrent601 city first NLL must improve under both shuffles. Ceiling ties are permitted prospectively;they are not improvement evidence. V2's original strict-positive-all8 gate stays failed.

## Registered per-cell results

| Init/shuffle/model | Arm | Train /96 | Train EOS/malformed/repetition | Dev /24 | Dev city/code/unknown | Dev EOS/malformed/repetition | Train full/answer/first NLL |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| i601-s1301-ordinary | drop50 | 96 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 0.165476/0.009339/0.016976 |
| i601-s1301-ordinary | uniform | 96 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 0.142127/0.007065/0.010599 |
| i601-s1301-recurrent | drop50 | 96 | 96/0/0 | 22 | 6/8/8 | 24/0/0 | 0.161781/0.010758/0.018377 |
| i601-s1301-recurrent | uniform | 96 | 96/0/0 | 20 | 5/7/8 | 24/0/0 | 0.140079/0.013672/0.026747 |
| i601-s1709-ordinary | drop50 | 96 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 0.163306/0.010122/0.017639 |
| i601-s1709-ordinary | uniform | 96 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 0.141714/0.007506/0.011732 |
| i601-s1709-recurrent | drop50 | 96 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 0.159099/0.011160/0.018750 |
| i601-s1709-recurrent | uniform | 96 | 96/0/0 | 20 | 5/7/8 | 24/0/0 | 0.140992/0.012230/0.021906 |
| i947-s1301-ordinary | drop50 | 96 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 0.156793/0.010329/0.020035 |
| i947-s1301-ordinary | uniform | 96 | 96/0/0 | 18 | 2/8/8 | 24/0/0 | 0.129367/0.010461/0.020274 |
| i947-s1301-recurrent | drop50 | 96 | 96/0/0 | 22 | 6/8/8 | 24/0/0 | 0.152842/0.012461/0.023020 |
| i947-s1301-recurrent | uniform | 96 | 96/0/0 | 23 | 7/8/8 | 24/1/0 | 0.125779/0.013006/0.023665 |
| i947-s1709-ordinary | drop50 | 96 | 96/0/0 | 24 | 8/8/8 | 24/0/0 | 0.156904/0.011567/0.023447 |
| i947-s1709-ordinary | uniform | 96 | 96/0/0 | 18 | 2/8/8 | 24/0/0 | 0.130220/0.013516/0.030053 |
| i947-s1709-recurrent | drop50 | 96 | 96/0/0 | 21 | 6/7/8 | 24/0/0 | 0.151277/0.010485/0.018508 |
| i947-s1709-recurrent | uniform | 96 | 96/0/0 | 19 | 4/7/8 | 24/1/0 | 0.128922/0.010478/0.014702 |

Training gate: **True**. Development evaluated: **True**. Decision: **STOP_DEVELOPMENT_FAILURE**.

[Independent audit](../../artifacts/local-answer-entity-dropout-dev-v1/independent-audit.json) contains every failed case,raw continuation,pair gate,candidate floor and cost. [Sealed execution summary](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/summary.json).

| Pair | Exact delta | Pair gate |
| --- | ---: | --- |
| i601-s1301-ordinary | 0 | True |
| i601-s1301-recurrent | 2 | True |
| i601-s1709-ordinary | 0 | True |
| i601-s1709-recurrent | 4 | True |
| i947-s1301-ordinary | 6 | True |
| i947-s1301-recurrent | -1 | False |
| i947-s1709-ordinary | 6 | True |
| i947-s1709-recurrent | 2 | True |

| Recurrent601 city first-token NLL | Uniform | Dropout | Mechanism gate |
| --- | ---: | ---: | --- |
| i601-s1301 | 1.566109 | 0.862512 | True |
| i601-s1709 | 1.119630 | 0.075940 | True |

Exact regressions: i947-s1301-recurrent. Candidate floors: {"i601-s1301-ordinary": true, "i601-s1301-recurrent": false, "i601-s1709-ordinary": true, "i601-s1709-recurrent": true, "i947-s1301-ordinary": true, "i947-s1301-recurrent": false, "i947-s1709-ordinary": true, "i947-s1709-recurrent": false}. Pair gates also test category/EOS regressions;the independent audit retains each gate.

Measured preferences and the training-origin hypothesis remain distinct. Any gain is consistent with this data intervention,not proof of an internal entity-copy mechanism. A failed registered gate rejects the intervention as a reliable fix in this design;neither pooled accuracy nor one favorable seed overrides it.

## Costs and raw evidence

Nested stage costs below are included in the registered budget;do not add them again. All are complete Windows Job lifetimes including cold imports,I/O,controllers and descendants. Preparation and registered totals do not overlap. Outermost observer, editing,registration,saved diagnosis outside a Job and report-writing lifetime costs are unknown. No complete project-cost or total-efficiency claim.

Preparation CPU/wall: 8.062500/13.637367s. Registered CPU/wall: **569.296875/472.513418s**. Registered peak commit 725377024 bytes,peak disk 37964465 bytes, max monitor gap 0.653977s,active processes 0. Budget seal SHA256 `400273662273cf805f00687a72e19170e8294785e7610279c3d3ad3cb35a0d2f`.

| Cell | Fit CPU/wall s | Train observation CPU/wall s | Dev CPU/wall s | Targets / padded positions | Generated train/dev tokens including replays |
| --- | --- | --- | --- | --- | --- |
| i601-s1301-ordinary-drop50 | 14.484375/15.207758 | 3.843750/4.338269 | 3.812500/4.674182 | 692224 / 786432 | 291/192 |
| i601-s1301-ordinary-uniform | 14.484375/15.073167 | 3.859375/4.362238 | 3.734375/4.388200 | 692224 / 786432 | 291/211 |
| i601-s1301-recurrent-drop50 | 23.062500/23.972951 | 4.562500/5.154374 | 4.359375/5.031351 | 692224 / 786432 | 291/139 |
| i601-s1301-recurrent-uniform | 21.968750/22.760565 | 4.093750/4.735265 | 3.750000/4.415281 | 692224 / 786432 | 291/151 |
| i601-s1709-ordinary-drop50 | 14.984375/15.629151 | 3.625000/4.331286 | 3.687500/4.426540 | 692224 / 786432 | 291/168 |
| i601-s1709-ordinary-uniform | 14.984375/15.862650 | 3.656250/4.365251 | 3.593750/4.266171 | 692224 / 786432 | 291/167 |
| i601-s1709-recurrent-drop50 | 22.468750/23.301062 | 4.390625/5.082107 | 4.046875/4.899308 | 692224 / 786432 | 291/149 |
| i601-s1709-recurrent-uniform | 22.562500/23.172483 | 4.078125/4.790412 | 3.812500/4.539105 | 692224 / 786432 | 291/147 |
| i947-s1301-ordinary-drop50 | 16.390625/17.303193 | 3.968750/4.648616 | 3.421875/4.113438 | 692224 / 786432 | 291/141 |
| i947-s1301-ordinary-uniform | 15.734375/16.244188 | 3.671875/4.379562 | 3.468750/4.260306 | 692224 / 786432 | 291/137 |
| i947-s1301-recurrent-drop50 | 21.046875/21.938067 | 4.000000/4.736304 | 4.046875/4.873856 | 692224 / 786432 | 291/173 |
| i947-s1301-recurrent-uniform | 20.828125/21.580453 | 4.109375/4.746995 | 3.921875/4.992551 | 692224 / 786432 | 291/162 |
| i947-s1709-ordinary-drop50 | 14.421875/15.058815 | 3.750000/4.405146 | 3.750000/4.495679 | 692224 / 786432 | 291/141 |
| i947-s1709-ordinary-uniform | 15.812500/16.791636 | 4.843750/5.689276 | 3.890625/4.557951 | 692224 / 786432 | 291/137 |
| i947-s1709-recurrent-drop50 | 25.484375/26.279002 | 4.687500/5.532453 | 3.906250/4.586065 | 692224 / 786432 | 291/167 |
| i947-s1709-recurrent-uniform | 25.281250/26.099587 | 4.921875/5.653429 | 3.812500/4.553229 | 692224 / 786432 | 291/176 |

Each stage's `token-costs.json` retains input/generated/teacher target/forward counts and request CPU/wall,including replays. Every raw native continuation,first logit vector,teacher loss,training step,checkpoint and monitor is retained. Checkpoints are ignored local inputs,with exact metadata hashes;no replacement weights were created.

| Cell | Training raw | Development raw | Fit metadata |
| --- | --- | --- | --- |
| i601-s1301-ordinary-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1301-ordinary-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1301-ordinary-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1301-ordinary-drop50/checkpoint-meta.json) |
| i601-s1301-ordinary-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1301-ordinary-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1301-ordinary-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1301-ordinary-uniform/checkpoint-meta.json) |
| i601-s1301-recurrent-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1301-recurrent-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1301-recurrent-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1301-recurrent-drop50/checkpoint-meta.json) |
| i601-s1301-recurrent-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1301-recurrent-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1301-recurrent-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1301-recurrent-uniform/checkpoint-meta.json) |
| i601-s1709-ordinary-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1709-ordinary-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1709-ordinary-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1709-ordinary-drop50/checkpoint-meta.json) |
| i601-s1709-ordinary-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1709-ordinary-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1709-ordinary-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1709-ordinary-uniform/checkpoint-meta.json) |
| i601-s1709-recurrent-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1709-recurrent-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1709-recurrent-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1709-recurrent-drop50/checkpoint-meta.json) |
| i601-s1709-recurrent-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i601-s1709-recurrent-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i601-s1709-recurrent-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i601-s1709-recurrent-uniform/checkpoint-meta.json) |
| i947-s1301-ordinary-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1301-ordinary-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1301-ordinary-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1301-ordinary-drop50/checkpoint-meta.json) |
| i947-s1301-ordinary-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1301-ordinary-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1301-ordinary-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1301-ordinary-uniform/checkpoint-meta.json) |
| i947-s1301-recurrent-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1301-recurrent-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1301-recurrent-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1301-recurrent-drop50/checkpoint-meta.json) |
| i947-s1301-recurrent-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1301-recurrent-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1301-recurrent-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1301-recurrent-uniform/checkpoint-meta.json) |
| i947-s1709-ordinary-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1709-ordinary-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1709-ordinary-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1709-ordinary-drop50/checkpoint-meta.json) |
| i947-s1709-ordinary-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1709-ordinary-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1709-ordinary-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1709-ordinary-uniform/checkpoint-meta.json) |
| i947-s1709-recurrent-drop50 | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1709-recurrent-drop50/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1709-recurrent-drop50/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1709-recurrent-drop50/checkpoint-meta.json) |
| i947-s1709-recurrent-uniform | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/evaluate-i947-s1709-recurrent-uniform/predictions-main.jsonl) | [raw](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/development-i947-s1709-recurrent-uniform/predictions-main.jsonl) | [metadata](../../artifacts/local-answer-entity-dropout-dev-v1/registered/execution/stages/fit-i947-s1709-recurrent-uniform/checkpoint-meta.json) |

## Verification and limits

Independent audit rechecks original v2 integrity,all new nested/root seals,all native scores and first-token ranks/margins,uniform loss partitions,1536 schedules/fit,64/64 dropout exposures,checkpoint/source bytes,control tensor/prediction parity and complete closed accounting. Its model-forward count is0. Relevant repository checks are in [verification receipts](../../artifacts/local-answer-entity-dropout-dev-v1/verification-checks.json). Hosted CI NOT_RUN;no push authorized. This is one small synthetic grammar,two initialization and two order seeds,finite shared values,and reused diagnostic development cases. No long-history,memory or chatbot advantage follows.

Offline checks (no research launcher rerun):

```powershell
.venv/Scripts/python.exe -B scripts/audit_entity_dropout_dev.py
.venv/Scripts/python.exe -m pytest -q tests/test_entity_dropout_dev.py tests/test_value_start_replication_v2.py tests/test_lifetime_job.py tests/test_lifetime_job_v2.py
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check src tests scripts
.venv/Scripts/python.exe -m mypy
.venv/Scripts/python.exe -m mypy --platform linux
git diff --check
```

Do not rerun prepare/resources/register/launch:the attempt is consumed and all paths are exclusive. Changes remain uncommitted for review.

Recommended next action: reject entity dropout as a reliable fix under this budget and preserve the failed gate;do not extend or retry this run.

## Exact remaining candidate errors and case regressions

| Cell | Case | Gold | Native IDs | Expected rank | Gold-minus-top |
| --- | --- | --- | --- | ---: | ---: |
| i601-s1301-recurrent-drop50 | v2-dev-000 | so | `[66, 2]` | 2 | -1.636110 |
| i601-s1301-recurrent-drop50 | v2-dev-006 | tu | `[118, 114, 2]` | 2 | -4.143453 |
| i947-s1301-recurrent-drop50 | v2-dev-006 | tu | `[66, 2]` | 2 | -3.301579 |
| i947-s1301-recurrent-drop50 | v2-dev-007 | la | `[112, 108, 2]` | 2 | -0.631796 |
| i947-s1709-recurrent-drop50 | v2-dev-006 | tu | `[66, 2]` | 2 | -2.514113 |
| i947-s1709-recurrent-drop50 | v2-dev-007 | la | `[112, 108, 2]` | 2 | -0.417741 |
| i947-s1709-recurrent-drop50 | v2-dev-009 | R-7 | `[89, 61, 55, 2]` | 2 | -0.635483 |

All seven failures start with the measured wrong first token,reach EOS,and are valid answer-inventory strings. They are wrong values or inappropriate unknown answers,not scorer rejection,missing supplied facts or EOS/format failures. [Casewise resolved/introduced errors](../../artifacts/local-answer-entity-dropout-dev-v1/case-regressions.json) also records individual-case regressions even in pairs with positive net gains.

Verification completed:42 focused tests passed;Ruff lint/format,default/Linux mypy, three-script focused mypy,frozen sources,dependencies and working/cached diff checks all passed. Independent audit and verification Jobs have closed process trees and seals. The isolated-index source/report whitespace check passed without changing the real index. Hosted CI was not run. Final Git remains at the starting HEAD with only seven new development paths and no tracked modification or staged change.
