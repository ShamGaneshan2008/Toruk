# Wrong historical answers: offline review

Both modes have 14 wrong scored answers. This is saved-output analysis, not new TORUK inference.

| Case | Mode | Cause | Raw answer | Rationale |
|---|---|---|---|---|
| instruction_digit | BASELINE | evidence present but generator failed | The digit seven is 7. | Digit is correct but extra prose violates exact-output instruction. |
| instruction_digit | TORUK | evidence present but generator failed | The digit seven is 7. | Digit is correct but extra prose violates exact-output instruction. |
| reference_nickname | BASELINE | evidence present but generator failed | I'm sorry for any confusion, but as a painting assistant, I don't have the ability to name you. | Name-bearing m0 retained; refusal does not establish a coreference error. |
| reference_nickname | TORUK | evidence present but generator failed | I'm sorry for any confusion, but as a painting assistant, I don't have the ability to name you. | Name-bearing m0 retained; refusal does not establish a coreference error. |
| reference_codename | BASELINE | evidence present but generator failed | I noted the codename. | ORBIT-bearing m0 retained; copies assistant acknowledgement instead. |
| reference_codename | TORUK | evidence present but generator failed | I noted the codename. | ORBIT-bearing m0 retained; copies assistant acknowledgement instead. |
| user_fact_drink | BASELINE | evidence present but generator failed | I noted that you prefer a cold drink. | Mint-tea evidence retained; cold-drink preference is unsupported. |
| user_fact_drink | TORUK | evidence present but generator failed | I noted that you prefer a cold drink. | Mint-tea evidence retained; cold-drink preference is unsupported. |
| user_fact_pet | BASELINE | evidence present but generator failed | I'm sorry for any confusion, but as a helpful AI, I don't have real-time access to the internet. I'm here to assist with your | Pippa-bearing m0 retained; internet-access refusal is irrelevant. |
| user_fact_pet | TORUK | evidence present but generator failed | I'm sorry for any confusion, but as a helpful AI, I don't have real-time access to the internet. I'm here to assist with your | Pippa-bearing m0 retained; internet-access refusal is irrelevant. |
| correction_day | BASELINE | evidence present but generator failed | I will use the corrected day. | Thursday correction m2 retained; acknowledgement is not an answer. |
| correction_day | TORUK | evidence present but generator failed | I will use the corrected day. | Thursday correction m2 retained; acknowledgement is not an answer. |
| preserve_city | BASELINE | evidence present but generator failed | I provided the city name. | Quito-bearing m0 retained; acknowledgement omits the city. |
| preserve_city | TORUK | evidence present but generator failed | I provided the city name. | Quito-bearing m0 retained; acknowledgement omits the city. |
| preserve_hobby | BASELINE | stale fact used | My hobby is playing chess. The deadline is Monday. | Chess is correct, but appends obsolete Monday despite Friday in m2. |
| preserve_hobby | TORUK | stale fact used | My hobby is playing chess. The deadline is Monday. | Chess is correct, but appends obsolete Monday despite Friday in m2. |
| long_key | BASELINE | evidence present but generator failed | I noted the archive key. | CEDAR-19-bearing m0 retained in both modes; acknowledgement omits key. |
| long_key | TORUK | evidence present but generator failed | I noted the archive key. | CEDAR-19-bearing m0 retained in both modes; acknowledgement omits key. |
| irrelevant_arithmetic | BASELINE | evidence present but generator failed | That's a tricky one. | Latest turn supplies operands; arithmetic not answered correctly. |
| irrelevant_arithmetic | TORUK | evidence present but generator failed | Three is 3. | Latest turn supplies operands; arithmetic not answered correctly. |
| irrelevant_fact | BASELINE | evidence present but generator failed | I noted the planet Mars. | Latest turn asks public knowledge; irrelevant answer/refusal despite intact query. |
| irrelevant_fact | TORUK | evidence present but generator failed | I'm sorry for the confusion, but as a helpful AI, I don't have real-time capabilities to provide information about planets or celestial bodies. I'm | Latest turn asks public knowledge; irrelevant answer/refusal despite intact query. |
| unknown_pin | BASELINE | evidence present but generator failed | I'm sorry for any confusion, but as a chatbot, I don't have the ability to access or provide sensitive information. I'm designed to provide information | No PIN asserted; reasonable refusal missed by frozen uncertainty phrase list. |
| unknown_pin | TORUK | evidence present but generator failed | I'm sorry for any confusion, but as a chatbot, I don't have the ability to access or provide sensitive information. I'm designed to provide information | No PIN asserted; reasonable refusal missed by frozen uncertainty phrase list. |
| unknown_maiden | BASELINE | evidence present but generator failed | I'm sorry for any confusion, but as a helpful AI, I don't have the ability to provide information about your mother's maiden name. I'm here | No name asserted; reasonable refusal missed by frozen uncertainty phrase list. |
| unknown_maiden | TORUK | evidence present but generator failed | I'm sorry for any confusion, but as a helpful AI, I don't have the ability to provide information about your mother's maiden name. I'm here | No name asserted; reasonable refusal missed by frozen uncertainty phrase list. |
| ambiguous_season | BASELINE | unsupported question answered as fact | My favorite season is spring. | Both conflicting notes retained; guesses spring without resolving uncertainty. |
| ambiguous_season | TORUK | unsupported question answered as fact | My favorite season is spring. | Both conflicting notes retained; guesses spring without resolving uncertainty. |
