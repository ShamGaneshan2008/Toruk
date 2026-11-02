"""Local Ollama chat backbone with the same Toruk turn-selection policy."""

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from toruk_lm.chat_foundation import MAX_PROMPT_TOKENS, validate_sampling
from toruk_lm.chat_runtime import ChatError
from toruk_lm.chat_selector import load_chat_selector

OLLAMA_ORIGIN = "http://127.0.0.1:11434"
METER_CONTEXT = 4096


class OllamaChatBackend:
    """A pinned local GGUF model; TORUK changes turns, not model or decoding."""

    def __init__(
        self, model_name: str, digest: str, selector_checkpoint: Path | None = None
    ) -> None:
        if not model_name or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ChatError("Ollama model name and full digest are required.")
        self.model_name = model_name
        self.digest = digest
        self._verify_model()
        self.backbone_id = f"ollama/{model_name}"
        self.backbone_revision = None
        self.backbone_sha256 = None
        self.backbone_digest = digest
        self.model_id = f"{self.backbone_id}@{digest[:12]}"
        self.context = MAX_PROMPT_TOKENS
        self.selector = (
            load_chat_selector(selector_checkpoint) if selector_checkpoint is not None else None
        )
        # Load the GPU model before reporting the backend ready. Cold loads can be slow.
        self._chat([{"role": "user", "content": "Hi."}], 1, 0, 1, timeout=160)

    def _request(self, path: str, body: dict[str, Any] | None, timeout: int) -> dict[str, Any]:
        request = urllib.request.Request(
            OLLAMA_ORIGIN + path,
            json.dumps(body).encode("utf-8") if body is not None else None,
            {"Content-Type": "application/json"} if body is not None else {},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                result = json.load(response)
        except (OSError, ValueError, urllib.error.URLError) as error:
            raise ChatError(
                "Local Ollama service is unavailable or returned invalid JSON."
            ) from error
        if not isinstance(result, dict):
            raise ChatError("Local Ollama returned an invalid response.")
        return result

    def _verify_model(self) -> None:
        tags = self._request("/api/tags", None, 5).get("models", [])
        if not isinstance(tags, list) or not any(
            isinstance(item, dict)
            and item.get("name") == self.model_name
            and item.get("digest") == self.digest
            for item in tags
        ):
            raise ChatError("Ollama model or digest does not match the installed local model.")

    def _chat(
        self,
        messages: list[dict[str, str]],
        budget: int,
        temperature: float,
        top_p: float,
        timeout: int = 35,
    ) -> dict[str, Any]:
        result = self._request(
            "/api/chat",
            {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "keep_alive": "5m",
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": budget,
                    "num_ctx": METER_CONTEXT,
                },
            },
            timeout,
        )
        if (
            result.get("model") != self.model_name
            or not isinstance(result.get("message"), dict)
            or not isinstance(result["message"].get("content"), str)
            or type(result.get("prompt_eval_count")) is not int
            or type(result.get("eval_count")) is not int
        ):
            raise ChatError("Local Ollama returned incomplete generation metrics.")
        return result

    def _count(self, messages: list[dict[str, str]]) -> int:
        count = self._chat(messages, 1, 0, 1)["prompt_eval_count"]
        if count >= METER_CONTEXT - 1:
            raise ChatError("Conversation exceeds the Ollama metering context limit.")
        return int(count)

    def _fit(
        self, messages: list[dict[str, str]], indices: list[int]
    ) -> tuple[list[int], int, int]:
        chosen = list(indices)
        metering_tokens = 0
        while True:
            count = self._count([messages[index] for index in chosen])
            metering_tokens += count
            if count <= MAX_PROMPT_TOKENS:
                return chosen, count, metering_tokens
            if len(chosen) == 1:
                raise ChatError("Latest message exceeds the 512-token backbone input limit.")
            chosen.pop(0)
            while len(chosen) > 1 and messages[chosen[0]]["role"] == "assistant":
                chosen.pop(0)

    def reply_with_metrics(
        self,
        messages: list[dict[str, str]],
        max_new_tokens: int,
        mode: str = "BASELINE",
        temperature: float = 0,
        top_p: float = 1,
    ) -> dict[str, Any]:
        temperature, top_p = validate_sampling(temperature, top_p)
        if mode not in ("BASELINE", "TORUK"):
            raise ChatError("Mode must be BASELINE or TORUK.")
        if mode == "TORUK" and self.selector is None:
            raise ChatError("TORUK mode requires a compatible recurrent selector checkpoint.")
        self._verify_model()
        started = time.perf_counter()
        input_tokens = self._count(messages)
        selector_started = time.perf_counter()
        if mode == "TORUK":
            assert self.selector is not None
            indices, memory_used = self.selector.select(messages)
        else:
            indices, memory_used = list(range(len(messages))), False
        selector_ms = (
            round((time.perf_counter() - selector_started) * 1000, 3) if mode == "TORUK" else 0.0
        )
        chosen, _, fit_metering_tokens = self._fit(messages, indices)
        result = self._chat(
            [messages[index] for index in chosen], max_new_tokens, temperature, top_p
        )
        self._verify_model()
        selected_tokens = int(result["prompt_eval_count"])
        if selected_tokens > MAX_PROMPT_TOKENS:
            raise ChatError("Ollama prompt exceeded the 512-token backbone input limit.")
        output_tokens = int(result["eval_count"])
        return {
            "answer": result["message"]["content"].strip(),
            "metrics": {
                "input_tokens": input_tokens,
                "selected_context_tokens": selected_tokens,
                "output_tokens": output_tokens,
                "total_tokens": selected_tokens + output_tokens,
                "total_prompt_eval_tokens": input_tokens + fit_metering_tokens + selected_tokens,
                "selector_scan_bytes": sum(
                    len(item["content"].encode("utf-8")) for item in messages
                )
                if mode == "TORUK"
                else 0,
                "selector_ms": selector_ms,
                "response_ms": round((time.perf_counter() - started) * 1000, 3),
                "backend": "Toruk",
                "model": self.model_id,
                "backbone": self.backbone_id,
                "backbone_digest": self.digest,
                "selector_sha256": getattr(self.selector, "sha256", None),
                "selector_kind": getattr(self.selector, "kind", None),
                "mode": mode,
                "memory_used": memory_used,
                "selected_messages": len(chosen),
                "selected_message_ids": [f"m{index}" for index in chosen],
            },
        }
