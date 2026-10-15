# Lane F1: live web/API endpoints for historical NHL lines (INV-19)

Run 2026-10-15 16:47-16:55 EDT. Read-only, anonymous GETs, generic Chrome UA, 0.4-1.2 s spacing, probes only. Scripts: `docs/ops/probes/laneF1_probe1..10.py`. Samples: `data/samples_laneF/espn_core/`, `data/samples_laneF/sbr/`. Not redone: Lane B's site-API `summary.pickcenter`.

## Ranking

| Rank | Source | 2024-25 | Open + close | Books | Terms | Bulk effort |
|---|---|---|---|---|---|---|
| 1 | ESPN core API `/odds` | YES, 100% of 10 sampled dates (73 games) | YES (ESPN BET), ML + PL + total | 1 in 2024-25; 9-13 in 2022-24 | unofficial API, no terms file (core host robots = 403); Lane B already accepted ESPN | ~1 req/game |
| 2 | Sportsbook Review `__NEXT_DATA__` | YES, game counts match ESPN on every sampled date 2021-25 | YES, opening + "latest" (post-game page, effectively close; unverified as a true close) | 6-8 (BetMGM, bet365, DK, FanDuel, BetRivers, Caesars, Fanatics, Hard Rock) | robots OK for `/betting-odds/`; **ToS forbids "data mining, bots, or similar data gathering"** | ~3 req/date (ML, spread, totals) |
| 3 | Action Network scoreboard JSON | works (31 odds rows/game, 6+ books, ML/PL/total/team total/period, bet% splits) | latest only seen; `line_status`/`meta` fields | 6+ | **api.actionnetwork.com robots.txt: `Disallow: /`. DO NOT USE.** Sample deleted | n/a |

## 1. ESPN core API (best find)

- Endpoint: `https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/{eid}/competitions/{eid}/odds` (event id = competition id). Per-provider detail at `.../odds/{providerId}` (58 = ESPN BET, 40 = DraftKings).
- Id mapping: ESPN event ids from the cached `data/raw/espn_scoreboard/{YYYYMMDD}.json.gz` (date + teams).
- Proof 2024-25, 2025-01-15 CAR @ BUF (401688304): provider ESPN BET, items carry `open`, `close`, `current` objects (ML, spread/puck line with price, over/under with total). ML away open -170, close -185; PL -1.5 open +140, close +130; total open 6.5 (over +120), close 5.5 (over -130). Sample `data/samples_laneF/espn_core/odds_20250115_401688304.json`. A second item "ESPN Bet - Live Odds" is an in-play line; ignore it.
- Coverage probe (`laneF1_probe7.py`, games with a non-live provider, open/close present):
  - 2024-25: 10/10 dates incl. 2024-10-22, 11-15, 12-15, 2025-01-15, 02-15, 03-15, 04-15: every game, open AND close. Hole in the site-API pickcenter is NOT present here.
  - 2025-26 (2025-11-15): 13/13 with open and close.
  - 2023-24: 4/4 (2023-11-15) and 12/12 (2024-02-15), 9-12 books (Bet365, DK, MGM, Caesars, Unibet, PointsBet, ESPN BET, Betfair...) with open and close on ML.
  - 2022-23: 9/9 and 6/6, multi-book, `close` present on most, `open` absent.
  - 2021-22: multi-book (13 names) with `current` only, no open/close.
  - Caveat: 2022-24 "current" is a final snapshot per book; treat as close only where `close` exists.
- `.../odds/58/history/0/movement` returns 200 with zero items for the game tried: no timestamp history here.
- Full season: ~1,400 requests (one per game) plus the cached scoreboards. At 2 req/s, ~12 min per season.
- Terms: core-API host robots returns 403 and no terms file for the endpoint; www.espn.com robots blocks some AI crawlers but this is an API host. Verdict: use politely, cache, log risk for PM (same posture as Lane B).

## 2. Sportsbook Review (SBR)

- URL pattern: `https://www.sportsbookreview.com/betting-odds/nhl-hockey/?date=YYYY-MM-DD` (moneyline), `.../nhl-hockey/pointspread/?date=`, `.../nhl-hockey/totals/?date=`. Data in `<script id="__NEXT_DATA__">`: `props.pageProps.oddsTables[0].oddsTableModel.gameRows[]`, each with `gameView` (teams, start, score), `oddsViews[]` per book (`openingLine`, `currentLine`: home/away odds, spreads, total, over/under odds), `openingLineViews`.
- Proof 2025-01-15 CAR @ BUF, ML away/home open -> latest: BetMGM -185/+150 -> -190/+155; bet365 -180/+150 -> -190/+160; DraftKings -175/+145 -> -185/+154; FanDuel -188/+155 -> -184/+152; BetRivers -175/+140 -> -190/+155; Caesars -179/+150 -> -189/+158. Spread and totals pages returned (e.g. total open 6 -110/-110, latest 5.5 -130/+100). Samples in `data/samples_laneF/sbr/`.
- Seasons: dates tested 2021-01-20, 2021-11-15, 2022-01-15, 2022-02-15, 2023-01-15, 2023-11-15, 2024-10-22 to 2025-04-15 all return rows and game counts equal to ESPN's; 2019-01-15 returned rows but no odds views. Only ML open/latest verified for pre-2025 dates.
- No timestamped line history (`moneyLineHistory` null). Game id `gameId` is SBR-internal; map by date + team names.
- Full season: ~180 dates x 3 markets = ~540 requests.
- Terms: robots permits `/betting-odds/`, but ToS (sportsbookreview.com/terms-of-use/) says users must not "use any data mining, bots, or similar data gathering and extraction tools on the Site". Verdict: technically readable, contractually prohibited. PM decision needed; I did not bulk pull.

## 3. Action Network

- `https://api.actionnetwork.com/web/v1/scoreboard/nhl?date=YYYYMMDD` returns rich JSON (200 for 2023 and 2025 dates) but `api.actionnetwork.com/robots.txt` is `User-agent: *  Disallow: /`. Verdict: do not use. Sample removed.

## Dead ends / not useful

- NHL `api-web.nhle.com/v1/partner-game/US/now`: DraftKings current odds for today's slate only; `/partner-game/US/2025-01-15` is 404. No history.
- Covers.com, Scores And Odds, Yahoo Sports scoreboard (`?dateRange=`): date parameter ignored or odds client-rendered; no game data for 2025-01-15 in the server HTML. Covers team past-results pages not tested (time).
- OddsShark `/nhl/odds` and `/nhl/scores?date=`: no 2025-01-15 game content in server HTML.
- VegasInsider, CBS Sports odds, Rotowire, Oddstrader, Pickswise, theScore: 200 with current-slate odds only; no date param verified. Not pursued.
- Fox bifrost scoreboard: 200 but 4 KB with no odds for the date; not pursued (needs an embedded API key).
- Core API `/probabilities` 400; movement sub-resource empty.
- FanDuel/Caesars/BetMGM event APIs: not probed (live events only, and ToS risk).

## Recommendation

1. Bulk-pull the ESPN core `/odds` endpoint for 2023-24 to 2025-26: it fills the 2024-25 hole with ESPN BET open+close ML/PL/total, and gives multi-book opens/closes for 2023-24. Keep 2021-23 Unibet/multi-book current lines as low-grade closes.
2. Use SBR only as a cross-check sample on a few dates unless the PM accepts the ToS risk; it would add multi-book open/close for 2021-25.
3. Single-book caution for 2024-25: ESPN BET only. A multi-book close for that season still needs SBR or a paid source (The Odds API).
