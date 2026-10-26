# Toruk chat release candidate — preregistered prototype protocol v2

Recorded before v2 questions are run (2026-10-26). Repository `C:\Users\susee\VScode Project\Toruk`, branch `main`, HEAD `add917398efa061cc67b1b10aff3853acf3c526c`; existing tracked and untracked work is preserved. The earlier seven-case result (0/7 strict-format answers in each mode) is a lead, not a result for this new set. Its prompts and answers are excluded from v2.

## Paired intervention

Backbone: `HuggingFaceTB/SmolLM2-135M-Instruct`, revision `12fd25f77366fa6b3b4b768ec3050bf629380bac`, local safetensors SHA-256 `5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`, Apache-2.0 per the [model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct). Frozen Toruk selector: `artifacts/m6-validation-001/recurrent/checkpoint.pt`, format `toruk-controlled-v1`; record its SHA-256 in results. Baseline and Toruk use identical backbone, tokenizer, built-in chat template/system instruction, 512-token prompt ceiling, greedy decoding (temperature 0, top-p 1), and 32-output-token cap. Only selection of conversation turns changes. BASELINE takes recent turns fitting the cap. TORUK ranks earlier turns with the frozen recurrent summaries, keeps at most two older turns plus the latest three, then applies the same cap. Neither model is trained or updated by this evaluation.

Dataset: `configs/chat-release-eval-v2.json`, 20 author-written examples, two in each of ten categories: instruction following, factual questions, multi-turn reference, user-provided facts, corrections, unrelated-fact preservation, long-context retrieval, irrelevant-history handling, unknown answers, and contradictory/ambiguous context. These are separate from M6 controlled-world training and the earlier seven-case chat evaluation. The fixed file contains message IDs, expected facts, accepted answer patterns, forbidden patterns, and exact-output rules. All cases run in both modes; no exclusions for bad answers, errors, or timeouts. The fixture SHA-256 is recorded by the runner.

Frozen fixture SHA-256: `86e31ab8afccb0e7ab88817fc11b7be4585a7d261c3d99f93eef60540c63a0c6` (20 cases, two per category, checked before any v2 model run).

Scoring is deterministic: normalize whitespace/case; an exact-output case must match one accepted string exactly. Other cases require at least one listed answer phrase, with no listed forbidden phrase. This binary answer-quality rule is primary. The same fixed fields identify factual correctness and correction handling for relevant categories. On unknown or ambiguity cases, an unsupported-answer flag is set when the response lacks one of the fixture's permitted uncertainty phrases or contains a forbidden fabricated value. Errors and timeouts count as quality failures. Per-case raw outputs remain in local artifacts; server logs retain token counts and message IDs but no message text.

Primary success criteria, fixed before running v2:

- Mean TORUK selected input tokens at least **35% lower** than BASELINE, measured on all 20 paired cases.
- TORUK overall answer quality no more than **5 percentage points** below BASELINE.
- No TORUK regression on either corrected-information case.
- No increase in unsupported answers on unknown/ambiguous cases.
- To call either mode meaningfully conversational, its answer quality must reach at least **60%** on this small set. Quality preservation is **inconclusive** if BASELINE is below that floor, even if both scores are equal.
- Every example and failure is retained. Token reduction alone does not support a quality-preserving efficiency claim.

Secondary measures: full input tokens before selection, selected tokens, output and total tokens, latency including selector work, selection identifiers, memory flag, failure rate, per-category quality, paired token-reduction distribution, and a deterministic 2,000-resample paired bootstrap interval for the mean token-reduction and quality difference (seed 23). These intervals describe this fixed prototype set only; they do not imply population generalization. A single deterministic decoding seed is used, so no seed-variability estimate is claimed.

Limits: CPU only, two Torch threads, 20 messages/8 KiB per request, 512 prompt tokens, 32 generated tokens, sequential paired calls, 15-minute hard evaluation timeout, and a 3 GiB measured private-memory stop on Windows. Python 3.14.6, Torch 2.14.1+cpu, Transformers 5.20.2, Safetensors 0.8.0, Node 24.19.0 were observed locally. The separate inference host's availability and cost are outside this local protocol.

## Execution log

The frozen fixture passed structural/rubric tests (3 passed) before the model run. The one paired run used distinct raw and wrapper filenames:

```powershell
.\.venv\Scripts\python.exe scripts/check.py --timeout 900 --output-dir artifacts/chat-release-v2 evaluation -- .\.venv\Scripts\python.exe scripts/evaluate_chat_release_v2.py --fixture configs/chat-release-eval-v2.json --backbone-dir artifacts/chat-foundation-001/backbone --selector-checkpoint artifacts/m6-validation-001/recurrent/checkpoint.pt --output artifacts/chat-release-v2/raw.json --report docs/research/chat-release-v2-results.md
```

The command passed in 48.84 seconds wall time; the wrapper log, source fingerprint and raw answers are retained in `artifacts/chat-release-v2/`. The pinned selector SHA-256 was `479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d`; peak observed Windows private memory was 1,475,166,208 bytes. BASELINE: 6/20 quality, 1,818 selected and 254 output tokens, 15,259.708 ms aggregate latency, 3 unsupported answers, 0 errors. TORUK: 6/20 quality, 1,546 selected and 278 output tokens, 15,552.248 ms aggregate latency, 3 unsupported answers, 0 errors. Reduction was 14.96%, below 35%; both modes were below the 60% meaningful-quality floor. Correction was 1/2 in each mode. The preregistered primary criterion **failed**. No questions, thresholds, scoring rule, context budget, backbone weights, or selector weights were changed after viewing results. See the [human comparison and failure table](chat-release-v2-results.md).
