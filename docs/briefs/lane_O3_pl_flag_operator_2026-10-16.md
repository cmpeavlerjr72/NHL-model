# Lane O3 brief: INV-38 puck-line sign flag, then AWS operator for the box queue

Model: Sonnet. Core cap: 1 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` (Compute) and `docs/ops/worker_rules_2026-10-16.md`. You are now the only lane that touches AWS. Chain: `docs/ops/aws_launch_chain.md`, `scripts/run_box_request.py`; previous run `docs/ops/aws_operator_O2_2026-10-16.md`. Spend cap $60 for the session (spent so far $0), stop launching at $50.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Part A: INV-38 (D21 in `ARCHITECTURE_DECISIONS.md`)

1. Write `scripts/build_lines_dratings_v2.py`, or add a flag step that reads v1, producing `data/processed/lines_dratings_v2.parquet`. It is v1 plus a per-game boolean `pl_sign_suspect`: the DRatings puck-line favourite (-1.5 side, closing) differs from its own no-vig closing ML favourite. Exact pick'em games (no-vig within 0.5 pp) are flagged `pl_sign_ambiguous`, not suspect. Do not rewrite any sign. Do not touch v1.
2. Add a test, and check that the 38 games in `docs/ops/lines_closeout_O2_2026-10-16.md` are reproduced (32 suspect, or explain the difference).
3. Report counts by season, plus the open-line version of the same check. Write `docs/ops/lines_pl_flag_O3_2026-10-16.md`. Commit, push, verify.

## Part B: serve the box queue

Lane A (stage 4, `docs/briefs/lane_A_shot_attribute_r1_2026-10-16.md`) may file `docs/ops/box_queue/req_A_*.md`. Until 17:00 EDT or until Lane A's report commit appears in `git log` (`shot_attribute_sl_r1`), check every 5 minutes for a `req_*.md` without a matching `done_` (blocking in-turn waits of at most 10 min). Run each with `run_box_request.py`, verify termination with `describe-instances`, and write, commit and push the done file promptly.

Before reporting, paste the `describe-instances` output (nothing pending or running) and the session spend. Report `docs/ops/aws_operator_O3_2026-10-16.md`. Message to the PM: under 400 words.
