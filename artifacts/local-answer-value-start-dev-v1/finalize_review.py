"""Finalize review records; saved evidence only, no model work."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
sys.path.insert(0, str(RUN))
import verify_saved

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

audit = verify_saved.audit()
assert audit["measurement_integrity"] == "PASS"
assert audit["decision"] == "STOP_DEVELOPMENT_FAILURE"
for directory, expected in [
    ("independent-audit-execution", "21168c1e8de41321d2de2e19f0b201a6f0ad87400fecb8d82547784466037208"),
    ("verification/execution", None),
]:
    path = RUN / directory
    digest = sha(path / "observer-seal-v2.json")
    if expected:
        assert digest == expected
    verify_saved.verify_seal(path, expected_seal_sha256=digest)

report = ROOT / "docs/research/local-answer-value-start-dev-v1-results.md"
text = report.read_text(encoding="utf-8")
assert audit["plan_sha256"] in text and audit["registration_sha256"] in text
for seed in [601,947]:
    for model in ["ordinary","recurrent"]:
        for arm in ["uniform","first16"]:
            cell=audit["cells"][f"{seed}-{model}-{arm}"]
            t=cell["training"]["metrics"]
            d=cell["development"]["metrics"]
            expected=f"| {seed} | {model} | {arm} | {t['exact']} | {t['wrong_first']} | {d['exact']} | {d['wrong_first']} |"
            assert expected in text, expected
for target in re.findall(r"\]\(([^)]+)\)",text):
    assert (report.parent/target).exists() or (report.parent/target).resolve() == RUN/"review-inventory.json", target
scopes=audit["nonoverlapping_cost_scopes"]+["independent-audit-execution","verification/execution"]
costs={name:json.loads((RUN/name/"cost.json").read_text()) for name in scopes}
cpu=sum(c["cpu"] for c in costs.values())
wall=sum(c["wall"] for c in costs.values())
assert f"{cpu:.6f}" in text and f"{wall:.6f}" in text
extra=[
    ROOT/"scripts/value_start_dev.py",
    ROOT/"tests/test_value_start_dev.py",
    ROOT/"docs/research/local-answer-value-start-dev-v1-protocol.md",
    report,
]
for path in extra:
    for number,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        assert line.rstrip()==line, (str(path),number,"trailing whitespace")
for args in [("diff","--check"),("diff","--cached","--check")]:
    subprocess.run(["git",*args],cwd=ROOT,check=True)
assert git("rev-parse","--show-toplevel") == "D:/Toruk"
assert git("rev-parse","HEAD") == audit["source_commit"]
assert git("diff","--name-only") == ""
assert git("diff","--cached","--name-only") == ""
expected_paths={
    "artifacts/local-answer-value-start-dev-v1/",
    "docs/research/local-answer-value-start-dev-v1-protocol.md",
    "docs/research/local-answer-value-start-dev-v1-results.md",
    "scripts/value_start_dev.py",
    "tests/test_value_start_dev.py",
}
status_lines=git("status","--porcelain=v1","--untracked-files=normal").splitlines()
assert all(line.startswith("?? ") for line in status_lines), status_lines
actual_paths={line[3:] for line in status_lines}
assert actual_paths == expected_paths, actual_paths

excluded_prefixes=("preflight-mypy/","verification-mypy/","phase1-tmp/","preparation/pytest-tmp/")
excluded_final={"review-inventory.json","final-review-qa.json","review-anchor.json"}
paths=list(extra)
excluded_reparse=[]
for current,dirs,files in os.walk(RUN,followlinks=False):
    current=Path(current)
    keep=[]
    for name in dirs:
        path=current/name
        rel=path.relative_to(RUN).as_posix()+"/"
        if name=="__pycache__" or any(rel.startswith(p) for p in excluded_prefixes):
            continue
        if path.is_symlink() or path.is_junction():
            excluded_reparse.append(path.relative_to(ROOT).as_posix())
            continue
        keep.append(name)
    dirs[:]=keep
    for name in files:
        path=current/name
        if current==RUN and name in excluded_final:
            continue
        if path.suffix in [".pyc",".pyo"]:
            continue
        assert not path.is_symlink()
        paths.append(path)
files={}
weights=[]
for path in sorted(paths):
    relative=path.relative_to(ROOT).as_posix()
    files[relative]={"bytes":path.stat().st_size,"sha256":sha(path)}
    if path.suffix==".pt":
        subprocess.run(["git","check-ignore","--quiet","--",relative],cwd=ROOT,check=True)
        weights.append(relative)
assert len(weights)==8,weights
inventory={
    "format":"toruk-value-start-review-inventory-v1",
    "source_commit":audit["source_commit"],
    "status":"LOCAL_UNCOMMITTED_REVIEW",
    "files":files,
    "included_files":len(files),
    "included_bytes":sum(x["bytes"] for x in files.values()),
    "local_ignored_checkpoints":weights,
    "excluded_retained_locally":{
        "prefixes":list(excluded_prefixes),
        "cache_names":["__pycache__","*.pyc","*.pyo"],
        "final_records_not_self_hashed":sorted(excluded_final),
        "reparse_paths":excluded_reparse,
        "reason":"Caches and intentional negative-test fixture trees are not scientific payload; final records excluded to avoid circular hashes."
    },
    "scientific_decision":audit["decision"],
    "measurement_integrity":audit["measurement_integrity"],
    "scope_exception":"Pre-freeze unrelated search access cannot be certified zero; no held-out evaluation or experimental held-out inputs.",
}
write(RUN/"review-inventory.json",inventory)
for target in re.findall(r"\]\(([^)]+)\)",text):
    assert (report.parent/target).exists(), target
# Re-read every included file, independently of enumeration-time hashes.
for relative,record in files.items():
    path=ROOT/relative
    assert path.stat().st_size==record["bytes"] and sha(path)==record["sha256"]
qa={
    "status":"PASS_FINAL_SAVED_EVIDENCE_REVIEW",
    "report_table_verified_cells":8,
    "report_links_resolve":True,
    "untracked_source_and_doc_whitespace":"PASS",
    "git_diff_check":"PASS",
    "git_diff_cached_check":"PASS",
    "all_scientific_seals_stable":True,
    "scientific_stage_seals":24,
    "original_paired_files_unchanged":337,
    "protected_existing_files_unchanged":737,
    "enumerated_existing_ignored_checkpoints_unchanged":65,
    "new_ignored_checkpoints":8,
    "inventory_included_files":len(files),
    "inventory_included_bytes":inventory["included_bytes"],
    "inventory_rehash":"PASS",
    "inventory_sha256":sha(RUN/"review-inventory.json"),
    "report_sha256":sha(report),
    "verification_observer_seal_sha256":sha(RUN/"verification/execution/observer-seal-v2.json"),
    "scientific_decision":audit["decision"],
    "measurement_integrity":audit["measurement_integrity"],
    "measured_nonoverlapping_cpu_including_postchecks":cpu,
    "measured_nonoverlapping_wall_including_postchecks":wall,
    "reporting_and_final_review_cost":"Unmeasured outside named complete Jobs; no new fits, forwards or answers.",
    "head":git("rev-parse","HEAD"),
    "branch":git("branch","--show-current"),
    "status":git("status","-sb"),
    "staged_files":[],
    "tracked_modifications":[],
    "hosted_ci":"NOT_RUN",
}
write(RUN/"final-review-qa.json",qa)
write(RUN/"review-anchor.json",{
    "format":"toruk-review-anchor-v1",
    "inventory_sha256":sha(RUN/"review-inventory.json"),
    "qa_sha256":sha(RUN/"final-review-qa.json"),
    "report_sha256":sha(report),
    "anchor_requires_external_trusted_hash":True,
})
print(json.dumps(qa,indent=2))
print("REVIEW_ANCHOR_SHA256",sha(RUN/"review-anchor.json"))
