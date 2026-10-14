"""Build progressive Pages assets: graph first, author records on demand."""
import gzip
import hashlib
import json
from pathlib import Path
import zipfile

scripts=Path(__file__).parent
data=Path('outputs/hinton-academic-tree/data')
out=Path('outputs/cloudflare-pages-progressive')
out.mkdir(parents=True,exist_ok=True)
def compact(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
def store(name,value):
    target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(gzip.compress(compact(value),compresslevel=6))
nodes=json.loads((data/'nodes.json').read_text())
edges=json.loads((data/'edges.json').read_text())
authors=json.loads((data/'authors.json').read_text())
works=json.loads((data/'works.json').read_text())
by_id={w['work_id']:w for w in works}
minimal_authors=[]
for author in authors:
    ids=list(dict.fromkeys(author.get('works',[])))
    detail={'author':author,'works':[by_id[i] for i in ids if i in by_id]}
    digest=hashlib.sha256(compact(detail)).hexdigest()[:16]
    path='authors/'+author['node_id'].replace(':','_')+'-'+digest+'.bin'
    store(path,detail)
    minimal_authors.append({k:author.get(k) for k in ['node_id','name','match_status','pagination_status','works']}|{'detail_url':path})
skeleton={'nodes':nodes,'edges':edges,'authors':minimal_authors,'works':[{'work_id':w['work_id'],'cited_by_count':w.get('cited_by_count',0)} for w in works]}
store('graph.bin',skeleton)
loader='''async function readCompressed(url){
 const response=await fetch(url);if(!response.ok)throw new Error('HTTP '+response.status);
 const stream=response.body.pipeThrough(new DecompressionStream('gzip'));
 return JSON.parse(await new Response(stream).text());
}
'''
lazy='''
const originalShow=show,detailCache=new Map();let activeRequest=0;
show=async function(id){
 const requestId=++activeRequest;selected=id;
 const author=authors.get(id),node=D.nodes.find(n=>n.id===id);
 if(!author?.detail_url){originalShow(id);return}
 if(!detailCache.has(id)){
  panel.innerHTML='<h2>'+esc(node.name)+'</h2><p>'+esc(node.institution||'')+'</p><p role="status">正在加载论文…</p>';
  const pending=readCompressed(author.detail_url).then(detail=>{
   detail.works.forEach(w=>works.set(w.work_id,w));authors.set(id,detail.author);return detail;
  }).catch(error=>{detailCache.delete(id);throw error});detailCache.set(id,pending);
 }
 try{await detailCache.get(id);if(requestId===activeRequest)originalShow(id)}
 catch(error){if(requestId===activeRequest){panel.innerHTML='<h2>'+esc(node.name)+'</h2><p>论文加载失败，请重试。</p><button id="retry-detail">重试</button>';document.querySelector('#retry-detail').onclick=()=>show(id)}}
};
'''
template=(scripts/'viewer.html').read_text()
template=template.replace('const D=__DATA__;','const D=await readCompressed("graph.bin");')
template=template.replace('<script>const D=','<script src="d3.min.js"></script><script>'+loader+'(async()=>{try{const D=')
template=template.replace('center(selected);show(selected);','center(selected);')
tail=lazy+'\n'+(scripts/'interactions.js').read_text()+'\n'+(scripts/'force_graph.js').read_text()+'\nrequestAnimationFrame(()=>requestAnimationFrame(()=>show(selected)));'
template=template.replace('</script></html>',tail+"\n}catch(error){document.querySelector('#panel').textContent='图谱加载失败：'+error.message;}})();</script></html>")
(out/'index.html').write_text(template)
(out/'d3.min.js').write_bytes((scripts/'d3.min.js').read_bytes())
with zipfile.ZipFile('outputs/cloudflare-pages-progressive.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(out.rglob('*')):
        if path.is_file():archive.write(path,path.relative_to(out))
print(json.dumps({'graph_bytes':(out/'graph.bin').stat().st_size,'author_files':len(authors),'initial_bytes':sum((out/f).stat().st_size for f in ['index.html','graph.bin','d3.min.js']),'total_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())}))
