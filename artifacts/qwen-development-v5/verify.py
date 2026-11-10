"""Verify preserved v5 bytes and replay development scoring without model weights."""

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path, PureWindowsPath

EVIDENCE = "artifacts/qwen-development-v5"


def relative(name):
    if Path(name).anchor or ".." in Path(name).parts or ":" in name or "\\" in name:
        raise ValueError("unsafe repository-relative binding: " + name)
    return Path(name)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_bindings(root, bindings, external, substitutions=None):
    checked = 0
    for name, expected in bindings.items():
        if name in external:
            if expected != external[name]:
                raise ValueError("recorded external asset identity drift: " + name)
            continue
        path = root / relative(name)
        raw = path.read_bytes()
        if digest(raw) != expected:
            # Accept a checkout newline variant only if its complete old hash
            # matches. Never modify originals or substitute a different hash.
            text_file = path.suffix in {".py", ".json", ".md", ".toml"} or path.name in {
                ".gitattributes",
                ".gitignore",
            }
            lf = raw.replace(b"\r\n", b"\n")
            if (
                not text_file
                or b"\0" in raw
                or not any(digest(v) == expected for v in (lf, lf.replace(b"\n", b"\r\n")))
            ):
                raise ValueError("preserved input bytes changed: " + name)
            if substitutions is not None:
                substitutions.append(
                    {
                        "path": name,
                        "expected_sha256": expected,
                        "from": "exact hash-matching checkout newline variant",
                    }
                )
        checked += 1
    return checked


def substantive(result):
    return {
        k: v
        for k, v in result.items()
        if k not in {"audit_wall_seconds", "audit_controller_cpu_seconds"}
    }


def verify(root):
    folder = root / EVIDENCE

    def read(path):
        return json.loads(path.read_bytes())

    manifest = read(folder / "evidence-manifest.json")
    substitutions = []
    payloads = verify_bindings(root, manifest["files"], {}, substitutions)
    run = folder / "attempt-002"
    reg = read(run / "registration.json")
    frozen = verify_bindings(root, reg["frozen_baseline"], {}, substitutions)
    sys.path[:0] = [str(root / "scripts"), str(root / "src")]
    import qwen_development_v5 as study

    if study.ROOT != root.resolve():
        raise ValueError("replay must import the selected checkout's sources")
    inputs = study.Inputs(root)
    original = inputs.json(study.OLD + "/arms/after/rehearsal/registration.json")
    original_assets = {
        PureWindowsPath(n).name: original["bindings"][n] for n in original["model_files"]
    }
    first = read(run / "arms/original-toruk/rehearsal/registration.json")
    external = {name: original_assets[PureWindowsPath(name).name] for name in first["model_files"]}
    if len(external) != len(original_assets):
        raise ValueError("external asset membership mismatch")
    bindings = verify_bindings(root, reg["bindings"], external, substitutions)
    for name, version in reg["dependencies"].items():
        if importlib.metadata.version(name) != version:
            raise ValueError("native replay dependency drift: " + name)
    for label in reg["config"]["order"]:
        candidate, arm = label.split("-")
        arm_reg = read(run / "arms" / label / "rehearsal/registration.json")
        bindings += verify_bindings(root, arm_reg["bindings"], external, substitutions)
        if (
            arm_reg["candidate"] != candidate
            or arm_reg["arm"] != arm
            or arm_reg["instruction"] != reg["config"]["candidates"][candidate]
            or set(arm_reg["model_files"]) != set(external)
        ):
            raise ValueError("asymmetric condition or asset membership")
    if (folder / "attempt-001/development-started.json").exists() or list(
        (folder / "attempt-001").glob("arms/*/rehearsal/*-answers.jsonl")
    ):
        raise ValueError("superseded registration unexpectedly generated answers")
    costs = read(run / "development-cost.json")
    limits = reg["config"]["limits"]
    if [s["condition"] for s in costs["stages"]] != reg["config"]["order"]:
        raise ValueError("cold stage membership/order mismatch")
    for stage in costs["stages"]:
        if (
            stage["failure"] is not None
            or stage["returncode"] != 0
            or stage["wall_seconds"] > limits["rehearsal_stage_wall_seconds"]
            or stage["cpu_seconds"] > limits["rehearsal_stage_cpu_seconds"]
            or max(stage["peak_private_bytes"], stage["peak_os_private_bytes"])
            > limits["memory_bytes"]
        ):
            raise ValueError("saved stage did not pass resource limits")
    for field in ("wall_seconds", "cpu_seconds"):
        if not math.isclose(sum(s[field] for s in costs["stages"]), costs["totals"][field]):
            raise ValueError("cold cost total mismatch")
        if costs["totals"][field] > limits["rehearsal_total_" + field]:
            raise ValueError("cumulative resource limit exceeded")
    saved = read(run / "results.json")
    # All repository bindings were checked above. Replace only asset-dependent
    # verification and the exclusive output writer in this offline audit process.
    # The sealed runner, scorer and evidence bytes on disk are never modified.
    original_verify, original_write = study.verify_registration, study.write
    captured = []
    try:
        study.verify_registration = lambda path: reg
        study.write = lambda path, data: captured.append((path, data))
        with contextlib.redirect_stdout(io.StringIO()):
            actual = study.summarize(run)
    finally:
        study.verify_registration, study.write = original_verify, original_write
    if (
        len(captured) != 1
        or captured[0][0] != run / "results.json"
        or substantive(actual) != substantive(saved)
    ):
        raise ValueError("native development audit does not reproduce")
    if not actual["technical_validity"] or any(
        d["development_support"] for d in actual["decisions"].values()
    ):
        raise ValueError("preserved result is not the reported valid negative study")
    return {
        "status": "PASS",
        "payload_hashes": payloads,
        "frozen_hashes": frozen,
        "registered_local_bindings_checked": bindings,
        "external_asset_identities_matched_to_original_registration": len(external),
        "external_asset_bytes_loaded_or_verified": False,
        "checkout_newline_substitutions": substitutions,
        "native_prompts_outputs_scores_costs_replays_and_failed_gates_reproduced": True,
        "conditions": {name: sum(c["correct"]) for name, c in actual["conditions"].items()},
        "decisions": actual["decisions"],
        "new_generations": 0,
        "heldout_records_parsed_or_scored": 0,
        "limitation": (
            "Offline result audit; excluded model weights and original host execution "
            "are not reproduced."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("receipt already exists")
    if args.staged:
        with tempfile.TemporaryDirectory(prefix="qwen-v5-index-") as temporary:
            root = Path(temporary).resolve()
            subprocess.run(
                ["git", "checkout-index", "--all", "--prefix=" + root.as_posix() + "/"],
                cwd=args.root,
                check=True,
            )
            result = verify(root)
        result["input"] = "exported Git index, excluding untracked/generated files"
    else:
        result = verify(args.root.resolve())
        result["input"] = "working tree"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
