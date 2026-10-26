# Chat release candidate v2 — paired local result

Fixture SHA-256: `86e31ab8afccb0e7ab88817fc11b7be4585a7d261c3d99f93eef60540c63a0c6`. Backbone: `HuggingFaceTB/SmolLM2-135M-Instruct@12fd25f77366`. Selector: `479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`.

| Mode | Quality | Selected tokens | Output tokens | Total tokens | Latency ms | Failures | Unsupported answers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BASELINE | 6/20 | 1818 | 254 | 2072 | 15259.708 | 0 | 3 |
| TORUK | 6/20 | 1546 | 278 | 1824 | 15552.248 | 0 | 3 |

Selected-token reduction: **14.96%**; quality difference: **0.0 percentage points**. Primary success: **False**.

## Per-category quality

| Category | BASELINE | TORUK |
| --- | ---: | ---: |
| ambiguous | 1/2 | 1/2 |
| correction | 1/2 | 1/2 |
| factual | 2/2 | 2/2 |
| instruction | 1/2 | 1/2 |
| irrelevant_history | 0/2 | 0/2 |
| long_retrieval | 1/2 | 1/2 |
| preservation | 0/2 | 0/2 |
| reference | 0/2 | 0/2 |
| unknown | 0/2 | 0/2 |
| user_fact | 0/2 | 0/2 |

## Failure cases and examples

| Case | Mode | Selected IDs | Answer | Quality |
| --- | --- | --- | --- | --- |
| instruction_word | BASELINE | ['m0'] | HELLO | True |
| instruction_word | TORUK | ['m0'] | HELLO | True |
| instruction_digit | BASELINE | ['m0'] | The digit seven is 7. | False |
| instruction_digit | TORUK | ['m0'] | The digit seven is 7. | False |
| fact_italy | BASELINE | ['m0'] | The capital city of Italy is Rome. | True |
| fact_italy | TORUK | ['m0'] | The capital city of Italy is Rome. | True |
| fact_water | BASELINE | ['m0'] | At sea level, pure water boils at a temperature of approximately 100 degrees Celsius. | True |
| fact_water | TORUK | ['m0'] | At sea level, pure water boils at a temperature of approximately 100 degrees Celsius. | True |
| reference_nickname | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | I'm sorry for any confusion, but as a painting assistant, I don't have the ability to name you. | False |
| reference_nickname | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | I'm sorry for any confusion, but as a painting assistant, I don't have the ability to name you. | False |
| reference_codename | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | I noted the codename. | False |
| reference_codename | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | I noted the codename. | False |
| user_fact_drink | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | I noted that you prefer a cold drink. | False |
| user_fact_drink | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | I noted that you prefer a cold drink. | False |
| user_fact_pet | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | I'm sorry for any confusion, but as a helpful AI, I don't have real-time access to the internet. I'm here to assist with your | False |
| user_fact_pet | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | I'm sorry for any confusion, but as a helpful AI, I don't have real-time access to the internet. I'm here to assist with your | False |
| correction_day | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | I will use the corrected day. | False |
| correction_day | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | I will use the corrected day. | False |
| correction_floor | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | Floor five. | True |
| correction_floor | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | Floor five. | True |
| preserve_city | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | I provided the city name. | False |
| preserve_city | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | I provided the city name. | False |
| preserve_hobby | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | My hobby is playing chess. The deadline is Monday. | False |
| preserve_hobby | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | My hobby is playing chess. The deadline is Monday. | False |
| long_key | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9', 'm10'] | I noted the archive key. | False |
| long_key | TORUK | ['m0', 'm1', 'm8', 'm9', 'm10'] | I noted the archive key. | False |
| long_color | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9', 'm10'] | The package label was violet. | True |
| long_color | TORUK | ['m0', 'm1', 'm8', 'm9', 'm10'] | The package label was violet. | True |
| irrelevant_arithmetic | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6'] | That's a tricky one. | False |
| irrelevant_arithmetic | TORUK | ['m0', 'm2', 'm4', 'm5', 'm6'] | Three is 3. | False |
| irrelevant_fact | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6'] | I noted the planet Mars. | False |
| irrelevant_fact | TORUK | ['m0', 'm2', 'm4', 'm5', 'm6'] | I'm sorry for the confusion, but as a helpful AI, I don't have real-time capabilities to provide information about planets or celestial bodies. I'm | False |
| unknown_pin | BASELINE | ['m0'] | I'm sorry for any confusion, but as a chatbot, I don't have the ability to access or provide sensitive information. I'm designed to provide information | False |
| unknown_pin | TORUK | ['m0'] | I'm sorry for any confusion, but as a chatbot, I don't have the ability to access or provide sensitive information. I'm designed to provide information | False |
| unknown_maiden | BASELINE | ['m0'] | I'm sorry for any confusion, but as a helpful AI, I don't have the ability to provide information about your mother's maiden name. I'm here | False |
| unknown_maiden | TORUK | ['m0'] | I'm sorry for any confusion, but as a helpful AI, I don't have the ability to provide information about your mother's maiden name. I'm here | False |
| ambiguous_season | BASELINE | ['m0', 'm1', 'm2', 'm3', 'm4'] | My favorite season is spring. | False |
| ambiguous_season | TORUK | ['m0', 'm1', 'm2', 'm3', 'm4'] | My favorite season is spring. | False |
| ambiguous_pronoun | BASELINE | ['m0', 'm1', 'm2'] | The pronoun could refer to either person. | True |
| ambiguous_pronoun | TORUK | ['m0', 'm1', 'm2'] | The pronoun could refer to either person. | True |

These are synthetic local probes with one deterministic decoding setting. A pretrained backbone supplies language ability; Toruk supplies only the experimental context selection. No general superiority follows from this set.

## Token distribution and trade-off

The aggregate selected-token reduction was 14.96%, below the preregistered 35% target. Sixteen paired cases retained 100% of the baseline context. The two irrelevant-history cases reduced selected tokens by 17.3% each; the two long-retrieval cases reduced them by 51.5% and 53.3%. Mean per-case reduction was about 7.0%. The paired 2,000-resample descriptive 95% interval for aggregate token reduction was **1.35% to 27.28%**, below 35% even at its upper endpoint. Quality difference was 0 percentage points for this exact fixture (descriptive interval 0 to 0) because the binary scores were identical case by case.

Among the four reduced-context cases, one was correct in both modes (`long_color`); three failed in both. Among the sixteen unchanged-context cases, five were correct in both modes. TORUK changed the wording of two irrelevant-history answers without making either correct. Total output tokens increased from 254 to 278 and aggregate response time from 15,260 ms to 15,552 ms, so this run does not show a latency benefit. Full input tokens before selection were 1,818 in each mode; the selector itself reads the older messages, so the selected-prompt saving is not a claim that Toruk processed fewer total tokens end to end.

## Failure interpretation

Both modes missed the requested digit-only format, two user-provided fact questions, both reference questions, the corrected meeting day, and both unrelated-fact preservation cases. Neither answered either unknown-answer case using the preregistered uncertainty rubric; the ambiguous season case guessed a season. The long archive-key case failed even though TORUK retained the key-bearing turn. The pretrained backbone answered the two short factual questions; this is backbone behavior, not a Toruk memory contribution. The seven-case earlier report and this fixed v2 set both show weak conversational reliability. These failures remain in the raw file and were not used to tune the selector or questions.

**Release decision:** research efficiency claim unsupported. The local website may remain an explicitly experimental prototype; public Toruk inference is not ready on answer quality or hosting evidence.

## Local qualification and release status

Repository: `C:\Users\susee\VScode Project\Toruk`, branch `main`, HEAD `add917398efa061cc67b1b10aff3853acf3c526c`. Existing tracked and untracked work remains in the working tree; this task was not committed or deployed. The raw paired run is `artifacts/chat-release-v2/raw.json`; its wrapper log and metadata are in the same directory. The initial two concurrent integration-smoke attempts and one sequential retry timed out waiting for backend readiness (20 then 60 seconds). A later sequential run of `.\.venv\Scripts\python.exe -u scripts/smoke_chat_foundation.py` passed with page, BASELINE, TORUK, model identity, selected-token telemetry, and backend-outage 503. The ordinary-checkpoint regression run `.\.venv\Scripts\python.exe -u scripts/smoke_vercel_local.py` also passed, returning `abc abc abc abc ` and outage 503. No model or selector change followed the v2 evaluation.

Local checks: `.\.venv\Scripts\python.exe -m pytest -q tests/test_chat.py tests/test_chat_foundation.py tests/test_chat_release_eval.py tests/test_inference_server.py tests/test_foundation.py` passed **26** tests. `npm.cmd --prefix web/vercel run check` passed and `npm.cmd --prefix web/vercel test` passed **8** tests. `.\.venv\Scripts\python.exe -m toruk_lm generate --checkpoint artifacts/minimal-lm-demo-001/train/checkpoint.pt --prompt 'abc ' --max-new-tokens 16` passed. The documented `.\.venv\Scripts\python.exe scripts/verify.py --prefix chat-release-v2 --output-dir artifacts/checks/chat-release-v2-verification` returned **exit 1**: install, package, import, help, diagnose, lint, format, reproduce, validate, summarize, research config/smoke, build, and both diff stages passed; both mypy stages failed while parsing NumPy 2.5.4's Python 3.12 `type` syntax under this project's Python 3.11 mypy target; the test stage showed one failure and hit its 420-second timeout. The first failure was the existing comparison CLI test, which passed alone (`1 passed in 53.37s`) and then passed in `.\.venv\Scripts\python.exe -m pytest -x -q` (`103 passed in 255.46s`). This indicates a timing-sensitive loaded run, not a reproduced chat defect. The focused `.\.venv\Scripts\python.exe -m mypy --python-version 3.14 src/toruk_lm/chat_foundation.py src/toruk_lm/chat_runtime.py src/toruk_lm/inference_server.py scripts/evaluate_chat_release_v2.py scripts/smoke_chat_foundation.py scripts/smoke_vercel_local.py` passed after an annotation-only correction. `git -c safe.directory='C:/Users/susee/VScode Project/Toruk' diff --check` passed.

The `web/vercel` project has 10 files totaling 26,071 bytes and no Python/Torch files, weights, or embedded backend token. Local preview and tests pass, but an authentic `vercel build` is unavailable because the CLI and linked project settings are absent. A dry-run `npm pack` is not a Vercel build and failed because this private frontend package has no version field; no deployment artifact was claimed. Production/preview proxy code rejects plaintext HTTP inference URLs; the Vercel Hobby firewall rule, HTTPS inference host, and public Vercel URL are not configured. GitHub Actions for exact HEAD `add917398efa061cc67b1b10aff3853acf3c526c` returned no workflow runs or statuses. Remote CI has not exercised this uncommitted work.

**Verdicts:** CHAT FOUNDATION **PASS** (local supported backbone and bounded generation); CHAT QUALITY **FAIL** (6/20 in both modes); TORUK MEMORY INTEGRATION **PASS** operationally (13 cases used selector, with selected message IDs recorded), with retrieval quality unproven; TOKEN REDUCTION **FAIL** (14.96% versus 35% target); QUALITY PRESERVATION **INCONCLUSIVE** (baseline below 60% floor); LOCAL END-TO-END CHAT **PASS** on the later sequential smoke; VERCEL FRONTEND **BLOCKED** on an authentic build and account configuration; PUBLIC TORUK INFERENCE **BLOCKED** on host availability and measured answer quality; RESEARCH CLAIM **UNSUPPORTED**.

The single most useful next step is to improve and evaluate the selector on a separate development set, then rerun a newly preregistered held-out paired evaluation with a conversational backbone that first clears the baseline quality floor. Do not use these v2 answers to tune the next model or selector.
