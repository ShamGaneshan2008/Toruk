"""Run one bounded check and retain its command, source identity, output and result."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sources():
    paths = [ROOT / name for name in ("pyproject.toml", "MANIFEST.in", "main.py", ".gitignore")]
    for directory in ("src", "tests", "scripts", ".github", "configs"):
        paths.extend((ROOT / directory).rglob("*.py"))
        paths.extend((ROOT / directory).rglob("*.yml"))
        paths.extend((ROOT / directory).rglob("*.json"))
    return sorted(p for p in paths if p.is_file() and "__pycache__" not in p.parts)


def source_identity():
    files = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources()
    }
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    base = None
    # Source distributions need not have Git installed or belong to a checkout.
    if (ROOT / ".git").exists():
        base = subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    return {"base_commit": base, "source_sha256": fingerprint, "source_files": files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/checks")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("command required after --")
    directory = args.output_dir.resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.label):
        parser.error("label must contain only letters, numbers, dots, dashes and underscores")
    directory.mkdir(parents=True, exist_ok=True)
    if any((directory / f"{args.label}.{suffix}").exists() for suffix in ("log", "json")):
        parser.error("check evidence already exists; select a fresh label or --output-dir")
    record = {
        **source_identity(),
        "command": command,
        "started_utc": datetime.now(UTC).isoformat(),
        "evidence_path": str(directory / f"{args.label}.log"),
    }
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            encoding="utf-8",
            errors="replace",
        )
        output = completed.stdout + completed.stderr
        code = completed.returncode
        record.update(status="PASS" if code == 0 else "FAIL", returncode=code)
    except subprocess.TimeoutExpired as error:

        def decoded(value: str | bytes | None) -> str:
            return (
                value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
            )

        output = decoded(error.stdout) + decoded(error.stderr)
        output += f"\nTimed out after {args.timeout} seconds"
        record.update(status="FAIL", returncode=None)
        code = 1
    except OSError as error:
        output = f"Could not start command: {type(error).__name__}: {error}\n"
        record.update(status="FAIL", returncode=None)
        code = 1
    record["seconds"] = time.perf_counter() - started
    (directory / f"{args.label}.log").write_text(output, encoding="utf-8")
    (directory / f"{args.label}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(output)
    print(json.dumps({k: record[k] for k in ("status", "seconds", "evidence_path")}))
    return code


if __name__ == "__main__":
    sys.exit(main())
