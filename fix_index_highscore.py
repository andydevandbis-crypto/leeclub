import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# A. Byt ut HTML-tabellen för Highscore till den med 6 kolumner
start_sec = html.find('<section class="panel" id="highscoreView"')
end_sec = html.find('</section>', start_sec) + 10

if start_sec != -1 and end_sec != -1:
    new_sec = '''<section class="panel" id="highscoreView" style="display:none;">
        <div class="panel-head"><h2>Highscore</h2></div>
        <div style="padding: 24px; overflow-y: auto;">
          <div class="table-wrap">
            <table class="admin-table" style="width:100%;">
              <thead><tr><th>Rank</th><th>Spelare</th><th style="text-align:right">Saldo</th><th style="text-align:right">Vinst (kr)</th><th style="text-align:right">Insats (kr)</th><th style="text-align:right">Antal Spel</th></tr></thead>
              <tbody id="highscoreBody"><tr><td colspan="6" style="text-align:center; color:var(--muted);">Laddar...</td></tr></tbody>
            </table>
          </div>
        </div>
      </section>'''
    html = html[:start_sec] + new_sec + html[end_sec:]

# B. Byt ut JavaScript-funktionen loadHighscore
start_js = html.find("async function loadHighscore() {")
end_js = html.find("async function loadHistory() {")

if start_js != -1 and end_js != -1:
    new_js = """async function loadHighscore() {
    const body = document.getElementById('highscoreBody');
    body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Laddar...</td></tr>';
    
    const { data: profiles } = await supabaseClient.from('profiles').select('id, display_name, username, balance').limit(20);
    if (!profiles) return;
    
    const { data: markets } = await supabaseClient.from('freemarket_markets').select('id, status').neq('status', 'open');
    const { data: trades } = await supabaseClient.from('freemarket_trades').select('*');

    const calculatedData = profiles.map(p => {
        const pTrades = trades ? trades.filter(t => t.buyer_id === p.id || t.seller_id === p.id) : [];
        let totalInvested = 0, totalReturned = 0;
        
        pTrades.forEach(t => {
            const market = markets ? markets.find(m => m.id === t.market_id) : null;
            if (market && market.status.startsWith('resolved')) {
                const winOutcome = market.status === 'resolved_yes' ? 'yes' : 'no';
                const sellerWon = t.seller_outcome === winOutcome;
                const buyerWon = !sellerWon;
                const won = (t.buyer_id === p.id) ? buyerWon : sellerWon;
                
                if (won) { totalReturned += (Number(t.amount) * Number(t.odds)); }
                totalInvested += Number(t.amount);
            }
        });

        const total = pTrades.length;
        const netProfit = totalReturned - totalInvested;
        
        return { ...p, total, netProfit, totalInvested };
    });

    calculatedData.sort((a, b) => b.netProfit - a.netProfit);

    body.innerHTML = calculatedData.map((p, i) => {
        const roundedProfit = Math.round(p.netProfit);
        const profitStr = roundedProfit > 0 ? '+' + roundedProfit + ' kr' : roundedProfit + ' kr';
        const profitColor = roundedProfit > 0 ? 'var(--green)' : roundedProfit < 0 ? 'var(--red)' : 'var(--muted)';

        return `
        <tr>
            <td style="color:${i === 0 ? 'var(--gold)' : 'inherit'};font-weight:800">#${i + 1}</td>
            <td>${esc(p.display_name || p.username || 'Okänd')}</td>
            <td style="text-align:right;color:var(--green);font-weight:800">${p.balance} kr</td>
            <td style="text-align:right;color:${profitColor};font-weight:800">${profitStr}</td>
            <td style="text-align:right">${p.totalInvested} kr</td>
            <td style="text-align:right">${p.total}</td>
        </tr>`;
    }).join('');
}

"""
    html = html[:start_js] + new_js + html[end_js:]

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("KLART! index.html har nu exakt samma Highscore-tabell som admin.html.")
