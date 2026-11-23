"""Saved raw predictions and schedules only; no models or new answers."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[1]
OLD=ROOT/"artifacts/local-answer-paired-batch-dev-v1"
def read(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines()]

def main():
    labels=read(OLD/"train-labels.json")
    labelmap={r["id"]:r for r in labels}
    schedules=read(OLD/"batch-schedules.json")
    schedule_stats={}
    outcomes={}
    for seed in (601,947):
        for arm in ("original","city-shuffled","city-paired"):
            schedule=schedules[f"{seed}-{arm}"]
            contrasts=0
            for batch in schedule:
                city=defaultdict(set)
                for i in batch["ids"]:
                    r=labelmap[i]
                    if r["category"]=="city":
                        city[r["canonical"][0]].add(r["gold"])
                contrasts+=any(len(v)>1 for v in city.values())
            schedule_stats[f"{seed}-{arm}"]=dict(steps=len(schedule),
                batches_with_same_entity_city_contrasts=contrasts,
                presentations=Counter(i for b in schedule for i in b["ids"]))
            for variant in ("ordinary","recurrent"):
                identity=f"{seed}-{variant}-{arm}"
                fit=OLD/"stages"/("fit-"+identity)
                observation=OLD/"stages"/("analyze-"+identity)
                trace=rows(fit/"training.jsonl")
                assert all(t["ids"]==b["ids"] for t,b in zip(trace,schedule,strict=True))
                predictions=rows(observation/"predictions-main.jsonl")
                assert len(predictions)==97 and predictions[0]["result"]==predictions[-1]["result"]
                seal=read(observation/"seal-main.json")
                assert hashlib.sha256((observation/"predictions-main.jsonl").read_bytes()).hexdigest()==seal["sha256"]
                vectors={r["id"]:r for r in rows(observation/"city-first-token.jsonl")}
                exact=0
                wrong=[]
                for p,l in zip(predictions[:-1],labels,strict=True):
                    ids=p["result"]["generated_ids"]
                    assert p["id"]==l["id"]
                    exact+=ids==[*(b+3 for b in l["gold"].encode()),2]
                    if l["category"]=="city":
                        assert vectors[l["id"]]["predicted_first_id"]==ids[0]
                    if ids[0]!=l["gold"].encode()[0]+3:
                        wrong.append(dict(id=l["id"],canonical=l["canonical"],
                            gold=l["gold"],answer=p["result"]["answer"],
                            wrong_first_id=ids[0]))
                outcomes[identity]=dict(exact=exact,wrong_first=wrong)
    result=dict(status="PASS_SAVED_RAW_AND_SCHEDULE_JOINS",schedule_statistics=schedule_stats,
                outcomes=outcomes,new_model_forwards=0,new_generated_answers=0,
                interpretation="Contrasts already occurred in all schedules. Error migration and finite learned preferences do not establish a unique training cause.")
    with (RUN/"saved-diagnosis-supplement.json").open("x",encoding="utf-8",newline="\n") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(dict(status=result["status"],cells=len(outcomes),
                          new_model_forwards=0,new_generated_answers=0)))
if __name__=="__main__": main()
