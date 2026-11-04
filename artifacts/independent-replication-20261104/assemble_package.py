"""Build a local base-checkout overlay with evidence; never include model weights."""

import hashlib
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDY = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import independent_replication as experiment


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


archive_path = STUDY / "toruk-replication-package.zip"
if archive_path.exists() or (STUDY / "final-accounting.json").exists():
    raise ValueError("Refusing existing final package/accounting")
experiment.verify(STUDY / "evaluation")
experiment.study.verify(STUDY / "phase1", True)
previous = ROOT / "artifacts/rank-budget-v1-20261104"
previous_seal = json.loads((previous / "outputs-seal.json").read_text(encoding="utf-8"))
assert all(digest(ROOT / path) == expected for path, expected in previous_seal.items())

package_dir = STUDY / "verification/package/final"
sdist = next(package_dir.glob("*.tar.gz"))
required = (
    "scripts/independent_replication.py", "scripts/independent_cases.py",
    "scripts/report_independent_replication.py", "configs/independent-chat-cards-v1.json",
    "docs/research/independent-replication-v1-protocol.md",
    "docs/research/independent-replication-v1-results.md",
    "docs/research/independent-replication-v1/draft.md",
    "docs/research/independent-replication-v1/claim-ledger.json",
    "docs/research/independent-replication-v1/reproduce.md",
)
with tarfile.open(sdist) as archive:
    names = archive.getnames()
    prefix = names[0].split("/")[0] + "/"
    assert all(prefix + path in names for path in required)
    assert not any("/docs/internal/" in name for name in names)

records = []
for folder in ("checks", "verification"):
    for path in sorted((STUDY / folder).glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if "command" in row and "status" in row:
            records.append({"record": path.relative_to(ROOT).as_posix(), **{
                key: row[key] for key in ("command", "status", "returncode", "seconds")
            }})
task_files = [
    ".github/workflows/ci.yml", ".gitignore", "MANIFEST.in", "README.md",
    "docs/architecture.md", "docs/experiments.md", "docs/local-chat.md",
    "docs/research/rank-budget-v1-results.md", "scripts/verify.py",
    "configs/independent-chat-cards-v1.json", "scripts/independent_cases.py",
    "scripts/independent_replication.py", "scripts/report_independent_replication.py",
    "tests/test_independent_replication.py",
    "docs/research/independent-replication-v1-protocol.md",
    "docs/research/independent-replication-v1-results.md",
    *[path.relative_to(ROOT).as_posix() for path in sorted((ROOT / "docs/research/independent-replication-v1").iterdir())],
]
summary = json.loads((STUDY / "evaluation/summary.json").read_text(encoding="utf-8"))
status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
accounting = {
    "starting": json.loads((STUDY / "start.json").read_text(encoding="utf-8")),
    "ending_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "ending_git_status": status,
    "task_changed_files": task_files,
    "new_artifact_directory": STUDY.relative_to(ROOT).as_posix(),
    "previous_evidence_files_preserved": len(previous_seal),
    "reproduction": "96/96 exact prompts/answers/scores/evidence/work fields",
    "independent_model_answers": 144,
    "controlled_model_answers": 72,
    "new_audit": "216/216 PASS",
    "central_claim": "NOT_ESTABLISHED; both frozen efficiency/quality gates fail",
    "gates": {suite: block["gates"] for suite, block in summary["suites"].items()},
    "records": records,
    "initial_failures_retained": [row for row in records if row["status"] != "PASS"],
    "additional_read_only_inspection_failure": "One ad-hoc python -c summary inspection had a mismatched delimiter; no file/inference changed. Corrected inspection and total-cost audit passed.",
    "engineering": {
        "python_ci_equivalents": "20/20 PASS", "full_python_tests": "204 passed; zero skips",
        "focused_new_tests": "9 passed", "node_tests": "13 passed; one optional live test skipped",
        "lint_format": "PASS; 111 files", "runtime_types": "Windows/Linux PASS, 30 files each",
        "research_types": "PASS; 3 files with documented suppressions",
        "build_final": "PASS; required draft, ledger, case/config and evaluator paths verified in sdist",
        "whitespace": "PASS", "hosted_ci": "NOT_RUN",
    },
    "archive": archive_path.relative_to(ROOT).as_posix(),
    "archive_audit": (STUDY / "package-audit.json").relative_to(ROOT).as_posix(),
    "next_submission_step": "External replication with independent human adjudication on a real conversational benchmark.",
}
with (STUDY / "final-accounting.json").open("x", encoding="utf-8") as stream:
    json.dump(accounting, stream, indent=2, ensure_ascii=False)
    stream.write("\n")

files = set(task_files)
for path in STUDY.rglob("*"):
    if path.is_file() and "package" not in path.parts and path.suffix != ".pt":
        files.add(path.relative_to(ROOT).as_posix())
seal = {name: digest(ROOT / name) for name in sorted(files)}
with (STUDY / "outputs-seal.json").open("x", encoding="utf-8") as stream:
    json.dump(seal, stream, indent=2)

tracked = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
payload = set(tracked + untracked)
# Preserve every frozen input's exact bytes, including source line endings and
# small model support files; the large pretrained weights are obtained separately.
manifests = [
    STUDY / "mechanism-freeze.json", STUDY / "evaluation/registration.json",
    previous / "registration.json", previous / "intervention.json",
]
for path in manifests:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    payload.update(name.replace("\\", "/") for name in manifest["bindings"])
for name in list(payload):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Package input outside repository: {name}")
    if (
        path.suffix in (".pt", ".safetensors", ".zip")
        or "package" in path.parts or "__pycache__" in path.parts
        or path.name in (".env", "credentials.json", "package-audit.json")
        or any(part in (".git", ".aws", ".codex", ".agents") for part in path.parts)
        or "/docs/internal/" in path.as_posix()
    ):
        payload.remove(name)
assert "artifacts/qwen-chat-001/backbone/model.safetensors" not in payload
hashes = {name: digest(ROOT / name) for name in sorted(payload)}
readme = (
    "TORUK exploratory replication overlay\n\n"
    "Base checkout: 84ad607473f76b04f9dd1c2aaae2e3201f4ee0ca\n"
    "Extract over that checkout; preserve supplied bytes. Pretrained weights are omitted.\n"
    "Start: docs/research/independent-replication-v1/README.md\n"
    "Reproduce: docs/research/independent-replication-v1/reproduce.md\n"
    "Verdict: efficiency/quality claim NOT ESTABLISHED. Local draft only; no publication.\n"
    "Each payload digest is in ZIP_PAYLOAD_SHA256.json. No .git, credentials or private notes.\n"
).encode()
hashes["REPLICATION_PACKAGE.md"] = hashlib.sha256(readme).hexdigest()
with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for name in sorted(payload):
        archive.write(ROOT / name, name)
    archive.writestr("REPLICATION_PACKAGE.md", readme)
    archive.writestr("ZIP_PAYLOAD_SHA256.json", json.dumps(hashes, indent=2) + "\n")
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    assert all(hashlib.sha256(archive.read(name)).hexdigest() == expected for name, expected in hashes.items())
    assert not any(name.endswith((".safetensors", ".pt")) for name in archive.namelist())
audit = {
    "status": "PASS", "archive": archive_path.relative_to(ROOT).as_posix(),
    "sha256": digest(archive_path), "bytes": archive_path.stat().st_size,
    "payload_entries_verified": len(hashes), "sealed_current_files": len(seal),
    "pretrained_weights_included": False, "sdist_required_paths_verified": list(required),
    "scope": "Local source/evidence overlay on named base checkout; not a hosted release or new external replication.",
}
with (STUDY / "package-audit.json").open("x", encoding="utf-8") as stream:
    json.dump(audit, stream, indent=2)
print(json.dumps(audit, indent=2))
