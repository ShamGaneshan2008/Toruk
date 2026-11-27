"""Verify preservation and check receipts without loading any models or checkpoints."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
CITY = ROOT / "artifacts/local-answer-city-contrastive-dev-v1"
V2 = ROOT / "artifacts/local-answer-value-start-replication-v2"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    assert not any(s in str(path).lower() for s in ("heldout", "held-out", "held_out"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    files = read(path)["files"]
    for name, expected in files.items():
        target = (ROOT / name).resolve()
        assert target.is_relative_to(ROOT), name
        assert target.stat().st_size == expected["bytes"], name
        assert digest(target) == expected["sha256"], name
    return len(files)


def verify():
    start = read(RUN / "starting-state.json")
    assert digest(CITY / "delivery-inventory.json") == start["scientific_inventory_sha256"]
    city_count = inventory(CITY / "delivery-inventory.json")
    v2_count = inventory(V2 / "review-inventory.json")
    sources = read(CITY / "plan-final.json")["sources"]
    for name, expected in sources.items():
        assert digest(ROOT / name) == expected, name
    intentionally_changed = {
        "src/toruk_lm/owned_resume.py",
        "tests/test_owned_resume.py",
        "docs/owned-resume.md",
    }
    for name, expected in start["files"].items():
        assert digest(RUN / "before" / name) == expected, name
        assert (digest(ROOT / name) != expected) == (name in intentionally_changed), name
    checks = {}
    for label in (
        "final-tests", "lint", "format", "types", "types-linux", "reviewer-types",
        "build", "offline-study-review-002",
    ):
        receipt = read(RUN / (label + ".json"))
        assert receipt["status"] == "PASS" and receipt["returncode"] == 0, label
        checks[label] = {
            "status": receipt["status"],
            "command": receipt["command"],
            "receipt_sha256": digest(RUN / (label + ".json")),
            "log_sha256": digest(RUN / (label + ".log")),
        }
    package = read(RUN / "package-import.json")
    assert digest(Path(package["module"])) == digest(ROOT / "src/toruk_lm/owned_resume.py")
    audit = read(RUN / "offline-study-review-002.log")
    checkpoints = [
        name for name in read(CITY / "delivery-inventory.json")["files"] if name.endswith(".pt")
    ]
    changed = intentionally_changed | {
        "scripts/check_city_contrastive_evidence.py",
        "tests/test_research_observation_review.py",
    }
    for name in changed:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert text.endswith("\n"), name
        assert all(line == line.rstrip() for line in text.splitlines()), name
    return {
        "status": "PASS",
        "city_artifacts_unchanged": city_count,
        "city_checkpoints_unchanged": len(checkpoints),
        "city_registered_sources_unchanged": len(sources),
        "v2_files_unchanged": v2_count,
        "archived_original_files": len(start["files"]),
        "current_review_files": {name: digest(ROOT / name) for name in sorted(changed)},
        "checks": checks,
        "package_import": package,
        "scientific_decision": audit["decision"],
        "observations_checked": audit["observations_checked"],
        "seals_checked": audit["scientific_seals"],
        "audit_model_forwards": audit["model_forwards"],
        "heldout_opened": audit["heldout_opened"],
        "limitations": "Focused tests only; no scientific cells retried; no model-quality claim.",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, allow_nan=False))
