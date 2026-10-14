#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from urllib.request import Request,urlopen
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--authors',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(); out=[]
 for x in json.loads(Path(a.authors).read_text()):
  name=x['name']; url='https://dblp.org/search/author/api?q='+name.replace(' ','%20')+'&h=10'
  try: body=urlopen(Request(url,headers={'User-Agent':'academic-tree-reproduction/1.0'}),timeout=30).read().decode('utf8','replace'); status='ok' if body.lstrip().startswith('{') else 'blocked'
  except Exception as e: body='';status='error:'+str(e)
  out.append({'node_id':x['node_id'],'name':name,'url':url,'status':status,'raw':body[:200000]})
 Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
