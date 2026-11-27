"""Verify preserved inputs, final checks and the built wheel without installation."""

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]


def verify():
    starting = json.loads((RUN / "starting-state.json").read_text())
    changed = []
    generated = []
    preserved = 0
    for relative, expected in starting["files"].items():
        path = ROOT / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if any(part.endswith(".egg-info") for part in path.parts):
            if actual != expected:
                generated.append(relative)
        elif actual != expected:
            changed.append(relative)
        else:
            preserved += 1
    assert not changed, changed
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == starting["head"]
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=normal"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    tracked = lambda text: {line for line in text.splitlines() if not line.startswith("??")}
    assert tracked(status.stdout) == tracked(starting["status"]), "tracked status changed"
    subprocess.run(["git", "diff", "--cached", "--exit-code"], cwd=ROOT, check=True,
                   capture_output=True)
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True, capture_output=True)
    wheel = next((RUN / "package-final").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        assert archive.read("toruk_lm/owned_resume.py") == (
            ROOT / "src/toruk_lm/owned_resume.py"
        ).read_bytes()
    code = (
        "import json, sys; sys.path.insert(0, sys.argv[1]); "
        "import toruk_lm; from toruk_lm import owned_resume; "
        "assert '.whl' in owned_resume.__file__; "
        "print(json.dumps({'version': toruk_lm.__version__, 'contract': owned_resume.CONTRACT, "
        "'module': owned_resume.__file__}))"
    )
    imported = subprocess.run([sys.executable, "-I", "-c", code, str(wheel)], cwd=RUN,
                              check=True, capture_output=True, text=True, timeout=60)
    checks = {}
    for label in ("resume-final", "final-pytest", "final-lint", "final-format", "final-types",
                  "final-types-linux", "final-build", "dependencies", "frozen-sources",
                  "web-check", "web-tests", "cli-help", "diagnose", "adapter-help"):
        record = json.loads((RUN / f"{label}.json").read_text())
        assert record["status"] == "PASS", label
        checks[label] = {key: record[key] for key in ("status", "command", "seconds")}
    return dict(
        status="PASS", head=head, preserved_source_config_test_doc_files=preserved,
        changed_preexisting_sources=changed, regenerated_build_metadata=generated,
        original_tracked_status_preserved=True, index_unchanged=True,
        wheel_import=json.loads(imported.stdout), checks=checks,
        scope="Software integrity validation only; no research-quality improvement claimed.",
    )


if __name__ == "__main__":
    result = verify()
    with (RUN / "delivery.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
