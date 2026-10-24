import re

# Den bombsäkra koden (sorterar på Vinst i kr)
new_js = """async function loadHighscore() {
    const body = document.getElementById('highscoreBody');
    if (!body) return;
    body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">Laddar...</td></tr>';
    
    // 1. Hämta alla spelare (UTAN att sortera på saldo)
    const { data: profiles } = await supabaseClient.from('profiles').select('id, display_name, username, balance');
    const { data: markets } = await supabaseClient.from('freemarket_markets').select('id, status').neq('status', 'open');
    const { data: trades } = await supabaseClient.from('freemarket_trades').select('*');

    if (!profiles) return;

    // 2. Räkna ut vinst i kronor för varje spelare
    const calculatedData = profiles.map(p => {
        const pTrades = trades ? trades.filter(t => t.buyer_id === p.id || t.seller_id === p.id) : [];
        let totalInvested = 0;
        let totalReturned = 0;
        
        pTrades.forEach(t => {
            const market = markets ? markets.find(m => m.id === t.market_id) : null;
            // Kolla bara avslutade matcher
            if (market && (market.status === 'resolved_yes' || market.status === 'resolved_no')) {
                const winOutcome = market.status === 'resolved_yes' ? 'yes' : 'no';
                const sellerWon = t.seller_outcome === winOutcome;
                const buyerWon = !sellerWon;
                const won = (t.buyer_id === p.id) ? buyerWon : sellerWon;
                
                totalInvested += Number(t.amount);
                if (won) totalReturned += (Number(t.amount) * Number(t.odds));
            }
        });

        const netProfit = totalReturned - totalInvested;
        return { ...p, total: pTrades.length, netProfit, totalInvested };
    });

    // 3. SORTERA PÅ NETTOVINST (Högst vinst först)
    calculatedData.sort((a, b) => b.netProfit - a.netProfit);

    // 4. Rita ut tabellen
    body.innerHTML = calculatedData.map((p, i) => {
        const roundedProfit = Math.round(p.netProfit);
        const profitStr = roundedProfit > 0 ? '+' + roundedProfit + ' kr' : roundedProfit + ' kr';
        const profitColor = roundedProfit > 0 ? 'var(--green)' : roundedProfit < 0 ? 'var(--red)' : 'var(--muted)';

        return `
        <tr>
            <td style="color:${i === 0 ? 'var(--gold)' : 'inherit'};font-weight:800">#${i + 1}</td>
            <td>${typeof esc === 'function' ? esc(p.display_name || p.username || 'Okänd') : (p.display_name || p.username)}</td>
            <td style="text-align:right;color:var(--green);font-weight:800">${p.balance} kr</td>
            <td style="text-align:right;color:${profitColor};font-weight:800">${profitStr}</td>
            <td style="text-align:right">${p.totalInvested} kr</td>
            <td style="text-align:right">${p.total}</td>
        </tr>`;
    }).join('');
}

"""
# Skriv över funktionen i båda filerna
for filename in ["admin.html", "index.html"]:
    with open(filename, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Leta upp start och slut på loadHighscore
    start_idx = html.find("async function loadHighscore() {")
    if start_idx != -1:
        # Hitta nästa funktion för att veta var den slutar
        end_idx = html.find("async function loadHistory", start_idx)
        if end_idx == -1: 
            end_idx = html.find("</script>", start_idx)
        
        html = html[:start_idx] + new_js + "\n" + html[end_idx:]
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"KLART! {filename} rankar nu efter Netto Vinst.")
    else:
        print(f"FEL: Kunde inte hitta loadHighscore i {filename}.")
