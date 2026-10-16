# Lane D2: data hygiene (INV-16, INV-18), 2026-10-16

## Part 1: INV-16 weekly resumable pull

Clock: first pull 10:12:41 to 10:13:07 -04:00 (26 s; 138 network requests, 21,195 cache hits, 0 fails).

- Schedule refresh wrote the sibling `data/processed/schedule_weekly.parquet` (7,224 games; final 7,111 vs 7,100 at the audit: 11 new 2026-27 finals, all pulled with shift charts). `schedule.parquet` untouched.
- Games with no cached (non-empty) shift chart, before vs after: **105 -> 105** (57 in 2024-25, dated 2025-04-08 to 2025-04-15; 48 in 2026-27, dated 2026-09-30 to 2026-10-07). The API still returns an empty chart for all 105; 0 newly empty, 0 recovered. Lists: the scheduled task re-requests them every run.
- Task `NHL-Model-weekly-pull` registered (`scripts/register_weekly_pull_task.ps1`, `scripts/chain_weekly_pull.py`): Monday 06:00, interactive logon only. Fired by hand at 10:13:20: finished OK in about 28 s (net=105: exactly the empty-chart re-requests), `LastTaskResult = 0`, NextRunTime 2026-10-19 06:00. Log `logs/weekly_pull_2026-10-16.log`.
- Small script edits (defaults unchanged): `pull_schedule.py --out`, `pull_games.py --schedule`.
- User-Agent check: `src/nhl_sim/clients/nhl_api.py` and `src/nhl_sim/live/common.py` both use `NHL-Model-research/0.1 (personal read-only research)`. Other pull scripts use generic or `...NHL-Model-research` browser-style strings. No email address anywhere in `src/` or `scripts/` (grep). The doc line claiming the loggers' UA contains an email was wrong; fixed in `docs/ops/live_loggers.md`, which also gained the weekly-pull section.

## Part 2: INV-18, 2021-22 shootout typing

- 2021-22 has 102 SO games (= every game with `end_state_box == SO`; set-equal), all `periodType` SO, period 5. SO events: 747 attempts = 385 `shot-on-goal` (SHOT) + 138 `missed-shot` (MISS, with reason wide-of-net 91 / goalpost 25 / over-net 15 / hit-crossbar 7) + 224 `goal`; plus per-game period-start, period-end, game-end and 103 `shootout-complete` (game 2021020336 has it twice; harmless, admin event). No `failed-shot-attempt` and no `blocked-shot` in 2021-22 SO. All attempts carry shot type, shooter, goalie and coordinates. Situation codes are 1010/0101 (penalty-shot style).
- 2022-23 for contrast: 25 `failed-shot-attempt` (no shot type, no reason) appear in SO, so the new type is a finer label for attempts with no shot; 2021-22 simply has none.
- Exclusion check: `attempt_events` excludes on `period_type == "SO"`, so all 747 are excluded (tally `shootout_attempts` 747). Leakage into stage-3 targets (`attempt_rows_v1_20212022`: period max 4, no SO rows) = **0**. Stage-4 (shot location x type) uses the same event table and the same period-type test; 0 leak. Other consumers (`strength_state/events.py`) exclude SO for penalties, goals and stoppages.
- Verification against boxscore finals (102 games): SO winner by SO goals matches the box-score winner in 102/102; no SO ties; box score = regulation goals + 1 for the SO winner in 102/102 (both sides); regulation tied in all; attempts per game 4-18, home/away counts differ by at most 1; no duplicate event ids. 224 SO goals total. Caveat: boxscore and pbp are one NHL feed (same caveat as the audit), and this API exposes no separate SO summary.
- Side note (not 2021-22): 9 `failed-shot-attempt` events in regular play (2022-23 to 2025-26, situation 0101/1010) are penalty-shot attempts with no shot; they are not in SHOT_ATTEMPT_TYPES, so they are outside the targets but are counted in `failed_shot_attempt_events`. Negligible; PM may rule.
- **No fix needed.** Added regression test `tests/test_so_2021_22.py` (skips if processed tables are absent).

## Not done
Independent non-NHL second source for finals (still the audit's PARTIAL item). Shift-chart gaps cannot be backfilled from this API.
