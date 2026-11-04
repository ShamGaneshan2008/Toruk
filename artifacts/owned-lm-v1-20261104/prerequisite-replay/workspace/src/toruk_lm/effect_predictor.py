"""Runtime effect estimator. This module has no world, oracle or label imports."""

from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn


def features(previous: Tensor, proposed: Tensor, summary: Tensor) -> Tensor:
    if (
        previous.ndim != 3
        or previous.shape != proposed.shape
        or summary.shape != (previous.shape[0], previous.shape[2])
    ):
        raise ValueError("effect feature shape mismatch")
    result = torch.cat((previous.flatten(1), proposed.flatten(1), summary), dim=1).detach()
    if not torch.isfinite(result).all():
        raise ValueError("nonfinite effect features")
    return result


class EffectPredictor(nn.Module):
    mean: Tensor
    scale: Tensor
    target_mean: Tensor
    target_scale: Tensor
    support: Tensor

    def __init__(self, inputs: int, hidden: int = 16) -> None:
        super().__init__()
        self.network = nn.Sequential(nn.Linear(inputs, hidden), nn.Tanh(), nn.Linear(hidden, 1))
        self.register_buffer("mean", torch.zeros(inputs))
        self.register_buffer("scale", torch.ones(inputs))
        self.register_buffer("target_mean", torch.zeros(()))
        self.register_buffer("target_scale", torch.ones(()))
        self.register_buffer("support", torch.ones(inputs) * 8)
        self.metadata: dict[str, Any] = {}
        self.fallbacks = 0

    def forward(self, inputs: Tensor) -> Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != self.mean.numel():
            raise ValueError("predictor input shape mismatch")
        if not torch.isfinite(inputs).all():
            raise ValueError("invalid predictor input")
        result = self.network((inputs - self.mean) / self.scale).squeeze(-1)
        return result * self.target_scale + self.target_mean

    @torch.no_grad()
    def recommend(self, previous: Tensor, proposed: Tensor, summary: Tensor) -> bool:
        try:
            inputs = features(previous, proposed, summary)
            if inputs.shape != (1, self.mean.numel()):
                raise ValueError("recommend expects one decision")
            if (((inputs - self.mean) / self.scale).abs() > self.support).any():
                self.fallbacks += 1
                return False
            score = self(inputs)
            return bool(torch.isfinite(score).all() and score.item() > 0)
        except ValueError:
            self.fallbacks += 1
            return False

    @classmethod
    def load(cls, path: Path, model_sha256: str) -> "EffectPredictor":
        saved: dict[str, Any] = torch.load(path, map_location="cpu", weights_only=True)
        if saved.get("format") != "toruk-effect-v1":
            raise ValueError("unsupported predictor checkpoint")
        if saved["metadata"]["checkpoint_sha256"] != model_sha256:
            raise ValueError("predictor/model identity mismatch")
        model = cls(saved["inputs"], saved["hidden"])
        model.load_state_dict(saved["model"])
        model.metadata = saved["metadata"]
        model.eval()
        return model
