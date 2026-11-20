"""Audit v1 bytes and negative decisions from working files or a committed tree."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "artifacts/answer-trainability-dev-v1/"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args, data=None):
    return subprocess.check_output(["git", *args], cwd=ROOT, input=data)


def audit(revision=None):
    inventory_name = PREFIX + "artifact-inventory.json"
    raw_inventory = git("show", revision + ":" + inventory_name) if revision else (ROOT / inventory_name).read_bytes()
    inventory = json.loads(raw_inventory)
    tracked = [n for n,v in inventory["files"].items() if not v["local_ignored_checkpoint"]]
    if revision:
        listing = {}
        for entry in git("ls-tree", "-r", "-z", revision).split(b"\0"):
            if entry:
                metadata, name = entry.split(b"\t",1)
                listing[name.decode()] = metadata.split()[2]
        assert set(tracked) <= listing.keys()
        stream = git("cat-file","--batch",data=b"\n".join(listing[n] for n in tracked)+b"\n")
        blobs, offset = {}, 0
        for name in tracked:
            end=stream.index(b"\n",offset); size=int(stream[offset:end].split()[2]); offset=end+1
            blobs[name]=stream[offset:offset+size]; offset+=size+1
    else:
        blobs={n:(ROOT/n).read_bytes() for n in tracked}
    present_checkpoints=0
    for name, expected in inventory["files"].items():
        if expected["local_ignored_checkpoint"]:
            if not (ROOT/name).exists():
                continue
            raw=(ROOT/name).read_bytes(); present_checkpoints+=1
        else:
            raw=blobs[name]
        assert len(raw)==expected["bytes"] and sha(raw)==expected["sha256"],name
    def read(name):
        return json.loads(blobs[PREFIX+name])
    assert sha(blobs[PREFIX+"registration.json"])=="d019194831da0039008f39ff3c3060f4384af3587cf5fa45f844a1ae56dc27a2"
    s, cost, ledger=read("summary.json"),read("execution/cost.json"),read("poststudy-accounting.json")
    assert s["decision"]=="STOP_GENERALIZATION_FAILURE" and not any(s["development_pass"].values())
    assert all(s["eligible"].values()) and sum(v["exact"] for k,v in s["metrics"].items() if k.startswith("dev-"))==49
    assert cost["status"]=="STOP" and cost["failure"]=="worker cost receipt missing"
    assert ledger["complete_lifetime_cpu"].startswith("UNKNOWN") and ledger["known_disjoint_cpu_lower_bound"]==300.109375
    assert inventory["formal_registered_envelope"].startswith("STOP")
    return dict(status="PASS",scope=revision or "working files",inventory_files=len(inventory["files"]),
                committed_inventory_entries=len(tracked),local_checkpoints_checked=present_checkpoints,
                inventory_sha256=sha(raw_inventory),raw_scores_unchanged=True,development_pass=False,
                registered_envelope_valid=False,complete_lifetime_cpu="UNKNOWN",training_or_generation_executed=False)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--revision"); parser.add_argument("--output",type=Path)
    options=parser.parse_args(); result=audit(options.revision)
    if options.output:
        with options.output.open("x",encoding="utf-8",newline="\n") as f: json.dump(result,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(result,sort_keys=True))
