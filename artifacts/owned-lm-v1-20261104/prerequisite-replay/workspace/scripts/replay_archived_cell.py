"""Run one recorded M7 cell from its verified historical source, without changing identities."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-output", type=Path, required=True)
    args = parser.parse_args()
    seal = json.loads((args.handoff / "manifest.json").read_text(encoding="utf-8"))
    archive = args.handoff / "source.zip"
    expected = [
        v for k, v in seal["evidence_sha256"].items() if k.endswith("m7-handoff/source.zip")
    ]
    if expected != [hashlib.sha256(archive.read_bytes()).hexdigest()]:
        parser.error("historical source archive checksum mismatch")
    if args.source_output.exists():
        parser.error("source-output must be a fresh directory")
    with zipfile.ZipFile(archive) as source:
        for name, digest in seal["source_files"].items():
            if name.startswith("src/toruk_lm/") and name.endswith(".py"):
                target = (args.source_output / name).resolve()
                if not target.is_relative_to(args.source_output.resolve()):
                    parser.error("source archive path escapes destination")
                payload = source.read(name)
                if hashlib.sha256(payload).hexdigest() != digest:
                    parser.error("historical source file checksum mismatch: " + name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
    env = dict(os.environ, PYTHONPATH=str((args.source_output / "src").resolve()))
    identity = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "from toruk_lm.controlled import package_fingerprint; print(package_fingerprint())",
        ],
        env=env,
        text=True,
        timeout=30,
    ).strip()
    if identity != seal["package_sha256"]:
        parser.error("extracted source package identity mismatch")
    command = [
        sys.executable,
        "-m",
        "toruk_lm",
        "evaluate-heldout",
        "--parent",
        str(args.parent),
        "--protocol",
        str(args.protocol),
        "--method",
        args.method,
        "--data",
        str(args.data),
        "--output",
        str(args.output),
    ]
    print(
        json.dumps(
            dict(command=command, source_package_sha256=identity, source_archive_sha256=expected[0])
        ),
        flush=True,
    )
    completed = subprocess.run(command, env=env, timeout=100)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
