"""Keep frozen study tests byte-identical; declare their actual execution contracts."""

import json
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ci_contracts import missing_probe_checkpoints, runtime_identity  # noqa: E402

PORTABLE_SEAL_TESTS = {
    "test_missing_final_receipt_retains_failure_marker_and_partial_output",
    "test_unclosed_final_receipt_cannot_be_sealed",
}


def pytest_configure(config):
    # The production sealer confines outputs to its checkout. Never weaken that guard.
    # A new owned path also avoids deleting any existing study output via --basetemp.
    if config.option.basetemp is None:
        parent = ROOT / "artifacts" / ".pytest_cache"
        if not parent.resolve().is_relative_to(ROOT):
            raise pytest.UsageError("test temporary output must remain inside this checkout")
        parent.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(parent / ("contract-" + uuid.uuid4().hex))


def pytest_collection_modifyitems(items):
    missing = None
    archival_runtime = None
    for item in items:
        filename = item.path.name
        name = item.originalname or item.name
        windows_only = (
            filename == "test_lifetime_job.py"
            or filename == "test_lifetime_job_v2.py"
            and name not in PORTABLE_SEAL_TESTS
            or filename == "test_qwen_long_history_v2.py"
            and name == "test_rehearsal_stops_on_first_failure_and_restores_power"
        )
        if windows_only and sys.platform != "win32":
            item.add_marker(
                pytest.mark.skip(
                    reason="Native Windows Job/ctypes.windll contract; exercised by Windows CI"
                )
            )
        if (
            filename == "test_first_byte_probe.py"
            and name == "test_exact_saved_inputs_and_260_record_plan"
        ):
            if missing is None:
                missing = missing_probe_checkpoints()
            if missing:
                item.add_marker(
                    pytest.mark.skip(
                        reason="Optional local research weights missing: "
                        + ", ".join(missing)
                        + "; use scripts/check_local_research_checkpoints.py. "
                        "Portable data/plan checks run separately."
                    )
                )
        if (
            filename == "test_paired_batch_dev.py"
            and name == "test_fixed_models_initialize_to_original_hashes_without_updates"
        ):
            if archival_runtime is None:
                archival_runtime = json.loads(
                    (ROOT / "artifacts/local-answer-dev-v1/registration.json").read_text()
                )["runtime"]
            current = runtime_identity()
            if current != archival_runtime:
                item.add_marker(
                    pytest.mark.skip(
                        reason="Exact archived initialization requires its frozen runtime; current="
                        + json.dumps(current, sort_keys=True)
                        + "; same-runtime determinism is tested separately. "
                        "Recorded expected hashes are unchanged."
                    )
                )
