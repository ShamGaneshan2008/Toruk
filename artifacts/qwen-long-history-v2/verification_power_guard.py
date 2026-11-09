"""Temporary idle-sleep request for engineering verification, outside benchmark costs."""

import ctypes
import json
import time
from pathlib import Path

import psutil

started = time.time()
acquired = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
targets = []
for process in psutil.process_iter(["cmdline"]):
    if process.info["cmdline"] and "scripts/verify.py" in process.info["cmdline"]:
        targets.append(process)
try:
    if not acquired:
        raise RuntimeError("engineering verification power request failed")
    while any(p.is_running() for p in targets) and time.time() - started < 600:
        time.sleep(0.5)
finally:
    restored = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    record = {"acquired": bool(acquired), "restored": bool(restored),
              "target_pids": [p.pid for p in targets], "wall_seconds": time.time() - started,
              "scope": "Engineering verification only, after successful benchmark rehearsal; no global policy change"}
    with (Path(__file__).parent / "verification-power-guard.json").open("x") as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps(record))
