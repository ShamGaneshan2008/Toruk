# Integrated memory v1: bounded CPU protocol

Registered before new final inference. Pilot/development checks may identify
engineering errors. Freeze source, configuration, all data hashes, checkpoints
and this protocol after development and before reading final generated answers.
Retain every pilot and failure. Do not tune on final results.

Use six categories: correction, preservation after another key is corrected,
long recall, recent/local fact, absent fact, and conflicting unconfirmed claims.
The latter has no authoritative fact and should abstain. It is separate from the
previous selector experiment's explicit-replacement `conflict` category.

Use 384/96/96 training/development/final cases, generator seeds 4101/5101/6101.
World IDs and text histories/questions are disjoint. Rendering and question
families differ by split. The finite three-name/two-field/six-value symbol
inventory is shared intentionally; this is a binding/composition experiment,
not held-out entity/value vocabulary. Labels and authoritative event oracle are
offline only. Reference answers never enter runtime inference.

Use the fixed byte tokenizer, width 48, six float32 slots, 96 local byte tokens,
64 record tokens, 64 question tokens, at most 16 records, and 12 generated tokens.
Answers are greedy until EOS. Exact UTF-8 decoded-answer equality is required;
`?` is the only correct unknown answer. An unsupported answer is any non-`?`
generated answer on unknown/conflicting-claim cases. Record obsolete-value matches
on correction/recall cases separately, without assuming they prove retrieval.

Train ordinary and integrated variants from scratch with Adam 0.003, batch 16,
one CPU thread, matched batches and objectives. Run an 80-step pilot first.
The maximum planned optimizer budget is 800 steps per method/seed, seeds 31
and 47 if each pilot projects under five CPU minutes. Training reads train only.
Development is for checking learnability and choosing a single fixed step budget,
never for reporting a final gain. No paid compute, downloads, or large-model fit.
All pilot/train/eval processes retain wall time and process peak working set.

Compare ordinary local context, integrated memory, integrated with state zeroed
at answer time (distribution-shift ablation), and the existing frozen v2 selector
feeding ordinary local context as an unqualified diagnostic. The latter may retain
at most its existing two old plus three recent messages, then the same 96-token
suffix fit; account for its full history scan. It receives no extra LM training.

Store every query, expected answer, generated token IDs, raw decoded answer,
correctness, unsupported/obsolete matches, category, selected record IDs,
history/input and local/selected tokens, memory update token positions, decoder
steps, total forwarded token positions, state bytes, local bytes, latency,
peak process memory, parameters, training wall time, seeds and identities.
Total forwarded positions are a workload proxy, not FLOPs or energy. Peak process
RSS includes Python/Torch and loading checkpoints, and is not incremental tensor
allocation. Compare costs with quality; a smaller answer prompt is insufficient.

Report both seeds and category counts without treating reused cases across seeds
as independent observations. A candidate factual benefit requires higher exact
known-fact accuracy in both seeds; a correction/preservation claim requires both
categories to improve or match without added unsupported answers. A total-cost
claim additionally requires quality preservation, lower measured full-history
latency and peak memory in both seeds, and no increase in forwarded token work.
This small controlled study alone is insufficient for a research-paper claim.

Preserve all old results and loaders. Test causality, state influence/gradients,
bounded streaming, reset/branch behavior, save/reload, exact optimizer-boundary
resume, incompatible checkpoints/states and final-freeze enforcement. Run local
CLI/tests/lint/types/build/Node checks, report exact commands and exit codes, and
inspect exact-commit remote CI separately. Chat remains on its pretrained path.
