"""Explicit offline check scope; no held-out loaders or experiment run commands."""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from segment_delta_watch import worker_receipt

STARTED = time.perf_counter()
PYTHON = sys.executable
TESTS = [
    "tests/test_answer_trainability_dev.py",
    "tests/test_foundation.py::test_tokenizer_round_trip",
    "tests/test_foundation.py::test_future_tokens_cannot_change_earlier_logits",
    "tests/test_foundation.py::test_padding_and_batch_isolation",
    "tests/test_foundation.py::test_shift_and_boundary_targets_once",
    "tests/test_foundation.py::test_valid_token_loss_and_gradients",
    "tests/test_recurrent.py::test_causality_write_timing_and_later_writer_gradients",
    "tests/test_recurrent.py::test_padding_lane_isolation_and_fixed_capacity",
    "tests/test_recurrent.py::test_session_commit_parity_reset_clone_and_independence",
    "tests/test_segment_delta.py::test_shapes_counts_state_and_old_recurrent_algebra",
    "tests/test_segment_delta.py::test_causal_logits_padding_and_entering_state_immutable",
    "tests/test_segment_delta.py::test_exact_same_key_correction_and_orthogonal_preservation",
    "tests/test_segment_delta.py::test_future_loss_gradients_cross_segment_and_actual_ablations",
]
COMMANDS = {
    "frozen-study-audit": [PYTHON, "-B", "scripts/answer_trainability_dev.py", "audit"],
    "independent-evidence-audit": [PYTHON, "-B", "artifacts/answer-trainability-dev-v1/poststudy-audit.py"],
    "legacy-evidence": [PYTHON, "-B", "artifacts/segment-delta-dev-v1-commit-review-001/review.py", "--revision", "HEAD", "--inspect-checkpoints"],
    "focused-tests": [PYTHON, "-B", "-m", "pytest", "-q", *TESTS, "-o", f"cache_dir={DIRECTORY/'pytest-cache'}", "--basetemp", str(DIRECTORY/'pytest-tmp')],
    "lint": [PYTHON, "-m", "ruff", "check", "."],
    "format": [PYTHON, "-m", "ruff", "format", "--check", "src", "tests", "scripts"],
    "types": [PYTHON, "-m", "mypy"],
    "types-linux": [PYTHON, "-m", "mypy", "--platform", "linux"],
    "frozen-sources": [PYTHON, "-B", "scripts/check_frozen_sources.py"],
    "diff-check": ["git", "diff", "--check"],
}


def main():
    receipts = {}
    try:
        for label, command in COMMANDS.items():
            began = time.perf_counter()
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=90)
            with (DIRECTORY/f"{label}.log").open("xb") as stream:
                stream.write(completed.stdout + completed.stderr)
            receipt = dict(command=command, returncode=completed.returncode,
                           wall=time.perf_counter()-began,
                           status="PASS" if completed.returncode == 0 else "FAIL")
            receipts[label] = receipt
            with (DIRECTORY/f"{label}.json").open("x",encoding="utf-8") as stream:
                json.dump(receipt,stream,indent=2,sort_keys=True)
                stream.write("\n")
            print(json.dumps(dict(label=label,**receipt)),flush=True)
        with (DIRECTORY/"coverage.json").open("x",encoding="utf-8") as stream:
            json.dump(dict(full_suite=False,selected_tests=TESTS,checks=receipts,
                      excluded="unfiltered pytest/verify, old study runners, held-out loaders, live integrations",
                      no_study_training_or_generation=True),stream,indent=2,sort_keys=True)
            stream.write("\n")
        return 0 if all(r["returncode"] == 0 for r in receipts.values()) else 1
    finally:
        worker_receipt(DIRECTORY,STARTED,0.0)


if __name__ == "__main__":
    sys.exit(main())
