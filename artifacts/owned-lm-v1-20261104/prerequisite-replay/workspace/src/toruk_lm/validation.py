"""Strict validation of the foundation config and document-split manifest."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from toruk_lm.data import check_separation, read_documents, sha256_file
from toruk_lm.engine import TrainConfig, load_checkpoint, load_model
from toruk_lm.model import ModelConfig


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}:{error.lineno}: invalid JSON: {error.msg}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def read_config(path: Path) -> tuple[ModelConfig, TrainConfig]:
    value = read_object(path)
    if set(value) != {"model", "training"}:
        raise ValueError("config requires exactly model and training objects")
    if not all(isinstance(value[key], dict) for key in ("model", "training")):
        raise ValueError("config model and training must be objects")
    try:
        return ModelConfig(**value["model"]), TrainConfig(**value["training"])
    except TypeError as error:
        raise ValueError(f"invalid config fields: {error}") from error


def validate_manifest(path: Path) -> dict[str, Any]:
    manifest = read_object(path)
    if manifest.get("kind") != "ordinary-text-smoke-fixture-v1":
        raise ValueError("unsupported dataset manifest kind")
    splits = manifest.get("splits")
    if not isinstance(splits, dict) or set(splits) != {"train", "validation", "test"}:
        raise ValueError("manifest must contain train, validation and test splits")
    documents = {}
    for name, spec in splits.items():
        if not isinstance(spec, dict):
            raise ValueError(f"manifest {name} must be an object")
        data = path.parent / f"{name}.jsonl"
        if sha256_file(data) != spec.get("sha256"):
            raise ValueError(f"stale manifest: {name} checksum mismatch")
        rows = read_documents(data)
        if type(spec.get("documents")) is not int or spec["documents"] != len(rows):
            raise ValueError(f"manifest {name} document count mismatch")
        if spec.get("ids") != [row["id"] for row in rows]:
            raise ValueError(f"manifest {name} IDs mismatch")
        documents[name] = rows
    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        try:
            check_separation(documents[left], documents[right])
        except ValueError as error:
            raise ValueError(f"manifest split separation {left}/{right}: {error}") from error
    return manifest


def require_split(manifest: Path, data: Path, name: str) -> None:
    value = validate_manifest(manifest)
    if name not in value["splits"]:
        raise ValueError(f"unknown manifest split: {name}")
    if data.resolve() != (manifest.parent / f"{name}.jsonl").resolve():
        raise ValueError(f"data path must match manifest {name} split")


def validate(
    manifest: Path, config: Path | None = None, checkpoint: Path | None = None
) -> dict[str, Any]:
    data = validate_manifest(manifest)
    result: dict[str, Any] = {"manifest_sha256": sha256_file(manifest), "splits": data["splits"]}
    model_config, train_config = read_config(config) if config else (None, None)
    if config:
        result["config_sha256"] = sha256_file(config)
    if checkpoint:
        saved = load_checkpoint(checkpoint)
        load_model(checkpoint)  # Also check that model weights match their configuration.
        expected = {name: data["splits"][name]["sha256"] for name in ("train", "validation")}
        if saved["datasets"] != expected:
            raise ValueError("checkpoint datasets do not match manifest")
        if model_config and saved["model_config"] != asdict(model_config):
            raise ValueError("checkpoint model_config does not match config")
        if train_config and saved["train_config"] != asdict(train_config):
            raise ValueError("checkpoint train_config does not match config")
        result["checkpoint_sha256"] = sha256_file(checkpoint)
        result["next_step"] = saved["next_step"]
    return result
