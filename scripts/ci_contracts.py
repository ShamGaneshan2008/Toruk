"""CI contracts for optional local inputs and versioned attribute evidence."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROBE = "artifacts/local-answer-first-byte-probe-v1"
PROBE_REGISTRATION_SHA = "b244089a172bf7933fe53ee1558b2e8ac1c393c03e837e22e884dee052863213"
ATTRIBUTE_BASE = "b304091bd16a12be7204d207ed7d82e51e5ba9a6"
ATTRIBUTE_COMMIT = "e3c143ab0095faeb36ecc693c7e1cea09e1f7d24"
ATTRIBUTE_SHA = "e3c9979c8b004038b145d85d10cc196d51c27bc7fc061b04a32db96ce6e12c41"
ATTRIBUTE_SNAPSHOT = (
    "artifacts/ci-contract-repair-45439669299-20261126/historical/attributes-e3c9979.txt"
)


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_identity() -> dict[str, str]:
    return dict(
        python=platform.python_version(),
        platform=platform.platform(),
        torch=importlib.metadata.version("torch"),
        psutil=importlib.metadata.version("psutil"),
    )


def missing_probe_checkpoints(root: Path = ROOT) -> list[str]:
    return [
        meta["path"]
        for meta in probe_registration(root)["checkpoints"].values()
        if not (root / meta["path"]).is_file()
    ]


def check_probe_checkpoints(root: Path = ROOT) -> dict[str, Any]:
    records = {}
    for cell, meta in probe_registration(root)["checkpoints"].items():
        path = root / meta["path"]
        if not path.is_file():
            records[cell] = dict(status="MISSING", path=meta["path"])
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        status = (
            "PASS" if actual == meta["sha256"] and path.stat().st_size == meta["bytes"] else "FAIL"
        )
        records[cell] = dict(
            status=status, path=meta["path"], expected_sha256=meta["sha256"], actual_sha256=actual
        )
    status = (
        "FAIL"
        if any(r["status"] == "FAIL" for r in records.values())
        else "MISSING_INPUTS"
        if any(r["status"] == "MISSING" for r in records.values())
        else "PASS"
    )
    return dict(status=status, checkpoints=records, model_loaded=False, substitutes_created=False)


def probe_registration(root: Path = ROOT) -> dict[str, Any]:
    raw = (root / PROBE / "registration.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROBE_REGISTRATION_SHA:
        raise ValueError("frozen probe registration changed")
    return dict(json.loads(raw))


def historical_attributes(root: Path, commit: str, expected: str) -> tuple[bytes, str]:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("historical attributes require a full frozen commit SHA")
    # The bundle manifest was published after its baseline commit. Its unchanged
    # attributes digest belongs to the publication blob, not the baseline blob.
    source_commit = (
        ATTRIBUTE_COMMIT if commit == ATTRIBUTE_BASE and expected == ATTRIBUTE_SHA else commit
    )
    result = subprocess.run(
        ["git", "show", f"{source_commit}:.gitattributes"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        raw, source = result.stdout, f"git:{source_commit}:.gitattributes"
    elif commit == ATTRIBUTE_BASE and expected == ATTRIBUTE_SHA:
        raw, source = (root / ATTRIBUTE_SNAPSHOT).read_bytes(), ATTRIBUTE_SNAPSHOT
    else:
        raise ValueError("historical attributes Git object is unavailable; no bound snapshot")
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("historical attributes hash mismatch")
    return raw, source


def current_attributes(root: Path = ROOT) -> dict[str, dict[str, str]]:
    expected = {
        "artifacts/local-answer-value-start-replication-v2/registration.json": {"text": "unset"},
        "docs/research/local-answer-value-start-replication-v2-results.md": {
            "text": "set",
            "eol": "lf",
        },
        "scripts/lifetime_job.py": {"text": "set", "eol": "lf"},
    }
    output = subprocess.check_output(
        ["git", "check-attr", "-z", "text", "eol", "--", *expected], cwd=root
    )
    parts = output.decode().strip("\0").split("\0")
    actual: dict[str, dict[str, str]] = {}
    for index in range(0, len(parts), 3):
        name, attribute, value = parts[index : index + 3]
        actual.setdefault(name, {})[attribute] = value
    for name, attributes in expected.items():
        if any(actual[name].get(key) != value for key, value in attributes.items()):
            raise ValueError("current repository attributes contract failed: " + name)
    return actual
