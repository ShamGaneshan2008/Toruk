"""Observer-owned sealing v2: finalize the process Job and its receipts before hashing."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lifetime_job import ROOT, watch

SCHEMA = "toruk-observer-owned-seal-v2"
SEAL_NAME = "observer-seal-v2.json"
FAILURE_NAME = "observer-sealing-failure-v2.json"
CONTROL_FILES = {SEAL_NAME, FAILURE_NAME}


class SealError(ValueError):
    """The output cannot be certified as a closed, unchanged snapshot."""


@dataclass(frozen=True)
class SealedRun:
    cost: dict[str, Any]
    seal_path: Path
    seal_sha256: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SealError(message)


def _read_json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(result, dict), "expected a JSON object: " + str(path))
    return dict(result)


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _write_new(path: Path, value: dict[str, Any]) -> None:
    # Exclusive creation never replaces an earlier receipt, seal or failed attempt.
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _directory(path: Path) -> Path:
    # Reject links before resolving them; do not certify a path through a junction.
    current = path.absolute()
    while current != current.parent:
        _require(
            not current.is_symlink() and not bool(getattr(current, "is_junction", lambda: False)()),
            "symlink/junction output path",
        )
        current = current.parent
    resolved = path.resolve()
    _require(resolved.is_relative_to(ROOT.resolve()), "outputs must remain inside the checkout")
    return resolved


def _walk_failed(error: OSError) -> None:
    raise error


def _files(directory: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for parent, dirs, files in os.walk(directory, followlinks=False, onerror=_walk_failed):
        base = Path(parent)
        for name in dirs:
            child = base / name
            _require(
                not child.is_symlink() and not bool(getattr(child, "is_junction", lambda: False)()),
                "symlink/junction in output tree",
            )
        for name in files:
            child = base / name
            relative = child.relative_to(directory).as_posix()
            if relative in CONTROL_FILES:
                continue
            _require(not child.is_symlink(), "symlink output file")
            _require(stat.S_ISREG(child.stat().st_mode), "non-regular output file")
            result[relative] = child
    return result


def _snapshot(directory: Path) -> dict[str, dict[str, Any]]:
    before = _files(directory)
    records: dict[str, dict[str, Any]] = {}
    for name, path in sorted(before.items()):
        prior = path.stat()
        digest = _digest(path)
        after = path.stat()
        _require(
            (prior.st_size, prior.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            "file changed while hashing: " + name,
        )
        records[name] = dict(bytes=after.st_size, sha256=digest)
    _require(set(before) == set(_files(directory)), "output membership changed while hashing")
    return records


def _closed_receipt(directory: Path) -> dict[str, Any]:
    _require((directory / "cost.json").is_file(), "final cost receipt missing")
    cost = _read_json(directory / "cost.json")
    _require(
        cost.get("complete_process_lifetimes") is True
        and cost.get("active_processes") == 0
        and cost.get("returncode") != 259,
        "process lifetimes are not closed",
    )
    _require(cost.get("status") in ("PASS", "STOP"), "non-terminal workload status")
    _require(
        cost["cpu"] == cost["user_cpu"] + cost["kernel_cpu"],
        "invalid final CPU accounting",
    )
    return cost


def _record_failure(directory: Path, error: BaseException) -> None:
    # Incomplete seals are never repaired or removed. A failure marker makes verification fail.
    if directory.is_dir() and not (directory / FAILURE_NAME).exists():
        _write_new(
            directory / FAILURE_NAME,
            dict(
                schema=SCHEMA,
                status="SEALING_FAILED",
                error=repr(error),
                cost_receipt_exists=(directory / "cost.json").is_file(),
                output_retained=True,
                note="Existing output and any incomplete seal are retained; no retry or overwrite.",
            ),
        )


def seal_closed_run(directory: Path) -> Path:
    """Seal an observer-owned directory only after its monitor has returned and closed writers.

    Use watch_and_seal for process execution. This separate function also refuses a
    missing/incomplete receipt, existing seal, or a changing output tree.
    """
    directory = _directory(directory)
    _require(directory.is_dir(), "output directory missing")
    _require(not (directory / SEAL_NAME).exists(), "seal already exists; overwrite refused")
    _require(not (directory / FAILURE_NAME).exists(), "previous sealing failure retained")
    try:
        cost = _closed_receipt(directory)
        first = _snapshot(directory)
        _require(first == _snapshot(directory), "outputs changed before sealing")
        _require(cost == _closed_receipt(directory), "final receipt changed before sealing")
        seal = directory / SEAL_NAME
        _write_new(
            seal,
            dict(
                schema=SCHEMA,
                workload_status=cost["status"],
                complete_process_lifetimes=True,
                active_processes=0,
                final_receipt="cost.json",
                final_receipt_sha256=first["cost.json"]["sha256"],
                publication="observer only, after watch returned and all output handles closed",
                files=first,
                note="A valid STOP snapshot certifies retained bytes, not workload success.",
            ),
        )
        # The seal's own file handle has closed before this check and before return.
        verify_seal(directory, expected_seal_sha256=_digest(seal))
        return seal
    except BaseException as error:
        _record_failure(directory, error)
        raise


def verify_seal(directory: Path, *, expected_seal_sha256: str | None = None) -> dict[str, Any]:
    """Read-only check of membership, payload hashes, final receipt and workload status."""
    directory = _directory(directory)
    _require(not (directory / FAILURE_NAME).exists(), "sealing failure marker present")
    seal_path = directory / SEAL_NAME
    _require(seal_path.is_file() and not seal_path.is_symlink(), "seal missing or unsafe")
    if expected_seal_sha256 is not None:
        _require(_digest(seal_path) == expected_seal_sha256, "seal digest changed")
    seal = _read_json(seal_path)
    _require(seal.get("schema") == SCHEMA, "wrong seal format")
    _require(
        seal.get("complete_process_lifetimes") is True and seal.get("active_processes") == 0,
        "seal records unclosed processes",
    )
    cost = _closed_receipt(directory)
    _require(seal.get("workload_status") == cost["status"], "workload status changed")
    actual = _snapshot(directory)
    _require(actual == seal.get("files"), "sealed output membership, size or hash changed")
    _require(
        actual["cost.json"]["sha256"] == seal.get("final_receipt_sha256"),
        "final cost receipt changed",
    )
    return seal


def watch_and_seal(
    command: list[str],
    directory: Path,
    root: Path,
    seconds: float,
    memory: int = 2 * 1024**3,
    disk: int = 128 * 1024**2,
    interrupt_after: float | None = None,
    poll: float = 0.05,
) -> SealedRun:
    """Run once, drain/close/write final cost through v1 accounting, then publish a v2 seal."""
    directory, root = _directory(directory), _directory(root)
    _require(directory.is_relative_to(root), "output directory must be inside disk-accounting root")
    _require(not directory.exists(), "existing output directory; overwrite refused")
    try:
        cost: dict[str, Any] = watch(
            command,
            directory,
            root,
            seconds,
            memory,
            disk,
            interrupt_after=interrupt_after,
            poll=poll,
        )
        # watch waits for zero active descendants, closes stdout and monitor streams,
        # queries final kernel counters, closes process/Job handles, writes/closes cost.json.
        # No worker writes an observer seal. No monitor code runs after this point.
        _require(cost == _closed_receipt(directory), "returned/final cost receipt mismatch")
        seal_path = seal_closed_run(directory)
        return SealedRun(cost=cost, seal_path=seal_path, seal_sha256=_digest(seal_path))
    except BaseException as error:
        _record_failure(directory, error)
        raise


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "verify"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--expected-seal-sha256")
    argv = sys.argv[1:]
    boundary = argv.index("--") if "--" in argv else len(argv)
    args = parser.parse_args(argv[:boundary])
    command = argv[boundary + 1 :] if boundary < len(argv) else []
    if args.action == "verify":
        seal = verify_seal(args.directory, expected_seal_sha256=args.expected_seal_sha256)
        print(json.dumps(dict(integrity="PASS", workload_status=seal["workload_status"])))
        return
    if args.root is None:
        parser.error("--root is required for run")
    if not command:
        parser.error("a command after -- is required")
    result = watch_and_seal(command, args.directory, args.root, args.seconds)
    print(
        json.dumps(
            dict(
                workload_status=result.cost["status"],
                seal_path=str(result.seal_path),
                seal_sha256=result.seal_sha256,
            )
        )
    )
    sys.exit(0 if result.cost["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
