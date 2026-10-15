# Lane F3: long-tail hunt for free historical NHL lines (INV-19)

Run 2026-10-15, 16:48-17:00 EDT. Read-only probes only: generic browser User-Agent, no keys, no logins, no signups, and 2 s or more between requests to the same host (about 45 requests in total). Probe scripts are `docs/ops/probes/laneF3_*.py` and samples are in `data/samples_laneF/F3_*/`. I did not touch anything on F1's or F2's lists.

## Headline

**DRatings (dratings.com) is a free, robots-permitted source of per-book OPEN and CLOSE NHL lines for moneyline, puck line and total, covering 2019-20 to today, including 2024-25.** Each completed-game page has a table for each market. Each table shows an "Open Line" column and closing prices from 5 offshore books (Heritage, Bovada, BetOnline, YouWager, SportsBetting) and 5 Las Vegas books (South Point, Circa, Wynn, Stations, Westgate). It also shows the best line and DRatings' no-vig price. The set of books is smaller in older seasons; 2021-22 has Bovada, BetOnline, SportsBetting, South Point, Circa, Stations and Westgate.

## Ranking

| # | Source | 2024-25 | Open/close | Books | Terms/robots | Bulk effort |
|---|---|---|---|---|---|---|
| 1 | **DRatings completed games** | YES (proved on 2025-03-11 and 2025-04-08) | Open plus per-book close for ML, PL and total | Up to 10 books plus no-vig | robots `Disallow:` is empty (allows all). No ToS page was found (`/terms/` and `/terms-of-use/` return 404); there is only `/about/predictions-disclaimer/`. Verdict: permitted by robots. Crawl slowly and keep it for personal research. | About 95 index pages plus about 1,400 game pages per season. At 3 s/request that is roughly 75 min per season, and roughly 6 h for 2020-21 to 2025-26. |
| 2 | OddsPapi API (`api.oddspapi.io/v4/historical-odds`). **The user must sign up.** | Unverified. The vendor blog shows NHL 2026 snapshots; archive start date is not stated. | Full timestamped price history per book, so open is the first tick and close is the last tick before puck drop. | Vendor claims 112 books on one NHL game, including Pinnacle, DK, FD, MGM, Bovada and Betfair; at most 3 books per call. | Site robots `Allow: /`. Without a key the endpoint returns 401 `MISSING_API_KEY` (endpoint is live). The API terms were not read. | 1 call per fixture per 3 books. Free tier has a per-minute limit (about 0.9 s/call) and "no hard row cap" according to the vendor. |
| 3 | Daily Faceoff `starting-goalies/YYYY-MM-DD` | Pages exist for 2025-01-15/16 and 2022-01-15 | One unnamed puck-line price pair only. No ML, no total, no open/close. | 1 (unnamed, from FantasyData) | robots disallows only `/api/` and `/cms/` | 1 request per date. **But there is a data-integrity problem; see below.** |

### 1. DRatings details (proof)
- Index URL: `https://www.dratings.com/predictor/nhl-hockey-predictions/completed/{page}`. Newest games come first, about 14-16 per page. Page 105 covers 2025-04-06..08, page 118 is 2025-03-11, page 400 is 2022-02-02..09, page 512 is 2020-03/08, and page 518 is 2020-02-26. Pages from about 525 on are empty. The `?date=` parameter is echoed back but ignored, so walk the pages to navigate.
- Each index row has the game UUID link, the UTC start time, away team (listed first) and home team (listed second, which I confirmed against the venue on the FLA@BOS page), the best offshore and best Vegas ML and puck line, and the final score.
- Game URL: `https://www.dratings.com/predictor/nhl-hockey-predictions/{uuid}`. It has the sections "Money Line Analysis", "Spread" and "Over/Under Analysis". Each is laid out as `Open Line | book1..book5 | Best Line | No-Vig`, with a row for each side, once for offshore and once for Vegas. It also shows implied margin at close and goalie names (season stats, which may be the starters; unverified).
- Sample, 2025-04-08 CAR@BUF. ML: Open CAR -170/BUF +151, closes at Heritage -226, Bovada -245, BetOnline -232, YouWager -240 and SportsBetting -232, no-vig -213.1. Vegas: open -180, close -240 at all five books. The total is o6.5 at about +104 with an open of o6. Files: `data/samples_laneF/F3_dratings/game_68117af4-*.json`, `index_page105.json`, `game_c4e8a1aa-*.json` (2021-22 NJ@MTL), `index_page400.json`, and the raw HTML `game_2025-03-11_FLA_BOS.html` (saved before the encoding fix, so "½" shows as mojibake).
- Caveats:
  - Page numbers shift as new games are added, so walk the pages within one session.
  - It is not clear whether "Open" is one consensus open or a market-maker open (it is shown once per book group).
  - "Close" means the last value DRatings recorded, with no timestamp.
  - Sometimes the book group quotes a different total (o6 vs o6.5).
  - Parse by `½`, and set `resp.encoding='utf-8'`.
- Mapping: date plus team names, then join to NHL game ids.
- Script: `docs/ops/probes/laneF3_dratings.py [page] [n_games]`. It currently saves the section text; it needs a cell parser before bulk use.

### 3. Daily Faceoff caveat (important for goalie work, INV-8)
The historical date pages have per-game goalie, Confirmed/Likely status and `NewsCreatedAt` timestamps, which looked like a bulk goalie-confirmation history that Lane B said did not exist. **But the goalie names do not match the teams.** On 2022-01-15 the page lists Logan Thompson for WSH, Kochetkov for CAR (before his NHL debut) and Talbot for CBJ. On 2025-01-16 it lists Woll for PHI, Bobrovsky for TOR and Shesterkin for UTA. Team names are also current ones (it says "Utah Mammoth" in Jan 2025). The pages appear to be rebuilt from today's data. **Do not use them for goalie or line history.** At most, the news text and timestamps might be salvageable; that is unverified. Files: `F3_dailyfaceoff/games_*.json`, script `laneF3_dailyfaceoff.py`.

## Signup-required options (for the user to decide; I signed up for nothing)

| API | Free quota | History reaches 2024-25? | Open/close | NHL | Source of claim |
|---|---|---|---|---|---|
| OddsPapi | Per-minute limit, "no row cap" | Unverified (archive start not published) | Timestamped ticks, so both can be derived | Yes (vendor blog) | vendor blog `oddspapi.io/blog/?p=2824`, `?p=2892`; 401 probe |
| TheRundown | 20k data points/day, 3 books (DK/FD/MGM), 5-min delay | **No.** Free tier has no history; Starter gives 7 days, Mega 1 year, Max unlimited | Open/close only from Pro ($149/mo) | Yes | therundown.io/api pricing |
| API-Sports hockey (`v1.hockey.api-sports.io/odds`) | 100 req/day (third-party claim) | Unverified; API-Sports odds usually keep a short window | Not stated | Yes (NHL league 57) | 403 "Missing application key" probe |
| odds-api.io | 100 req/hour | No history on free tier | No | Yes | odds-api.io/pricing/free |
| SportsGameOdds | 10 req/min, 2,500 objects/month | No; history is Pro and above ($99+) | Pro | Yes | vendor ML page |
| BALLDONTLIE NHL | Free tier covers teams/players only | No (odds are in a paid tier; unverified) | ? | Yes | 401 probe; secondary sources |
| MySportsFeeds | No free tier. Personal plan from $5/mo "if you qualify". ODDS add-on costs extra. | Base covers 2 seasons; older seasons $19-69 each | Not stated | Yes | mysportsfeeds.com/feed-pricing |

## Dead ends
- TeamRankings: NHL pages now redirect to the NFL-only homepage, so the site no longer covers NHL.
- SportsDatabase.com: returns 500, and robots.txt is 404.
- Killersports: now a JS SPA shell. I did not probe the SDQL query API because the time box ran out, and it may need a login.
- StatMuse Money: the natural-language URL returned 422 and has no odds table.
- Lineups.com: Cloudflare "Just a moment" challenge, which I did not bypass.
- Dimers: shows only live/today schedule odds; I found no historical route.
- fastRhockey `espn_nhl_betting`: a wrapper over ESPN, which F1 covers.

## Recommendation
Use DRatings as the 2024-25 open/close fill, and cross-check it against ESPN (2021-23, 2025-26) on overlapping games before trusting it. Write a cell parser and pull politely, at no more than 1 request every 3 s. Ask the user whether to get a free OddsPapi key to test archive depth for timestamped Pinnacle closes.
