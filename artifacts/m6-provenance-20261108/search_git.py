"""Hash all local Git blob payloads, including unreachable objects, without checkout/reset."""
import hashlib
import io
import json
import subprocess
import tarfile
import zipfile
from pathlib import Path

EXPECTED = "479c5ee26ff907783018fcaf9004d2b072610793f019648735d7405bc2ec156d"
OUT = Path(__file__).resolve().parent
objects = subprocess.check_output(
    ["git", "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
    text=True,
).splitlines()
reachable = subprocess.check_output(["git", "rev-list", "--all", "--reflog", "--objects"], text=True)
paths = {}
for line in reachable.splitlines():
    oid, _, path = line.partition(" ")
    if path:
        paths.setdefault(oid, []).append(path)
batch = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
blobs, references, archives, matches, pointers = [], [], [], [], []
for line in objects:
    oid, kind, size = line.split()
    if kind != "blob":
        continue
    batch.stdin.write((oid + "\n").encode())
    batch.stdin.flush()
    header = batch.stdout.readline().decode().split()
    payload = batch.stdout.read(int(header[2]))
    assert len(payload) == int(size)
    assert batch.stdout.read(1) == b"\n"
    digest = hashlib.sha256(payload).hexdigest()
    item = {"object": oid, "bytes": len(payload), "sha256": digest, "paths": paths.get(oid, [])}
    blobs.append(item)
    if digest == EXPECTED:
        matches.append(item)
    if EXPECTED.encode() in payload:
        references.append(item)
    if payload.startswith(b"version https://git-lfs.github.com/spec/v1"):
        pointers.append({**item, "pointer": payload.decode(errors="replace")})
    stream = io.BytesIO(payload)
    members = []
    if zipfile.is_zipfile(stream):
        with zipfile.ZipFile(stream) as z:
            for info in z.infolist():
                if not info.is_dir():
                    with z.open(info) as member:
                        members.append({"name": info.filename, "bytes": info.file_size,
                                        "sha256": hashlib.file_digest(member, "sha256").hexdigest()})
    elif payload.startswith(b"\x1f\x8b"):
        try:
            with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tar:
                for info in tar:
                    if info.isfile():
                        with tar.extractfile(info) as member:
                            members.append({"name": info.name, "bytes": info.size,
                                            "sha256": hashlib.file_digest(member, "sha256").hexdigest()})
        except tarfile.TarError:
            pass
    if members:
        archives.append({**item, "members": members})
        matches += [{"git_archive_object": oid, **m} for m in members if m["sha256"] == EXPECTED]
batch.stdin.close()
assert batch.wait() == 0
result = {"expected": EXPECTED, "scope": "all Git blob objects, including unreachable/reflog-only",
          "blob_payloads": blobs, "hash_references": references, "archives": archives,
          "lfs_pointers": pointers, "matches": matches}
(OUT / "git-object-search.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"blobs_hashed": len(blobs), "bytes_hashed": sum(x["bytes"] for x in blobs),
                  "archive_objects": len(archives), "archive_members_hashed": sum(len(a["members"]) for a in archives),
                  "hash_reference_blobs": len(references), "lfs_pointers": len(pointers), "matches": matches}))
