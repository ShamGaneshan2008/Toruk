"""Seal the local M7 source and referenced evidence without publishing anything."""

import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check import source_identity, sources  # noqa: E402

from toruk_lm.controlled import package_fingerprint  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


directory = ROOT / "artifacts/m7-handoff"
directory.mkdir(exist_ok=False)
files = sources() + [ROOT / "README.md"] + list((ROOT / "docs").rglob("*.md"))
files += [ROOT / "artifacts/m7-analyze.py", Path(__file__).resolve()]
with zipfile.ZipFile(directory / "source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(files)):
        archive.write(path, path.relative_to(ROOT).as_posix())
environment = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
(directory / "environment.txt").write_text(environment, encoding="utf-8")
evidence = list((ROOT / "artifacts/checks").glob("m7-*"))
for path in (ROOT / "artifacts").glob("m7-*"):
    if path == directory:
        continue
    evidence += list(path.rglob("*")) if path.is_dir() else [path]
for name in ("m6-validation-001", "m6-failed-tiny-001", "m6-handoff"):
    evidence += list((ROOT / "artifacts" / name).rglob("*"))
evidence += list(directory.iterdir())
identity = source_identity()
checks = {p.stem: json.loads(p.read_text()) for p in (ROOT / "artifacts/checks").glob("m7-*.json")}
assert all(
    r["status"] == "PASS" and r["source_sha256"] == identity["source_sha256"]
    for name, r in checks.items()
    if name.startswith("m7-final-")
)
protocols = [
    json.loads((ROOT / f"artifacts/m7-{s}-001/protocol.json").read_text())
    for s in ("templates", "load")
]
assert all(p["package_sha256"] == package_fingerprint() for p in protocols)
record = dict(
    **identity,
    schema="m7-local-handoff-v1",
    sealed_utc=datetime.now(UTC).isoformat(),
    branch=subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
    status="PARTIAL; exploratory failure studies, no generalization advantage",
    package_sha256=package_fingerprint(),
    evidence_sha256={
        p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(evidence)) if p.is_file()
    },
    checks={
        name: {k: r[k] for k in ("status", "seconds", "command", "evidence_path")}
        for name, r in checks.items()
    },
    remote=json.loads((ROOT / "artifacts/m7-remote-runs.json").read_text(encoding="utf-8-sig")),
    final_test="NOT_RUN for scoring/selection; M6 manifest hashes verified only",
    clean_machine_reproduction="NOT_RUN; retained checkpoints required and ignored by Git",
    training_seeds=[23],
    data_seeds=[117, 118],
    new_study_training_steps=0,
    uncertainties="No training-seed replication; four correlated semantic anchors",
    accounting="Stage/check wall times retained; test training-token accounting incomplete",
    actions="No commit, push, branch creation, publishing, paid compute or workflow trigger",
)
(directory / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
assert all(digest(ROOT / name) == expected for name, expected in record["evidence_sha256"].items())
print(
    json.dumps(
        {
            "status": "PASS",
            "source_sha256": identity["source_sha256"],
            "evidence_files": len(record["evidence_sha256"]),
            "branch": record["branch"],
        }
    )
)
