# Raw answers: regression

Owned answers are unmodified role-line continuations; quotes/newlines are shown.
Errors are explicit. Inputs and answers are in the sealed data files.

| Case | Expected | historical | control | candidate | no_read | no_update | external_qwen |
|---|---|---|---|---|---|---|---|
| test-instruction-0 | `"Evalueinstruction0"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" rag blis g g lis lime.\nOther pe"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"Evaluating instruction 0"` |
| test-instruction-1 | `"Evalueinstruction1"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" re.\nNote 555: sun.\nNote 153: ra"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"Evaluating instruction 1."` |
| test-instruction-2 | `"Evalueinstruction2"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" re.\nNote 555: sun.\nNote 153: ra"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"Evaluating instruction 2."` |
| test-factual-0 | `"Evaluefactual0"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 53: rain.\nAnswer Cy's"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` | `"Evaluefactual0"` |
| test-factual-1 | `"Evaluefactual1"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 53: rain.\nAnswer Cy's"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` | `"Evaluefactual1"` |
| test-factual-2 | `"Evaluefactual2"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 53: rain.\nAnswer Cy's"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` | `"Evaluefactual2"` |
| test-uncertainty-0 | `"Unknown."` | `" is red.\nNote 2: sun.\nNote 582: "` | `" rain.\nNote 153: rain.\nNote 13: "` | `"\"\nabel? Reply only the exact lab"` | `" rs Tvaluedistant3.\"\nassistant:\""` | `" rs Tvaluedistant3.\"\nassistant:\""` | `"Unknown"` |
| test-uncertainty-1 | `"Unknown."` | `" is red.\nNote 2: sun.\nNote 582: "` | `" sun.\nNote 11: rain.\nNote 356: r"` | `"\"\nabel? Reply only the exact lab"` | `" rs Tvaluedistant3.\"\nassistant:\""` | `" rs Tvaluedistant3.\"\nassistant:\""` | `"Unknown"` |
| test-uncertainty-2 | `"Unknown."` | `" is red.\nNote 2: sun.\nNote 582: "` | `" sun.\nNote 11: rain.\nNote 356: r"` | `"\"\nabel? Reply only the exact lab"` | `" rs Tvaluedistant3.\"\nassistant:\""` | `" rs Tvaluedistant3.\"\nassistant:\""` | `"Unknown"` |
| test-correction-0 | `"Evaluecorrection0"` | `" swiswer Answer Bo's tain.\nNote "` | `" r raisun.\nAnswer Ad\nNold.\nNote "` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"Eoldcorrection0"` |
| test-correction-1 | `"Evaluecorrection1"` | `" swiswer Answer Bo's tain.\nNote "` | `" r raisun.\nAnswer Ad\nNold.\nNote "` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"Eoldcorrection1"` |
| test-correction-2 | `"Evaluecorrection2"` | `" swinswisunswer Bo's tain.\nNote "` | `" r raisun.\nNote 199: sun.\nNote 1"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"Evaluecorrection2"` |
| test-distant-0 | `"Evaluedistant0"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gain.\nNote 553: rain.\nNote 43"` | `"\"Tvaluedistant2\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"Evaluatedistant0"` |
| test-distant-1 | `"Evaluedistant1"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gain.\nNote 553: rain.\nNote 43"` | `"\"Tvaluedistant2\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"Evaluedistant1"` |
| test-distant-2 | `"Evaluedistant2"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gain.\nNote 553: rain.\nNote 43"` | `"\"Tvaluedistant2\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"Evaluatedistant2"` |
| test-exact-0 | `"E/Q-0_x!"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gain.\nNote 555: rain.\nNote 43"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"E/Q-0_x!"` |
| test-exact-1 | `"E/Q-1_x!"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gain.\nNote 555: rain.\nNote 43"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"E/Q-1_x!"` |
| test-exact-2 | `"E/Q-2_x!"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gain.\nNote 555: rain.\nNote 43"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"E/Q-2_x!"` |
| test-math-0 | `"10"` | `" wer racind.\nNote 58: re tag? go"` | `" ra sain.\nNote 5555: sun.\nNote 7"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` | `"10"` |
| test-math-1 | `"10"` | `" wer racind.\nNote 58: re tag? go"` | `" ra sain.\nNote 5555: sun.\nNote 7"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` | `"10"` |
| test-math-2 | `"10"` | `" wer racind.\nNote 58: re tag? go"` | `" ra sain.\nNote 5555: sun.\nNote 7"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` | `"10"` |
| test-refusal-0 | `"10"` | `" r rain.\nNote 5: rain.\nNote 58: "` | `" rain.\nNote 153: rain.\nNote 135:"` | `"\"Tpistant:\"4\"\n"` | `"\"What is Tpersoncorrection7's la"` | `"\"What is Tpersoncorrection7's la"` | `"The sum of five plus five is ten."` |
| test-refusal-1 | `"10"` | `" swind.\nNote 5858: wind.\nNote 25"` | `" rain.\nNote 3553: sun.\nAnswer Cy"` | `"\"6\"\n"` | `"\"6\"\n"` | `"\"6\"\n"` | `"10"` |
| test-refusal-2 | `"10"` | `" swind.\nNote 5858: wind.\nNote 25"` | `" rain.\nNote 3553: sun.\nAnswer Cy"` | `"\"6\"\n"` | `"\"6\"\n"` | `"\"6\"\n"` | `"10"` |
| test-observed-full-refusal | `"10"` | `"generation prefix exceeds CPU smoke budget"` | `"generation prefix exceeds CPU smoke budget"` | `"generation prefix exceeds CPU smoke budget"` | `"generation prefix exceeds CPU smoke budget"` | `"generation prefix exceeds CPU smoke budget"` | `"The sum of 5 and 5 is 10."` |
