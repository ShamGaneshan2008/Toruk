"""Train the existing eight-feature selector on v2 evidence labels."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import torch
from torch.nn import functional as F

from toruk_lm.chat_selector import FEATURES, FORMAT, ChatRelevanceSelector, features


def read_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def examples(cases: list[dict]) -> tuple[torch.Tensor, torch.Tensor]:
    x, y = [], []
    for case in cases:
        messages = case["messages"]
        for index, message in enumerate(messages[:-3]):
            if message["role"] == "user":
                x.append(features(messages[-1]["content"], message["content"], message["role"], index, len(messages)))
                y.append(float(index in case["evidence_ids"]))
    return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


def f1(scores: list[float], labels: list[float], threshold: float) -> float:
    tp = sum(s >= threshold and y == 1 for s, y in zip(scores, labels, strict=True))
    fp = sum(s >= threshold and y == 0 for s, y in zip(scores, labels, strict=True))
    fn = sum(s < threshold and y == 1 for s, y in zip(scores, labels, strict=True))
    return 2 * tp / max(1, 2 * tp + fp + fn)


def peak_working_set() -> int | None:
    if os.name != "nt":
        return None
    import ctypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        return counters.PeakWorkingSetSize
    try:
        return int(subprocess.check_output(["powershell", "-NoProfile", "-Command",
                                            f"(Get-Process -Id {os.getpid()}).PeakWorkingSet64"], text=True).strip())
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh checkpoint path")
    manifest_raw = (args.data_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest.get("format") != "toruk-chat-selector-data-v2":
        raise ValueError("wrong dataset format")
    for split in ("train", "dev"):
        if hashlib.sha256((args.data_dir / f"{split}.jsonl").read_bytes()).hexdigest() != manifest["split_sha256"][split]:
            raise ValueError(f"{split} hash mismatch")
    train, dev = (read_cases(args.data_dir / f"{split}.jsonl") for split in ("train", "dev"))
    if any(case["split"] != "train" for case in train) or any(case["split"] != "dev" for case in dev):
        raise ValueError("split label mismatch")
    if args.pilot:
        train = [case for case in train if case["history_length"] == "long"][:8]
    x, y = examples(train)
    dx, dy = examples(dev)
    torch.manual_seed(173)
    torch.set_num_threads(1)
    model = torch.nn.Linear(len(FEATURES), 1)
    with torch.no_grad():
        model.weight.zero_()
        model.bias.zero_()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.03)
    steps = 80 if args.pilot else 180
    curve = []
    started = time.perf_counter()
    for step in range(1, steps + 1):
        optimizer.zero_grad()
        loss = F.binary_cross_entropy_with_logits(model(x).squeeze(-1), y, pos_weight=torch.tensor(5.0))
        loss.backward()
        optimizer.step()
        if step == 1 or step % 20 == 0:
            curve.append({"step": step, "loss": round(float(loss.item()), 6)})
    with torch.no_grad():
        train_scores = torch.sigmoid(model(x).squeeze(-1)).tolist()
        dev_scores = torch.sigmoid(model(dx).squeeze(-1)).tolist()
    thresholds = [round(i * 0.05, 2) for i in range(2, 19)]
    threshold = max(thresholds, key=lambda t: (f1(dev_scores, dy.tolist(), t), t))
    checkpoint = {"format": FORMAT, "features": list(FEATURES),
                  "weights": model.weight.detach().squeeze(0).tolist(),
                  "bias": float(model.bias.detach().item()), "threshold": threshold,
                  "protocol": "chat-selector-v2", "data_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
                  "train_sha256": manifest["split_sha256"]["train"], "dev_sha256": manifest["split_sha256"]["dev"],
                  "training": {"pilot": args.pilot, "seed": 173, "steps": steps, "optimizer": "Adam",
                               "lr": 0.03, "objective": "weighted evidence-turn BCE", "positive_weight": 5,
                               "train_cases": len(train), "dev_cases": len(dev), "train_examples": len(y),
                               "dev_examples": len(dy), "curve": curve, "train_evidence_f1": f1(train_scores, y.tolist(), threshold),
                               "dev_evidence_f1": f1(dev_scores, dy.tolist(), threshold),
                               "seconds": round(time.perf_counter() - started, 4),
                               "peak_working_set_bytes": peak_working_set()}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    loaded = ChatRelevanceSelector(args.output)
    replay = [loaded.score(dev[0]["messages"][-1]["content"], dev[0]["messages"][0]["content"],
                           "user", 0, len(dev[0]["messages"])) for _ in range(2)]
    if replay[0] != replay[1]:
        raise AssertionError("checkpoint replay was not deterministic")
    print(json.dumps({"checkpoint_sha256": loaded.sha256, "threshold": threshold,
                      "replay_score": replay[0], "training": checkpoint["training"]}, indent=2))


if __name__ == "__main__":
    main()
