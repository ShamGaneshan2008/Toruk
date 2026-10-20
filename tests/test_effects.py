import json

import pytest
import torch

from toruk_lm.controlled import train_controlled
from toruk_lm.data import sha256_file
from toruk_lm.effect_predictor import EffectPredictor, features
from toruk_lm.effect_training import evaluate_effect, fit_effect, paired_labels
from toruk_lm.model import ModelConfig
from toruk_lm.worlds import make_worlds


def test_feature_api_shapes_finite_fallback_and_no_offline_imports():
    import inspect

    import toruk_lm.effect_predictor as runtime

    source = inspect.getsource(runtime)
    assert "from toruk_lm.worlds" not in source
    assert "from toruk_lm.effect_training" not in source
    assert list(inspect.signature(features).parameters) == ["previous", "proposed", "summary"]
    old, new, summary = torch.zeros(1, 2, 8), torch.ones(1, 2, 8), torch.ones(1, 8)
    assert features(old, new, summary).shape == (1, 40)
    predictor = EffectPredictor(40)
    assert torch.isfinite(predictor(features(old, new, summary))).all()
    assert not predictor.recommend(old, new * float("nan"), summary)
    assert not predictor.recommend(old, new * 100, summary)
    assert predictor.fallbacks == 2
    with pytest.raises(ValueError, match="shape"):
        features(old, new[:, :1], summary)


def test_real_pair_fit_evaluate_cache_determinism_and_checkpoint(tmp_path):
    data, run = tmp_path / "data", tmp_path / "model"
    make_worlds(data, worlds_per_split=2)
    train_controlled(
        data / "train.jsonl",
        data / "validation.jsonl",
        run,
        "recurrent",
        steps=1,
        config=ModelConfig(width=8, heads=2, layers=1),
    )
    checkpoint = run / "checkpoint.pt"
    first = paired_labels(
        checkpoint, data / "train.jsonl", tmp_path / "labels", limit=2, answer_budget=2
    )
    repeat = paired_labels(
        checkpoint, data / "train.jsonl", tmp_path / "repeat", limit=2, answer_budget=2
    )
    assert first["features"] == repeat["features"]
    assert first["labels"] == repeat["labels"]
    assert first["no_weight_updates"]
    for row in first["labels"]:
        left, right = row["branches"]
        assert left["initial_state_sha256"] == right["initial_state_sha256"]
        assert left["targets"] == right["targets"]
        assert [(p["question"], p["gold"]) for p in left["probes"]] == [
            (p["question"], p["gold"]) for p in right["probes"]
        ]
    fitted = fit_effect(tmp_path / "labels/labels.json", tmp_path / "predictor", steps=3)
    assert fitted["max_gradient_norm"] > 0
    model = EffectPredictor.load(tmp_path / "predictor/predictor.pt", sha256_file(checkpoint))
    x = torch.tensor(first["features"])
    reloaded = EffectPredictor.load(tmp_path / "predictor/predictor.pt", sha256_file(checkpoint))
    torch.testing.assert_close(model(x), reloaded(x), rtol=0, atol=0)
    paired_labels(
        checkpoint,
        data / "validation.jsonl",
        tmp_path / "val-labels",
        "validation",
        limit=2,
        answer_budget=2,
    )
    result = evaluate_effect(
        tmp_path / "predictor/predictor.pt", tmp_path / "val-labels/labels.json", tmp_path / "eval"
    )
    assert set(result["policies"]) == {
        "retain",
        "write",
        "predictor",
        "heuristic",
        "shuffled",
        "oracle",
    }
    with pytest.raises(ValueError, match="identity"):
        paired_labels(
            checkpoint, data / "train.jsonl", tmp_path / "labels", limit=1, answer_budget=2
        )
    with pytest.raises(ValueError, match="identity"):
        paired_labels(
            checkpoint,
            data / "validation.jsonl",
            tmp_path / "labels",
            "validation",
            answer_budget=2,
        )
    with pytest.raises(ValueError, match="identity"):
        EffectPredictor.load(tmp_path / "predictor/predictor.pt", "different-checkpoint")
    changed = torch.load(checkpoint, weights_only=True)
    changed["model"][next(iter(changed["model"]))] += 0.01
    torch.save(changed, tmp_path / "changed.pt")
    with pytest.raises(ValueError, match="identity"):
        paired_labels(tmp_path / "changed.pt", data / "train.jsonl", tmp_path / "labels")
    path = tmp_path / "labels/labels.json"
    corrupt = json.loads(path.read_text())
    corrupt["features"][0][0] += 1
    path.write_text(json.dumps(corrupt))
    with pytest.raises(ValueError, match="corrupt"):
        paired_labels(
            checkpoint, data / "train.jsonl", tmp_path / "labels", limit=2, answer_budget=2
        )
