"""Judge-facing landing + interactive demo at "/".

Pitch + a "Run Scopebound" CTA that opens an in-browser chat (driving the real
backend via /sim — no phone required) next to the live dashboard. The WhatsApp
path still works in parallel; this just makes the submission URL self-contained.
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Scopebound — claim a spending agent by text</title>
<style>
  :root { --bg:#0b141a; --panel:#111b21; --line:#223; --in:#005c4b; --out:#202c33;
          --ok:#16a34a; --deny:#dc2626; --muted:#8696a0; --txt:#e9edef; --accent:#25d366; }
  * { box-sizing:border-box; }
  body { margin:0; font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--txt); }
  a { color:var(--accent); }
  .wrap { max-width:1100px; margin:0 auto; padding:28px 20px 60px; }
  /* hero */
  .hero h1 { font-size:40px; margin:8px 0 6px; letter-spacing:-0.5px; }
  .hero .tag { font-size:18px; color:var(--muted); margin:0 0 18px; }
  .q { border-left:3px solid var(--accent); padding:10px 16px; margin:18px 0; color:#cfe; font-style:italic; background:#0e1a17; border-radius:0 8px 8px 0; }
  .lead { font-size:15.5px; color:#d6dde0; max-width:760px; }
  .explainer { width:100%; max-width:800px; height:865px; border:1px solid var(--line);
               border-radius:12px; background:#0d0f14; display:block; margin:20px auto 8px; }
  .cta-row { display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-top:8px; }
  .cta { display:inline-flex; align-items:center; gap:10px; background:var(--accent); color:#04231a;
         font-weight:700; font-size:17px; border:0; border-radius:30px; padding:14px 28px; cursor:pointer; }
  .cta:hover { filter:brightness(1.07); }
  .sub { color:var(--muted); font-size:13px; margin-top:12px; }
  .badges { color:var(--muted); font-size:13px; margin-top:18px; }
  /* app */
  #app { display:none; margin-top:26px; }
  .split { display:grid; grid-template-columns:1fr 1fr; gap:16px; height:560px; }
  .pane { background:#0c1317; border:1px solid var(--line); border-radius:12px; display:flex; flex-direction:column; overflow:hidden; }
  .pane h2 { font-size:12px; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin:0; padding:12px 14px; border-bottom:1px solid var(--line); }
  .chat { flex:1; overflow-y:auto; padding:14px; }
  .bubble { max-width:82%; padding:8px 11px; border-radius:10px; margin:6px 0; white-space:pre-wrap; word-wrap:break-word; }
  .b-in  { background:var(--in);  margin-left:auto; border-bottom-right-radius:3px; }
  .b-out { background:var(--out); margin-right:auto; border-bottom-left-radius:3px; }
  .chips { display:flex; flex-wrap:wrap; gap:6px; padding:10px 12px; border-top:1px solid var(--line); }
  .chip { background:#16242c; border:1px solid #2b3b44; color:#cfe; border-radius:16px; padding:5px 10px; font-size:12.5px; cursor:pointer; }
  .chip:hover { background:#1d3038; }
  .composer { display:flex; gap:8px; padding:10px 12px; border-top:1px solid var(--line); }
  .composer input { flex:1; background:#0b141a; border:1px solid #2b3b44; color:var(--txt); border-radius:18px; padding:9px 13px; }
  .composer button { background:var(--accent); color:#04231a; border:0; border-radius:18px; padding:0 16px; font-weight:700; cursor:pointer; }
  .dash { flex:1; overflow-y:auto; padding:12px 14px; }
  .ctx { padding:10px 14px; border-bottom:1px solid var(--line); color:var(--muted); font-size:12.5px; }
  .ctx b { color:var(--txt); }
  .txn { border-left:4px solid var(--muted); background:var(--panel); border-radius:6px; padding:9px 11px; margin:8px 0; }
  .txn.allowed { border-color:var(--ok); } .txn.denied { border-color:var(--deny); }
  .txn .top { display:flex; justify-content:space-between; align-items:baseline; }
  .txn .vendor { font-weight:600; } .txn .meta { color:var(--muted); font-size:12px; margin-top:3px; word-break:break-all; }
  .pill { font-size:10.5px; padding:1px 7px; border-radius:10px; }
  .pill.allowed { background:rgba(22,163,74,.18); color:#4ade80; } .pill.denied { background:rgba(220,38,38,.18); color:#f87171; }
  .empty { color:var(--muted); font-style:italic; }
  .toolbar { display:flex; gap:10px; align-items:center; margin-bottom:12px; }
  .toolbar button { background:#16242c; border:1px solid #2b3b44; color:#cfe; border-radius:16px; padding:7px 14px; cursor:pointer; }
  @media (max-width:820px){ .axes{grid-template-columns:1fr;} .split{grid-template-columns:1fr; height:auto;} .pane{height:420px;} }
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>🔐 Scopebound</h1>
    <p class="tag">Claim an AI spending agent by text. It acts <b>as you</b> — and only within the scope you set.</p>
    <div class="q">When your agent acts, is it acting as itself, or as you? Where does its authority come from, and who answers for what it does?</div>
    <p class="lead">Step through how it works below — the trust gap, then the three layers that close it:
      a disposable <b>Daytona</b> runtime, a deterministic <b>rule gate</b>, and an <b>intent observer</b>
      that stops in-budget, on-vendor, but <i>off-task</i> spend. Then run it live.</p>
    <iframe class="explainer" src="/explainer" title="How Scopebound works — interactive explainer" loading="lazy"></iframe>
    <div class="cta-row">
      <button class="cta" onclick="launch()">▶ Run Scopebound</button>
      <span class="sub">Runs the real backend in your browser — no phone needed. (You can also text it on WhatsApp.)</span>
    </div>
    <div class="badges">Built on <b>1Password</b> + <b>Daytona</b> · payments via <b>Stripe</b> (test mode) + Connect · orchestrator on Railway.</div>
  </div>

  <div id="app">
    <div class="toolbar">
      <button onclick="autoplay()">▶ Auto-play the demo</button>
      <button onclick="reset()">↻ New session</button>
      <span class="sub" id="hint">Tip: click the chips below in order, or just auto-play.</span>
    </div>
    <div class="split">
      <div class="pane">
        <h2>💬 You (a brand-new user)</h2>
        <div class="chat" id="chat"></div>
        <div class="chips" id="chips"></div>
        <div class="composer"><input id="inp" placeholder="type a message…" onkeydown="if(event.key==='Enter')hit()"/><button onclick="hit()">Send</button></div>
      </div>
      <div class="pane">
        <h2>📊 Live dashboard — what the agent did (and didn't)</h2>
        <div class="ctx" id="ctx">no activity yet</div>
        <div class="dash" id="dash"><div class="empty">Charges and denials appear here in real time.</div></div>
      </div>
    </div>
  </div>
</div>
<script>
let PHONE = 'web:' + Math.random().toString(36).slice(2,10);
let poll = null;
const SCRIPT = ["CLAIM","Budgetbot","budget 400","allow Acme, Staples",
  "Set up the new hire's desk: keyboard, mouse, monitor","espresso machine $250 from Acme","hey"];
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function fmt(s){return esc(s).replace(/\\*([^*]+)\\*/g,'<b>$1</b>').replace(/\\n/g,'<br>');}
function money(c){return '$'+((c||0)/100).toFixed(2);}
const sleep = ms => new Promise(r=>setTimeout(r,ms));

function launch(){
  document.getElementById('app').style.display='block';
  document.getElementById('app').scrollIntoView({behavior:'smooth'});
  renderChips();
  if(!poll) poll = setInterval(refresh, 1800);
  refresh();
}
function renderChips(){
  document.getElementById('chips').innerHTML = SCRIPT.map((m,i)=>
    `<span class="chip" onclick="send(${JSON.stringify(m).replace(/"/g,'&quot;')})">${esc(m.length>34?m.slice(0,32)+'…':m)}</span>`).join('');
}
function bubble(cls, html){
  const el=document.createElement('div'); el.className='bubble '+cls; el.innerHTML=html;
  const c=document.getElementById('chat'); c.appendChild(el); c.scrollTop=c.scrollHeight; return el;
}
async function send(text){
  bubble('b-in', esc(text));
  const pend = bubble('b-out','⏳ …');
  try{
    const r = await fetch('/sim',{method:'POST',headers:{'content-type':'application/json'},
      body:JSON.stringify({from_phone:PHONE,text})});
    const d = await r.json(); pend.innerHTML = fmt(d.reply);
  }catch(e){ pend.textContent='⚠️ network error'; }
  refresh();
}
function hit(){ const i=document.getElementById('inp'); if(i.value.trim()){ send(i.value.trim()); i.value=''; } }
async function autoplay(){ for(const m of SCRIPT){ await send(m); await sleep(800); } }
function reset(){ PHONE='web:'+Math.random().toString(36).slice(2,10); document.getElementById('chat').innerHTML='';
  document.getElementById('dash').innerHTML='<div class="empty">Charges and denials appear here in real time.</div>';
  document.getElementById('ctx').textContent='no activity yet'; }
async function refresh(){
  try{
    const d = await (await fetch('/ops/data?phone='+encodeURIComponent(PHONE))).json();
    const o = d.owner||{};
    document.getElementById('ctx').innerHTML = (o.agent||o.goal||d.transactions.length)
      ? `agent <b>${esc(o.agent||'—')}</b> · 🎯 ${esc(o.goal||'no goal yet')} · budget $${o.budget_cents!=null?(o.budget_cents/100).toFixed(0):'—'} · vendors ${o.allowlist?o.allowlist.map(esc).join(', '):'—'} · mode ${esc(d.mode||'simple')}`
      : 'no activity yet';
    const t = d.transactions.slice().reverse().map(t=>{
      const ok=t.outcome==='allowed';
      const l2 = ok ? `receipt ${esc(t.charge_id||'—')} · sandbox ${esc((t.sandbox_id||'—').slice(0,8))}`
                    : `denied — ${esc(t.reason)} · no charge`;
      return `<div class="txn ${t.outcome}"><div class="top"><span class="vendor">${esc(t.vendor||t.intent||'—')}</span>
        <span>${money(t.amount_cents)} <span class="pill ${t.outcome}">${ok?'PAID':'DENIED'}</span></span></div>
        <div class="meta">${esc(t.intent||'')} · ${l2}</div></div>`;
    }).join('');
    document.getElementById('dash').innerHTML = t || '<div class="empty">Charges and denials appear here in real time.</div>';
  }catch(e){}
}
</script>
</body>
</html>"""
