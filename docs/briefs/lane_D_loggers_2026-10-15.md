# Lane D brief: forward loggers + scheduled tasks; ESPN coverage (INV-8, INV-10, INV-11)

Model: Sonnet. Core cap: 2. Rules: `docs/ops/worker_rules_2026-10-15.md` and `CLAUDE.md` (read both first). Decisions you implement: `ARCHITECTURE_DECISIONS.md` D6-D8.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Context

Lane B's audit (`docs/ops/lines_sources_audit_2026-10-15.md`, `docs/ops/data_sources.md`, probes in `docs/ops/probes/laneB_*.py`) found access methods for Daily Faceoff goalie JSON, Kalshi NHL markets (anonymous), and the DKeX NHL board (league 42133, percent-encoded query, CFB header recipe). None has usable history, so every day not logged is lost. Build from Lane B's probes; do not re-research.

## Hard limits

Read-only. No orders, no logins, no account endpoints, no credentials. Kalshi calls are anonymous. Poll sparsely, retry with backoff, identify a User-Agent. Daily Faceoff: one fetch per run.

## Steps (chained, in order)

1. **Loggers** (`scripts/log_goalies.py`, `scripts/log_kalshi_nhl.py`, `scripts/log_dkex_nhl.py`, shared helpers in `src/nhl_sim/live/`). Each run writes one timestamped raw snapshot (`fetched_at` UTC in the filename AND inside the payload) under `data/raw/live/<source>/<YYYY-MM-DD>/`, plus one append-only normalised row file per day (parquet or jsonl):
   - goalies: game/date, team, goalie name, status (Confirmed/Likely/Unconfirmed), source timestamp, fetched_at.
   - Kalshi: every open NHL market (game winner, spread, totals, team totals, period, player props): ticker, event, strike, yes bid/ask, last, volume, open interest, fetched_at.
   - DKeX: every NHL board selection: event, market, selection, line/strike, price, fetched_at.
   Each logger exits non-zero on failure and writes a one-line status to `logs/live/<source>.log`. A failed run never deletes or overwrites earlier files. Offline tests with saved fixtures in `tests/`.
2. **Runner.** `scripts/chain_live_log.py` runs all three independently (one failing does not stop the others). It needs only `requests` (plus pyarrow if you use parquet). Use `C:\Users\devuser\NHL-Model\.venv\Scripts\python.exe` if it exists and has what you need (read-only, do not pip install into it, Lane A owns it); otherwise tell the PM which packages are missing and use system `py -3.12` for testing.
3. **Schedule.** Register Windows Task Scheduler tasks (user-approved, D8), names prefixed `NHL-Model-`:
   - `NHL-Model-live-log`: every 30 minutes from 09:00 to 23:30 local time, daily, running `chain_live_log.py`. It runs whether the user is logged on or not only if that needs no stored password; otherwise "only when logged on". Hidden window. No overlapping instances.
   Document the exact registration and removal commands in `docs/ops/live_loggers.md` and verify with `Get-ScheduledTask` / `Get-ScheduledTaskInfo` after the first scheduled run fires (wait in-turn for it; ≤10 min blocking waits).
4. **ESPN coverage (INV-11).** Using Lane B's ESPN pickcenter probe, measure line coverage for EVERY regular-season game in 2023-24 and 2024-25 (and 2025-26 for comparison only, no grading): % games with any line, provider, whether open/close exist, ML/PL/total present. Cache raw JSON under `data/raw/espn/`. Write `docs/tests/espn_lines_coverage_2026-10-15.md`. If Lane A's `data/processed/games*.parquet` is not ready, use the ESPN scoreboard for game ids.
5. Commit only your files, push, verify with `git ls-remote origin main`.

## Out of scope

Modeling, Odds API (D7: not purchased), anything Lane A or Lane C owns, PM-owned docs.

## Report

Under 400 words: logger status (files written in the first scheduled run, row counts per source), task registration evidence, ESPN coverage table summary, failures, commit hashes.
