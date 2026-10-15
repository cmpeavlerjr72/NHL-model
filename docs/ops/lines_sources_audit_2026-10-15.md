# Lines, props and goalie-confirmation source audit (Lane B, INV-3 / INV-8)

Run 2026-10-15 14:26-14:45 -04:00 (wall clock). Research and read-only probes only. No orders, no login, no credentials used or printed: every Kalshi call was an UNAUTHENTICATED public endpoint (the CFB client's signed key in `C:\Users\devuser\kalshi-rfq\.env` was not touched; the brief's `C:\Users\devuser\.kalshi` is not where the CFB code loads keys). Probe scripts: `docs/ops/probes/laneB_*.py`. Samples: `data/samples_laneB/`.

## Recommendation summary

| Need | Recommendation |
|---|---|
| (a) Historical closes 2021-26 | No single free source. ESPN `summary.pickcenter` (free): 2021-23 Unibet single line (no open/close, no timestamp); 2025-26 DraftKings with open+close ML/PL/total; 2024-25 EMPTY in the sampled week. Fill gaps and get timestamped closes via The Odds API historical (paid, ask user). Kalshi history covers 2025-26 only (incl. props). Prop history otherwise: The Odds API from 2023-05 (paid). |
| (b) Live markets | Kalshi: deep NHL catalog incl. player props, readable anonymously. DKeX: NHL listed, readable anonymously with the CFB header recipe (league 42133). No HAR needed for reads. |
| (c) Goalie confirmations | Live: Daily Faceoff starting-goalies page JSON (`__NEXT_DATA__`) has per-team status (Confirmed/Likely/Unconfirmed) and creation timestamps. No bulk historical timestamps; Wayback has ~125 snapshot days over 5 seasons. Start forward logging now; label any 2021-26 backtest "oracle goalie" per CLAUDE.md. |
| (d) Third-party sites | MoneyPuck: bulk CSV, non-commercial with credit, ask for anything else. Sports/Hockey-Reference: automation needs written permission and AI/ML use prohibited; do not use. NST: robots block Claude bots, crawl-delay 240, 403; do not use. Evolving-Hockey: terms not retrieved, subscriber-only; do not use. |

## 1. Reuse from sister projects (what transfers)

- `cfb-props-sim/scripts/kalshi_client.py`: signed RSA-PSS read-only client (key id + PEM path from `kalshi-rfq/.env`). Not needed here: market data, candlesticks and trades are public for NHL.
- `capture_kalshi_candles.py` and the INV-49 "purge race" lesson: settled-market data used to vanish. Kalshi now has a `/historical/*` tier (cutoff 2026-08-16), so partly obsolete, but still bank the live tier in-season.
- `pull_dk_predictions_cfb.py`, `pull_dk_predictions_book.py`, `docs/ops/dk_predictions_api.md` (CFB repo): headers `x-pe-cn/cv/ep/loc`, board endpoint, book resolver. Transfers directly; league id and subcategory ids change. Pitfall found today: the query MUST be percent-encoded via `urllib.parse.quote` as the CFB puller does; `requests` default encoding got Akamai 403 even for CFB. Also send `referer` and a current Chrome UA.
- `grade_kalshi_economics.py`: fee = 0.07*P*(1-P) per contract (standard sports taker); ROI is always fee-inclusive (CFB standing rule). `decision_policy.py` and `props_edge_dkex.py` are model-layer; not reviewed in depth.
- CBB: `pull_cbbd_lines_v1.py`, `probe_lines_sources_v1.py` (CBBD is college only, no NHL); CBB postmortem 06 notes The Odds API pricing ($30/mo 20K credits, $59/mo 100K credits) and Scottfree CSV ($119, CBB).
- CFB memory notes: DK trades are manual in a logged-in browser; Kalshi is cheaper than DK on nearly every matched line (DK 8-9c wide + ~2c fee vs Kalshi 1-3c + 1-2c).

## 2. Kalshi NHL (anonymous GET, `https://api.elections.kalshi.com/trade-api/v2`)

Open markets 2026-10-15 ~14:27 (`laneB_kalshi_nhl2.py`):

| Series | Contract | Open mkts / events | Notes |
|---|---|---|---|
| KXNHLGAME | team to win (2 binaries per game) | 92 / 46 (to 10-21) | 24h vol 305k, median spread 3c, `quadratic_with_maker_fees` |
| KXNHLSPREAD | "wins by over N.5 goals" | 108 / 27 | spread 4c |
| KXNHLTOTAL | "over N.5 goals" ladder | 243 / 27 | median spread 20c (thin rungs) |
| KXNHLTEAMTOTAL | team over N.5 | 130 / 13 | |
| KXNHL1P, KXNHL1PTOTAL, KXNHLOT, KXNHLF10G | period / OT / first-10 | 39, 39, 13, 13 | under 6k volume |
| KXNHLGOAL | player 1+ goal | 702 / 11 | vol 98k |
| KXNHLPTS | player 1+/2+ points | 478 / 11 | vol 29k |
| KXNHLAST | player 1+ assists | 348 / 11 | vol 34k |
| KXNHLSAVE | goalie N+ saves | 15 / 10 | vol 2.2k, thin |
| KXNHLFIRSTGOAL | first goalscorer | 404 / 11 | mostly one-sided books |

No SOG props on Kalshi today (DKeX lists them).

Structure: all `market_type=binary`, 1c price grid, YES/NO complementary, ladders via `floor_strike` (`strike_type=greater`), game winner `structured`. Props list on game day; game markets about a week ahead. Fees: series `fee_type` is `quadratic` (props, totals, spreads) or `quadratic_with_maker_fees` (KXNHLGAME); taker coefficient 0.07*P*(1-P) per contract is from the CFB repo. The Kalshi fee PDF returned HTTP 429, so the exact current coefficient and maker rate are UNVERIFIED.

History (no key needed):
- `/historical/cutoff` = 2026-08-16. `/historical/markets?series_ticker=`, `/historical/markets/{ticker}/candlesticks` (period_interval=60, yes_bid/yes_ask OHLC, `price` null in no-trade hours) and `/historical/trades?ticker=` return 200. Post-cutoff markets use `/series/{s}/markets/{t}/candlesticks` and `/markets/trades` (also anonymous); the live path 404s for pre-cutoff tickers.
- Coverage: KXNHLGAME 3,076 markets from 2025-04-20 (2025 playoffs, Sep 2025 preseason, Oct 2025 to Jun 2026, ~450/month); KXNHLSPREAD and KXNHLTOTAL from 2025-10-23; KXNHLGOAL from 2025-11-22 (37,973); KXNHLPTS and KXNHLAST from 2025-11-25 (41,919 / 29,869); KXNHLTEAMTOTAL, SAVE, 1PTOTAL, OT returned no historical markets. Post-cutoff settled: games from 2026-09-20, props from ~09-29.
- So Kalshi history is the 2025-26 season only; it cannot support 2021-25. It gives tradable bid/ask paths and trades, not a single "close"; define close as the last pre-puck-drop candle (`created_at < puck_drop`).
- Samples: `data/samples_laneB/kalshi_KXNHLGAME_historical_sample.json`, `kalshi_nhl_series.json`.

## 3. DraftKings Predictions (DKeX) NHL

- The owner's HAR nav lists `markets/hockey/nhl`; id `42133` beside "nhl" is the league id (same pattern as `87637` ncaaf). Anonymous read with the CFB header recipe returns 200 (no cookie, no login). `laneB_dk_nhl.py` reads boards only; the order-book POST was NOT called.
- Subcategories for league 42133 (11-13 events today): 4525 Moneyline / Puck Line / Total Goals; 13192 Alternate Total Goals; 16715 team goals by period; 16716 team total goals; 14495 Anytime + 1st Goalscorer; 16544 Shots on Goal (176 markets); 16545 Points; 16546 Assists; 16547 Goals; 16549 Goalie Saves; 16550 Goalie Saves O/U. The sweep covered ids 4510-4530, 4625-4650, 13190-13210, 16535-16580, 16715-16725 plus the CFB-HAR ids; other subcategories may exist.
- Board gives American odds (U+2212 minus) and `trueOdds`; no bid/ask/depth (needs the trade-panel POST, anonymous per CFB notes, not exercised).
- Historical DKeX: the CFB project pulls the DKeX daily report feed for settlements and trades; NHL availability not checked. No historical board.
- No fresh HAR needed to READ NHL. Only if the user wants the NHL trade-panel or combo flow: capture the NHL game page with the trade panel open on a moneyline and a SOG prop. Trading stays manual.
- Samples: `data/samples_laneB/dk_nhl_42133_*.json`.

## 4. Historical closes (candidates)

| Source | Coverage | Books / timestamps | Terms | Verdict |
|---|---|---|---|---|
| ESPN `site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event=` `pickcenter` (ids from `scoreboard?dates=`) | Dec 8-14 sample per season (season-start year): 2021 53 games, 51 with line; 2022 50/49; 2023 50/50; 2024 53/0; 2025 53/53 | 2021-23 Unibet single line (ML, PL, total), no open/close or timestamp; 2025 DraftKings with open and close ML/PL/total | unofficial API, no licence found | Best free. Recheck the 2024-25 hole on other weeks. 1 req/s, cache. |
| Kalshi `/historical` | 2025-04 to 2026-06 | bid/ask candles, trades with timestamps | public API | Best for 2025-26 incl. props |
| The Odds API historical | ML/PL/total from 2020-06-29 (10 min, 5 min from 2022-09); props from 2023-05-03 | multi-book timestamped snapshots | paid plan only; 10 credits per market per region (event-odds 10 per event) | Best for real closes; ask the user |
| Princeton DSS Historical Sports Odds | NHL 2008-2023 open+close ML and O/U (search snippet) | no timestamps | page blocked by bot check; access/licence unverified | lead only |
| FantasyData CSV | historical odds | | paid All-Access | skip |
| sportsbookreviewsonline archive | URL 404 | | | dead lead |
| OddsPortal | wide | | forbids automated access, aggregation, commercial use | do not use |

Samples: `data/samples_laneB/espn_nhl_oneweek_per_season_dec8-14.json` (per game per provider), `espn_nhl_pickcenter_2025-12-15.json`.

## 5. Goalie confirmations

- NHL API `gamecenter/{id}/landing` matchup block lists season goalie leaders, not a confirmed starter. The starter is known from boxscore only after the fact (oracle).
- Daily Faceoff `dailyfaceoff.com/starting-goalies`: robots allow `/` (disallow `/api/`, `/cms/`). The page embeds `__NEXT_DATA__` with per-game home/away goalie id/name, `homeNewsStrengthName` / `awayNewsStrengthName`, `homeNewsCreatedAt` / `awayNewsCreatedAt` (e.g. 2026-10-15T14:50:33Z), and moneyline/point spread. Best live source. Its ToS page was not found (guessed URL 404), so the verdict is robots-permits-only; poll a few times per game day and store `fetched_at`.
- RotoWire starting-goalies page returns 200; not parsed, terms not checked.
- Historical timestamps: none in bulk. Wayback CDX (status 200) Daily Faceoff 142 snapshots / 125 distinct days 2021-2026 (by year 20, 51, 16, 25, 22, 8); RotoWire 117 / 106 days. A 2023-11-22 snapshot parses (JSON present). About 8% of game days: not enough to backtest. Action: log forward from now (honest ledger for 2026-27); label 2021-26 backtests "oracle goalie".

## 6. Third-party terms (page text read 2026-10-15; not legal advice)

- MoneyPuck `moneypuck.com/data.htm`: "free to use for non-commercial purposes and by journalists"; credit MoneyPuck.com; other uses ask first; "Non-approved scraping ... will be blocked"; ask before scraping anything not on the data page. robots.txt has only content-signal comments. Bulk: season and game-by-game skaters/goalies/lines/teams 2008-09 to 2026-27, shot-level 2007-08 to 2025-26 (2.08M shots), 2026-27 shots nightly. No odds. Verdict: usable via listed downloads for research with credit; ask for commercial use; any xG feed still needs the leak test.
- Hockey-Reference / Sports-Reference: automated access prohibited without written permission (sec 5.9); AI/ML training or prompting prohibited (5.11); no competing database. robots: Crawl-delay 3. Verdict: DO NOT USE.
- Natural Stat Trick: robots crawl-delay 240, many disallows, ClaudeBot/Claude-User and most AI bots fully blocked; homepage 403. Verdict: DO NOT USE.
- Evolving-Hockey: terms not retrieved; subscriber-only data. Verdict: DO NOT USE without reading terms and asking the user.
- NHL.com Hockeyverse ToS: prohibits "unauthorized spidering, scraping, or harvesting"; non-commercial personal use. That governs the NHL.com service; no published terms found for `api-web.nhle.com`, which CLAUDE.md names primary. FLAG for PM: keep polite rates and record the risk.
- DK Predictions: the board JSON is the site's own anonymous API; DK ToS not read; the CFB project accepted this for reads.

## Not done / partial

- ESPN 2024-25 gap measured on one week only (Dec 8-14, 2024).
- Kalshi fee coefficient and maker rate unverified (PDF 429).
- DKeX depth POST not exercised; DK ToS, RotoWire terms, Daily Faceoff ToS, Evolving-Hockey terms not read; Polymarket and FanDuel NHL not probed.
- System `py -3.12` with `requests` used; `.venv` untouched.
