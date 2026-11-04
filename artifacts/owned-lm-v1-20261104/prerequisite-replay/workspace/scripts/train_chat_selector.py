"""Train the v1 lexical turn ranker using train and development splits only."""

import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
from torch.nn import functional as F

from toruk_lm.chat_selector import FEATURES, FORMAT, features


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def examples(cases: list[dict]) -> tuple[torch.Tensor, torch.Tensor]:
    x, y = [], []
    for case in cases:
        messages = case["messages"]
        for index, message in enumerate(messages[:-3]):
            if message["role"] == "user":
                x.append(
                    features(
                        messages[-1]["content"],
                        message["content"],
                        message["role"],
                        index,
                        len(messages),
                    )
                )
                y.append(float(index in case["evidence_ids"]))
    return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)


def f1_at(scores: list[float], labels: list[float], threshold: float) -> float:
    tp = sum(score >= threshold and label == 1 for score, label in zip(scores, labels, strict=True))
    fp = sum(score >= threshold and label == 0 for score, label in zip(scores, labels, strict=True))
    fn = sum(score < threshold and label == 1 for score, label in zip(scores, labels, strict=True))
    return 2 * tp / max(1, 2 * tp + fp + fn)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("use a fresh checkpoint path")
    manifest = json.loads((args.data_dir / "manifest.json").read_text(encoding="utf-8"))
    for split in ("train", "dev"):
        raw = (args.data_dir / f"{split}.jsonl").read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["split_sha256"][split]:
            raise ValueError(f"{split} hash mismatch")
    train = rows(args.data_dir / "train.jsonl")
    dev = rows(args.data_dir / "dev.jsonl")
    if any(case["split"] != "train" for case in train) or any(
        case["split"] != "dev" for case in dev
    ):
        raise ValueError("split label mismatch")
    x, y = examples(train)
    dx, dy = examples(dev)
    torch.manual_seed(73)
    torch.set_num_threads(1)
    model = torch.nn.Linear(len(FEATURES), 1)
    with torch.no_grad():
        model.weight.zero_()
        model.bias.zero_()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.03)
    started = time.perf_counter()
    for _ in range(120):
        optimizer.zero_grad()
        loss = F.binary_cross_entropy_with_logits(
            model(x).squeeze(-1), y, pos_weight=torch.tensor(5.0)
        )
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        scores = torch.sigmoid(model(dx).squeeze(-1)).tolist()
    labels = dy.tolist()
    thresholds = [round(i * 0.05, 2) for i in range(2, 19)]
    threshold = max(thresholds, key=lambda t: (f1_at(scores, labels, t), t))
    checkpoint = {
        "format": FORMAT,
        "features": list(FEATURES),
        "weights": model.weight.detach().squeeze(0).tolist(),
        "bias": float(model.bias.detach().item()),
        "threshold": threshold,
        "training": {
            "seed": 73,
            "steps": 120,
            "optimizer": "Adam",
            "lr": 0.03,
            "objective": "class-weighted binary cross entropy on evidence turns",
            "positive_weight": 5,
            "train_cases": len(train),
            "dev_cases": len(dev),
            "train_examples": len(y),
            "dev_examples": len(dy),
            "final_train_loss": round(float(loss.item()), 6),
            "dev_evidence_f1": round(f1_at(scores, labels, threshold), 6),
            "seconds": round(time.perf_counter() - started, 3),
        },
        "data_manifest_sha256": hashlib.sha256(
            (args.data_dir / "manifest.json").read_bytes()
        ).hexdigest(),
        "train_sha256": manifest["split_sha256"]["train"],
        "dev_sha256": manifest["split_sha256"]["dev"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "checkpoint_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "training": checkpoint["training"],
                "threshold": threshold,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
