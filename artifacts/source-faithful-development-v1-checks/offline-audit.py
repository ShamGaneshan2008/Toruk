"""Post-study saved-output audit only. No model weights, training or generation."""

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import source_faithful_development_v1 as study  # noqa: E402
from evidence_first_policy import answer, make_view  # noqa: E402
from qwen_long_history import envelope  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402


def main():
    base, run = study.base, study.RUN
    record = study.verify_freeze()
    cases = {c["id"]: c for c in base.read(run / "inputs.json")}
    labels = {c["id"]: c for c in base.read(run / "labels-evaluator-only.json")}
    tokenizer = AutoTokenizer.from_pretrained(
        ROOT / "artifacts/research-evidence-portable-v1/tokenizers/qwen",
        local_files_only=True, trust_remote_code=False,
    )
    rows = [r for n, order in enumerate(study.ORDER, 1) for cell in order
            for r in base.rows(run / f"pass-{n}" / cell / "requests.jsonl")]
    results = base.read(run / "results.json")
    policy_rows = 0
    for row in rows:
        assert row["failure"] is None
        messages = cases[row["case"]]["messages"]
        view = make_view(messages, row["selected_indices"], row["fitted_indices"])
        expected = [{"turn": s.interval.turn, "start": s.interval.start, "end": s.interval.end,
                     "content": s.raw.decode(), "revision": s.revision,
                     "sha256": s.turn_sha256} for s in view.sources]
        assert row["fitted_sources"] == expected
        assert row["prompt_messages"] == envelope(messages, row["fitted_indices"])
        if row["policy"] is not None:
            policy_rows += 1
            policy = answer(view, token_count=lambda text: len(
                tokenizer.encode(text, add_special_tokens=False)))
            assert json.loads(json.dumps(asdict(policy))) == row["policy"]
            assert row["payload"] == policy.payload and row["lm_calls"] == 0
        else:
            assert row["payload"] == row["raw_generated"].strip()
        if not row["replay"]:
            scored = study.score(labels[row["case"]], row)
            saved = results["report"]["scores"][str(row["pass"])][row["cell"]][row["index"]]
            assert scored == saved
    for row, scheduled in zip(rows, record["requests"], strict=True):
        assert all(row[key] == value for key, value in scheduled.items())
    for key, field in (("lm_calls", "lm_calls"), ("input_tokens", "executed_input_tokens"),
                       ("output_tokens", "executed_output_tokens")):
        assert results[key] == sum(r[field] for r in rows)
    for dimension in ("wall", "cpu"):
        assert abs(results[f"total_{dimension}_seconds"] - (
            results[f"stage_{dimension}_seconds"] + results["shared"][f"{dimension}_seconds"]
        )) < 1e-8
    stages = [base.read(run / f"pass-{n}-{cell}-cost.json")
              for n, order in enumerate(study.ORDER, 1) for cell in order]
    rescored = study.evaluate(rows, stages, results["shared"], True)
    assert rescored == results["report"]
    for name, wanted in base.read(run / "output-sha256.json")["files"].items():
        assert base.file_sha(run / name) == wanted
    print(json.dumps({"status": "PASS", "saved_rows": len(rows),
                      "offline_policy_replays": policy_rows, "score_replays": 96,
                      "frozen_schedule_and_cost_reconciliation": True,
                      "new_model_generations": 0}, indent=2))


if __name__ == "__main__":
    main()
