"""Optional instruct backbone with a separately identified Toruk context selector."""

import hashlib
import json
import math
import re
import time
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

from toruk_lm.chat_runtime import ChatError, ModelStartupError
from toruk_lm.chat_selector import load_chat_selector
from toruk_lm.context_selection import LexicalContextSelector
from toruk_lm.controlled import load_controlled
from toruk_lm.recurrent import RecurrentLM
from toruk_lm.tokenizer import ByteTokenizer

BACKBONE_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
BACKBONE_REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
BACKBONE_SHA256 = "5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c"
MAX_PROMPT_TOKENS = 512
CHAT_INSTRUCTIONS = (
    "You are a helpful assistant. Answer the user's question directly and concisely. "
    "Facts about the user belong to the user, not to you. Use facts from this conversation. "
    "Use explicit corrections in place of earlier facts; keep unrelated facts. "
    "If facts conflict without a correction, explain the uncertainty. "
    "If information is missing, say you don't know. Do not invent facts."
)

# Keep the historical SmolLM identity for reproducible research/deployment artifacts.
# New local chat uses Qwen; neither pretrained model is Toruk-trained.
BACKBONES = {
    "smollm2": {
        "model": BACKBONE_ID,
        "revision": BACKBONE_REVISION,
        "model_sha256": BACKBONE_SHA256,
        "model_type": "llama",
    },
    "qwen2.5": {
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "revision": "7ae557604adf67be50417f59c2c2f167def9a775",
        "model_sha256": "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe",
        "model_type": "qwen2",
    },
}


def backbone_spec(manifest: object) -> dict[str, str]:
    for spec in BACKBONES.values():
        if manifest == {key: spec[key] for key in ("model", "revision", "model_sha256")}:
            return spec
    raise ModelStartupError("BACKBONE_INVALID", "Backbone identity or revision mismatch.")


def read_backbone_manifest(model_dir: Path) -> dict[str, str]:
    """Require a local, content-identified model before loading executable model code."""
    manifest_path = model_dir / "toruk-backbone.json"
    if not manifest_path.is_file():
        raise ModelStartupError("BACKBONE_MISSING", "Backbone manifest unavailable.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ModelStartupError("BACKBONE_INVALID", "Backbone manifest unavailable.") from error
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"model", "revision", "model_sha256"}
        or not all(isinstance(value, str) and value for value in manifest.values())
        or not re.fullmatch(r"[0-9a-f]{64}", manifest["model_sha256"])
    ):
        raise ModelStartupError("BACKBONE_INVALID", "Backbone identity or revision mismatch.")
    if any(spec["model"] == manifest["model"] for spec in BACKBONES.values()):
        backbone_spec(manifest)
    weights = model_dir / "model.safetensors"
    if not weights.is_file():
        raise ModelStartupError("BACKBONE_MISSING")
    if weight_sha256(weights) != manifest["model_sha256"]:
        raise ModelStartupError("BACKBONE_INVALID", "Backbone weights have the wrong SHA-256.")
    return manifest


def weight_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_sampling(temperature: object, top_p: object) -> tuple[float, float]:
    if (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or not math.isfinite(temperature)
    ):
        raise ChatError("Temperature must be a finite number.")
    if isinstance(top_p, bool) or not isinstance(top_p, (int, float)) or not math.isfinite(top_p):
        raise ChatError("Top-p must be a finite number.")
    if not 0 <= temperature <= 2 or not 0 < top_p <= 1:
        raise ChatError("Temperature must be 0–2 and top-p must be above 0 and at most 1.")
    return float(temperature), float(top_p)


class TorukContextSelector:
    """Explore frozen M6 recurrent summaries for verbatim turn selection.

    M6 was trained on controlled worlds, not semantic retrieval. Scores are experimental.
    """

    def __init__(self, checkpoint: Path) -> None:
        try:
            model, saved = load_controlled(checkpoint)
        except (OSError, ValueError, KeyError, RuntimeError) as error:
            raise ModelStartupError("SELECTOR_UNAVAILABLE") from error
        if not isinstance(model, RecurrentLM):
            raise ModelStartupError("SELECTOR_UNAVAILABLE")
        self.model = model
        self.tokenizer = ByteTokenizer()
        self.sha256 = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        self.checkpoint_id = self.sha256[:12]
        self.kind = "toruk-m6-controlled-qa"
        if saved.get("tokenizer") != ByteTokenizer.fingerprint:
            raise ModelStartupError("SELECTOR_UNAVAILABLE")

    @torch.inference_mode()
    def select(self, messages: list[dict[str, str]]) -> tuple[list[int], bool]:
        if len(messages) <= 3:
            return list(range(len(messages))), False
        # The last user turn and its immediately preceding two turns are always retained.
        keep = set(range(max(0, len(messages) - 3), len(messages)))
        query = self._summary(messages[-1]["content"], self.model.initial_state())[0]
        memory = self.model.initial_state()
        ranked: list[tuple[float, int]] = []
        for index, message in enumerate(messages[:-1]):
            summary, memory = self._summary(message["content"], memory)
            if index not in keep:
                similarity = float(F.cosine_similarity(summary, query, dim=0).item())
                ranked.append((similarity, index))
        keep.update(index for _, index in sorted(ranked, reverse=True)[:2])
        return sorted(keep), bool(ranked)

    def _summary(self, content: str, memory: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        tokens = [self.tokenizer.bos_id, *self.tokenizer.encode(content)]
        # Each message is bounded by the server. Read all chunks so the recurrent
        # state, rather than only the last bytes, participates in the selection.
        summary = memory.new_zeros(self.model.config.width)
        for start in range(0, len(tokens), self.model.config.context):
            chunk = tokens[start : start + self.model.config.context]
            _, memory, value = self.model(torch.tensor([chunk]), memory)
            summary = value[0]
        return summary, memory


class PretrainedChatBackend:
    """Local content-identified backbone; TORUK changes context, never weights."""

    def __init__(
        self,
        model_dir: Path,
        selector_checkpoint: Path | None = None,
        context_selector: str | None = None,
    ) -> None:
        if selector_checkpoint and context_selector:
            raise ChatError("Choose a learned selector checkpoint or a heuristic selector.")
        manifest = read_backbone_manifest(model_dir)
        spec = next(
            (item for item in BACKBONES.values() if item["model"] == manifest["model"]), None
        )
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise ModelStartupError(
                "CHAT_DEPENDENCIES_MISSING",
                "Install optional chat dependencies with pip install -e '.[chat]'.",
            ) from error
        torch.set_num_threads(2)
        try:
            self.tokenizer: Any = AutoTokenizer.from_pretrained(
                model_dir, local_files_only=True, trust_remote_code=False
            )
            self.model: Any = AutoModelForCausalLM.from_pretrained(
                model_dir,
                local_files_only=True,
                trust_remote_code=False,
                use_safetensors=True,
                dtype=torch.float32,
            )
        except (OSError, ValueError, RuntimeError) as error:
            raise ModelStartupError("BACKBONE_INCOMPATIBLE") from error
        if (
            spec and self.model.config.model_type != spec["model_type"]
        ) or not self.tokenizer.chat_template:
            raise ModelStartupError("BACKBONE_INCOMPATIBLE")
        if self.tokenizer.eos_token_id is None or self.tokenizer.pad_token_id is None:
            raise ModelStartupError("BACKBONE_INCOMPATIBLE")
        self.model.eval()
        self.context = MAX_PROMPT_TOKENS
        self.backbone_id = manifest["model"]
        self.backbone_revision = manifest["revision"]
        self.backbone_sha256 = manifest["model_sha256"]
        self.model_id = f"{self.backbone_id}@{self.backbone_revision[:12]}"
        # Preserve the historical SmolLM prompt for archived study reproduction.
        self.system_prompt = CHAT_INSTRUCTIONS if spec and spec["model_type"] == "qwen2" else ""
        self.selector: Any = (
            load_chat_selector(selector_checkpoint) if selector_checkpoint is not None else None
        )
        if context_selector:
            self.selector = LexicalContextSelector(context_selector)
        self.selector_id = (
            getattr(self.selector, "selector_id", getattr(self.selector, "kind", "m6-recurrent"))
            if self.selector
            else None
        )

    def _tokens(self, messages: list[dict[str, str]]) -> torch.Tensor:
        if self.system_prompt:
            messages = [{"role": "system", "content": self.system_prompt}, *messages]
        encoded: Any = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        return encoded["input_ids"]

    def _fit(
        self, messages: list[dict[str, str]], indices: list[int]
    ) -> tuple[torch.Tensor, list[int]]:
        chosen = list(indices)
        while True:
            tokens = self._tokens([messages[index] for index in chosen])
            if tokens.shape[-1] <= MAX_PROMPT_TOKENS:
                return tokens, chosen
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
            raise ChatError("TORUK mode requires an explicitly configured context selector.")
        started = time.perf_counter()
        tokenizer_started = time.perf_counter()
        input_tokens = int(self._tokens(messages).shape[-1])
        history_tokenization_ms = (time.perf_counter() - tokenizer_started) * 1000
        selector_started = time.perf_counter()
        if mode == "TORUK":
            assert self.selector is not None
            indices, memory_used = self.selector.select(messages)
        else:
            indices, memory_used = list(range(len(messages))), False
        selector_ms = (time.perf_counter() - selector_started) * 1000 if mode == "TORUK" else 0
        fit_started = time.perf_counter()
        prompt, chosen = self._fit(messages, indices)
        prompt_fit_ms = (time.perf_counter() - fit_started) * 1000
        options: dict[str, Any] = {
            "input_ids": prompt,
            "max_new_tokens": max_new_tokens,
            "do_sample": temperature > 0,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
            "use_cache": True,
        }
        if temperature > 0:
            options.update(temperature=temperature, top_p=top_p)
        with torch.inference_mode():
            output = self.model.generate(**options)
        generated = output[0, prompt.shape[-1] :].tolist()
        answer = str(self.tokenizer.decode(generated, skip_special_tokens=True)).strip()
        return {
            "answer": answer,
            "metrics": {
                "input_tokens": input_tokens,
                "selected_context_tokens": int(prompt.shape[-1]),
                "output_tokens": len(generated),
                "total_tokens": int(prompt.shape[-1]) + len(generated),
                "response_ms": round((time.perf_counter() - started) * 1000, 3),
                "backend": "Toruk",
                "model": self.model_id,
                "backbone": self.backbone_id,
                "selector_sha256": getattr(self.selector, "sha256", None),
                "selector_kind": getattr(self.selector, "kind", None),
                "mode": mode,
                "memory_used": memory_used,
                "selector_id": getattr(self, "selector_id", None) if mode == "TORUK" else None,
                "selected_messages": len(chosen),
                "selected_message_ids": [f"m{index}" for index in chosen],
                "history_tokenization_ms": round(history_tokenization_ms, 3),
                "prompt_fit_ms": round(prompt_fit_ms, 3),
                "selector_ms": round(selector_ms, 3),
                "history_bytes_read": sum(len(m["content"].encode("utf-8")) for m in messages),
                "selector_history_bytes": sum(len(m["content"].encode("utf-8")) for m in messages)
                if mode == "TORUK"
                else 0,
                "persistent_state_bytes": 0,
            },
        }
