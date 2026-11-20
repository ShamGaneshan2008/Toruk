# Saved answer-trainability v1: development failure diagnosis

20 November 2026. Development only. This analyzes the16 v1 cases at eight
seed/model/objective cells:128 saved predictions,49 correct and79 failures.
No answers were regenerated and no v1 scores or gates changed. The v1 record is
committed at `301dd9edbf12403aa97e5013247d5b1f33be0746`, including its enclosing
STOP and unknown complete-lifetime CPU. Eight ignored checkpoints stay local.

Reproduce from D:/Toruk:

```powershell
.\.venv\Scripts\python.exe -B scripts/diagnose_local_answer_v1.py
.\.venv\Scripts\python.exe -B artifacts/answer-trainability-dev-v1-commit-review-001/review.py --revision 301dd9edbf12403aa97e5013247d5b1f33be0746
```

[Machine classification](../../artifacts/local-answer-dev-v1-preparation/v1-diagnosis-derived.json)
includes all128 native ID sequences, raw strings, primary cause, independent EOS
and malformed flags, source path/line, unknown status and training-prior matches.
[Original report and raw links](answer-trainability-dev-v1-results.md) remain unchanged.

| Seed | Objective | Model | Correct | Wrong closed value | Malformed with EOS | No EOS | Training-question value match among failures |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 419 | uniform | ordinary | 7 | 9 | 0 | 0 | 6 |
| 419 | uniform | recurrent | 6 | 9 | 0 | 1 | 9 |
| 419 | answer16 | ordinary | 5 | 6 | 3 | 2 | 5 |
| 419 | answer16 | recurrent | 5 | 10 | 1 | 0 | 8 |
| 733 | uniform | ordinary | 9 | 6 | 0 | 1 | 5 |
| 733 | uniform | recurrent | 4 | 10 | 0 | 2 | 10 |
| 733 | answer16 | ordinary | 8 | 8 | 0 | 0 | 6 |
| 733 | answer16 | recurrent | 5 | 10 | 0 | 1 | 9 |
| Total | | | 49 | 68 | 4 | 7 | 58 |

Primary causes are exclusive: an unfinished output is classified as EOS failure;
a closed non-inventory answer is malformed; a closed wrong inventory value is
a wrong value. All seven EOS failures are also malformed, giving the original
11 malformed outputs. The four closed malformed outputs are EOS alone, `uv`,
`=R`, and `i`. The original strict scorer accepts none of these.

All16 development cases, aggregating their eight saved cell outputs:

| Case | Category | Correct /8 | Wrong closed value | Malformed with EOS | No EOS |
| --- | --- | ---: | ---: | ---: | ---: |
| dev-000 | city | 0 | 8 | 0 | 0 |
| dev-001 | city | 1 | 7 | 0 | 0 |
| dev-002 | city | 1 | 7 | 0 | 0 |
| dev-003 | city | 1 | 7 | 0 | 0 |
| dev-004 | city | 2 | 6 | 0 | 0 |
| dev-005 | city | 1 | 6 | 0 | 1 |
| dev-006 | city | 0 | 7 | 1 | 0 |
| dev-007 | city | 1 | 6 | 1 | 0 |
| dev-008 | code | 3 | 2 | 0 | 3 |
| dev-009 | code | 2 | 3 | 1 | 2 |
| dev-010 | code | 4 | 4 | 0 | 0 |
| dev-011 | code | 6 | 1 | 0 | 1 |
| dev-012 | unknown | 5 | 2 | 1 | 0 |
| dev-013 | unknown | 6 | 2 | 0 | 0 |
| dev-014 | unknown | 8 | 0 | 0 | 0 |
| dev-015 | unknown | 8 | 0 | 0 | 0 |

Representative evidence (EOS ID2, byte+3 otherwise):

- All eight cells, dev-000: source `uvo city=mi`, question `uvo city?=`, gold `mi`,
  output `[111,100,2]` (`la` + EOS). This equals uvo's training city answer.
- 419 answer16 ordinary, dev-006: gold `la`, output `[2]`, an empty closed output.
- 419 answer16 ordinary, dev-008: gold `R-7`, output
  `[85,35,117,100,108,64,113,100]` (`R rai=na`), cap8 without EOS.
- 733 uniform recurrent, dev-012: source `uvo role=so`, asks for city, gold `?`,
  output `[111,100,2]` (`la` + EOS), unsupported on an intentionally unknown field.

**Entity/attribute confusion versus wrong values:** every history contains only
one entity and one assignment. No output can be directly attributed to another
supplied entity; no wrong unknown answer copies the supplied wrong-field value.
Thus verified other-entity substitutions and wrong-attribute copies are both0.
Of68 wrong closed values,58 match a known training answer for the same question.
This supports an entity/question-prior hypothesis; it does not prove a hidden
entity-selection computation. The small shared value inventory also makes
matches to some other training entity ambiguous. Do not label all wrong values
as entity/attribute confusion without that qualification.

**Missing information:** no known-answer source is missing or outside the local
answer segment. Four unknown cases intentionally omit the queried attribute;
of32 such predictions,27 are correct and5 fail (four unsupported closed values,
one malformed `=R`). Missing source data therefore does not explain the known
case errors. Unknown-case mistakes are output failures, not absent gold labels.

**Overlap/template audit:** IDs, complete texts and assignment/query cores have
zero train/dev overlap.13/16 development questions were seen verbatim in training;
the three unseen questions are code queries for previously untrained entity/code
pairs. Both splits use the same single question syntax; there is no new syntactic
template at development. Only one city value per entity was trained, so fresh
city combinations expose a trainability/generalization distinction. Uniform
ordinary733 answers all four code cases correctly, including novel questions,
but city accuracy is1/8. Novel query identity alone cannot explain the shared
city failures. No counterfactual prompt was regenerated in this audit, so causal
template effects beyond these saved comparisons remain hypotheses.

The next registered design uses multiple training values per entity, balanced
answer inventories, two templates present in both splits, fresh held-back
entity/value combinations **within development only**, a source parser and a
question-only diagnostic. Uniform remains primary; no favorable answer16 cell
selects a condition. No long-history or memory-advantage inference is warranted.
