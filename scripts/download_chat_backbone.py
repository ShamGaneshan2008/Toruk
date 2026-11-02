"""Download a revision-pinned compatible instruct model, verifying its weight hash."""

import argparse
import json
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
<<<<<<< HEAD
    parser = argparse.ArgumentParser(description="Download a pinned small instruct backbone")
    parser.add_argument("--model", choices=tuple(BACKBONES), default="qwen2.5")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    spec = BACKBONES[args.model]
    if args.output is None:
        folder = "qwen-chat-001" if args.model == "qwen2.5" else "chat-foundation-001"
        args.output = Path("artifacts") / folder / "backbone"
    files = (
        (*FILES, "special_tokens_map.json")
        if args.model == "smollm2"
        else (*FILES, "merges.txt", "vocab.json", "LICENSE")
    )
=======
    parser = argparse.ArgumentParser(description="Download pinned 135M instruct backbone")
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/chat-foundation-001/backbone")
    )
    parser.add_argument("--model", default=BACKBONE_ID)
    parser.add_argument("--revision", default=BACKBONE_REVISION)
    parser.add_argument("--sha256", default=BACKBONE_SHA256)
    args = parser.parse_args()
    if args.model != BACKBONE_ID and (
        args.revision == BACKBONE_REVISION or args.sha256 == BACKBONE_SHA256
    ):
        parser.error("a different model requires its own --revision and --sha256")
>>>>>>> origin/main
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("use a fresh output directory")
    try:
        from huggingface_hub import snapshot_download
    except ImportError as error:
        parser.error(f"install optional chat dependencies first: {error}")
    args.output.mkdir(parents=True, exist_ok=True)
    snapshot_download(
<<<<<<< HEAD
        repo_id=spec["model"],
        revision=spec["revision"],
        allow_patterns=list(files),
=======
        repo_id=args.model,
        revision=args.revision,
        allow_patterns=list(FILES),
>>>>>>> origin/main
        local_dir=args.output,
        max_workers=1,
    )
    for name in files:
        if not (args.output / name).is_file():
            raise ValueError(f"missing backbone file: {name}")
    digest = weight_sha256(args.output / "model.safetensors")
<<<<<<< HEAD
    if digest != spec["model_sha256"]:
        raise ValueError("model.safetensors SHA-256 mismatch")
    manifest = {
        "model": spec["model"],
        "revision": spec["revision"],
=======
    if digest != args.sha256:
        raise ValueError("model.safetensors SHA-256 mismatch")
    manifest = {
        "model": args.model,
        "revision": args.revision,
>>>>>>> origin/main
        "model_sha256": digest,
    }
    (args.output / "toruk-backbone.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({**manifest, "bytes": sum((args.output / f).stat().st_size for f in files)}))


if __name__ == "__main__":
    main()
