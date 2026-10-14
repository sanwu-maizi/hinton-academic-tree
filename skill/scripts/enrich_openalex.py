#!/usr/bin/env python3
import argparse,json,time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen
def get(url):
    try:return json.loads(urlopen(Request(url,headers={'User-Agent':'academic-tree-reproduction/1.0'}),timeout=30).read())
    except Exception as e:return {'error':str(e)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--nodes',required=True);ap.add_argument('--output',required=True);ap.add_argument('--limit',type=int,default=100);ap.add_argument('--delay',type=float,default=.2);a=ap.parse_args(); nodes=json.loads(Path(a.nodes).read_text()); authors=[]; works=[]
    for n in nodes:
        q=get('https://api.openalex.org/authors?search='+quote(n['name'])+'&per-page=5'); res=q.get('results',[]) if isinstance(q,dict) else []; match=res[0] if res else None
        author={'node_id':n['id'],'name':n['name'],'openalex':match or None,'works':[]}
        if match and match.get('id'):
            aid=match['id'].split('/')[-1]; cursor='*'; count=0
            while cursor and count<a.limit:
                page=get(f'https://api.openalex.org/works?filter=author.id:{aid}&per-page=200&cursor={quote(cursor)}'); rows=page.get('results',[]); works.extend(rows); author['works'].extend([x.get('id') for x in rows]); count+=len(rows); cursor=page.get('meta',{}).get('next_cursor'); time.sleep(a.delay)
        authors.append(author)
    o=Path(a.output); o.mkdir(parents=True,exist_ok=True); (o/'authors.json').write_text(json.dumps(authors,ensure_ascii=False,indent=2)); (o/'works.openalex.json').write_text(json.dumps(works,ensure_ascii=False,indent=2)); print(json.dumps({'authors':len(authors),'works':len(works)}))
if __name__=='__main__':main()
