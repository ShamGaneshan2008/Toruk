"""Explicit posthoc assistant judgments of method-blinded unique answers."""

import hashlib
import json
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parent / "evaluation"
items = json.loads((RUN / "review-items-independent-utf8.json").read_text(encoding="utf-8"))
# These lists encode a completed manual reading of each unique answer against
# its source ledger. They are annotations, never an inference-time classifier.
supported = {2,9,15,29,30,36,40,61,64,65,68,71,72,86,87,89,93,97,100,102}
format_only = {13,17,19,35,39,42,43,45,46,51,52}
nonassertion = {3,5,6,8,10,16,24,25,31,32,34,37,38,41,44,55,57,69,73,76,77,78,79,84,85,94,95,96,98,99}
unsupported = {1,4,7,11,12,14,18,20,21,22,23,26,27,28,33,47,48,49,50,53,54,56,58,59,60,62,63,66,67,70,74,75,80,81,82,83,88,90,91,92,101,103}
assert len(supported | format_only | nonassertion | unsupported) == len(items) == 103
assert sum(map(len, (supported,format_only,nonassertion,unsupported))) == len(items)
special = {
    8: "An explicit [Studio Name] placeholder supplies no concrete contact; not a correct answer.",
    32: "Generic definition of an owner; no unsupported named owner is asserted.",
    44: "Generic ticket advice, not a claimed private seat identifier; not a correct answer.",
    49: "Purports to supply a serial string absent from the ledger; treated as an unsupported identifier.",
    55: "Repeats generic clarification instructions rather than asserting label content.",
    69: "Denies making a selection on the user's behalf; no specific chosen activity is supplied.",
    76: "Explicitly expresses insufficient referent information; does not select either locker.",
    81: "Recasts ambiguous 'she' as Neris without evidence resolving the referent.",
    86: "Friday is supported as a day; the requested time remains unknown. Primary failure retained.",
    87: "Friday is supported as a day; the requested time remains unknown. Primary failure retained.",
    88: "Binds Oren's appointment to the user without an established identity link.",
    89: "Verbatim true theatre/cushion side note in the full history; irrelevant, not an asserted replacement day.",
    93: "Correctly repeats the source's explicitly unlogged serial; primary uncertainty-matcher failure retained.",
    97: "Correctly repeats the source's explicitly unlogged serial; primary uncertainty-matcher failure retained.",
    100: "Correctly reports that the repair fee was not quoted; primary matcher result remains unchanged.",
    102: "Correctly reports that the repair fee was not quoted; primary matcher result remains unchanged.",
}
annotations = []
for item in items:
    index = int(item["id"].split("-")[1])
    if index in unsupported:
        label, note = "unsupported", "Asserts an unsupported, obsolete or incorrectly bound answer value."
    elif index in format_only:
        label, note = "format_only", "Source value is recognizable; literal formatting/copying fails separately."
    elif index in nonassertion:
        label, note = "nonassertion", "Refusal, uncertainty, generic advice or placeholder supplies no concrete world answer."
    else:
        label, note = "supported", "Asserted content follows the source ledger; relevance and frozen scoring are separate."
    annotations.append({**item,"classification":label,"unsupported_world_assertion":label=="unsupported","note":special.get(index,note)})
lookup = {(r["case"],r["answer"]):r for r in annotations}
rows=[]
summary=Counter({m:0 for m in ("recent","lexical","toruk","no_envelope","no_learned_rank","restore_cutoff")})
for line in (RUN/'independent.jsonl').read_text(encoding='utf-8').splitlines():
    raw=json.loads(line)
    annotation=lookup[raw['case']['id'],raw['answer']]
    rows.append({"suite":"independent","id":raw['case']['id'],"method":raw['method'],"answer":raw['answer'],"review_item":annotation['id'],"classification":annotation['classification'],"unsupported_world_assertion":annotation['unsupported_world_assertion'],"note":annotation['note']})
    summary[raw['method']]+=annotation['unsupported_world_assertion']
result={
    "status":"POSTHOC_ASSISTANT_REVIEW_NOT_INDEPENDENT_HUMAN_VALIDATION",
    "rule":"Asserted or implied answer bindings must follow the ledger and latest corrections. Refusal/uncertainty/generic advice and literal formatting errors are separate. True but irrelevant statements are not false world assertions.",
    "method_blinded_unique_answer_annotation":True,
    "primary_scores_unchanged":True,
    "bindings":{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (RUN/'independent.jsonl',RUN/'review-items-independent-utf8.json',Path(__file__))},
    "summary":dict(summary),"unique_annotations":annotations,"rows":rows,
}
with (RUN/'assertion-review-independent.json').open('x',encoding='utf-8') as f: json.dump(result,f,indent=2,ensure_ascii=False)
print(json.dumps(dict(summary),indent=2))
