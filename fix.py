import re

file_path = "admin.html"

with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Byt ut CSS
old_css = """  .live-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(115px, 1fr)); gap:8px; overflow-y: auto; padding-right: 4px; }
  .live-card { background:var(--panel2); border:1px solid var(--border); border-radius:6px; padding:8px; }
  .live-card-no { font-size:10px; color:var(--gold); font-weight:800; margin-bottom:4px;}
  .live-card-teams { font-size:11px; font-weight:600; line-height:1.3; margin-bottom:6px;}
  .live-card-pick { font-size:14px; font-weight:800; color:var(--gold); text-align:center; background:rgba(232,193,90,0.1); padding:6px; border-radius:4px; border:1px solid rgba(232,193,90,0.3); }"""

new_css = """  .live-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); grid-auto-rows: 1fr; gap: 8px; padding: 10px; overflow-y: auto; flex: 1; align-content: stretch; }
  .live-card { display: flex; flex-direction: column; justify-content: space-between; padding: 10px; background: var(--panel2); border: 1px solid var(--border); border-radius: 6px; gap: 6px; transition: 0.2s; }
  .live-card-header { display: flex; justify-content: space-between; align-items: center; }
  .live-card-no { font-size: 10px; font-weight: 800; color: var(--gold); }
  .live-card-teams { font-size: 12px; font-weight: 600; line-height: 1.3; display: block; }
  .live-card-teams span { display: block; }
  .live-card-signs { display: flex; gap: 4px; margin-top: auto; }
  .live-card-sign { flex: 1; text-align: center; font-size: 12px; font-weight: 700; padding: 6px 0; border-radius: 4px; color: var(--muted); background: rgba(255,255,255,0.02); border: 1px solid var(--border-soft); }
  .live-card-sign.on { color: var(--gold); background: rgba(232,193,90,0.15); border-color: rgba(232,193,90,0.4); }
  .live-card-content { display: flex; justify-content: space-between; align-items: flex-start; flex-grow: 1; margin: 4px 0; }
  .live-card-score { display: flex; flex-direction: column; align-items: flex-end; font-size: 18px; font-weight: 800; line-height: 1.1; }
  .live-card-score span { display: block; }
  .live-card-score.red { color: var(--red); }
  .live-card-score.green { color: var(--green); }
  .live-badge { font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }
  .live-badge.tid { background: #fff; color: var(--red); }
  .live-badge.score { background: transparent; color: var(--text); border: 1px solid var(--border); }
  .live-card-sign.win { background: var(--green) !important; color: #000 !important; border-color: var(--green) !important; }
  .live-card-sign.lose { background: #f08a3c !important; color: #000 !important; border-color: #f08a3c !important; }
  .live-card.ft-win { background: rgba(51,224,138,0.15) !important; border-color: var(--green) !important; box-shadow: 0 0 0 1px var(--green) inset !important; }
  .live-card.ft-loss { background: rgba(224,90,90,0.15) !important; border-color: var(--red) !important; box-shadow: 0 0 0 1px var(--red) inset !important; }
  .live-card-note { background: var(--panel2); border: 1px dashed var(--border); border-radius: 10px; padding: 10px; display: flex; flex-direction: column; }"""

if old_css in html:
    html = html.replace(old_css, new_css)
else:
    html = re.sub(r"\.live-grid \{.*?\.live-card-pick \{[^\}]*\}", new_css, html, flags=re.DOTALL)

# 2. Se till att liveScores finns
if "let liveScores = {};" not in html:
    html = html.replace("function renderAdminLiveView() {", "let liveScores = {};\n  function renderAdminLiveView() {")

# 3. Byt ut JS
old_js = """  function renderAdminLiveView() {
    const grid = document.getElementById('adminLiveGrid'); if(!grid) return; grid.innerHTML = '';
    state.matches.forEach((m, i) => {
      const leePick = m.signs.length > 0 ? m.signs.join(' ') : 'Väntar...';
      const el = document.createElement('div'); el.className = 'live-card';
      el.innerHTML = `<div class="live-card-no">M${i+1}</div><div class="live-card-teams">${esc(m.home)}<br>${esc(m.away)}</div><div class="live-card-pick">${leePick}</div>`;
      grid.appendChild(el);
    });
  }"""

new_js = """  function renderAdminLiveView() {
    const grid = document.getElementById('adminLiveGrid'); if(!grid) return; grid.innerHTML = '';
    for (let i = 0; i < 13; i++) {
      const m = state.matches[i] || { home: '', away: '', signs: ['1'] };
      const live = liveScores[i];
      const p = m.signs || [];
      let currentWin = null;
      let isFinished = false;

      if (live && live.home_goals != null && live.away_goals != null) {
          if (live.home_goals > live.away_goals) currentWin = '1';
          else if (live.home_goals < live.away_goals) currentWin = '2';
          else currentWin = 'X';
          const st = (live.status || '').toLowerCase();
          isFinished = (st === 'ft' || st === 'settled' || st === 'ended');
      }

      let badgeHtml = '';
      if (live) {
          const st = (live.status || '').toLowerCase();
          if (isFinished) badgeHtml = `<div class="live-badge score" style="color:var(--muted);">SLUT</div>`;
          else if (st === 'pending' || st === 'ns' || !st) {
              let timeStr = '00:00';
              if (live.datetime) timeStr = new Date(live.datetime).toLocaleTimeString('sv-SE', {hour: '2-digit', minute:'2-digit'});
              badgeHtml = `<div class="live-badge score">${timeStr}</div>`;
          } else badgeHtml = `<div class="live-badge tid">LIVE</div>`;
      }

      let scoreHtml = '';
      if (live) {
          let hg = live.home_goals, ag = live.away_goals;
          const st = (live.status || '').toLowerCase();
          if ((st === 'ns' || st === 'pending') && (hg === null || hg === undefined)) { hg = 0; ag = 0; }
          scoreHtml = `<div class="live-card-score ${isFinished ? 'green' : 'red'}"><span>${hg ?? '-'}</span><span>${ag ?? '-'}</span></div>`;
      }

      let c1 = 'live-card-sign' + (p.includes('1') ? ' on' : '');
      let cx = 'live-card-sign' + (p.includes('X') ? ' on' : '');
      let c2 = 'live-card-sign' + (p.includes('2') ? ' on' : '');

      if (live && currentWin) {
          if (currentWin === '1') c1 += ' win'; if (currentWin === 'X') cx += ' win'; if (currentWin === '2') c2 += ' win';
          if (currentWin !== '1' && p.includes('1')) c1 += ' lose'; if (currentWin !== 'X' && p.includes('X')) cx += ' lose'; if (currentWin !== '2' && p.includes('2')) c2 += ' lose';
          if (!p.includes('1') && currentWin !== '1') c1 += ' dim'; if (!p.includes('X') && currentWin !== 'X') cx += ' dim'; if (!p.includes('2') && currentWin !== '2') c2 += ' dim';
      }

      const el = document.createElement('div'); 
      let cardClass = 'live-card';
      if (isFinished && currentWin && p.length > 0) cardClass += p.includes(currentWin) ? ' ft-win' : ' ft-loss';
      el.className = cardClass;

      el.innerHTML = `
        <div class="live-card-header"><span class="live-card-no">M${i+1}</span>${badgeHtml}</div>
        <div class="live-card-teams"><span>${esc(m.home)}</span><span>${esc(m.away)}</span></div>
        <div class="live-card-content">${scoreHtml}</div>
        <div class="live-card-signs"><div class="${c1}">1</div><div class="${cx}">X</div><div class="${c2}">2</div></div>`;
      grid.appendChild(el);
    }

    const noteCard = document.createElement('div');
    noteCard.className = 'live-card-note';
    noteCard.innerHTML = `
      <div class="data-label" style="margin-bottom: 6px;">Egna noteringar</div>
      <textarea placeholder="Skriv dina egna noteringar här..." readonly style="flex:1;background:var(--panel);border:1px solid var(--border);border-radius:6px;color:var(--text);padding:8px;resize:none;outline:none;font-family:inherit;font-size:12px;">${esc(localStorage.getItem('lee_admin_notes') || '')}</textarea>
    `;
    grid.appendChild(noteCard);

    setTimeout(() => {
        const tpl = getComputedStyle(grid).gridTemplateColumns;
        if (tpl && tpl !== 'none') {
            const cols = tpl.split(' ').filter(Boolean).length || 1;
            const rem = 13 % cols;
            noteCard.style.gridColumn = 'span ' + (rem === 0 ? cols : cols - rem);
        }
    }, 10);
  }"""

if old_js in html:
    html = html.replace(old_js, new_js)
else:
    html = re.sub(r"function renderAdminLiveView\(\) \{.*?\n  \}", new_js, html, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(html)
print("KLART! admin.html har uppdaterats exakt.")
