import json
import threading
from dataclasses import asdict
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
import torch

from toruk_lm.chat_runtime import ChatController, ChatError, OrdinaryChatBackend
from toruk_lm.chat_server import create_controller, make_handler
from toruk_lm.engine import setup
from toruk_lm.model import CausalLM, ModelConfig, generate
from toruk_lm.tokenizer import ByteTokenizer


class FakeBackend:
    label = "test ordinary checkpoint"
    context = 32

    def __init__(self, answer="reply"):
        self.answer = answer
        self.calls = []

    def reply(self, messages, max_new_tokens):
        self.calls.append((messages, max_new_tokens))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def request_json(base, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = Request(
        base + path,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    with urlopen(request, timeout=5) as response:
        return json.load(response)


@pytest.fixture
def server():
    controller = ChatController(FakeBackend())
    http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(controller))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield controller, f"http://127.0.0.1:{http.server_port}"
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)


def test_http_message_empty_input_and_clear(server):
    controller, base = server
    with urlopen(base + "/", timeout=5) as response:
        page = response.read().decode()
    assert "Experimental local model" in page
    assert "Toruk is generating" in page
    assert request_json(base, "/api/status")["ready"]
    with pytest.raises(HTTPError) as error:
        request_json(base, "/api/chat", {"message": "  "})
    assert error.value.code == 400
    sent = request_json(base, "/api/chat", {"message": "hello", "max_new_tokens": 16})
    assert sent["messages"] == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "reply"},
    ]
    assert controller.backend.calls[0][1] == 16
    assert request_json(base, "/api/clear", {})["messages"] == []
    assert request_json(base, "/api/status")["messages"] == []


def test_generation_error_and_limits():
    controller = ChatController(FakeBackend(RuntimeError("forward failed")))
    for content in ("", "  ", "é" * 600):
        with pytest.raises(ChatError):
            controller.send(content, 16)
    with pytest.raises(ChatError, match="Generation length"):
        controller.send("hello", 65)
    with pytest.raises(ChatError, match="Generation failed: forward failed"):
        controller.send("hello", 16)
    assert not controller.status()["busy"]
    assert controller.status()["messages"] == []


def test_loading_state_and_clear_invalidates_pending_reply():
    started, release = threading.Event(), threading.Event()

    class SlowBackend(FakeBackend):
        def reply(self, messages, max_new_tokens):
            started.set()
            assert release.wait(5)
            return "late answer"

    controller = ChatController(SlowBackend())
    outcome = []

    def send():
        try:
            controller.send("hello", 16)
        except ChatError as error:
            outcome.append(str(error))

    thread = threading.Thread(target=send)
    thread.start()
    assert started.wait(5)
    assert controller.status()["busy"]
    assert controller.clear()["messages"] == []
    release.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert outcome == ["Chat was cleared while generation was running."]
    assert controller.status()["messages"] == []
    assert not controller.status()["busy"]


def test_supported_checkpoint_uses_existing_generation_path(tmp_path: Path):
    setup(9, 1)
    config = ModelConfig(context=8, width=16, heads=2, layers=1)
    model = CausalLM(config)
    checkpoint = tmp_path / "ordinary.pt"
    torch.save(
        {
            "format": "toruk-ordinary-v1",
            "tokenizer": ByteTokenizer.fingerprint,
            "model_config": asdict(config),
            "train_config": {},
            "model": model.state_dict(),
            "optimizer": {},
            "scheduler": None,
            "python_rng": (),
            "torch_rng": torch.get_rng_state(),
            "datasets": {},
            "next_step": 0,
            "data_progress": {},
        },
        checkpoint,
    )
    backend = OrdinaryChatBackend(checkpoint)
    messages = [{"role": "user", "content": "abc"}]
    prefix = [1, *ByteTokenizer().encode("User: abc\nToruk:")]
    assert backend.reply(messages, 3) == ByteTokenizer().decode(generate(backend.model, prefix, 3))
    assert "toruk-ordinary-v1" in backend.label


def test_unsupported_and_malformed_checkpoints_remain_visible(tmp_path: Path):
    controlled = tmp_path / "recurrent.pt"
    torch.save({"format": "toruk-controlled-v1"}, controlled)
    controller = create_controller(controlled)
    assert not controller.status()["ready"]
    assert "controlled and recurrent" in controller.status()["error"]
    with pytest.raises(ChatError, match="Unsupported checkpoint"):
        controller.send("hello", 16)
    malformed = tmp_path / "malformed.pt"
    malformed.write_bytes(b"not a checkpoint")
    broken = create_controller(malformed)
    assert not broken.status()["ready"]
    assert "Checkpoint validation failed" in broken.status()["error"]


def test_unsupported_checkpoint_is_visible_over_http(tmp_path: Path):
    controlled = tmp_path / "recurrent.pt"
    torch.save({"format": "toruk-controlled-v1"}, controlled)
    controller = create_controller(controlled)
    http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(controller))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{http.server_port}"
    try:
        status = request_json(base, "/api/status")
        assert not status["ready"]
        assert "controlled and recurrent" in status["error"]
        with pytest.raises(HTTPError) as error:
            request_json(base, "/api/chat", {"message": "hello"})
        assert error.value.code == 503
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)
