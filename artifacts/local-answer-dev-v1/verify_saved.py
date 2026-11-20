"""Independent offline audit of the stopped run, without model execution."""

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[1]


def read(path): return json.loads(path.read_text(encoding="utf-8"))
def lines(path): return [json.loads(s) for s in path.read_text().splitlines()]
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def require(condition,message):
    if not condition: raise ValueError(message)


def audit():
    reg=read(RUN/"registration.json"); summary=read(RUN/"summary.json"); outer=read(RUN/"execution/cost.json")
    require(digest(RUN/"registration.json")=="c11e16cb45dfe116f3f45f2c2e3412f7e26930e2f0db0a607784f4eae54253b4","registration")
    for name,expected in reg["sources"].items():
        require(digest(RUN/"sources"/name)==digest(ROOT/name)==expected,"source: "+name)
    for name,expected in reg["data"].items():require(digest(RUN/name)==expected,"data: "+name)
    require(outer["status"]=="PASS" and outer["complete_process_lifetimes"] and outer["active_processes"]==0,"outer lifetime accounting")
    require(outer["cpu"]==outer["user_cpu"]+outer["kernel_cpu"],"kernel CPU sum")
    require(read(RUN/"execution/controller-final.json")["status"]=="PASS","controller finally")
    documents=read(RUN/"train-documents.json"); lookup={d["id"]:d for d in documents}
    labels=read(RUN/"train-labels.json"); inputs=read(RUN/"train-inputs.json")
    expected_targets=sum(len(d["text"].encode())+1 for d in documents)*128
    refs={}; cells={}; actual_gate=True; expected_failures=[]
    for seed,variant in reg["order"]:
        name=f"{seed}-{variant}"; train=RUN/"stages"/f"train-{name}"
        trace=lines(train/"training.jsonl"); stats=read(train/"training-summary.json")
        require(len(trace)==1536 and [r["step"] for r in trace]==list(range(1,1537)),"steps")
        signature=[(r["ids"],r["history_targets"],r["answer_targets"],r["forward_positions"]) for r in trace]
        require(signature==refs.setdefault(seed,signature),"matched exposure/work")
        require(Counter(i for row in trace for i in row["ids"])==Counter({d["id"]:128 for d in documents}),"presentation counts")
        for row in trace:
            count=sum(len(lookup[i]["text"].encode())+1 for i in row["ids"])
            answers=sum(len(lookup[i]["gold"].encode())+1 for i in row["ids"])
            require(row["history_targets"]+row["answer_targets"]==count and row["answer_targets"]==answers,"target count")
            require(math.isfinite(row["objective"]) and math.isfinite(row["gradient_norm"]),"finite trajectory")
            require(math.isclose(row["objective"],(row["history_loss"]+row["answer_loss"])/count,rel_tol=1e-6),"uniform CE")
        require(stats["targets"]==expected_targets,"total targets")
        checkpoint=train/"checkpoint.pt"; meta=read(train/"checkpoint-meta.json")
        require(digest(checkpoint)==meta["sha256"] and checkpoint.stat().st_size==meta["bytes"],"checkpoint bytes")
        pred=RUN/"stages"/f"generate-train-{name}"/"predictions.jsonl"; predictions=lines(pred)
        require(len(predictions)==97 and predictions[0]["result"]==predictions[-1]["result"] and predictions[-1]["replay"],"replay")
        require(digest(pred)==read(pred.parent/"seal.json")["sha256"],"prediction seal")
        totals=Counter(); categories=Counter(); templates=Counter(); failures=[]
        for line,(p,case,label) in enumerate(zip(predictions[:-1],inputs,labels,strict=True),1):
            require(p["id"]==case["id"]==label["id"] and p["prefix"]==case["prefix"],"case/prefix")
            require(p["input_ids"]==[1,*(b+3 for b in case["prefix"].encode())],"native prompt")
            ids=p["result"]["generated_ids"]; gold_ids=[*(b+3 for b in label["gold"].encode()),2]
            correct=ids==gold_ids
            closed=any(ids==[*(b+3 for b in value.encode()),2] for value in ("la","mi","so","tu","R-7","Q_2","V:4","Z!6","?"))
            repeated=any(ids[i:i+w]*3==ids[i:i+3*w] for w in (1,2) for i in range(len(ids)-3*w+1))
            totals.update(dict(exact=int(correct),eos=int(ids[-1]==2),malformed=int(not closed),repetitive=int(repeated)))
            categories[label["category"]]+=int(correct); templates[label["template"]]+=int(correct)
            if not correct:failures.append(dict(id=label["id"],gold=label["gold"],canonical=label["canonical"],template=label["template"],
                ids=ids,raw=bytes(t-3 for t in ids if t>=3).decode(),eos=ids[-1]==2,malformed=not closed,
                wrong_first_byte=ids[0]!=gold_ids[0],source=f"{pred.relative_to(ROOT).as_posix()}:{line}"))
        metrics=summary["results"][f"train-{name}"]
        require(all(metrics[k]==v for k,v in totals.items()) and metrics["categories"]==dict(categories) and metrics["templates"]==dict(templates),"raw metrics")
        passed=totals["exact"]>=90 and totals["eos"]==96 and totals["malformed"]==0
        actual_gate=actual_gate and passed
        fit=read(train/"cost.json"); gen=read(pred.parent/"cost.json"); lossdir=RUN/"stages"/f"loss-train-{name}"
        losses=lines(lossdir/"losses.jsonl")
        nh=sum(l["history_targets"] for l in losses); na=sum(l["answer_targets"] for l in losses)
        h=sum(l["history_loss"] for l in losses); a=sum(l["answer_loss"] for l in losses)
        require(math.isclose(metrics["full_nll"],(h+a)/(nh+na)) and math.isclose(metrics["answer_nll"],a/na),"loss totals")
        cells[name]=dict(metrics=metrics,training=stats,fit=fit,generation=gen,scoring=read(lossdir/"cost.json"),failures=failures,
                       first_objective=trace[0]["objective"],last_objective=trace[-1]["objective"],
                       warm_generation={k:sum(p["cost"][k] for p in predictions) for k in ("cpu","wall")})
    require(actual_gate==summary["training_gate"]==read(RUN/"training-gate.json")["pass_gate"],"gate")
    require(not actual_gate and summary["decision"]=="STOP_TRAINING_FAILURE" and not summary["gates"],"stop decision")
    require(not list((RUN/"stages").glob("*dev*")) and not (RUN/"stages/controls").exists(),"forbidden post-gate evaluation")
    for cost in summary["stages"].values():
        require(cost["complete_process_lifetimes"] and cost["active_processes"]==0 and cost["status"]=="PASS","stage lifetime")
    return dict(status="PASS",decision=summary["decision"],development_evaluated=False,controls_after_gate_evaluated=False,
                cells=cells,execution=outer,registered_requests=388,scored_training_outputs=384,
                training_or_generation_executed=False)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path);args=parser.parse_args()
    result=audit()
    if args.output:
        with args.output.open("x",encoding="utf-8",newline="\n") as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write("\n")
        print(json.dumps(dict(status=result["status"],decision=result["decision"],output=str(args.output))))
    else:print(json.dumps(result,sort_keys=True))
