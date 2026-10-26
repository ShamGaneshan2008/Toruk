"""Local Windows inference footprint; this does not emulate Vercel Linux cold starts."""

import ctypes
import json
import os
import sys
import time
from pathlib import Path


def package_bytes(path):
    if path.is_file():
        return path.stat().st_size
    return sum((Path(root) / name).stat().st_size for root, _, names in os.walk(path) for name in names)


class ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def memory():
    result = ProcessMemoryCounters()
    result.cb = ctypes.sizeof(result)
    current_process = ctypes.windll.kernel32.GetCurrentProcess
    current_process.restype = ctypes.c_void_p
    process_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    process_memory.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong)
    process_memory.restype = ctypes.c_int
    handle = current_process()
    if not process_memory(handle, ctypes.byref(result), result.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return result.PeakWorkingSetSize, result.WorkingSetSize, result.PrivateUsage


started = time.perf_counter()
import torch

from toruk_lm.engine import load_model, setup
from toruk_lm.model import generate
from toruk_lm.tokenizer import ByteTokenizer

import_seconds = time.perf_counter() - started
root = Path(__file__).resolve().parents[2]
checkpoint = root / "artifacts/minimal-lm-demo-001/train/checkpoint.pt"
setup(23, 1)
loading = time.perf_counter()
model = load_model(checkpoint)
load_seconds = time.perf_counter() - loading
tokenizer = ByteTokenizer()
prefix = [tokenizer.bos_id, *tokenizer.encode("User: Hello\nToruk:")]
latencies = []
outputs = []
for _ in range(3):
    t0 = time.perf_counter()
    ids = generate(model, prefix, 16)
    latencies.append(time.perf_counter() - t0)
    outputs.append(tokenizer.decode(ids))
site = Path(torch.__file__).parents[1]
sizes = {
    name: package_bytes(site / name)
    for name in ("torch", "sympy", "networkx", "jinja2", "fsspec", "filelock")
}
peak, current, private = memory()
result = {
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "checkpoint_bytes": checkpoint.stat().st_size,
    "checkpoint_format": "toruk-ordinary-v1",
    "model_parameters": sum(p.numel() for p in model.parameters()),
    "package_bytes": sizes,
    "package_total_bytes": sum(sizes.values()),
    "import_seconds": import_seconds,
    "checkpoint_load_seconds": load_seconds,
    "generation_seconds_each": latencies,
    "generated_text_each": outputs,
    "generated_tokens_each": [len(tokenizer.encode(text)) for text in outputs],
    "peak_working_set_bytes": peak,
    "working_set_bytes": current,
    "private_bytes": private,
    "process_seconds_after_start": time.perf_counter() - started,
    "note": "Windows process measurement; excludes Vercel upload, build, Linux boot and network.",
}
target = Path(__file__).with_name("metrics.json")
target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
