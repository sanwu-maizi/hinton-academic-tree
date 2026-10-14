import json
from pathlib import Path
d=Path('outputs/hinton-academic-tree/data')
payload={k:json.loads((d/(k+'.json')).read_text()) for k in ['nodes','edges','authors','works']}
template=Path(__file__).with_name('viewer.html').read_text()
interactions=Path(__file__).with_name('interactions.js').read_text()
force=Path(__file__).with_name('force_graph.js').read_text()
d3=Path(__file__).with_name('d3.min.js').read_text()
template=template.replace('</html>','<script>'+d3+'</script><script>'+interactions+'</script><script>'+force+'</script></html>')
Path('outputs/hinton-academic-tree/hinton-academic-tree.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False).replace('</','<\\/')))
