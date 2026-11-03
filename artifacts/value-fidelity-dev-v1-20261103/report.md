# Existing-model value-fidelity development gate

Milestone verdict: **FAIL**. Development only. No new final set was generated or opened for scoring. Historical final artifacts were integrity-checked only, not used for fitting or checkpoint selection. The architecture, pretrained chat backbone and external conversational selector remain unchanged. Both 800-step fits were fixed in advance.

| Method | Exact /168 seed31/47 | Known /120 | Unsupported /48 | Selected tokens | Forward positions | Extra routing positions | Latency ms | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| recent | 46.0 / 30.0 | 8.0 / 6.0 | 10.0 / 24.0 | 22088.0 / 22088.0 | 22659.0 / 22749.0 | 0.0 / 0.0 | 639.4 / 648.4 | 205.0 / 205.5 |
| lexical | 45.0 / 36.0 | 7.0 / 11.0 | 10.0 / 23.0 | 18425.0 / 18425.0 | 19015.0 / 19079.0 | 0.0 / 0.0 | 572.4 / 581.3 | 205.3 / 206.2 |
| old | 113.0 / 113.0 | 65.0 / 65.0 | 0.0 / 0.0 | 22088.0 / 22088.0 | 55908.0 / 55908.0 | 36731.0 / 36731.0 | 2212.9 / 2354.4 | 207.1 / 207.7 |
| augmented | 98.0 / 82.0 | 50.0 / 34.0 | 0.0 / 0.0 | 22088.0 / 22088.0 | 55925.0 / 55911.0 | 36731.0 / 36731.0 | 2136.4 / 2134.2 | 207.4 / 207.5 |
| zero | 48.0 / 48.0 | 0.0 / 0.0 | 0.0 / 0.0 | 22088.0 / 22088.0 | 55547.0 / 55547.0 | 36731.0 / 36731.0 | 2095.7 / 2111.9 | 207.3 / 207.1 |


Accuracy is exact per world, requiring both multi-fact answers to match. Token/work/latency totals cover 192 generated answers over 168 worlds. RSS includes interpreter/model loading and offline routing diagnostics. Recurrent positions and additional pooling/embedding positions are different workload proxies; neither is FLOPs, energy or total compute.

## Deciding gate

```json
{
  "31": {
    "checks": {
      "correction_at_least_80": false,
      "known_at_least_80": false,
      "memory_zero_known_drop_at_least_50pp": false,
      "overall_at_least_80": false,
      "preservation_at_least_80": false,
      "unsupported_at_most_5": true
    },
    "known_accuracy": 0.4166666666666667,
    "known_accuracy_drop_zero": 0.4166666666666667,
    "status": "FAIL"
  },
  "47": {
    "checks": {
      "correction_at_least_80": false,
      "known_at_least_80": false,
      "memory_zero_known_drop_at_least_50pp": false,
      "overall_at_least_80": false,
      "preservation_at_least_80": false,
      "unsupported_at_most_5": true
    },
    "known_accuracy": 0.2833333333333333,
    "known_accuracy_drop_zero": 0.2833333333333333,
    "status": "FAIL"
  }
}
```

## Categories and regressions

| Training seed | Category | Old /24 | Augmented /24 | Change |
|---|---|---:|---:|---:|
| 31 | ambiguity | 24 | 24 | +0 |
| 31 | correction | 14 | 12 | -2 |
| 31 | distant | 16 | 10 | -6 |
| 31 | distraction | 11 | 9 | -2 |
| 31 | multi | 6 | 4 | -2 |
| 31 | preservation | 18 | 15 | -3 |
| 31 | unknown | 24 | 24 | +0 |
| 47 | ambiguity | 24 | 24 | +0 |
| 47 | correction | 14 | 7 | -7 |
| 47 | distant | 16 | 8 | -8 |
| 47 | distraction | 11 | 6 | -5 |
| 47 | multi | 6 | 2 | -4 |
| 47 | preservation | 18 | 11 | -7 |
| 47 | unknown | 24 | 24 | +0 |

## Memory evidence and routing

| Method | Seed | Relevant records ingested /queries | Relevant suffix exposure /queries | Read /queries | Write /records | Full history scans, tokens |
|---|---:|---:|---:|---:|---:|---:|
| augmented | 31 | 144/144 | 41/144 | 192/192 | 1854/1854 | 34929 |
| augmented | 47 | 144/144 | 41/144 | 192/192 | 1854/1854 | 34929 |
| lexical | 31 | 144/144 | 144/144 | N/A | N/A | 34929 |
| lexical | 47 | 144/144 | 144/144 | N/A | N/A | 34929 |
| old | 31 | 144/144 | 41/144 | 192/192 | 1854/1854 | 34929 |
| old | 47 | 144/144 | 41/144 | 192/192 | 1854/1854 | 34929 |
| recent | 31 | 144/144 | 41/144 | N/A | N/A | 34929 |
| recent | 47 | 144/144 | 41/144 | N/A | N/A | 34929 |
| zero | 31 | 144/144 | 41/144 | 192/192 | 1854/1854 | 34929 |
| zero | 47 | 144/144 | 41/144 | 192/192 | 1854/1854 | 34929 |

Ingestion is not proof of faithful latent-state retention. Suffix exposure counts any contributing bytes, not necessarily a complete record. Correct generated values and the zero-state gap provide separate evidence of memory use.

## Individual generated outputs

| Seed | Kind | World | Query | Expected | Old | Augmented |
|---|---|---|---|---|---|---|
| 31 | gains | 9101-correction-3 | What Cyd's is color? | cat | blue | cat |
| 31 | gains | 9101-preservation-7 | is pet? Cyd's What | owl | cat | owl |
| 31 | known_failures | 9101-correction-0 | What Cyd's is pet? | red | blue | green |
| 31 | known_failures | 9101-correction-1 | is color? Ada's What | red | blue | cat |
| 31 | regressions | 9101-correction-2 | is pet? Ada's What | red | red | dog |
| 31 | regressions | 9101-correction-4 | What Ben's is pet? | blue | blue | owl |
| 31 | unsupported | No example | | | | |
| 47 | gains | 9101-correction-3 | What Cyd's is color? | cat | blue | cat |
| 47 | gains | 9101-distant-5 | is pet? Ben's What | green | cat | green |
| 47 | known_failures | 9101-correction-0 | What Cyd's is pet? | red | blue | cat |
| 47 | known_failures | 9101-correction-1 | is color? Ada's What | red | blue | cat |
| 47 | regressions | 9101-correction-2 | is pet? Ada's What | red | red | cat |
| 47 | regressions | 9101-correction-4 | What Ben's is pet? | blue | blue | green |
| 47 | unsupported | No example | | | | |

Full histories are in development.json; all decoded answers and token IDs are in raw/*.json. No answer normalization, scripted output or gold-state injection was used. Offline labels only score runtime outputs.

## Output diversity on known facts

```json
{
  "old": {
    "31": {
      "blue": 49,
      "cat": 48,
      "dog": 7,
      "green": 12,
      "owl": 13,
      "red": 15
    },
    "47": {
      "blue": 49,
      "cat": 48,
      "dog": 7,
      "green": 12,
      "owl": 13,
      "red": 15
    }
  },
  "augmented": {
    "31": {
      "cat": 35,
      "dog": 27,
      "green": 45,
      "owl": 36,
      "red": 1
    },
    "47": {
      "cat": 106,
      "green": 38
    }
  },
  "zero": {
    "31": {
      "?": 144
    },
    "47": {
      "?": 144
    }
  }
}
```

## Conditional uncertainty

Two trained checkpoints; paired worlds are clustered across those checkpoints and stratified by development seed/category. These are development diagnostics, not final-test or training-population intervals.

```json
{
  "augmented": {
    "accuracy_95": [
      0.4880952380952381,
      0.5833333333333334
    ],
    "difference_vs_old_95": [
      -0.20833333333333334,
      -0.0625
    ]
  },
  "lexical": {
    "accuracy_95": [
      0.20833333333333334,
      0.2767857142857143
    ],
    "difference_vs_old_95": [
      -0.5,
      -0.36607142857142855
    ]
  },
  "old": {
    "accuracy_95": [
      0.6130952380952381,
      0.7321428571428571
    ],
    "difference_vs_old_95": [
      0.0,
      0.0
    ]
  },
  "recent": {
    "accuracy_95": [
      0.19345238095238096,
      0.25892857142857145
    ],
    "difference_vs_old_95": [
      -0.5119047619047619,
      -0.37797619047619047
    ]
  },
  "zero": {
    "accuracy_95": [
      0.2857142857142857,
      0.2857142857142857
    ],
    "difference_vs_old_95": [
      -0.44642857142857145,
      -0.3273809523809524
    ]
  }
}
```

## Each development world seed

| Method | Training seed | World seed | Exact /56 | Known /40 | Unsupported /16 |
|---|---:|---:|---:|---:|---:|---:|
| augmented | 31 | 9101 | 32 | 16 | 0 |
| augmented | 31 | 9102 | 34 | 18 | 0 |
| augmented | 31 | 9103 | 32 | 16 | 0 |
| augmented | 47 | 9101 | 28 | 12 | 0 |
| augmented | 47 | 9102 | 26 | 10 | 0 |
| augmented | 47 | 9103 | 28 | 12 | 0 |
| lexical | 31 | 9101 | 11 | 1 | 6 |
| lexical | 31 | 9102 | 17 | 3 | 2 |
| lexical | 31 | 9103 | 17 | 3 | 2 |
| lexical | 47 | 9101 | 15 | 5 | 6 |
| lexical | 47 | 9102 | 9 | 4 | 11 |
| lexical | 47 | 9103 | 12 | 2 | 6 |
| old | 31 | 9101 | 34 | 18 | 0 |
| old | 31 | 9102 | 39 | 23 | 0 |
| old | 31 | 9103 | 40 | 24 | 0 |
| old | 47 | 9101 | 34 | 18 | 0 |
| old | 47 | 9102 | 39 | 23 | 0 |
| old | 47 | 9103 | 40 | 24 | 0 |
| recent | 31 | 9101 | 12 | 1 | 5 |
| recent | 31 | 9102 | 19 | 5 | 2 |
| recent | 31 | 9103 | 15 | 2 | 3 |
| recent | 47 | 9101 | 10 | 1 | 7 |
| recent | 47 | 9102 | 8 | 3 | 11 |
| recent | 47 | 9103 | 12 | 2 | 6 |
| zero | 31 | 9101 | 16 | 0 | 0 |
| zero | 31 | 9102 | 16 | 0 | 0 |
| zero | 31 | 9103 | 16 | 0 | 0 |
| zero | 47 | 9101 | 16 | 0 | 0 |
| zero | 47 | 9102 | 16 | 0 | 0 |
| zero | 47 | 9103 | 16 | 0 | 0 |

## Training cost and identities

Total optimizer-loop time: 85.145 seconds; 1,600 optimizer steps and 25,600 sampled world presentations. One Torch CPU thread, float32; no model downloads, GPU jobs or paid compute. Full process durations include startup/checking and are in check records.

```json
{
  "31": {
    "config": {
      "answer_tokens": 12,
      "local_tokens": 96,
      "max_records": 16,
      "query_tokens": 64,
      "record_tokens": 64,
      "slots": 6,
      "width": 48
    },
    "curve": [
      {
        "answer_ce": 5.692324161529541,
        "loss": 6.609908580780029,
        "read_ce": 1.7040493488311768,
        "step": 1,
        "write_ce": 1.9662883281707764
      },
      {
        "answer_ce": 0.6910353302955627,
        "loss": 1.098705768585205,
        "read_ce": 0.7944658398628235,
        "step": 100,
        "write_ce": 0.836215615272522
      },
      {
        "answer_ce": 0.5422700047492981,
        "loss": 0.6824902296066284,
        "read_ce": 0.25879037380218506,
        "step": 200,
        "write_ce": 0.30209052562713623
      },
      {
        "answer_ce": 0.34823569655418396,
        "loss": 0.4030395746231079,
        "read_ce": 0.10206219553947449,
        "step": 300,
        "write_ce": 0.11715324968099594
      },
      {
        "answer_ce": 0.41698959469795227,
        "loss": 0.44544970989227295,
        "read_ce": 0.055876992642879486,
        "step": 400,
        "write_ce": 0.05796352028846741
      },
      {
        "answer_ce": 0.337632954120636,
        "loss": 0.3562512695789337,
        "read_ce": 0.03177294135093689,
        "step": 500,
        "write_ce": 0.04270026832818985
      },
      {
        "answer_ce": 0.36064612865448,
        "loss": 0.3729000687599182,
        "read_ce": 0.02101975865662098,
        "step": 600,
        "write_ce": 0.027996022254228592
      },
      {
        "answer_ce": 0.41446107625961304,
        "loss": 0.42348289489746094,
        "read_ce": 0.016406472772359848,
        "step": 700,
        "write_ce": 0.019680850207805634
      },
      {
        "answer_ce": 0.23510141670703888,
        "loss": 0.2415575087070465,
        "read_ce": 0.011219209991395473,
        "step": 800,
        "write_ce": 0.014605159871280193
      }
    ],
    "data_sha256": "b6264bb32d8b66224de1f1f2d33985f753799a132cf6d44ba1a01c71a1884566",
    "format": "toruk-pooled-router-v2",
    "next_step": 800,
    "parameters": 70208,
    "process_high_water_bytes": 316428288,
    "registration_sha256": "795ceecaf550e3e0bb6128aa96a23e84c759a9521e710bf60d28d70b7af02098",
    "sampled_peak_rss": 315506688,
    "seed": 31,
    "sha256": "9e23717095fef05073cdacd55ce61b65ffbe8efea5406b46032bbd4ff6944a97",
    "steps": 800,
    "tokenizer": "ebf7d205ce6fc5e51a3109713ea3a0c29f01f7d309a8f2f5dca7a9863ea970d7",
    "training_history_tokens": 2431855,
    "training_recipe": "value-fidelity-dev-v1",
    "training_recurrent_padded_positions": 5169616,
    "training_routing_embedding_padded_positions": 3866816,
    "training_seconds": 42.62897460000022
  },
  "47": {
    "config": {
      "answer_tokens": 12,
      "local_tokens": 96,
      "max_records": 16,
      "query_tokens": 64,
      "record_tokens": 64,
      "slots": 6,
      "width": 48
    },
    "curve": [
      {
        "answer_ce": 5.5550007820129395,
        "loss": 6.487760543823242,
        "read_ce": 1.7817715406417847,
        "step": 1,
        "write_ce": 1.949268102645874
      },
      {
        "answer_ce": 0.6282098889350891,
        "loss": 1.0535166263580322,
        "read_ce": 0.8321400880813599,
        "step": 100,
        "write_ce": 0.8690871000289917
      },
      {
        "answer_ce": 0.5461653470993042,
        "loss": 0.6840639114379883,
        "read_ce": 0.2902214229106903,
        "step": 200,
        "write_ce": 0.26137274503707886
      },
      {
        "answer_ce": 0.33405551314353943,
        "loss": 0.3937810957431793,
        "read_ce": 0.10825299471616745,
        "step": 300,
        "write_ce": 0.1306493580341339
      },
      {
        "answer_ce": 0.3605097830295563,
        "loss": 0.39088982343673706,
        "read_ce": 0.05400216579437256,
        "step": 400,
        "write_ce": 0.06751801073551178
      },
      {
        "answer_ce": 0.392586886882782,
        "loss": 0.4135272204875946,
        "read_ce": 0.03281662240624428,
        "step": 500,
        "write_ce": 0.050944700837135315
      },
      {
        "answer_ce": 0.3447909951210022,
        "loss": 0.357980877161026,
        "read_ce": 0.022801600396633148,
        "step": 600,
        "write_ce": 0.02995789796113968
      },
      {
        "answer_ce": 0.2929515540599823,
        "loss": 0.30175116658210754,
        "read_ce": 0.016776971518993378,
        "step": 700,
        "write_ce": 0.018421443179249763
      },
      {
        "answer_ce": 0.2497047781944275,
        "loss": 0.2577638030052185,
        "read_ce": 0.013744081370532513,
        "step": 800,
        "write_ce": 0.018492067232728004
      }
    ],
    "data_sha256": "b6264bb32d8b66224de1f1f2d33985f753799a132cf6d44ba1a01c71a1884566",
    "format": "toruk-pooled-router-v2",
    "next_step": 800,
    "parameters": 70208,
    "process_high_water_bytes": 316440576,
    "registration_sha256": "795ceecaf550e3e0bb6128aa96a23e84c759a9521e710bf60d28d70b7af02098",
    "sampled_peak_rss": 315625472,
    "seed": 47,
    "sha256": "6ece706f9c2fa0bb3cbec0037f0abe073fc1e8b1146d2e2af120fe0516acf555",
    "steps": 800,
    "tokenizer": "ebf7d205ce6fc5e51a3109713ea3a0c29f01f7d309a8f2f5dca7a9863ea970d7",
    "training_history_tokens": 2424322,
    "training_recipe": "value-fidelity-dev-v1",
    "training_recurrent_padded_positions": 5145968,
    "training_routing_embedding_padded_positions": 3843280,
    "training_seconds": 42.51616550000108
  }
}
```

Original source/split/old-checkpoint hashes are in registration.json; new checkpoint hashes were sealed in models.json before inference. New files keep the toruk-pooled-router-v2 model format with an explicit value-fidelity-dev-v1 training recipe and distinct paths/SHA values. All historical artifacts stay intact.

## Exact commands and exit codes

Registration exit-0 evidence is artifacts/checks/value-fidelity-register-20261103.json.

| Check | Exit | Exact argv |
|---|---:|---|
| analysis | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "analyze", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-augmented-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "31", "--method", "augmented", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-augmented-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "47", "--method", "augmented", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-lexical-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "31", "--method", "lexical", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-lexical-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "47", "--method", "lexical", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-old-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "31", "--method", "old", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-old-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "47", "--method", "old", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-recent-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "31", "--method", "recent", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-recent-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "47", "--method", "recent", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-zero-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "31", "--method", "zero", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| development-zero-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "evaluate", "--seed", "47", "--method", "zero", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| model-seal | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "seal", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| train-31 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "train", "--seed", "31", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| train-47 | 0 | `["C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\.venv\\Scripts\\python.exe", "C:\\Users\\susee\\VS_CODE_PROJECT\\Toruk\\scripts\\value_fidelity_dev.py", "train", "--seed", "47", "--run", "artifacts\\value-fidelity-dev-v1-20261103"]` |
| build | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "build", "--no-isolation", "--outdir", "artifacts/value-fidelity-dev-v1-20261103/package"]` |
| chat-paired | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_chat_foundation.py", "--backbone-dir", "artifacts/qwen-chat-001/backbone", "--selector-checkpoint", "artifacts/chat-selector-v2-20261101/selector.json", "--output-dir", "artifacts/value-fidelity-dev-v1-20261103/chat-paired"]` |
| cli-diagnose | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "diagnose"]` |
| cli-help | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "toruk_lm", "--help"]` |
| diff-check | 0 | `["git", "diff", "--check"]` |
| final-focused-format | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "scripts/value_fidelity_dev.py", "scripts/report_value_fidelity_dev.py", "scripts/audit_value_fidelity_dev.py", "tests/test_value_fidelity_dev.py"]` |
| final-focused-lint | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "scripts/value_fidelity_dev.py", "scripts/report_value_fidelity_dev.py", "scripts/audit_value_fidelity_dev.py", "tests/test_value_fidelity_dev.py"]` |
| final-independent-scoring | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/audit_value_fidelity_dev.py", "--run", "artifacts/value-fidelity-dev-v1-20261103"]` |
| final-types | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy", "--follow-imports", "silent", "src/toruk_lm", "scripts/value_fidelity_dev.py", "scripts/report_value_fidelity_dev.py", "scripts/audit_value_fidelity_dev.py"]` |
| format | 1 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "src", "tests", "scripts"]` |
| independent-scoring | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/audit_value_fidelity_dev.py", "--run", "artifacts/value-fidelity-dev-v1-20261103"]` |
| lint | 1 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", ".", "--output-format", "concise"]` |
| live-page-handlers | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/smoke_qualification_ui.py", "--output-dir", "artifacts/value-fidelity-dev-v1-20261103/live-page-handlers"]` |
| node-check | 0 | `["npm.cmd", "--prefix", "web/vercel", "run", "check"]` |
| node-tests | 0 | `["npm.cmd", "--prefix", "web/vercel", "test"]` |
| package-dependencies | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "pip", "check"]` |
| python-tests | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "pytest", "-q", "-p", "no:cacheprovider"]` |
| report-format | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "format", "--check", "scripts/report_value_fidelity_dev.py"]` |
| report-lint | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "ruff", "check", "scripts/report_value_fidelity_dev.py"]` |
| study-help | 0 | `[".\\.venv\\Scripts\\python.exe", "scripts/value_fidelity_dev.py", "--help"]` |
| types-linux | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy", "--platform", "linux", "--follow-imports", "silent", "src/toruk_lm", "scripts/value_fidelity_dev.py", "scripts/report_value_fidelity_dev.py"]` |
| types | 0 | `[".\\.venv\\Scripts\\python.exe", "-m", "mypy", "--follow-imports", "silent", "src/toruk_lm", "scripts/value_fidelity_dev.py", "scripts/report_value_fidelity_dev.py"]` |

This completes one development gate. No final qualification, research-paper claim, resource advantage, chat integration or deployment milestone is started. Finite shared symbols, synthetic permutations, two training seeds and shared-host timing limit interpretation. Original final answers were never used to fit this recipe.
