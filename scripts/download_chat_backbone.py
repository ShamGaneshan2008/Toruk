"""Download a revision-pinned compatible instruct model, verifying its weight hash."""

import argparse
import json
import re
from pathlib import Path

from toruk_lm.chat_foundation import (
    BACKBONES,
    weight_sha256,
)

FILES = (
    "config.json",
    "generation_config.json",
    "model.safetensors",
    "tokenizer.json",
    "tokenizer_config.json",
    "README.md",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a pinned small instruct backbone")
    parser.add_argument("--model", default="qwen2.5", help="Pinned alias or Hugging Face model ID")
    parser.add_argument("--revision")
    parser.add_argument("--sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    alias = next(
        (name for name, item in BACKBONES.items() if args.model in (name, item["model"])), None
    )
    if alias is not None:
        spec = BACKBONES[alias]
        if (args.revision and args.revision != spec["revision"]) or (
            args.sha256 and args.sha256 != spec["model_sha256"]
        ):
            parser.error("pinned model revision and SHA-256 cannot be overridden")
    else:
        if not args.revision or not args.sha256 or not args.output:
            parser.error("a custom model requires --revision, --sha256 and --output")
        if not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
            parser.error("--sha256 must be a full lowercase SHA-256")
        spec = {"model": args.model, "revision": args.revision, "model_sha256": args.sha256}
    if args.output is None:
        folder = "qwen-chat-001" if alias == "qwen2.5" else "chat-foundation-001"
        args.output = Path("artifacts") / folder / "backbone"
    files = (
        (*FILES, "special_tokens_map.json")
        if alias == "smollm2"
        else (*FILES, "merges.txt", "vocab.json", "LICENSE")
        if alias == "qwen2.5"
        else FILES
    )
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("use a fresh output directory")
    try:
        from huggingface_hub import snapshot_download
    except ImportError as error:
        parser.error(f"install optional chat dependencies first: {error}")
    args.output.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=spec["model"],
        revision=spec["revision"],
        allow_patterns=[*files, "special_tokens_map.json", "merges.txt", "vocab.json", "LICENSE"],
        local_dir=args.output,
        max_workers=1,
    )
    for name in files:
        if not (args.output / name).is_file():
            raise ValueError(f"missing backbone file: {name}")
    digest = weight_sha256(args.output / "model.safetensors")
    if digest != spec["model_sha256"]:
        raise ValueError("model.safetensors SHA-256 mismatch")
    manifest = {
        "model": spec["model"],
        "revision": spec["revision"],
        "model_sha256": digest,
    }
    (args.output / "toruk-backbone.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({**manifest, "bytes": sum((args.output / f).stat().st_size for f in files)}))


if __name__ == "__main__":
    main()
