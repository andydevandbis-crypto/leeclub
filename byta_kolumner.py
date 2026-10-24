# Byter plats på Saldo och Vinst i HTML-tabellen och i JavaScriptet
for filename in ["admin.html", "index.html"]:
    with open(filename, "r", encoding="utf-8") as f:
        html = f.read()

    # A. Byt plats i HTML-tabellen (thead)
    old_thead = '<th>Rank</th><th>Spelare</th><th style="text-align:right">Saldo</th><th style="text-align:right">Vinst (kr)</th><th style="text-align:right">Insats (kr)</th><th style="text-align:right">Antal Spel</th>'
    new_thead = '<th>Rank</th><th>Spelare</th><th style="text-align:right">Vinst (kr)</th><th style="text-align:right">Saldo</th><th style="text-align:right">Insats (kr)</th><th style="text-align:right">Antal Spel</th>'
    html = html.replace(old_thead, new_thead)

    # B. Byt plats i JavaScript-loopen (tbody)
    old_row = '''<td>${typeof esc === 'function' ? esc(p.display_name || p.username || 'Okänd') : (p.display_name || p.username)}</td>
            <td style="text-align:right;color:var(--green);font-weight:800">${p.balance} kr</td>
            <td style="text-align:right;color:${profitColor};font-weight:800">${profitStr}</td>'''

    new_row = '''<td>${typeof esc === 'function' ? esc(p.display_name || p.username || 'Okänd') : (p.display_name || p.username)}</td>
            <td style="text-align:right;color:${profitColor};font-weight:800">${profitStr}</td>
            <td style="text-align:right;color:var(--green);font-weight:800">${p.balance} kr</td>'''
            
    html = html.replace(old_row, new_row)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"KLART! Bytte plats pa Saldo och Vinst i {filename}.")
