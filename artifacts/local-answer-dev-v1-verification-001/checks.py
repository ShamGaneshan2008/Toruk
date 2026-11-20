"""Explicit offline verification; all child lifetimes are Job-accounted."""

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"scripts"))
from lifetime_job import controller_record, watch

PY=sys.executable
TESTS=[
    "tests/test_lifetime_job.py","tests/test_local_answer_dev.py","tests/test_answer_trainability_dev.py",
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
COMMANDS={
    "local-saved-audit":[PY,"-B","artifacts/local-answer-dev-v1/verify_saved.py"],
    "frozen-local-audit":[PY,"-B","scripts/local_answer_dev.py","audit"],
    "v1-committed-record":[PY,"-B","artifacts/answer-trainability-dev-v1-commit-review-001/review.py","--revision","301dd9edbf12403aa97e5013247d5b1f33be0746"],
    "segment-delta-record":[PY,"-B","artifacts/segment-delta-dev-v1-commit-review-001/review.py","--revision","39c4e4756b24ca3d09c4a9aa8ae63b1a2b5ab208","--inspect-checkpoints"],
    "focused-tests":[PY,"-B","-m","pytest","-q",*TESTS,"-o",f"cache_dir={HERE/'pytest-cache'}","--basetemp",str(HERE/'pytest-tmp')],
    "lint":[PY,"-m","ruff","check","."],
    "format":[PY,"-m","ruff","format","--check","src","tests","scripts"],
    "types":[PY,"-m","mypy"],
    "types-linux":[PY,"-m","mypy","--platform","linux"],
    "frozen-sources":[PY,"-B","scripts/check_frozen_sources.py"],
    "diff-check":["git","diff","--check"],
}


def main():
    records={}
    with controller_record(HERE/"execution"):
        for label,command in COMMANDS.items():
            cost=watch(command,HERE/label,HERE,240,2*1024**3,128*1024**2)
            records[label]=cost
            print(json.dumps(dict(check=label,status=cost["status"],cpu=cost["cpu"],wall=cost["wall"],complete=cost["complete_process_lifetimes"])),flush=True)
        with (HERE/"coverage.json").open("x",encoding="utf-8",newline="\n") as stream:
            json.dump(dict(full_suite=False,selected_tests=TESTS,checks=records,
                      excluded="unfiltered verify/pytest, all study run commands, held-out loaders, live integrations",
                      study_training_or_generation_repeated=False),stream,indent=2,sort_keys=True);stream.write("\n")
    return 0 if all(c["status"]=="PASS" and c["complete_process_lifetimes"] for c in records.values()) else 1


if __name__=="__main__":raise SystemExit(main())
