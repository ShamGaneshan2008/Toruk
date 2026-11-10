# Qwen development v5 evidence

Development only. The study protocol is
`docs/research/qwen-development-v5-protocol.md`; results are in the adjacent v5
report. No production behavior, frozen v1-v4 evidence, weights or scorer changed.

`attempt-001/` preserves the first registration and source snapshot. It generated
no answers and was superseded before inference solely to correct static typing
of dynamic research worker adapters. `preflight-notes.md` and `checks/` retain
the failed and corrected Mypy checks and both preparation costs.

`attempt-002/registration.json` seals all conditions before inference. Its
`source.zip` retains exact as-run new and inherited implementation bytes.
`baseline.json` seals pre-existing tracked research evidence and runtime source;
held-out files are hashed as opaque bytes only. Registration binds the local
backbone and selector assets by their original hashes, read from the earlier
C-drive checkout without modifying it. Weights are not duplicated here.

Each `attempt-002/arms/<condition>/rehearsal/` contains registration, the exact
seven development questions, tokenizer-only full-prompt IDs, raw answer JSONL,
logs, progress, worker telemetry, resource monitor heartbeats and stage costs.
Raw rows preserve all supplied sources, prompt/output IDs, answers, frozen scores,
failure labels, selection/fitting/generation/request costs and token counts.
`results.json` summarizes seven-case and replay-inclusive results separately.
`development-cost.json` includes every cold stage, including replay and setup.

Engineering check receipts remain in `checks/` and `verification/`. Generated
fixture directories and wheels/sdists are deliberately local and ignored; they
are not Qwen study inputs or evidence of held-out quality. Original historical
evidence is left byte-identical. Do not run the broad portable-v1 verifier here:
it also rescores historical held-out records. Use the development-only v4
portable verifier documented in `artifacts/qwen-long-history-dev-v4/README.md`.

From the checkout root, with the existing development/chat environment:

```powershell
.venv/Scripts/python.exe artifacts/qwen-long-history-dev-v4/verify.py --output <fresh-receipt.json>
.venv/Scripts/python.exe -m pytest -q tests/test_qwen_development_v5.py
.venv/Scripts/python.exe scripts/verify.py --prefix v5 --output-dir <fresh-verification-directory>
git diff --check
```

The registered inference action is single-use. Do not rerun it, change its
instructions after answers, or overwrite any receipts. Existing registration,
source ZIP, start receipt and raw results retain the execution chronology.
Scoped attributes preserve the new source/config/protocol bytes as LF while
leaving all earlier frozen attribute rules unchanged; artifact bytes stay raw.
