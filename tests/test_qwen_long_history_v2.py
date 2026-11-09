"""No-model contracts for interruption handling, bounds, and the held-out boundary."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "qwen_v2_contract", ROOT / "scripts/qwen_long_history_v2.py"
)
assert spec and spec.loader
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)


@pytest.mark.skipif(v2.os.name != "nt", reason="Windows awake-time clock")
def test_live_clock_exports_and_monotonicity():
    start, end = v2.clocks(), v2.clocks()
    assert start["awake_seconds"] > 0
    assert all(end[k] >= start[k] for k in start)


def test_sleep_is_invalid_and_never_subtracted():
    config = {"max_monitor_gap_seconds": 5, "max_suspended_gap_seconds": 2}
    start = {"utc_seconds": 0, "perf_seconds": 0, "awake_seconds": 0}
    now = {"utc_seconds": 1255, "perf_seconds": 1255, "awake_seconds": 5}
    assert v2.elapsed(start, now) == 1255
    assert "interruption" in v2.interruption(start, start, now, config)
    previous = {"utc_seconds": 1254, "perf_seconds": 1254, "awake_seconds": 4}
    assert "suspension" in v2.interruption(start, previous, now, config)


def test_clock_reversal_blocks():
    c = {"max_monitor_gap_seconds": 5, "max_suspended_gap_seconds": 2}
    start = {"utc_seconds": 10, "perf_seconds": 10, "awake_seconds": 10}
    assert v2.interruption(start, start, {**start, "utc_seconds": 9}, c)


def test_limits_use_worst_request_and_conservative_rounding():
    result = v2.propose_limits(
        {"wall_seconds": 56.5, "cpu_seconds": 120},
        [
            {"request_wall_seconds": 7, "request_cpu_seconds": 14},
            {"request_wall_seconds": 1, "request_cpu_seconds": 2},
        ],
    )
    assert result["wall_seconds"] == 420
    assert result["cpu_seconds"] == 840
    with pytest.raises(ValueError, match="ceiling"):
        v2.propose_limits(
            {"wall_seconds": 180, "cpu_seconds": 360},
            [{"request_wall_seconds": 30, "request_cpu_seconds": 60}],
        )


def test_output_guard_rejects_other_checkout():
    with pytest.raises(ValueError, match="namespace"):
        v2.paths_under(Path("D:/Toruk/artifacts/qwen-long-history-v1"))


def test_exclusive_records_and_identity_drift(tmp_path):
    target = tmp_path / "evidence.json"
    v2.write(target, {"status": "BLOCKED"})
    with pytest.raises(FileExistsError):
        v2.write(target, {"status": "PASS"})
    digest = v2.sha(target)
    v2.verify_bindings({str(target): digest})
    target.write_text("drift")
    with pytest.raises(ValueError, match="drift"):
        v2.verify_bindings({str(target): digest})


def test_only_progress_reads_retry_and_charge_delay(tmp_path, monkeypatch):
    target = tmp_path / "progress.json"
    target.write_text("{}")
    calls = []

    def contested(path):
        calls.append(path)
        if len(calls) < 3:
            raise PermissionError("contention")
        return {"active": True}

    sleeps = []
    monkeypatch.setattr(v2, "read", contested)
    monkeypatch.setattr(v2.time, "sleep", sleeps.append)
    assert v2.progress(
        target,
        tmp_path / "retries.jsonl",
        {"monitor_read_attempts": 5, "monitor_read_delay_seconds": 0.01},
    ) == {"active": True}
    assert sleeps == [0.01, 0.01]
    assert len((tmp_path / "retries.jsonl").read_text().splitlines()) == 2


def test_no_heldout_command_and_no_generation_retry(monkeypatch):
    config = json.loads((ROOT / "configs/qwen-long-history-v2.json").read_text())
    monkeypatch.setattr(v2.sys, "argv", ["qwen_long_history_v2.py", "heldout", "--run", "x"])
    with pytest.raises(SystemExit) as error:
        v2.main()
    assert error.value.code == 2
    assert config["heldout_authorized"] is False
    assert config["generation_retries"] == 0


def test_rehearsal_stops_on_first_failure_and_restores_power(tmp_path, monkeypatch):
    v2.write(
        tmp_path / "rehearsal/registration.json",
        {"bindings": {}, "v2_config": {"rehearsal_order": ["full", "toruk"]}},
    )
    power_calls, stage_calls = [], []

    def power(flags):
        power_calls.append(flags)
        return 1

    def failed_stage(run, arm, totals):
        stage_calls.append(arm)
        return {"wall_seconds": 180, "cpu_seconds": 12, "failure": "interruption"}

    monkeypatch.setattr(
        v2.ctypes,
        "windll",
        SimpleNamespace(kernel32=SimpleNamespace(SetThreadExecutionState=power)),
    )
    monkeypatch.setattr(
        v2, "clocks", lambda: {"utc_seconds": 1, "perf_seconds": 1, "awake_seconds": 1}
    )
    monkeypatch.setattr(v2, "stage", failed_stage)
    v2.rehearse(tmp_path)
    assert stage_calls == ["full"]
    assert power_calls == [0x80000001, 0x80000000]
    record = json.loads((tmp_path / "rehearsal-cost.json").read_text())
    assert record["complete"] is False
    assert record["heldout_completed"] == 0
    assert record["totals"]["wall_seconds"] == 180
