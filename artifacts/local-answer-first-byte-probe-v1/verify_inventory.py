"""Verify the final new-file inventory using only bytes and Git metadata."""

import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def main():
    record = json.loads((BASE / "inventory.json").read_text(encoding="utf-8"))
    assert Path(git("rev-parse", "--show-toplevel")).resolve() == ROOT.resolve()
    assert git("rev-parse", "HEAD") == record["head"]
    assert git("branch", "--show-current") == record["branch"] == "main"
    assert git("diff", "--name-only") == git("diff", "--cached", "--name-only") == ""
    for name, expected in record["files"].items():
        path = ROOT / name
        assert path.stat().st_size == expected["bytes"], name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"], name
    actual = set(git("ls-files", "--others", "--exclude-standard").splitlines())
    assert actual == set(record["files"]) | {
        "artifacts/local-answer-first-byte-probe-v1/inventory.json"
    }
    print(
        json.dumps(
            dict(
                status="PASS",
                files=len(record["files"]),
                head=record["head"],
                all_probe_work_uncommitted=True,
                model_execution=False,
            )
        )
    )


if __name__ == "__main__":
    main()
