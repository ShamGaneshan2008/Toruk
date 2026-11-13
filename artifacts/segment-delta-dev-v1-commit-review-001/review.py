"""Read-only audit of the recorded result, using working files, index or a Git tree.

--prepare writes only a fresh review manifest. Verification never fits a model,
generates an answer, imports a held-out dataset or rewrites historical evidence.
"""

import argparse
import hashlib
import io
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = "artifacts/segment-delta-dev-v1/"
REVIEW = "artifacts/segment-delta-dev-v1-commit-review-001/"
MANIFEST = REVIEW + "review-manifest.json"
GENERATED = (
    RUN + "contracts/tmp/",
    "artifacts/segment-delta-dev-v1-verification-001/package/",
    "artifacts/segment-delta-dev-v1-verification-001/pytest-cache/",
    "artifacts/segment-delta-dev-v1-verification-001/pytest-tmp/",
)
REGISTRATION = "bb828757efe6f4073d7d1c74405aa7c73120e11fcfdfff6c09b8a95812e1d2dd"
LOCK = "8711afee882f4e4837e4048a878447c1d1706220ca72faa7ed5270c07e878984"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args, data=None):
    return subprocess.check_output(["git", *args], cwd=ROOT, input=data)


def decode(raw):
    return json.loads(raw.decode("utf-8-sig"))


def prepare():
    original = decode((ROOT / RUN / "artifact-inventory.json").read_bytes())
    include, exclude = {}, {}
    for name, expected in original["files"].items():
        raw = (ROOT / name).read_bytes()
        require(
            len(raw) == expected["bytes"] and digest(raw) == expected["sha256"],
            "original inventory mismatch: " + name,
        )
        if name.startswith(GENERATED):
            exclude[name] = dict(
                **expected, reason="disposable test/cache/package output; retained locally"
            )
        else:
            include[name] = expected
    for name in (
        ".gitattributes",
        ".gitignore",
        RUN + "artifact-inventory.json",
        REVIEW + "review.py",
        "docs/research/segment-delta-dev-v1-commit-review.md",
    ):
        raw = (ROOT / name).read_bytes()
        include[name] = dict(bytes=len(raw), sha256=digest(raw))
    draft = "docs/research/toruk-custom-lm-architecture-decision-v1.md"
    exclude[draft] = dict(
        bytes=(ROOT / draft).stat().st_size,
        sha256=digest((ROOT / draft).read_bytes()),
        reason="pre-existing unrelated untracked draft; preserve outside commit",
    )
    manifest = dict(
        version="segment-delta-dev-v1-commit-review-001",
        base_commit=git("rev-parse", "HEAD").decode().strip(),
        included=include,
        excluded=exclude,
        generated_bytecode="ignored; not research evidence",
        included_bytes=sum(row["bytes"] for row in include.values()),
        original_inventory_files=len(original["files"]),
        no_evidence_rewritten=True,
    )
    with (ROOT / MANIFEST).open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return manifest


def git_blobs(names, revision=None):
    if revision is None:
        raw = git("ls-files", "--stage", "-z")
        entries = {}
        for entry in raw.split(b"\0"):
            if entry:
                metadata, name = entry.split(b"\t", 1)
                _, oid, stage = metadata.split()
                require(stage == b"0", "unmerged index")
                entries[name.decode()] = oid
        changes = set(
            git("diff", "--cached", "--name-only", "-z").decode().strip("\0").split("\0")
        ) - {""}
        allowed = set(names) | {MANIFEST}
        require(
            all(name in allowed or name.startswith(REVIEW) for name in changes),
            "unreviewed staged path",
        )
        names = set(names) | {MANIFEST} | {name for name in changes if name.startswith(REVIEW)}
    else:
        tree = git("rev-parse", revision + "^{tree}").decode().strip()
        entries = {}
        for entry in git("ls-tree", "-r", "-z", tree).split(b"\0"):
            if entry:
                metadata, name = entry.split(b"\t", 1)
                _, kind, oid = metadata.split()
                require(kind == b"blob", "non-blob tree entry")
                entries[name.decode()] = oid
        names = set(names) | {MANIFEST} | {name for name in entries if name.startswith(REVIEW)}
    require(set(names) <= entries.keys(), "required reviewed files absent from index/tree")
    oids = list(dict.fromkeys(entries[name] for name in sorted(names)))
    packed = git("cat-file", "--batch", data=b"\n".join(oids) + b"\n")
    objects, offset = {}, 0
    for oid in oids:
        end = packed.index(b"\n", offset)
        actual, kind, length = packed[offset:end].split()
        require(actual == oid and kind == b"blob", "invalid Git blob response")
        offset = end + 1
        size = int(length)
        objects[oid] = packed[offset : offset + size]
        offset += size + 1
    return {name: objects[entries[name]] for name in names}


def security(files):
    patterns = {
        "private-key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "openai-key": rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}",
        "github-token": rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})",
        "aws-access-id": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        "credential-literal": rb"""(?i)["']?(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)["']?\s*[:=]\s*["'][^"'\r\n]{12,}["']""",
    }
    findings = []
    for name, raw in files.items():
        require(len(raw) <= 1024**2, "oversized file (>1MiB): " + name)
        require(
            not name.startswith(GENERATED) and "__pycache__" not in name,
            "generated staged file: " + name,
        )
        for kind, pattern in patterns.items():
            if re.search(pattern, raw):
                findings.append(dict(path=name, pattern=kind))
    require(not findings, "possible secret patterns (values suppressed): " + json.dumps(findings))
    return dict(
        files_scanned=len(files),
        max_bytes=max(map(len, files.values())),
        findings=0,
        method="bounded credential-pattern scan plus reviewed scope; not a general secret detector",
    )


def audit(read, inspect_checkpoints=False):
    def obj(name):
        return decode(read(RUN + name))

    def lines(name):
        return [json.loads(line) for line in read(RUN + name).decode().splitlines()]

    require(digest(read(RUN + "registration.json")) == REGISTRATION, "registration changed")
    require(digest(read(RUN + "implementation-lock.json")) == LOCK, "implementation lock changed")
    reg, lock, summary, cost = [
        obj(name)
        for name in (
            "registration.json",
            "implementation-lock.json",
            "summary.json",
            "run-cost.json",
        )
    ]
    for name, expected in reg["data"].items():
        require(digest(read(RUN + name)) == expected, "dataset hash mismatch: " + name)
    for snapshot, mapping in (
        ("protocol-sources/", reg["source_files"]),
        ("implementation-sources/", lock["sources"]),
    ):
        for name, expected in mapping.items():
            require(digest(read(RUN + snapshot + name)) == expected, "as-run source hash: " + name)
    for name, expected in reg["rehearsal_files"].items():
        require(digest(read(RUN + name)) == expected, "rehearsal hash mismatch: " + name)
    require(
        digest(read(RUN + "contracts/cost.json")) == lock["contracts_sha256"],
        "contract receipt hash",
    )
    labels, inputs = obj("labels-evaluator-only.json"), obj("inputs.json")
    require(len(labels) == len(inputs) == 24, "case counts")
    for case in inputs:
        require(
            digest(json.dumps(case, sort_keys=True).encode()) == lock["case_sha256"][case["id"]],
            "case hash",
        )
    from_index = {}
    for name, cell in summary["cells"].items():
        raw_name = "stages/generate-" + name + "/predictions.jsonl"
        require(
            digest(read(RUN + raw_name))
            == obj("stages/generate-" + name + "/generation-seal.json")["sha256"],
            "raw prediction seal",
        )
        predictions = lines(raw_name)
        require(
            len(predictions) == 25
            and predictions[-1]["replay"]
            and predictions[-1]["result"] == predictions[0]["result"],
            "replay/count mismatch",
        )
        exact = 0
        for prediction, case, label in zip(predictions[:24], inputs, labels, strict=True):
            require(
                prediction["id"] == case["id"] == label["id"]
                and prediction["prefix"] == case["prefix"],
                "case/prefix mismatch",
            )
            require(
                prediction["result"]["input_ids"] == [1, *(b + 3 for b in case["prefix"].encode())],
                "native input IDs",
            )
            exact += prediction["result"]["generated_ids"] == [
                *(b + 3 for b in label["gold"].encode()),
                2,
            ]
        require(
            exact == cell["correct"] == 0
            and cell["long_correct"] == 0
            and all(v == 0 for v in cell["categories"].values()),
            "negative LM scores changed",
        )
        for metric in ("cpu", "wall"):
            expected = (
                sum(cost["stages"][f"{stage}-{name}"][metric] for stage in ("generate", "score"))
                + summary["shared"][metric] / 10
            )
            require(
                math.isclose(cell["eval_" + metric], expected, rel_tol=1e-12),
                "evaluation cost mismatch",
            )
        from_index[name] = exact
    lex = lines("stages/lexical/predictions.jsonl")
    require(len(lex) == 25 and lex[0]["result"] == lex[-1]["result"], "lexical replay")
    lexical = sum(
        row["result"]["generated_ids"] == [*(b + 3 for b in label["gold"].encode()), 2]
        for row, label in zip(lex[:24], labels, strict=True)
    )
    require(
        lexical == summary["lexical"]["correct"] == 24 and summary["advance"] is False,
        "lexical/no-go result changed",
    )
    checkpoints = []
    for seed in (113, 227):
        delta, recurrent = [
            summary["cells"][f"{seed}-{variant}-full"] for variant in ("delta", "recurrent")
        ]
        for key in ("train_cpu", "train_wall", "eval_cpu", "eval_wall"):
            require(delta[key] > recurrent[key], "higher delta cost was not preserved: " + key)
        expected_gates = dict(
            category_no_regression=True,
            ordinary_nll=True,
            distant_gain=False,
            exact_floor_and_gain=False,
            inference_cpu=False,
            inference_wall=False,
            memory_dependence=False,
            training_cpu=False,
            training_wall=False,
            unknown_safety=False,
        )
        require(summary["gates"][str(seed)] == expected_gates, "recorded failed gates changed")
        trace_refs = []
        for variant in ("ordinary", "recurrent", "delta"):
            prefix = f"stages/train-{seed}-{variant}/"
            trace = lines(prefix + "checkpoint.trace.jsonl")
            stats, meta = obj(prefix + "training.json"), obj(prefix + "checkpoint-meta.json")
            raw = read(RUN + prefix + "checkpoint.pt")
            require(
                len(trace) == 128 and stats["targets"] == sum(row["targets"] for row in trace),
                "training target trace",
            )
            trace_refs.append([(row["ids"], row["targets"]) for row in trace])
            require(
                digest(raw) == meta["sha256"] and len(raw) == meta["bytes"], "checkpoint hash/size"
            )
            if inspect_checkpoints:
                import torch

                saved = torch.load(io.BytesIO(raw), weights_only=True, map_location="cpu")
                require(
                    saved["format"] == "toruk-segment-delta-dev-v1"
                    and saved["variant"] == variant
                    and saved["fit"]["seed"] == seed,
                    "checkpoint type/variant/seed",
                )
                require(
                    saved["next_step"] == 128
                    and saved["next_document_cursor"] == 256
                    and saved["targets"] == stats["targets"],
                    "checkpoint progress",
                )
                require(
                    saved["identity"]["registration"] == REGISTRATION
                    and saved["identity"]["implementation"] == LOCK,
                    "checkpoint seal binding",
                )
                require(
                    sum(t.numel() for t in saved["model"].values()) == reg["parameters"][variant],
                    "checkpoint parameter count",
                )
                require(
                    all(torch.isfinite(t).all() for t in saved["model"].values()),
                    "nonfinite saved weights",
                )
            checkpoints.append(dict(path=RUN + prefix + "checkpoint.pt", **meta))
        require(trace_refs[0] == trace_refs[1] == trace_refs[2], "unmatched training exposure")
    require(
        cost["status"] == "COMPLETED"
        and len(cost["stages"]) == 27
        and all(r["status"] == "PASS" for r in cost["stages"].values()),
        "registered stage integrity",
    )
    require(
        obj("rehearsal-numeric.json")["optimizer_steps"] == 0
        and obj("rehearsal/worker.json")["lifetime_cpu"] > 0,
        "failed rehearsal lost",
    )
    require(
        read(RUN + "rehearsal/resources.jsonl")
        and obj("cost-ledger.json")["full_project_cpu"] == "UNKNOWN, not zero",
        "partial cost evidence lost",
    )
    return dict(
        status="PASS",
        lm_exact=from_index,
        lexical_exact=lexical,
        advance=False,
        requests=275,
        checkpoints=checkpoints,
        checkpoint_payloads_inspected=inspect_checkpoints,
        training_or_generation_executed=False,
        held_out_access=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--staged", action="store_true")
    scope.add_argument("--revision")
    parser.add_argument("--inspect-checkpoints", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        result = prepare()
        print(
            json.dumps(
                dict(
                    status="PREPARED",
                    included=len(result["included"]),
                    excluded=len(result["excluded"]),
                    bytes=result["included_bytes"],
                )
            )
        )
        return
    manifest = decode((ROOT / MANIFEST).read_bytes())
    if args.staged or args.revision:
        files = git_blobs(manifest["included"], args.revision)
        require(
            files[MANIFEST] == (ROOT / MANIFEST).read_bytes(),
            "review manifest changed in index/tree",
        )
    else:
        files = {name: (ROOT / name).read_bytes() for name in manifest["included"]}
    for name, expected in manifest["included"].items():
        require(
            len(files[name]) == expected["bytes"] and digest(files[name]) == expected["sha256"],
            "reviewed file changed: " + name,
        )
    result = audit(files.__getitem__, args.inspect_checkpoints)
    result["security"] = security(files)
    result["scope"] = "index" if args.staged else args.revision or "working files"
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
