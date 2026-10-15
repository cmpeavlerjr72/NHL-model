# Data sources register

One row per source. Verdicts from Lane B audit 2026-10-15 (details: `lines_sources_audit_2026-10-15.md`). Not legal advice. Other lanes append rows for their sources (NHL API, etc.).

| Source | What | Coverage | Terms verdict | Access method |
|---|---|---|---|---|
| Kalshi public API (`api.elections.kalshi.com/trade-api/v2`) | NHL game, spread, total, team total, period, OT, player goal/points/assists/saves markets; prices, candles, trades | live now; `/historical/*` 2025-04 to 2026-06 (games, spreads, totals, goal/points/assist props from Oct-Nov 2025); cutoff 2026-08-16 | OK for read-only market data (anonymous GET; no key). Trading by agents banned. Fee coefficient unverified | GET, 0.3 s spacing, cache raw JSON |
| DraftKings Predictions board (`sportsbook-nash.draftkings.com/sites/PREDICT/...`, NHL league 42133) | ML/puck line/total, alt totals, period/team goals, goalscorer, SOG, points, assists, goals, goalie saves | live only (no history) | Site's own anonymous JSON; DK ToS not read; reads only, no login, trading manual | GET with `x-pe-*` headers, percent-encoded query, referer, Chrome UA (see CFB `dk_predictions_api.md`) |
| ESPN site API (`site.api.espn.com/apis/site/v2/sports/hockey/nhl`) | scoreboard ids, summary `pickcenter` lines | 2021-23 Unibet single line; 2024 empty in sample; 2025-26 DraftKings open+close Full-population check 2026-10-15: 2023-24 Unibet single line 100% (no open/close); 2024-25 EMPTY (0 of 1312); 2025-26 DraftKings open+close from 2025-11-25 (936 of 1312). | Unofficial; no licence found; research use at low rate | GET 1 req/s, cache |
| The Odds API (historical) | multi-book timestamped ML/PL/total, props from 2023-05 | 2020-06-29 onward | Paid plan, 10 credits per market per region; needs USER APPROVAL to buy | REST with key |
| Daily Faceoff starting goalies | projected/confirmed goalie, status, news timestamp | live; Wayback ~125 days 2021-26 | robots allow `/`; ToS not read | GET page, parse `__NEXT_DATA__`; poll sparsely; log `fetched_at` |
| RotoWire starting goalies | projected goalies | live; Wayback ~106 days | terms not checked | not used yet |
| Internet Archive Wayback CDX | snapshots of goalie pages | sparse | public service | CDX query, politely |
| MoneyPuck (`moneypuck.com/data.htm`) | season and game-level skater/goalie/line/team CSV, shot-level xG | 2008-09 to 2026-27; shots to 2025-26 plus nightly | Free for non-commercial use with credit to MoneyPuck.com; ask for other uses; unapproved scraping blocked | download listed CSVs only; leak-test xG |
| Hockey-Reference / Sports-Reference | stats | | Automated access needs written permission; AI/ML use prohibited. DO NOT USE | none |
| Natural Stat Trick | stats | | robots crawl-delay 240, AI bots blocked, 403. DO NOT USE | none |
| Evolving-Hockey | models/stats | subscriber | Terms not retrieved. DO NOT USE without asking user | none |
| NHL.com / `api-web.nhle.com` | schedule, pbp, shifts, boxscores (project primary) | all | NHL.com Hockeyverse ToS bars scraping and non-personal use; no published terms found for the stats API: RISK FLAGGED for PM | polite GET, cache |
| OddsPortal | odds | | forbids automated access and commercial use. DO NOT USE | none |
| Princeton DSS Historical Sports Odds | NHL 2008-2023 open/close ML, O/U | | access/licence unverified (bot-check page) | lead only |
