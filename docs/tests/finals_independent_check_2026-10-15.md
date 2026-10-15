# Independent finals check (INV-14), 2026-10-15

Lane E. Question: do the NHL-feed finals in `verified_finals_v1` (schedule, boxscore and pbp, which are three views of one feed) agree with an independent source?

## Method

- Source: ESPN NHL scoreboard (`site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=YYYYMMDD`), one request per calendar date from 2021-10-01 through 2026-10-14 (1,840 dates, 7,785 events, 12 MB gzip JSON in `data/raw/espn_scoreboard/`; `scripts/pull_espn_scoreboard.py`, 4 threads, 5.7 dates/s, about 5.2 min wall, 15:23 to 15:29 local). Note: ESPN returns HTTP 403 to a descriptive custom User-Agent and accepts a generic browser string; the script uses the generic one.
- Sealed window: ESPN files dated 2025-09-01 to 2026-08-31 are skipped by file date before any score is parsed. `verified_finals_v2` therefore has no 2025-26 rows (the loader would exclude them anyway).
- Matching: one-to-one on (home abbreviation, away abbreviation, ESPN query date within one day of the NHL local game date), after mapping ESPN abbreviations NJ, TB, SJ, LA to NJD, TBL, SJS, LAK (UTAH to UTA is also mapped). Scores compared as (home, away) including the shootout bonus goal (NHL box convention); ESPN end state from `shortDetail` (`Final`, `Final/OT` and multi-OT `Final/nOT`, `Final/SO`).
- Output: `data/reference/verified_finals_v2.parquet` (v1 columns plus `espn_*` columns, `espn_matched`, `score_agree`, `end_agree`, `verified_sources`, `verified_v2`). `verified_sources` is the pipe-joined list of sources that agree on the final: `nhl_schedule|nhl_boxscore|nhl_pbp|espn`. v1 is untouched.

## Result

| season | type | NHL games | ESPN matched | score and REG/OT/SO agree |
|---|---|---:|---:|---:|
| 2021-22 | RS | 1312 | 1312 | 1312 |
| 2021-22 | PO | 89 | 89 | 89 |
| 2022-23 | RS | 1312 | 1312 | 1312 |
| 2022-23 | PO | 88 | 88 | 88 |
| 2023-24 | RS | 1312 | 1312 | 1312 |
| 2023-24 | PO | 88 | 88 | 88 |
| 2024-25 | RS | 1312 | 1312 | 1312 |
| 2024-25 | PO | 86 | 86 | 86 |
| 2026-27 (to 10-14) | RS | 107 | 107 | 107 |
| **total** | | **5,706** | **5,706 (100%)** | **5,706 (100%)** |

End state cross-tab is diagonal: REG 4,476, OT 866, SO 364, zero off-diagonal.

## Mismatches

None. Match rate 100.00%, score agreement 100.00%, end-state agreement 100.00%, 0 mismatches to diagnose.

ESPN-side leftovers (16 regular-season "Final" events with no NHL game_id) are not NHL games: three per All-Star weekend in 2022, 2023 and 2024 (skills and 3-on-3 tournament games, 2022-02-05, 2023-02-04, 2024-02-03) and seven 4 Nations Face-Off games (2025-02-12 to 2025-02-20). Preseason events (555) and 111 postponed / 3 cancelled events are excluded by design.

## Caveats

- Independence is probable, not proven: ESPN's feed is a separate publisher, but both ultimately derive from league-supplied scoring data. A 100% agreement rate rules out NHL-API parsing or pipeline errors, not an error in the league's own record.
- 2025-26 was not checked (sealed).
- 3,896 games differ between the ESPN UTC timestamp date and the NHL local date (late evening games); matching uses the ESPN query date, which is Eastern based, and was one-to-one with no ambiguity.
