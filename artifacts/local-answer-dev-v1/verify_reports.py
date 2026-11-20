"""Read-only checks of diagnosis/results tables, raw examples, links and whitespace."""

import json
import math
import re
from collections import Counter
from pathlib import Path

RUN=Path(__file__).resolve().parent;ROOT=RUN.parents[1]
DOCS=ROOT/"docs/research"


def read(path):return json.loads(path.read_text(encoding="utf-8"))
def close(actual,expected,tolerance=.00000051):
    assert math.isclose(float(actual),expected,abs_tol=tolerance,rel_tol=0),(actual,expected)
def table(text,begin,end,prefixes):
    section=text.split(begin,1)[1].split(end,1)[0]
    return [[p.strip() for p in row.split('|')[1:-1]] for row in section.splitlines() if row.startswith(prefixes)]


def main():
    diagnosis=read(ROOT/"artifacts/local-answer-dev-v1-preparation/v1-diagnosis-derived.json")
    text=(DOCS/"local-answer-v1-saved-diagnosis.md").read_text(encoding="utf-8")
    aggregate=table(text,"| Seed | Objective | Model | Correct","Primary causes",("| 419 |","| 733 |"))
    assert len(aggregate)==8
    for parts in aggregate:
        seed,objective,variant=parts[:3]; data=diagnosis['cells'][f'{seed}-{objective}-{variant}']
        assert [int(p) for p in parts[3:7]]==[data['counts'].get(k,0) for k in ('correct','wrong_value','malformed_closed','eos_failure')]
        assert int(parts[7])==data['prior_matches']
    cases=table(text,"| Case | Category | Correct /8","Representative evidence",("| dev-",))
    assert len(cases)==16
    for index,parts in enumerate(cases):
        examples=[c['cases'][index] for c in diagnosis['cells'].values()];counts=Counter(c['primary'] for c in examples)
        assert parts[:2]==[examples[0]['id'],examples[0]['category']]
        assert list(map(int,parts[2:]))==[counts[k] for k in ('correct','wrong_value','malformed_closed','eos_failure')]
    analysis=read(RUN/'saved-audit.json')
    report=(DOCS/'local-answer-dev-v1-results.md').read_text(encoding='utf-8')
    quality=table(report,"| Seed | Model | Exact /96","Total368",("| 601 |","| 947 |")); assert len(quality)==4
    for parts in quality:
        data=analysis['cells']['-'.join(parts[:2])];m=data['metrics']
        assert list(map(int,parts[2:9]))==[m[k] for k in ('exact','eos','malformed','repetitive')]+[m['categories'][k] for k in ('city','code','unknown')]
        assert parts[9]==f"{m['templates']['A']}/{m['templates']['B']}"
    loss=table(report,"| Seed | Model | First update CE","All objectives",("| 601 |","| 947 |"));assert len(loss)==4
    for parts in loss:
        data=analysis['cells']['-'.join(parts[:2])];m=data['metrics']
        for actual,expected in zip(parts[2:],(data['first_objective'],data['last_objective'],m['full_nll'],m['history_nll'],m['answer_nll']),strict=True):close(actual,expected)
    costs=table(report,"| Seed | Model | Cold fit CPU/wall","Four fits total",("| 601 |","| 947 |"));assert len(costs)==4
    for parts in costs:
        data=analysis['cells']['-'.join(parts[:2])]
        for part,key in zip((parts[2],parts[4],parts[5]),('fit','generation','scoring'),strict=True):
            for actual,metric in zip(part.split('/'),('cpu','wall'),strict=True):close(actual,data[key][metric])
        for actual,key in zip(parts[3].split('/'),('loop_cpu','loop_wall'),strict=True):close(actual,data['training'][key])
        assert int(parts[6])==data['fit']['peak_private']
    failed=table(report,"| Ordinary947 training cases |","The same failure",("| train-",));assert len(failed)==4
    native=analysis['cells']['947-ordinary']['failures']
    for index,parts in enumerate(failed):
        group=native[index*4:index*4+4]
        assert all(c['ids']==json.loads(parts[3].strip('`')) and c['gold']==parts[2].strip('`') for c in group)
        assert len(group)==int(parts[5]) and all(c['wrong_first_byte'] and c['eos'] for c in group)
    links=0
    paths=[DOCS/name for name in ('local-answer-dev-v1-results.md','local-answer-v1-saved-diagnosis.md','local-answer-accounting-v1.md')]
    for path in paths:
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            assert (path.parent/link).is_file(),(path,link);links+=1
    for path in [*paths,DOCS/'local-answer-dev-v1-protocol.md',ROOT/'scripts/local_answer_dev.py',ROOT/'scripts/lifetime_job.py',ROOT/'scripts/diagnose_local_answer_v1.py',ROOT/'tests/test_lifetime_job.py',ROOT/'tests/test_local_answer_dev.py']:
        raw=path.read_bytes();assert raw.endswith(b'\n') and not raw.endswith(b'\n\n'),path
        assert all(s==s.rstrip() for s in raw.decode().splitlines()),path
    print(json.dumps(dict(status='PASS',v1_cell_rows=8,v1_case_rows=16,new_quality_loss_cost_rows=12,new_failure_groups=4,links=links,development_evaluated=False)))


if __name__=='__main__':main()
