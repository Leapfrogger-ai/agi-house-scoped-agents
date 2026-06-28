"""Self-contained interactive explainer (canvas animation, 4 scenes) served at
/explainer and iframed into the landing page. Kept as its own document so its
CSS/JS never collides with the landing/operator pages."""

EXPLAINER = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scopebound — a visual explainer</title>
<style>
  body{margin:0;background:#0d0f14;color:#e8eaf0;font-family:system-ui,-apple-system,sans-serif;display:flex;justify-content:center;}
  .wrap{max-width:760px;width:100%;padding:32px 20px 48px;}
  h1{font-size:22px;font-weight:600;margin:0 0 4px;}
  .meta{font-size:13px;color:#8b90a0;margin-bottom:20px;}
  .meta a{color:#58C4DD;text-decoration:none;}
  .bar{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;}
  #ttl{font-size:17px;font-weight:600;}
  #cnt{font-size:12px;color:#8b90a0;}
  canvas{width:100%;aspect-ratio:640/360;display:block;border-radius:12px;background:#14161d;}
  .knob{display:flex;align-items:center;gap:12px;margin-top:10px;font-size:12px;color:#a7adbd;}
  .knob input{flex:1;accent-color:#FFD66B;}
  .knob b{font-family:ui-monospace,monospace;font-weight:600;color:#e8eaf0;min-width:46px;text-align:right;}
  #nar{min-height:150px;margin-top:12px;font-size:15px;line-height:1.7;color:#cfd3de;}
  .nav{display:flex;justify-content:space-between;align-items:center;margin-top:14px;}
  button{background:none;border:1px solid #3a3f4d;color:#e8eaf0;border-radius:8px;padding:6px 14px;font-size:13px;cursor:pointer;}
  button:hover{background:#1b1e27;}
  .dots{display:flex;gap:8px;}
  .dots span{width:9px;height:9px;border-radius:50%;background:#3a3f4d;cursor:pointer;display:inline-block;}
  .dots span.on{background:#e8eaf0;}
</style>
</head>
<body>
<div class="wrap">
  <h1>Scopebound: identity, runtime authority &amp; accountability for spending agents</h1>
  <div class="meta">AGI House · Agent Identity Build Day · June 2026 — spirit layer builds on <a href="https://arxiv.org/abs/2606.02060">DRIFT (arXiv:2606.02060)</a></div>
  <div class="bar"><div id="ttl"></div><div id="cnt"></div></div>
  <canvas id="cv"></canvas>
  <div class="knob" id="knobRow"><span>requested charge amount &rarr;</span><input id="kw" type="range" min="0" max="100" step="5" value="30"><b id="kwv">$30</b></div>
  <div id="nar"></div>
  <div class="nav"><button id="prev">&larr; back</button><div class="dots" id="dots"></div><button id="next">next &rarr;</button></div>
</div>
<script>
const BLUE='#58C4DD',YEL='#FFD66B',RED='#FF7B72',GRN='#7BD389',PUR='#B48EEC',WHT='#E8EAF0';
const cv=document.getElementById('cv'),dpr=Math.min(2,window.devicePixelRatio||1);
cv.width=640*dpr;cv.height=360*dpr;
const cx=cv.getContext('2d');cx.scale(dpr,dpr);
function txt(s,x,y,size,col,align){cx.font=size+'px system-ui,sans-serif';cx.fillStyle=col;cx.textAlign=align||'left';cx.fillText(s,x,y);}
function mono(s,x,y,size,col,align){cx.font=size+'px ui-monospace,monospace';cx.fillStyle=col;cx.textAlign=align||'left';cx.fillText(s,x,y);}
function glow(x,y,r,col){cx.fillStyle=col+'1f';cx.beginPath();cx.arc(x,y,r*2.6,0,7);cx.fill();cx.fillStyle=col+'4d';cx.beginPath();cx.arc(x,y,r*1.6,0,7);cx.fill();cx.fillStyle=col;cx.beginPath();cx.arc(x,y,r,0,7);cx.fill();}
function ring(x,y,r,col,lw){cx.strokeStyle=col;cx.lineWidth=lw||1.4;cx.beginPath();cx.arc(x,y,r,0,7);cx.stroke();}
function arrow(x1,y1,x2,y2,col,lw){cx.strokeStyle=col;cx.lineWidth=lw||1.2;cx.beginPath();cx.moveTo(x1,y1);cx.lineTo(x2,y2);cx.stroke();const a=Math.atan2(y2-y1,x2-x1);cx.fillStyle=col;cx.beginPath();cx.moveTo(x2,y2);cx.lineTo(x2-7*Math.cos(a-0.4),y2-7*Math.sin(a-0.4));cx.lineTo(x2-7*Math.cos(a+0.4),y2-7*Math.sin(a+0.4));cx.fill();}
function lerp(a,b,u){return a+(b-a)*u;}
function ease(u){u=Math.max(0,Math.min(1,u));return u*u*(3-2*u);}
function bg(){cx.fillStyle='#14161d';cx.fillRect(0,0,640,360);}
function rrect(x,y,w,h,r){cx.beginPath();cx.moveTo(x+r,y);cx.arcTo(x+w,y,x+w,y+h,r);cx.arcTo(x+w,y+h,x,y+h,r);cx.arcTo(x,y+h,x,y,r);cx.arcTo(x,y,x+w,y,r);cx.closePath();}

const RAILY=192,AX=66,GATEX=178,EYEX=320,CHX=470,MX=590,BUD=50;
let w=30;
const kw=document.getElementById('kw'),kwv=document.getElementById('kwv'),knobRow=document.getElementById('knobRow');
if(kw)kw.addEventListener('input',()=>{w=parseFloat(kw.value);kwv.textContent='$'+w;if(reduced)scenes[cur].d(5);});

let sd=9;function rr(){sd=(sd*16807)%2147483647;return sd/2147483647;}
const cloud=[];for(let i=0;i<16;i++)cloud.push([360+rr()*250,68+rr()*64]);
const VND=[[420,82],[492,70],[556,96]];

function corridor(){cx.strokeStyle='rgba(232,234,240,0.10)';cx.lineWidth=1;cx.beginPath();cx.moveTo(AX+16,RAILY);cx.lineTo(MX-24,RAILY);cx.stroke();}
function universe(a){cloud.forEach(p=>glow(p[0],p[1],1.7,'rgba(88,196,221,'+(a||0.16)+')'));}
function agentNode(sub){glow(AX,RAILY,6,BLUE);txt('agent',AX,RAILY-16,9.5,'rgba(88,196,221,0.85)','center');if(sub)txt(sub,AX,RAILY+20,8,'rgba(232,234,240,0.4)','center');}
function moneyNode(){cx.fillStyle='rgba(255,214,107,0.09)';cx.beginPath();cx.arc(MX,RAILY,20,0,7);cx.fill();
  cx.strokeStyle=YEL;cx.lineWidth=1.4;rrect(MX-13,RAILY-11,26,24,4);cx.stroke();ring(MX,RAILY,3.5,YEL,1.2);
  txt('funds',MX,RAILY+28,9,'rgba(255,214,107,0.7)','center');}
function keyGlyph(x,y,col){cx.strokeStyle=col;cx.lineWidth=1.8;ring(x,y,5,col,1.8);cx.beginPath();cx.moveTo(x+5,y);cx.lineTo(x+18,y);cx.moveTo(x+13,y);cx.lineTo(x+13,y+4);cx.moveTo(x+17,y);cx.lineTo(x+17,y+4);cx.stroke();}
function gateNode(state){const open=state==='open';
  cx.strokeStyle=BLUE;cx.lineWidth=2;cx.beginPath();cx.moveTo(GATEX,RAILY+14);cx.lineTo(GATEX,RAILY-2);cx.stroke();
  const ang=open?-1.12:0,len=38;cx.strokeStyle=open?GRN:RED;cx.lineWidth=2.4;
  cx.beginPath();cx.moveTo(GATEX,RAILY-2);cx.lineTo(GATEX+Math.cos(ang)*len,(RAILY-2)+Math.sin(ang)*len);cx.stroke();
  txt('overseer · rules',GATEX+8,RAILY+30,8,'rgba(232,234,240,0.5)','center');}
function eyeNode(state){const col=state==='reject'?RED:PUR;cx.strokeStyle=col;cx.lineWidth=1.5;
  cx.beginPath();cx.moveTo(EYEX-15,RAILY);cx.quadraticCurveTo(EYEX,RAILY-11,EYEX+15,RAILY);cx.quadraticCurveTo(EYEX,RAILY+11,EYEX-15,RAILY);cx.stroke();
  glow(EYEX,RAILY,3,col);txt('observer · spirit',EYEX,RAILY+28,8,'rgba(232,234,240,0.5)','center');}
function chamberNode(active){cx.setLineDash([4,3]);cx.strokeStyle=active?BLUE:'rgba(88,196,221,0.4)';cx.lineWidth=1.3;
  rrect(CHX-30,RAILY-24,60,48,12);cx.stroke();cx.setLineDash([]);txt('executor',CHX,RAILY+38,8,'rgba(88,196,221,0.65)','center');}
function token(x,col,r){glow(x,RAILY,r||3.5,col);}
function buy(fromX,fromY,p,u,col){cx.strokeStyle=col+(Math.round(0.6*u*255).toString(16).padStart(2,'0'));cx.lineWidth=1.2;cx.beginPath();cx.moveTo(fromX,fromY);cx.lineTo(lerp(fromX,p[0],u),lerp(fromY,p[1],u));cx.stroke();glow(p[0],p[1],3,col);}

function scene1(t){bg();const c=t%6;
  txt('the problem: agents can’t be trusted',24,32,12,'rgba(232,234,240,0.7)');
  glow(64,118,5.5,GRN);txt('human',64,102,9,'rgba(123,211,137,0.85)','center');
  cx.strokeStyle='rgba(123,211,137,0.4)';cx.lineWidth=1;cx.beginPath();cx.moveTo(64,126);cx.lineTo(66,178);cx.stroke();
  txt('gives key',104,150,8.5,'rgba(232,234,240,0.5)','left');
  let kx=64,ky=126;if(c>=0.3&&c<1.6){const u=ease((c-0.3)/1.3);kx=lerp(64,80,u);ky=lerp(126,190,u);}else if(c>=1.6){kx=80;ky=190;}
  keyGlyph(kx-4,ky,YEL);
  corridor();agentNode();moneyNode();
  if(c>1.9)txt('has funds',320,RAILY-12,8.5,'rgba(232,234,240,0.5)','center');
  if(c>1.8&&c<3.2)token(lerp(AX+18,MX-24,ease((c-1.8)/1.4)),'rgba(232,234,240,0.9)');
  let fan=0;if(c>3.0&&c<4.6)fan=(c-3.0)/1.6;else if(c>=4.6&&c<5.2)fan=1;else if(c>=5.2&&c<6)fan=1-(c-5.2)/0.8;
  const nred=Math.floor(fan*cloud.length);
  cloud.forEach((p,i)=>{const on=i<nred;if(on){cx.strokeStyle='rgba(255,123,114,'+(0.22*fan).toFixed(3)+')';cx.lineWidth=1;cx.beginPath();cx.moveTo(MX,RAILY-12);cx.lineTo(p[0],p[1]);cx.stroke();}glow(p[0],p[1],2,on?RED:'rgba(88,196,221,0.26)');});
  txt('the universe it could buy',300,52,9,'rgba(232,234,240,0.32)','center');
  if(fan>0)txt('can spend on anything',300,52,9.5,'rgba(255,123,114,'+(0.5+0.5*fan).toFixed(3)+')','center');
  txt('a human hands over a standing key → the agent controls the funds → it can spend on anything',320,316,10.5,'rgba(232,234,240,0.7)','center');
  txt('no limit on amount, vendor, or purpose — and no record of who asked',320,337,10,'rgba(232,234,240,0.45)','center');}

function scene2(t){bg();const c=t%7;
  txt('solution 1 — in-depth security',24,32,12,'rgba(232,234,240,0.7)');
  universe(0.16);txt('the universe it could buy',300,52,9,'rgba(232,234,240,0.3)','center');
  const OVX=92,SBX=350,VX=576,PD=VND[0];
  let boxA=1;if(c<0.45)boxA=ease(c/0.45);else if(c>5.7)boxA=1-ease((c-5.7)/1.2);
  glow(OVX,RAILY,6,BLUE);txt('overseer',OVX,RAILY-16,9,'rgba(88,196,221,0.85)','center');txt('decides · no key',OVX,RAILY+18,8,'rgba(232,234,240,0.4)','center');
  cx.strokeStyle=YEL;cx.lineWidth=1.4;rrect(VX-13,RAILY-12,26,24,4);cx.stroke();keyGlyph(VX-8,RAILY,YEL);txt('1Password vault',VX,RAILY-20,8.5,'rgba(255,214,107,0.72)','center');
  if(c>0.6)arrow(OVX+14,RAILY,SBX-66,RAILY,'rgba(88,196,221,0.5)',1.1);
  cx.globalAlpha=boxA;
  cx.setLineDash([4,3]);cx.strokeStyle=BLUE;cx.lineWidth=1.4;rrect(SBX-64,RAILY-30,128,60,12);cx.stroke();cx.setLineDash([]);
  txt('Daytona sandbox',SBX,RAILY-38,8.5,'rgba(88,196,221,0.85)','center');
  glow(SBX-26,RAILY,5,BLUE);txt('agent runs here',SBX-26,RAILY+18,7.5,'rgba(88,196,221,0.7)','center');
  cx.globalAlpha=1;
  let cap='the overseer sends the task into the box';
  if(c>1.3&&c<2.5){const u=ease((c-1.3)/1.2);glow(lerp(VX-10,SBX+8,u),RAILY,3.4,YEL);cap='key resolved inside the box — one variable';}
  if(c>=2.4&&c<4.7)keyGlyph(SBX+6,RAILY,YEL);
  if(c>=2.8&&c<5.2){buy(SBX+12,RAILY-28,PD,ease(Math.min(1,(c-2.8)/0.7)),GRN);txt('one purchase',PD[0],PD[1]-10,8,'rgba(123,211,137,0.85)','center');cap='the agent makes exactly one purchase';}
  else if(c>=5.2){cap='delete the key · destroy the box';}
  txt(cap,SBX,RAILY+46,8.6,'rgba(232,234,240,0.7)','center');
  txt('the agent runs inside a Daytona box; the key is resolved there and the charge hits one vendor',320,316,10,'rgba(232,234,240,0.7)','center');
  txt('a hijack is trapped in that box — the rest of the universe stays untouched',320,337,10,'rgba(232,234,240,0.45)','center');}

function scene3(t){bg();
  const allow=w<=BUD;
  txt('solution 2 — task adherence (the rules)',24,32,12,'rgba(232,234,240,0.7)');
  universe(0.15);txt('the universe it could buy',300,52,9,'rgba(232,234,240,0.3)','center');
  corridor();agentNode();
  mono('charge $'+w+' → Acme',AX,RAILY+22,8.5,allow?'rgba(123,211,137,0.85)':'rgba(255,123,114,0.85)','center');
  glow(GATEX,RAILY-60,3.5,GRN);txt('owner',GATEX,RAILY-68,8,'rgba(123,211,137,0.8)','center');
  cx.strokeStyle='rgba(123,211,137,0.4)';cx.setLineDash([3,3]);cx.lineWidth=1;cx.beginPath();cx.moveTo(GATEX,RAILY-56);cx.lineTo(GATEX,RAILY-22);cx.stroke();cx.setLineDash([]);
  txt('budget $50',GATEX,RAILY-42,8,'rgba(123,211,137,0.7)','center');
  gateNode(allow?'open':'closed');chamberNode(allow);moneyNode();
  const cyc=t%4,PD=VND[0];
  if(allow){
    if(cyc<2.4)token(lerp(AX+18,CHX,ease(cyc/2.4)),'rgba(232,234,240,0.9)');
    else{token(CHX,YEL,4.2);buy(CHX,RAILY-24,PD,ease(Math.min(1,(cyc-2.4)/0.8)),GRN);txt('one approved purchase',PD[0],PD[1]-10,8,'rgba(123,211,137,0.8)','center');}
  }else{token(lerp(AX+18,GATEX-8,ease(Math.min(1,cyc/1.2))),RED);}
  txt(allow?'ALLOW — passes to the chamber, then one purchase':'DENY — stopped here, nothing is purchased',320,RAILY+54,9.5,allow?GRN:RED,'center');
  txt('a deterministic gate: amount ≤ budget, vendor allowlisted — pure and reproducible',320,308,11.5,'rgba(232,234,240,0.72)','center');
  txt('drag the amount past $50 · the budget comes from the owner record, not the message',320,333,10,'rgba(232,234,240,0.45)','center');}

const itemsList=[['desk',true],['monitor',true],['gift card',false]];
function scene4(t){bg();const c=t%8.6;
  const allow=w<=BUD,done=c>7.0;
  txt('solution 3 — in-spirit adherence (the observer)',24,32,12,'rgba(232,234,240,0.7)');
  txt(done?'trust = rules + spirit + containment':'goal: equip one desk',320,54,done?12:10,done?YEL:'rgba(232,234,240,0.6)','center');
  universe(0.15);
  corridor();agentNode();
  const span=2.3,idx=Math.min(2,Math.floor(c/span)),lt=c-idx*span;
  const it=itemsList[idx],onGoal=it[1],passGate=idx===0?allow:true;
  const rejected=passGate&&!onGoal&&lt>1.0;
  gateNode((idx===0?allow:true)?'open':'closed');eyeNode(rejected?'reject':'idle');chamberNode(true);moneyNode();
  const deskDone=allow&&c>1.7,monDone=c>4.0;
  if(deskDone){cx.strokeStyle='rgba(123,211,137,0.4)';cx.lineWidth=1;cx.beginPath();cx.moveTo(CHX,RAILY-24);cx.lineTo(VND[0][0],VND[0][1]);cx.stroke();glow(VND[0][0],VND[0][1],3,GRN);txt('desk',VND[0][0],VND[0][1]-9,7.5,'rgba(123,211,137,0.8)','center');}
  if(monDone){cx.strokeStyle='rgba(123,211,137,0.4)';cx.lineWidth=1;cx.beginPath();cx.moveTo(CHX,RAILY-24);cx.lineTo(VND[1][0],VND[1][1]);cx.stroke();glow(VND[1][0],VND[1][1],3,GRN);txt('monitor',VND[1][0],VND[1][1]-9,7.5,'rgba(123,211,137,0.8)','center');}
  if(c>4.7){ring(VND[2][0],VND[2][1],4,'rgba(255,123,114,0.55)',1.1);txt('gift card ✗',VND[2][0],VND[2][1]-9,7.5,'rgba(255,123,114,0.7)','center');}
  let tx=AX+18,col='rgba(232,234,240,0.9)';
  if(!passGate){tx=lerp(AX+18,GATEX-8,ease(Math.min(1,lt/1.0)));col=RED;}
  else if(!onGoal){tx=lerp(AX+18,EYEX-6,ease(Math.min(1,lt/1.1)));col=lt>1.0?RED:'rgba(232,234,240,0.9)';}
  else{tx=lerp(AX+18,CHX,ease(Math.min(1,lt/1.6)));col=lt>1.55?YEL:GRN;}
  token(tx,col);txt(it[0],tx,RAILY-14,8.5,col,'center');
  let v;if(!passGate)v=it[0]+': over budget → denied at the gate';
  else if(!onGoal)v=it[0]+': in budget, approved vendor — but off-goal → observer halts it';
  else v=it[0]+': on-goal → charged';
  txt(v,320,RAILY+54,9.5,(passGate&&onGoal)?GRN:RED,'center');
  txt('only the on-goal items get bought — the gift card is left in the universe, untouched',320,308,11.5,'rgba(232,234,240,0.72)','center');
  txt('declared intent = one check per item · reconstructing hidden intent (DRIFT) ≈ 50%',320,333,10,'rgba(232,234,240,0.45)','center');}

const scenes=[
 {t:'The problem: agents can’t be trusted',n:'It starts with a simple handoff. A human gives the agent a credential — a standing, broad key. Now the agent controls the funds, and with that one key it can spend on anything in the universe of possible purchases: any amount, any vendor, any purpose. Nothing limits it, and nothing records who authorized a given charge. Hand over a broad key and you’ve handed over unbounded, untraceable spending power. That’s the trust gap: rules, spirit, and a blast radius if it fails.',d:scene1},
 {t:'Solution 1 — in-depth security',n:'Security comes from where the work runs. The overseer decides but holds no key. The agent runs inside a fresh, attested Daytona sandbox; only there is the key resolved from the 1Password vault, into a single variable. Inside that box the agent makes exactly one purchase — one vendor out of the whole universe — then the key is deleted and the box destroyed. If the agent is hijacked, it’s trapped in that disposable box: the charge still hits only one thing, and the rest of the universe stays untouched.',d:scene2},
 {t:'Solution 2 — task adherence (the rules)',knob:true,n:'Security contains failure; this layer prevents it. Before anything runs, a gate — the overseer — checks the explicit rules: amount within budget, vendor on the allowlist. It’s pure and reproducible, and the budget comes from your record, not the agent’s message. Drag the amount: under budget the gate opens, the charge reaches the chamber, and one approved purchase lights up; over budget it stays shut and nothing in the universe is touched. An out-of-policy request gets no runtime at all.',d:scene3},
 {t:'Solution 3 — in-spirit adherence (the observer)',knob:true,n:'Rules see an action’s shape — amount, vendor — never its purpose. So a third guardian watches: the observer. For a mission like equipping a new desk, it weighs each charge against the declared goal. The desk and monitor are on-goal and get bought; the gift card is in budget and an approved vendor — yet off-goal, so the observer halts it and it’s left untouched in the universe. Declaring the goal up front makes this one check per item, where reconstructing hidden intent (DRIFT) reaches only about fifty percent.',d:scene4}
];

let cur=0,t0=performance.now();
const ttl=document.getElementById('ttl'),nar=document.getElementById('nar'),cnt=document.getElementById('cnt'),dotsEl=document.getElementById('dots');
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
scenes.forEach((s,i)=>{const d=document.createElement('span');d.onclick=()=>go(i);dotsEl.appendChild(d);});
function paintDots(){[...dotsEl.children].forEach((d,i)=>d.classList.toggle('on',i===cur));}
function go(i){cur=(i+scenes.length)%scenes.length;t0=performance.now();ttl.textContent=scenes[cur].t;nar.textContent=scenes[cur].n;cnt.textContent='scene '+(cur+1)+' of '+scenes.length;knobRow.style.display=scenes[cur].knob?'flex':'none';paintDots();if(reduced)scenes[cur].d(5);}
document.getElementById('prev').onclick=()=>go(cur-1);
document.getElementById('next').onclick=()=>go(cur+1);
go(0);
if(!reduced)(function loop(){scenes[cur].d((performance.now()-t0)/1000);requestAnimationFrame(loop);})();
</script>
</body>
</html>"""
