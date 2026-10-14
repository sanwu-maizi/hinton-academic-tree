#!/usr/bin/env python3
import argparse, json, re, time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.request import Request, urlopen
from html.parser import HTMLParser

UA='academic-tree-reproduction/1.0 (research; contact: local)'
class LinkParser(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.current=None; self.text=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):
            self.current=a['href']; self.text=[]
    def handle_data(self, data):
        if self.current is not None: self.text.append(data)
    def handle_endtag(self, tag):
        if tag=='a' and self.current is not None:
            self.links.append((self.current,' '.join(''.join(self.text).split())))
            self.current=None

def fetch(url, cache, delay):
    cache.mkdir(parents=True, exist_ok=True); key=re.sub(r'[^A-Za-z0-9_.-]','_',url)+'.html'; p=cache/key
    if p.exists(): return p.read_text(errors='replace')
    time.sleep(delay); req=Request(url,headers={'User-Agent':UA})
    try:
        body=urlopen(req,timeout=30).read().decode('utf-8','replace'); p.write_text(body); return body
    except Exception as e:
        (cache/(key+'.error')).write_text(str(e)); return ''

def node_from_url(url, label, source):
    q=parse_qs(urlparse(url).query); pid=q.get('pid',[None])[0]
    m=re.search(r'(academictree|neurotree)\.org/([^/]+)/',url)
    tree=m.group(2) if m else source
    parts=[x.strip() for x in re.split(r'\s*<br\s*/?>\s*|\s{2,}', label, flags=re.I) if x.strip()]
    name=' '.join(parts[:]) or f'pid {pid}'
    return {'id':f'{tree}:{pid}','pid':pid,'name':name,'tree':tree,'url':url,'institution':None}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pid',default='1446'); ap.add_argument('--tree',default='computerscience'); ap.add_argument('--ancestors',type=int,default=4); ap.add_argument('--limit',type=int,default=80); ap.add_argument('--cache-dir',default='work/academic-tree-cache'); ap.add_argument('--output',required=True); ap.add_argument('--rate-limit',type=float,default=10); ap.add_argument('--resume',action='store_true'); a=ap.parse_args()
    root=f'https://academictree.org/{a.tree}/tree.php?pid={a.pid}&fontsize=0&pnodecount=4&cnodecount=2'; cache=Path(a.cache_dir); html=fetch(root,cache,a.rate_limit)
    nodes={}; edges=[]; queue=[(root,0)]; seen=set()
    while queue and len(seen)<a.limit:
        url,depth=queue.pop(0); key=url
        if key in seen: continue
        seen.add(key); body=html if url==root else fetch(url,cache,a.rate_limit)
        if not body: continue
        p=LinkParser(); p.feed(body)
        page_nodes=[]
        for href,label in p.links:
            full=urljoin(url,href)
            if 'tree.php?pid=' not in full: continue
            n=node_from_url(full,label,a.tree)
            if not n['pid']: continue
            nodes[n['id']]=n; page_nodes.append(n)
        center=re.search(r'peopleinfo\.php\?pid=(\d+)',body)
        center_id=f'{a.tree}:{center.group(1)}' if center else (next(iter(nodes),None))
        if center_id and center_id not in nodes:
            title=re.search(r'<title>.*?Tree - (.*?) Family Tree',body,re.I|re.S)
            nodes[center_id]={'id':center_id,'pid':center_id.split(':')[-1],'name':re.sub('<.*?>','',title.group(1)).strip() if title else center_id,'tree':a.tree,'url':url,'institution':None}
        for n in page_nodes:
            if center_id and n['id']!=center_id:
                relation='advisor' if depth>0 else 'descendant'
                edges.append({'source_id':n['id'] if relation=='advisor' else center_id,'target_id':center_id if relation=='advisor' else n['id'],'relation':'advisor','source_url':url,'confidence':'explicit'})
        if depth<a.ancestors or depth==0:
            for n in page_nodes:
                if n['url'] not in seen and len(seen)+len(queue)<a.limit: queue.append((n['url'],depth+1))
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    (out/'nodes.json').write_text(json.dumps(list(nodes.values()),ensure_ascii=False,indent=2)); (out/'edges.json').write_text(json.dumps(edges,ensure_ascii=False,indent=2))
    (out/'manifest.json').write_text(json.dumps({'source':'AcademicTree','root':root,'ancestors':a.ancestors,'limit':a.limit,'node_count':len(nodes),'edge_count':len(edges),'cache':str(cache)},ensure_ascii=False,indent=2))
    print(json.dumps({'nodes':len(nodes),'edges':len(edges)}))
if __name__=='__main__': main()
