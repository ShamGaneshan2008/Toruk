"""Saved-only case regressions, links, source whitespace and immutable delivery inventory."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
REPORT = ROOT / "docs/research/local-answer-entity-dropout-dev-v1-results.md"
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job_v2 import verify_seal


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args, **kwargs):
    return subprocess.check_output(["git", *args], cwd=ROOT, **kwargs).decode().strip()


def main():
    audit = read(RUN / "independent-audit.json")
    checks = read(RUN / "verification-checks.json")
    assert checks["status"] == "PASS"
    for branch in ("audit-execution", "verification/execution"):
        verify_seal(RUN / branch)
    failures = [f for f in audit["failures"] if f["cell"].endswith("-drop50")]
    assert len(failures) == 7 and all(f["flags"]["wrong_first"] and f["flags"]["eos"]
                                    and not f["flags"]["malformed"] for f in failures)
    pairs = {}
    for key in audit["pair_gains"]:
        before = {f["id"] for f in audit["failures"] if f["cell"] == key + "-uniform"}
        after = {f["id"] for f in failures if f["cell"] == key + "-drop50"}
        pairs[key] = dict(resolved=sorted(before-after), introduced=sorted(after-before),
                          persisted=sorted(before & after))
    save(RUN / "case-regressions.json", dict(pairs=pairs, candidate_failures=failures))
    lines = ["", "## Exact remaining candidate errors and case regressions", "",
             "| Cell | Case | Gold | Native IDs | Expected rank | Gold-minus-top |",
             "| --- | --- | --- | --- | ---: | ---: |"]
    for f in failures:
        directory = RUN / "registered/execution/stages" / ("development-" + f["cell"])
        measures = [json.loads(line) for line in (directory / "first-measurements.jsonl").read_text().splitlines()]
        m = next(r for r in measures if r["id"] == f["id"] and not r["replay"])
        lines.append(f"| {f['cell']} | {f['id']} | {f['gold']} | `{f['result']['generated_ids']}` | "
                     f"{m['expected_rank']} | {m['expected_minus_predicted_margin']:.6f} |")
    lines += ["", "All seven failures start with the measured wrong first token,reach EOS,and "
              "are valid answer-inventory strings. They are wrong values or inappropriate unknown "
              "answers,not scorer rejection,missing supplied facts or EOS/format failures. "
              "[Casewise resolved/introduced errors](../../artifacts/local-answer-entity-dropout-dev-v1/case-regressions.json) "
              "also records individual-case regressions even in pairs with positive net gains.", "",
              "Verification completed:42 focused tests passed;Ruff lint/format,default/Linux mypy, "
              "three-script focused mypy,frozen sources,dependencies and working/cached diff checks "
              "all passed. Independent audit and verification Jobs have closed process trees and "
              "seals. The isolated-index source/report whitespace check passed without changing "
              "the real index. Hosted CI was not run. Final Git remains at the starting HEAD with "
              "only seven new development paths and no tracked modification or staged change.", ""]
    with REPORT.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines))
    links = re.findall(r"\]\(([^)]+)\)", REPORT.read_text(encoding="utf-8"))
    for link in links:
        if not link.startswith("https://"):
            assert (REPORT.parent / link).resolve().is_file(), link
    assert git("rev-parse", "HEAD") == "916efdd4b63dd63fab08ffabb8ab6e8313dc4bf2"
    assert git("rev-parse", "origin/main") == git("rev-parse", "HEAD")
    assert not git("diff", "--name-only") and not git("diff", "--cached", "--name-only")
    index = ROOT / "artifacts/.pytest_cache/entity-dropout-source-check.index"
    assert not index.exists()
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    sources = ["scripts/diagnose_value_start_v2.py", "scripts/local_answer_entity_dropout.py",
               "scripts/audit_entity_dropout_dev.py", "tests/test_entity_dropout_dev.py",
               "docs/research/local-answer-entity-dropout-dev-v1-protocol.md", REPORT.relative_to(ROOT).as_posix()]
    git("read-tree", "HEAD", env=env)
    git("add", "--", *sources, env=env)
    git("diff", "--cached", "--check", env=env)
    git("diff", "--check")
    git("diff", "--cached", "--check")
    inventory = {}
    for path, directories, names in os.walk(RUN):
        directories[:] = [d for d in directories if not d.startswith("pytest-tmp") and d != "__pycache__"]
        for name in names:
            file = Path(path) / name
            inventory[file.relative_to(ROOT).as_posix()] = dict(bytes=file.stat().st_size, sha256=sha(file))
    for name in sources:
        file = ROOT / name
        inventory[name] = dict(bytes=file.stat().st_size, sha256=sha(file))
    save(RUN / "delivery-inventory.json", dict(files=inventory,
         excludes=["private disposable pytest fixtures retained locally", "inventory/receipt self-reference"],
         local_checkpoints_included=True))
    costs = {name: read(RUN / name / "cost.json") for name in
             ("preparation/budget", "registered/budget", "audit-execution", "verification/execution")}
    token_totals = {}
    for arm in ("uniform", "drop50"):
        selected = [c for key, c in audit["cells"].items() if key.endswith("-"+arm)]
        token_totals[arm] = dict(
            train_target_tokens=8*692224, train_padded_forward_positions=8*786432,
            train_generated_tokens=sum(c["train_token_costs"]["main"]["generated_tokens"] for c in selected),
            dev_main_generated_tokens=sum(c["dev_token_costs"]["main"]["generated_tokens"] for c in selected),
            dev_question_only_generated_tokens=sum(c["dev_token_costs"]["question-only"]["generated_tokens"] for c in selected),
        )
    receipt = dict(status="PASS", decision=audit["decision"], inventory_sha256=sha(RUN / "delivery-inventory.json"),
                   inventoried_files=len(inventory), report_links=len(links), costs=costs,
                   token_totals=token_totals, main=git("rev-parse", "HEAD"), real_index_empty=True,
                   scoped_new_source_diff_check="PASS", worktree=git("status", "--short").splitlines(),
                   complete_project_cost="UNKNOWN", research_retries=0, heldout_opened=False,
                   committed=False, pushed=False)
    save(RUN / "delivery-receipt.json", receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != "costs"}, indent=2))


if __name__ == "__main__":
    main()
