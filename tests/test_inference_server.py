import json
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from toruk_lm.chat_runtime import ChatError
from toruk_lm.inference_server import make_handler, validate_request


class FakeBackend:
    model_id = "toruk-ordinary-v1:test"
    context = 32

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def reply_with_metrics(self, messages, budget, mode="BASELINE", temperature=0, top_p=1):
        self.calls.append((messages, budget))
        if self.error:
            raise self.error
        return {
            "answer": "abc",
            "metrics": {
                "input_tokens": 12,
                "selected_context_tokens": 12,
                "output_tokens": 3,
                "response_ms": 2.0,
                "backend": "Toruk",
                "model": self.model_id,
                "backbone": "Toruk ordinary byte LM",
                "mode": mode,
                "memory_used": False,
            },
        }


def call(base, path, body=None, token="secret", timeout=5):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(base + path, data=data, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


@pytest.fixture
def server():
    backend = FakeBackend()
    http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(backend, None, "secret"))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield backend, f"http://127.0.0.1:{http.server_port}"
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)


def test_stateless_inference_and_telemetry(server):
    backend, base = server
    assert call(base, "/api/status")["model"] == backend.model_id
    request = {"messages": [{"role": "user", "content": "hello"}], "max_new_tokens": 16}
    for _ in range(2):
        result = call(base, "/api/infer", request)
        assert result["answer"] == "abc"
        assert result["metrics"]["output_tokens"] == 3
        assert not result["metrics"]["memory_used"]
    assert len(backend.calls) == 2
    assert all(len(messages) == 1 for messages, _ in backend.calls)


def test_auth_and_input_limits(server):
    backend, base = server
    request = {"messages": [{"role": "user", "content": "hello"}]}
    with pytest.raises(HTTPError) as error:
        call(base, "/api/infer", request, token="wrong")
    assert error.value.code == 401
    for content in ("", "é" * 600):
        with pytest.raises(HTTPError) as error:
            call(base, "/api/infer", {"messages": [{"role": "user", "content": content}]})
        assert error.value.code == 400
    with pytest.raises(HTTPError) as error:
        call(base, "/api/infer", {**request, "max_new_tokens": 65})
    assert error.value.code == 400
    assert backend.calls == []


def test_unsupported_and_failed_backend():
    with pytest.raises(ChatError, match="final message"):
        validate_request({"messages": [{"role": "assistant", "content": "x"}]})
    unavailable = make_handler(None, "Unsupported checkpoint", "secret")
    http = ThreadingHTTPServer(("127.0.0.1", 0), unavailable)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{http.server_port}"
        status = call(base, "/api/status")
        assert status["ready"] is False
        assert "Unsupported checkpoint" in status["error"]
        with pytest.raises(HTTPError) as error:
            call(base, "/api/infer", {"messages": [{"role": "user", "content": "x"}]})
        assert error.value.code == 503
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)

    private_path = "C:/private/model.safetensors"
    http = ThreadingHTTPServer(
        ("127.0.0.1", 0), make_handler(None, f"Missing {private_path}", "secret")
    )
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        status = call(f"http://127.0.0.1:{http.server_port}", "/api/status")
        assert private_path not in status["error"]
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)
    backend = FakeBackend(RuntimeError("inference broke"))
    http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(backend, None, "secret"))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{http.server_port}"
        with pytest.raises(HTTPError) as error:
            call(base, "/api/infer", {"messages": [{"role": "user", "content": "x"}]})
        assert error.value.code == 500
        assert "inference broke" not in error.value.read().decode()
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)


def test_overlapping_requests_are_bounded_by_single_generation_slot():
    entered = threading.Event()
    release = threading.Event()

    class SlowBackend(FakeBackend):
        def reply_with_metrics(self, messages, budget, mode="BASELINE", temperature=0, top_p=1):
            entered.set()
            if not release.wait(timeout=20):
                raise TimeoutError("test backend did not release")
            return super().reply_with_metrics(messages, budget, mode, temperature, top_p)

    backend = SlowBackend()
    http = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(backend, None, "secret"))
    server_thread = threading.Thread(target=http.serve_forever, daemon=True)
    server_thread.start()
    first_result = []
    base = f"http://127.0.0.1:{http.server_port}"
    payload = {"messages": [{"role": "user", "content": "hello"}]}
    first_thread = threading.Thread(
        target=lambda: first_result.append(call(base, "/api/infer", payload, timeout=20))
    )
    first_thread.start()
    try:
        assert entered.wait(timeout=5)
        with pytest.raises(HTTPError) as error:
            call(base, "/api/infer", payload, timeout=10)
        assert error.value.code == 503
    finally:
        release.set()
        first_thread.join(timeout=5)
        http.shutdown()
        http.server_close()
        server_thread.join(timeout=5)
    assert first_result[0]["answer"] == "abc"
