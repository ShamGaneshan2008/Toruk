"""Seal the unreleased M8 handoff without copying checkpoints or environment secrets."""

import importlib.metadata
import json
import platform
import subprocess
import zipfile
from datetime import UTC, datetime

from check import ROOT, source_identity, sources


def main():
    import hashlib

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    output = ROOT / "artifacts/m8-handoff"
    output.mkdir(exist_ok=True)
    files = sources() + [ROOT / "README.md"] + list((ROOT / "docs").rglob("*.md"))
    with zipfile.ZipFile(output / "source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    environment = dict(
        python=platform.python_version(),
        platform=platform.platform(),
        packages={d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
    )
    (output / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )
    evidence = [
        p
        for p in (ROOT / "artifacts").glob("m8-*/**/*")
        if p.is_file()
        and output not in p.parents
        and "env" not in p.parts
        and "__pycache__" not in p.parts
        and p.suffix != ".pt"
    ]
    evidence += list((ROOT / "artifacts/checks").glob("m8-*.*"))
    checkpoints = [p for p in (ROOT / "artifacts/m6-validation-001").rglob("*.pt")]
    record = dict(
        **source_identity(),
        schema="m8-internal-handoff-v1",
        sealed_utc=datetime.now(UTC).isoformat(),
        branch=subprocess.check_output(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "branch", "--show-current"],
            cwd=ROOT,
            text=True,
        ).strip(),
        status="PARTIAL; see docs/internal/m8/audit.md",
        publication="not authorized; internal only",
        archive_sha256=digest(output / "source.zip"),
        environment_sha256=digest(output / "environment.json"),
        evidence_sha256={p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(evidence))},
        checkpoint_inventory={
            p.relative_to(ROOT).as_posix(): dict(
                sha256=digest(p),
                bytes=p.stat().st_size,
                availability="local only; ignored by Git; no authorized download",
            )
            for p in checkpoints
        },
        test_access=(
            "research runs generate/hash test; unit tests inspect deterministic test labels; "
            "no recorded final-test model scoring"
        ),
        limitations=(
            "No redistribution license, hermetic fresh-dependency install, "
            "full M7 regeneration or multi-seed research confirmation"
        ),
    )
    (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({key: record[key] for key in ("base_commit", "source_sha256", "archive_sha256")})
    )


if __name__ == "__main__":
    main()
