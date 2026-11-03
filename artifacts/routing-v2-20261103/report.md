# Path A routing v2: measured evidence

One registered routing intervention; old baselines/weights unchanged. Final worlds use previously unused word-order templates and three fresh seeds. This tests permutation transfer in a finite domain, not conversational capability.

| Method | Exact /168 seed31/47 | Known /120 | Unsupported /48 | Selected tokens | Forward positions | Extra routing positions | Latency ms | RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| recent | 30.0 / 25.0 | 7.0 / 8.0 | 25.0 / 31.0 | 22100.0 / 22100.0 | 22784.0 / 22780.0 | 0.0 / 0.0 | 661.3 / 693.0 | 209.3 / 209.2 |
| lexical | 35.0 / 25.0 | 9.0 / 8.0 | 22.0 / 31.0 | 18518.0 / 18518.0 | 19190.0 / 19201.0 | 0.0 / 0.0 | 602.5 / 614.7 | 210.0 / 209.7 |
| learned | 35.0 / 27.0 | 9.0 / 8.0 | 22.0 / 29.0 | 15793.0 / 15793.0 | 16459.0 / 16472.0 | 0.0 / 0.0 | 555.4 / 598.2 | 211.5 / 211.4 |
| old | 23.0 / 39.0 | 6.0 / 21.0 | 31.0 / 30.0 | 22100.0 / 22100.0 | 51415.0 / 51243.0 | 0.0 / 0.0 | 1900.8 / 1802.9 | 213.7 / 213.3 |
| new | 62.0 / 62.0 | 14.0 / 14.0 | 0.0 / 0.0 | 22100.0 / 22100.0 | 51261.0 / 51261.0 | 32085.0 / 32085.0 | 2026.5 / 2011.9 | 212.8 / 212.4 |
| new_zero | 48.0 / 48.0 | 0.0 / 0.0 | 0.0 / 0.0 | 22100.0 / 22100.0 | 50901.0 / 50901.0 | 32085.0 / 32085.0 | 2004.9 / 1933.0 | 211.9 / 212.5 |


All primary columns are load-0 totals over 168 worlds /192 generated answers. Both answers must match in multi-fact worlds. RSS is sampled over loading, all loads and offline routing diagnostics. Forward positions are recurrent work only; extra routing positions count additional embedding/pooling work, which must not be treated as free or added as equivalent FLOPs.

## Routing and evidence exposure

| Method | Seed | Read correct /queries | Write correct /records | Relevant suffix exposure /144 | Relevant ingestion /144 |
|---|---:|---:|---:|---:|---:|
| learned | 31 | N/A | N/A | 144/144 | 144/144 |
| learned | 47 | N/A | N/A | 144/144 | 144/144 |
| lexical | 31 | N/A | N/A | 144/144 | 144/144 |
| lexical | 47 | N/A | N/A | 144/144 | 144/144 |
| new | 31 | 192/192 | 1584/1584 | 83/144 | 144/144 |
| new | 47 | 192/192 | 1584/1584 | 83/144 | 144/144 |
| new_zero | 31 | 192/192 | 1584/1584 | 83/144 | 144/144 |
| new_zero | 47 | 192/192 | 1584/1584 | 83/144 | 144/144 |
| old | 31 | 97/192 | 667/1584 | 83/144 | 144/144 |
| old | 47 | 86/192 | 1266/1584 | 83/144 | 144/144 |
| recent | 31 | N/A | N/A | 83/144 | 144/144 |
| recent | 47 | N/A | N/A | 83/144 | 144/144 |

Suffix exposure counts any contributing bytes, not a full usable record. Integrated history ingestion is not evidence of semantic state retention. Read/write labels score diagnostic outputs offline; inference sees only text. Posthoc saved-output analysis finds a collapse at both seeds: every queried revised fact generates blue (72 queries), and every queried original fact generates cat (72 queries), despite varied reference values. This association does not prove a causal localization to one encoder layer. Perfect top-1 address accuracy does not imply uncontaminated soft state or faithful decoding. The 14 correct known worlds are insufficient evidence of useful value recall.

## Categories: old versus new

| Seed | Category | Old /24 | New /24 | Change |
|---|---|---:|---:|---:|
| 31 | ambiguity | 5 | 24 | +19 |
| 31 | correction | 1 | 4 | +3 |
| 31 | distant | 2 | 4 | +2 |
| 31 | distraction | 1 | 3 | +2 |
| 31 | multi | 0 | 0 | +0 |
| 31 | preservation | 2 | 3 | +1 |
| 31 | unknown | 12 | 24 | +12 |
| 47 | ambiguity | 7 | 24 | +17 |
| 47 | correction | 8 | 4 | -4 |
| 47 | distant | 2 | 4 | +2 |
| 47 | distraction | 6 | 3 | -3 |
| 47 | multi | 0 | 0 | +0 |
| 47 | preservation | 5 | 3 | -2 |
| 47 | unknown | 11 | 24 | +13 |

## Paired uncertainty

Intervals are conditional on two trained models. Worlds are clustered, including training-seed pairing. Repeated stress loads are not independent data.

```json
{
  "learned": {
    "accuracy95": [
      0.15476190476190477,
      0.21428571428571427
    ],
    "difference_vs_lexical95": [
      -0.005952380952380952,
      0.020833333333333332
    ],
    "difference_vs_old95": [
      -0.044642857142857144,
      0.044642857142857144
    ],
    "difference_vs_recent95": [
      0.005952380952380952,
      0.03869047619047619
    ]
  },
  "lexical": {
    "accuracy95": [
      0.1488095238095238,
      0.20833333333333334
    ],
    "difference_vs_lexical95": [
      0.0,
      0.0
    ],
    "difference_vs_old95": [
      -0.05357142857142857,
      0.03869047619047619
    ],
    "difference_vs_recent95": [
      0.0,
      0.03273809523809524
    ]
  },
  "new": {
    "accuracy95": [
      0.3333333333333333,
      0.40476190476190477
    ],
    "difference_vs_lexical95": [
      0.14285714285714285,
      0.24107142857142858
    ],
    "difference_vs_old95": [
      0.13988095238095238,
      0.22916666666666666
    ],
    "difference_vs_recent95": [
      0.16071428571428573,
      0.25297619047619047
    ]
  },
  "new_zero": {
    "accuracy95": [
      0.2857142857142857,
      0.2857142857142857
    ],
    "difference_vs_lexical95": [
      0.07738095238095238,
      0.13690476190476192
    ],
    "difference_vs_old95": [
      0.06547619047619048,
      0.13392857142857142
    ],
    "difference_vs_recent95": [
      0.09226190476190477,
      0.15178571428571427
    ]
  },
  "old": {
    "accuracy95": [
      0.15178571428571427,
      0.22023809523809523
    ],
    "difference_vs_lexical95": [
      -0.03869047619047619,
      0.05357142857142857
    ],
    "difference_vs_old95": [
      0.0,
      0.0
    ],
    "difference_vs_recent95": [
      -0.023809523809523808,
      0.06547619047619048
    ]
  },
  "recent": {
    "accuracy95": [
      0.13392857142857142,
      0.19345238095238096
    ],
    "difference_vs_lexical95": [
      -0.03273809523809524,
      0.0
    ],
    "difference_vs_old95": [
      -0.06547619047619048,
      0.023809523809523808
    ],
    "difference_vs_recent95": [
      0.0,
      0.0
    ]
  },
  "target_read_world_macro_difference95": [
    0.47023809523809523,
    0.5773809523809523
  ],
  "target_write_world_macro_difference95": [
    0.37462797619047616,
    0.40029761904761907
  ]
}
```

## Stress loads and history accounting

| Method | Seed | Added turns | Exact /168 | Known /120 | Unsupported /48 | Scanned tokens | Selected tokens | Forward positions | Extra routing | Latency ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| learned | 31 | 0 | 35 | 9 | 22 | 30001 | 15793 | 16459 | 0 | 555.4 |
| learned | 31 | 8 | 38 | 10 | 20 | 58385 | 16131 | 16809 | 0 | 570.4 |
| learned | 31 | 32 | 32 | 8 | 24 | 143554 | 17663 | 18307 | 0 | 631.7 |
| learned | 47 | 0 | 27 | 8 | 29 | 30001 | 15793 | 16472 | 0 | 598.2 |
| learned | 47 | 8 | 26 | 9 | 31 | 58385 | 16131 | 16817 | 0 | 602.0 |
| learned | 47 | 32 | 27 | 6 | 27 | 143554 | 17663 | 18337 | 0 | 685.2 |
| lexical | 31 | 0 | 35 | 9 | 22 | 30001 | 18518 | 19190 | 0 | 602.5 |
| lexical | 31 | 8 | 39 | 12 | 21 | 58385 | 18471 | 19165 | 0 | 602.0 |
| lexical | 31 | 32 | 33 | 6 | 21 | 143554 | 18487 | 19131 | 0 | 606.3 |
| lexical | 47 | 0 | 25 | 8 | 31 | 30001 | 18518 | 19201 | 0 | 614.7 |
| lexical | 47 | 8 | 24 | 9 | 33 | 58385 | 18471 | 19159 | 0 | 609.7 |
| lexical | 47 | 32 | 25 | 6 | 29 | 143554 | 18487 | 19167 | 0 | 621.5 |
| new | 31 | 0 | 62 | 14 | 0 | 30001 | 22100 | 51261 | 32085 | 2026.5 |
| new | 31 | 8 | 62 | 14 | 0 | 58385 | 22100 | 78109 | 58933 | 3240.2 |
| new | 31 | 32 | 62 | 14 | 0 | 143554 | 22100 | 158670 | 139494 | 6962.9 |
| new | 47 | 0 | 62 | 14 | 0 | 30001 | 22100 | 51261 | 32085 | 2011.9 |
| new | 47 | 8 | 62 | 14 | 0 | 58385 | 22100 | 78109 | 58933 | 3257.6 |
| new | 47 | 32 | 62 | 14 | 0 | 143554 | 22100 | 158670 | 139494 | 6973.4 |
| new_zero | 31 | 0 | 48 | 0 | 0 | 30001 | 22100 | 50901 | 32085 | 2004.9 |
| new_zero | 31 | 8 | 48 | 0 | 0 | 58385 | 22100 | 77749 | 58933 | 3315.4 |
| new_zero | 31 | 32 | 48 | 0 | 0 | 143554 | 22100 | 158310 | 139494 | 7030.7 |
| new_zero | 47 | 0 | 48 | 0 | 0 | 30001 | 22100 | 50901 | 32085 | 1933.0 |
| new_zero | 47 | 8 | 48 | 0 | 0 | 58385 | 22100 | 77749 | 58933 | 3136.2 |
| new_zero | 47 | 32 | 48 | 0 | 0 | 143554 | 22100 | 158310 | 139494 | 6831.1 |
| old | 31 | 0 | 23 | 6 | 31 | 30001 | 22100 | 51415 | 0 | 1900.8 |
| old | 31 | 8 | 21 | 7 | 34 | 58385 | 22100 | 78311 | 0 | 2986.6 |
| old | 31 | 32 | 18 | 7 | 37 | 143554 | 22100 | 158936 | 0 | 6282.5 |
| old | 47 | 0 | 39 | 21 | 30 | 30001 | 22100 | 51243 | 0 | 1802.9 |
| old | 47 | 8 | 33 | 18 | 33 | 58385 | 22100 | 78112 | 0 | 2842.2 |
| old | 47 | 32 | 32 | 17 | 33 | 143554 | 22100 | 158689 | 0 | 6018.6 |
| recent | 31 | 0 | 30 | 7 | 25 | 30001 | 22100 | 22784 | 0 | 661.3 |
| recent | 31 | 8 | 39 | 13 | 22 | 58385 | 22100 | 22776 | 0 | 665.0 |
| recent | 31 | 32 | 32 | 8 | 24 | 143554 | 22100 | 22760 | 0 | 683.5 |
| recent | 47 | 0 | 25 | 8 | 31 | 30001 | 22100 | 22780 | 0 | 693.0 |
| recent | 47 | 8 | 25 | 10 | 33 | 58385 | 22100 | 22788 | 0 | 700.4 |
| recent | 47 | 32 | 27 | 7 | 28 | 143554 | 22100 | 22782 | 0 | 721.4 |

## Per-evaluation-seed accuracy

| Method | Training seed | World seed | Exact /56 | Known /40 | Unsupported /16 |
|---|---:|---:|---:|---:|---:|
| learned | 31 | 8101 | 15 | 4 | 5 |
| learned | 31 | 8102 | 10 | 4 | 10 |
| learned | 31 | 8103 | 10 | 1 | 7 |
| learned | 47 | 8101 | 10 | 4 | 10 |
| learned | 47 | 8102 | 8 | 0 | 8 |
| learned | 47 | 8103 | 9 | 4 | 11 |
| lexical | 31 | 8101 | 14 | 4 | 6 |
| lexical | 31 | 8102 | 10 | 4 | 10 |
| lexical | 31 | 8103 | 11 | 1 | 6 |
| lexical | 47 | 8101 | 10 | 4 | 10 |
| lexical | 47 | 8102 | 6 | 0 | 10 |
| lexical | 47 | 8103 | 9 | 4 | 11 |
| new | 31 | 8101 | 22 | 6 | 0 |
| new | 31 | 8102 | 22 | 6 | 0 |
| new | 31 | 8103 | 18 | 2 | 0 |
| new | 47 | 8101 | 22 | 6 | 0 |
| new | 47 | 8102 | 22 | 6 | 0 |
| new | 47 | 8103 | 18 | 2 | 0 |
| new_zero | 31 | 8101 | 16 | 0 | 0 |
| new_zero | 31 | 8102 | 16 | 0 | 0 |
| new_zero | 31 | 8103 | 16 | 0 | 0 |
| new_zero | 47 | 8101 | 16 | 0 | 0 |
| new_zero | 47 | 8102 | 16 | 0 | 0 |
| new_zero | 47 | 8103 | 16 | 0 | 0 |
| old | 31 | 8101 | 8 | 2 | 10 |
| old | 31 | 8102 | 7 | 1 | 10 |
| old | 31 | 8103 | 8 | 3 | 11 |
| old | 47 | 8101 | 10 | 7 | 13 |
| old | 47 | 8102 | 15 | 7 | 8 |
| old | 47 | 8103 | 14 | 7 | 9 |
| recent | 31 | 8101 | 13 | 3 | 6 |
| recent | 31 | 8102 | 9 | 4 | 11 |
| recent | 31 | 8103 | 8 | 0 | 8 |
| recent | 47 | 8101 | 10 | 4 | 10 |
| recent | 47 | 8102 | 6 | 0 | 10 |
| recent | 47 | 8103 | 9 | 4 | 11 |

## Generated gains, failures and regressions

### Training seed 31

| Kind | World | Query | Expected | Old generated | New generated |
|---|---|---|---|---|---|
| gains | 8101-correction-0 | color? Ben's is What | blue | ? | blue |
| gains | 8101-correction-1 | pet? Cyd's is What | blue | ? | blue |
| known_failures | 8101-correction-2 | pet? Cyd's is What | dog | green | blue |
| known_failures | 8101-correction-3 | color? Ben's is What | cat | green | blue |
| regressions | 8101-preservation-3 | pet? Cyd's is What | green | green | cat |
| regressions | 8101-distraction-4 | color? Cyd's is What | green | green | blue |
| unsupported | No such example | | | | |
### Training seed 47

| Kind | World | Query | Expected | Old generated | New generated |
|---|---|---|---|---|---|
| gains | 8101-correction-1 | pet? Cyd's is What | blue | owl | blue |
| gains | 8101-preservation-6 | color? Cyd's is What | cat | blue | cat |
| known_failures | 8101-correction-2 | pet? Cyd's is What | dog | owl | blue |
| known_failures | 8101-correction-3 | color? Ben's is What | cat | ? | blue |
| regressions | 8101-correction-4 | color? Cyd's is What | cat | cat | blue |
| regressions | 8101-correction-6 | pet? Cyd's is What | owl | owl | blue |
| unsupported | No such example | | | | |

## Verdicts

```json
{
  "path": "A",
  "target_routing_improved_both_seeds": "PASS",
  "target_factual_improved_both_seeds": "FAIL",
  "minimum_quality_by_method": {
    "learned": "FAIL",
    "lexical": "FAIL",
    "new": "FAIL",
    "new_zero": "FAIL",
    "old": "FAIL",
    "recent": "FAIL"
  },
  "requested_gates": {
    "useful_conversational_answers": "INCONCLUSIVE: synthetic research decoder; Qwen integration smoke only",
    "toruk_owned_useful_learned_memory": "FAIL",
    "fewer_selected_tokens_preserved_quality": "FAIL: same integrated prompt budget; quality gate required",
    "lower_total_resource_cost": "FAIL: full history updates and extra routing work; no qualified cost reduction",
    "generalization": "FAIL on useful factual transfer; broader conversation unestablished",
    "research_paper_readiness": "FAIL: qualified evidence prerequisites unmet",
    "protected_preview_readiness": "FAIL: Path A; no qualified integrated chat candidate or preview gate",
    "public_chatbot_readiness": "FAIL: no qualified public release candidate"
  },
  "mechanism_exists": "PASS: learned routing/state influence tested; distinct trained checkpoints"
}
```

## Compute

New optimization: 1,600 steps, 25,600 sampled case presentations, 91.075 seconds in optimizer loops. All training uses one Torch CPU thread; no GPU/download/paid compute. All evaluation cells ran serially before verification. OS/shared-host activity is uncontrolled; report latency/RSS observations without speedup claims.

Training and per-process peak memory, all parent wall times, and separate offline diagnostic time are retained in JSON. RSS is sampled every 5 ms and can miss short peaks; it includes framework/model loading and diagnostics. All history is rebuilt for each query, including both multi-fact answers.

## Exact commands and exit codes

Registration command and its exit-0 record are in artifacts/checks/routing-v2-register-20261103.json. Every command below has a source identity, full log, parent duration and result.

| Check | Exit | Exact argv |
|---|---:|---|
| analysis | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/study_routing_v2.py", "analyze", "--run", "artifacts/routing-v2-20261103"]` |
| development-31 | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/study_routing_v2.py", "development", "--run", "artifacts/routing-v2-20261103", "--seed", "31"]` |
| development-47 | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/study_routing_v2.py", "development", "--run", "artifacts/routing-v2-20261103", "--seed", "47"]` |
| final-learned-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "learned", "--seed", "31"]` |
| final-learned-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "learned", "--seed", "47"]` |
| final-lexical-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "lexical", "--seed", "31"]` |
| final-lexical-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "lexical", "--seed", "47"]` |
| final-new-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "new", "--seed", "31"]` |
| final-new-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "new", "--seed", "47"]` |
| final-new_zero-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "new_zero", "--seed", "31"]` |
| final-new_zero-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "new_zero", "--seed", "47"]` |
| final-old-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "old", "--seed", "31"]` |
| final-old-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "old", "--seed", "47"]` |
| final-recent-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "recent", "--seed", "31"]` |
| final-recent-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\study_routing_v2.py", "evaluate", "--run", "artifacts\\routing-v2-20261103", "--method", "recent", "--seed", "47"]` |
| freeze | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/study_routing_v2.py", "freeze", "--run", "artifacts/routing-v2-20261103"]` |
| train-31 | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/study_routing_v2.py", "train", "--run", "artifacts/routing-v2-20261103", "--seed", "31"]` |
| train-47 | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/study_routing_v2.py", "train", "--run", "artifacts/routing-v2-20261103", "--seed", "47"]` |
| build | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "artifacts/routing-v2-20261103/package"]` |
| chat-http | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_chat_foundation.py", "--backbone-dir", "artifacts/qwen-chat-001/backbone", "--baseline-only", "--output-dir", "artifacts/routing-v2-20261103/chat-http"]` |
| cli-diagnose | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "diagnose"]` |
| cli-help | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "--help"]` |
| cli-reproduce | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/foundation.json", "--output", "artifacts/routing-v2-20261103/verification/pipeline"]` |
| cli-summary | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "summarize", "--run", "artifacts/routing-v2-20261103/verification/pipeline", "--output", "artifacts/routing-v2-20261103/verification/tables"]` |
| cli-validate | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "validate", "--manifest", "artifacts/routing-v2-20261103/verification/pipeline/data/manifest.json", "--config", "configs/foundation.json", "--checkpoint", "artifacts/routing-v2-20261103/verification/pipeline/train/checkpoint.pt"]` |
| controlled-resume-smoke | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "reproduce", "--config", "configs/reproduce-smoke-v1.json", "--output", "artifacts/routing-v2-20261103/verification/research-smoke"]` |
| diff-check | 0 | `["git", "diff", "--check"]` |
| final-tools-format | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "scripts/package_routing_v2.py", "scripts/audit_routing_v2.py", "scripts/study_routing_v2.py", "src/toruk_lm/pooled_router.py", "tests/test_pooled_router.py"]` |
| final-tools-lint | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "scripts/package_routing_v2.py", "scripts/audit_routing_v2.py", "scripts/study_routing_v2.py", "src/toruk_lm/pooled_router.py", "tests/test_pooled_router.py"]` |
| focused-format | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts/study_routing_v2.py", "scripts/package_routing_v2.py", "scripts/smoke_qualification_ui.py"]` |
| focused-lint | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "src", "tests", "scripts/study_routing_v2.py", "scripts/package_routing_v2.py", "scripts/smoke_qualification_ui.py"]` |
| format | 1 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]` |
| independent-scoring | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/audit_routing_v2.py", "--run", "artifacts/routing-v2-20261103"]` |
| lint | 1 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", ".", "--output-format", "concise"]` |
| live-page-handlers | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_qualification_ui.py", "--output-dir", "artifacts/routing-v2-20261103/live-page-handlers"]` |
| node-check | 0 | `["npm.cmd", "--prefix", "web/vercel", "run", "check"]` |
| node-tests | 0 | `["npm.cmd", "--prefix", "web/vercel", "test"]` |
| package-dependencies | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "pip", "check"]` |
| python-tests | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q", "-p", "no:cacheprovider"]` |
| study-help | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/study_routing_v2.py", "--help"]` |
| types-linux | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy", "--platform", "linux"]` |
| types | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy"]` |
