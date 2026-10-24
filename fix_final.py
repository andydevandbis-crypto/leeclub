import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Hitta hela loadMarkets-funktionen
start_idx = html.find("async function loadMarkets() {")
end_idx = html.find("async function loadMyMatches()")
if end_idx == -1: end_idx = html.find("function doMatch(")

if start_idx != -1 and end_idx != -1:
    new_func = """async function loadMarkets() {
    const container = document.getElementById('fm-markets-list');
    if (!container) return;
    container.innerHTML = '<div style="color: var(--muted); grid-column: 1/-1;">Laddar...</div>';

    const { data: myTrades } = await supabaseClient.from('freemarket_trades').select('market_id').or(`buyer_id.eq.${currentUserId},seller_id.eq.${currentUserId}`);
    const myMarketIds = myTrades ? myTrades.map(t => t.market_id) : [];

    const { data: markets } = await supabaseClient.from('freemarket_markets').select('*, freemarket_orders(*)').eq('status', 'open').order('created_at', { ascending: false });
    
    if(!markets || markets.length === 0) { 
        container.innerHTML = '<div style="color: var(--muted); grid-column: 1/-1;">Inga marknader.</div>'; 
        return; 
    }

    const availableMarkets = markets.filter(m => m.creator_id !== currentUserId && !myMarketIds.includes(m.id));

    if (availableMarkets.length === 0) {
        container.innerHTML = '<div style="color: var(--muted); grid-column: 1/-1;">Inga tillgängliga marknader just nu.</div>';
        return;
    }

    container.innerHTML = availableMarkets.map(m => {
        const order = m.freemarket_orders[0]; if(!order || Number(order.amount) <= 0) return '';
        const sP = order.outcome === 'yes' ? 'Ja' : 'Nej';
        const bP = order.outcome === 'yes' ? 'Nej' : 'Ja';
        let isLocked = false, timeStr = "";
        if (m.match_time) {
            const d = new Date(m.match_time); timeStr = d.toLocaleString('sv-SE', { month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit' });
            if (d < new Date()) isLocked = true;
        }

        let btn = isLocked 
            ? '<span class="fm-lock">LÅST</span>' 
            : `<button onclick="doMatch('${order.id}', '${m.id}', '${order.user_id}', ${order.odds}, ${order.amount}, '${order.outcome}')" class="fm-match-btn">Matcha (${bP})</button>`;

        return `<div class="fm-card ${isLocked ? 'locked-card' : ''}">
          <div class="fm-card-top"><span class="fm-time">${timeStr}</span></div>
          <div class="fm-q">${esc(m.question)}</div>
          <div class="fm-info" style="display:flex; justify-content:space-between; align-items:center; padding:10px; gap:8px;">
            <div style="flex:1; min-width:0;">
              <div class="fm-sells">Säljs: ${sP}</div>
              <div class="fm-odds-row"><span class="fm-odds">Odds ${parseFloat(order.odds).toFixed(2)}</span><span class="fm-amt">${order.amount} kr</span></div>
              <div style="font-size:10px; color:var(--muted); margin-top:2px;">Köparens kostnad: ${(order.amount * (order.odds - 1)).toFixed(0)} kr · Vinst: ${(order.amount * order.odds).toFixed(0)} kr</div>
            </div>
            <div style="flex-shrink: 0;">
              ${btn}
            </div>
          </div>
        </div>`;
    }).join('');
}

"""
    html = html[:start_idx] + new_func + html[end_idx:]

# Lägg till rätt CSS för att korten ska bli breda på mobilen och få färger
new_css = """
  .fm-card.locked-card { border-color: var(--red) !important; box-shadow: 0 0 0 1px var(--red) inset !important; }
  @media (max-width: 768px) {
    .fm-layout { display: flex !important; flex-direction: column !important; width: 100% !important; padding: 12px !important; }
    .fm-form { width: 100% !important; box-sizing: border-box !important; }
    .fm-list { display: flex !important; flex-direction: column !important; width: 100% !important; gap: 12px !important; }
    .fm-card { width: 100% !important; box-sizing: border-box !important; }
  }
"""
if '.fm-card.locked-card' not in html:
    html = html.replace('</style>', new_css + '\n</style>')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("KLART!")
