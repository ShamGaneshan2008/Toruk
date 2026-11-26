"""Real portable file-sealing tests using explicitly synthetic receipt inputs.

These check schema/hash/publication behavior, never claim measured OS lifetimes.
"""

import json

import lifetime_job_v2 as sealing
import pytest


def synthetic_receipt(directory, status="PASS"):
    directory.mkdir()
    (directory / "payload.txt").write_text("test payload")
    (directory / "cost.json").write_text(
        json.dumps(
            dict(
                accounting_scope="SYNTHETIC unit-test schema input; NOT kernel measurements",
                complete_process_lifetimes=True,
                active_processes=0,
                returncode=0 if status == "PASS" else 7,
                status=status,
                cpu=3,
                user_cpu=2,
                kernel_cpu=1,
            )
        )
    )


@pytest.mark.parametrize("status", ["PASS", "STOP"])
def test_portable_closed_receipt_seal_preserves_workload_status(tmp_path, status):
    directory = tmp_path / "synthetic"
    synthetic_receipt(directory, status)
    seal = sealing.seal_closed_run(directory)
    result = sealing.verify_seal(directory, expected_seal_sha256=sealing._digest(seal))
    assert result["workload_status"] == status
    assert set(result["files"]) == {"cost.json", "payload.txt"}
    with pytest.raises(sealing.SealError, match="seal already exists"):
        sealing.seal_closed_run(directory)


@pytest.mark.parametrize("mutation", ["payload", "receipt", "added", "removed", "seal"])
def test_portable_seal_detects_mutation(tmp_path, mutation):
    directory = tmp_path / "synthetic"
    synthetic_receipt(directory)
    seal = sealing.seal_closed_run(directory)
    digest = sealing._digest(seal)
    path = directory / ("payload.txt" if mutation in ("payload", "removed") else "cost.json")
    if mutation == "removed":
        path.unlink()  # Disposable file owned solely by this test.
    elif mutation == "added":
        (directory / "added.txt").write_text("new")
    else:
        with (seal if mutation == "seal" else path).open("a") as stream:
            stream.write("\n")
    with pytest.raises(sealing.SealError):
        sealing.verify_seal(directory, expected_seal_sha256=digest)


def test_portable_guard_still_rejects_other_checkout():
    outside = sealing.ROOT.parent / "__not_a_toruk_test_checkout__"
    with pytest.raises(sealing.SealError, match="inside the checkout"):
        sealing.seal_closed_run(outside)
