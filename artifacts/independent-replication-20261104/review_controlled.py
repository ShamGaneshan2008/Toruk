"""Explicit method-blinded controlled-answer review and exhaustive merge."""

import hashlib
import json
from collections import Counter
from pathlib import Path

run = Path(__file__).resolve().parent / "evaluation"
items = json.loads((run / "review-items-controlled.json").read_text(encoding="utf-8"))
unsupported = {1,2,4,5,7,11,12,13,16,17,18,20,22,26,28,30,32,35,36,37,39,40,41,42,43}
supported = {3,6,14,19,23,27,29,33,34,38}
format_only = {9,10}
nonassertion = {8,15,21,24,25,31,44,45,46,47,48}
assert len(unsupported | supported | format_only | nonassertion) == len(items) == 48
assert sum(map(len,(unsupported,supported,format_only,nonassertion))) == 48
special = {
    16:"Returns the superseded unlock string despite its explicit revision.",
    26:"Adds an unrecorded message-review procedure as Marigold6's behavior.",
    28:"Adds recipient-acknowledgment delivery behavior absent from the source.",
    30:"Adds a 24-hour retention limit absent from the source, despite a primary gist pass.",
    32:"Adds an unrecorded message-review procedure as Marigold7's behavior.",
    33:"Retains/retries the recorded messages; awkward timing wording is not treated as a new policy here.",
    40:"Chooses a code without resolving which of two projects the pronoun denotes.",
    45:"Refuses to supply a locker combination. The generic reason about projects is outside this answer-binding review's scope.",
    48:"Normative advice about storing a locker, not an asserted private combination.",
}
annotations=[]
for item in items:
    index=int(item['id'].split('-')[1])
    if index in unsupported:
        classification,note='unsupported','Unsupported or incorrectly bound answer value or extra policy assertion.'
    elif index in format_only:
        classification,note='format_only','Motto copying/formatting error; distinct from invented world facts.'
    elif index in supported:
        classification,note='supported','Source ledger supports the asserted answer content; rubric completeness is separate.'
    else:
        classification,note='nonassertion','Refusal, uncertainty, generic advice or nonanswer; no concrete target value is asserted.'
    annotations.append({**item,'classification':classification,'unsupported_world_assertion':classification=='unsupported','note':special.get(index,note)})
lookup={(a['case'],a['answer']):a for a in annotations}
rows=[]
summary=Counter({m:0 for m in ('recent','lexical','toruk','no_envelope','no_learned_rank','restore_cutoff')})
for line in (run/'controlled.jsonl').read_text(encoding='utf-8').splitlines():
    raw=json.loads(line); a=lookup[raw['case']['id'],raw['answer']]
    rows.append({'suite':'controlled','id':raw['case']['id'],'method':raw['method'],'answer':raw['answer'],'review_item':a['id'],'classification':a['classification'],'unsupported_world_assertion':a['unsupported_world_assertion'],'note':a['note']})
    summary[raw['method']]+=a['unsupported_world_assertion']
independent=json.loads((run/'assertion-review-independent.json').read_text(encoding='utf-8'))
result={
    'status':independent['status'],
    'rule':independent['rule'],
    'scope':'Target answer bindings and identifiable added policies; not a complete semantic audit of generic/refusal commentary. Exact deviations scored separately.',
    'method_blinded_unique_answer_annotation':True,
    'primary_scores_unchanged':True,
    'summary':{'controlled':dict(summary),'independent':independent['summary']},
    'unique_annotations':annotations+independent['unique_annotations'],
    'rows':rows+independent['rows'],
    'bindings':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (run/'controlled.jsonl',run/'independent.jsonl',run/'review-items-controlled.json',run/'assertion-review-independent.json',Path(__file__))},
}
assert len(result['rows'])==216
with (run/'assertion-review.json').open('x',encoding='utf-8') as f: json.dump(result,f,indent=2,ensure_ascii=False)
print(json.dumps(result['summary'],indent=2))
