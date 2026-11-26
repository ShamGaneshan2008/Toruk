"""Create a disposable depth-one clone plus the exact pending CI repair overlay."""

import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
FILES = [
    ".github/workflows/ci.yml",
    "scripts/audit_qwen_development_v4.py",
    "scripts/ci_contracts.py",
    "scripts/check_local_research_checkpoints.py",
    "scripts/diagnose_initialization_contract.py",
    "tests/conftest.py",
    "tests/test_ci_contracts.py",
    "tests/test_lifetime_sealing_portable.py",
    "artifacts/ci-contract-repair-45439669299-20261126/.gitattributes",
    "artifacts/ci-contract-repair-45439669299-20261126/historical/attributes-e3c9979.txt",
    "artifacts/ci-contract-repair-45439669299-20261126/historical/attributes-provenance.json",
]


def main():
    destination=BASE / "fresh-clone-001"
    assert destination.resolve().is_relative_to(ROOT) and not destination.exists()
    command=["git","-c","core.autocrlf=false","clone","--depth","1","--no-local","--no-hardlinks","--single-branch",ROOT.as_uri(),str(destination)]
    with (BASE / "fresh-clone-create.log").open("xb") as stream:
        subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    for name in FILES:
        target=destination / name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    assert not list((destination / "artifacts/local-answer-dev-v1/stages").glob("*/checkpoint.pt"))
    print(json.dumps(dict(clone=str(destination),overlay_files=len(FILES),historical_weights_present=False)))


if __name__=="__main__":
    main()
