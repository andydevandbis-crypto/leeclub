import re

with open("admin.html", "r", encoding="utf-8") as f:
    html = f.read()

# A. Byt ut kolumnrubrikerna (Ta bort %, lägg till Belopp)
old_table = '''<table class="admin-table" style="width:100%;">
            <thead><tr><th>Rank</th><th>Spelare</th><th style="text-align:right">Saldo</th><th style="text-align:right">ROI</th><th style="text-align:right">Vinstprocent</th><th style="text-align:right">Antal Spel</th></tr></thead>
            <tbody id="highscoreBody"></tbody>
          </table>'''

new_table = '''<table class="admin-table" style="width:100%;">
            <thead><tr><th>Rank</th><th>Spelare</th><th style="text-align:right">Saldo</th><th style="text-align:right">Vinst (kr)</th><th style="text-align:right">Insats (kr)</th><th style="text-align:right">Antal Spel</th></tr></thead>
            <tbody id="highscoreBody"></tbody>
          </table>'''
html = html.replace(old_table, new_table)

# B. Byt ut funktionen för att räkna ut vinst i kronor
start_idx = html.find("async function loadHighscore() {")
end_idx = html.find("async function loadHistory() {")

if start_idx != -1 and end_idx != -1:
    new_js = """async function loadHighscore() {
    const body = document.getElementById('highscoreBody');
    body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Laddar...</td></tr>';
    
    // 1. Hämta alla spelare
    const { data: profiles } = await supabaseClient.from('profiles').select('id, display_name, username, balance').limit(20);
    if (!profiles) return;
    
    // 2. Hämta alla avslutade matcher och trades för att räkna ut vinsten i kr
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
                
                // Om man vann får man tillbaka insats * odds
                if (won) { totalReturned += (Number(t.amount) * Number(t.odds)); }
                // Insatsen dras alltid
                totalInvested += Number(t.amount);
            }
        });

        const total = pTrades.length;
        const netProfit = totalReturned - totalInvested; // Vinst i kronor
        
        return { ...p, total, netProfit, totalInvested };
    });

    // 3. Sortera på Netto vinst i kronor (högst först)
    calculatedData.sort((a, b) => b.netProfit - a.netProfit);

    body.innerHTML = calculatedData.map((p, i) => {
        const profitStr = p.netProfit > 0 ? '+' + p.netProfit + ' kr' : p.netProfit + ' kr';
        const profitColor = p.netProfit > 0 ? 'var(--green)' : p.netProfit < 0 ? 'var(--red)' : 'var(--muted)';

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
    html = html[:start_idx] + new_js + html[end_idx:]

with open("admin.html", "w", encoding="utf-8") as f:
    f.write(html)
print("KLART! Highscore visar nu vinst i kronor istallet for procent.")
