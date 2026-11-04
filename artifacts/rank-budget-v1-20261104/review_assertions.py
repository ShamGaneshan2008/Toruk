"""Retain explicit posthoc assistant annotations; never change primary scores."""

import hashlib
import json
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parent
PREVIOUS = RUN.parent / "recall-v2-20261104/assertion-review.json"
prior = json.loads(PREVIOUS.read_text(encoding="utf-8"))
lookup = {(row["id"], row["method"]): row for row in prior["rows"]}
# Explicit assistant judgments after reading the complete new answers and source
# histories. Unchanged answers inherit the prior review, not a new adjudication.
changed = {
    "v2-heldout-exact_code": (False, "The exact unlock string is supported by source turn 0."),
    "v2-heldout-exact_code_gap": (False, "The exact unlock string is supported by source turn 0."),
    "v2-heldout-correction": (True, "Asserts obsolete-2-3 despite the later explicit revision."),
    "v2-heldout-preservation": (False, "Returns the unchanged unlock string, not the launch date."),
    "v2-heldout-gist": (False, "Retention during outage and retry online are supported; no added policy."),
    "v2-heldout-clear": (False, "Returns the only candidate's source unlock string."),
    "v2-heldout-ambiguous": (True, "Binds the vague referent to one of two plausible projects without clarification."),
    "v2-heldout-missing": (False, "Explicitly lacks information; asserts no private locker combination."),
}
rows = []
for line in (RUN / "heldout.jsonl").read_text(encoding="utf-8").splitlines():
    raw = json.loads(line)
    key = raw["case"]["id"], raw["method"]
    old = lookup[key]
    same = raw["answer"] == old["answer"]
    if same:
        flag, note = old["unsupported_world_assertion"], old["note"]
    else:
        assert raw["method"] == "new"
        flag, note = changed[key[0]]
    rows.append({
        "id": key[0], "method": "candidate" if key[1] == "new" else key[1],
        "answer": raw["answer"], "unsupported_world_assertion": flag,
        "note": note, "annotation": "inherited identical answer" if same else "new assistant review",
    })
for old in prior["rows"]:
    if old["method"] == "new":
        rows.append({**old, "method": "envelope_before", "annotation": "prior assistant review"})
counts = Counter({method: 0 for method in ("recent", "lexical", "old", "envelope_before", "candidate")})
for row in rows:
    counts[row["method"]] += row["unsupported_world_assertion"]
result = {
    "status": "POSTHOC_NONPRIMARY_REVIEW",
    "rule": prior["rule"],
    "primary_scores_unchanged": True,
    "prior_baseline_annotations_inherited": True,
    "summary": dict(counts),
    "bindings": {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (PREVIOUS, RUN / "heldout.jsonl", Path(__file__))
    },
    "rows": rows,
}
with (RUN / "assertion-review.json").open("x", encoding="utf-8") as stream:
    json.dump(result, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(json.dumps(dict(counts), indent=2))
