# Lane I brief: SBRO 2021-23 + full DRatings 2021-25 lines pulls (INV-24)

Model: Sonnet. Core cap: 2. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`. Read both first.
Decisions you implement: `ARCHITECTURE_DECISIONS.md` D10 and D11. Read LEARNINGS L9, L10, L18 and L19.
Read `docs/ops/lines_hunt_F3_2026-10-15.md` and `docs/ops/lines_hunt_F1_2026-10-15.md`, and reuse `docs/ops/probes/laneF3_dratings.py`, `scripts/pull_dratings_sample.py`, `src/nhl_sim/dratings.py` and the Lane G ingest pattern (`scripts/pull_lines_espn_core.py`, `scripts/build_lines_espn_core.py`).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start.
- Everything you run in-turn stops by **22:30 EDT**. Commit and push the report by **22:45 EDT**.

## Exception to the waiting rule (PM grant, this lane only)

The full DRatings pull takes about 70 min per season at 3 s/request, so about 5 h for 4 seasons, and it outlives this turn. Run it as a **detached, resumable, one-shot Windows scheduled task**: name it `NHL-Model-dratings-pull`, set it to run once, and make it run only while the user is logged on. It is not a child of your shell. Its script must:

- skip every page already cached under `data/raw/dratings/` (never re-fetch);
- log progress to `results/logs/dratings_pull_<date>.log`;
- build `data/processed/lines_dratings_v1.parquet` from the cache when it finishes;
- unregister its own task when it ends.

Before launching it, measure a >= 3 minute slice in-turn and verify the parsed rows on 5 games by hand against the page.

## Steps (chained, in order)

1. **HF push.** Push `data/raw` to HF (`scripts/hf_sync_data.py`), because the live-log files have accumulated (session-resume note). Report the status count.
2. **SBRO 2021-22 + 2022-23.** Do the following:
   - Check robots.txt and the terms first, and record them in `docs/ops/data_sources.md` (append a section).
   - Pull, cache under `data/raw/sbro/`, and parse to `data/processed/lines_sbro_v1.parquet`: consensus open/close ML and total, and close PL, matched to NHL `game_id`.
   - Report the match rate and list the unmatched games.
3. **DRatings full pull.** Run the slice, then the detached task. The target is every game 2021-22 through 2024-25.
   - Pull NOTHING for 2025-26 (sealed) and nothing for 2026-27.
   - Keep pregame/close fields only. If a page shows any in-game price, the parser rejects it (L18).
4. **Cross-check SBRO vs DRatings** on the 2021-23 games DRatings has cached by 22:15. Use the same tolerance logic as `scripts/crosscheck_espn_dratings.py`. Report it as PARTIAL coverage, with n.
5. **Report.** Write `docs/ops/lines_pulls_I_2026-10-15.md` with the slice timing, the task name, the log path, the expected finish time and the resume command. Commit only your files by explicit path, push, and verify.

## Concurrency

Lane H (Opus, engine core) runs at the same time and uses 6 cores and `data/processed/strength_state/`. Stay network-bound and do not touch its paths.

## Report to PM (under 400 words)

Give the result per step with numbers, the scheduled task status and its expected finish, what is PARTIAL, any incidents, and the commits.
