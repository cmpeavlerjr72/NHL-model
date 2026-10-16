# Lane D2 brief: INV-16 weekly resumable pull, INV-18 2021-22 shootout typing

Model: Sonnet. Core cap: 2 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first. Network: the NHL API only, polite (at most 4 concurrent, backoff, cache-first, never re-fetch a cached file).
Context: `docs/tests/data_audit_nhl_api_2026-10-15.md` (sections 1, 4 and the open items), `scripts/pull_games.py`, `docs/ops/live_loggers.md` (how the existing `NHL-Model-live-log` scheduled task is registered; copy its pattern).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Lanes A (stage 4) and O2 (AWS) are running. Lane A reads `data/processed/events`: do NOT rewrite any existing processed file. Any rebuilt table is a versioned sibling.

## Part 1: INV-16

1. Run `scripts/pull_games.py` once now (cache-first). Report before/after counts of games with empty shift charts: 57 in 2024-25 after 04-08, and 48 early 2026-27 at the audit. Say which ones the API still returns empty.
2. Register a weekly scheduled task `NHL-Model-weekly-pull` (Monday 06:00 local, interactive-logon only, like the live logger). It runs the resumable pull and appends to a dated log under `logs/`. Fire it once by hand and confirm `LastTaskResult` is 0.
3. Document it in `docs/ops/live_loggers.md` under a new heading. Also correct that doc's stale line saying the loggers' User-Agent contains an email address: check the actual UA string in `src/nhl_sim/live/common.py` and the pull scripts, report what it is (no email may remain; if one does, remove it and say so), and fix the doc.

## Part 2: INV-18

How did 2021-22 type its shootout attempts? (`failed-shot-attempt` first appears in 2022-23.)
1. Find the 2021-22 shootout events (period type SO), and tabulate the event types and fields used.
2. Check that the loader's shootout exclusion (shot-attempt targets exclude shootout attempts, SA-R1) catches every 2021-22 shootout attempt. Report how many leak into any stage-3 or stage-4 target, if any.
3. Check the shootout winner and the shootout goal count for all 2021-22 SO games against the boxscore / verified finals.
4. If a fix is needed, do it in the event map with a test. Do not rebuild shared processed tables in place; write a versioned sibling and report it, and the PM switches.

## Report

`docs/tests/data_hygiene_d2_2026-10-16.md`. Commit, push, verify with `git ls-remote`. Message to the PM: under 400 words.
