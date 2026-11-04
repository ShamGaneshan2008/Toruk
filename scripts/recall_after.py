"""Run the sealed study after freezing its additive provenance-envelope intervention."""

import json
import sys
from pathlib import Path

import recall_study

from toruk_lm.source_spans import SourceEnvelopeBackend

if __name__ == "__main__":
    run = Path(sys.argv[sys.argv.index("--run") + 1])
    action = sys.argv[1]
    seal_path = run / "execution-seal.json"
    if action != "freeze":
        frozen = json.loads(seal_path.read_text(encoding="utf-8"))
        for name, digest in frozen.items():
            if recall_study.sha(Path(name)) != digest:
                raise ValueError("execution input drift")
        if action == "heldout":
            rows = (run / "development.jsonl").read_text(encoding="utf-8").splitlines()
            if len(rows) != 48 or not (run / "development-cost.json").exists():
                raise ValueError("complete development before opening heldout")
    recall_study.PretrainedChatBackend = SourceEnvelopeBackend
    recall_study.main()
    if action == "freeze":
        files = [
            Path(__file__),
            Path("tests/test_recall_protocol.py"),
            run / "before.jsonl",
            run / "intervention.md",
        ]
        recall_study.write(seal_path, {str(path): recall_study.sha(path) for path in files})
