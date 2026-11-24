"""Rehash final v2 review payloads, including ignored local research weights."""

import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def main():
    inventory = json.loads((BASE / "review-inventory.json").read_text(encoding="utf-8"))
    for name, meta in inventory["files"].items():
        path = ROOT / name
        assert path.stat().st_size == meta["bytes"], name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == meta["sha256"], name
    anchor = json.loads((BASE / "review-anchor.json").read_text(encoding="utf-8"))
    for name, digest in anchor["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    assert (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        == inventory["head"]
    )
    state = json.loads((BASE / "ending-state.json").read_text())
    assert state["tracked_changes"] == state["staged_changes"] == []
    assert inventory["ignored_local_checkpoints"] == 16
    print(
        json.dumps(
            dict(
                status="PASS",
                files=len(inventory["files"]),
                local_checkpoints=16,
                head=inventory["head"],
                scientific_decision=inventory["scientific_decision"],
                model_work_executed=False,
            )
        )
    )


if __name__ == "__main__":
    main()
