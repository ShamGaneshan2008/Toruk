"""Static study data and disposable numerical contracts, no study fits or answers."""

import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import local_answer_dev as study  # noqa: E402

from toruk_lm.engine import setup  # noqa: E402
from toruk_lm.owned_lm import OwnedConfig, OwnedSession, build_model  # noqa: E402


def test_split_coverage_template_balance_local_placement_and_parser():
    files = study.datasets()
    study.validate(files)
    for split in ("train", "dev"):
        for case, label in zip(
            files[f"{split}-inputs.json"], files[f"{split}-labels.json"], strict=True
        ):
            assert study.parser_answer(case["prefix"]) == label["gold"]
            hidden = study.question_only(case["prefix"])
            assert len(hidden.encode()) == len(case["prefix"].encode())
            assert hidden.splitlines()[-1] == case["prefix"].splitlines()[-1]
            assert study.parser_answer(hidden) == "?"
    files["dev-labels.json"][0]["gold"] = "?"
    with pytest.raises(ValueError, match="source"):
        study.validate(files)


def test_strict_scorer_completion_and_repetition():
    assert study.score([85, 48, 58, 2], "R-7")
    for wrong in ([85, 48, 58], [35, 85, 48, 58, 2], [85, 48, 58, 35, 2], [2]):
        assert not study.score(wrong, "R-7")
    assert study.classify([2]) == dict(eos=True, malformed=True, repetitive=False)
    assert study.classify([ord("x") + 3] * 3)["repetitive"]


@pytest.mark.parametrize("variant", ["ordinary_matched", "memory_on"])
def test_uniform_target_accounting_and_session_alignment_on_disposable_fixture(variant):
    setup(900307, 1)
    model = build_model(OwnedConfig(context=8, width=8, heads=2, layers=1, slots=2), variant)
    prefix = "abcdefg" + "x=b\nx?="
    documents = [dict(prefix=prefix, text=prefix + "b")]
    x, y, answer = study.make_batch(documents, context=8)
    assert answer.sum() == 2 and int(y[0, len(prefix)]) == ord("b") + 3
    logits = study.forward_batch(model, x)
    torch.testing.assert_close(
        OwnedSession(model).consume([1, *(b + 3 for b in prefix.encode())]),
        logits[0, len(prefix)],
        atol=1e-6,
        rtol=1e-6,
    )
    objective, stats = study.batch_objective(model, documents)
    direct = torch.nn.functional.cross_entropy(logits.transpose(1, 2), y)
    torch.testing.assert_close(objective, direct)
    assert stats["answer_targets"] == 2
    objective.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
