"""Fetch a reviewed root author's works and capture budget without exposing a key."""
import os,json,subprocess
from pathlib import Path
from urllib.parse import urlencode
key=os.environ['OPENALEX_API_KEY'];out=Path('outputs/award-reproduction/tao');out.mkdir(parents=True,exist_ok=True)
def get(endpoint,params):
 params={**params,'api_key':key};r=subprocess.run(['curl','-Ls','--max-time','20','https://api.openalex.org/'+endpoint+'?'+urlencode(params)],capture_output=True,text=True);return json.loads(r.stdout)
def save(name,data):
 if isinstance(data,dict):data.pop('api_key',None)
 (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2).replace(key,'[REDACTED]'))
save('budget-before.json',get('rate-limit',{}));author=get('authors/A5066728260',{});save('author.json',author)
works=[];cursor='*';page=0
while cursor:
 d=get('works',{'filter':'author.id:A5066728260','per-page':200,'cursor':cursor});save(f'works-page-{page}.json',d)
 if 'results' not in d:break
 works+=d['results'];cursor=d.get('meta',{}).get('next_cursor');page+=1
save('works.json',works);save('budget-after.json',get('rate-limit',{}));print('Tao works',len(works),'pagination_complete',cursor is None)
