import re

with open("admin.html", "r", encoding="utf-8") as f:
    html = f.read()

# A. Ta bort decimalerna i JavaScriptet (avrunda till heltal)
old_js_profit = "const profitStr = p.netProfit > 0 ? '+' + p.netProfit + ' kr' : p.netProfit + ' kr';"
new_js_profit = "const roundedProfit = Math.round(p.netProfit); const profitStr = roundedProfit > 0 ? '+' + roundedProfit + ' kr' : roundedProfit + ' kr';"
html = html.replace(old_js_profit, new_js_profit)

# B. Lägg till mobil-CSS för att göra tabellen kompakt
mobile_css = """
  @media (max-width: 768px) {
    .admin-table th, .admin-table td {
        padding: 8px 4px !important;
        font-size: 11px !important;
        white-space: nowrap !important;
    }
  }
"""
if '@media (max-width: 768px)' not in html:
    html = html.replace('</style>', mobile_css + '\n</style>')
else:
    # Om det redan finns media queries, lägg bara till denna i slutet av style
    html = html.replace('</style>', mobile_css + '\n</style>')

with open("admin.html", "w", encoding="utf-8") as f:
    f.write(html)
print("KLART! Decimaler borttagna och tabellen gor sig mindre pa mobilen.")
