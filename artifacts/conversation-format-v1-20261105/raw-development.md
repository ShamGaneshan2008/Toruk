# Raw answers: development

Owned answers are unmodified role-line continuations; quotes/newlines are shown.
Errors are explicit. Inputs and answers are in the sealed data files.

| Case | Expected | historical | control | candidate | no_read | no_update |
|---|---|---|---|---|---|---|
| development-instruction-0 | `"Dvalueinstruction0"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" rag blis g g lis lime.\nOther pe"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` |
| development-instruction-1 | `"Dvalueinstruction1"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" re.\nNote 555: sun.\nNote 153: ra"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` |
| development-factual-0 | `"Dvaluefactual0"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 53: rain.\nAnswer Cy's"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` |
| development-factual-1 | `"Dvaluefactual1"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 5353: sun.\nAnswer Cy'"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` |
| development-uncertainty-0 | `"Not stated."` | `" rain.\nNote 5: wind.\nNote 5: 2: "` | `" rain.\nNote 13: rain.\nNote 55: s"` | `"\"Recorded.\"\nuser:\"Corralalalal.\""` | `"\"Recorded.\"\nuser:\"Correction: ty"` | `"\"Recorded.\"\nuser:\"Correction: ty"` |
| development-uncertainty-1 | `"Not stated."` | `" rain.\nNote 5: wind.\nNote 5: 2: "` | `" rain.\nNote 13: rain.\nNote 55: s"` | `"\"Recorded.\"\nuser:\"Corr\nact\nalonl"` | `"\"Recorded.\"\nuser:\"Correction: ty"` | `"\"Recorded.\"\nuser:\"Correction: ty"` |
| development-correction-0 | `"Dvaluecorrection0"` | `" swiswer Answer Bo's tain.\nNote "` | `" r raisun.\nAnswer Ad\nAd the park"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` |
| development-correction-1 | `"Dvaluecorrection1"` | `" swiswer Answer Bo's tain.\nNote "` | `" r raisun.\nAnswer Ad\nAd the park"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` |
| development-distant-0 | `"Dvaluedistant0"` | `" r gold.\nNote 6: 72: rain.\nNote "` | `" r gain.\nAnswer Ada's tag? blue\n"` | `"\"Tvaluedistant2\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` |
| development-distant-1 | `"Dvaluedistant1"` | `" iswe's tag? gold\n"` | `" r isun.\nNote 19: rain.\nNote 355"` | `"\"Tvaluedistant7\"\n"` | `"\"Tvaloud cloud cloud cloud cloud"` | `"\"Tval is Toldcorrection6.\"\nassis"` |
| development-exact-0 | `"D/Q-0_x!"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gold.\nNote 555: rain.\nNote 49"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` |
| development-exact-1 | `"D/Q-1_x!"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gold.\nNote 555: rain.\nNote 49"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` |
| development-math-0 | `"14"` | `" weraracind.\nNote 58: r is red.\n"` | `" rag in.\nNote g 3: raisund.\nNote"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` |
| development-math-1 | `"14"` | `" weraracind.\nNote 58: r is red.\n"` | `" rag in.\nNote g 3: raisund.\nNote"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` |
| development-refusal-0 | `"16"` | `" swind.\nNote 5858: wind.\nNote 25"` | `" rain.\nNote 3553: sun.\nNote 71: "` | `"\"6\"\n"` | `"\"6\"\n"` | `"\"6\"\n"` |
| development-refusal-1 | `"16"` | `" swind.\nNote 5858: wind.\nNote 25"` | `" rain.\nNote 3553: sun.\nNote 71: "` | `"\"6\"\n"` | `"\"6\"\n"` | `"\"6\"\n"` |
