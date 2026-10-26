# Chat foundation protocol — frozen before model download or inference (2026-10-26)

Repository HEAD: `add917398efa061cc67b1b10aff3853acf3c526c`; branch `main`; existing tracked and untracked work is preserved.

## Choice and identity

The 12,112-parameter ordinary checkpoint learned only `abc `; the controlled recurrent smoke scored 0/12. A further tiny from-scratch run is not a credible conversational foundation. The candidate backbone is **HuggingFaceTB/SmolLM2-135M-Instruct**, pinned at Hugging Face revision `12fd25f77366fa6b3b4b768ec3050bf629380bac`, Apache-2.0, 134,515,008 parameters. Its BF16 `model.safetensors` is 269 MB; tokenizer/config files add about 4 MB. Source: [model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) and [repository files](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/tree/12fd25f77366fa6b3b4b768ec3050bf629380bac). This is a pretrained backbone, not a Toruk-trained language model.

The existing M6 `toruk-controlled-v1` recurrent checkpoint and byte tokenizer cannot be loaded as a SmolLM model or inserted into its hidden state. TORUK mode will use that frozen recurrent architecture only to score/select **verbatim** earlier turns for the backbone prompt. This is a prototype transfer with no validated relevance quality; BASELINE uses ordinary recent turns. No research checkpoint weights are changed. If a compatible M6 checkpoint or the backbone is unavailable, TORUK mode must report unavailable, never silently switch to baseline.

## Bounded resource and evaluation plan

- Download only the pinned safetensors and tokenizer/config files. Estimated added disk below 600 MB including cache/temporary copies; no dataset download. No model training or paid API.
- CPU only, two Torch threads, at most 20 messages / 8 KiB history, 512 backbone input tokens, 32 generated tokens, one request at a time. Expected resident RAM below 2 GiB, with a hard operational stop if observed peak exceeds 3 GiB. A 60-second proxy deadline bounds a request; evaluation is wrapped in a 15-minute process timeout. These are estimates/limits, not prior measurements.
- Fixed author-written prompts, stored before evaluation, cover basic instructions, factual questions, multi-turn reference, correction, unrelated-fact preservation, long-context retrieval, and unknown-answer behavior. No tuning on their outputs. Greedy generation for paired modes; temperature 0 means greedy, and positive temperature/top-p are exposed for interactive use only.
- For each case run identical messages once in each mode against the same pinned backbone. Report exact/criterion-based quality, selected prompt tokens, generated tokens, latency, errors, and whether the Toruk selector was used. A token-efficiency claim requires lower selected tokens **and** no loss of answer quality or higher failure rate. If weights/dependencies cannot be obtained within the bounds, retain the failure and mark quality/efficiency inconclusive.

## Planned commands

From Windows PowerShell in the repository root: install optional chat dependencies with `.\.venv\Scripts\python.exe -m pip install -e '.[chat]'`; download the pinned model with the documented bounded download command; run focused tests, `scripts/evaluate_chat_foundation.py`, `scripts/smoke_vercel_local.py`, `scripts/verify.py`, and `git diff --check`. Each actual command and outcome will be appended below after execution.

## Results

The pinned six-file download succeeded: 271,170,520 bytes, weight SHA-256 matched; installed chat dependencies include Transformers 5.20.2 and Safetensors 0.8.0. The first one-turn probe failed because Transformers 5 returned a mapping from `apply_chat_template`; the adapter was corrected to use `return_dict=True` and `input_ids`. Its same bounded rerun answered `Hello!` in 3 generated tokens. The M6-assisted probe loaded the frozen recurrent checkpoint and produced a reply without changing weights.

The first seven-category paired run completed in 17.4 seconds with 0/7 strict-format answers for each mode, 710 versus 532 selected tokens, and zero runtime failures. See the execution correction below. The retained rerun, with unchanged questions/settings, took 18.749 seconds: again **0/7 versus 0/7**, zero failures, 710 versus 532 selected tokens, 103 output tokens in each mode, and 6,543 versus 6,435 ms aggregate request latency (BASELINE versus TORUK). Peak observed Windows private bytes were 1,462,267,904, below the 3 GiB stop. The pretrained backbone answered the planet and long-context code factually, but did not follow their short-output formats; the other tasks include substantive failures. These are [raw retained outputs](../../artifacts/chat-foundation-001/eval-results.json), not evidence of useful chat or a reliable memory advantage.

The local browser-style proxy smoke succeeded: both modes used the same pinned model, TORUK selected 119 rather than 297 prompt tokens for the long-context probe, both generated `The vault code is LIME42.`, and a backend outage returned HTTP 503 without a fake answer. This single successful retrieval does not establish general token efficiency. Final verdict: **efficiency not verified**.

### Recorded execution correction before retained rerun

The first paired execution returned 0/7 for both modes and a misleading `efficiency_verified: true`: equality at zero quality is insufficient evidence of preserved answer quality. Its script output path also collided with `scripts/check.py`'s evidence JSON, so the raw per-case result was overwritten. The wrapper log retains the aggregate 0/7 outcome. The verdict rule is amended **after seeing that outcome** to require at least one correct answer in each mode, in addition to no quality loss, no additional failures, and fewer selected tokens. This is a conservative reporting guard, not a prospective success criterion. The frozen questions, weights, selector and generation settings remain unchanged; the retained rerun will use separate filenames. No efficiency claim from this evaluation can be considered preregistered.
