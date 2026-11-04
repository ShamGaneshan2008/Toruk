| Case | Expected | Owned before: raw output | External Qwen: raw output | Pilot |
|---|---|---|---|---|
| test-instruction-0 | `"Evalueinstruction0"` | `" sun.\nNote 2: wi"` | `"Evaluating instruction 0"` | NOT_RUN |
| test-instruction-1 | `"Evalueinstruction1"` | `" sun.\nNote 2: wi"` | `"Evaluating instruction 1."` | NOT_RUN |
| test-instruction-2 | `"Evalueinstruction2"` | `" sun.\nNote 2: wi"` | `"Evaluating instruction 2."` | NOT_RUN |
| test-factual-0 | `"Evaluefactual0"` | `" swer rain.\nNote"` | `"Evaluefactual0"` | NOT_RUN |
| test-factual-1 | `"Evaluefactual1"` | `" swer rain.\nNote"` | `"Evaluefactual1"` | NOT_RUN |
| test-factual-2 | `"Evaluefactual2"` | `" swer rain.\nNote"` | `"Evaluefactual2"` | NOT_RUN |
| test-uncertainty-0 | `"Unknown."` | `" is red.\nNote 2:"` | `"Unknown"` | NOT_RUN |
| test-uncertainty-1 | `"Unknown."` | `" is red.\nNote 2:"` | `"Unknown"` | NOT_RUN |
| test-uncertainty-2 | `"Unknown."` | `" is red.\nNote 2:"` | `"Unknown"` | NOT_RUN |
| test-correction-0 | `"Evaluecorrection0"` | `" swiswer Answer "` | `"Eoldcorrection0"` | NOT_RUN |
| test-correction-1 | `"Evaluecorrection1"` | `" swiswer Answer "` | `"Eoldcorrection1"` | NOT_RUN |
| test-correction-2 | `"Evaluecorrection2"` | `" swinswisunswer "` | `"Evaluecorrection2"` | NOT_RUN |
| test-distant-0 | `"Evaluedistant0"` | `" r gold.\nNote 5:"` | `"Evaluatedistant0"` | NOT_RUN |
| test-distant-1 | `"Evaluedistant1"` | `" r gold.\nNote 5:"` | `"Evaluedistant1"` | NOT_RUN |
| test-distant-2 | `"Evaluedistant2"` | `" r gold.\nNote 5:"` | `"Evaluatedistant2"` | NOT_RUN |
| test-exact-0 | `"E/Q-0_x!"` | `" r gold.\nNote 5:"` | `"E/Q-0_x!"` | NOT_RUN |
| test-exact-1 | `"E/Q-1_x!"` | `" r gold.\nNote 5:"` | `"E/Q-1_x!"` | NOT_RUN |
| test-exact-2 | `"E/Q-2_x!"` | `" r gold.\nNote 5:"` | `"E/Q-2_x!"` | NOT_RUN |
| test-math-0 | `"10"` | `" wer racind.\nNot"` | `"10"` | NOT_RUN |
| test-math-1 | `"10"` | `" wer racind.\nNot"` | `"10"` | NOT_RUN |
| test-math-2 | `"10"` | `" wer racind.\nNot"` | `"10"` | NOT_RUN |
| test-refusal-0 | `"10"` | `" r rain.\nNote 5:"` | `"The sum of five plus five is ten."` | NOT_RUN |
| test-refusal-1 | `"10"` | `" swind.\nNote 585"` | `"10"` | NOT_RUN |
| test-refusal-2 | `"10"` | `" swind.\nNote 585"` | `"10"` | NOT_RUN |
| test-observed-full-refusal | `"10"` | `"generation prefix exceeds CPU smoke budget"` | `"The sum of 5 and 5 is 10."` | NOT_RUN |
