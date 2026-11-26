"""Read-only evidence/link checks plus a disposable Git index whitespace check."""

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from prepare_fresh_clone import FILES, ROOT

BASE = Path(__file__).resolve().parent
REPORT = ROOT / "docs/research/ci-contract-repair-45439669299.md"


def main():
    def git(*args, **kwargs):
        return subprocess.check_output(["git", *args], cwd=ROOT, **kwargs).decode().strip()

    packet = json.loads((BASE / "ci-commit.json").read_text())
    for name, expected in packet["files"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        assert git("hash-object", "--path", name, name) == git(
            "rev-parse", packet["commit"] + ":" + name), name
    assert git("rev-parse", "HEAD") == packet["parent"]
    assert git("branch", "--show-current") == "main"
    assert git("rev-list", "--left-right", "--count", "HEAD...origin/main") == "0\t0"
    assert not git("diff", "--cached", "--name-only")
    assert set(git("diff", "--name-only").splitlines()) == {
        ".github/workflows/ci.yml", "scripts/audit_qwen_development_v4.py"}
    links = re.findall(r"\]\(([^)]+)\)", REPORT.read_text(encoding="utf-8"))
    local = [link for link in links if not link.startswith("https://")]
    for link in local:
        path = (REPORT.parent / link).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(), link
    run = json.loads((BASE / "hosted-run-final.json").read_text())
    jobs = json.loads((BASE / "hosted-jobs-final.json").read_text())["jobs"]
    assert run["conclusion"] == "success" and run["head_sha"] == packet["commit"]
    assert len(jobs) == 3 and all(j["conclusion"] == "success" for j in jobs)
    assert all(s["conclusion"] == "success" for j in jobs for s in j["steps"])
    index = ROOT / ".git" / "ci-contract-delivery-45439669299.index"
    assert not index.exists()
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    git("read-tree", "HEAD", env=env)
    git("add", "--", *FILES, REPORT.relative_to(ROOT).as_posix(), env=env)
    git("diff", "--cached", "--check", env=env)
    git("diff", "--check")
    git("diff", "--cached", "--check")
    receipt = dict(
        status="PASS", head=packet["parent"], branch="main",
        main_ahead=0, main_behind=0, real_index_empty=True,
        scoped_ci_commit=packet["commit"], temporary_branch=packet["branch"],
        packet_files_verified=len(FILES), local_report_links_verified=len(local),
        hosted_run=run["id"], hosted_matrix="SUCCESS",
        working_diff_check="PASS", cached_diff_check="PASS",
        isolated_source_and_report_diff_check="PASS",
        historical_tracked_changes=[],
        status_porcelain=git("status", "--short").splitlines(),
        raw_logs_whitespace_preserved=True, second_push_performed=False,
    )
    with (BASE / "delivery-verification.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
