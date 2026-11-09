"""General C-drive engineering checks, isolated from the completed model comparison."""

import ctypes
import json
import subprocess
import sys
import time
from pathlib import Path

out = Path(__file__).resolve().parent
started = time.perf_counter()
acquired = ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
code = None
try:
    if not acquired:
        raise RuntimeError("engineering verification power request unavailable")
    code = subprocess.run([sys.executable, "-B", "-X", "utf8", "scripts/verify.py",
                           "--prefix", "qwen-v3", "--output-dir", str(out / "verification")]).returncode
finally:
    restored = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    with (out / "verify-command.json").open("x", encoding="utf-8") as stream:
        json.dump({"returncode": code, "wall_seconds": time.perf_counter()-started,
                   "power_acquired": bool(acquired), "power_restored": bool(restored),
                   "scope": "C-drive existing engineering tests/smokes; no v3 model or Qwen heldout inference"}, stream, indent=2)
sys.exit(code if code is not None else 1)
