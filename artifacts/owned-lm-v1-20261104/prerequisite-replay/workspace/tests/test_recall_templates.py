"""Task-bearing template separation, independent worlds and fixed task counts."""

import importlib.util
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("recall_v2", SCRIPTS / "recall_v2.py")
assert SPEC and SPEC.loader
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


def skeleton(text: str) -> str:
    text = re.sub(r"[TDH]/\d+: 9_x!|obsolete-\d+-\d+|204\d-\d\d-\d\d", "VALUE", text)
    text = re.sub(r"Larch\d+|Zephyr\d+|Marigold\d+|Aster\d+|Beryl\d+|Nacre\d+", "ENTITY", text)
    text = re.sub(r"Tavian|Seren|Ysolde", "PERSON", text)
    text = re.sub(r"Keep;  calm!|Count:  four beats!|Wait\?  Five turns\.", "MOTTO", text)
    return text


def test_task_templates_are_disjoint_and_worlds_unique() -> None:
    templates = []
    histories = set()
    for split in ("training", "development", "heldout"):
        rows = study.strict_cases(split)
        assert len(rows) == 12
        current = set()
        for row in rows:
            history = tuple(message["content"] for message in row["messages"])
            assert history not in histories
            histories.add(history)
            current.add(skeleton(row["messages"][-1]["content"]))
            for index in row["evidence"]:
                current.add(skeleton(row["messages"][index]["content"]))
            assert len(row["messages"]) <= 64
            assert sum(len(m["content"].encode()) for m in row["messages"]) <= 16384
        templates.append(current)
    for i in range(3):
        for j in range(i):
            assert not templates[i] & templates[j]
