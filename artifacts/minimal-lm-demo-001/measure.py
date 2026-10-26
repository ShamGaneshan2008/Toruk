"""Frozen, read-only measurements for the minimal LM demo."""

import json
import math
import sys
from collections import Counter
from pathlib import Path

import torch

from toruk_lm.data import batch, read_documents, sha256_file, windows
from toruk_lm.engine import load_checkpoint, load_model, setup
from toruk_lm.model import CausalLM, ModelConfig, generate, loss_sum
from toruk_lm.tokenizer import ByteTokenizer
from toruk_lm.validation import read_config


ROOT = Path(__file__).resolve().parent
CONFIG = Path("configs/minimal-lm-demo-v1.json")
phase = sys.argv[1]
if phase not in ("baseline", "trained"):
    raise SystemExit("usage: measure.py baseline|trained")

model_config, training_config = read_config(CONFIG)
setup(training_config.seed, training_config.threads)
model = CausalLM(model_config) if phase == "baseline" else load_model(ROOT / "train/checkpoint.pt")
model.eval()


def score(path: Path) -> dict:
    examples = windows(read_documents(path), model.config.context)
    loss, correct, count = 0.0, 0, 0
    with torch.no_grad():
        for start in range(0, len(examples), 4):
            x, y = batch(examples[start : start + 4])
            logits = model(x)
            summed, valid = loss_sum(logits, y)
            mask = y.ne(-100)
            loss += float(summed)
            correct += int((logits.argmax(-1)[mask] == y[mask]).sum())
            count += valid
    return {
        "tokens": count,
        "loss_nats_per_token": loss / count,
        "perplexity": math.exp(loss / count),
        "top1_accuracy": correct / count,
    }


train_path = ROOT / "data/train.jsonl"
validation_path = ROOT / "data/validation.jsonl"
training_targets = [target for _, ys in windows(read_documents(train_path), model.config.context) for target in ys]
majority = Counter(training_targets).most_common(1)[0][0]
heldout_targets = [target for _, ys in windows(read_documents(validation_path), model.config.context) for target in ys]
prompt = "abc "
ids = generate(model, [ByteTokenizer.bos_id, *ByteTokenizer().encode(prompt)], 16)
result = {
    "phase": phase,
    "config_sha256": sha256_file(CONFIG),
    "train_sha256": sha256_file(train_path),
    "validation_sha256": sha256_file(validation_path),
    "parameters": sum(parameter.numel() for parameter in model.parameters()),
    "train": score(train_path),
    "validation": score(validation_path),
    "majority_training_target_id": majority,
    "majority_validation_accuracy": heldout_targets.count(majority) / len(heldout_targets),
    "prompt": prompt,
    "sample_ids": ids,
    "sample": ByteTokenizer().decode(ids),
    "python": sys.version.split()[0],
    "torch": torch.__version__,
}
if phase == "trained":
    saved = load_checkpoint(ROOT / "train/checkpoint.pt")
    result["checkpoint_sha256"] = sha256_file(ROOT / "train/checkpoint.pt")
    result["checkpoint_next_step"] = saved["next_step"]
    result["checkpoint_datasets"] = saved["datasets"]
target = ROOT / f"{phase}.json"
target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
