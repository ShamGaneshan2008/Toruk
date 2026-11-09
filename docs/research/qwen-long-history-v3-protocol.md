# Qwen long-history v3: one development-only selector intervention

This is an adaptive development diagnostic, designed after inspecting all seven
v2 development outputs. It is not a new held-out experiment, independent
replication, or evidence of a research win. V1 remains BLOCKED with zero held-out
answers; v2's sealed proposal and evidence remain unchanged. No held-out output
is opened or generated. No commit, push, deployment or publication.

## Observed diagnosis and the single change

V2 TORUK omitted required sources in correction, distractor, exact-copy,
preservation and reference cases. It selected acknowledgements in three of
these and archive logs in the others. In distant recall, m0 and its answer were
retained but Qwen returned the ledger ID, whereas lexical's different selected
context produced the correct location. Missing information was answered UNKNOWN
correctly. Saved sources are in chronological order and are rendered verbatim;
no observed source corruption, fit eviction or ordering reversal explains the
six failures. The absent exact quotation is a selection failure, not evidence
that the decoder cannot preserve its double space. Prompt sensitivity may
contribute to distant recall; internal causal attribution is not proven.

Introduce one candidate-admission gate: an older turn must be a USER turn and
share at least one term from the unchanged lexical-v1 query tokenizer/stopwords.
Only admitted turns compete for the existing recurrent/cosine top two. Preserve
the latest three messages, source order, full streaming summaries/state updates,
same two-slot maximum and 512-native-token whole-turn fit. No category, case ID,
expected value, required index, negation parser or answer extractor is supplied
to selection. No new correction rule, prompt instruction, order change, decoder
or output repair. This gate can reject useful paraphrases or assistant-authored
facts and can admit misleading overlaps; report those limitations.

The gate is an explicit hybrid of lexical admission and learned ranking, not
Toruk-only semantic retrieval. Lexical-v1 remains the transparent primary
comparator. Do not call reproducing lexical's evidence a learned advantage.

## Identities and frozen sources

Work/output root: C:/Users/susee/VS_CODE_PROJECT/Toruk. Read-only old inputs:
D:/Toruk. Preserve both checkouts' starting statuses and old evidence hashes.
Require v2 proposed-freeze SHA-256
84f23a07cd78935536b4586885bfb9d20bc78ae7d964a6a2d1ffffc8ccc4fec7 and all
its registered input/output bindings before running a model.

Qwen/Qwen2.5-0.5B-Instruct revision
7ae557604adf67be50417f59c2c2f167def9a775, safetensors SHA-256
fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe.
Keep every tokenizer/model asset from qualification, the D-drive source/worker
and Python 3.12.14, Torch 2.15.0+cpu, Transformers 5.22.2, Tokenizers 0.23.3,
Safetensors 0.8.0 and Psutil 7.2.2. Weights are unchanged. Successor checkpoint:
f38f35b168b3bdaddb7caff8f6ff9bc7cb67694b77095cb52bef5bf63af65f49.
No new checkpoint is trained. A separate selector-identity.json binds the old
weight hash, v3 gate source and combined runtime identity; do not assign the new
identity to old weights or modify the historical checkpoint.

Seal source, config, protocol, tests, development data, prompt IDs, per-case
baseline diagnosis and selector identity in registration/source ZIP before v3
candidate answers. Keep all raw outputs and failures in fresh exclusive files.

## Cases, fairness, scoring and evaluation order

Use byte-identical copies of v2's seven development cases only: distant fact,
correction, distracting competing record, exact quotation with internal double
space, unchanged flower following a folder-shade update, reference, and absent
password. Before/after/lexical receive identical questions and histories. Declare
the intentional overlap with v1/v2 dev; create no new cases or training set.
Use the sealed dev-only IDs as an allowlist and reject any additional case.
The held-out file is not copied or parsed; previous frozen bindings may be
verified by hashing without inspecting semantic contents or answers.

Fresh sequential workers: BEFORE (unchanged successor selector), LEXICAL
(unchanged lexical-v1), AFTER (admission-gated successor). Seven cases plus
first-case replay each: 24 charged generations total. Before/lexical must
reproduce v2 source indices, prompt IDs, generated IDs, answers and scores.
Use saved v2 full/recent rows for context only; do not rerun those arms or present
their old costs as a matched fresh v3 comparison. No favorable model retry and
no second selector variant after seeing new outputs. No held-out action exists.

Use identical qualification system instructions, native Qwen chat template,
chronological Reference/Question/Answer wrapper, whole-turn 512-token prompt fit,
float32 CPU/two threads, seed 81751, greedy one beam, temperature request 0,
top-p 1, repetition penalty 1, cache, and 64-token answer maximum. Copy evidence
verbatim; do not add expected values. Use unchanged v1/qualification scorer,
including literal whole-answer equality ignoring outer whitespace only.
Exact-copy and preservation are separate from overall accuracy. Every arm gets
the same selection-trace serialization; count its overhead in selector timing.

## Bounds, interruption policy and resource accounting

180 wall / 360 CPU seconds per arm, 540 wall / 1080 CPU cumulative, 30 wall
seconds per question, 6 GiB worker-tree private memory, 3 GiB study plus fixed
model/checkpoint inputs. Acquire/restore a process-scoped Windows idle-sleep
request. Reuse hash-bound v2 monitoring: approximately 50-ms samples, durable
one-second heartbeats, UTC/perf/awake clocks; invalidate >5-second monitor gaps,
>2-second elapsed/awake divergence or backwards clocks. Charge real elapsed
time including sleep, stop on first failed arm, terminate child trees, preserve
partial work. Five logged 10-ms PermissionError file-read retries only; zero
model/request retries. Durable started-without-completed output means incomplete,
never PASS. Further attempts require a new registration and retained costs.

Record per-case and aggregate selected prompt/output tokens, evidence/indices,
gate candidate reasons/cosines/term scan bytes, recurrent byte forwards and
updates, full-history/fitting BPE work, selector CPU/wall, generation/request
CPU/wall, setup and complete stage CPU/wall and memory. Charge replays but exclude
them from seven-case accuracy. Report both seven-case and eight-request costs.
Process CPU includes sampled descendants and controller, supplemented with final
worker lifetime values; missing final CPU is a lower bound. Sampled memory can
miss peaks and RSS may double-count shared pages. Timer zero is below resolution.
Do not compare old and fresh wall times as a selector effect; fixed-order cold
cache effects and host load limit single-trial cost interpretation.

No new training. Disclose inherited successor profile/training 14.578125 CPU /
17.6733196 wall seconds separately; its peak RAM remains unknown. Both recurrent
arms share the same inherited weights; no amortized total-efficiency claim on
these seven adapted development questions. Preserve all prior failures/sunk
costs in their original ledgers. General engineering checks and offline audits
are separate from timed model comparison and do not access Qwen held-out data.

## Predeclared development diagnostics and stop

Technical: complete all 24 requests within limits, all replays deterministic,
before/lexical reproduce their v2 prompts/answers, frozen identities/preservation
pass, no new runtime errors. Diagnostic targets: after retains all six known
required-source sets, improves over before's 1/7, loses no question versus fresh
lexical, copies the exact plate and preserves the flower. Report each target
independently whether passed or failed, with exact before/after answers, prompt
tokens and selector CPU/wall for each question. No post-output case, scorer,
gate or cap edits. Remaining failures with retained evidence belong to decoder
behavior in that prompt; omitted evidence is upstream selection failure. Order,
rendering and irrelevance are audited separately, not asserted as causal facts
without an intervention that isolates them.

Stop and report after development. Even 7/7 is development fitting on known
cases and cannot establish generalization, quality-cost superiority, or a
research win. Future unseen testing would require another authorization and
registration; nothing here authorizes opening held-out answers.
