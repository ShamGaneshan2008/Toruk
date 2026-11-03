"""Focused optional-backbone formatting, selection, and generation checks."""

import json
from pathlib import Path

import pytest
import torch

from toruk_lm.chat_foundation import (
    BACKBONES,
    PretrainedChatBackend,
    backbone_spec,
    read_backbone_manifest,
    validate_sampling,
    weight_sha256,
)
from toruk_lm.chat_runtime import ChatError, ModelStartupError
from toruk_lm.context_selection import LexicalContextSelector
from toruk_lm.inference_server import validate_request


class FakeTokenizer:
    eos_token_id = 2
    pad_token_id = 2

    def apply_chat_template(self, messages, **kwargs):
        self.messages = messages
        self.seen_messages = list(messages)
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
    value.backbone_id = "SmolLM2"
    value.system_prompt = ""
    value.selector = FakeSelector()
    return value


@pytest.mark.parametrize("name", list(BACKBONES))
def test_pinned_identity_and_weight_validation(name, tmp_path):
    spec = BACKBONES[name]
    manifest = {key: spec[key] for key in ("model", "revision", "model_sha256")}
    assert backbone_spec(manifest)["model_type"] == spec["model_type"]
    (tmp_path / "toruk-backbone.json").write_text(json.dumps(manifest))
    (tmp_path / "model.safetensors").write_bytes(b"wrong weights")
    with pytest.raises(ChatError, match="wrong SHA-256"):
        PretrainedChatBackend(tmp_path)
    for field in manifest:
        with pytest.raises(ChatError, match="identity or revision"):
            backbone_spec({**manifest, field: "untrusted"})


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
    assert value.tokenizer.seen_messages == messages
    assert baseline["metrics"]["selected_message_ids"] == ["m0", "m1", "m2"]
    assert baseline["metrics"]["memory_used"] is False
    assert value.model.options["eos_token_id"] == 2
    assert value.model.options["do_sample"] is False
    toruk = value.reply_with_metrics(messages, 8, mode="TORUK", temperature=0.7, top_p=0.9)
    assert toruk["metrics"]["selected_context_tokens"] == 40
    assert toruk["metrics"]["memory_used"] is True
    assert value.model.options["do_sample"] is True
    assert value.model.options["top_p"] == 0.9


def test_heuristic_selection_is_reflected_after_prompt_fitting():
    value = backend()
    value.selector = LexicalContextSelector("lexical-v2")
    value.selector_id = "lexical-v2"
    messages = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"note {i}"} for i in range(15)
    ]
    messages[0]["content"] = "The badge color is gold."
    messages[2]["content"] = "Correction: it is silver."
    messages[-1]["content"] = "What is the badge color?"
    response = value.reply_with_metrics(messages, 8, mode="TORUK")
    metrics = response["metrics"]
    assert metrics["selector_id"] == "lexical-v2" and metrics["memory_used"]
    assert {"m0", "m2", "m14"} <= set(metrics["selected_message_ids"])
    assert metrics["selected_context_tokens"] < metrics["input_tokens"]


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


def test_missing_optional_chat_dependencies_have_a_safe_code(tmp_path, monkeypatch):
    import builtins

    import toruk_lm.chat_foundation as foundation

    spec = BACKBONES["qwen2.5"]
    manifest = {key: spec[key] for key in ("model", "revision", "model_sha256")}
    (tmp_path / "toruk-backbone.json").write_text(json.dumps(manifest))
    (tmp_path / "model.safetensors").write_bytes(b"fixture")
    monkeypatch.setattr(foundation, "weight_sha256", lambda path: spec["model_sha256"])
    original_import = builtins.__import__

    def without_transformers(name, *args, **kwargs):
        if name == "transformers":
            raise ImportError("private-dependency-detail")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_transformers)
    with pytest.raises(ModelStartupError) as error:
        PretrainedChatBackend(tmp_path)
    assert error.value.code == "CHAT_DEPENDENCIES_MISSING"
    assert "private-dependency-detail" not in str(error.value)


def test_backbone_manifest_accepts_other_verified_identity(tmp_path: Path):
    weights = tmp_path / "model.safetensors"
    weights.write_bytes(b"a separate local model")
    manifest = {
        "model": "example/stronger-instruct",
        "revision": "revision-123",
        "model_sha256": weight_sha256(weights),
    }
    (tmp_path / "toruk-backbone.json").write_text(json.dumps(manifest))
    assert read_backbone_manifest(tmp_path) == manifest
    weights.write_bytes(b"tampered")
    with pytest.raises(ChatError, match="SHA-256"):
        read_backbone_manifest(tmp_path)


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


def test_system_instructions_survive_trimming_and_are_counted():
    value = backend()
    value.system_prompt = "Use conversation facts and acknowledge missing information."
    messages = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(39)
    ]
    prompt, chosen = value._fit(messages, list(range(len(messages))))
    assert prompt.shape[-1] <= 512
    assert prompt.shape[-1] == 20 * (len(chosen) + 1)
    assert value.tokenizer.messages[0] == {"role": "system", "content": value.system_prompt}
    assert value.tokenizer.messages[-1] == messages[-1]
    assert messages[chosen[0]]["role"] == "user"


@pytest.mark.parametrize("model_name", ["Qwen/Qwen2.5-0.5B-Instruct", "example/local-instruct"])
def test_verified_backbone_loads_with_trained_selector(tmp_path, monkeypatch, model_name):
    import sys
    from types import SimpleNamespace

    import toruk_lm.chat_foundation as foundation

    spec = BACKBONES["qwen2.5"]
    manifest = {
        "model": model_name,
        "revision": spec["revision"],
        "model_sha256": spec["model_sha256"],
    }
    (tmp_path / "toruk-backbone.json").write_text(json.dumps(manifest))
    (tmp_path / "model.safetensors").write_bytes(b"fixture")
    monkeypatch.setattr(foundation, "weight_sha256", lambda path: spec["model_sha256"])
    tokenizer = FakeTokenizer()
    tokenizer.chat_template = "fixture"
    model = SimpleNamespace(config=SimpleNamespace(model_type="qwen2"), eval=lambda: None)
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a, **k: tokenizer),
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=lambda *a, **k: model),
        ),
    )
    selector = SimpleNamespace(kind="toruk-chat-selector-v2")
    checkpoint = tmp_path / "selector.json"
    monkeypatch.setattr(foundation, "load_chat_selector", lambda path: selector)
    value = PretrainedChatBackend(tmp_path, checkpoint)
    assert value.selector is selector
    assert value.selector_id == "toruk-chat-selector-v2"
    assert value.backbone_id == model_name
    assert bool(value.system_prompt) == (model_name == spec["model"])
