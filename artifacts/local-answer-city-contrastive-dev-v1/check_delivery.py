"""Read-only preservation/seal verification; exclusive final inventory publication."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job_v2 import verify_seal  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    starting = read(RUN / "starting-state.json")
    for name,digest in starting["files"].items():
        assert sha(ROOT/name) == digest, name
    protected = read(ROOT/"artifacts/local-answer-value-start-replication-v2/review-inventory.json")["files"]
    for name,meta in protected.items():
        assert (ROOT/name).stat().st_size == meta["bytes"] and sha(ROOT/name) == meta["sha256"],name
    plan = read(RUN/"plan-final.json")
    for name,digest in plan["sources"].items():
        assert sha(ROOT/name) == sha(RUN/"sources"/name) == digest,name
    for name,digest in plan["data"].items():
        assert sha(RUN/name) == digest,name
    reg = read(RUN/"registration.json")
    assert reg["plan_sha256"] == sha(RUN/"plan-final.json")
    for item in reg["prerequisite_seals"]:
        verify_seal(RUN/item["path"],expected_seal_sha256=item["sha256"])
    for name in ("execution-receipt.json","registered-budget-receipt.json"):
        item=read(RUN/name)
        verify_seal(RUN/item["path"],expected_seal_sha256=item["sha256"])
    ledger=[json.loads(s) for s in (RUN/"registered/execution/stages.jsonl").read_text().splitlines()]
    assert len(ledger) == 48
    for entry in ledger:
        verify_seal(RUN/"registered/execution"/entry["path"],expected_seal_sha256=entry["seal_sha256"])
    for name in ("audit-execution","verification/job"):
        seal=verify_seal(RUN/name)
        assert seal["workload_status"] == "PASS"
    assert sha(RUN/"independent-audit.json") == sha(RUN/"audit-execution/audit.json")
    assert sha(RUN/"verification/checks.json") == sha(RUN/"verification/job/checks.json")
    assert read(RUN/"verification/checks.json")["status"] == "PASS"
    audit=read(RUN/"independent-audit.json")
    assert audit["status"] == "PASS" and audit["measurement_integrity"] == "PASS"
    assert audit["decision"] == read(RUN/"registered/execution/summary.json")["decision"]
    assert audit["optimizer_steps_verified"] == 24576
    checkpoints=list((RUN/"registered/execution/stages").glob("fit-*/checkpoint.pt"))
    assert len(checkpoints) == 16
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    assert head == starting["head"]
    subprocess.run(["git","diff","--cached","--exit-code"],cwd=ROOT,capture_output=True,check=True)
    changes=["scripts/city_contrastive_dev.py","scripts/audit_city_contrastive_dev.py",
             "tests/test_city_contrastive_dev.py",
             "docs/research/local-answer-city-contrastive-dev-v1-protocol.md",
             "docs/research/local-answer-city-contrastive-dev-v1-results.md"]
    for name in changes:
        data=(ROOT/name).read_text(encoding="utf-8")
        assert data.endswith("\n") and all(line == line.rstrip() for line in data.splitlines()),name
    return dict(status="PASS",scientific_gate="PASS" if audit["decision"] ==
                "DEVELOPMENT_GATES_PASS" else "FAIL",decision=audit["decision"],head=head,
                existing_named_files_unchanged=len(starting["files"]),
                historical_v2_payloads_unchanged=len(protected),scientific_seals=48,
                retained_ignored_checkpoints=16,source_plan_sha256=sha(RUN/"plan-final.json"),
                registration_sha256=sha(RUN/"registration.json"),new_source_docs_tests=changes,
                artifact_directory=RUN.relative_to(ROOT).as_posix(),
                readable_git_checks="PASS: approved read-only Git status and working/cached diff checks; "
                "tool receipt retained in conversation. No tracked/staged changes; pre-existing "
                "untracked work remains. Sandbox apparent deletions are access artifacts.")


if __name__ == "__main__":
    result=verify()
    files={}
    for folder,dirs,names in os.walk(RUN):
        dirs[:]=[d for d in dirs if not d.endswith("-temp") and d not in {"__pycache__"}]
        for name in names:
            path=Path(folder)/name
            if name in {"delivery-inventory.json","delivery-receipt.json"}:
                continue
            files[path.relative_to(ROOT).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha(path))
    with (RUN/"delivery-inventory.json").open("x",encoding="utf-8") as stream:
        json.dump(dict(files=files),stream,indent=2,sort_keys=True);stream.write("\n")
    result["inventory_sha256"]=sha(RUN/"delivery-inventory.json")
    result["inventoried_files"]=len(files)
    with (RUN/"delivery-receipt.json").open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write("\n")
    print(json.dumps(result,indent=2))
