"""Publish the verified working copy with path/hash guards and online SQLite/source backups."""

import argparse
import hashlib
import json
import os
import socket
import shutil
import sqlite3
import subprocess
import time
import urllib.request
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

ARTIFACTS = Path(__file__).resolve().parent
STAGE = ARTIFACTS / "don-codino-v2"
TARGET = Path(r"C:\Users\susee\VScode Project\Don-Codino").resolve()
MANIFEST = ARTIFACTS / "don-codino-v2-publish-manifest.json"
DIRECTORIES = {"app", "tests", "docs", "scripts", "verification", ".github"}
ROOT_FILES = {"README.md", "AGENTS.md", "IMPLEMENTATION_STATUS.md", "MASTER_VALIDATION_REPORT.md",
              "pyproject.toml", ".env.example"}
HOST_PYTHON = TARGET / ".venv" / "Scripts" / "python.exe"


def expected_server():
    script = (
        "$listenerProcess = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 "
        "-State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess; "
        "if (-not $listenerProcess) { throw 'Expected local Don Codino server is not listening' }; "
        "$codinoProcess = Get-CimInstance Win32_Process -Filter \"ProcessId=$listenerProcess\"; "
        "if ($codinoProcess.CommandLine -notmatch [regex]::Escape('uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8765') "
        "-or $codinoProcess.CommandLine -notmatch [regex]::Escape('Don-Codino\\.venv\\Scripts\\python.exe')) "
        "{ throw 'Port 8765 belongs to an unexpected process; refusing to stop it' }; "
        "$codinoProcess | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                            capture_output=True, text=True, timeout=20, check=True)
    return json.loads(result.stdout)


def stop_expected_server(process):
    pid = int(process["ProcessId"])
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                    f"Stop-Process -Id {pid} -Force"], check=True, timeout=15)
    for _ in range(50):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", 8765))
                return
            except OSError:
                time.sleep(0.1)
    raise TimeoutError("Verified Don Codino server did not release port 8765")


def start_and_smoke(history_ids, repair_ids):
    logs = TARGET / "data"
    output = (logs / "server-v2.stdout.log").open("ab")
    errors = (logs / "server-v2.stderr.log").open("ab")
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS |
             subprocess.CREATE_NO_WINDOW)
    process = subprocess.Popen(
        [str(HOST_PYTHON), "-m", "uvicorn", "app.main:create_app", "--factory",
         "--host", "127.0.0.1", "--port", "8765"],
        cwd=TARGET, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
        creationflags=flags, env={key: value for key, value in os.environ.items()
                                 if key.upper() != "PYTHONPATH"},
    )
    output.close()
    errors.close()
    for _ in range(100):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=2) as response:
                health = json.load(response)
            break
        except OSError:
            if process.poll() is not None:
                raise RuntimeError("V2 server stopped during startup")
            time.sleep(0.2)
    else:
        raise TimeoutError("V2 server did not become healthy")
    if health != {"status": "ok", "application": "Don Codino"}:
        raise ValueError("V2 health response changed unexpectedly")
    with urllib.request.urlopen("http://127.0.0.1:8765/api/tasks?limit=100", timeout=5) as response:
        records = json.load(response)
    if [task["id"] for task in records] != history_ids:
        raise ValueError("Existing task history changed during the update")
    with urllib.request.urlopen("http://127.0.0.1:8765/api/v1/system/diagnostics", timeout=30) as response:
        diagnostic = json.load(response)
    if diagnostic["database"]["check"] != "ok" or diagnostic["codex"]["available"] is not True:
        raise ValueError("Post-update DB or Codex readiness failed")
    for route in ("/", "/static/app.js", "/openapi.json", "/api/workspaces"):
        with urllib.request.urlopen("http://127.0.0.1:8765" + route, timeout=5) as response:
            body = response.read()
            if response.status != 200:
                raise ValueError("Post-update route failed: " + route)
            if route == "/" and b"THE VAULT" not in body:
                raise ValueError("Updated dashboard did not load")
    for task_id in repair_ids:
        with urllib.request.urlopen(f"http://127.0.0.1:8765/api/v1/tasks/{task_id}/execution",
                                    timeout=5) as response:
            evidence = json.load(response)
        if evidence["attempts"] != 1 or [event["state"] for event in evidence["transitions"]][-1] != "VERIFIED":
            raise ValueError("Verified repair audit trail did not survive restart")
    return {"pid": process.pid, "health": health, "history_count": len(records),
            "history_ids": history_ids, "paths_http_200": True,
            "codex": diagnostic["codex"], "database": diagnostic["database"],
            "repair_task_ids": repair_ids, "logs": ["data/server-v2.stdout.log",
                                                       "data/server-v2.stderr.log"]}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def paths():
    for path in STAGE.rglob("*"):
        relative = path.relative_to(STAGE)
        if "__pycache__" in relative.parts or path.is_symlink() or not path.is_file():
            continue
        if relative.parts[0] in DIRECTORIES or relative.as_posix() in ROOT_FILES:
            destination = TARGET / relative
            if not destination.resolve().is_relative_to(TARGET):
                raise ValueError("Destination escaped the explicitly named repository")
            if digest(path) != digest(destination):
                yield relative.as_posix(), digest(destination), digest(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        changes = [{"path": path, "before": before, "after": after}
                   for path, before, after in paths()]
        MANIFEST.write_text(json.dumps(changes, indent=2), encoding="utf-8")
        print(json.dumps({"changed_files": len(changes), "paths": [c["path"] for c in changes]}))
        return
    changes = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for change in changes:
        if digest(TARGET / change["path"]) != change["before"]:
            raise ValueError("Source changed after review: " + change["path"])
        if digest(STAGE / change["path"]) != change["after"]:
            raise ValueError("Payload changed after review: " + change["path"])
    backup = TARGET / "data" / ("v2-backup-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S"))
    backup.mkdir(parents=True, exist_ok=False)
    database = TARGET / "data" / "don-codino.sqlite3"
    counts = {}
    if database.exists():
        with closing(sqlite3.connect(database)) as source:
            if source.execute("SELECT count(*) FROM tasks WHERE status='RUNNING'").fetchone()[0]:
                raise ValueError("A contract is still running; do not interrupt it")
            history_ids = [row[0] for row in source.execute(
                "SELECT id FROM tasks ORDER BY started_at DESC LIMIT 100")]
            repair_ids = [row[0] for row in source.execute(
                "SELECT id FROM tasks WHERE workspace LIKE '%calculator-ce0773e169' "
                "ORDER BY started_at DESC LIMIT 1")]
            counts = {table: source.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                      for table in ("tasks", "events")}
            with closing(sqlite3.connect(backup / "don-codino.sqlite3")) as destination:
                source.backup(destination)
    for change in changes:
        destination = TARGET / change["path"]
        if destination.exists():
            previous = backup / "source" / change["path"]
            previous.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, previous)
    (backup / "manifest.json").write_text(json.dumps({"changes": changes, "counts": counts}, indent=2),
                                          encoding="utf-8")
    # Everything is checked and backed up before stopping the verified local server.
    prior_process = expected_server()
    stop_expected_server(prior_process)
    # No running task was recorded before shutdown; the source update is now offline.
    for change in changes:
        destination = TARGET / change["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(STAGE / change["path"], destination)
    for change in changes:
        if digest(TARGET / change["path"]) != change["after"]:
            raise ValueError("Copy verification failed: " + change["path"])
    runtime = start_and_smoke(history_ids, repair_ids)
    report = TARGET / "MASTER_VALIDATION_REPORT.md"
    with report.open("a", encoding="utf-8") as stream:
        stream.write("\n## Published source validation\n\n")
        stream.write(f"Applied {len(changes)} hash-checked source changes after stopping the "
                     f"verified localhost server (PID {prior_process['ProcessId']}). Source backup "
                     f"and SQLite online backup: `{backup}`. Preserved task/event rows: {counts}.\n\n")
        stream.write(f"Restarted `{HOST_PYTHON} -m uvicorn app.main:create_app --factory "
                     f"--host 127.0.0.1 --port 8765` (PID {runtime['pid']}); /health returned "
                     f"HTTP 200 `{runtime['health']}`. Dashboard, static JS, OpenAPI and "
                     f"workspace routes returned HTTP 200. Persisted all {runtime['history_count']} "
                     f"pre-existing task IDs; V2 diagnostics report DB quick_check ok and "
                     f"Codex available. The real repair task retains its VERIFIED attempt history.\n")
    print(json.dumps({"published": len(changes), "backup": str(backup), "history_before": counts,
                      "previous_process": prior_process["ProcessId"], "runtime": runtime}))


if __name__ == "__main__":
    main()
