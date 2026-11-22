"""Offline contracts for the added observed-error comparison."""

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_first_token_margins as review  # noqa: E402


def test_observed_error_margin_is_distinct_from_top_and_runner_up() -> None:
    logits = [-100.0] * 259
    logits[112], logits[118], logits[111] = 8.0, 7.0, 3.0
    result = review.margins(logits, 112, 111)
    assert result["expected_rank"] == 1
    assert result["expected_minus_top"] == 0
    assert result["expected_minus_best_other"] == 1
    assert result["expected_minus_observed_error"] == 5


def test_wrong_gold_rank_and_no_invented_error_for_correct_archived_case() -> None:
    logits = [-100.0] * 259
    logits[111] = 3.0
    logits[112] = 2.5
    result = review.margins(logits, 112, 111)
    assert result["expected_rank"] == 2 and result["expected_minus_top"] == -0.5
    assert result["expected_minus_observed_error"] == -0.5
    assert review.margins(logits, 111, None)["expected_minus_observed_error"] is None


def test_hashes_preserve_native_ids_and_nonfinite_stops() -> None:
    assert review.id_hash([1, 66, 64]) != review.id_hash([66, 64])
    with pytest.raises(ValueError, match="finite"):
        review.margins([float("nan")] * 259, 112, 111)


def test_review_source_is_standard_library_only_and_has_no_inference_calls() -> None:
    tree = ast.parse(Path(review.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module]
            assert all(name and name.split(".")[0] in sys.stdlib_module_names for name in names)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {
                "forward",
                "generate",
                "backward",
                "step",
                "load_state_dict",
            }
