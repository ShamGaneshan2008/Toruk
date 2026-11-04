"""Prepare method-blinded unique answers using explicit UTF-8 on Windows."""

import json
from pathlib import Path

run = Path(__file__).resolve().parent / "evaluation"
for suite, prefix, name in (
    ("independent", "ind", "review-items-independent-utf8.json"),
    ("controlled", "ctrl", "review-items-controlled.json"),
):
    rows = [json.loads(line) for line in (run / f"{suite}.jsonl").read_text(encoding="utf-8").splitlines()]
    items = []
    for cid in dict.fromkeys(row["case"]["id"] for row in rows):
        current = [row for row in rows if row["case"]["id"] == cid]
        case = current[0]["case"]
        print("\nCASE", cid, "EXPECTED", case["groups"], "FORBIDDEN", case["forbidden"])
        for answer in sorted({row["answer"] for row in current}):
            item = {
                "id": f"{prefix}-{len(items)+1:03d}", "case": cid,
                "question": case["messages"][-1]["content"],
                "sources": [case["messages"][i] for i in case["evidence"]],
                "task": case["task"], "groups": case["groups"],
                "forbidden": case["forbidden"], "answer": answer,
            }
            items.append(item)
            if suite == "controlled":
                print(item["id"], json.dumps(answer, ensure_ascii=False))
    if suite == "independent":
        old = json.loads((run / "review-items-independent.json").read_text(encoding="utf-8"))
        assert len(old) == len(items) == 103
        assert all(a["id"] == b["id"] and a["case"] == b["case"] for a,b in zip(old, items, strict=True))
    with (run / name).open("x", encoding="utf-8") as stream:
        json.dump(items, stream, indent=2, ensure_ascii=False)
    print("UNIQUE ITEMS", suite, len(items))
