"""Post-run checks only; preserve expected failures without changing registered evidence."""

import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lifetime_job import controller_record


def main():
    directory = RUN / "verification/execution"
    with controller_record(directory):
        py = sys.executable
        commands = [
            (
                "registered-auditor",
                [py, "-B", "scripts/paired_batch_dev.py", "audit"],
                1,
                "observation seal",
            ),
            (
                "independent-saved-observations",
                [
                    py,
                    "-I",
                    "-S",
                    "-B",
                    str(RUN / "verify_saved.py"),
                    "--output",
                    str(RUN / "independent-audit.json"),
                ],
                2,
                "OBSERVATIONS_VERIFIED_WITH_REGISTERED_SEAL_FAILURE",
            ),
            (
                "old-first-token-margins",
                [py, "-B", "scripts/audit_first_token_margins.py", "audit"],
                0,
                None,
            ),
            (
                "old-first-token-report",
                [py, "-B", "artifacts/local-answer-first-token-review-v1/verify_report.py"],
                0,
                None,
            ),
            ("frozen-sources", [py, "-B", "scripts/check_frozen_sources.py"], 0, None),
            (
                "preserved-handoff",
                [
                    py,
                    "-I",
                    "-S",
                    "-B",
                    "artifacts/checkpoint-handoff-v1-20261123/verify_handoff.py",
                    "verify",
                    "--bundle",
                    "artifacts/checkpoint-handoff-v1-20261123/toruk-checkpoints-v1.zip",
                    "--expected-sha256",
                    "b6e336cb004f3334a244101b6d3a102ccee3da6e3106fa447c565b2e6d731300",
                ],
                0,
                None,
            ),
            ("repository-lint", [py, "-B", "-m", "ruff", "check", "--no-cache", "."], 0, None),
            (
                "repository-format",
                [
                    py,
                    "-B",
                    "-m",
                    "ruff",
                    "format",
                    "--check",
                    "--no-cache",
                    "src",
                    "tests",
                    "scripts",
                ],
                0,
                None,
            ),
            ("dependencies", [py, "-B", "-m", "pip", "check"], 0, None),
            ("unstaged-diff-check", ["git", "diff", "--check"], 0, None),
            ("staged-diff-check", ["git", "diff", "--cached", "--check"], 0, None),
            (
                "older-portable-verifier",
                [py, "-B", "scripts/verify_portable_research_evidence.py", "verify"],
                1,
                "included file hash mismatch: .gitattributes",
            ),
        ]
        results = []
        for name, command, expected, needle in commands:
            p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
            with (directory / (name + ".stdout.log")).open(
                "x", encoding="utf-8", newline="\n"
            ) as f:
                f.write(p.stdout)
            with (directory / (name + ".stderr.log")).open(
                "x", encoding="utf-8", newline="\n"
            ) as f:
                f.write(p.stderr)
            match = p.returncode == expected and (needle is None or needle in p.stdout + p.stderr)
            item = dict(
                name=name,
                command=command,
                returncode=p.returncode,
                expected_returncode=expected,
                matched_expectation=match,
                classification="PASS"
                if expected == 0 and match
                else "EXPECTED_FAILURE_PRESERVED"
                if match
                else "UNEXPECTED_FAILURE",
            )
            results.append(item)
            print(json.dumps(item), flush=True)
            if not match:
                break
        report = dict(
            status="CHECKS_COMPLETE_WITH_REGISTERED_SEAL_FAILURE",
            registered_integrity_gate_passed=False,
            all_check_expectations_met=all(r["matched_expectation"] for r in results)
            and len(results) == len(commands),
            commands=results,
            new_model_forwards=0,
            new_generated_answers=0,
            prior_focused_tests="18 passed inside preparation/contracts; no new fitting tests",
            known_old_portable_failure=".gitattributes historical dependency drift",
            known_new_failure="twelve observation seals bind a prefix of a growing resources.jsonl",
        )
        with (RUN / "checks.json").open("x", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, indent=2)
            f.write("\n")
        if not report["all_check_expectations_met"]:
            raise RuntimeError("post-run checks found an unexpected failure")


if __name__ == "__main__":
    main()
