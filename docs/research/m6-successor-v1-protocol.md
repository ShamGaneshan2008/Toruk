# M6 successor v1: frozen experiment protocol

This is a new experiment, authorized on 8 November 2026. Historical M6 is
NOT REPRODUCIBLE; its expected hash and archived outputs are unchanged. No
historical selector or published evaluation question is substituted into this run.

The hypothesis is that a newly fitted small recurrent selector preserves factual
answer quality from longer histories while lowering complete measured CPU and
wall work against both recent-context and simple lexical retrieval. The selector
is the existing Toruk recurrent summary/cosine mechanism, with new random
parameters trained by the unchanged controlled QA trainer. It is not a new memory
algorithm or a backbone fine-tune. Twelve steps on controlled synthetic worlds
are a severe training/data-domain limitation, disclosed regardless of outcome.

Before training, `register` seals config, source, datasets, backbone/tokenizer
files and actual dependency versions in registration.json. source.zip preserves
exact consumed code/data bytes. The registered config is
configs/m6-successor-v1.json. Training uses seed 8041 and world seed 8031;
the two-step execution profile uses seed 8042. Width 32, two layers, four heads,
64 byte positions, four state slots, 12 AdamW steps, LR .003, QA + .1 history LM,
CPU float32 and one thread. The new checkpoint retains toruk-controlled-v1 with
a new experiment sidecar and actual byte SHA-256. It must differ from historical M6.

All generators are the same external SmolLM2-135M-Instruct revision
12fd25f77366fa6b3b4b768ec3050bf629380bac, weight SHA-256
5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c.
Its pinned tokenizer/template/generation config are sealed. Inference uses CPU
float32/two threads, greedy temperature 0/top-p 1, 512 prompt tokens, 32 generated
tokens and the unchanged historical SmolLM template, equally in every method.
The locally copied backbone is hash-verified; it is not a Toruk selector.

Development: six newly authored/generated cases, seed 8051. Held-out: 24 cases,
seed 8061, four each for distant fact, correction, preservation, exact literal,
clear reference and missing evidence. They have disjoint IDs, factual values and
task-bearing templates. Exact value copying is excluded literally from selector
training text. Common uncertainty instructions/weather scaffolding remain shared;
this is a small synthetic transfer test, not unseen-domain or independent-human
validation. The value pools and generator are fixed before any answer is observed.
Each history has 18 weather distraction pairs. More than 20 messages are accepted
only through the research backend; this does not expand the web API's limits.

Recent keeps all turns before the same whole-turn 512-token fit. Lexical-v1 keeps
two query-overlap older user turns plus the latest three. Toruk uses its new
recurrent summaries, at most two older turns plus the latest three, before the
same final fit. The existing mechanisms, including their overhead, are measured.
Only role/content reaches the generator; scoring labels are offline.

Order is lexical, Toruk, recent, each in a fresh worker per split so process peaks
are not shared cumulative peaks across methods. One deterministic first-case
replay per method is included in the development smoke and fully charged. All
three must complete technically before freeze.json binds the checkpoint and
smoke outputs. Smoke accuracy does not select a change or suppress the held-out
run. Then the held-out set is generated once per method; started markers prevent
retries or overwrite. Failed attempts and partial outputs remain retained.

Primary accuracy uses token-boundary value matching, rejects obsolete values,
requires full exact equality for literal cases, and a frozen uncertainty phrase
rubric for missing evidence. Raw answers are retained. Unsupported-abstention and
stale-value flags are proxies, not exhaustive semantic false-assertion counts.
Evidence retention, category scores and representative failures are secondary.

All success conditions must pass against BOTH baselines: each candidate/baseline
at least 60% correct; Toruk at most five percentage points worse; no additional
unsupported/stale proxy flags; at least 10% lower total measured CPU AND wall time.
Totals include each method's cold startup, development smoke/replay and held-out
workers. Toruk additionally pays all new two-step profiling and 12-step training.
Controller CPU is included. Common environment installation, identical backbone
copy and data registration are separate shared setup costs, not attributed as a
saving. Per-request online costs are also reported separately. Token reduction
alone cannot pass. No confidence or population-equivalence claim follows from
this single small trial.

Record raw prompts/token IDs, generated IDs, selected text/IDs, per-case scores,
full-history and fitting tokenization positions, actual backbone forwards,
selector byte positions/calls, state bound, CPU/wall time, and separate per-method
sampled RSS/private-memory peaks. Selector byte and backbone BPE positions are
not interchangeable; these are work counters, not FLOPs or energy. State is reset
per request; the 512-byte state excludes model/history/cache/process storage.

Limits: 110 seconds per profile/training worker, 180 seconds per evaluation
worker, 900 seconds cumulative experiment workers, 3 GiB sampled private memory
per worker, 3 GiB experiment disk excluding the environment. A parent watchdog
samples every 50 ms and kills a worker on a cap violation. It retains failures
and prevents favorable retries. No paid compute, deployment, publication, commit
or push. Verification's existing tiny fixtures remain separate from this study.
