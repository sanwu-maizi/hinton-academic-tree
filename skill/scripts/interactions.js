// Start pointer capture only after a drag, so node clicks keep their target.
const hoverTip=document.createElement('div');
hoverTip.className='hover-tip';document.body.appendChild(hoverTip);
const interactionStyle=document.createElement('style');
interactionStyle.textContent=`
.hover-tip{position:fixed;z-index:20;pointer-events:none;display:none;background:#fff;color:#24312f;border:1px solid #bdcec4;border-radius:5px;padding:10px 12px;box-shadow:0 4px 18px #24312f20;font-size:13px;max-width:260px}
#canvas>g{transition:opacity .16s}#canvas>g circle{transition:stroke .16s,filter .16s;vector-effect:non-scaling-stroke}
#canvas>g.is-related circle{stroke:#419e80;stroke-width:2.5}#canvas>g.is-current circle{stroke:#123f31;stroke-width:3;filter:drop-shadow(0 0 3px #419e8060)}
#canvas>path{transition:stroke .16s,opacity .16s;vector-effect:non-scaling-stroke}#canvas>path.is-related{stroke:#237557;stroke-width:2.5}
#svg{animation:gentle-float 7s ease-in-out infinite;touch-action:none}@keyframes gentle-float{0%,100%{transform:translateY(-.33px)}50%{transform:translateY(.33px)}}
@media(prefers-reduced-motion:reduce){#svg{animation:none}}
`;
document.head.appendChild(interactionStyle);
const nodeElements=new Map([...canvas.querySelectorAll('g[data-id]')].map(g=>[g.dataset.id,g]));
const edgeElements=[...canvas.querySelectorAll(':scope>path')];
const visibleEdges=D.edges.filter(e=>positions[e.source_id]&&positions[e.target_id]);
let hovered=null;
function highlight(id){
    const related=new Set([id]);
    visibleEdges.forEach(e=>{if(e.source_id===id||e.target_id===id){related.add(e.source_id);related.add(e.target_id)}});
    const query=document.querySelector('#search').value.toLowerCase();
    nodeElements.forEach((g,key)=>{
        g.classList.toggle('is-current',key===id);
        g.classList.toggle('is-related',!!id&&related.has(key)&&key!==id);
        const name=D.nodes.find(n=>n.id===key).name.toLowerCase();
        g.style.opacity=id?(related.has(key)?1:.22):(!query||name.includes(query)?1:.12);
    });
    edgeElements.forEach((path,i)=>{
        const e=visibleEdges[i],active=!!id&&(e.source_id===id||e.target_id===id);
        path.classList.toggle('is-related',active);path.style.opacity=id?(active?1:.12):1;
    });
}
function tipPosition(e){
    hoverTip.style.left=Math.max(8,Math.min(e.clientX+16,innerWidth-hoverTip.offsetWidth-8))+'px';
    hoverTip.style.top=Math.max(8,Math.min(e.clientY+16,innerHeight-hoverTip.offsetHeight-8))+'px';
}
nodeElements.forEach((g,id)=>{
    g.setAttribute('tabindex','0');g.setAttribute('role','button');
    const n=D.nodes.find(n=>n.id===id),a=authors.get(id),ids=a?.works||[];
    const citations=ids.reduce((sum,wid)=>sum+(works.get(wid)?.cited_by_count||0),0);
    g.setAttribute('aria-label',n.name);
    g.onpointerenter=e=>{
        hovered=id;highlight(id);
        hoverTip.innerHTML=`<b>${esc(n.name)}</b><br>论文数量：${a?.match_status==='matched'?ids.length.toLocaleString():'未匹配'}<br>引用数量：${a?.match_status==='matched'?citations.toLocaleString():'未匹配'}`;
        hoverTip.style.display='block';tipPosition(e);
    };
    g.onpointermove=e=>{if(hovered===id)tipPosition(e)};
    g.onpointerleave=()=>{hovered=null;hoverTip.style.display='none';highlight(null)};
    g.onclick=e=>{if(suppressClick){e.preventDefault();return}show(id);highlight(hovered)};
    g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show(id);highlight(id)}};
});
let pointerDrag=null,suppressClick=false;
svg.onpointerdown=e=>{
    if(e.button!==0)return;
    pointerDrag={x:e.clientX,y:e.clientY,ox:offset.x,oy:offset.y,id:e.pointerId,moved:false};suppressClick=false;
};
svg.onpointermove=e=>{
    if(!pointerDrag)return;
    if(!pointerDrag.moved&&Math.hypot(e.clientX-pointerDrag.x,e.clientY-pointerDrag.y)>4){
        pointerDrag.moved=true;svg.setPointerCapture(e.pointerId);hoverTip.style.display='none';
    }
    if(pointerDrag.moved){offset.x=pointerDrag.ox+e.clientX-pointerDrag.x;offset.y=pointerDrag.oy+e.clientY-pointerDrag.y;transform()}
};
function finishPointer(){
    if(!pointerDrag)return;
    suppressClick=pointerDrag.moved;
    if(svg.hasPointerCapture(pointerDrag.id))svg.releasePointerCapture(pointerDrag.id);
    pointerDrag=null;setTimeout(()=>suppressClick=false,0);
}
svg.onpointerup=finishPointer;svg.onpointercancel=finishPointer;
highlight(selected);
