"""Single-use pre-training protocol seal; no model or old dataset is loaded."""
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path

started = time.perf_counter()
root = Path(__file__).resolve().parent
repo = root.parents[1]
sys.path.insert(0, str(repo / "scripts"))
from segment_delta_data import sha, validate
from segment_delta_watch import worker_receipt, write
from toruk_lm.tokenizer import ByteTokenizer

validate(*[json.loads((root / name).read_text()) for name in (
    "train.json", "inputs.json", "labels-evaluator-only.json", "dev-prose.json")])
sources = ["docs/research/segment-delta-dev-v1-protocol.md",
           "docs/research/toruk-custom-lm-architecture-decision-v2.md",
           "scripts/segment_delta_data.py", "scripts/segment_delta_watch.py",
           "src/toruk_lm/model.py", "src/toruk_lm/recurrent.py", "src/toruk_lm/owned_lm.py",
           "src/toruk_lm/owned_training.py", "src/toruk_lm/engine.py",
           "src/toruk_lm/tokenizer.py", "pyproject.toml"]
manifest = {p: sha(repo / p) for p in sources}
snapshot = root / "protocol-sources"
snapshot.mkdir()
for name in sources:
    target = snapshot / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((repo / name).read_bytes())
stages = [(seed, variant) for seed, order in (
    (113, ("ordinary", "recurrent", "delta")),
    (227, ("delta", "recurrent", "ordinary"))) for variant in order]
write(root / "registration.json", dict(
    registration="segment-delta-dev-v1", client_date="2026-11-13",
    head="ab6d3a65538b5f33d17efe4f45189906f1394a38",
    protocol_sha256=manifest[sources[0]], source_files=manifest,
    data={p.name: sha(p) for p in root.glob("*.json") if p.name in (
        "train.json", "inputs.json", "labels-evaluator-only.json", "dev-prose.json", "data-manifest.json")},
    tokenizer=dict(identity=ByteTokenizer.identity, fingerprint=ByteTokenizer.fingerprint),
    runtime=dict(python=platform.python_version(), torch=importlib.metadata.version("torch"),
                 psutil=importlib.metadata.version("psutil"), platform=platform.platform()),
    config=dict(context=24, width=16, heads=4, layers=1, rank=8, ff=116, slots=4, maximum=192),
    parameters=dict(ordinary=13914, recurrent=14288, delta=14277),
    train=dict(steps=128, batch=2, learning_rate=.003, betas=[.9,.999], eps=1e-8,
               weight_decay=.01, clip=1., foreach=False, fused=False, seeds=[113,227]),
    fit_order=stages, decode=dict(greedy=True, max_new_tokens=8, eos=2, suppress=[0,1]),
    caps=dict(fit_seconds=150, eval_seconds=20, score_seconds=20, request_seconds=1.5,
              prepare_seconds=60, tests_seconds=60, seal_seconds=20, controller_seconds=60,
              total_seconds=1500, private_bytes=2*1024**3, disk_bytes=128*1024**2, monitor_gap=5),
    rehearsal_files={p.relative_to(root).as_posix():sha(p) for p in (
        root/"rehearsal-numeric.json", root/"rehearsal/worker.json",
        root/"rehearsal-002-numeric.json", root/"rehearsal-002/cost.json")},
    status="FROZEN_BEFORE_IMPLEMENTATION_AND_TRAINING",
))
print("registration_sha256", sha(root / "registration.json"))
worker_receipt(root / "prepare", started, 0.)
