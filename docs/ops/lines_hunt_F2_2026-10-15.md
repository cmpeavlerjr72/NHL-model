# Lane F2: datasets, archives, exchanges (INV-19 lines hunt)

Run 2026-10-15 16:47-16:55 EDT. Read-only, anonymous, generic UA. Probes: `docs/ops/probes/laneF2_probe1..7.py`. Samples: `data/samples_laneF/f2/`.

## Headline

No free source found with 2024-25 NHL open/close lines. Free archives stop at 2022-23 (SBRO, GitHub); free Kaggle/HF data starts at 2025-26. The only free 2024-25 price series is Polymarket moneyline (exchange probabilities, not book lines, from 2024-12-04). Sold sources (Flashscore-derived minmaxxxer, OddsPortal-derived oliviersportsdata, The Odds API) do cover 2024-25.

## Ranking

| # | Source | 2024-25 | Open/close | Books | Terms | Bulk effort | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | SBRO per-season HTML pages (2007-08 to 2022-23) | NO | open+close ML, close puck line (+-1.5), open+close total | one SBR consensus line | robots allow all; ToS not read | 16 requests | Best free for 2021-23 cross-check of ESPN Unibet |
| 2 | GitHub flancast90/sportsbookreview-scraper `data/nhl_archive_10Y.json` | NO (ends 2022-06-24) | open+close ML, close PL, open+close total | one SBR line | MIT repo (data origin SBR) | 1 file, 7.3 MB | Same content as SBRO, easier to parse; 13,678 games |
| 3 | Polymarket gamma + clob | YES, game moneyline events from 2024-12-04 | no open/close; coarse daily history | 1 exchange market | public API, ToS not read | 1 history call per game | Only free 2024-25 price signal; ML only |
| 4 | Kaggle/HF `minmaxer(xxxer)/nhl-closing-odds-2025-26` | NO (2025-26 only) | open+close consensus no-vig prob, spread, total | median 20 books, consensus | CC BY 4.0; HF download anonymous | 1 file | Free for 2025-26 (ESPN DK already covers); other seasons are sold |
| 5 | Harvard Dataverse doi:10.7910/DVN/39ZFRO | NO (2018-19 to 2021-22) | per-team xlsx, 12 books | 12 | CC BY-NC | ~220 messy files | Low value, overlaps SBRO |

## Proofs

### SBRO (sportsbookreviewsonline.com)
- Index `https://www.sportsbookreviewsonline.com/scoresoddsarchives/nhl/nhloddsarchives.htm` returns 200 (Lane B logged a 404 for an older path). Season pages `/scoresoddsarchives/nhl-odds-YYYY-YY/` are linked for 2007-08 to 2019-20, `nhl-odds-2021`, `2021-22`, `2022-23`. No xlsx links any more: the table is rendered as HTML.
- `nhl-odds-2023-24`, `2024-25`, `2025-26` all 301 to the home page, so they do not exist. Index last modified 2024-11-07.
- Columns: Date(MMDD, no year; infer from season) Rot VH Team 1st 2nd 3rd Final Open Close PuckLine OpenOU CloseOU, two rows per game. Example 2022-10-07 San Jose v Nashville: open 150/-180, close 165/-185, total 5.5 open and close. Sample: `sbro_nhl_2022-23_head.txt`.
- robots.txt: `Allow: /` (only /go/ disallowed). Wayback also holds the season pages (2026 snapshots).

### GitHub flancast90/sportsbookreview-scraper
- `https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/main/data/nhl_archive_10Y.json`: 7,322,138 bytes, 13,678 rows, seasons 2011..2021 (2021 = 1,400 games, max date 2022-06-24). Fields: period scores, home/away open_ml and close_ml, close spread (+odds), open/close over_under (+odds). Team names are nicknames. Sample: `gh_flancast90_nhl_archive_sample.json`.
- Other repos found (unauthenticated repo search only): nothing with 2023-25 NHL odds (Sports-Odds-Algorithms 2020, oddshub TUI, mcp-sports-hub, hockey-betting-scraper). Code search needs auth.

### Polymarket
- Gamma: `https://gamma-api.polymarket.com/events?tag_slug=nhl&end_date_min=2025-01-14&end_date_max=2025-01-16&limit=100` returns game events with slug `nhl-{away}-{home}-YYYY-MM-DD` (e.g. `nhl-fla-phi-2025-01-13`, volume about 62k USD). Earliest game event found 2024-12-04; Oct-Nov 2024 window returned only 6 non-game events. Futures exist from 2024-02.
- One moneyline market per event with `clobTokenIds`.
- History: `https://clob.polymarket.com/prices-history?market={token}&interval=max&fidelity=1440` returned 2 points for a resolved game; `fidelity=60` returned empty. Coarse; not a closing line. No spread or total. Sample: `polymarket_nhl_2025-01-15_sample.json`.

### Kaggle / Hugging Face (public listing API, no login)
- `minmaxer/nhl-closing-odds-2025-26` (Kaggle) = `minmaxxxer/nhl-closing-odds-2025-26` (HF, ungated, anonymous CSV). 1,394 games, open/close no-vig home win prob, spread, total, graded results, Flashscore ids, median 20 books. Its description promotes a paid Apify Actor / RapidAPI product with per-book open/close back to 2009, so 2024-25 exists but is sold. `nhl-odds-2026-27` is updated weekly (forward collection). Sample: `hf_minmaxxxer_nhl_2025_26_head.csv`.
- `jonathanncoletti/nhl-historical-game-data`: ESPN-derived (spread, over_under, favourite_moneyline); its 2024-25 companion states it has no odds: the same ESPN hole.
- `oliviersportsdata/us-sports-master-historical-closing-odds`: NHL 1998-2026 closing ML, OddsPortal-sourced (terms forbid, per Lane B) and sold. Do not use.
- `michaelmallari/sportsbook-odds-on-nhl-games` and HF `michaelmallari/sportsbook-nhl`: 2021-22 and 2022-23 only; HF is gated (login). Redundant with SBRO.

### Wayback CDX (distinct 200-status days, 2024-10-01 to 2025-06-30)
- sportsbookreview.com/betting-odds/nhl-hockey/*: 52 days; covers.com/sport/hockey/nhl/odds*: 29; oddsshark.com/nhl/odds*: 56; covers.com/sports/nhl/matchups*: 14. Most SBR hits are the undated landing page, futures and `line-history/{id}` pages; only one `?date=` snapshot seen in January. Well under 20% of days, content unverified. Not usable for backfill.

### Other
- Betfair Historical Data: historicdata.betfair.com returns 403 to scripts. Per Betfair workbook docs BASIC is free but needs a Betfair account; ice hockey and granularity unconfirmed. Not registered. Exchange prices only.
- Kalshi: Lane B result stands (KXNHLGAME history from 2025-04). Old prefix `NHLGAME` returns empty; date filters on historical/markets did not take, so no older ticker found. Not re-verified deeper.
- Zenodo and OSF: no NHL odds datasets. Dataverse: only DVN/39ZFRO above; "Line Movement Dataset" (DVN/AONGK9) is Jun-Aug 2026 aggregates, no NHL game rows.
- Princeton DSS not re-probed (bot check). Pinnacle public closing dumps: none found on GitHub, Kaggle or Zenodo searches.

## Recommendations
1. For 2021-23, pull the SBRO pages or the GitHub JSON (open+close ML and total, close PL) to validate and enrich the ESPN Unibet closes; join on date + team.
2. For 2024-25 open/close, free options in F2 are exhausted. Best remaining: F1 live endpoints (SBR `?date=`, Action Network) or paid (The Odds API historical; minmaxxxer Actor).
3. Optionally collect Polymarket moneyline from 2024-12 as a coarse sanity series.
4. Pull `minmaxxxer/nhl-odds-2026-27` weekly for forward data (CC BY 4.0, attribute).
