"""Real Windows process accounting, including abrupt exit and descendant cleanup."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lifetime_job import watch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mode,exit_code", [("success", 0), ("failure", 7), ("interrupt", 130)])
def test_controller_always_records_and_kernel_closes_lifetime(tmp_path, mode, exit_code):
    directory = tmp_path / mode
    code = (
        "import sys; from pathlib import Path; sys.path.insert(0,'scripts'); "
        "from lifetime_job import controller_record\n"
        f"with controller_record(Path({str(directory)!r})):\n"
        + (
            " print('success')\n"
            if mode == "success"
            else " raise SystemExit(7)\n"
            if mode == "failure"
            else " raise KeyboardInterrupt()\n"
        )
    )
    result = watch([sys.executable, "-B", "-c", code], directory, tmp_path, 5)
    assert result["complete_process_lifetimes"] and result["active_processes"] == 0
    assert result["returncode"] == exit_code or (
        mode == "interrupt" and result["returncode"] == 0xC000013A
    )
    assert result["status"] == ("PASS" if mode == "success" else "STOP")
    final = json.loads((directory / "controller-final.json").read_text())
    assert final["status"] == ("PASS" if mode == "success" else "STOP")
    assert result["cpu"] >= final["cpu_to_receipt"]


def test_abrupt_exit_without_self_receipt_is_completely_accounted(tmp_path):
    result = watch(
        [sys.executable, "-B", "-c", "import os; os._exit(9)"], tmp_path / "abrupt", tmp_path, 5
    )
    assert result["returncode"] == 9 and result["status"] == "STOP"
    assert result["complete_process_lifetimes"] and result["active_processes"] == 0
    assert not (tmp_path / "abrupt/controller-final.json").exists()


@pytest.mark.parametrize("interrupt", [False, True])
def test_cap_and_observer_interruption_drain_entire_tree(tmp_path, interrupt):
    code = (
        "import subprocess,sys,time; "
        "subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)']); time.sleep(10)"
    )
    result = watch(
        [sys.executable, "-B", "-c", code],
        tmp_path / ("cancel" if interrupt else "cap"),
        tmp_path,
        5 if interrupt else 0.25,
        interrupt_after=0.25 if interrupt else None,
    )
    assert result["status"] == "STOP" and result["complete_process_lifetimes"]
    assert result["active_processes"] == 0 and result["total_processes"] >= 2
    assert result["failure"] == ("observer interrupted" if interrupt else "CPU/wall cap")


def test_descendant_outlives_parent_and_lifetime_cpu_exceeds_coarse_samples(tmp_path):
    leaf = "import time; t=time.process_time();\nwhile time.process_time()-t<0.2: pass"
    code = f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{leaf!r}])"
    result = watch(
        [sys.executable, "-B", "-c", code], tmp_path / "descendant", tmp_path, 5, poll=0.4
    )
    assert result["status"] == "PASS" and result["complete_process_lifetimes"]
    assert result["active_processes"] == 0 and result["total_processes"] >= 2
    assert result["cpu"] >= 0.18
    assert result["cpu"] == result["user_cpu"] + result["kernel_cpu"]
