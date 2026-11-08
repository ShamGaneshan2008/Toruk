"""Read-only file/archive inventory, retaining failures rather than treating them as absence."""
import hashlib
import json
import os
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EXPECTED = "479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d"
SKIP = {".git", ".venv", "venv", "review-env", "site-packages", "node_modules", "__pycache__"}
MAX_MEMBER = 128 * 1024 * 1024
files, archives, errors = [], [], []

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def onerror(error):
    errors.append({"path": str(error.filename), "error": str(error)})

paths = []
for base, dirs, names in os.walk(ROOT, onerror=onerror, followlinks=False):
    dirs[:] = [d for d in dirs if d not in SKIP and not (Path(base) / d).is_symlink()]
    for name in names:
        p = Path(base) / name
        if p.suffix.lower() in (".pt", ".pth", ".ckpt", ".bin") or name.endswith(".pt.tmp"):
            try:
                files.append({"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)})
            except OSError as e:
                onerror(e)
        if name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z")):
            paths.append(p)

# Explicit documented former checkout and likely owner-managed backup locations.
locations = []
for root in [Path(r"C:\Users\susee\VScode Project\Toruk"),
             Path(r"C:\Users\susee\Downloads"), Path(r"C:\Users\susee\Desktop"),
             Path(r"C:\Users\susee\Documents")]:
    try:
        contents = list(root.iterdir())
        locations.append({"path": str(root), "status": "listed"})
        for p in contents:
            if p.is_file() and p.name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z")):
                paths.append(p)
    except OSError as e:
        locations.append({"path": str(root), "error": str(e)})

for p in sorted(set(paths)):
    entry = {"path": str(p), "members": []}
    try:
        entry.update(bytes=p.stat().st_size, sha256=sha(p))
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:
                for info in z.infolist():
                    if info.is_dir():
                        continue
                    item = {"name": info.filename, "bytes": info.file_size}
                    # Hash every readable member, not just checkpoint-like names.
                    # Large unrelated course/data archives retain member listings only.
                    if info.file_size <= MAX_MEMBER and (p.is_relative_to(ROOT) or
                        any(s in info.filename.lower() for s in ["toruk", "m6", "checkpoint", ".pt", ".ckpt"])):
                        with z.open(info) as stream:
                            item["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
                    else:
                        item["hash_scope"] = "listing only: external unrelated or >128 MiB member"
                    entry["members"].append(item)
        elif p.name.lower().endswith((".tar", ".tar.gz", ".tgz")):
            with tarfile.open(p) as archive:
                for info in archive:
                    if not info.isfile():
                        continue
                    item = {"name": info.name, "bytes": info.size}
                    if info.size <= MAX_MEMBER:
                        with archive.extractfile(info) as stream:
                            item["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
                    else:
                        item["hash_scope"] = "listing only: >128 MiB member"
                    entry["members"].append(item)
        else:
            entry["error"] = "unsupported archive type; raw archive hashed only"
    except (OSError, ValueError, zipfile.BadZipFile, tarfile.TarError) as e:
        entry["error"] = str(e)
    archives.append(entry)

matches = [x for x in files if x.get("sha256") == EXPECTED]
for a in archives:
    if a.get("sha256") == EXPECTED:
        matches.append({"archive": a["path"]})
    matches += [{"archive": a["path"], **m} for m in a["members"] if m.get("sha256") == EXPECTED]
result = {"expected": EXPECTED, "excluded_directory_names": sorted(SKIP), "files": files,
          "archives": archives, "external_locations": locations, "walk_errors": errors,
          "matches": matches, "warning": "NOT FOUND applies only to readable searched material."}
(OUT / "local-search.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"candidate_files": len(files), "archives": len(archives),
                  "members_hashed": sum("sha256" in m for a in archives for m in a["members"]),
                  "archive_errors": [{"path": a["path"], "error": a["error"]} for a in archives if "error" in a],
                  "walk_errors": errors, "matches": matches}, indent=2))
