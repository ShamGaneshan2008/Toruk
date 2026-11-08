"""Offline human-coded review; never imported by selection, generation or training."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
historical = json.loads((OUT / "historical-audit.json").read_bytes())
fixture = json.loads((ROOT / "configs/chat-release-eval-v2.json").read_bytes())
cases = {case["id"]: case for case in fixture["cases"]}
notes = {
    "instruction_digit": "Digit is correct but extra prose violates exact-output instruction.",
    "reference_nickname": "Name-bearing m0 retained; refusal does not establish a coreference error.",
    "reference_codename": "ORBIT-bearing m0 retained; copies assistant acknowledgement instead.",
    "user_fact_drink": "Mint-tea evidence retained; cold-drink preference is unsupported.",
    "user_fact_pet": "Pippa-bearing m0 retained; internet-access refusal is irrelevant.",
    "correction_day": "Thursday correction m2 retained; acknowledgement is not an answer.",
    "preserve_city": "Quito-bearing m0 retained; acknowledgement omits the city.",
    "preserve_hobby": "Chess is correct, but appends obsolete Monday despite Friday in m2.",
    "long_key": "CEDAR-19-bearing m0 retained in both modes; acknowledgement omits key.",
    "irrelevant_arithmetic": "Latest turn supplies operands; arithmetic not answered correctly.",
    "irrelevant_fact": "Latest turn asks public knowledge; irrelevant answer/refusal despite intact query.",
    "unknown_pin": "No PIN asserted; reasonable refusal missed by frozen uncertainty phrase list.",
    "unknown_maiden": "No name asserted; reasonable refusal missed by frozen uncertainty phrase list.",
    "ambiguous_season": "Both conflicting notes retained; guesses spring without resolving uncertainty.",
}
review = []
for row in historical["rows"]:
    if row["score"]["quality"]:
        continue
    key = row["id"]
    cause = ("stale fact used" if key == "preserve_hobby" else
             "unsupported question answered as fact" if key == "ambiguous_season" else
             "evidence present but generator failed")
    required = ["m0"]
    if key == "correction_day":
        required = ["m2"]
    elif key in ("preserve_hobby", "ambiguous_season"):
        required = ["m0", "m2"]
    elif key.startswith("irrelevant_"):
        required = [cases[key]["messages"][-1]["id"]]
    assert set(required) <= set(row["metrics"]["selected_message_ids"])
    review.append({"id": key, "mode": row["mode"], "cause": cause,
                   "rubric_false_negative": key.startswith("unknown_"),
                   "required_source_ids": required, "notes": notes[key],
                   "answer": row["answer"], "selected_sources": row["selected_sources"]})
counts = {mode: dict(Counter(r["cause"] for r in review if r["mode"] == mode))
          for mode in ("BASELINE", "TORUK")}
latest = json.loads((OUT / "latest-archive-audit.json").read_bytes())["latest_launch_archive"]
latest_review = []
for name, method in latest["methods"].items():
    for row in method["rows"]:
        if not row.get("scored_final_turn", True) or row["score"]["quality"]:
            continue
        category = row["category"]
        stale = category == "correction"
        rubric = category in ("uncertainty", "refusal", "repetition", "generated-conflict")
        messages = row["request"]["messages"]
        indices = [int(s[1:]) for s in row["response"]["metrics"]["selected_message_ids"]]
        latest_review.append({"method": name, "id": row["id"],
            "cause": "stale fact used" if stale else "evidence present but generator failed",
            "rubric_false_negative": rubric, "answer": row["content"],
            "notes": ("Obsolete value repeated with correction present." if stale else
                      "Semantically valid uncertainty/math/conflict reply missed by phrase/number rubric."
                      if rubric else "Instruction literal or evidence literal changed by generator."),
            "selected_sources": [{"id": f"m{i}", **messages[i]} for i in indices]})
data = {"scope": "Offline interpretive review; labels do not establish internal model causality.",
        "historical_failure_counts_per_mode": counts, "historical_wrong_rows": review,
        "historical_false_assertion_review": {
            "scope": "Task-related factual assertions, not generic assistant-capability statements.",
            "each_mode": {"stale_assertion": 1, "unsupported_preference": 1, "unsupported_season_guess": 1},
            "unknown_refusals_fabricating_private_values": 0,
            "warning": "Frozen unsupported proxy is 3 per mode; these are different reviewed events."},
        "latest_wrong_scored_rows": latest_review,
        "latest_counts": {name: dict(Counter(r["cause"] for r in latest_review if r["method"] == name))
                          for name in latest["methods"]},
        "latest_rubric_false_negatives": {name: sum(r["rubric_false_negative"] for r in latest_review
                                                  if r["method"] == name) for name in latest["methods"]}}
(OUT / "failure-review.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
lines = ["# Wrong historical answers: offline review", "",
         "Both modes have 14 wrong scored answers. This is saved-output analysis, not new TORUK inference.", "",
         "| Case | Mode | Cause | Raw answer | Rationale |", "|---|---|---|---|---|"]
for row in review:
    cells = [row["id"], row["mode"], row["cause"], row["answer"], row["notes"]]
    lines.append("| " + " | ".join(s.replace("|", "\\|").replace("\n", " ") for s in cells) + " |")
(OUT / "failure-review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"historical": counts, "latest": data["latest_counts"],
                  "latest_rubric_false_negatives": data["latest_rubric_false_negatives"]}, indent=2))
