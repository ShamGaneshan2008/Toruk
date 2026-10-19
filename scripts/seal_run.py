"""Retain source snapshot, environment, and artifact hashes for an uncommitted experiment."""

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from check import ROOT, source_identity, sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    directory = args.directory
    files = sources() + [ROOT / "README.md"] + list((ROOT / "docs").rglob("*.md"))
    snapshot = directory / "source.zip"
    with zipfile.ZipFile(snapshot, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    environment = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    (directory / "environment.txt").write_text(environment, encoding="utf-8")
    record = {
        **source_identity(),
        "sealed_utc": datetime.now(UTC).isoformat(),
        "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "artifact_hashes": {
            path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.rglob("*")
            if path.is_file() and path != directory / "manifest.json"
        },
        "checks": {
            path.name: json.loads(path.read_text())
            for path in (ROOT / "artifacts/checks").glob("*.json")
        },
        "test_split": "generated and fingerprinted, never loaded for training/evaluation",
        "milestone": "ordinary-LM foundation; M2 missing; M3 incomplete",
    }
    (directory / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record[key] for key in ("base_commit", "source_sha256")}))


if __name__ == "__main__":
    main()
