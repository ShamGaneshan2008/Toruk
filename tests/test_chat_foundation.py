"""Focused optional-backbone formatting, selection, and generation checks."""

import json
from pathlib import Path

import pytest
import torch

from toruk_lm.chat_foundation import PretrainedChatBackend, validate_sampling
from toruk_lm.chat_runtime import ChatError
from toruk_lm.inference_server import validate_request


class FakeTokenizer:
    eos_token_id = 2
    pad_token_id = 2

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs["add_generation_prompt"]
        assert kwargs["return_dict"]
        return {"input_ids": torch.ones((1, 20 * len(messages)), dtype=torch.long)}

    def decode(self, tokens, **kwargs):
        assert kwargs["skip_special_tokens"]
        return " Hello "


class FakeModel:
    def __init__(self):
        self.options = None

    def generate(self, **kwargs):
        self.options = kwargs
        return torch.cat((kwargs["input_ids"], torch.tensor([[8, 2]])), dim=1)


class FakeSelector:
    def select(self, messages):
        return [0, len(messages) - 1], True


def backend():
    value = PretrainedChatBackend.__new__(PretrainedChatBackend)
    value.tokenizer = FakeTokenizer()
    value.model = FakeModel()
    value.model_id = "SmolLM2:test"
    value.selector = FakeSelector()
    return value


def test_template_modes_sampling_and_eos():
    value = backend()
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "ack"},
        {"role": "user", "content": "now"},
    ]
    baseline = value.reply_with_metrics(messages, 8)
    assert baseline["answer"] == "Hello"
    assert baseline["metrics"]["selected_context_tokens"] == 60
    assert baseline["metrics"]["memory_used"] is False
    assert value.model.options["eos_token_id"] == 2
    assert value.model.options["do_sample"] is False
    toruk = value.reply_with_metrics(messages, 8, mode="TORUK", temperature=0.7, top_p=0.9)
    assert toruk["metrics"]["selected_context_tokens"] == 40
    assert toruk["metrics"]["memory_used"] is True
    assert value.model.options["do_sample"] is True
    assert value.model.options["top_p"] == 0.9


def test_missing_or_incompatible_backbone_and_invalid_options(tmp_path: Path):
    with pytest.raises(ChatError, match="manifest unavailable"):
        PretrainedChatBackend(tmp_path)
    (tmp_path / "toruk-backbone.json").write_text(json.dumps({"model": "other"}))
    with pytest.raises(ChatError, match="identity or revision mismatch"):
        PretrainedChatBackend(tmp_path)
    for temperature, top_p in ((-1, 1), (0, 0), (float("nan"), 1), (True, 1)):
        with pytest.raises(ChatError):
            validate_sampling(temperature, top_p)
    with pytest.raises(ChatError, match="requires"):
        value = backend()
        value.selector = None
        value.reply_with_metrics([{"role": "user", "content": "hi"}], 8, mode="TORUK")


def test_server_request_parses_mode_and_controls():
    messages, budget, mode, temperature, top_p = validate_request(
        {
            "messages": [{"role": "user", "content": "hi"}],
            "max_new_tokens": 16,
            "mode": "TORUK",
            "temperature": 0.5,
            "top_p": 0.8,
        }
    )
    assert messages[0]["content"] == "hi"
    assert (budget, mode, temperature, top_p) == (16, "TORUK", 0.5, 0.8)


def test_recent_context_fit_keeps_a_user_turn_at_the_front():
    value = backend()
    messages = [
        {"role": "user" if index % 2 == 0 else "assistant", "content": str(index)}
        for index in range(40)
    ]
    messages[-1]["role"] = "user"
    prompt, chosen = value._fit(messages, list(range(len(messages))))
    assert prompt.shape[-1] <= 512
    assert messages[chosen[0]]["role"] == "user"
    assert chosen[-1] == len(messages) - 1
