# Backbone qualification v1 protocol

Registered before any new candidate inference. This milestone qualifies only an
external answer generator on complete, plain-context references. It does not
rerun the 24 successor held-out questions, train anything, use a selector or claim
Toruk memory/selector superiority. The old frozen scores and artifacts are immutable.

Two candidates are fixed: HuggingFaceTB/SmolLM2-135M-Instruct at revision
12fd25f77366fa6b3b4b768ec3050bf629380bac (SHA-256
5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c), and
Qwen/Qwen2.5-0.5B-Instruct at revision 7ae557604adf67be50417f59c2c2f167def9a775
(SHA-256 fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe).
Both are Apache-2.0 per their pinned model cards/license. The versioned config
contains the direct official license URLs. Model/tokenizer/generation files and
runtime dependencies are sealed by SHA-256; local copies are verified, not trained.

Data is newly authored/generated, repository-owned synthetic reference material.
Development: 12 cases, seed 81711. Held-out: 30 cases, seed 81731. Each has factual
binding, correction, preservation, exact quoted literal, clear reference and
missing information. Held-out has five cases per category: 25 known questions
and five missing-information questions. No model generation is used to create data.
Known expected values, IDs and normalized question templates must be disjoint
between splits and from all 24 successor held-out cases. Shared generic reference
headers/instructions are disclosed. This is not proof of semantic/pretraining
independence. No old question or answer is fed to either candidate.

Both candidates receive the exact same explicit system instruction and a single
user message containing the entire reference and question. All needed evidence
is present. Tokenizer-only preflight must preserve the source text and fit the
entire system/reference within 512 tokens for BOTH native model chat templates;
otherwise registration fails. No truncation, retrieval, compression or memory
selection is permitted. Token IDs/native chat-template wrappers can differ, but
the role/content messages must be byte-identical. Label/alternative fields are
used offline only. The ordinary API defaults are not silently used as additional
model-specific system instructions.

Greedy decoding: CPU float32, two Torch threads, generation seed 81751,
64 output tokens, temperature request 0, top-p 1, one beam, repetition penalty
1.0 and KV cache enabled. A fresh common GenerationConfig overrides candidate
sampling/penalty defaults. Native EOS/pad IDs differ appropriately. Full effective
generation settings, prompts, input/output token IDs and answers are retained.
No candidate-dependent prompt tuning or settings changes after registration.

Development runs SmolLM then Qwen, including one exact first-case replay per
candidate. It validates execution, full evidence and deterministic generation;
its accuracy does not select or change questions/settings. Candidate identities,
settings and development outputs are frozen before held-out. Technically passing
candidates then run held-out once, in reverse order to reduce a fixed order bias.
Failed/resource-exceeding candidates remain failures; no retry or extra candidate
is permitted. Both held-out result sets use the same questions. Partial/missing
answers cannot qualify.

Primary scoring is frozen before inference. Known factual values require a
word-boundary match, no listed competing value, no explicit negation or
abstention. Exact quoted literals require whole-answer equality after outer
whitespace removal, retaining internal spaces/case/punctuation. Missing-information
replies accept explicit uncertainty including UNKNOWN, not known, not available,
not provided, do not know and cannot determine; mixed guesses/asserted code values
are rejected. These are bounded automated rubrics, not exhaustive semantic
judgment. Raw replies and any later interpretation remain separate from the
primary score. Known wrong listed values and unsupported-response proxies are
reported separately from proven fabricated facts.

A candidate qualifies only if all 30 held-out requests complete without errors,
all resource caps pass, overall accuracy is at least 18/30 (60%), AND known-fact
accuracy is at least 15/25 (60%). The latter prevents abstention credit alone
from satisfying factual quality. No per-category floor is claimed. Among
qualifiers select the one with lowest held-out process/controller CPU; this is
a fixed qualification choice, not model training or a population-superiority claim.
No confidence/generalization claim follows from a single small synthetic trial.

New stated budget: 6 GiB sampled worker-tree private memory (also checked against
worker OS lifetime peaks), 3 GiB study/input disk including both candidate files,
300 seconds per candidate/split, 30 seconds per request, 900 summed candidate-stage
seconds. These are new qualification limits; successor's prior 3 GiB cap remains
unchanged. The host has about 13 GB available RAM and 713 GB free disk; workers
are sequential. A 50 ms watchdog includes Windows venv descendants, CPU and memory,
kills the entire worker tree on a cap failure and retains failed/partial outputs.
No silent budget increase or paid job. Environment installation and engineering
verification are separate from timed candidate stages.

If a candidate qualifies, freeze its model, tokenizer, instruction/template,
generation identities and measured budget, and propose a separately registered
long-history recent/lexical/TORUK comparison using new data. Do not run that
comparison here. If none qualifies, publish the measured local tradeoff internally
and propose only the smallest justified next probe. Do not deploy, publish,
commit or push from this milestone.
