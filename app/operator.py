"""Operator view (conversation-design §7) — a bare two-up demo surface:
left = the owner's WhatsApp thread, right = the agent's transactions (allowed +
denied). Polls /ops/data. No build step, no framework — one self-contained page.
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Claim-an-Agent — operator view</title>
<style>
  :root { --bg:#0b141a; --panel:#111b21; --in:#005c4b; --out:#202c33; --line:#222d34;
          --ok:#16a34a; --deny:#dc2626; --muted:#8696a0; --txt:#e9edef; }
  * { box-sizing:border-box; }
  body { margin:0; font:15px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;
         background:var(--bg); color:var(--txt); }
  header { padding:12px 18px; border-bottom:1px solid var(--line); display:flex;
           align-items:center; gap:14px; }
  header h1 { font-size:16px; margin:0; font-weight:600; }
  header .who { color:var(--muted); font-size:13px; }
  .wrap { display:grid; grid-template-columns:1fr 1fr; gap:0; height:calc(100vh - 50px); }
  .pane { overflow-y:auto; padding:16px; }
  .pane.left { border-right:1px solid var(--line); background:#0c1317; }
  .pane h2 { font-size:12px; text-transform:uppercase; letter-spacing:.08em;
             color:var(--muted); margin:0 0 12px; }
  .bubble { max-width:78%; padding:8px 11px; border-radius:10px; margin:6px 0;
            white-space:pre-wrap; word-wrap:break-word; }
  .in  { background:var(--in);  margin-left:auto; border-bottom-right-radius:3px; }
  .out { background:var(--out); margin-right:auto; border-bottom-left-radius:3px; }
  .bubble .t { display:block; font-size:10px; color:var(--muted); margin-top:3px; }
  .txn { border-left:4px solid var(--muted); background:var(--panel); border-radius:6px;
         padding:10px 12px; margin:8px 0; }
  .txn.allowed { border-color:var(--ok); }
  .txn.denied  { border-color:var(--deny); }
  .txn .top { display:flex; justify-content:space-between; align-items:baseline; }
  .txn .vendor { font-weight:600; }
  .txn .amt { font-variant-numeric:tabular-nums; }
  .txn .meta { color:var(--muted); font-size:12px; margin-top:4px; word-break:break-all; }
  .badge { font-size:11px; padding:1px 7px; border-radius:10px; }
  .badge.allowed { background:rgba(22,163,74,.18); color:#4ade80; }
  .badge.denied  { background:rgba(220,38,38,.18); color:#f87171; }
  .empty { color:var(--muted); font-style:italic; }
</style>
</head>
<body>
<header>
  <h1>Claim-an-Agent — operator view</h1>
  <span class="who" id="who">waiting for activity…</span>
</header>
<div class="wrap">
  <div class="pane left"><h2>📱 WhatsApp thread</h2><div id="chat"></div></div>
  <div class="pane right"><h2>💳 Agent transactions (allowed + denied)</h2><div id="txns"></div></div>
</div>
<script>
function esc(s){return s.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function fmt(s){return esc(s).replace(/\\*([^*]+)\\*/g,'<b>$1</b>');}
function time(ts){try{return new Date(ts).toLocaleTimeString();}catch(e){return '';}}
function money(c){return '$'+(c/100).toFixed(2);}
async function tick(){
  const q = new URLSearchParams(location.search).get('phone');
  const r = await fetch('/ops/data'+(q?('?phone='+encodeURIComponent(q)):''));
  const d = await r.json();
  document.getElementById('who').textContent =
    d.phone ? ('owner: '+d.phone+'  ·  '+d.transactions.length+' actions') : 'waiting for activity…';
  const chat = d.messages.map(m =>
    `<div class="bubble ${m.direction==='in'?'in':'out'}">${fmt(m.text)}<span class="t">${time(m.ts)}</span></div>`
  ).join('') || '<div class="empty">No messages yet.</div>';
  document.getElementById('chat').innerHTML = chat;
  const txns = d.transactions.slice().reverse().map(t => {
    const ok = t.outcome === 'allowed';
    const line2 = ok
      ? `receipt ${t.charge_id||'—'} · sandbox ${(t.sandbox_id||'—').slice(0,8)}`
      : `denied — ${t.reason} · no charge, no sandbox`;
    return `<div class="txn ${t.outcome}">
       <div class="top">
         <span class="vendor">${esc(t.vendor||t.intent||'—')}</span>
         <span class="amt">${money(t.amount_cents||0)}
           <span class="badge ${t.outcome}">${ok?'PAID':'DENIED'}</span></span>
       </div>
       <div class="meta">${esc(line2)}</div>
       <div class="meta">${esc(t.intent||'')} · ${time(t.ts)}</div>
     </div>`;
  }).join('') || '<div class="empty">No transactions yet.</div>';
  document.getElementById('txns').innerHTML = txns;
  const c=document.querySelector('.pane.left'); c.scrollTop=c.scrollHeight;
}
tick(); setInterval(tick, 1500);
</script>
</body>
</html>"""
