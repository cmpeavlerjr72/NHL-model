# Lane I: SBRO 2021-23 and full DRatings 2021-25 lines pulls (INV-24)

Run 2026-10-15, 18:43 to 20:55 EDT (in-turn work). Sonnet worker. No orders, no credentials, no sub-agents.

## 1. HF push
`scripts/hf_sync_data.py push --dirs raw` at 18:44. Before: raw local 30657, remote 30648, 9 live-log files missing (dkex, goalies, kalshi 2026-10-15). After: raw 30657 = 30657, missing 0; results 11 = 11. The DRatings cache that follows is NOT yet on HF; push it after the task ends.

## 2. SBRO 2021-22 and 2022-23
- robots.txt (2026-10-15): `User-agent: *`, `Disallow: /go/`, `Allow: /`. No ToS or licence page found for the archive. Recorded in `docs/ops/data_sources.md` (Lane I section).
- The season pages hold the data as an inline HTML table (the old xlsx links no longer exist). 2 page fetches, cached in `data/raw/sbro/nhl-odds-2021-22.html` and `nhl-odds-2022-23.html` (gitignored).
- `scripts/pull_lines_sbro.py` and `scripts/build_lines_sbro.py` write `data/processed/lines_sbro_v1.parquet` (1743 rows): consensus open and close ML, open and close total (line plus both prices), one puck line (treated as close), matched to NHL `game_id`.
- **Match rate 1743 of 1743 parsed rows (100%), 0 unmatched** (key: local date + home + away; 0 date shifts, 0 swaps). Final scores agree with the NHL box for 1742 of 1743; the one miss is 2021020682 BUF-DET (SBRO 0-1, a shootout game). Not used for grading.
- **Coverage is PARTIAL for 2022-23: the SOURCE page stops at 2022-11-27 (342 of 1400 games, 24%).** 2021-22 is complete (1401 of 1401 including 89 playoff games, to 2022-06-26). 2022-23 from 2022-11-28 has no SBRO lines; DRatings is the only free source for the rest of that season.
- Total prices: the two rows are the visitor and home rows. Over/under assignment is inferred as row1 = over (correlation of row1-price-premium with over hit +0.039, n=1671, about 1.6 sigma: underpowered, unverified). Use the total line, not the side prices, until verified.
- SBRO defects seen in the cross-check: some opening ML are implausible (e.g. 2021020034 open -850/+600, close +117/-127), and 38 puck-line rows differ in sign from DRatings. SBRO is a single unnamed consensus.

## 3. DRatings full pull
- Parser reused (`src/nhl_sim/dratings.py`); new builder `scripts/build_lines_dratings.py` (long format: market, group, side, open / each book close / best / no-vig close, line, price). Completed-game pages carry only open and close fields. The builder rejects any page whose visible text matches in-game / live / in-play markers (L18); none of the pages fetched so far matched. 2025-26 and later: the builder asserts start < 2025-07-01 and the puller drops those index rows. One index page (94, the boundary page) lists 2025-26 rows by necessity; no 2025-26 game page was fetched.
- **Slice timings (measured, 3-4 min each):** index walk 65 pages in 218 s (3.35 s/page, sequential); game pages 75 in 224 s (3.0 s/page, 3 in flight under global 3 s spacing).
- **Hand verification:** 5 random 2024-25 games (CBJ@VGK, FLA@TOR x2, DAL@COL, WSH@CAR): all 60 market rows (ML, PL, total x offshore, vegas x 2 sides, 8 price columns) match an independent regex over the raw table HTML (0 mismatches). ML open/close/no-vig values also eyeballed against the page text.
- **Index:** 287 pages (445 down to 94) gave 5598 completed games dated 2021-09-01 to 2025-06-30, vs 5599 NHL regular-season plus playoff games in `games.parquet` (1401 + 1400 + 1400 + 1398). All 5598 match an NHL `game_id`. 1 NHL game (2024-25) has no DRatings row.
- **Finding (L19-style): DRatings labels pre-2024-25 Arizona games "Utah Mammoth"** (current name; 246 rows). The builder remaps UTA to ARI for games before 2024-07-01 and flags `dr_team_label_remapped`. The 102 Arizona games in the SBRO overlap agree with SBRO as well as the rest (median ML diff 0.0022 vs 0.0024), so the odds themselves look genuinely as-of, not rebuilt.
- **Scheduled task `NHL-Model-dratings-pull`** (one-shot, interactive-logon only, 10 h limit, unregisters itself at exit). First launch 19:09; I restarted it at 19:25 (stopped only its own two python PIDs) after finding the Arizona label issue; everything cached carried over. Order: games that overlap SBRO first (finished 20:51), then newest season first.
- Log: `results/logs/dratings_pull_2026-10-15.log`. At 20:50: 1700 of 5392 fetched this run, 0 failures, 1946 game pages on disk (169 MB raw). **Expected finish about 23:55 EDT** (3.0 s per page).
- On finish the task rebuilds `data/processed/lines_dratings_v1.parquet` and unregisters itself. **Resume command if interrupted** (cache-first, same log, from the repo root): `.venv/Scripts/python.exe scripts/pull_dratings_full.py`. Rebuild only: `.venv/Scripts/python.exe scripts/build_lines_dratings.py`.
- The `lines_dratings_v1.parquet` on disk now is a partial in-turn build and is NOT committed. Commit the final one after the task ends; then `hf_sync_data.py push --dirs raw` for the cache.

## 4. Cross-check SBRO vs DRatings
Script `scripts/crosscheck_sbro_dratings.py` (same tolerance logic as the ESPN check); outputs `data/processed/lines_crosscheck_sbro_dratings_v1.{csv,json}`. All 1743 SBRO games were already cached in DRatings (1401 from 2021-22, 342 from 2022-23), so this is complete for SBRO's own coverage. It is PARTIAL in the sense that SBRO has nothing for the rest of 2022-23.

| Check | n | Result |
|---|---|---|
| ML close, no-vig home prob, DR median across 7-8 books vs SBRO | 1743 | mean abs 0.0037, median 0.0024, p95 0.0107, max 0.167; 99.5% within 0.02; mean signed -0.0002 |
| ML open, DR offshore open vs SBRO open | 1743 | median 0.0071, p95 0.043, 78.7% within 0.02, max 0.43 |
| ML open, DR Vegas open vs SBRO open | 1743 | median 0.0065, p95 0.037, 83.1% within 0.02, max 0.53 |
| Total close line, DR mode of books vs SBRO | 1743 | 96.0% identical; every miss exactly 0.5 (30 at -0.5, 40 at +0.5) |
| Total open line, DR offshore open vs SBRO | 1743 | 88.9% identical; 137 at -0.5, 51 at +0.5, 3 at -1.0, 2 at +3.5 |
| Puck line (away side), DR close mode vs SBRO | 1743 | 97.8% identical; the other 38 are sign flips (3.0 apart), 2021-10-16 to 2022-11-21 |

Reading: closing ML is well inside the D11-style tolerance (median 0.0024, versus 0.0057 in the ESPN check); the worst outlier is 2021021045 (0.167) plus a 3-game cluster on 2021-12-02 at about 0.05. Closing total lines agree 96%, unlike ESPN BET vs DRatings (54%), which supports the D11 reading that ESPN BET picks its own main total. The open-ML tails come mostly from SBRO defects (the -850/+600 example), not DRatings. The 38 puck-line sign disagreements are unresolved; do not use the puck-line sign from either source for those games without a third source.

## Incidents
- **At about 19:00 I stopped Windows PID 15152 by mistake.** I was cleaning up a hung shell of my own and killed a PID I had read from a process listing without verifying its command line. It was Lane H's `scripts/diag_strength_state_replay.py --expire-first --out results/strength_state_r1/replay_expire_first`. Lane H must rerun that diag. Not repeated; afterwards I only stopped processes whose command line named my own task.
- Task restart at 19:25 (own PIDs 15120, 8904 and their cmd parent), described above.
- `git push` printed "fatal: Key not valid for use in specified state" once, but `git ls-remote origin main` showed the commit at 8af89a8.

## Files
Scripts: `scripts/pull_lines_sbro.py`, `build_lines_sbro.py`, `pull_dratings_full.py`, `build_lines_dratings.py`, `crosscheck_sbro_dratings.py`. Data: `data/processed/lines_sbro_v1.parquet`, `lines_crosscheck_sbro_dratings_v1.{csv,json}`. Docs: this file, `docs/ops/data_sources.md`.

## Proposed text for PM docs
- LEARNINGS L20: "Third-party historical pages can carry today's team names. DRatings labels pre-2024 Arizona games 'Utah Mammoth'. Every team-name join to history needs an era-aware map and an unmatched-row count."
- LEARNINGS L21: "A free single-consensus archive can silently stop mid-season. SBRO 2022-23 ends 2022-11-27; check max date against the schedule before trusting a season."
