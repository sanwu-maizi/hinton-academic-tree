#!/usr/bin/env python3
"""Use saved public tree HTML; no challenge solving or private endpoints."""
import json, re, subprocess, time, unicodedata, hashlib, os
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from difflib import SequenceMatcher
from lxml import html

BASE='https://academictree.org/computerscience/tree.php?pid=1446'
OUT=Path('outputs/hinton-academic-tree/data')
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    content=json.dumps(value,ensure_ascii=False,indent=2)
    key=os.environ.get('OPENALEX_API_KEY')
    if key:content=content.replace(key,'[REDACTED]')
    path.write_text(content)
def norm(s):
    return re.sub(r'[^a-z0-9 ]','',unicodedata.normalize('NFKD',s).lower())
def request(url, path):
    if path.exists():
        try:
            cached=json.loads(path.read_text())
            if not cached.get('error'):return cached
        except ValueError:pass
    if os.environ.get('OPENALEX_API_KEY'):url+='&'+urlencode({'api_key':os.environ['OPENALEX_API_KEY']})
    result=subprocess.run(['curl','-L','--max-time','15','-sS',url],capture_output=True,text=True)
    try:
        data=json.loads(result.stdout);write(path,data);return data
    except ValueError:return {'error':result.stderr or result.stdout[:200]}
def main():
    raw_html=Path('outputs/academictree-access-evidence/tree.html').read_text()
    doc=html.fromstring(raw_html)
    raw_names={}
    for raw_link in re.finditer(r'<a\b([^>]*class=["\']centerNode["\'][^>]*)>(.*?)</a>',raw_html,re.S|re.I):
        href=re.search(r'href=["\']([^"\']+)',raw_link.group(1),re.I)
        if href:
            fragment=re.sub(r'<br\s*/?>',' ',raw_link.group(2),flags=re.I)
            raw_names[urljoin(BASE,href.group(1))]=' '.join(html.fromstring('<div>'+fragment+'</div>').text_content().split())
    links=doc.xpath('//a[contains(concat(" ",normalize-space(@class)," ")," centerNode ")]')
    nodes={}; link_ids={}; pid_ids={}
    for a in links:
        url=urljoin(BASE,a.get('href',''));pid=parse_qs(urlparse(url).query).get('pid',[None])[0]
        if not pid:continue
        tree=urlparse(url).path.strip('/').split('/')[0];ident=tree+':'+pid
        font=a.xpath('.//font[1] | .//b[1]')
        name=' '.join(' '.join((font[0] if font else a).itertext()).split());institution=''
        if not font:
            chunks=[]
            if a.text:chunks.append(a.text)
            for child in a:
                if child.tag=='br':
                    if child.tail:chunks.append(child.tail)
                elif child.tag=='div':
                    if child.text:chunks.append(child.text)
                    for part in child:
                        if part.tag=='br' and part.tail:chunks.append(part.tail)
                        elif part.tag!='br':break
                    break
                else:break
            name=' '.join(' '.join(chunks).split())
        name=raw_names.get(url,name)
        if not name:continue
        following=a.xpath('following-sibling::font[1]')
        if following:institution=' '.join(following[0].itertext()).strip()
        if ident=='computerscience:1446':institution='University of Toronto'
        nodes[ident]={'id':ident,'pid':pid,'name':name,'tree':tree,'institution':institution,'url':url,'source_url':BASE,'details_status':'unavailable','generation':0}
        link_ids[a]=ident;pid_ids[pid]=ident
    edges={}
    for a,ident in link_ids.items():
        containers=a.xpath('ancestor::div[starts-with(@id,"div")]')
        if containers:
            parent=pid_ids.get(containers[-1].get('id')[3:])
            if parent and parent!=ident:edges[(parent,ident)]={'source_id':parent,'target_id':ident,'relation':'training','confidence':'tree-structure','source_url':BASE}
    # Ancestor tables are bottom-aligned. The smallest enclosing parent cell
    # with a later node identifies the next generation, without flattening links.
    center=doc.xpath('//a[@id="centerNodeName"]')[0]
    ancestors=[a for a in links if a in link_ids and a.sourceline<center.sourceline]
    for a in ancestors:
        own=a.xpath('ancestor::table')[ -1 ]
        for cell in own.xpath('ancestor::table')[::-1]:
            later=[b for b in cell.xpath('.//a[contains(@class,"centerNode")]') if b in link_ids and b.sourceline>a.sourceline and b.sourceline<=center.sourceline and b.xpath('ancestor::table')[-1] is cell]
            if later:
                b=min(later,key=lambda x:x.sourceline)
                if link_ids[b]!=link_ids[a]:edges[(link_ids[a],link_ids[b])]={'source_id':link_ids[a],'target_id':link_ids[b],'relation':'training','confidence':'tree-structure','source_url':BASE}
                break
    root='computerscience:1446';depth={root:0}
    for _ in range(12):
        for p,c in edges:
            if p in depth and c not in depth:depth[c]=depth[p]+1
            if c in depth and p not in depth:depth[p]=depth[c]-1
    for k,n in nodes.items():n['generation']=depth.get(k,0)
    write(OUT/'nodes.json',list(nodes.values()));write(OUT/'edges.json',list(edges.values()))
    authors=[];works={};budget_exhausted=False
    for index,n in enumerate(nodes.values()):
        cache=OUT/'source-records'/n['id'].replace(':','_');cache.mkdir(parents=True,exist_ok=True)
        query='Geoffrey Hinton' if n['id']==root else n['name']
        search_path=cache/('search-'+hashlib.sha256(query.encode()).hexdigest()[:12]+'.json')
        search={'error':'budget_exhausted; resume with OPENALEX API access'} if budget_exhausted and not search_path.exists() else request('https://api.openalex.org/authors?'+urlencode({'search':query,'per-page':5}),search_path)
        if 'budget' in str(search.get('message','')).lower() or 'Rate limit' in str(search.get('error','')):budget_exhausted=True
        candidates=search.get('results',[])
        def score(x):
            names=[x.get('display_name','')]+x.get('display_name_alternatives',[])+x.get('raw_author_names',[])
            return max([SequenceMatcher(None,norm(n['name']),norm(v)).ratio() for v in names] or [0])
        ranked=sorted(candidates,key=score,reverse=True);best=ranked[0] if ranked else None
        accepted=best is not None and score(best)>=.87 and (len(ranked)==1 or score(best)-score(ranked[1])>=.04)
        if n['id']==root:
            best=next((x for x in candidates if x['id'].endswith('A5108093963')),None)
            if best is None:best={'id':'https://openalex.org/A5108093963','display_name':'Geoffrey E. Hinton'}
            accepted=True
        author={'node_id':n['id'],'name':n['name'],'identity_verified':bool(n['id']==root and accepted),'match_status':'matched' if accepted else 'ambiguous' if candidates else 'not_found','match_score':score(best) if best else 0,'match_method':'name-variants; Hinton explicitly verified','candidates':[{'id':x['id'],'name':x.get('display_name'),'score':score(x)} for x in ranked],'openalex':best if accepted else None,'works':[],'pagination_status':'not_started'}
        if search.get('error') and not accepted:author['match_status']='api_error';author['error']=search
        if accepted:
            cursor='*';page_no=0;seen=set();author['pagination_status']='complete'
            while cursor and cursor not in seen:
                seen.add(cursor);page=request('https://api.openalex.org/works?'+urlencode({'filter':'author.id:'+best['id'].split('/')[-1],'per-page':200,'cursor':cursor}),cache/f'works-{page_no}.json')
                if 'results' not in page:author['pagination_status']='failed';author['error']=page;break
                author['expected_works']=page.get('meta',{}).get('count')
                for w in page['results']:
                    author['works'].append(w['id']);works[w['id']]=w
                cursor=page.get('meta',{}).get('next_cursor');page_no+=1;time.sleep(.15)
        authors.append(author)
        if index%25==0:write(OUT/'authors.json',authors)
        print(index+1,len(nodes),n['name'],author['match_status'],len(author['works']),flush=True)
    write(OUT/'authors.json',authors);write(OUT/'works.raw.json',list(works.values()))
    normalized=[]
    for w in works.values():
        normalized.append({**w,'work_id':w['id'],'authors':[x['author']['display_name'] for x in w.get('authorships',[])],'author_ids':[x['author']['id'] for x in w.get('authorships',[])],'institutions':[i for x in w.get('authorships',[]) for i in x.get('institutions',[])],'venue':((w.get('primary_location') or {}).get('source') or {}).get('display_name'),'sources':['openalex']})
    write(OUT/'works.json',normalized)
    write(OUT/'manifest.json',{'root':root,'scope':'nodes visible in saved public tree; NOT exhaustive descendants','details_status':'Turnstile','dblp_status':'blocked','nodes':len(nodes),'edges':len(edges),'authors_matched':sum(x['match_status']=='matched' for x in authors),'works':len(works),'pagination_failures':sum(x['pagination_status']=='failed' for x in authors),'source_url':BASE,'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    from audit_nodes import audit
    audit(OUT)
if __name__=='__main__':main()
