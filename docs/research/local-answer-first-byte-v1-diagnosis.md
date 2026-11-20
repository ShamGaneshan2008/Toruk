# Local-answer first-byte diagnosis v1 — saved evidence only

20 November 2026. Root `D:\Toruk`, branch `main`; starting HEAD
`301dd9edbf12403aa97e5013247d5b1f33be0746`, status contained only the existing
local-answer study/accounting work. Reviewed its283 inventory entries and report
tables/examples, then committed exactly280 non-checkpoint files including the
inventory as **`bb27b57d82f0185c9cc4f100b3afffd2d3e9f020`**. No push. Four
checkpoints remain local/ignored as specified by the record. The failed training
gate and absence of development evaluation remain unchanged.

**Most supported finding:** ordinary947 has a city first-byte decision failure:
it never emits `m` for any city answer, despite balanced supervision. There is
no verified tokenizer, delimiter, mask, batch-lane, checkpoint or scorer defect.
Optimization/order interaction is plausible; the saved evidence does not identify
its cause or establish a confidence collapse. No training, forward pass, answer
generation, held-out access, production edit or v1 score revision occurred here.

## All16 failures

[Machine audit](../../artifacts/local-answer-first-byte-v1/audit.json) records each
full prompt/native ID stream, mask reconstruction, batch slots, contrast exposure,
checkpoint metadata and all three passing comparisons. [Offline auditor](../../scripts/audit_local_answer_first_byte.py).
Original [raw predictions](../../artifacts/local-answer-dev-v1/stages/generate-train-947-ordinary/predictions.jsonl),
[loss records](../../artifacts/local-answer-dev-v1/stages/loss-train-947-ordinary/losses.jsonl).

Bytes are ASCII/UTF-8; IDs are byte+3. **NR** means neither gold/predicted
first-byte probability nor rank was recorded. Positions are zero-based.
`y/local` means first-answer target index / causal local-logit index. These
positions are reconstructed from saved bytes and sealed code, not a saved mask dump.

| Case | T | Expected byte /ID | Predicted byte /ID | P/rank | y/local | Prompt ends | Malformed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train-004 | A | `m`109/112 | `l`108/111 | NR | 53/21 | `uvo city?=` | yes |
| train-005 | A | `m`109/112 | `l`108/111 | NR | 53/21 | `uvo city?=` | yes |
| train-006 | B | `m`109/112 | `l`108/111 | NR | 53/21 | `city uvo?=` | yes |
| train-007 | B | `m`109/112 | `l`108/111 | NR | 53/21 | `city uvo?=` | yes |
| train-024 | A | `m`109/112 | `s`115/118 | NR | 53/21 | `pex city?=` | no |
| train-025 | A | `m`109/112 | `s`115/118 | NR | 53/21 | `pex city?=` | no |
| train-026 | B | `m`109/112 | `s`115/118 | NR | 53/21 | `city pex?=` | no |
| train-027 | B | `m`109/112 | `s`115/118 | NR | 53/21 | `city pex?=` | no |
| train-048 | A | `s`115/118 | `t`116/119 | NR | 53/21 | `zim city?=` | no |
| train-049 | A | `s`115/118 | `t`116/119 | NR | 53/21 | `zim city?=` | no |
| train-050 | B | `s`115/118 | `t`116/119 | NR | 53/21 | `city zim?=` | no |
| train-051 | B | `s`115/118 | `t`116/119 | NR | 53/21 | `city zim?=` | no |
| train-076 | A | `l`108/111 | `t`116/119 | NR | 53/21 | `nax city?=` | no |
| train-077 | A | `l`108/111 | `t`116/119 | NR | 53/21 | `nax city?=` | no |
| train-078 | B | `l`108/111 | `t`116/119 | NR | 53/21 | `city nax?=` | no |
| train-079 | B | `l`108/111 | `t`116/119 | NR | 53/21 | `city nax?=` | no |

All53-byte prefixes contain a31-byte prelude followed by the complete local
assignment/query. BOS+prelude fills32 IDs. The final delimiter is `?=` IDs66,64;
the `=` input is native index53/local21. Gold first byte is native document
index54, target y53; answer mask is y53..55 inclusive (two bytes plus EOS).
Saved loss counts confirm53 history and3 answer targets. Every failure ends in
EOS, without budget exhaustion. Four malformed `lo` outputs are exactly
train-004..007, a subset of the16 errors. The others are `mi→so`, `so→tu`,
`la→tu`, four examples each. Both answer bytes differ; the earliest divergence
is the first byte, and later generation is conditioned on that wrong byte.
For ordinary, nonce variants have identical second-segment inputs and no entering
memory. Thus these16 rows represent eight distinct local prefixes, not16
independent answer contexts; they still comprise every recorded error.

## Comparisons and pipeline audit

Ordinary601, recurrent601 and recurrent947 return the complete gold answer for
all16 identical prompts:48/48 comparisons correct, with the same native input,
delimiter and target offsets. City first-byte counts across all32 city cases:

| Run | l | m | s | t |
| --- | ---: | ---: | ---: | ---: |
| ordinary947 | 8 | 0 | 8 | 16 |
| each of the three passing runs | 8 | 8 | 8 | 8 |

- **Tokenization/boundary:** unchanged259-ID byte tokenizer; no unknown token,
  trimming or answer extraction. Complete evidence is in the current segment.
  Sixteen other city cases at the same y53/local21 position pass in ordinary947.
- **Mask/loss:** sealed [make_batch](../../artifacts/local-answer-dev-v1/sources/scripts/answer_trainability_dev.py)
  constructs y from full-document shifted IDs and marks answer positions from
  prefix byte length. The [uniform objective](../../artifacts/local-answer-dev-v1/sources/scripts/local_answer_dev.py)
  sums BOTH history and answer CE. The answer mask partitions reporting; it does
  not remove or upweight first-answer targets. Every city first-byte class has
  eight documents x128 presentations =1,024 supervised targets per fit.
- **Batches/order:** every failed document appears128 times and occupies all
  eight batch lanes. Ordinary947 and passing recurrent947 have identical ordered
  examples, targets and padded work at every step. Each failed example shares a
  batch with its other value for the SAME question10–27 times. Across all eight
  city questions there are268 batch/query contrast events (21–43 per question),
  not268 necessarily distinct batches. Contrasting examples were not absent.
- **Checkpoint/decoding:** hashes match all four final1536-step checkpoints;
  saved configuration, seed, initial identity and optimizer progress match.
  There is one checkpoint candidate per cell, no earlier selection. The sealed
  [decoder](../../artifacts/local-answer-dev-v1/sources/src/toruk_lm/owned_lm.py)
  suppresses only PAD/BOS, not `m`112, and takes greedy argmax. All16 errors close
  correctly; exact scoring is not hiding correct answers.

No per-token logits, ranks or first-token CE were saved. The failing suffix CE
sums are0.837031–1.359381, all>=ln2, consistent with a wrong first argmax. Passing
comparisons have much smaller suffix losses, but sums cannot recover exact
first-token probability or margin. No first-byte trajectory distinguishes
never-acquired from later-forgotten behavior. Prefix-only versus teacher-forced full-document
paths are semantically aligned; actual-case numerical parity/near ties cannot
be checked from these records. Do not invent their logits from checkpoint weights.

The601/947 seed changes BOTH initialization and epoch shuffle, so an
initialization-only attribution is unsupported. Passing ordinary601 demonstrates
that this configuration can fit the mapping; passing recurrent947 shows that
the947 schedule is not universally broken. Neither comparison identifies the
underlying optimization, ordering or value-interference mechanism.

## Curriculum assessment and next action

Pairing is expected to strengthen first-byte dependence on the supplied value
for a fixed entity/question: recover all eight `mi` cases and the other eight
wrong cases while retaining correct code/unknown/EOS behavior. It is not an EOS,
missing-fact or delimiter repair. The claim that pairs were missing is already
falsified by the trace. More examples/steps are not justified by missing exposure.

Earlier/more concentrated city contrasts might change optimization; that remains
a hypothesis. A compound warmup/pairing/template change would not isolate it,
and errors occur in BOTH existing templates. A future matched-exposure pairing
test would fail its stated sufficiency claim if it did not recover the16 first
bytes without regressions. If an otherwise matched city warmup without forced
pairs fixed them equally, pairing-specific necessity would be falsified; a warmup
effect could remain. Current records cannot perform that intervention or establish
whether these are near-tie decisions.

**Next action: collect the missing first-token margins and numerical-parity
evidence under the single [bounded inference-only proposal](local-answer-first-byte-v1-next-study-proposal.md)
before any curriculum fit.** No additional training examples, updates or answers
were produced in this audit. The proposal and this diagnostic remain uncommitted.

Offline checks (no model forward or generation):

```powershell
Set-Location D:\Toruk
.\.venv\Scripts\python.exe -B scripts/audit_local_answer_first_byte.py --inspect-checkpoints
.\.venv\Scripts\python.exe -B artifacts/local-answer-dev-v1/verify_saved.py
.\.venv\Scripts\python.exe -m ruff check scripts/audit_local_answer_first_byte.py
.\.venv\Scripts\python.exe -m ruff format --check scripts/audit_local_answer_first_byte.py
git diff --check
git status --short
```

Checkpoint inspection uses weights-only payload reading and finite/progress
checks; no model is constructed. Integrity checks pass; v1 remains
STOP_TRAINING_FAILURE with development unrun. Complete registered v1 workload
CPU103.500000 is unchanged; the earlier answer-trainability-v1 lifetime cost
remains UNKNOWN. No push or production change.
