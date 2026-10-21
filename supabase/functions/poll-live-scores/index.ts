import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const ODDS_API_KEY = Deno.env.get('ODDS_API_KEY')
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

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

async function fetchWithTimeout(resource: string, options: any = {}, timeout = 8000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  const response = await fetch(resource, { ...options, signal: controller.signal });
  clearTimeout(id);
  return response;
}

serve(async (req) => {
  try {
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    const headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json" }
    
    const games = ['europatipset', 'stryktipset', 'topptipset'];
    let totalMatches = 0;
    const summary: any[] = [];

    for (const game of games) {
        const apiPaths: Record<string, string> = {
            europatipset: 'europatipset',
            stryktipset: 'stryktipset',
            topptipset: 'topptipsetfamily'
        };
        const apiPath = apiPaths[game] || game;

        // 1. Försök hämta öppna omgångar
        let spelRes = await fetchWithTimeout(`https://api.spela.svenskaspel.se/draw/1/${apiPath}/draws`, { headers })
        let rawData: any = { draws: [] };
        
        if (spelRes.ok) {
            rawData = JSON.parse(new TextDecoder("utf-8").decode(await spelRes.arrayBuffer()));
        }
        
        // 2. Hitta rätt omgång (den som stänger tidigast bland de öppna)
        let currentDraw = null;
        if (rawData.draws && rawData.draws.length > 0) {
            const openDraws = rawData.draws.filter((d: any) => d.drawState === 'Open');
            if (openDraws.length > 0) {
                openDraws.sort((a: any, b: any) => {
                    const dateA = new Date(a.regCloseTime || a.closeTime).getTime();
                    const dateB = new Date(b.regCloseTime || b.closeTime).getTime();
                    return dateA - dateB;
                });
                currentDraw = openDraws[0];
            } else {
                currentDraw = rawData.draws[0];
            }
        }

        // 3. Om ingen öppen omgång, hämta senaste resultat
        if (!currentDraw) {
            const resultRes = await fetchWithTimeout(`https://api.spela.svenskaspel.se/draw/1/${apiPath}/draws/result`, { headers })
            if (resultRes.ok) {
                const resultData = JSON.parse(new TextDecoder("utf-8").decode(await resultRes.arrayBuffer()));
                if (Array.isArray(resultData) && resultData.length > 0) {
                    currentDraw = resultData[0]; 
                } else if (resultData.draws && resultData.draws.length > 0) {
                    currentDraw = resultData.draws[0];
                } else if (resultData.draw) {
                    currentDraw = resultData.draw;
                }
            }
        }

        if (!currentDraw) { summary.push({ game, error: 'no draw and no result' }); continue; }
        
        const events = currentDraw.drawEvents || [];
        if (events.length === 0) { summary.push({ game, error: 'no events' }); continue; }

        // 4. Skapa eller uppdatera rundan
        const deadline = currentDraw.closeTime || currentDraw.regCloseTime || currentDraw.drawTime;
        let roundId;
        
        const { data: existingRound } = await supabase
            .from('rounds')
            .select('id')
            .eq('game_type', game)
            .order('created_at', { ascending: false })
            .limit(1)
            .maybeSingle();
        
        if (existingRound) {
            roundId = existingRound.id;
            await supabase.from('rounds').update({ deadline: deadline }).eq('id', roundId);
        } else {
            const { data: newRound, error: insertErr } = await supabase
                .from('rounds')
                .insert({ game_type: game, deadline: deadline })
                .select('id')
                .single();
            if (insertErr || !newRound) { summary.push({ game, error: insertErr?.message || 'round insert failed' }); continue; }
            roundId = newRound.id;
        }

        // 5. Spara alla matcher
        const matchesPayload = events.map((e: any) => {
            const parts = e.match?.participants || [];
            return {
                round_id: roundId,
                match_order: e.eventNumber,
                home: parts.find((p: any) => p.type === "home")?.name || "",
                away: parts.find((p: any) => p.type === "away")?.name || "",
                game_type: game
            }
        });

        await supabase.from('matches').delete().eq('round_id', roundId);
        await supabase.from('matches').insert(matchesPayload);

        // 6. Kolla matchtid
        const now = new Date().getTime();
        const isMatchTime = events.some((e: any) => {
            const startStr = e.match?.matchStart;
            if (!startStr) return false;
            const start = new Date(startStr).getTime();
            return (now > start - (2 * 60 * 60 * 1000)) && (now < start + (3 * 60 * 60 * 1000));
        });

        // 7. Hämta odds
        let oddsData: any[] = [];
        if (isMatchTime) {
            const today = new Date().toISOString().split('T')[0]
            const tomorrow = new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]
            const oddsRes = await fetchWithTimeout(`https://api.odds-api.io/v3/events?apiKey=${ODDS_API_KEY}&sport=football&status=pending,live,settled&from=${today}T00:00:00Z&to=${tomorrow}T23:59:59Z&limit=5000`, { headers })
            oddsData = await oddsRes.json()
            if (!Array.isArray(oddsData)) oddsData = [];
        }

        // 8. Bygg livePayload
        const livePayload = matchesPayload.map((sp: any, index: number) => {
            const originalEvent = events[index];
            let oe = null;
            if (isMatchTime && oddsData.length > 0) {
                oe = oddsData.find((o: any) => teamsMatch(sp.home, o.home?.name || o.home) && teamsMatch(sp.away, o.away?.name || o.away));
            }
            return {
                match_order: sp.match_order,
                game_type: game,
                home: sp.home,
                away: sp.away,
                status: oe ? oe.status : 'NS',
                minute: oe?.clock?.minute || 0,
                home_goals: oe?.scores?.home ?? null,
                away_goals: oe?.scores?.away ?? null,
                datetime: originalEvent.match?.matchStart || deadline
            }
        });

        // 9. Spara resultaten — uppdaterar alltid datum, men resultat bara under matchtid
        if (livePayload.length > 0) {
            if (isMatchTime) {
                await supabase.from('live_scores').upsert(livePayload, { onConflict: 'game_type, match_order' });
            } else {
                const { data: existingScores } = await supabase
                    .from('live_scores')
                    .select('match_order')
                    .eq('game_type', game);
                const existingOrders = new Set((existingScores || []).map((e: any) => e.match_order));
                
                const updates = livePayload.filter((p: any) => existingOrders.has(p.match_order));
                if (updates.length > 0) {
                    for (const u of updates) {
                        await supabase.from('live_scores')
                            .update({ home: u.home, away: u.away, datetime: u.datetime })
                            .eq('game_type', game)
                            .eq('match_order', u.match_order);
                    }
                }
                
                const newOnly = livePayload.filter((p: any) => !existingOrders.has(p.match_order));
                if (newOnly.length > 0) {
                    await supabase.from('live_scores').upsert(newOnly, { onConflict: 'game_type, match_order' });
                }
            }
        }

        totalMatches += matchesPayload.length;
        summary.push({ game, roundId, deadline, matches: matchesPayload.length, isMatchTime });
    }
    
    return new Response(JSON.stringify({ success: true, total_processed: totalMatches, summary }), { 
      headers: { "Content-Type": "application/json; charset=utf-8" } 
    })
  } catch (err: any) {
    console.error("Edge Function Error:", err.message);
    return new Response(JSON.stringify({ success: false, error: err.message }), { 
      status: 200, 
      headers: { "Content-Type": "application/json; charset=utf-8" } 
    })
  }
})