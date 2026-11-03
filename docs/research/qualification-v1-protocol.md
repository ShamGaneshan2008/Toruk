# Independent qualification v1 — 3 November 2026

This protocol evaluates existing frozen checkpoints; it does not retrain or tune
them. The integrated v1 blocker is resolved: four real checkpoints, optimizer
records, a sealed evaluation and same-runtime retraining parity exist. Its poor
transfer is retained. Prior final answers informed this hypothesis, so the old
final split is historical evidence only. New answers must not guide this run.

## Hypothesis and decision rules

Primary metric: per-world exact generated-answer accuracy, equally weighted over
seven categories and three evaluation seeds, at the ordinary history load.
Multi-fact worlds require both independently generated answers to be exact.
Hypothesis: learned memory improves this metric over both recent context and a
fixed lexical selector. Require positive paired 95% world-cluster bootstrap lower
bounds against both controls and positive differences at both training seeds.
Minimum useful quality: >=80% overall AND known-world accuracy, >=70% in every
category, and <=5% unsupported unknown/ambiguous answers, at each training seed.
These are qualification thresholds, not a retrospective claim about old results.
Failing quality prevents every quality-preserving efficiency claim, including ties.

Correction/preservation claims additionally require no category regression and no
unsupported-answer increase against recent and lexical. Total-cost efficiency
requires passing quality, fewer forwarded token positions, lower full-request
latency and lower sampled process RSS at both seeds. Token reduction alone is a
separate descriptive result. State-size bounds alone do not establish efficiency.
PASS means these rules were met; FAIL means measured requirements were violated;
INCONCLUSIVE means missing evidence, incompatible variants, or uncertainty.

## Fixed models and data

Use existing integrated-study ordinary and integrated checkpoints, training seeds
31 and 47, each trained 800 steps / batch 16 / Adam 0.003 on the old training
worlds only. Match byte tokenizer, width 48, six allocated slots, 96 local tokens,
64 record/query tokens, 12 greedy output tokens, CPU float32 and one Torch thread.
The ordinary decoder is shared exactly by recent/lexical/learned selectors within
each seed. Integrated uses its separately trained matched architecture: training
budget and seed match, but weights and effective computation differ. Do not claim
the ordinary and integrated checkpoint are the same language model weights.

Final data: seeds 7101, 7102, 7103; eight worlds per category per seed; categories
correction, preservation, distant recall, ambiguity, distraction, multi-fact,
unknown. Each world starts with three distinct keys, corrects one, and ends in
four irrelevant-key writes. Unknown/ambiguous queries use an absent fourth key;
ambiguity adds two unauthoritative claims. Multi-fact asks the revised and
preserved keys separately; pair scoring requires both. Distant recall queries
the third initial key, which has no correction. Correction and distraction share
the revised-key task with independently drawn worlds; their category names do
not identify independent causal effects of distraction. New text uses `Fact`,
`Amend`, `Rumor` and `Give ... for ...` templates, disjoint from all old
train/dev/final families. The finite trained entity/value vocabulary is shared.
No broad language or unseen-entity generalization claim is possible.

Stress loads add 8 or 32 irrelevant writes to each base world. Reuse the world
identity across loads; these are repeated measures. Use the same first four
irrelevant writes at all loads; extra load is the only changed factor. Final
data must have unique histories/query bundles and no overlap with historical
training/development/final examples. Seal data, protocol, evaluator, dependencies,
checkpoint bytes and selector before generation. Store UTC freeze time. Never
select hyperparameters or epochs from these final outputs.

## Baselines and interventions

1. Recent: all turns ingested, last 96 byte tokens retained.
2. Lexical: rank older turns by count of shared lowercase alphanumeric words
   with the query (no stopword list); tie favors later turns; retain top two older
   turns plus last two history turns, then apply the same 96-token suffix.
3. Learned: frozen v2 selector, two older turns plus the same two recent history
   turns (third recent message is the query); same suffix. This is an unqualified
   diagnostic: its training distribution differs from the tiny decoder's.
4. Position: remove learned relevance scoring only, choose the two latest eligible
   older turns regardless of threshold; same candidate and retention limits.
5. Integrated: learned history updates and decoder state reads.
6. Zero: integrated state zeroed only at answer time.
7. No correction updates: bypass state updates on raw `Amend ` records only;
   still consume them into the identical local suffix. This explicit marker
   intervention is not a learned correction detector or an oracle-value lookup.
8. No preservation: zero the entire state before each update; keep local suffix.
9. Half capacity: zero slots 3–5 after each update and before answering; keep all
   allocated parameters and tensor bytes. Report 576 effective retained bytes and
   1,152 allocated bytes. This is inference masking, not a smaller trained model.

Only the named factor changes in each intervention. Zero/capacity/update ablations
shift the training distribution; they cannot identify a causal training advantage.
No old controlled M6 weights may be substituted. Missing checkpoints are reported
as unavailable. Pretrained Qwen/Ollama are chat components, not comparable trained
Toruk decoders; use separate local chat smoke evidence, not pooled accuracy.

## Scoring, uncertainty and accounting

Runtime receives texts and queries only. Gold event metadata is used solely by
the generator/scorer. Score UTF-8 decoded strings exactly, with no stripping,
case folding or synonym repair. Only `?` is correct for absent/ambiguous evidence;
any other answer there is unsupported. Store every raw answer and token ID.
Ambiguous answer phrasing is recorded as incorrect with its raw text; a reviewer
may append a separate adjudication file but cannot change the primary scorer.

Report counts per category, training/evaluation seed and history load. At load 0,
bootstrap 2,000 times, RNG seed 9301, resample world IDs within each evaluation
seed/category; preserve both training seeds and paired methods in each cluster.
Report percentile intervals for accuracy and paired differences. These intervals
are conditional on two trained checkpoints; they do not estimate population
training-seed uncertainty. Report min/max over training seeds separately. Stress
results are descriptive and receive no multiplicity-adjusted significance claim.

For each query, rebuild history from scratch for every method, including the two
queries of a multi-fact world. Count those repeated reads/updates twice. Store
history bytes/tokens scanned, selected record IDs, record IDs contributing any
suffix bytes, actual local+query tokens, update token positions, generated IDs,
forwarded positions (update+local+query+decode), allocated/effective state bytes,
update cells and response latency from before selection to after decoding.
Forward positions exclude tokenization, ranking and matrix/slot arithmetic: they
are a proxy, never FLOPs or total compute. Include all input scans separately.
Measure fresh subprocess wall time, process high-water RSS, and RSS sampled every
5 ms across checkpoint loading/evaluation, plus before/after each world. Report
sampling limitations and per-method process peaks, not incremental state claims.
Retain historical training-loop cost; no new training cost for frozen replay.

Run methods sequentially, rotate method order by seed, cap each subprocess at
180 seconds and sampled RSS at 2 GiB. Keep failures and logs, with no silent retry
or replacement; failed/missing cells block a complete qualification verdict.
Run tests before final inference. Any evaluator correction after freeze needs a
new version; keep failed evidence. Package exact argv/exit codes, environment,
Git revision and initial/final status, hashes, source copies, analysis, examples,
checks and an outline only. Weights/private notes remain ignored and local.
