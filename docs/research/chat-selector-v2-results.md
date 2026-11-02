# Chat selector v2: held out local result

The [protocol](chat-selector-v2-protocol.md), [freeze record](../../artifacts/chat-selector-v2-20261101/freeze.json), [training checkpoint](../../artifacts/chat-selector-v2-20261101/selector.json), and [raw three-way replies](../../artifacts/chat-selector-v2-20261101/final-three-way.json) identify this separate experiment. V1 and M6 weights and results were preserved. Source HEAD at freeze: `66028db306a0176edfb48a163cba2f0b3106432a`; the working tree also contains uncommitted changes. The generator and scorer hashes, all split hashes, and backbone digest are in `freeze.json`. A syntax error in the new evaluator was fixed and its hash resealed **before any final answer was scored**. The final data was then evaluated once; no weights, threshold, labels, or scoring rules were changed after seeing the result.

## Audit and training

The ordinary demo checkpoint is a byte-level text continuation model, not the conversational backbone. M6 is an untouched `toruk-controlled-v1` recurrent checkpoint (SHA-256 `479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`) trained for controlled-world QA, not chat relevance. V1 is a separately trained lexical logistic ranker (SHA-256 `09b804ee11a93e22426870c2c29481f209c8b8b99862ed74e0c6286a5861ad92`). Its final cases changed entities and values but reused training templates. V2 reuses that bounded eight-feature architecture and `toruk-chat-selector-v1` **file format**, with distinct `protocol: chat-selector-v2` weights and visible `toruk-chat-selector-v2` runtime kind. The v2 SHA-256 is `abd9d2d1c20edb3ad5cf3282f8a26fca49fb44d508d4ba2ada5ebc9c666b7548`; the file is 1,958 bytes. It scans up to 20 supplied turns and 8 KiB text, retaining at most two older user turns plus the latest three before a 512-token prompt fit. This is learned lexical selection, not persistent or semantic memory.

Train/dev/final had 168/56/28 generated cases, with distinct entity, value, slot, and wording families. Half of each category was short, half long. The eight-case CPU pilot took 0.179 s for its optimizer loop; weighted BCE fell from 1.089 to 0.193, fit the tiny training subset (evidence F1 1.0), reloaded, and replayed deterministically. Its dev evidence F1 was only 0.143. The full 180-step CPU run used seed 173, Adam 0.03, positive weight 5, and weighted evidence-turn BCE. Its loss fell from 1.267 to 0.526; train evidence F1 was 0.571 and dev F1 0.857 at the dev-selected threshold 0.20. The optimizer loop took 0.129 s, with a 311,771,136-byte peak process working set; launching Python/Torch took longer (~8 s). The trained component fit comfortably in system RAM and used no GPU training. These synthetic scores do not show semantic transfer.

The shared answer generator was installed local Ollama `llama3.2:latest`, digest `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`, a pretrained 3.2B Q4_K_M instruct model. No model download or paid API was used in this milestone. The device has 16,831,897,600 bytes physical RAM and a 4,096 MiB RTX 3050 Laptop GPU. GPU memory used after evaluation was 2,366 MiB. The evaluation's GPU sampling helper returned null, so this run does **not** establish peak GPU memory. Available system RAM fell from 1.543 to 0.539 GiB across the 76.204 s final run; this is a host snapshot, not a process peak.

## Frozen final comparison

All three methods received the same 28 histories and used the same model, chat template, greedy decoding, top-p 1, 512 selected-prompt-token cap, and 32 output-token cap. The baseline used recent turns; LEXICAL used untrained word overlap; TORUK used v2 trained scores. Each had zero API errors. The raw artifact retains every prompt, answer, selected message ID, count, latency, and case label.

| Measure | Recent BASELINE | Nonlearned LEXICAL | Trained TORUK |
| --- | ---: | ---: | ---: |
| Strict correct | 26/28 | 22/28 | 22/28 |
| Unsupported answers | 1 | 6 | 6 |
| Required known evidence retained | 22/24 | 24/24 | 24/24 |
| Unnecessary older turns in unknown cases | 32 | 4 | 0 |
| Full history prompt tokens measured | 8,254 | 8,254 | 8,254 |
| Selected prompt tokens | 8,223 | 3,174 | 2,912 |
| Total Ollama prompt evaluation tokens, including metering | 25,741 | 14,602 | 14,078 |
| Selector history scan | 0 | 25,366 bytes | 25,366 bytes |
| Selector CPU time (sum) | 0 | 4.1 ms | 8.8 ms |
| Response time (sum) | 24.23 s | 21.28 s | 19.42 s |

| Category (four cases each) | BASELINE | LEXICAL | TORUK |
| --- | ---: | ---: | ---: |
| Correction | 3 | 2 | 2 |
| Preservation | 4 | 4 | 4 |
| Conflict | 4 | 0 | 0 |
| Irrelevant history | 4 | 4 | 4 |
| Long recall | 4 | 4 | 4 |
| Two facts | 3 | 4 | 4 |
| Unknown | 4 | 4 | 4 |

TORUK selected 64.6% fewer prompt tokens than recent BASELINE and 8.3% fewer than LEXICAL, but its correctness was 14.3 percentage points below recent context and equal to LEXICAL. It therefore fails the preregistered answer-improvement and quality-preserving token-reduction rules. Total prompt evaluation tokens fell, but the selector still read all history; the Ollama metering and trimming calls dominate these totals. A single run under changing host RAM does not show a reliable latency or memory advantage.

The concrete regression is `final-conflict-00`: the later valid port was **Ranchi**. BASELINE answered “Ranchi.” TORUK and LEXICAL both retained `m0` (obsolete Nashik) and `m2` (the later correction), then answered “Finalmember00 has Nashik as the port.” Thus evidence retention alone did not yield a correct answer. On `final-multi_fact-03`, BASELINE answered Udaipur plus the correct code and failed strict correctness; both selectors answered the correct Nashik plus `FINALCODE03`. On `final-unknown-01`, all three answered “I don't know.” These are actual outputs, not scripted responses.

The [local page smoke](../../artifacts/chat-selector-v2-20261101/page-smoke/results.json) passed through browser-facing Node proxy and Python inference, loaded v2 SHA and kind, exercised multi-turn BASELINE/TORUK replies, and returned an outage 503 after stopping the backend. On the older vault-code case, both modes answered `LIME42`; TORUK selected 95 versus 285 prompt tokens. This fixes the specific v1 paraphrase failure on that smoke case, but the final conflicts show a separate regression.

After updating the page's selector-use label, a first smoke retry failed during backend startup (`Checkpoint load failed`); the next [smoke retry](../../artifacts/chat-selector-v2-20261101/page-smoke-retry/results.json) passed with the final page code, both modes, identities, vault answer, and outage handling. The failure log is retained in `page-smoke-final/backend-integration.log`.

## Engineering checks

Focused Python selector, Ollama, chat foundation, and inference tests passed **27/27** on the final rerun. One earlier run had 26 passes and a Windows connection abort in the inference auth test; that test passed on retry. `python -m toruk_lm --help` and `diagnose` exited 0. Mypy passed on 24 source files. Node syntax check and 11 proxy tests passed. `git diff --check` passed for tracked changes. Ruff check **failed with 49 issues** and format check **failed for three files** in the frozen new v2 generator, trainer, and evaluator scripts; those source bytes are bound into the manifest and pre-final freeze, so they are retained as run. Ruff check and format passed for the runtime selector and focused v2 tests. The applicable `.github/workflows/ci.yml` runs the broader CPU foundation suite on push/PR; no GitHub Actions runs were associated with the local HEAD, and uncommitted v2 work has not run remotely.

## Reproduce and limits

From the repository root in Windows PowerShell, use fresh output paths for a replay (the stored files are frozen):

```powershell
$digest = 'a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72'
.\.venv\Scripts\python.exe scripts/build_chat_selector_data_v2.py --output-dir artifacts/chat-selector-v2-replay/data
.\.venv\Scripts\python.exe scripts/train_chat_selector_v2.py --data-dir artifacts/chat-selector-v2-replay/data --output artifacts/chat-selector-v2-replay/pilot.json --pilot
.\.venv\Scripts\python.exe scripts/train_chat_selector_v2.py --data-dir artifacts/chat-selector-v2-replay/data --output artifacts/chat-selector-v2-replay/selector.json
.\.venv\Scripts\python.exe scripts/smoke_chat_foundation.py --ollama-model llama3.2:latest --ollama-digest $digest --selector-checkpoint artifacts/chat-selector-v2-20261101/selector.json --output-dir artifacts/chat-selector-v2-replay/page-smoke --chat-probes
```

To reproduce the **sealed final comparison**, use the stored files and a fresh output path:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_chat_selector_v2.py --data-dir artifacts/chat-selector-v2-20261101/data --selector-checkpoint artifacts/chat-selector-v2-20261101/selector.json --freeze artifacts/chat-selector-v2-20261101/freeze.json --model llama3.2:latest --digest $digest --output artifacts/chat-selector-v2-replay/final-three-way.json
```

Its hash checks reject changed protocol, evaluator, final data, checkpoint, or digest.

Next research change: train a versioned selector that models fact updates and conflicts, then test it against an equally bounded nonlearned retrieval method on new held out wording and worlds. Keep this failed final result unchanged. The current experiment is a working local component and chat integration, not a verified accuracy gain, total-resource efficiency result, or paper-ready Toruk conversational memory model.
