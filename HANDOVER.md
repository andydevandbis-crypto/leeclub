# Lee Betting – Teknisk Handover (Live-integration)
**Datum:** 19 oktober 2026  
**Status:** Driftsatt på Cloudflare Pages & Supabase  
**Språk i gränssnittet:** Svenska

## 1. Sammanfattning
Lee Betting är en webbapplikation för att tippa en Stryktips-liknande kupong med 13 matcher. Applikationen har tidigare varit helt statisk, men är nu uppgraderad med **automatisk live-uppdatering**.
*   **Frontend:** Hostas på Cloudflare Pages (`LEEBET`). Består av `index.html` (spelare) och `admin.html` (admin).
*   **Backend:** Supabase (Auth, Postgres, Edge Functions).
*   **Integration:** En Supabase Edge Function hämtar matchlistan från Svenska Spel och live-resultat från Odds-API.io, utan att API-nycklar exponeras i webbläsaren.

## 2. Arkitektur & Dataflöde
All logik för live-uppdateringar sker i bakgrunden:
1.  **Schema (pg_cron):** En cron-jobb i Supabase körs varje timme dygnet runt.
2.  **Hämtning (Edge Function):** Funktionen `poll-live-scores` anropas.
    *   Den hämtar den senaste Europatipset-kupongen (13 matcher) från Svenska Spels interna API.
    *   Den hämtar matchresultat från Odds-API.io.
    *   Den matchar lagnamnen genom att normalisera texten och ta bort accenter/klubbsuffix.
3.  **Lagring:** Resultaten sparas i Supabase-tabellen `live_scores`.
4.  **Presentation (Frontend):** `index.html` läser av `live_scores` och ritar ut resultat, tid (LIVE/SLUT) och färger.

## 3. Filstruktur & Drift
**Frontend (Cloudflare):** `C:\Users\C_Kos\Desktop\APP\LEEBET`
*   `index.html` – Spelarvyn (uppdaterad med ny layout och färger).
*   `admin.html` – Adminvyn.
*   `js/config.js` – Supabase-uppkoppling.

**Backend (Supabase):** `C:\Users\C_Kos\Desktop\APP\LEEBET_BACKEND`
*   `supabase/functions/poll-live-scores/index.ts` – Koden för API-hämtning och matchning.

**Backuper:** `C:\Users\C_Kos\Desktop\APP\LEEBET_backup_[DATUM]` (Innehåller de gamla, statiska originalfilerna).

## 4. Databas & Konfiguration (Supabase)
*   **Projekt-ID:** `yjkyikxtklaokscnpxdj`
*   **Ny tabell:** `live_scores` (lagrar match_order, home, away, status, minute, home_goals, away_goals, datetime). RLS är aktiverat så att alla inloggade spelare kan läsa.
*   **Hemligheter:** Odds-API-nyckeln ligger säkert i Supabase (som `ODDS_API_KEY`).
*   **Cron-schema:** `poll-live-scores-hourly` (körs `0 * * * *`).

## 5. Frontend (index.html) – Ny layout
Spelarvyn har uppdaterats för att visa live-data:
*   **Resultat:** Ställningen (t.ex. 2-2) är staplad till höger om lagen.
*   **Status-badge:** Uppe till höger visas `00:00` (innan match), `LIVE` (pågående) eller `SLUT` (färdigspelad).
*   **Färger:**
    *   Rätt tips lyser **grönt** (transparent bakgrund på hela rutan).
    *   Fel tips lyser **orange** (transparent bakgrund).
    *   Korten är automatiskt låsta (ej klickbara) när de är live eller inlämnade, men chatten och "Logga ut" fungerar.

## 6. Framtida arbete & Underhåll
*   **Nya omgångar:** Systemet hittar automatiskt nya kuponger från Svenska Spel. Inget manuellt ingripande krävs.
*   **API-kvoter:** Odds-API:et anropas 24 gånger per dygn (en gång i timmen). Detta ligger långt under gratisgränsen på 500 anrop/dygn.
*   **Felsökning:** Om matcher inte dyker upp, kontrollera Edge Function-loggen i Supabase eller kör ett manuellt testanrop för att se vad Svenska Spel svarar.