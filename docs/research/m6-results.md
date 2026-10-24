# M6 registered validation results

Run: `artifacts/m6-validation-001`, 2026-10-20 (Asia/Calcutta). Base commit `a025f0148965089b24a69344a13cd8a6447afef9`; source is uncommitted. Status: **PARTIAL**. Protocol: [frozen validation design](m6-validation-protocol.md).

## Per-seed quality (seed 23)

Four validation worlds, 24 generated answers per configuration. Primary corrected/preserved known-fact macro accuracy is **0% for every configuration**. These results do not establish useful memory or revision.

| Configuration | Primary | All-answer exact accuracy | Attempted-answer coverage | Answer CE | History CE | Inference seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no-correction-write | 0.0% | 0.0% | 83.3% | 4.1113 | 5.4308 | 2.182 |
| no-preservation-write | 0.0% | 0.0% | 100.0% | 4.9466 | 5.1634 | 3.441 |
| ordinary-wide-write | 0.0% | 0.0% | 100.0% | 3.2422 | 5.1684 | 1.376 |
| ordinary-write | 0.0% | 33.3% | 0.0% | 3.8520 | 5.3568 | 0.965 |
| recurrent-predictor | 0.0% | 12.5% | 29.2% | 3.7912 | 5.1837 | 2.697 |
| recurrent-write | 0.0% | 8.3% | 33.3% | 3.7933 | 5.1837 | 3.330 |
| revision-heuristic | 0.0% | 0.0% | 83.3% | 4.1968 | 5.2339 | 2.695 |
| revision-predictor | 0.0% | 0.0% | 83.3% | 4.1972 | 5.2339 | 3.288 |
| revision-random | 0.0% | 0.0% | 83.3% | 4.1972 | 5.2339 | 3.457 |
| revision-reset | 0.0% | 0.0% | 83.3% | 4.2989 | 5.2932 | 3.684 |
| revision-retain | 0.0% | 0.0% | 83.3% | 4.1972 | 5.2339 | 3.293 |
| revision-write | 0.0% | 0.0% | 83.3% | 4.1969 | 5.2339 | 3.741 |
| slots2-write | 0.0% | 0.0% | 50.0% | 3.7947 | 5.1840 | 2.301 |
| slots8-write | 0.0% | 8.3% | 33.3% | 3.7904 | 5.1826 | 2.552 |

CE is teacher-forced nats/byte-or-newline, separate from generated-answer accuracy. Inference times are single-run history processing plus answer generation, excluding load and offline answer scoring. They are not statistically reliable speed comparisons.

## Model and training resources

| Training configuration | Parameters | Recurrent-state bytes | Steps | Training forward-token positions | Optimizer-loop seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| no-correction | 57,088 | 512 | 12 | 7,137 | 1.426 |
| no-preservation | 57,088 | 512 | 12 | 7,137 | 2.099 |
| ordinary | 44,096 | 0 | 12 | 26,397 | 3.295 |
| ordinary-wide | 62,800 | 0 | 12 | 26,397 | 2.700 |
| recurrent | 57,088 | 512 | 12 | 7,137 | 1.556 |
| revision | 57,088 | 512 | 12 | 7,137 | 1.544 |
| slots2 | 56,960 | 256 | 12 | 7,137 | 1.652 |
| slots8 | 57,344 | 1024 | 12 | 7,137 | 1.286 |

All recurrent four-slot models have 57,088 parameters; each predictor adds 4,641 parameters (61,729 combined). The wide ordinary sensitivity has 62,800 parameters, approximately 1.7% more than that combined count. Parameter proximity does not match FLOPs or total training cost.

## Effect estimation diagnostics

| Bound checkpoint | RMSE nats | Sign ranking | Harm recall | Harm precision | Fallback worlds | Predictor regret | Heuristic regret | Retain regret |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| recurrent | 0.002765 | 0.50 | 0.50 | 1.00 | 4/4 | 0.000000 | 0.002054 | 0.000000 |
| revision | 0.000856 | 0.50 | 0.50 | 0.50 | 4/4 | 0.000513 | 0.000117 | 0.000513 |

Regret uses offline best-branch answer NLL at one fixed final-history boundary. Oracle regret is zero by construction, not evidence of a deployable oracle. Calibration bins/raw effects are retained in the effect-eval metrics. Four validation labels cannot establish calibration. Raw MLP timing was approximately 33 microseconds/example (recurrent) and 103 microseconds/example (revision), vectorized over four examples, excluding feature extraction/support checks; deployed decisions fell back before MLP execution.

## Registered costs

The registered process took 90.935 seconds wall time; driver stages took 87.341 seconds. Cumulative process peak working set: 352,514,048 bytes (336.18 MiB). This includes interpreter/framework and all stages, not per-model tensor allocation.

```json
{
  "branch_count": 32,
  "branch_generated_forward_tokens": 107808,
  "failed_stages": [],
  "label_forward_tokens": 13066,
  "label_generation_seconds": 25.28509999999369,
  "lm_training_seconds": 16.981316299992613,
  "note": "Includes profiles/labels/predictors in this pilot. Earlier test/failed-check costs are separate check records; no total CPU-hours claim.",
  "predictor_steps": 200,
  "predictor_training_seconds": 0.3798924000002444,
  "total_lm_optimizer_steps": 100,
  "train_forward_tokens": 101256
}
```

Retained failed tiny pilot costs (additional to the registered pilot):

```json
{
  "reason": "predictor/evaluation output directory collision; corrected, no metric-based retry",
  "lm_steps": 6,
  "train_forward_tokens": 8344,
  "training_seconds": 1.2734797000157414,
  "branches": 8,
  "label_seconds": 3.6529788999905577,
  "predictor_steps": 100,
  "stage_wall_seconds": 9.089848899981007
}
```

Full current-task check wall times, including tests and failed checks, are recorded separately in `artifacts/checks/m6-*.json` and summed in `artifacts/m6-analysis.json`. They overlap and are not CPU time. Test-suite optimizer/token accounting is incomplete; no comprehensive CPU-hour total is claimed.

## Failure analysis and limits

The ordinary model returned `?` to every question. Its 33.3% overall accuracy is
solely eight unknown/ambiguous answers, with zero attempted-answer coverage.
Revision answers include plausible but wrong colors (`gold`) and malformed
names/dates/numbers (`gd`, `gol`); the wide ordinary model repeated `2020...`.
All sixteen known-fact answers per configuration were wrong. No configuration is
a demonstrated strongest Toruk model: all tie at the primary endpoint.

Nonzero writer gradients, causal/session tests and checkpoint parity establish
execution, not useful delayed memory. Twelve steps and bundled template/entity/
update-count shifts are plausible explanations, not isolated causal diagnoses.
The run was not extended or modified to find a favorable score.

Both predictors rejected all four validation decisions as out of support. Only
the final write was suppressed; preceding writes still occurred. Recurrent
predictor regret equals fixed retain, so it demonstrates no learned advantage.
Revision predictor regret (0.000513 nats) is worse than heuristic (0.000117).
Shuffling identical fallback decisions is uninformative; the independent seeded
random runtime diagnostic is retained separately. Four labels and 50% sign ranking
do not establish calibration. Raw MLP timing excludes feature/support checks;
deployed fallbacks happened before MLP execution.

Objective and 2/4/8-slot ablations all hit the known-fact learning floor; no
component contribution or saturation conclusion follows. Reset is additionally
an inference distribution shift. Posthoc validation counts by history length,
distractors, evidence distance and known-fact density are in
`artifacts/m6-analysis.json`: known-fact accuracy remains zero in every populated
stratum. These tiny correlated strata are descriptive, not confirmatory endpoints.
Validation has three corrections per world, so a correction-count curve is absent.

## Checks, status and reproduction

Local PASS: 24 tests, no skips, including real CLI train/reload/generate/score
comparisons; Ruff lint/format; mypy (13 package files); dependency/package checks;
CLI help/diagnostics. The optional NumPy warning is retained. Initial FAIL
records include typing/lint issues, a grad/no-grad parity mismatch and directory
collision. Session parity now uses the same no-grad inference context; bitwise
assertions were not relaxed. Evidence: `artifacts/checks/m6-final-*`.

Remote PASS covers existing HEAD `a025f0148965089b24a69344a13cd8a6447afef9` only:
[CPU foundation run 39294787042](https://github.com/ShamGaneshan2008/Toruk/actions/runs/39294787042).
The fresh exact-SHA API response is `artifacts/m6-remote-runs.json`. New source,
tests and documentation are uncommitted/unpushed and NOT_RUN remotely. No workflow
was triggered or paid compute started.

```powershell
.\.venv\Scripts\python.exe scripts/check.py m6-pilot-reproduction -- .\.venv\Scripts\python.exe -m toruk_lm controlled-pilot --output artifacts/m6-reproduction --steps 12 --worlds 4 --answer-budget 16 --seconds 110
```

Use a fresh output/label. Final test: NOT_RUN. Across-seed uncertainty: not
estimable. Fully matched total training/inference compute: NOT_RUN. M6 is
**PARTIAL**: prerequisite prototype execution and a negative validation pilot,
not verified correction/preservation capability. Before M7: meaningful validation
learning, multiple seeds, factorized held-out shifts, stronger resource controls,
complete compute accounting and a separately frozen final test. No novelty,
superiority or efficiency claim follows; related-work overlap remains.
