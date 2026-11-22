"""Verify this uncommitted review's final inventory and repository scope."""

import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def main():
    inv = json.loads((BASE / "inventory.json").read_text(encoding="utf-8"))
    assert git("rev-parse", "HEAD") == inv["head"]
    assert git("branch", "--show-current") == inv["branch"]
    assert git("diff", "--name-only") == git("diff", "--cached", "--name-only") == ""
    for name, meta in inv["files"].items():
        path = ROOT / name
        assert path.stat().st_size == meta["bytes"], name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == meta["sha256"], name
    others = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    assert others == set(inv["files"]) | {
        "artifacts/local-answer-first-token-review-v1/inventory.json"
    }
    print(
        json.dumps(
            dict(
                status="PASS",
                files=len(inv["files"]),
                head=inv["head"],
                review_uncommitted=True,
                model_execution=False,
            )
        )
    )


if __name__ == "__main__":
    main()
