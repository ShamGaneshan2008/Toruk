"""Verify portable v4 evidence and replay development auditing, without generation."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

EVIDENCE = "artifacts/qwen-long-history-dev-v4"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def relative(name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or ":" in name or "\\" in name:
        raise ValueError("invalid repository-relative path: " + name)
    return path


class Resolver:
    def __init__(self, root, files):
        self.root = root
        self.snapshots = {
            sha(raw): (name, raw) for name, raw in files.items() if "/snapshots/" in name
        }
        self.cache = {}
        self.substitutions = []

    def get(self, name, expected):
        key = (name, expected)
        if key in self.cache:
            return self.cache[key]
        path = self.root / relative(name)
        if path.is_file():
            raw = path.read_bytes()
            if sha(raw) == expected:
                self.cache[key] = raw
                return raw
            # Restore checkout newline variants only if the complete old hash matches.
            # Neither the working tree nor any saved hash record is rewritten.
            if (
                path.suffix
                in {
                    ".py",
                    ".json",
                    ".md",
                    ".toml",
                    ".yml",
                    ".yaml",
                    ".js",
                    ".mjs",
                    ".html",
                    ".css",
                    ".txt",
                    ".in",
                }
                or path.name == ".gitignore"
            ) and b"\0" not in raw:
                lf = raw.replace(b"\r\n", b"\n")
                for variant in (lf, lf.replace(b"\n", b"\r\n")):
                    if sha(variant) == expected:
                        self.substitutions.append(
                            {
                                "path": name,
                                "sha256": expected,
                                "from": "checkout newline variant; exact hash matched",
                            }
                        )
                        self.cache[key] = variant
                        return variant
        if expected in self.snapshots:
            label, raw = self.snapshots[expected]
            self.substitutions.append({"path": name, "sha256": expected, "from": label})
            self.cache[key] = raw
            return raw
        raise ValueError("unresolved recorded source/input hash: " + name + " " + expected)


def verify(root):
    folder = root / EVIDENCE
    manifest = json.loads((folder / "portable-manifest.json").read_bytes())
    files = {}
    for name, expected in manifest["files"].items():
        raw = (root / relative(name)).read_bytes()
        if sha(raw) != expected:
            raise ValueError("portable evidence bytes changed: " + name)
        files[name] = raw

    def read_json(name):
        return json.loads(files[EVIDENCE + "/" + name])

    baseline, saved, summary = (
        read_json(name) for name in ("baseline.json", "audit.json", "verification-summary.json")
    )
    resolver = Resolver(root, files)
    dependencies = {}
    for mapping in (
        baseline["sha256"],
        saved["consumed_development_inputs"],
        manifest["runtime_dependencies"],
    ):
        for name, expected in mapping.items():
            if name in dependencies and dependencies[name] != expected:
                raise ValueError("contradictory input hash: " + name)
            dependencies[name] = expected
            resolver.get(name, expected)
    for name, expected in summary["final_new_source_sha256"].items():
        resolver.get(name, expected)
    receipts = {}
    for name in manifest["receipts"]:
        receipt = json.loads(files[name])
        mapping = receipt["source_files"]
        if sha(json.dumps(mapping, sort_keys=True).encode()) != receipt["source_sha256"]:
            raise ValueError("receipt source fingerprint mismatch: " + name)
        for source, expected in mapping.items():
            resolver.get(source, expected)
        log = manifest["receipt_logs"][name]
        if log not in files:
            raise ValueError("receipt log missing: " + name)
        if (receipt["status"] == "PASS") != (receipt["returncode"] == 0):
            raise ValueError("receipt status disagreement: " + name)
        receipts[name] = receipt
    for label, reported in summary["full_verify_stages"].items():
        receipt = receipts[f"{EVIDENCE}/verification/{label}.json"]
        if any(receipt[k] != reported[k] for k in ("status", "returncode", "seconds")):
            raise ValueError("historical verification summary mismatch: " + label)
    if len(summary["full_verify_stages"]) != 26:
        raise ValueError("historical verification stage count mismatch")
    # Only generated engineering fixtures/builds may be omitted; never audit inputs.
    omitted = manifest["omitted_generated_files"]
    allowed = tuple(
        f"{EVIDENCE}/verification/{name}/"
        for name in (
            "package",
            "conversation-data",
            "independent-cases",
            "owned-lm-smoke",
            "pipeline",
            "research-smoke",
            "tables",
        )
    )
    if any(not name.startswith(allowed) for name in omitted):
        raise ValueError("omission outside generated engineering outputs")
    if set(omitted) & (set(files) | set(dependencies)):
        raise ValueError("required audit input declared omitted")
    # Recreate exact original bytes in a disposable scratch directory. Inherited
    # held-out files are copied/hashed as opaque bytes and never parsed or scored.
    with tempfile.TemporaryDirectory(prefix="qv4-inputs-") as temporary:
        replay_root = Path(temporary)
        for name, expected in dependencies.items():
            path = replay_root / relative(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(resolver.get(name, expected))
        sys.path[:0] = [str(replay_root / "scripts"), str(replay_root / "src")]
        import audit_qwen_development_v4 as replay

        actual = replay.audit(replay_root, baseline)
        skip = {"audit_cpu_seconds", "audit_wall_seconds"}
        if {k: v for k, v in actual.items() if k not in skip} != {
            k: v for k, v in saved.items() if k not in skip
        }:
            raise ValueError("saved development audit does not reproduce")
    return {
        "status": "PASS",
        "scope": "v4 portable evidence and offline development-only audit replay",
        "evidence_files": len(files),
        "frozen_baseline_hashes": len(baseline["sha256"]),
        "consumed_input_hashes": len(saved["consumed_development_inputs"]),
        "historical_receipts_verified": len(receipts),
        "historical_verification_stages": len(summary["full_verify_stages"]),
        "source_hash_bindings_verified": len(resolver.cache),
        "source_substitutions": resolver.substitutions,
        "audit_reproduced_except_new_cpu_wall_timing": True,
        "omitted_generated_files": len(omitted),
        "omitted_builds_needed_for_audit": False,
        "original_build_binary_identity": (
            "NOT VERIFIED against original build; no original binary hashes were recorded"
        ),
        "new_generations": 0,
        "heldout_records_parsed_or_scored": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--staged", action="store_true", help="verify only exported Git-index files"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        parser.error("output already exists; preserve previous receipts")
    if args.staged:
        with tempfile.TemporaryDirectory(prefix="qv4-index-") as temporary:
            subprocess.run(
                ["git", "checkout-index", "--all", "--prefix=" + Path(temporary).as_posix() + "/"],
                cwd=args.root,
                check=True,
            )
            result = verify(Path(temporary))
        result["input"] = "exported Git index; no untracked generated files"
    else:
        result = verify(args.root)
        result["input"] = "working tree"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "source_substitutions"}))


if __name__ == "__main__":
    main()
