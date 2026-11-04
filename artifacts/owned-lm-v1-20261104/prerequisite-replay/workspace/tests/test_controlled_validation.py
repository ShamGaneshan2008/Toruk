"""Controlled models retain the finite-checkpoint guarantee of the foundation."""

from dataclasses import asdict

import pytest
import torch

from toruk_lm.controlled import load_controlled
from toruk_lm.model import CausalLM, ModelConfig
from toruk_lm.recurrent import RecurrentLM
from toruk_lm.tokenizer import ByteTokenizer


@pytest.mark.parametrize("variant", ["ordinary", "recurrent"])
@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_controlled_nonfinite_weights_fail_before_inference(tmp_path, variant, value):
    config = ModelConfig(width=8, heads=2, layers=1)
    model = RecurrentLM(config, 2) if variant == "recurrent" else CausalLM(config)
    state = model.state_dict()
    next(iter(state.values())).fill_(value)
    saved = dict(
        format="toruk-controlled-v1",
        boundary="drained-document",
        tokenizer=ByteTokenizer.fingerprint,
        config=dict(model=asdict(config), variant=variant, slots=2),
        model=state,
    )
    path = tmp_path / "invalid.pt"
    torch.save(saved, path)
    with pytest.raises(ValueError, match="nonfinite model weights"):
        load_controlled(path)


def test_controlled_state_shape_error_is_actionable(tmp_path):
    saved = dict(
        format="toruk-controlled-v1",
        boundary="drained-document",
        tokenizer=ByteTokenizer.fingerprint,
        config=dict(model=asdict(ModelConfig(width=8, heads=2, layers=1)), variant="ordinary"),
        model={},
    )
    path = tmp_path / "invalid.pt"
    torch.save(saved, path)
    with pytest.raises(ValueError, match="model state mismatch"):
        load_controlled(path)
