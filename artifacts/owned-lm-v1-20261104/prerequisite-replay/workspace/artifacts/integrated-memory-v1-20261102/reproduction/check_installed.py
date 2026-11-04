"""Replay six sealed answers from an installed wheel without importing the checkout."""

import json
import sys
from pathlib import Path

import torch
import toruk_lm.integrated_memory as runtime
from toruk_lm.data import sha256_file
from toruk_lm.integrated_study import file_identity

root = Path(sys.argv[1]).resolve()
assert Path(runtime.__file__).is_relative_to(Path(sys.prefix))
torch.set_num_threads(1)
frozen = json.loads((root / "freeze.json").read_text())
assert file_identity(Path(runtime.__file__)) == frozen["files"]["src/toruk_lm/integrated_memory.py"]
checkpoint = root / "train/integrated-31.pt"
model, _ = runtime.load_integrated(checkpoint)
rows = [json.loads(line) for line in (root / "data/final.jsonl").read_text().splitlines()]
saved = {row["id"]: row for row in json.loads((root / "final/integrated-31.json").read_text())["predictions"]}
selected = [next(row for row in rows if row["category"] == category)
            for category in ("correction", "preservation", "long_recall", "local", "unknown", "conflict")]
for row in selected:
    session = runtime.IntegratedSession(model, sha256_file(checkpoint))
    for event in row["events"]:
        session.consume(event["text"])
    assert session.answer(row["query"]) == saved[row["id"]]["generated_ids"]
record = {"installed_runtime": str(runtime.__file__), "sealed_source_matches": True,
          "generated_token_parity_cases": len(selected), "all_exact": True}
(root / "reproduction/installed-parity.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record))
