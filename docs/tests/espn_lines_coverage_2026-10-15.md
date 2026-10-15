# ESPN pickcenter line coverage (INV-11), 2026-10-15

Question: for EVERY regular-season game in 2023-24 and 2024-25 (2025-26 for comparison only, no grading), does ESPN's free `summary.pickcenter` carry a line, from which provider, with open/close, and which markets?

## Method

- Game list: `data/processed/schedule.parquet` (Lane A), `game_type == 2`, finished (`OFF`/`FINAL`): 1312 games per season, 3936 total.
- ESPN event ids from `scoreboard?dates=YYYYMMDD` (one call per game date; range queries return HTTP 400). Matched on (local date, home, away) with ESPN abbreviations TB/NJ/SJ/LA/UTAH mapped to NHL codes: 3936 of 3936 matched, 0 unmatched.
- Each event: `summary?event=<id>`, read `pickcenter`. Flags per provider row: ML, PL, total present (new-format `moneyline`/`pointSpread`/`total` blocks, or legacy `homeTeamOdds.moneyLine` / `spread` / `overUnder`); open present, close present (new-format `.open` / `.close` blocks only).
- Rate: about 2 req/s total (2 threads, global 0.5 s spacing), polite User-Agent. Wall clock 2026-10-15 14:55 to 15:33 (528 scoreboards 268 s, 3936 summaries 1994 s). No errors; nothing failed or was left uncached.
- Raw cache: `data/raw/espn/scoreboard/<date>.json` (full) and `data/raw/espn/summary/<eventid>.json` (trimmed to `pickcenter`, `odds`, status; gitignored). Per game x provider table: `data/processed/espn_lines_coverage.csv`. Scripts: `scripts/diag_espn_lines_coverage.py`, `scripts/diag_espn_lines_summary.py`.
- Incident note: a first launch used a User-Agent containing an email address; ESPN answered 403 to that UA (plain UA gets 200). It cached nothing and was stopped after under two minutes; the relaunch used the plain UA.

## Result

| Season | Games | Any line | ML | PL | Total | Open | Close | Open+Close | Provider |
|---|---|---|---|---|---|---|---|---|---|
| 2023-24 | 1312 | 100.0% | 100.0% | 98.5% | 100.0% | 0% | 0% | 0% | Unibet (1312) |
| 2024-25 | 1312 | 0.0% | 0.0% | 0.0% | 0.0% | 0% | 0% | 0% | none |
| 2025-26 (comparison only) | 1312 | 71.3% | 71.3% | 71.3% | 71.3% | 71.3% | 71.3% | 71.3% | DraftKings (936) |

By month (any line):

- 2023-24: 100% every month, Oct 2023 through Apr 2024.
- 2024-25: 0% every month. `pickcenter` is an empty list for all 1312 games and the game-level `odds` field is also empty, so this is a real hole, not a fetch error.
- 2025-26: 0% in Oct 2025, 12.9% in Nov (29 of 225), 100% from 2025-11-25 through 2026-04-16 (936 games, all with open and close for ML/PL/total).

## Reading the numbers

- 2023-24: complete but a single Unibet line in the legacy format: ML, total, and puck line (PL missing for 1.5% of games). No open/close and no timestamp, so it cannot be treated as a closing line or used for CLV; it is usable as an "a line of unknown timing" accuracy reference only, and the leak test applies before any use as a feature.
- 2024-25: ESPN has no lines for the whole season. Not recoverable from this source; this is the gap The Odds API historical (D7: not purchased) or Kalshi `/historical` (2025-04 on; 2024-25 regular season partly pre-dates it) would have to fill.
- 2025-26: DraftKings open+close from 2025-11-25 onward only, for comparison; not graded.
- No sample-size caveat applies to the coverage percentages (full population of regular-season games). Provider semantics (what "close" means in time) are unverified.

## Proposed text for PM docs

Add to `docs/ops/data_sources.md` ESPN row: "Full-population check 2026-10-15: 2023-24 Unibet single line 100% (no open/close); 2024-25 EMPTY (0 of 1312); 2025-26 DraftKings open+close from 2025-11-25 (936 of 1312)."
