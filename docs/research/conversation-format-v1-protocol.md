# Owned conversation framing pilot v1 — frozen 5 November 2026

Starting commit: `265f88137f41b5a646ec56c232b4bd1b49dadd38`.
The pre-existing dirty tree is retained in
`artifacts/conversation-format-v1-20261105/starting-status.txt` and
`starting-diff.patch`; those edits are outside this experiment.

## Diagnosis and hypothesis

The prior conversational pilot was NOT_RUN. Its readiness diagnostic measured
0/25 exact, 24/24 capped malformed continuations and one 512-byte input error.
Fresh historical inference reproduced all 768 answers in 16 conditions before
implementation. Fresh readiness inference is retained separately. Categories:
instruction 0/3, factual 0/3, corrections 0/3, distant 0/3, exact strings 0/3,
math 0/3, uncertainty 0/3, refusal-history math 0/4. Only nine distinct outputs
across 24 accepted prompts; zero repeated word trigrams at the short cap.
Examples: instruction -> ` sun.\nNote 2: wi`; unknown ->
` is red.\nNote 2:`; correction -> ` swiswer Answer `.

The selected weakness is failure to produce a completed assistant response.
The inherited model trained on synthetic notes rather than role-formatted
conversation. Role syntax is a data/distribution mismatch; absent conversational
learning also prevents instruction following. This evidence cannot isolate
memory's contribution to failed factual recall. The full-history input rejection
is an inference-interface limit, not a memory result. Short output caps and scoring
raw JSON as content are additional diagnostic limitations.

Hypothesis: the unchanged 56,064-parameter memory-on architecture, trained from
random initialization on the existing audited 64-conversation training split,
will learn response framing and EOS better than the historical checkpoint and
an equally scheduled nonconversational-data control. This is a data intervention,
not a new memory algorithm or a fine-tune of the exposed old checkpoint.

## Fixed design (no held-out tuning)

- Candidate: existing 64 original synthetic conversations, all-target next-token
  loss, existing role JSON lines, no new training examples or third-party data.
  Preserve source manifest permission/license information; no broader project
  license is inferred. Existing conversation split has zero held-out answer matches.
- Control: existing filtered 191-document pretraining corpus, further filtered
  against new reserved complete answers. Same random seed, architecture, optimizer,
  batch and steps. Different document lengths mean actual target counts differ.
- Both start at seed 31 from random weights. AdamW LR .003, batch two, 512 steps,
  one CPU thread, float32. Candidate saves at step 256 and resumes to 512 under
  the existing exact data/config/RNG checkpoint contract; no weights-only transfer.
- Development: existing 16 development cases. Used for reporting only, no selection.
- Primary held-out: 24 deterministic renamings of the existing test templates,
  seed 11301, Eperson/Evalue/Eold -> Hperson/Hvalue/Hold, E/Q -> H/Q;
  uncertainty target `Unavailable.`, math/refusal operand 9 and answer 18.
  IDs prefixed `fresh-`. These are unseen strings, NOT independent templates.
  Audit canonical split duplication and complete reserved-answer exposure before
  fitting. Generated datasets and hashes sealed before training.
- Regression: the published 25 readiness prompts including the complete recorded
  refusal conversation. Already exposed diagnostic, never claimed fresh.
- Conditions on identical prompts: historical checkpoint, new control, candidate,
  candidate with actual memory reads removed, candidate with updates removed,
  separately labeled local manifest-verified Qwen backbone. No external answers
  enter training. Development runs owned conditions only.
- Greedy decoding, 32 native output tokens for every condition (owned bytes versus
  Qwen BPE); native templates; unchanged 512-byte owned input limit. Record errors,
  never truncate to hide rejection. New cap is fixed before fitting and allows
  quoted values plus newline/EOS to fit; old 16-token replay remains separate.
- Parse one complete JSON string followed only by whitespace for owned content
  scoring. Preserve raw bytes/IDs; report raw exact and decoded content exact.
  An unterminated or trailing-junk JSON response fails framing. External responses
  are native content, not role-line JSON. No constrained decoding or answer rules.

## Caps and gates

Each fit: at most 393,216 optimized byte/EOS targets, 120 s training wall, 512 MiB
RSS, 16 MiB checkpoint output. Combined fits at most 786,432 targets / 240 s.
Entire experiment: 64 MiB disk, 600 s excluding prior replay and repository checks;
owned RSS 512 MiB, external RSS 4 GiB; no GPU, paid API or job. Enforce deadlines
per optimizer/request boundary, outer timeout 620 s; not an OS memory sandbox.
No hyperparameter sweep, retry with alternate settings or held-out model selection.

Framing success: candidate improves valid framed output AND EOS termination by
at least 0.50 absolute versus BOTH historical and new control on primary held-out.
Content exact may lose at most one answer overall and in any category versus either
control; unsupported-unknown proxy, invalid UTF-8 and repeated-trigram counts may
not increase. Report per-category counts, unknown fragments separately from
interpretable false assertions, stale values, errors, repeated outputs, latency,
CPU, prompt/output tokens, actual owned positions, training resources and disk.
No hardware energy/FLOP or dollar savings claim; local measured time is cost proxy.

Chat integration additionally requires >=80% content exact overall, >=60% every
category, zero unsupported unknown answers, zero refusal errors/input errors or
invalid outputs, >=95% EOS termination, clean lineage, and passing framing and
regression gates. Apply to BOTH primary and published regression suites. Failure
retains the checkpoint and raw negative result; API/UI/defaults stay unchanged.
General-purpose chatbot qualification is outside this experiment.

Source/config/data/checkpoint hashes and the training freeze bind evaluation.
Evaluate held-out once after final checkpoint freeze. Record all attempts.
Use existing resume tests plus actual 256->512 pilot resume; no new checkpoint
format or relaxation of historical runtime validation.
