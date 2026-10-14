// D3's force solver keeps genealogy columns while allowing local elastic motion.
svg.style.animation='none';svg.style.transform='none';
const forceStyle=document.createElement('style');
forceStyle.textContent=`#svg{animation:none!important}#canvas>g text{fill:#445b55;font-size:15px}#canvas>g circle{stroke:#aac4b8;stroke-width:1.3}#canvas>g.is-current circle{stroke:#134d3a;stroke-width:2.4}#canvas>path{stroke:#b3c9bf;stroke-width:1.2;opacity:1}#canvas>path.is-related{stroke:#377f65;stroke-width:1.8}`;
document.head.appendChild(forceStyle);
const forceNodes=D.nodes.map(n=>({...n,x:positions[n.id].x,y:positions[n.id].y,r:+nodeElements.get(n.id).querySelector('circle').getAttribute('r')}));
const forceById=new Map(forceNodes.map(n=>[n.id,n]));
forceNodes.forEach(n=>{const box=nodeElements.get(n.id).querySelector('text').getBBox();n.labelWidth=box.width;n.labelHeight=box.height});
// Resolve the whole circle-plus-label rectangle, rather than just the circle.
function labelCollision(){
 let nodes=[];
 function force(alpha){
  for(let pass=0;pass<3;pass++)for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
   const a=nodes[i],b=nodes[j],pad=8;
   const ax=a.x+a.vx,ay=a.y+a.vy,bx=b.x+b.vx,by=b.y+b.vy;
   const ar=a.r*1.16,br=b.r*1.16;
   const left=Math.max(ax-ar-pad,bx-br-pad),right=Math.min(ax+ar+12+a.labelWidth+pad,bx+br+12+b.labelWidth+pad);
   const top=Math.max(ay-Math.max(ar,a.labelHeight/2)-pad,by-Math.max(br,b.labelHeight/2)-pad),bottom=Math.min(ay+Math.max(ar,a.labelHeight/2)+pad,by+Math.max(br,b.labelHeight/2)+pad);
   if(right<=left||bottom<=top)continue;
   const dx=right-left,dy=bottom-top;
   if(dy<dx){const push=(dy+.5)*.5*alpha*(ay<=by?-1:1);if(a.fy==null)a.vy+=push;if(b.fy==null)b.vy-=push}
   else{const push=(dx+.5)*.5*alpha*(ax<=bx?-1:1);if(a.fx==null)a.vx+=push;if(b.fx==null)b.vx-=push}
  }
 }
 force.initialize=value=>nodes=value;return force;
}
const forceLinks=visibleEdges.map(e=>({source:e.source_id,target:e.target_id}));
const simulation=d3.forceSimulation(forceNodes)
 .force('link',d3.forceLink(forceLinks).id(n=>n.id).distance(190).strength(.12))
 .force('charge',d3.forceManyBody().strength(-260))
 .force('collision',d3.forceCollide(n=>n.r+22).strength(.85))
 .force('labels',labelCollision())
 .force('column',d3.forceX(n=>n.generation*320).strength(.28))
 .force('row',d3.forceY(n=>positions[n.id].y*.65).strength(.035))
 .velocityDecay(.38).alphaDecay(.025);
function paintForce(){
 forceNodes.forEach(n=>{const g=nodeElements.get(n.id),c=g.querySelector('circle'),t=g.querySelector('text');c.setAttribute('cx',n.x);c.setAttribute('cy',n.y);t.setAttribute('x',n.x+n.r+7);t.setAttribute('y',n.y+4)});
 forceLinks.forEach((e,i)=>{const a=e.source,b=e.target;edgeElements[i].setAttribute('d',`M${a.x},${a.y} C${a.x+90},${a.y} ${b.x-90},${b.y} ${b.x},${b.y}`)});
}
simulation.on('tick',paintForce);
const previousHighlight=highlight;
highlight=function(id){
 previousHighlight(id);
 nodeElements.forEach((g,key)=>{g.style.opacity='1';const n=forceById.get(key),circle=g.querySelector('circle'),active=g.classList.contains('is-current'),related=g.classList.contains('is-related');circle.setAttribute('r',n.r*(active?1.16:related?1.08:1));g.querySelector('text').style.fill=active||related?'#203c30':'#536b60'});
 edgeElements.forEach(p=>p.style.opacity='1');
};
nodeElements.forEach((g,id)=>{
 const circle=g.querySelector('circle'),base=circle.getAttribute('fill');
 circle.setAttribute('fill',authors.get(id)?.match_status==='matched'?base:'#b8c4bd');
});
let forceDrag=null;
svg.onpointerdown=e=>{
 if(e.button!==0)return;const g=e.target.closest('g[data-id]');
 if(!g){pointerDrag={x:e.clientX,y:e.clientY,ox:offset.x,oy:offset.y,id:e.pointerId,moved:false};return}
 const n=forceById.get(g.dataset.id);forceDrag={n,x:e.clientX,y:e.clientY,ox:n.x,oy:n.y,id:e.pointerId,moved:false};suppressClick=false;
};
svg.onpointermove=e=>{
 if(forceDrag){const f=forceDrag;if(!f.moved&&Math.hypot(e.clientX-f.x,e.clientY-f.y)>4){f.moved=true;svg.setPointerCapture(e.pointerId);simulation.alphaTarget(.18).restart();hoverTip.style.display='none'}if(f.moved){f.n.fx=f.ox+(e.clientX-f.x)/offset.k;f.n.fy=f.oy+(e.clientY-f.y)/offset.k}return}
 if(pointerDrag){if(!pointerDrag.moved&&Math.hypot(e.clientX-pointerDrag.x,e.clientY-pointerDrag.y)>4){pointerDrag.moved=true;svg.setPointerCapture(e.pointerId)}if(pointerDrag.moved){offset.x=pointerDrag.ox+e.clientX-pointerDrag.x;offset.y=pointerDrag.oy+e.clientY-pointerDrag.y;transform()}}
};
svg.onpointerup=()=>{if(forceDrag){suppressClick=forceDrag.moved;forceDrag.n.fx=null;forceDrag.n.fy=null;if(svg.hasPointerCapture(forceDrag.id))svg.releasePointerCapture(forceDrag.id);forceDrag=null;simulation.alphaTarget(0);setTimeout(()=>suppressClick=false,0)}else finishPointer()};svg.onpointercancel=svg.onpointerup;
center=function(id){const n=forceById.get(id);offset.x=svg.clientWidth/2-n.x*offset.k;offset.y=svg.clientHeight/2-n.y*offset.k;transform()};
function fitGraph(){const xs=forceNodes.map(n=>n.x),ys=forceNodes.map(n=>n.y);const minX=Math.min(...xs)-100,maxX=Math.max(...xs)+240,minY=Math.min(...ys)-80,maxY=Math.max(...ys)+80;offset.k=Math.min(svg.clientWidth/(maxX-minX),svg.clientHeight/(maxY-minY),.8)*.92;offset.x=svg.clientWidth/2-(minX+maxX)/2*offset.k;offset.y=svg.clientHeight/2-(minY+maxY)/2*offset.k;transform()}
document.querySelector('#reset').onclick=fitGraph;
for(let i=0;i<160;i++)simulation.tick();paintForce();fitGraph();highlight(null);
