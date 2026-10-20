# M5 prerequisite audit

2026-10-20 (Asia/Calcutta). **M5 BLOCKED before implementation.**
Starting branch: `main`; HEAD: `a025f0148965089b24a69344a13cd8a6447afef9`.
Existing M4 documentation/evidence edits were present and preserved. No
AGENTS.md was found in the repository/ancestor locations. Reviewed the request,
README, internal research notes, registry, source, configurations, tests and CI.

## M4 verification

The package still implements only an ordinary causal LM. The actual forward
interface accepts token tensors and returns logits, without memory state; the
trainer uses independent shuffled windows; the generator retains a token suffix.
There is no recurrent writer, paired-label generator, effect predictor or
revision module. The fixture emits prose journals, not controlled-world events.
The public CLI exposes only diagnose/make-fixture/train/evaluate/generate.

| M4 acceptance requirement | Status | Evidence |
| --- | --- | --- |
| Candidate branches share initial model/memory | BLOCKED | No M3 memory or branch evaluator in the implementation |
| Labels separate from runtime predictor inputs | BLOCKED | No predictor feature/label code; an unexecuted draft is not a leakage test |
| Comparable branch targets and randomness | BLOCKED | No branch evaluations or paired labels |
| Predictor training, checkpointing, inference | BLOCKED | No predictor implementation/checkpoint; retained checkpoint is ordinary LM only |
| Recurrent baseline and simple alternatives | BLOCKED | No recurrent model or predictor comparison |
| Predictor cost and measured results | BLOCKED | Prior manifest records zero branch labels and null predictor metrics |
| Leakage tests | NOT_RUN | Only ordinary-foundation tests exist |
| Reproducible bounded M4 pilot | BLOCKED | No M4 CLI flow or executable pilot |

The current source/config/test/workflow identity exactly matches the previously
verified snapshot: SHA256
`9df6808d9a8d8b753ebc0f7159ffbf104d9117ef2463810fb664b4be27236b39`.
Before appending this handoff, all 49 prior sealed evidence/document files were
rehash-verified and all 15 recorded checks had PASS status. This verifies the
origin of prior checks; it does not turn those checks into M4 verification.
Later registry/status additions naturally change those documents' current hashes;
the historical manifest is preserved. See `artifacts/m5-prerequisite-audit.json`.

M4 cannot be established by a local repair: the entire M2 controlled-world
generator/oracle/scorer and M3 recurrent baseline are missing. Their implementation,
training and validation comparison must precede an M4 paired-label/predictor pilot.
Per the request's explicit stop condition, this task stops at that gate rather
than adding revision losses, a second benchmark, or a predictor surrogate.

## M5 method, metrics and costs

No M5 objective, controller, model, data extension or experiment was implemented.
No final M5 protocol was frozen and no final test worlds/labels were opened.
Correction/preservation accuracies, baseline comparisons, uncertainty, predictor
overhead and peak memory are **NOT_RUN**, not zero-valued results. There is no
M5 end-to-end run or reproduction command. New model training and branch-label
generation in this task: zero steps. This is a blocked dependency, not a null
research result. A conditional M4 design remains in `m4-effect-predictor.md`.

## Checks and reproduction

Fresh CLI inspection (120-second timeout; PASS):

```powershell
.\.venv\Scripts\python.exe scripts/check.py m5-gate-help -- .\.venv\Scripts\python.exe -m toruk_lm --help
```

Use a new label when retaining another check so existing logs remain intact.
Evidence: `artifacts/checks/m5-gate-help.{json,log}`. Fresh whitespace check:
`git diff --check`, recorded as `m5-gate-diff`. Source/evidence identity validation
is recorded in `artifacts/m5-prerequisite-audit.json` with its verification code.

Previously executed checks for the identical source: PASS install, dependency,
import, help/console, diagnostics, Ruff lint/format, mypy, pytest (9 passed, no
skips), package build and whitespace checks. They were not rerun as M5 tests;
there are no M5 tests to run. Evidence: `artifacts/checks/m4-gate-*`.
Prior foundation validation loss was 1.2481076462 nats/byte-or-EOS over 925
targets. This is an ordinary prose-continuation result, not correction accuracy.
Prior training/pilot costs and limitations remain in `m4-prerequisite-audit.md`.

Remote evidence previously retrieved for the unchanged exact HEAD is PASS:
[CPU foundation push run 39294787042](https://github.com/ShamGaneshan2008/Toruk/actions/runs/39294787042).
The recorded response is `artifacts/m4-remote-runs.json`. This audit reused that
same-commit evidence; it did not query or trigger another remote run. Local M4/M5
documentation edits remain uncommitted and unpushed, with remote status NOT_RUN.

## Evidence required before M6

First independently verify M2 world/event semantics, corrections and ambiguity,
document/template splits and autoregressive answer scoring. Establish the M3
state/writer, causal timing, resets, gradients, isolation, resume and matched
ordinary/recurrent comparison. Then implement and validate M4 paired branches,
future-free runtime features, cache identity, predictor learning/reload, calibration,
baselines, measured costs and a reproducible bounded pilot. Only after these gates
can M5 freeze correction-versus-preservation endpoints, train the revision model
and compare genuine deployed decision policies. M6 additionally needs those M5
raw generated answers, uncertainty and full cost accounting for fair ablations.

No source/tests/workflow changes, commit, push, publication, tag, visibility
change or paid compute occurred. Existing edits were retained.
