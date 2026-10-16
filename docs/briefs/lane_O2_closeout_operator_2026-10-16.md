# Lane O2 brief: INV-24 DRatings close-out, then AWS operator for the box queue

Model: Sonnet. Core cap: 1 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` (Compute) and `docs/ops/worker_rules_2026-10-16.md`. You are today's only lane that touches AWS. Chain: `docs/ops/aws_launch_chain.md`, `scripts/run_box_request.py`; previous run `docs/ops/aws_operator_O_2026-10-15.md`. Spend cap $60, stop launching at $50.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Part A: INV-24 close-out (do first)

The detached DRatings pull finished 2026-10-15 23:55 (log `results/logs/dratings_pull_2026-10-15.log`: 5392 ok, 0 fail, 0 games without a page; the log says the task unregistered, but `Get-ScheduledTask NHL-Model-dratings-pull` still listed it at 09:20 today: check, and if it is still registered and not running, unregister it).
1. Validate `data/processed/lines_dratings_v1.parquet` (490,968 rows, 5,598 game_ids): every game_id in `games.parquet`, no game dated on/after 2025-07-01, the UTA->ARI remap flag count, per-season game counts vs `games.parquet`, which single 2024-25 NHL game has no row. Then commit it.
2. `scripts/hf_sync_data.py push --dirs raw`, then `status`: 0 outstanding. Record before/after counts.
3. The 38 SBRO-vs-DRatings puck-line sign mismatches (`data/processed/lines_crosscheck_sbro_dratings_v1.csv`): tabulate them (game, both signs, both ML favourites, final margin). For each, say which source's sign agrees with its own ML favourite (the puck-line favourite is -1.5 on the ML favourite in nearly all NHL games). Do not fetch a third source. The PM rules.
4. Write `docs/ops/lines_closeout_O2_2026-10-16.md`; commit, push, verify.

## Part B: serve the box queue

Until 17:00 EDT or until the PM's lanes S3 and L2 have both reported (check `git log` for their report commits), check `docs/ops/box_queue/` for new `req_*.md` without a matching `done_` every 5 minutes (blocking in-turn waits of at most 10 min). Run each with `run_box_request.py`, verify termination with `describe-instances`, write the done file, commit and push it promptly (the requesting lane is waiting on it). Before reporting, paste the `describe-instances` output showing nothing running or pending, and the session spend.

Report `docs/ops/aws_operator_O2_2026-10-16.md`. Message to the PM under 400 words.
