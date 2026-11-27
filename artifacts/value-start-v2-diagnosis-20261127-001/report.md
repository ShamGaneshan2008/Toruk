# Value-start v2 saved-record diagnosis — 27 November 2026

Decision: **STOP_DEVELOPMENT_FAILURE**. Integrity: **PASS**.

Recomputed with the unchanged independent auditor. Zero model forwards, training, or held-out access. Training mastery is 96/96 in all sixteen cells; 48 stage seals and 24,576 recorded updates verify. All 34 development failures start at the first byte (eight first16; 26 uniform). Five malformed outputs and one EOS failure are additional symptoms, not evidence of a scorer defect.

## Every failed primary development prediction

Crossed IDs encode initialization and shuffle separately. Answers are JSON strings: `\n` denotes a literal newline. EOS and format are independently checked. Every row has consistent data/evidence, wrong allowed argmax, correct mismatch scoring, and passing integrity. Its specific optimization cause remains unidentified.

| Cell | Case | Expected | Actual | Gold rank | Gold − top | EOS | Malformed |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| i601-s1301-ordinary-first16 | v2-dev-012 | `"la"` | `"so"` | 2 | -0.540195 | True | False |
| i601-s1301-recurrent-first16 | v2-dev-012 | `"la"` | `"?"` | 8 | -6.150173 | True | False |
| i601-s1301-recurrent-first16 | v2-dev-013 | `"mi"` | `"\nu"` | 2 | -0.081824 | True | True |
| i601-s1301-recurrent-first16 | v2-dev-018 | `"mi"` | `"Z!in.?ty"` | 5 | -1.660897 | False | True |
| i601-s1301-recurrent-uniform | v2-dev-006 | `"tu"` | `"la"` | 5 | -4.100118 | True | False |
| i601-s1301-recurrent-uniform | v2-dev-012 | `"la"` | `"so"` | 6 | -4.718753 | True | False |
| i601-s1301-recurrent-uniform | v2-dev-013 | `"mi"` | `"?"` | 3 | -0.864803 | True | False |
| i601-s1301-recurrent-uniform | v2-dev-014 | `"R-7"` | `"V:4"` | 6 | -7.738980 | True | False |
| i601-s1709-recurrent-first16 | v2-dev-012 | `"la"` | `"?"` | 10 | -5.792510 | True | False |
| i601-s1709-recurrent-first16 | v2-dev-013 | `"mi"` | `"\nu"` | 5 | -2.647539 | True | True |
| i601-s1709-recurrent-first16 | v2-dev-018 | `"mi"` | `"la"` | 15 | -5.589559 | True | False |
| i601-s1709-recurrent-uniform | v2-dev-006 | `"tu"` | `"mi"` | 4 | -3.554341 | True | False |
| i601-s1709-recurrent-uniform | v2-dev-012 | `"la"` | `"so"` | 2 | -1.101170 | True | False |
| i601-s1709-recurrent-uniform | v2-dev-013 | `"mi"` | `"?"` | 3 | -2.475056 | True | False |
| i601-s1709-recurrent-uniform | v2-dev-014 | `"R-7"` | `"V:4"` | 9 | -5.873707 | True | False |
| i947-s1301-ordinary-uniform | v2-dev-000 | `"so"` | `"la"` | 3 | -3.986070 | True | False |
| i947-s1301-ordinary-uniform | v2-dev-006 | `"tu"` | `"mi"` | 2 | -0.292912 | True | False |
| i947-s1301-ordinary-uniform | v2-dev-007 | `"la"` | `"so"` | 3 | -4.714710 | True | False |
| i947-s1301-ordinary-uniform | v2-dev-012 | `"la"` | `"so"` | 3 | -6.115627 | True | False |
| i947-s1301-ordinary-uniform | v2-dev-013 | `"mi"` | `"tu"` | 3 | -1.487523 | True | False |
| i947-s1301-ordinary-uniform | v2-dev-019 | `"so"` | `"la"` | 2 | -4.096232 | True | False |
| i947-s1301-recurrent-first16 | v2-dev-012 | `"la"` | `"mi"` | 2 | -1.096484 | True | False |
| i947-s1301-recurrent-uniform | v2-dev-000 | `"so"` | `"4i"` | 165 | -5.801198 | True | True |
| i947-s1709-ordinary-uniform | v2-dev-000 | `"so"` | `"la"` | 2 | -1.789447 | True | False |
| i947-s1709-ordinary-uniform | v2-dev-007 | `"la"` | `"so"` | 2 | -0.574149 | True | False |
| i947-s1709-ordinary-uniform | v2-dev-012 | `"la"` | `"so"` | 3 | -2.669399 | True | False |
| i947-s1709-ordinary-uniform | v2-dev-013 | `"mi"` | `"tu"` | 5 | -1.290184 | True | False |
| i947-s1709-ordinary-uniform | v2-dev-018 | `"mi"` | `"tu"` | 2 | -0.841144 | True | False |
| i947-s1709-ordinary-uniform | v2-dev-019 | `"so"` | `"la"` | 2 | -2.732007 | True | False |
| i947-s1709-recurrent-uniform | v2-dev-000 | `"so"` | `"la"` | 66 | -7.740048 | True | False |
| i947-s1709-recurrent-uniform | v2-dev-006 | `"tu"` | `"?"` | 2 | -0.867869 | True | False |
| i947-s1709-recurrent-uniform | v2-dev-007 | `"la"` | `"ci"` | 2 | -3.471719 | True | True |
| i947-s1709-recurrent-uniform | v2-dev-015 | `"Q_2"` | `"V:4"` | 2 | -1.095729 | True | False |
| i947-s1709-recurrent-uniform | v2-dev-019 | `"so"` | `"la"` | 2 | -0.924119 | True | False |

## Registered uniform controls

| Cell | Uniform /24 | First16 /24 | Delta | Fixed cases | Introduced errors |
| --- | ---: | ---: | ---: | --- | --- |
| i601-s1301-ordinary | 24 | 23 | -1 | none | v2-dev-012 |
| i601-s1301-recurrent | 20 | 21 | +1 | v2-dev-006, v2-dev-014 | v2-dev-018 |
| i601-s1709-ordinary | 24 | 24 | +0 | none | none |
| i601-s1709-recurrent | 20 | 21 | +1 | v2-dev-006, v2-dev-014 | v2-dev-018 |
| i947-s1301-ordinary | 18 | 24 | +6 | v2-dev-000, v2-dev-006, v2-dev-007, v2-dev-012, v2-dev-013, v2-dev-019 | none |
| i947-s1301-recurrent | 23 | 23 | +0 | v2-dev-000 | v2-dev-012 |
| i947-s1709-ordinary | 18 | 24 | +6 | v2-dev-000, v2-dev-007, v2-dev-012, v2-dev-013, v2-dev-018, v2-dev-019 | none |
| i947-s1709-recurrent | 19 | 24 | +5 | v2-dev-000, v2-dev-006, v2-dev-007, v2-dev-015, v2-dev-019 | none |

Five pairs improve, two tie, one regresses. Both recurrent601 candidates fail the city and format floors; shuffle1301 also loses EOS. Ordinary601/1301 loses a correct city case. Recurrent947/1301 fixes case000 but loses case012 despite unchanged net accuracy. The registered strict-positive-all-eight gate remains failed; no ceiling exception is applied retroactively.

## Cause boundaries

All 120 train/development labels independently agree with their assignment/query text, all needed evidence fits segment2, and canonical train/dev overlap is zero. All 1952 saved first-logit vectors (including replays) match recorded greedy first IDs; raw decoding and scoring also agree. The largest teacher-prefix CE difference is 4.95687589641e-06.

Twenty-two failures emit a value seen for the same entity/category during training. Entity/value shortcuts are plausible, not causally established. Templates have 21/13 failures but differ in canonical cases, so template effects are confounded. Three failures share the question-only first byte; this does not establish complete disregard of evidence. Forcing a correct first byte was not tested and cannot be assumed to fix suffixes or termination.

This is a local-combination generalization failure, not a demonstrated distant-memory bottleneck. The later entity-dropout study also failed its own gate; it is preserved and is not proposed again. See `proposal.md` for the one prospective objective intervention. Reused dev cases make that proposal an adaptive development repair study, not independent generalization evidence.
