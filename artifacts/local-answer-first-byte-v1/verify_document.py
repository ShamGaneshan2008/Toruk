"""Check the versioned failure table against saved-only audit output."""

import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent


def main():
    data=json.loads((BASE/'audit.json').read_text())
    path=ROOT/'docs/research/local-answer-first-byte-v1-diagnosis.md'
    text=path.read_text(encoding='utf-8')
    table=[s for s in text.splitlines() if s.startswith('| train-')]
    assert len(table)==16
    for row,case in zip(table,data['failed_cases'],strict=True):
        parts=[p.strip() for p in row.split('|')[1:-1]]
        expected=case['expected_first'];predicted=case['predicted_first']
        assert parts==[case['id'],case['template'],f"`{expected['char']}`{expected['byte']}/{expected['id']}",
                      f"`{predicted['char']}`{predicted['byte']}/{predicted['id']}",'NR','53/21',
                      '`'+case['prompt']['prefix'].splitlines()[-1]+'`','yes' if case['malformed'] else 'no']
        assert not case['probability_rank_recorded'] and case['probability'] is None and case['rank'] is None
        assert len(case['passing_comparisons'])==3 and all(v['ids']==case['expected_ids'] for v in case['passing_comparisons'].values())
    links=0
    files=[path,ROOT/'docs/research/local-answer-first-byte-v1-next-study-proposal.md',ROOT/'scripts/audit_local_answer_first_byte.py',Path(__file__)]
    for document in files:
        raw=document.read_bytes();assert raw.endswith(b'\n') and not raw.endswith(b'\n\n')
        assert all(s==s.rstrip() for s in raw.decode().splitlines())
        if document.suffix=='.md':
            for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',document.read_text(encoding='utf-8')):
                assert (document.parent/link).is_file(),link;links+=1
    assert data['paired_query_events']==268
    assert data['city_first_class_counts']['947-ordinary'].get('m',0)==0
    print(json.dumps(dict(status='PASS',failure_table_rows=16,passing_comparisons=48,links=links,
                         recorded_probabilities_or_ranks=False,training_or_generation_executed=False)))


if __name__=='__main__':main()
