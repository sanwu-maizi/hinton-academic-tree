"""Parse explicit MGP relationships, preserving the source boundary."""
import json
from pathlib import Path
from lxml import html
from urllib.parse import parse_qs,urlparse
p=Path('outputs/award-reproduction/tao');d=p/'data';doc=html.fromstring((p/'mgp-source.html').read_bytes());url='https://www.genealogy.math.ndsu.nodak.edu/id.php?id=43967'
root='mgp:43967';nodes=[{'id':root,'name':'Terence Chi-Shen Tao','tree':'MGP','institution':'Princeton University (PhD, 1996)','phd_institution':'Princeton University','phd_year':1996,'generation':0,'url':url,'source_name':'Mathematics Genealogy Project'}];edges=[]
for a in doc.xpath('//p[contains(text(),"Advisor:")]/a'):
 ident='mgp:'+parse_qs(urlparse(a.get('href')).query)['id'][0];nodes.append({'id':ident,'name':a.text_content().strip(),'tree':'MGP','generation':-1,'url':'https://www.genealogy.math.ndsu.nodak.edu/'+a.get('href'),'source_name':'Mathematics Genealogy Project'});edges.append({'source_id':ident,'target_id':root,'relation':'phd_advisor','source_url':url,'confidence':'explicit'})
for row in doc.xpath('//tr[td/a[contains(@href,"id.php?id=")]]'):
 cells=row.xpath('./td');a=cells[0].xpath('./a')[0];ident='mgp:'+parse_qs(urlparse(a.get('href')).query)['id'][0];name=a.text_content().strip();parts=name.split(', ',1);name=' '.join(parts[::-1]) if len(parts)==2 else name
 nodes.append({'id':ident,'name':name,'tree':'MGP','institution':cells[1].text_content().strip(),'phd_year':cells[2].text_content().strip(),'generation':1,'url':'https://www.genealogy.math.ndsu.nodak.edu/'+a.get('href'),'source_name':'Mathematics Genealogy Project'});edges.append({'source_id':root,'target_id':ident,'relation':'phd_advisor','source_url':url,'confidence':'explicit'})
authors=json.loads((d/'authors.json').read_text());author=next(a for a in authors if a.get('identity_verified'));author['node_id']=root;authors=[author]+[{'node_id':n['id'],'name':n['name'],'match_status':'not_processed','pagination_status':'not_started','works':[]} for n in nodes if n['id']!=root]
for name,value in [('nodes',nodes),('edges',edges),('authors',authors),('manifest',{'root':root,'title':'Terence Tao 学术谱系','source':'MGP','scope':'one advisor and direct students on saved page; not exhaustive descendants','nodes':len(nodes),'edges':len(edges),'openalex_root_works':len(author['works']),'academic_tree_status':'search challenged; no verified PID'})]:
 (d/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2))
print(len(nodes),len(edges))
