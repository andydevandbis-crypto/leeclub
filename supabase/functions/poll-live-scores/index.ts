import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const ODDS_API_KEY = Deno.env.get('ODDS_API_KEY')
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

// Här mappar vi Svenska Spels namn till Odds-API:ets namn (rensade från accenter)
const TEAM_ALIASES: Record<string, string> = {
  "bayernmunchen": "bayernmunich",
  "fckopenhamn": "fccopenhagen",
  "sportinglissabon": "sportingcp",
  "juventus": "juventusturin"
};

function cleanName(name: string) {
  if (!name) return "";
  let clean = name.toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/(fc|if|sk|bk|ff|aik|ac|as|ss|us|cf|cd|club|kf|fk|sc)/gi, "")
    .replace(/[^a-z0-9]/g, "");
  return TEAM_ALIASES[clean] || clean;
}

function teamsMatch(a: string, b: string) {
  const cA = cleanName(a), cB = cleanName(b);
  if (!cA || !cB) return false;
  return cA.includes(cB) || cB.includes(cA);
}

serve(async (req) => {
  try {
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    const headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json" }
    const spelRes = await fetch("https://api.spela.svenskaspel.se/draw/1/europatipset/draws", { headers })
    if (!spelRes.ok) throw new Error(`Svenska Spel status: ${spelRes.status}`)
    
    const rawData = JSON.parse(new TextDecoder("utf-8").decode(await spelRes.arrayBuffer()))
    const currentDraw = rawData.draws && rawData.draws.length > 0 ? rawData.draws[0] : null;
    if (!currentDraw) throw new Error("Hittade ingen draw i draws-listan.")
    
    const events = currentDraw.drawEvents || [];
    if (events.length === 0) throw new Error("Hittade inga drawEvents i dragningen.")

    const now = new Date().getTime();
    const isMatchTime = events.some((e: any) => {
        const startStr = e.match?.matchStart;
        if (!startStr) return false;
        const start = new Date(startStr).getTime();
        return (now > start - (2 * 60 * 60 * 1000)) && (now < start + (3 * 60 * 60 * 1000));
    });

    const spelMatches = events.map((e: any) => {
      const parts = e.match?.participants || [];
      return {
        match_order: e.eventNumber,
        home: parts.find((p: any) => p.type === "home")?.name || "",
        away: parts.find((p: any) => p.type === "away")?.name || "",
        datetime: e.match?.matchStart
      }
    })

    let oddsData: any[] = [];
    
    if (isMatchTime) {
        const today = new Date().toISOString().split('T')[0]
        const tomorrow = new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]
        const oddsRes = await fetch(`https://api.odds-api.io/v3/events?apiKey=${ODDS_API_KEY}&sport=football&status=pending,live,settled&from=${today}T00:00:00Z&to=${tomorrow}T23:59:59Z&limit=5000`)
        oddsData = await oddsRes.json()
        if (!Array.isArray(oddsData)) throw new Error("Ovantat svar fran Odds-API")
    }

    const updates = spelMatches.map((sp: any) => {
      let oe = null;
      if (isMatchTime) {
          oe = oddsData.find((o: any) => teamsMatch(sp.home, o.home?.name || o.home) && teamsMatch(sp.away, o.away?.name || o.away));
      }
      
      return {
        match_order: sp.match_order, home: sp.home, away: sp.away,
        status: oe ? oe.status : 'NS', minute: oe?.clock?.minute || 0,
        home_goals: oe?.scores?.home ?? null, away_goals: oe?.scores?.away ?? null,
        datetime: sp.datetime
      }
    })

    if (updates.length > 0) {
      const { error } = await supabase.from('live_scores').upsert(updates)
      if (error) throw new Error("Databasfel: " + error.message)
    }
    
    return new Response(JSON.stringify({ success: true, count: updates.length, matches: updates.map(u => `${u.home} - ${u.away}`), odds_called: isMatchTime }), { 
      headers: { "Content-Type": "application/json; charset=utf-8" } 
    })
  } catch (err: any) {
    return new Response(JSON.stringify({ success: false, error: err.message }), { 
      status: 200, 
      headers: { "Content-Type": "application/json; charset=utf-8" } 
    })
  }
})