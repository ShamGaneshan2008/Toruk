"""Final read-only preservation checks, cost-gap ledger and artifact inventory."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

started, before = time.perf_counter(), time.process_time()
run = Path(__file__).resolve().parent
repo = run.parents[1]
sys.path.insert(0, str(repo / "scripts"))
from segment_delta_data import save, sha
from segment_delta_study import read, verify

verify(run)
preserved = repo / "docs/research/toruk-custom-lm-architecture-decision-v1.md"
assert sha(preserved) == read(run/"preflight.json")["preserved_draft_sha256"]
def git(*args):
    return subprocess.check_output(["git",*args],cwd=repo,text=True).strip()
assert git("rev-parse","HEAD") == "ab6d3a65538b5f33d17efe4f45189906f1394a38"
assert not git("diff","--name-only") and not git("diff","--cached","--name-only")
code = [
    "src/toruk_lm/segment_delta.py", "src/toruk_lm/segment_delta_training.py",
    "scripts/segment_delta_data.py", "scripts/segment_delta_watch.py",
    "scripts/segment_delta_study.py", "scripts/verify_segment_delta_dev.py",
    "tests/test_segment_delta.py", "docs/research/toruk-custom-lm-architecture-decision-v2.md",
    "docs/research/segment-delta-dev-v1-protocol.md", "docs/research/segment-delta-dev-v1-results.md",
]
for name in code:
    for number,line in enumerate((repo/name).read_text(encoding="utf-8").splitlines(),1):
        assert line.rstrip() == line, f"trailing whitespace {name}:{number}"
        assert not line.startswith(("<<<<<<< ","=======",">>>>>>> ")), f"conflict marker {name}:{number}"
save(run/"final-git-state.json",dict(
    root=git("rev-parse","--show-toplevel"),branch=git("branch","--show-current"),
    head=git("rev-parse","HEAD"),status=git("status","-sb").splitlines(),
    tracked_diff=git("diff","--stat"),staged_diff=git("diff","--cached","--stat"),
    preserved_draft_sha256=sha(preserved),new_files_whitespace="PASS",committed=False,
))
verification = repo/"artifacts/segment-delta-dev-v1-verification-001"
checks = {p.stem:read(p)["status"] for p in verification.glob("*.json") if p.name!="coverage.json"}
assert all(value=="PASS" for value in checks.values())
measured = {"registered_study":read(run/"run-cost.json"),
            "rehearsal002":read(run/"rehearsal-002/cost.json"),
            "poststudy_audit":read(run/"poststudy-audit-cost/cost.json"),
            "scoped_verification":read(repo/"artifacts/segment-delta-dev-v1-verification-cost-001/cost.json")}
save(run/"cost-ledger.json",dict(
    measured_scopes={name:{key:r[key] for key in ("cpu","wall")} for name,r in measured.items()},
    known_disjoint_process_scope_cpu=sum(r["cpu"] for r in measured.values()),
    failed_rehearsal_lower_bound=read(run/"poststudy-audit.json")["failed_rehearsal_lower_bound"],
    unknown_costs=["early inspection/paper search/editing", "failed rehearsal final controller tail",
                   "data generation and early format/type commands outside monitors",
                   "research CLI help and wheel-membership check CPU", "final report/inventory work"],
    full_project_cpu="UNKNOWN, not zero",full_project_elapsed_wall="UNKNOWN; some post-study scopes overlap",
    supplemental_checks={name:read(verification/f"{name}.json")["seconds"] for name in ("research-cli-help","wheel-prototype-members")},
    local_check_statuses=checks,hosted_ci="NOT RUN",
    handoff_self_cost_before_inventory=dict(wall=time.perf_counter()-started,cpu=time.process_time()-before),
))
paths = [repo/name for name in code]
directories = [run,verification,repo/"artifacts/segment-delta-dev-v1-verification-cost-001"]
paths += [p for directory in directories for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
inventory = {p.relative_to(repo).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(paths))}
save(run/"artifact-inventory.json",dict(
    excludes=["this inventory itself", "generated __pycache__"],
    files=inventory,total_bytes=sum(r["bytes"] for r in inventory.values()),
    files_count=len(inventory),historical_sources_edited=False,
))
print(json.dumps(dict(status="PASS",files=len(inventory),checks=checks,
                     known_measured_cpu=sum(r["cpu"] for r in measured.values()))))
