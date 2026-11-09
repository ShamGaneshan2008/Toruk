"""Prepare or verify a byte-preserving, offline research evidence hand-off.

No training or generation. Historical evidence files are never rewritten.
"""

import argparse
import ast
import hashlib
import io
import json
import math
import re
import shutil
import subprocess
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = "artifacts/research-evidence-portable-v1"
MANIFEST = SUPPORT + "/manifest.json"
STUDIES = (
    "m6-successor-v1",
    "backbone-qualification-v1",
    "qwen-long-history-v1",
    "qwen-long-history-v2",
    "qwen-long-history-v3",
)
PROFILE = "artifacts/m6-successor-v1/execution/profile/checkpoint.pt"
SECRET = re.compile(
    r"\b(?:AKIA[A-Z0-9]{16}|ASIA[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{30,}|hf_[A-Za-z0-9]{25,}|sk-(?:proj-)?[A-Za-z0-9_-]{25,})\b"
    r"|-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def portable_path(name: str) -> str:
    """Map recorded Windows checkout prefixes without depending on either device."""
    name = name.replace("\\", "/")
    for prefix in ("D:/Toruk/", "C:/Users/susee/VS_CODE_PROJECT/Toruk/"):
        if name.casefold().startswith(prefix.casefold()):
            name = name[len(prefix) :]
            break
    if name.startswith("/") or ":" in name or ".." in Path(name).parts:
        raise ValueError("unsupported external path: " + name)
    return name


def classification(name: str) -> str:
    parts = name.replace("\\", "/").split("/")
    if name == PROFILE:
        return "essential profile checkpoint (one copy covers both identical profiles)"
    if len(parts) > 2 and parts[2] in ("backbone", "backbones"):
        return "external model download; identity retained, weights not needed for offline checks"
    if "verification" in parts and parts.index("verification") < len(parts) - 2:
        return "generated verification build/fixture; original check receipts retained"
    if any(p in parts for p in (".cache", "__pycache__", "node_modules", "build", "dist")):
        return "cache or build output"
    if name.endswith(".pt"):
        return "duplicate primary checkpoint; exact bytes in selector-bundle.zip"
    if name.endswith((".tmp", ".lock")):
        return "temporary file"
    return "essential frozen evidence or original verification receipt"


def selected(name: str) -> bool:
    return classification(name).startswith("essential")


def write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def index_blobs(root: Path) -> dict[str, bytes]:
    entries = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=root)
    paths: dict[str, str] = {}
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        staged_header, name = entry.split(b"\t", 1)
        _, object_id, stage = staged_header.split()
        if stage != b"0":
            raise ValueError("unmerged index")
        paths[name.decode()] = object_id.decode()
    # One batch process avoids hundreds of shell calls and preserves binary bytes.
    oids = list(dict.fromkeys(paths.values()))
    response = subprocess.check_output(
        ["git", "cat-file", "--batch"], input=("\n".join(oids) + "\n").encode(), cwd=root
    )
    content: dict[str, bytes] = {}
    cursor = 0
    for oid in oids:
        end = response.index(b"\n", cursor)
        batch_header = response[cursor:end].split()
        size = int(batch_header[2])
        cursor = end + 1
        content[oid] = response[cursor : cursor + size]
        cursor += size + 1
    return {name: content[oid] for name, oid in paths.items()}


class Evidence:
    def __init__(self, root: Path, files: dict[str, bytes]) -> None:
        self.root, self.files = root, files
        self.by_hash: dict[str, tuple[str, bytes]] = {}
        for name, data in files.items():
            self.by_hash.setdefault(digest(data), (name, data))
        for name, data in files.items():
            if name.endswith(".zip"):
                self._archive(name, data)

    def _archive(self, name: str, data: bytes, depth: int = 0) -> None:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for item in archive.infolist():
                if item.is_dir():
                    continue
                if item.filename.startswith(("/", "\\")) or ".." in Path(item.filename).parts:
                    raise ValueError("unsafe source archive member")
                if item.file_size > 12_000_000:
                    raise ValueError("unexpected large archive member")
                raw = archive.read(item)
                label = name + "!" + item.filename
                self.by_hash.setdefault(digest(raw), (label, raw))
                if item.filename.endswith(".zip") and depth < 3:
                    self._archive(label, raw, depth + 1)

    def resolve(self, name: str, expected: str) -> tuple[str, bytes] | None:
        name = portable_path(name)
        if name in self.files and digest(self.files[name]) == expected:
            return name, self.files[name]
        return self.by_hash.get(expected)

    def read_json(self, name: str) -> Any:
        return json.loads(self.files[name])


def hash_maps(name: str, value: dict) -> list[dict]:
    result = []
    for key in ("bindings", "files", "sha256", "registered_inputs", "output_bindings"):
        mapping = value.get(key)
        if (
            isinstance(mapping, dict)
            and mapping
            and all(
                isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) for v in mapping.values()
            )
        ):
            result.append(mapping)
    return result


def verify(root: Path, staged: bool = False, native: bool = True) -> dict:
    blobs = index_blobs(root) if staged else None
    raw = blobs[MANIFEST] if blobs is not None else (root / MANIFEST).read_bytes()
    manifest = json.loads(raw)
    files = {}
    for name, expected in manifest["files"].items():
        data = blobs.get(name) if blobs is not None else (root / name).read_bytes()
        if data is None or digest(data) != expected:
            raise ValueError("included file hash mismatch: " + name)
        files[name] = data
    evidence = Evidence(root, files)
    exclusions = manifest["excluded"]
    counts: Counter[str] = Counter()
    substitutions = []
    for name, data in files.items():
        if not name.endswith(
            (
                "registration.json",
                "manifest.json",
                "proposed-freeze.json",
                "final-manifest.json",
                "development-seal.json",
            )
        ):
            continue
        value = json.loads(data)
        for mapping in hash_maps(name, value):
            for original, expected in mapping.items():
                rel = portable_path(original)
                resolved = evidence.resolve(original, expected)
                if resolved:
                    counts["verified_recorded_hashes"] += 1
                    if resolved[0] != rel:
                        substitutions.append(
                            {"record": name, "path": original, "exact_bytes_from": resolved[0]}
                        )
                elif rel in exclusions:
                    counts["declared_omitted_dependencies"] += 1
                else:
                    raise ValueError("unresolved required binding: " + name + " -> " + original)
    results = verify_answers(evidence, manifest, native)
    return {
        "status": "PASS",
        "scope": "offline published-report verification; no model generation",
        "input": "Git index" if staged else "working tree",
        "files": len(files),
        "bytes": sum(len(v) for v in files.values()),
        "hash_checks": dict(counts),
        "snapshot_substitutions": len(substitutions),
        "substitution_details": substitutions,
        "raw_evidence": results,
        "original_environment_replay": "NOT RUN; external weights and generated fixtures omitted",
        "historical_build_binary_hashes": "NOT VERIFIED; deliberately excluded, including wheels",
        "suspension_cpu_memory": "saved observations audited, not newly measured",
    }


def frozen_functions(
    evidence: Evidence, registration: str, source: str, names: set[str], env: dict
) -> None:
    reg = evidence.read_json(registration)
    bindings = reg["bindings"]
    expected = next(h for n, h in bindings.items() if portable_path(n) == source)
    resolved = evidence.resolve(source, expected)
    if not resolved:
        raise ValueError("as-run scorer missing")
    tree = ast.parse(resolved[1].decode("utf-8-sig"))
    definitions: list[ast.stmt] = [
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names
    ]
    exec(compile(ast.Module(body=definitions, type_ignores=[]), resolved[0], "exec"), env)


def verify_answers(evidence: Evidence, manifest: dict, native: bool) -> dict:
    env: dict[str, Any] = {"Any": Any, "re": re}
    frozen_functions(
        evidence,
        "artifacts/backbone-qualification-v1/registration.json",
        "scripts/qualify_answer_backbone.py",
        {"normalized", "phrase", "score"},
        env,
    )
    base_score = env["score"]
    succ: dict[str, Any] = {"Any": Any, "re": re}
    frozen_functions(
        evidence,
        "artifacts/m6-successor-v1/execution/registration.json",
        "scripts/m6_successor.py",
        {"score"},
        succ,
    )
    qwen = {**env, "base_score": base_score}
    frozen_functions(
        evidence,
        "artifacts/qwen-long-history-v1/execution-v2/registration.json",
        "scripts/qwen_long_history.py",
        {"score"},
        qwen,
    )
    tokenizers: dict[str, Any] = {}
    if native:
        from transformers import AutoTokenizer

        # Only verifier assets are read; neither original absolute checkout is needed.
        for alias in ("smollm", "qwen"):
            tokenizers[alias] = AutoTokenizer.from_pretrained(
                evidence.root / SUPPORT / "tokenizers" / alias,
                local_files_only=True,
                trust_remote_code=False,
            )
    specifications = [
        (
            "successor",
            "artifacts/m6-successor-v1/execution",
            "heldout",
            ("recent", "lexical", "toruk"),
            succ["score"],
        ),
        (
            "qualification",
            "artifacts/backbone-qualification-v1",
            "heldout",
            ("smollm", "qwen"),
            base_score,
        ),
        (
            "long-v1",
            "artifacts/qwen-long-history-v1/execution-v2",
            "development",
            ("full", "lexical", "toruk"),
            qwen["score"],
        ),
        (
            "long-v2",
            "artifacts/qwen-long-history-v2/attempt-003/rehearsal",
            "development",
            ("full", "recent", "lexical", "toruk"),
            qwen["score"],
        ),
    ]
    scores, audited = {}, 0
    for label, folder, split, arms, scorer in specifications:
        cases = evidence.read_json(folder + "/" + split + ".json")
        gold = {c["id"]: c for c in cases}
        for arm in arms:
            data = [
                json.loads(s)
                for s in evidence.files[f"{folder}/{split}-{arm}-answers.jsonl"].splitlines()
            ]
            ordinary = [
                r for r in data if not r.get("is_replay") and not r["id"].endswith("-replay")
            ]
            scores[label + "/" + arm] = [
                sum(r["score"]["correct"] for r in ordinary),
                len(ordinary),
            ]
            for row in data:
                case = gold[row["id"].removesuffix("-replay")]
                if row["score"] != scorer(row["answer"], case):
                    raise ValueError("saved score mismatch")
                metrics = row.get("metrics", row)
                if len(row["prompt_ids"]) != metrics.get(
                    "selected_context_tokens", row.get("prompt_tokens")
                ):
                    raise ValueError("prompt token count mismatch")
                if len(row["generated_ids"]) != metrics["output_tokens"]:
                    raise ValueError("output token count mismatch")
                if "selected_sources" in row:
                    for source in row["selected_sources"]:
                        original = case["messages"][int(source["id"][1:])]
                        if {k: source[k] for k in ("role", "content")} != original:
                            raise ValueError("selected evidence text mismatch")
                if native:
                    alias = "smollm" if label == "successor" or arm == "smollm" else "qwen"
                    tokenizer = tokenizers[alias]
                    messages = row.get("prompt_messages", row.get("messages"))
                    if messages is None:
                        messages = [
                            {k: s[k] for k in ("role", "content")} for s in row["selected_sources"]
                        ]
                    ids = tokenizer.apply_chat_template(
                        messages, tokenize=True, add_generation_prompt=True, return_dict=False
                    )
                    if (
                        ids != row["prompt_ids"]
                        or tokenizer.decode(row["generated_ids"], skip_special_tokens=True).strip()
                        != row["answer"]
                    ):
                        raise ValueError("native prompt/decode mismatch")
                audited += 1
    # V3 stores the same worker format under three named arm directories.
    v3 = evidence.read_json("artifacts/qwen-long-history-v3/attempt-001/results.json")
    v3_cases = evidence.read_json("artifacts/qwen-long-history-v3/attempt-001/development.json")
    gold = {c["id"]: c for c in v3_cases}
    for arm in ("before", "lexical", "after"):
        internal = "lexical" if arm == "lexical" else "toruk"
        folder = f"artifacts/qwen-long-history-v3/attempt-001/arms/{arm}/rehearsal"
        data = [
            json.loads(s)
            for s in evidence.files[f"{folder}/development-{internal}-answers.jsonl"].splitlines()
        ]
        count = sum(r["score"]["correct"] for r in data if not r["is_replay"])
        if count != v3["arms"][arm]["correct"]:
            raise ValueError("v3 reported count mismatch")
        for label, subset in (
            ("seven_case_costs", [r for r in data if not r["is_replay"]]),
            ("including_replay_costs", data),
        ):
            for field, total in v3["arms"][arm][label].items():
                if not math.isclose(sum(r[field] for r in subset), total, abs_tol=1e-8):
                    raise ValueError("v3 cost sum mismatch: " + field)
        if arm in ("before", "lexical"):
            old = [
                json.loads(s)
                for s in evidence.files[
                    f"artifacts/qwen-long-history-v2/attempt-003/rehearsal/development-{internal}-answers.jsonl"
                ].splitlines()
            ]
            for current, saved in zip(data, old, strict=True):
                if any(
                    current[k] != saved[k]
                    for k in (
                        "answer",
                        "score",
                        "prompt_ids",
                        "generated_ids",
                        "selected_indices",
                        "work",
                    )
                ):
                    raise ValueError("v3 control does not reproduce v2")
        for row in data:
            case = gold[row["id"].removesuffix("-replay")]
            if row["score"] != qwen["score"](row["answer"], case):
                raise ValueError("v3 score mismatch")
            if native:
                tok = tokenizers["qwen"]
                ids = tok.apply_chat_template(
                    row["prompt_messages"],
                    tokenize=True,
                    add_generation_prompt=True,
                    return_dict=False,
                )
                if (
                    ids != row["prompt_ids"]
                    or tok.decode(row["generated_ids"], skip_special_tokens=True).strip()
                    != row["answer"]
                ):
                    raise ValueError("v3 native mismatch")
            audited += 1
        scores["long-v3/" + arm] = [count, 7]
    expected = manifest["expected_scores"]
    if scores != expected:
        raise ValueError("published report totals changed")
    blocked = evidence.read_json("artifacts/qwen-long-history-v1/blocked-results.json")
    if blocked["status"] != "BLOCKED" or any(blocked["heldout_evaluations_per_arm"].values()):
        raise ValueError("v1 held-out boundary changed")
    return {
        "scores": scores,
        "saved_rows_checked": audited,
        "native_prompt_and_decode": native,
        "heldout_generation": False,
    }


def prepare(root: Path) -> None:
    support = root / SUPPORT
    if support.exists():
        raise ValueError("fresh support directory required")
    support.mkdir(parents=True)
    chosen, excluded, inventory = {}, {}, {}
    for study in STUDIES:
        for path in sorted((root / "artifacts" / study).rglob("*")):
            if not path.is_file():
                continue
            name = path.relative_to(root).as_posix()
            reason = classification(name)
            try:
                before = file_digest(path)
            except PermissionError:
                before = None
                if selected(name):
                    raise
            inventory[name] = {"sha256": before, "bytes": path.stat().st_size, "category": reason}
            if selected(name):
                chosen[name] = before
            else:
                excluded[name] = inventory[name]
    copies = []
    asset_sets = {
        "smollm": (
            "artifacts/m6-successor-v1/backbone",
            (
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "generation_config.json",
                "toruk-backbone.json",
                "README.md",
            ),
        ),
        "qwen": (
            "artifacts/backbone-qualification-v1/backbones/qwen",
            (
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "generation_config.json",
                "toruk-backbone.json",
                "LICENSE",
                "README.md",
            ),
        ),
    }
    for alias, (folder, names) in asset_sets.items():
        for name in names:
            source, destination = root / folder / name, support / "tokenizers" / alias / name
            before = digest(source.read_bytes())
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                with source.open("rb") as original:
                    shutil.copyfileobj(original, stream)
            if digest(destination.read_bytes()) != before or digest(source.read_bytes()) != before:
                raise ValueError("copy failed byte verification")
            relative = destination.relative_to(root).as_posix()
            chosen[relative] = before
            copies.append(
                {"source": folder + "/" + name, "copy": relative, "sha256_before_and_after": before}
            )
    # Preserve any published source/report bytes not already recoverable from source ZIPs.
    evidence = Evidence(root, {name: (root / name).read_bytes() for name in chosen})
    missing = []
    for name, data in list(evidence.files.items()):
        if not name.endswith(
            (
                "registration.json",
                "manifest.json",
                "proposed-freeze.json",
                "final-manifest.json",
                "development-seal.json",
            )
        ):
            continue
        for mapping in hash_maps(name, json.loads(data)):
            for original, expected_hash in mapping.items():
                rel = portable_path(original)
                if evidence.resolve(original, expected_hash) or rel in excluded:
                    continue
                candidates = []
                if (root / rel).is_file():
                    candidates.append((rel, (root / rel).read_bytes()))
                archived_root = Path("D:/Toruk")
                if archived_root.is_dir() and (archived_root / rel).is_file():
                    candidates.append(("D:/Toruk/" + rel, (archived_root / rel).read_bytes()))
                process = subprocess.run(
                    ["git", "show", "HEAD:" + rel], cwd=root, capture_output=True
                )
                if process.returncode == 0:
                    candidates.append(("git:HEAD:" + rel, process.stdout))
                match = next(
                    ((label, raw) for label, raw in candidates if digest(raw) == expected_hash),
                    None,
                )
                if match is None:
                    missing.append({"record": name, "path": original, "sha256": expected_hash})
                    continue
                label, raw = match
                target = SUPPORT + "/snapshots/" + expected_hash + "/" + Path(rel).name
                write_new(root / target, raw)
                if file_digest(root / target) != expected_hash:
                    raise ValueError("snapshot copy changed bytes")
                chosen[target] = expected_hash
                evidence.by_hash[expected_hash] = (target, raw)
                copies.append(
                    {"source": label, "copy": target, "sha256_before_and_after": expected_hash}
                )
    if missing:
        raise ValueError("required evidence not recoverable: " + json.dumps(missing))
    # Include all known scientific result totals; no scorer/case or evidence is regenerated.
    expected = {
        "successor/recent": [0, 24],
        "successor/lexical": [7, 24],
        "successor/toruk": [5, 24],
        "qualification/smollm": [15, 30],
        "qualification/qwen": [18, 30],
        "long-v1/full": [5, 7],
        "long-v1/lexical": [7, 7],
        "long-v1/toruk": [0, 1],
        "long-v2/full": [5, 7],
        "long-v2/recent": [1, 7],
        "long-v2/lexical": [7, 7],
        "long-v2/toruk": [1, 7],
        "long-v3/before": [1, 7],
        "long-v3/lexical": [7, 7],
        "long-v3/after": [5, 7],
    }
    write_new(support / "inventory.json", json_bytes(inventory))
    write_new(support / "copies.json", json_bytes(copies))
    readme = (
        b"# Portable frozen research evidence\n\n"
        b"Run `python scripts/verify_portable_research_evidence.py verify` from the checkout root. "
        b"Install the existing optional chat dependencies for offline native-tokenizer checks. "
        b"No backbone weights, network, training or generation are used. `--no-native` omits only "
        b"native tokenization/decode verification and reports that limitation.\n\n"
        b"Historical files remain byte-identical. Recorded D:/Toruk and C-drive paths map to "
        b"repository-relative paths; exact as-run source/checkpoint bytes can resolve through "
        b"frozen ZIP members rather than the current source. No hash is repaired or normalized.\n\n"
        b"Excluded model downloads, caches, generated fixture models and all wheels/sdists remain "
        b"local. Original broad manifests include those files; their omitted bindings are reported "
        b"explicitly, so this is complete OFFLINE REPORT evidence, not a full original environment "
        b"or a model-inference reproduction. Original check receipts/logs remain included. "
        b"Tokenizers are verified byte copies of existing inputs, not regenerated evidence. "
        b"The selector ZIP contains the primary trained checkpoint; one profile checkpoint "
        b"covers both identical recorded profile weights.\n\n"
        b"Original frozen records contain machine paths and user-directory names. They are "
        b"preserved for provenance, not redacted. Review before committing/sharing.\n"
    )
    write_new(support / "README.md", readme)
    for name in (
        SUPPORT + "/inventory.json",
        SUPPORT + "/copies.json",
        SUPPORT + "/README.md",
        "scripts/verify_portable_research_evidence.py",
        "tests/test_portable_research_evidence.py",
        ".gitattributes",
    ):
        chosen[name] = digest((root / name).read_bytes())
    paths = sorted([*chosen, MANIFEST, SUPPORT + "/STAGED-PATHS.txt"])
    write_new(support / "STAGED-PATHS.txt", ("\n".join(paths) + "\n").encode())
    chosen[SUPPORT + "/STAGED-PATHS.txt"] = digest((support / "STAGED-PATHS.txt").read_bytes())
    manifest = {
        "schema": "portable-research-evidence-v1",
        "base_commit": "b304091bd16a12be7204d207ed7d82e51e5ba9a6",
        "files": dict(sorted(chosen.items())),
        "excluded": excluded,
        "expected_scores": expected,
        "no_evidence_regenerated": True,
        "scope": "offline report verification; external original environment dependencies declared",
    }
    write_new(root / MANIFEST, json_bytes(manifest))
    print(
        json.dumps(
            {
                "prepared_paths": len(paths),
                "included_bytes": sum((root / n).stat().st_size for n in paths),
                "excluded_paths": len(excluded),
                "explicit_profile_checkpoint": PROFILE,
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--no-native", action="store_true")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.root.resolve())
    else:
        result = verify(args.root.resolve(), args.staged, not args.no_native)
        print(
            json.dumps({k: v for k, v in result.items() if k != "substitution_details"}, indent=2)
        )


if __name__ == "__main__":
    main()
