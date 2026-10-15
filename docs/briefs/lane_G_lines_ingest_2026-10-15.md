# Lane G brief: ESPN core lines ingest 2023-24 + 2024-25, DRatings cross-check (INV-23)

Model: Sonnet. Core cap: 2. Rules: `CLAUDE.md`, `docs/ops/worker_rules_2026-10-15.md`. Decision you implement: `ARCHITECTURE_DECISIONS.md` D10. Read `docs/ops/lines_hunt_F1_2026-10-15.md` and `docs/ops/lines_hunt_F3_2026-10-15.md`, and reuse their probes (`docs/ops/probes/laneF1_*`, `laneF3_dratings.py`). Read LEARNINGS L18.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start.
- Stop launching new pulls at **17:30 EDT**.
- The report must be committed and pushed by **17:40 EDT**.
- Anything unfinished is marked PARTIAL with the resume command.

## Steps (chained)

1. **Client + puller.**
   - `src/nhl_sim/clients/espn_core_odds.py` and `scripts/pull_lines_espn_core.py`.
   - Game ids: ESPN event ids from `data/raw/espn_scoreboard/` (Lane E's cache), mapped to NHL `game_id`.
   - Raw cache: `data/raw/espn_core_odds/<event_id>.json`. Never re-fetch a cached file.
   - At most 4 concurrent requests, backoff on errors, and a generic User-Agent with no personal info.
   - Order of work: 2024-25 regular season first, then 2024-25 playoffs, then 2023-24.
   - Do NOT pull 2025-26 (sealed).
   - Time a 3-minute slice and extrapolate before the full run.
2. **Parse to `data/processed/lines_espn_core_v1.parquet`.**
   - One row per game x provider x market: `game_id, season, provider, market` (ml / pl / total), `side_or_line, open_price, close_price, open_line, close_line`.
   - Keep only pregame provider items. Identify live items explicitly ("Live Odds" in the provider name, or an id you verify) and drop them.
   - Fail the build if a game has an ambiguous provider set.
   - Every parsed close moneyline must have an implied probability sum (vig) between 1.00 and 1.10. List the outliers.
   - Report coverage per season and market: % of games with open, % with close.
   - Offline tests with a saved fixture, including one live item that must be dropped.
3. **DRatings cross-check.**
   - Write a cell parser for DRatings game pages.
   - Pull a 2024-25 sample of at least 100 games, spread across months; polite, 3 s between requests.
   - Raw pages go to `data/raw/dratings/`.
   - Compare against ESPN core on the same games:
     - moneyline close implied probability (no-vig), mean absolute difference and the max;
     - total line, % identical;
     - puck line, % identical.
   - Report in `docs/tests/lines_crosscheck_espn_dratings_2026-10-15.md`.
   - Pre-set tolerance: median |no-vig ML prob difference| <= 0.02 and total-line agreement >= 85% means PASS; otherwise FAIL with a diagnosis.
4. Commit only your files, push, and verify with `git ls-remote origin main`.

## Out of scope

SBRO / 2021-23 (INV-24), full DRatings pull, any grading or ROI, PM-owned docs, other lanes' files.

## Report

Under 300 words:
- pull counts per season;
- coverage table;
- live items dropped;
- vig outliers;
- the cross-check numbers and PASS/FAIL;
- PARTIAL items with the resume command;
- commit hash.
