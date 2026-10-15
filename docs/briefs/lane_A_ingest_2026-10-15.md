# Lane A brief: NHL API ingest + data audit (INV-1, INV-2)

Model: Sonnet. Core cap: 4. Rules: `docs/ops/worker_rules_2026-10-15.md` and `CLAUDE.md` (read both first).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Goal

A complete, cached, re-runnable raw pull of public NHL API data for regular season + playoffs, 2021-22 through today (2026-27 in progress), and an audit that tells the PM what the data can and cannot support.

## Steps (chained; do them in order in this one turn)

1. **Environment.** Create `.venv` with Python 3.12 (`py -3.12 -m venv .venv`), install the project (`pip install -e .[sim,dev]`). Commit nothing in `.venv`.
2. **Client.** `src/nhl_sim/clients/nhl_api.py`: a small client over `api-web.nhle.com/v1` (schedule, gamecenter play-by-play, boxscore, roster) and `api.nhle.com/stats/rest/en` (shift charts by gameId). Disk cache under `data/raw/nhl_api/<endpoint>/<key>.json`; never re-fetch a cached completed game. Polite: <=4 concurrent, backoff, User-Agent. Add `tests/test_nhl_api_client.py` (offline, using a saved fixture).
3. **Pull scripts.** `scripts/pull_schedule.py`, `scripts/pull_games.py` (pbp + boxscore + shifts per game id, resumable, logs progress to `logs/`). Time a slice of at least 3 minutes, extrapolate, report the measured rate, then run the full pull in-turn. If the full pull will exceed ~3 hours at the measured rate, pull 2023-24, 2024-25 and 2026-27-to-date first, then report with the resume command for the rest.
4. **Processed tables** (parquet, `data/processed/`): `games` (game_id, season, type, date, puck-drop UTC, home/away, final score, end state REG/OT/SO), `events` (one row per pbp event with normalised coordinates and strength state), `shifts`, `player_box`, `goalie_box`. Explicit event-type mapping table in `src/nhl_sim/pbp/event_map.py` with a test that FAILS on an unknown type.
5. **Verified finals.** Cross-check final scores and REG/OT/SO between at least two sources (boxscore vs schedule/score endpoint vs pbp-accumulated goals). Write `data/reference/verified_finals_v1.parquet`; list every disagreement.
6. **Audit doc** `docs/tests/data_audit_nhl_api_2026-10-15.md` with, per season: games pulled / expected; event-type vocabulary and any drift; % shots with coordinates; coordinate convention (does the rink side flip by period?); shift-chart coverage (% games with shifts, % of game time with 5+5 skaters identified); goalie start identification; per-season reference numbers (goals/game, SOG/game, PP opps/team-game, PP%, OT rate, SO rate, empty-net goals/game, home win %); finals disagreements; anything that blocks the plan in `docs/FRAMEWORK_PLAN.md`.

## Out of scope

Modeling, features, ratings, lines. Do not edit PM-owned docs.

## Report

Under 400 words per the worker rules, with the audit doc path and commit hashes.
