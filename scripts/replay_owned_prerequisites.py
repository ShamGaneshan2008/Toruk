"""Replay sealed owned-model evidence using its archived build metadata in isolation."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from toruk_lm.integrated_study import file_identity

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ("routing-v2-20261103", "value-fidelity-dev-v1-20261103")


def registered_source(root: Path, reference: Path, name: str, expected: str) -> Path:
    current = root / name
    if current.is_file() and file_identity(current) == expected:
        return current
    # Only the measured metadata drift is restored. Never waive runtime/data/
    # checkpoint integrity or substitute a newly fitted model.
    archived = reference / "source" / name
    if name == "pyproject.toml" and archived.is_file() and file_identity(archived) == expected:
        return archived
    raise ValueError(f"Cannot reproduce registered input: {name}")


def deterministic(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: deterministic(item) for key, item in value.items() if key != "response_ms"}
    if isinstance(value, list):
        return [deterministic(item) for item in value]
    return value


def value_worker(run: Path) -> None:
    import value_fidelity_dev as study

    for seed in (31, 47):
        for method in study.METHODS:
            study.evaluate(run, method, seed)
    study.analyze(run)


def replay(output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Use a fresh prerequisite replay directory")
    sources: dict[str, Path] = {}
    declarations = []
    artifact_roots = set(REFERENCES)
    for folder in REFERENCES:
        reference = ROOT / "artifacts" / folder
        registered = json.loads((reference / "registration.json").read_text(encoding="utf-8"))
        for name, expected in registered["files"].items():
            path = registered_source(ROOT, reference, name, expected)
            if name in sources and file_identity(sources[name]) != file_identity(path):
                raise ValueError(f"Conflicting registered input identities: {name}")
            sources[name] = path
            declarations.append(
                {
                    "reference": folder,
                    "input": name,
                    "sha256": expected,
                    "source": str(path),
                    "archived_metadata": path != ROOT / name,
                }
            )
            parts = Path(name).parts
            if parts[0] == "artifacts":
                artifact_roots.add(parts[1])
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    # Copies, not junctions: no output can modify the original evidence tree.
    for folder in ("scripts", "tests", "src/toruk_lm"):
        target = workspace / folder
        target.mkdir(parents=True)
        for source in (ROOT / folder).glob("*.py"):
            shutil.copy2(source, target / source.name)
    for folder in sorted(artifact_roots):
        original = ROOT / "artifacts" / folder
        for source in original.rglob("*"):
            if not source.is_file() or any(
                part in ("checks", "verification", "package", "__pycache__")
                for part in source.parts
            ):
                continue
            target = workspace / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for name, source in sources.items():
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for row in declarations:
        if file_identity(workspace / row["input"]) != row["sha256"]:
            raise ValueError("Staged input does not match original registration")
    value = output / "value-replay"
    (value / "train").mkdir(parents=True)
    (value / "raw").mkdir()
    original_value = ROOT / "artifacts" / REFERENCES[1]
    for name in ("registration.json", "models.json", "development.json"):
        shutil.copy2(original_value / name, value / name)
    for seed in (31, 47):
        shutil.copy2(
            original_value / "train" / f"augmented-{seed}.pt",
            value / "train" / f"augmented-{seed}.pt",
        )
    env = {**os.environ, "PYTHONPATH": str(workspace / "src"), "PYTHONIOENCODING": "utf-8"}
    commands = []

    def run(label: str, args: list[str], timeout: int = 180) -> None:
        command = [sys.executable, *args]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
        (output / f"{label}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        commands.append(
            {
                "command": command,
                "cwd": str(workspace),
                "returncode": completed.returncode,
                "seconds": time.perf_counter() - started,
            }
        )
        (output / "commands.json").write_text(
            json.dumps(commands, indent=2) + "\n", encoding="utf-8"
        )
        if completed.returncode:
            raise RuntimeError(f"Prerequisite replay failed: {label}; preserve output")
        print(label, "PASS", flush=True)

    run(
        "routing",
        [
            "scripts/replay_routing_v2.py",
            "--sealed-run",
            "artifacts/routing-v2-20261103",
            "--output",
            str(output / "routing.json"),
            "--loads",
            "0",
        ],
    )
    run("value", ["scripts/replay_owned_prerequisites.py", "--value-worker", str(value)])
    run("value-oracle", ["scripts/audit_value_fidelity_dev.py", "--run", str(value)])
    differences = []
    answers = 0
    for fresh in sorted((value / "raw").glob("*.json")):
        previous = json.loads((original_value / "raw" / fresh.name).read_text(encoding="utf-8"))
        current = json.loads(fresh.read_text(encoding="utf-8"))
        if deterministic(previous["predictions"]) != deterministic(current["predictions"]):
            differences.append(fresh.name)
        if deterministic(previous["totals"]) != deterministic(current["totals"]):
            differences.append(fresh.name + ": totals")
        for key in ("checkpoint_sha256", "development_sha256", "model_seal_sha256"):
            if current[key] != previous[key]:
                differences.append(fresh.name + ": " + key)
        answers += sum(len(p["answers"]) for p in current["predictions"])
    routing = json.loads((output / "routing.json").read_text(encoding="utf-8"))
    result = {
        "status": "PASS" if not differences and routing["status"] == "PASS" else "FAIL",
        "restoration": "Only registered archived pyproject.toml in an isolated copied workspace",
        "source_bindings": declarations,
        "routing_answers": routing["answers"],
        "value_answers": answers,
        "value_differences": differences,
        "value_gates": json.loads((value / "summary.json").read_text(encoding="utf-8"))["gates"],
        "original_metadata_sha256": file_identity(ROOT / "pyproject.toml"),
        "isolated_metadata_sha256": file_identity(workspace / "pyproject.toml"),
        "commands": commands,
        "new_training_steps": 0,
    }
    with (output / "replay.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    if result["status"] != "PASS":
        raise ValueError("Generated answers differ; do not build on this comparison")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--value-worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.value_worker is not None:
        value_worker(args.value_worker)
    elif args.output is not None:
        result = replay(args.output.resolve())
        print(
            json.dumps(
                {k: v for k, v in result.items() if k not in ("source_bindings", "commands")},
                indent=2,
            )
        )
    else:
        parser.error("--output required")


if __name__ == "__main__":
    main()
