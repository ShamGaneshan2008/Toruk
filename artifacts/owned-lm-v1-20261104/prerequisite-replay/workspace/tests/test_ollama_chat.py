"""Focused checks for one pinned Ollama backbone across both context modes."""

from pathlib import Path

import pytest

from toruk_lm.chat_runtime import ChatError
from toruk_lm.ollama_chat import OllamaChatBackend

DIGEST = "a" * 64


class FakeSelector:
    def __init__(self, checkpoint: Path) -> None:
        self.sha256 = "b" * 64

    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        return [0, len(messages) - 1], True


def test_same_pinned_model_and_options_in_both_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_request(self, path, body, timeout):
        if path == "/api/tags":
            return {"models": [{"name": "llama3.2:latest", "digest": DIGEST}]}
        calls.append(body)
        return {
            "model": body["model"],
            "message": {"role": "assistant", "content": " 10 "},
            "prompt_eval_count": 20 * len(body["messages"]),
            "eval_count": 2,
        }

    monkeypatch.setattr(OllamaChatBackend, "_request", fake_request)
    monkeypatch.setattr("toruk_lm.ollama_chat.load_chat_selector", FakeSelector)
    backend = OllamaChatBackend("llama3.2:latest", DIGEST, Path("selector.pt"))
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "reply"},
        {"role": "user", "content": "new"},
    ]
    baseline = backend.reply_with_metrics(messages, 32)
    toruk = backend.reply_with_metrics(messages, 32, mode="TORUK")
    assert baseline["answer"] == toruk["answer"] == "10"
    assert baseline["metrics"]["model"] == toruk["metrics"]["model"]
    assert baseline["metrics"]["backbone_digest"] == toruk["metrics"]["backbone_digest"] == DIGEST
    assert baseline["metrics"]["selected_message_ids"] == ["m0", "m1", "m2"]
    assert toruk["metrics"]["selected_message_ids"] == ["m0", "m2"]
    assert baseline["metrics"]["selected_context_tokens"] == 60
    assert toruk["metrics"]["selected_context_tokens"] == 40
    assert {call["model"] for call in calls} == {"llama3.2:latest"}
    assert all(call["options"]["num_ctx"] == 4096 for call in calls)


def test_digest_mismatch_refuses_to_load(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        OllamaChatBackend,
        "_request",
        lambda self, path, body, timeout: {
            "models": [{"name": "llama3.2:latest", "digest": "b" * 64}]
        },
    )
    with pytest.raises(ChatError, match="digest"):
        OllamaChatBackend("llama3.2:latest", DIGEST)


def test_changed_model_digest_rejects_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    tag_checks = 0

    def fake_request(self, path, body, timeout):
        nonlocal tag_checks
        if path == "/api/tags":
            tag_checks += 1
            return {
                "models": [
                    {
                        "name": "llama3.2:latest",
                        "digest": DIGEST if tag_checks < 3 else "b" * 64,
                    }
                ]
            }
        return {
            "model": body["model"],
            "message": {"role": "assistant", "content": "ok"},
            "prompt_eval_count": 20,
            "eval_count": 1,
        }

    monkeypatch.setattr(OllamaChatBackend, "_request", fake_request)
    backend = OllamaChatBackend("llama3.2:latest", DIGEST)
    with pytest.raises(ChatError, match="digest"):
        backend.reply_with_metrics([{"role": "user", "content": "hi"}], 8)


def test_toruk_unavailable_without_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(self, path, body, timeout):
        if path == "/api/tags":
            return {"models": [{"name": "llama3.2:latest", "digest": DIGEST}]}
        return {
            "model": body["model"],
            "message": {"role": "assistant", "content": "ok"},
            "prompt_eval_count": 8,
            "eval_count": 1,
        }

    monkeypatch.setattr(OllamaChatBackend, "_request", fake_request)
    backend = OllamaChatBackend("llama3.2:latest", DIGEST)
    with pytest.raises(ChatError, match="requires a compatible recurrent selector"):
        backend.reply_with_metrics([{"role": "user", "content": "hi"}], 8, mode="TORUK")


def test_baseline_reports_exact_turns_after_token_fit(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(self, path, body, timeout):
        if path == "/api/tags":
            return {"models": [{"name": "llama3.2:latest", "digest": DIGEST}]}
        return {
            "model": body["model"],
            "message": {"role": "assistant", "content": "answer"},
            "prompt_eval_count": 200 * len(body["messages"]),
            "eval_count": 1,
        }

    monkeypatch.setattr(OllamaChatBackend, "_request", fake_request)
    backend = OllamaChatBackend("llama3.2:latest", DIGEST)
    messages = [
        {"role": "user", "content": "old fact"},
        {"role": "assistant", "content": "noted"},
        {"role": "user", "content": "question"},
    ]
    result = backend.reply_with_metrics(messages, 8)
    assert result["metrics"]["input_tokens"] == 600
    assert result["metrics"]["selected_context_tokens"] == 200
    assert result["metrics"]["selected_message_ids"] == ["m2"]
