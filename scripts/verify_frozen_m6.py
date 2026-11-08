"""Verify a recovered M6 candidate before loading it; never substitute or normalize weights."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d"
EXPECTED_ARCHIVE_SHA256 = "def3d8be4f380f92bf2ae7e2a3ef4b8675f4576f08fd859258da3a2f9f53710d"
CHECKPOINT = "artifacts/m6-validation-001/recurrent/checkpoint.pt"


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def historical_contract(root: Path = ROOT) -> dict[str, Any]:
    """Cross-check independent recorded bindings against immutable expected identities."""
    run = root / "artifacts/m6-validation-001"
    metrics = read(run / "recurrent/metrics.json")
    seal = read(root / "artifacts/m6-handoff/manifest.json")
    bindings = {
        "training_metrics": metrics["checkpoint_sha256"],
        "run_manifest": read(run / "manifest.json")["files"]["recurrent/checkpoint.pt"],
        "handoff_manifest": seal["evidence_sha256"][CHECKPOINT],
        "chat_release": read(root / "artifacts/chat-release-v2/raw.json")["selector_sha256"],
    }
    if any(value != EXPECTED_SHA256 for value in bindings.values()):
        raise ValueError("historical checkpoint bindings disagree with frozen expected hash")
    archive = root / "artifacts/m6-handoff/source.zip"
    if (
        sha256_file(archive) != EXPECTED_ARCHIVE_SHA256
        or seal["evidence_sha256"]["artifacts/m6-handoff/source.zip"] != EXPECTED_ARCHIVE_SHA256
    ):
        raise ValueError("historical source archive identity mismatch")
    with zipfile.ZipFile(archive) as source:
        for name in (
            "src/toruk_lm/data.py",
            "src/toruk_lm/controlled.py",
            "src/toruk_lm/comparisons.py",
        ):
            if hashlib.sha256(source.read(name)).hexdigest() != seal["source_files"][name]:
                raise ValueError("historical source member identity mismatch: " + name)
    return {
        "expected_sha256": EXPECTED_SHA256,
        "hash_material": "raw bytes of the complete checkpoint.pt file; no normalization",
        "bindings": bindings,
        "source_archive_sha256": EXPECTED_ARCHIVE_SHA256,
        "config": metrics["config"],
        "data": metrics["data"],
        "package_sha256": metrics["package_sha256"],
        "parameters": metrics["parameters"],
        "steps": metrics["total_steps"],
    }


def inspect_candidate(path: Path, root: Path = ROOT) -> dict[str, Any]:
    contract = historical_contract(root)
    result: dict[str, Any] = {
        "checkpoint": str(path),
        "contract": contract,
        "candidate_status": "MISSING",
        "m6_reproduction": "BLOCKED",
        "warning": "Candidate verification is not fresh M6 inference reproduction.",
    }
    if not path.is_file():
        return result
    result["actual_sha256"] = sha256_file(path)
    if result["actual_sha256"] != EXPECTED_SHA256:
        result["candidate_status"] = "IDENTITY_MISMATCH"
        return result

    # No unverified candidate reaches deserialization. The loader uses weights_only=True.
    from toruk_lm.controlled import load_controlled
    from toruk_lm.recurrent import RecurrentLM

    model, saved = load_controlled(path)
    if (
        not isinstance(model, RecurrentLM)
        or saved["config"] != contract["config"]
        or saved["data"] != contract["data"]
        or saved["package_sha256"] != contract["package_sha256"]
        or saved["next_step"] != contract["steps"]
        or sum(parameter.numel() for parameter in model.parameters()) != contract["parameters"]
        or sha256_file(path) != EXPECTED_SHA256
    ):
        raise ValueError("identified checkpoint is incompatible with recorded M6 model metadata")
    result.update(
        candidate_status="VERIFIED_ORIGINAL",
        format=saved["format"],
        boundary=saved["boundary"],
        tokenizer=saved["tokenizer"],
        m6_reproduction="NOT_RUN; use the verified archived inference/scoring source",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / CHECKPOINT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh output path; prior provenance evidence is immutable")
    result = inspect_candidate(args.checkpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["candidate_status"] == "VERIFIED_ORIGINAL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
