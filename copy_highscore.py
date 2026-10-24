import re

# Läs admin.html
with open("admin.html", "r", encoding="utf-8") as f:
    admin_html = f.read()

# Extrahera Highscore-sektionen (HTML)
html_match = re.search(r'(<section[^>]*id="highscoreView".*?</section>)', admin_html, flags=re.DOTALL)
if not html_match:
    print("FEL: Kunde inte hitta highscoreView i admin.html")
    exit()
admin_html_section = html_match.group(1)

# Extrahera Highscore-funktionen (JS)
js_match = re.search(r'(async function loadHighscore\(\) \{.*?)(?=async function loadHistory|\Z)', admin_html, flags=re.DOTALL)
if not js_match:
    print("FEL: Kunde inte hitta loadHighscore i admin.html")
    exit()
admin_js_function = js_match.group(1)

# Läs index.html
with open("index.html", "r", encoding="utf-8") as f:
    index_html = f.read()

# Ersätt sektionen i index.html
index_html = re.sub(r'<section[^>]*id="highscoreView".*?</section>', admin_html_section, index_html, flags=re.DOTALL)

# Ersätt funktionen i index.html
index_html = re.sub(r'async function loadHighscore\(\) \{.*?(?=async function loadHistory|\Z)', admin_js_function, index_html, flags=re.DOTALL)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

print("KLART! index.html har nu exakt samma Highscore som admin.html.")
