"""Windows Job accounting: retain kernel lifetime totals after every descendant exits.

The job contains the workload/controller and all descendants, not this measurement
observer. No worker-final JSON is required. Observer CPU is a separate snapshot.
"""

import argparse
import ctypes
import json
import os
import subprocess
import time
from contextlib import contextmanager
from ctypes import wintypes as W
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BasicLimit(ctypes.Structure):
    _fields_ = [
        ("ProcessTime", ctypes.c_longlong),
        ("JobTime", ctypes.c_longlong),
        ("Flags", W.DWORD),
        ("MinWS", ctypes.c_size_t),
        ("MaxWS", ctypes.c_size_t),
        ("ActiveLimit", W.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("Priority", W.DWORD),
        ("Scheduling", W.DWORD),
    ]


class IOCounters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_ulonglong)
        for name in (
            "ReadOperations",
            "WriteOperations",
            "OtherOperations",
            "ReadBytes",
            "WriteBytes",
            "OtherBytes",
        )
    ]


class ExtendedLimit(ctypes.Structure):
    _fields_ = [
        ("Basic", BasicLimit),
        ("IO", IOCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemory", ctypes.c_size_t),
        ("PeakJobMemory", ctypes.c_size_t),
    ]


class Accounting(ctypes.Structure):
    _fields_ = [
        ("UserTime", ctypes.c_longlong),
        ("KernelTime", ctypes.c_longlong),
        ("ThisUser", ctypes.c_longlong),
        ("ThisKernel", ctypes.c_longlong),
        ("PageFaults", W.DWORD),
        ("TotalProcesses", W.DWORD),
        ("ActiveProcesses", W.DWORD),
        ("TerminatedProcesses", W.DWORD),
    ]


class Startup(ctypes.Structure):
    _fields_ = [
        ("cb", W.DWORD),
        ("reserved", W.LPWSTR),
        ("desktop", W.LPWSTR),
        ("title", W.LPWSTR),
        ("x", W.DWORD),
        ("y", W.DWORD),
        ("xsize", W.DWORD),
        ("ysize", W.DWORD),
        ("xchars", W.DWORD),
        ("ychars", W.DWORD),
        ("fill", W.DWORD),
        ("flags", W.DWORD),
        ("show", W.WORD),
        ("reserved_size", W.WORD),
        ("reserved_ptr", ctypes.c_void_p),
        ("stdin", W.HANDLE),
        ("stdout", W.HANDLE),
        ("stderr", W.HANDLE),
    ]


class ProcessInfo(ctypes.Structure):
    _fields_ = [("process", W.HANDLE), ("thread", W.HANDLE), ("pid", W.DWORD), ("tid", W.DWORD)]


def api():
    if os.name != "nt":
        raise RuntimeError("This accounting implementation requires Windows kernel Jobs")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateJobObjectW": ([ctypes.c_void_p, W.LPCWSTR], W.HANDLE),
        "SetInformationJobObject": ([W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD], W.BOOL),
        "QueryInformationJobObject": (
            [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD, ctypes.c_void_p],
            W.BOOL,
        ),
        "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
        "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
        "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
        "ResumeThread": ([W.HANDLE], W.DWORD),
        "CloseHandle": ([W.HANDLE], W.BOOL),
        "GetExitCodeProcess": ([W.HANDLE, ctypes.POINTER(W.DWORD)], W.BOOL),
        "CreateProcessW": (
            [
                W.LPCWSTR,
                W.LPWSTR,
                ctypes.c_void_p,
                ctypes.c_void_p,
                W.BOOL,
                W.DWORD,
                ctypes.c_void_p,
                W.LPCWSTR,
                ctypes.POINTER(Startup),
                ctypes.POINTER(ProcessInfo),
            ],
            W.BOOL,
        ),
    }
    for name, (args, returns) in signatures.items():
        function = getattr(kernel, name)
        function.argtypes = args
        function.restype = returns
    return kernel


def checked(value):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error())
    return value


def query(kernel, job, kind, structure):
    value = structure()
    checked(
        kernel.QueryInformationJobObject(job, kind, ctypes.byref(value), ctypes.sizeof(value), None)
    )
    return value


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def watch(
    command,
    directory,
    root,
    seconds,
    memory=2 * 1024**3,
    disk=128 * 1024**2,
    interrupt_after=None,
    poll=0.05,
):
    import msvcrt

    directory, root = Path(directory).resolve(), Path(root).resolve()
    if not directory.is_relative_to(ROOT) or not root.is_relative_to(ROOT):
        raise ValueError("All output and disk-accounting paths must stay in D:/Toruk")
    directory.mkdir(parents=True, exist_ok=False)
    kernel = api()
    started, observer_start = time.perf_counter(), time.process_time()
    job = checked(kernel.CreateJobObjectW(None, None))
    info = ProcessInfo()
    failure = error = None
    assigned = False
    peak_disk = max_gap = 0.0
    accounting = Accounting()
    limits = ExtendedLimit()
    limits.Basic.Flags = 0x2000 | 0x200  # KILL_ON_JOB_CLOSE | JOB_MEMORY
    limits.JobMemoryLimit = memory
    checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
    try:
        with (directory / "output.log").open("xb") as log, open(os.devnull, "rb") as null:
            os.set_inheritable(log.fileno(), True)
            os.set_inheritable(null.fileno(), True)
            startup = Startup()
            startup.cb = ctypes.sizeof(startup)
            startup.flags = 0x100
            startup.stdin = msvcrt.get_osfhandle(null.fileno())
            startup.stdout = startup.stderr = msvcrt.get_osfhandle(log.fileno())
            buffer = ctypes.create_unicode_buffer(
                subprocess.list2cmdline([str(x) for x in command])
            )
            checked(
                kernel.CreateProcessW(
                    None,
                    buffer,
                    None,
                    None,
                    True,
                    0x08000004,
                    None,
                    str(ROOT),
                    ctypes.byref(startup),
                    ctypes.byref(info),
                )
            )
            checked(kernel.AssignProcessToJobObject(job, info.process))
            assigned = True
            if kernel.ResumeThread(info.thread) == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            previous = started
            with (directory / "resources.jsonl").open("x", encoding="utf-8") as trace:
                while True:
                    accounting = query(kernel, job, 1, Accounting)
                    current = query(kernel, job, 9, ExtendedLimit)
                    now = time.perf_counter()
                    elapsed = now - started
                    gap = now - previous
                    max_gap = max(max_gap, gap)
                    previous = now
                    logical = sum(p.stat().st_size for p in root.rglob("*") if p.is_file())
                    peak_disk = max(peak_disk, logical)
                    cpu = (accounting.UserTime + accounting.KernelTime) / 10_000_000
                    trace.write(
                        json.dumps(
                            dict(
                                elapsed=elapsed,
                                gap=gap,
                                job_cpu=cpu,
                                active=accounting.ActiveProcesses,
                                total_processes=accounting.TotalProcesses,
                                peak_private=current.PeakJobMemory,
                                disk=logical,
                            )
                        )
                        + "\n"
                    )
                    trace.flush()
                    if accounting.ActiveProcesses == 0:
                        break
                    if interrupt_after is not None and elapsed >= interrupt_after:
                        raise KeyboardInterrupt("deterministic observer-interruption test")
                    if gap > 5:
                        failure = "monitor gap"
                    elif max(elapsed, cpu) > seconds:
                        failure = "CPU/wall cap"
                    elif logical > disk:
                        failure = "disk cap"
                    elif current.PeakJobMemory > memory:
                        failure = "job private-memory cap"
                    if failure:
                        break
                    time.sleep(poll)
    except KeyboardInterrupt as exception:
        failure = "observer interrupted"
        error = repr(exception)
    except BaseException as exception:
        failure = "observer or spawn error"
        error = repr(exception)
    finally:
        if assigned:
            accounting = query(kernel, job, 1, Accounting)
            if accounting.ActiveProcesses:
                checked(kernel.TerminateJobObject(job, 130))
            deadline = time.perf_counter() + 10
            while query(kernel, job, 1, Accounting).ActiveProcesses:
                if time.perf_counter() > deadline:
                    failure = "job failed to drain"
                    break
                time.sleep(0.01)
            accounting = query(kernel, job, 1, Accounting)
            limits = query(kernel, job, 9, ExtendedLimit)
        elif info.process:
            kernel.TerminateProcess(info.process, 130)
        exit_code = W.DWORD(259)
        if info.process:
            checked(kernel.GetExitCodeProcess(info.process, ctypes.byref(exit_code)))
        for handle in (info.thread, info.process, job):
            if handle:
                kernel.CloseHandle(handle)
    wall = time.perf_counter() - started
    cpu = (accounting.UserTime + accounting.KernelTime) / 10_000_000
    complete = assigned and accounting.ActiveProcesses == 0
    if complete and max(wall, cpu) > seconds:
        failure = failure or "final CPU/wall cap"
    if complete and limits.PeakJobMemory > memory:
        failure = failure or "final memory cap"
    result = dict(
        command=[str(x) for x in command],
        returncode=exit_code.value,
        failure=failure,
        error=error,
        status="PASS" if complete and exit_code.value == 0 and not failure else "STOP",
        complete_process_lifetimes=complete,
        cpu=cpu,
        user_cpu=accounting.UserTime / 10_000_000,
        kernel_cpu=accounting.KernelTime / 10_000_000,
        wall=wall,
        total_processes=accounting.TotalProcesses,
        active_processes=accounting.ActiveProcesses,
        terminated_processes=accounting.TerminatedProcesses,
        peak_private=limits.PeakJobMemory,
        peak_disk=int(peak_disk),
        max_monitor_gap=max_gap,
        root_pid=info.pid,
        observer_cpu_to_receipt=time.process_time() - observer_start,
        accounting_scope=(
            "kernel Job: complete workload/controller and descendants; observer outside job"
        ),
    )
    write(directory / "cost.json", result)
    return result


@contextmanager
def controller_record(directory):
    """Always retain controller status; authoritative lifetime CPU comes from its parent Job."""
    directory = Path(directory)
    began, cpu = time.perf_counter(), time.process_time()
    error = None
    try:
        yield
    except BaseException as exception:
        error = repr(exception)
        raise
    finally:
        write(
            directory / "controller-final.json",
            dict(
                pid=os.getpid(),
                status="STOP" if error else "PASS",
                error=error,
                cpu_to_receipt=time.process_time() - cpu,
                wall_to_receipt=time.perf_counter() - began,
                complete_lifetime_source="parent Windows Job after exit; self-report is diagnostic",
            ),
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seconds", type=float, required=True)
    parser.add_argument("--memory", type=int, default=2 * 1024**3)
    parser.add_argument("--disk", type=int, default=128 * 1024**2)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    result = watch(command, args.directory, args.root, args.seconds, args.memory, args.disk)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
