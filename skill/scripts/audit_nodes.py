"""Audit local evidence without API calls; complete means retrieval, not identity proof."""
import csv, json
from pathlib import Path
from datetime import datetime, timezone

def audit(data_dir):
    d=Path(data_dir); nodes=json.loads((d/'nodes.json').read_text()); authors={a['node_id']:a for a in json.loads((d/'authors.json').read_text())}; works={w.get('work_id',w.get('id')):w for w in json.loads((d/'works.json').read_text())}; rows=[]
    for n in nodes:
        a=authors.get(n['id'],{}); ids=a.get('works',[]); unique=set(ids); missing=sorted(unique-works.keys()); expected=a.get('expected_works'); reasons=[]
        if a.get('match_status')!='matched':reasons.append('author_'+a.get('match_status','not_processed'))
        if a.get('pagination_status')!='complete':reasons.append('pagination_'+a.get('pagination_status','not_started'))
        if expected is None:reasons.append('expected_count_unknown')
        elif expected!=len(unique):reasons.append('count_mismatch')
        if len(ids)!=len(unique):reasons.append('duplicate_work_ids')
        if missing:reasons.append('missing_work_records')
        if not a:reasons.append('author_record_missing')
        complete=not reasons
        identity_verified=a.get('identity_verified',n['id']=='computerscience:1446' and bool(a.get('openalex',{}).get('id','').endswith('A5108093963')))
        rows.append({'node_id':n['id'],'name':n['name'],'openalex_id':(a.get('openalex') or {}).get('id'),'retrieval_complete':complete,'identity_verified':identity_verified,'details_complete':False,'all_sources_complete':False,'match_status':a.get('match_status','not_processed'),'pagination_status':a.get('pagination_status','not_started'),'expected_works':expected,'retrieved_unique_works':len(unique),'missing_record_count':len(missing),'missing_work_ids':missing,'failure_reasons':reasons,'source_error':a.get('error'),'checked_at':datetime.now(timezone.utc).isoformat()})
    (d/'node-status.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    with (d/'node-status.csv').open('w',newline='') as f:
        fields=['node_id','name','retrieval_complete','identity_verified','all_sources_complete','match_status','pagination_status','expected_works','retrieved_unique_works','missing_record_count','failure_reasons'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    with (d/'acquisition-log.jsonl').open('a') as f:
        for row in rows:f.write(json.dumps({'event':'node_audit',**row},ensure_ascii=False)+'\n')
    return rows
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--data',default='outputs/hinton-academic-tree/data');args=ap.parse_args();r=audit(args.data);print(json.dumps({'nodes':len(r),'retrieval_complete':sum(x['retrieval_complete'] for x in r),'incomplete':sum(not x['retrieval_complete'] for x in r)}))
