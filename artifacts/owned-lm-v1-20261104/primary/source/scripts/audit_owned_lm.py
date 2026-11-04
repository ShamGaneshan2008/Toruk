"""Read-only audit of owned-study identities/accounting and optional chat replay."""

import argparse
import json
from pathlib import Path
from typing import Any

from study_owned_lm import sha, success

from toruk_lm.owned_data import digest
from toruk_lm.owned_training import runtime_identity, write_json


def audit(run: Path, chat_reference: Path | None, chat_replay: Path | None) -> dict:
    def read(path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    registration = read(run / "registration.json")
    freeze = read(run / "freeze.json")
    summary = read(run / "summary.json")
    assert runtime_identity() == registration["runtime"] == freeze["runtime"]
    assert sha(Path(__file__).with_name("study_owned_lm.py")) == freeze["driver_sha256"]
    for split, binding in registration["manifest"]["splits"].items():
        rows = read(run / "data" / f"{split}.json")
        assert digest(rows) == binding["sha256"]
        assert len(rows) == binding["count"]
    train_rows = read(run / "data/train.json")
    full = {}
    for name, recorded in summary["heldout"].items():
        result = read(run / "heldout" / f"{name}.json")
        assert {k: v for k, v in result.items() if k != "rows"} == recorded
        checkpoint_name = f"{result['seed']}-{result['variant']}"
        assert result["checkpoint_sha256"] == freeze["checkpoints"][checkpoint_name]
        assert (
            sha(run / "models" / checkpoint_name / "checkpoint.pt") == result["checkpoint_sha256"]
        )
        assert result["dataset"] == registration["manifest"]["splits"]["heldout"]["sha256"]
        assert result["questions"] == len(result["rows"])
        assert result["correct"] == sum(row["correct"] for row in result["rows"])
        for row in result["rows"]:
            answer = row["generation"]["answer"].strip()
            assert row["correct"] == (answer == row["expected"])
            assert row["nll_forward_positions"] == row["targets"]
            assert (
                len(row["generation"]["generated_ids"]) <= registration["config"]["max_new_tokens"]
            )
        full[name] = result
    assert success(full, registration["config"]["seeds"]) == summary["criterion"]
    for name, training in summary["training"].items():
        trace = read(run / "models" / name / "checkpoint.json")["trace"]
        by_id = {row["id"]: row for row in train_rows}
        assert sum(row["targets"] for row in trace) == training["training_targets_total"]
        assert (
            sum(
                len(by_id[item]["text"].encode()) + 1
                for row in trace
                for item in row["document_ids"]
            )
            == training["training_targets_total"]
        )
    chat_count = 0
    if chat_reference is not None and chat_replay is not None:

        def stable(row: dict) -> dict:
            row = {k: v for k, v in row.items() if k not in ("timing", "memory")}
            row["metrics"] = {k: v for k, v in row["metrics"].items() if k != "response_ms"}
            return row

        for suite in ("controlled", "independent"):
            old = [
                json.loads(line)
                for line in (chat_reference / f"{suite}.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            new = [
                json.loads(line)
                for line in (chat_replay / f"{suite}.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            assert len(old) == len(new)
            assert [stable(row) for row in old] == [stable(row) for row in new]
            chat_count += len(new)
    result = {
        "status": "PASS",
        "model_inference": False,
        "owned_evaluations": len(full),
        "chat_answers_exactly_reproduced": chat_count,
        "criterion": summary["criterion"]["passed"],
    }
    write_json(run / "audit.json", result)
    print(json.dumps(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--chat-reference", type=Path)
    parser.add_argument("--chat-replay", type=Path)
    args = parser.parse_args()
    audit(args.run, args.chat_reference, args.chat_replay)


if __name__ == "__main__":
    main()
