"""A replay must compare actual prompts and answers, not just aggregate scores."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

SPEC = importlib.util.spec_from_file_location(
    "compare_recall_runs", Path(__file__).resolve().parents[1] / "scripts/compare_recall_runs.py"
)
assert SPEC and SPEC.loader
comparison = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(comparison)


def fixture_runs(tmp_path: Path) -> tuple[Path, Path]:
    paths = (tmp_path / "reference", tmp_path / "replay")
    for path in paths:
        path.mkdir()
        for stage in ("development", "heldout"):
            rows: list[dict[str, Any]] = []
            for index in range(12):
                for method in ("recent", "lexical", "old", "new"):
                    row = dict.fromkeys(comparison.FIELDS)
                    row.update(case={"id": f"{stage}-{index}"}, method=method, answer="answer")
                    row["metrics"] = dict.fromkeys(comparison.METRICS)
                    row["metrics"]["response_ms"] = 10 if path == paths[0] else 20
                    rows.append(row)
            (path / f"{stage}.jsonl").write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
            )
    return paths


def test_replay_allows_timing_variance_but_detects_prompt_drift(tmp_path: Path) -> None:
    reference, replay = fixture_runs(tmp_path)
    assert comparison.compare(reference, replay)["exact_reproduction"]
    path = replay / "heldout.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["prompt_ids"] = [42]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    result = comparison.compare(reference, replay)
    assert not result["exact_reproduction"]
    assert result["stages"]["heldout"]["differences"][0]["fields"] == ["prompt_ids"]


def test_replay_rejects_duplicate_case_method_rows(tmp_path: Path) -> None:
    reference, replay = fixture_runs(tmp_path)
    path = replay / "heldout.jsonl"
    lines = path.read_text().splitlines()
    lines[-1] = lines[0]
    path.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(ValueError, match="Incomplete or duplicate"):
        comparison.compare(reference, replay)
