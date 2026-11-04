"""Check immutable experiment scripts excluded from formatting, without loading models."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root: Path = ROOT) -> None:
    manifest = json.loads((root / "configs/frozen-source-sha256.json").read_text(encoding="utf-8"))
    for relative, expected in manifest.items():
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Frozen experiment source changed: {relative}")
    print(f"Verified {len(manifest)} frozen experiment source files.")


if __name__ == "__main__":
    verify()
