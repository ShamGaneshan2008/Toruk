# Raw answers: primary

Owned answers are unmodified role-line continuations; quotes/newlines are shown.
Errors are explicit. Inputs and answers are in the sealed data files.

| Case | Expected | historical | control | candidate | no_read | no_update | external_qwen |
|---|---|---|---|---|---|---|---|
| fresh-test-instruction-0 | `"Hvalueinstruction0"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" rag blis g g lis lime.\nOther pe"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"Hvalueinstruction0"` |
| fresh-test-instruction-1 | `"Hvalueinstruction1"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" re.\nNote 555: sun.\nNote 153: ra"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"Hvalueinstruction1"` |
| fresh-test-instruction-2 | `"Hvalueinstruction2"` | `" sun.\nNote 2: wis red.\nNote 5: r"` | `" re.\nNote 555: sun.\nNote 153: ra"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"\"Tvalueinstruction6\"\n"` | `"Hvalueinstruction2"` |
| fresh-test-factual-0 | `"Hvaluefactual0"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 53: rain.\nAnswer Cy's"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` | `"Hvaluefactual0"` |
| fresh-test-factual-1 | `"Hvaluefactual1"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 53: rain.\nAnswer Cy's"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` | `"Hvaluefactual1"` |
| fresh-test-factual-2 | `"Hvaluefactual2"` | `" swer rain.\nNote 5: wind.\nNote 2"` | `" sun.\nNote 53: rain.\nAnswer Cy's"` | `"\"Tvaluefactual3\"\n"` | `"\"Tvaluefactuala\"\n"` | `"\"Tvaluefactualalnt is Tvaluedist"` | `"Hvaluefactual2"` |
| fresh-test-uncertainty-0 | `"Unavailable."` | `" wind.\nNote 1: raind.\nNote 5: wi"` | `" rain.\nNote 11: rain.\nNote 155: "` | `"\"ep:\"oprsoty pd\"Tpersontionly d "` | `"\"ep:\"oprsoty Tperssonly Yonluss "` | `"\"ep:\"opersondistant2's label is "` | `"Unavailable."` |
| fresh-test-uncertainty-1 | `"Unavailable."` | `" wind.\nNote 1: raind.\nNote 5: wi"` | `" rain.\nNote 11: rain.\nNote 155: "` | `"\"ep:\"oprsoty pd\"Tpersontionly d."` | `"\"ep:\"oprsoty Tperssonly Yonluss "` | `"\"ep:\"opersondistant2's label is "` | `"Unavailable."` |
| fresh-test-uncertainty-2 | `"Unavailable."` | `" wind.\nNote 1: raind.\nNote 5: wi"` | `" rain.\nNote 11: rain.\nNote 155: "` | `"\"ep:\"oprsoty pd\"Tpers\n"` | `"\"ep:\"oprsoty Tperssonly Yonluss "` | `"\"ep:\"opersondistant2's label is "` | `"Unavailable."` |
| fresh-test-correction-0 | `"Hvaluecorrection0"` | `" swiswer Answer Bo's tain.\nNote "` | `" r raisun.\nAnswer Ad\nAd the park"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"Holdcorrection0"` |
| fresh-test-correction-1 | `"Hvaluecorrection1"` | `" swiswer Answer Bo's tain.\nNote "` | `" r raisun.\nAnswer Ad\nAd the park"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"Holdcorrection1"` |
| fresh-test-correction-2 | `"Hvaluecorrection2"` | `" swiswer Answer Bo's tain.\nNote "` | `" r raisun.\nAnswer Ad\nAd the park"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"\"Tvaluecorrection3\"\n"` | `"Holdcorrection2"` |
| fresh-test-distant-0 | `"Hvaluedistant0"` | `" rainsag tag is isund.\nNote 25: "` | `" r gain.\nAnswer Ada's tag? blue\n"` | `"\"Tvaluedistant2\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"Hvaluedistant0"` |
| fresh-test-distant-1 | `"Hvaluedistant1"` | `" rainsag tag is isund.\nNote 25: "` | `" r gain.\nAnswer Ada's tag? blue\n"` | `"\"Tvaluedistant2\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"Hvaluedistant1"` |
| fresh-test-distant-2 | `"Hvaluedistant2"` | `" iswe's tag? gold\n"` | `" r isun.\nNote 19: rain.\nNote 355"` | `"\"Tvaluedistant7\"\n"` | `"\"Tvaloud cloud cloud cloud cloud"` | `"\"Tval is Toldcorrection6.\"\nassis"` | `"Hvaluedistant2"` |
| fresh-test-exact-0 | `"H/Q-0_x!"` | `" r gold.\nNote 6: isun.\nNote 25: "` | `" r gold.\nNote 555: rain.\nNote 49"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"H/Q-0_x!"` |
| fresh-test-exact-1 | `"H/Q-1_x!"` | `" r gold.\nNote 6: isun.\nNote 25: "` | `" r gold.\nNote 555: rain.\nNote 49"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"H/Q-1_x!"` |
| fresh-test-exact-2 | `"H/Q-2_x!"` | `" r gold.\nNote 5: isun.\nNote 25: "` | `" r gold.\nNote 555: rain.\nNote 49"` | `"\"T/Q-6_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"\"T/Q-4_x!\"\n"` | `"H/Q-2_x!"` |
| fresh-test-math-0 | `"18"` | `" weraracind.\nNote 58: r rain.\nNo"` | `" rag in.\nNote g 3: raisund.\nNote"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` | `"18"` |
| fresh-test-math-1 | `"18"` | `" weraracind.\nNote 58: r rain.\nNo"` | `" rag in.\nNote g 3: raisund.\nNote"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` | `"18"` |
| fresh-test-math-2 | `"18"` | `" weraracind.\nNote 58: r rain.\nNo"` | `" rag in.\nNote g 3: raisund.\nNote"` | `"\"4\"\n"` | `"\"4\"\n"` | `"\"4\"\n"` | `"18"` |
| fresh-test-refusal-0 | `"18"` | `" is red.\nNote 2: sun.\nNote 582: "` | `" rain.\nNote 153: rain.\nNote 135:"` | `"\"Rhat is Tpersoncorrection7's la"` | `"\"What is Tpersoncorrection7's la"` | `"\"What is Tpersoncorrection7's la"` | `"The sum of 9 plus 9 is 18."` |
| fresh-test-refusal-1 | `"18"` | `" swind.\nNote 5858: wind.\nNote 25"` | `" rain.\nNote 53: rain.\nNote 39: r"` | `"\"6\"\n"` | `"\"6\"\n"` | `"\"6\"\n"` | `"18"` |
| fresh-test-refusal-2 | `"18"` | `" swind.\nNote 5858: wind.\nNote 25"` | `" rain.\nNote 53: rain.\nNote 39: r"` | `"\"6\"\n"` | `"\"6\"\n"` | `"\"6\"\n"` | `"18"` |
