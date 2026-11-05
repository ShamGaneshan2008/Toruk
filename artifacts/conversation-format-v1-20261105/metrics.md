# Derived metrics

EOS termination is not exposed by the external backend and is unavailable there.
External forward-position accounting is also unavailable, not zero work.

## development

| Condition | N | Content exact | Framed | EOS | Errors | Unknown proxy | Repeated trigrams | Unique | Seconds | Prompt tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| historical | 16 | 0 | 0 | 1 | 0 | 2 | 0 | 9 | 0.8525 | 2233 | 499 |
| control | 16 | 0 | 0 | 0 | 0 | 2 | 0 | 11 | 0.9154 | 2233 | 512 |
| candidate | 16 | 0 | 14 | 14 | 0 | 2 | 0 | 10 | 0.5059 | 2233 | 266 |
| no_read | 16 | 0 | 13 | 13 | 0 | 2 | 1 | 8 | 0.3487 | 2233 | 274 |
| no_update | 16 | 0 | 11 | 11 | 0 | 2 | 0 | 8 | 0.5235 | 2233 | 302 |

Category exact scores:

| Category | historical | control | candidate | no_read | no_update |
|---|---|---|---|---|---|
| correction | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| distant | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| exact | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| factual | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| instruction | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| math | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| refusal | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| uncertainty | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |

## primary

| Condition | N | Content exact | Framed | EOS | Errors | Unknown proxy | Repeated trigrams | Unique | Seconds | Prompt tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| historical | 24 | 0 | 0 | 1 | 0 | 3 | 0 | 11 | 1.2674 | 3300 | 755 |
| control | 24 | 0 | 0 | 0 | 0 | 3 | 0 | 11 | 1.3177 | 3300 | 768 |
| candidate | 24 | 0 | 20 | 21 | 0 | 3 | 0 | 12 | 0.7893 | 3300 | 417 |
| no_read | 24 | 0 | 19 | 19 | 0 | 3 | 1 | 9 | 0.5629 | 3300 | 428 |
| no_update | 24 | 0 | 16 | 16 | 0 | 3 | 0 | 9 | 0.8001 | 3300 | 470 |
| external_qwen | 24 | 20 | native content | unavailable | 0 | 0 | 0 | 18 | 34.9088 | 2990 | 128 |

Category exact scores:

| Category | historical | control | candidate | no_read | no_update | external_qwen |
|---|---|---|---|---|---|---|
| correction | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| distant | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| exact | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| factual | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| instruction | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| math | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| refusal | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 2/3 |
| uncertainty | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |

## regression

| Condition | N | Content exact | Framed | EOS | Errors | Unknown proxy | Repeated trigrams | Unique | Seconds | Prompt tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| historical | 25 | 0 | 0 | 0 | 1 | 3 | 0 | 9 | 1.2865 | 3273 | 768 |
| control | 25 | 0 | 0 | 0 | 1 | 3 | 0 | 12 | 1.3096 | 3273 | 768 |
| candidate | 25 | 0 | 20 | 21 | 1 | 3 | 0 | 9 | 0.7553 | 3273 | 409 |
| no_read | 25 | 0 | 20 | 20 | 1 | 3 | 0 | 8 | 0.5394 | 3273 | 408 |
| no_update | 25 | 0 | 17 | 17 | 1 | 3 | 0 | 8 | 0.7710 | 3273 | 450 |
| external_qwen | 25 | 13 | native content | unavailable | 0 | 3 | 0 | 19 | 38.4721 | 3256 | 140 |

Category exact scores:

| Category | historical | control | candidate | no_read | no_update | external_qwen |
|---|---|---|---|---|---|---|
| correction | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 1/3 |
| distant | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 1/3 |
| exact | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| factual | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| instruction | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| math | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 3/3 |
| refusal | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 | 2/4 |
| uncertainty | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |

