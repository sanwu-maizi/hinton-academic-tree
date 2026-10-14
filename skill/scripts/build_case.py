import argparse,json,html
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--root',required=True);ap.add_argument('--title',required=True);a=ap.parse_args()
base=Path(a.case);d=base/'data';s=Path(__file__).parent
payload={k:json.loads((d/(k+'.json')).read_text()) for k in ['nodes','edges','authors','works']}
template=(s/'viewer.html').read_text().replace('computerscience:1446',a.root).replace('Hinton 学术谱系',html.escape(a.title))
template=template.replace('AcademicTree 来源','${esc(n.source_name||n.tree||"谱系")} 来源')
tail=(s/'interactions.js').read_text()+(s/'force_graph.js').read_text().replace('computerscience:1446',a.root)
template=template.replace('</html>','<script>'+(s/'d3.min.js').read_text()+'</script><script>'+tail+'</script></html>')
(base/'index.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False).replace('</','<\\/')))
