import re

with open("admin.html", "r", encoding="utf-8") as f:
    html = f.read()

# A. Byt ut HTML-tabellen för Highscore
old_table = '''<table class="admin-table" style="width:100%;">
            <thead><tr><th>#</th><th>Spelare</th><th style="text-align:right">Saldo</th></tr></thead>
            <tbody id="highscoreBody"></tbody>
          </table>'''

new_table = '''<table class="admin-table" style="width:100%;">
            <thead><tr><th>Rank</th><th>Spelare</th><th style="text-align:right">Saldo</th><th style="text-align:right">ROI</th><th style="text-align:right">Vinstprocent</th><th style="text-align:right">Antal Spel</th></tr></thead>
            <tbody id="highscoreBody"></tbody>
          </table>'''
html = html.replace(old_table, new_table)

# B. Byt ut JavaScript-funktionen loadHighscore
start_idx = html.find("async function loadHighscore() {")
end_idx = html.find("async function loadHistory() {")

if start_idx != -1 and end_idx != -1:
    new_js = """async function loadHighscore() {
    const body = document.getElementById('highscoreBody');
    body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Laddar...</td></tr>';
    
    // Hämta spelare
    const { data: profiles, error: pErr } = await supabaseClient.from('profiles').select('id, display_name, username, balance').order('balance', { ascending: false }).limit(20);
    if (pErr || !profiles) { body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--red)">Kunde inte hämta</td></tr>'; return; }
    
    // Hämta avslutade matcher och trades för att räkna ut ROI
    const { data: markets } = await supabaseClient.from('freemarket_markets').select('id, status').neq('status', 'open');
    const { data: trades } = await supabaseClient.from('freemarket_trades').select('*');

    if (!profiles.length) { 
        body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Inga spelare ännu.</td></tr>'; 
        return; 
    }

    body.innerHTML = profiles.map((p, i) => {
        const pTrades = trades ? trades.filter(t => t.buyer_id === p.id || t.seller_id === p.id) : [];
        let wins = 0, totalInvested = 0, totalReturned = 0;
        
        pTrades.forEach(t => {
            const market = markets ? markets.find(m => m.id === t.market_id) : null;
            if (market && market.status.startsWith('resolved')) {
                const winOutcome = market.status === 'resolved_yes' ? 'yes' : 'no';
                const sellerWon = t.seller_outcome === winOutcome;
                const buyerWon = !sellerWon;
                const won = (t.buyer_id === p.id) ? buyerWon : sellerWon;
                if (won) { wins++; totalReturned += (Number(t.amount) * Number(t.odds)); }
                totalInvested += Number(t.amount);
            }
        });

        const total = pTrades.length;
        const winRate = total > 0 ? Math.round((wins / total) * 100) + '%' : '0%';
        let roi = 0;
        if (totalInvested > 0) roi = Math.round(((totalReturned - totalInvested) / totalInvested) * 100);
        const roiStr = roi > 0 ? '+' + roi + '%' : roi + '%';
        const roiColor = roi > 0 ? 'var(--green)' : roi < 0 ? 'var(--red)' : 'var(--muted)';

        return `
        <tr>
            <td style="color:${i === 0 ? 'var(--gold)' : 'inherit'};font-weight:800">#${i + 1}</td>
            <td>${esc(p.display_name || p.username || 'Okänd')}</td>
            <td style="text-align:right;color:var(--green);font-weight:800">${p.balance} kr</td>
            <td style="text-align:right;color:${roiColor};font-weight:800">${roiStr}</td>
            <td style="text-align:right">${winRate}</td>
            <td style="text-align:right">${total}</td>
        </tr>`;
    }).join('');
}

"""
    html = html[:start_idx] + new_js + html[end_idx:]

with open("admin.html", "w", encoding="utf-8") as f:
    f.write(html)
print("KLART! Highscore-tabellen ar nu fixad.")
