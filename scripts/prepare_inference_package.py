"""Create a reviewed allowlist package locally; never upload or copy research data."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTOR_SHA = "479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d"
MODULES = (
    "__init__",
    "chat_runtime",
    "chat_foundation",
    "inference_server",
    "inference_worker",
    "controlled",
    "engine",
    "data",
    "model",
    "recurrent",
    "effect_predictor",
    "worlds",
    "tokenizer",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--selector", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new directory; existing work is never overwritten")
    if not args.selector.is_file():
        parser.error("original evaluated M6 selector is missing; no substitute is allowed")
    if hashlib.sha256(args.selector.read_bytes()).hexdigest() != SELECTOR_SHA:
        parser.error("selector SHA-256 differs from the evaluated model")
    files = {
        name: ROOT / "deploy/huggingface" / name
        for name in ("README.md", "Dockerfile", "requirements.txt", ".dockerignore")
    }
    files["download_chat_backbone.py"] = ROOT / "scripts/download_chat_backbone.py"
    files["selector.pt"] = args.selector
    files.update({f"src/toruk_lm/{name}.py": ROOT / f"src/toruk_lm/{name}.py" for name in MODULES})
    manifest = []
    for relative, source in files.items():
        target = args.output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        manifest.append(
            {
                "path": relative,
                "bytes": target.stat().st_size,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        )
    (args.output / "publication-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
