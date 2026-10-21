# Lane Z brief: stage 7-8 step-0 audit (INV-65): goalie pulls, empty net, overtime, shootout, in-game goalie changes, rebounds

Model: Sonnet. Core cap: 4 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus `docs/FRAMEWORK_PLAN.md` (stages 7-8), `docs/gates.yaml` (G7), `docs/ops/sim_output_schema.md`, and the data audit `docs/tests/data_audit_nhl_api_2026-10-15.md`. Data through the single loader `src/nhl_sim/data/load.py` only (the seal stays on).
Commit attribution line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`

**Scope.** This is a read-only empirical audit to ground the stage 7 and stage 8 pre-registrations. No model is fit, no parameter is chosen, nothing gates. **Use the training seasons only: 2021-22, 2022-23, 2023-24.** 2024-25 is the fold-2 holdout and must not be read, not even for a count. 2025-26 is sealed. Regular season and playoffs are reported separately (playoff OT is 5v5 and continuous; no shootout).

**Concurrency.** Lanes E3 and B5 edit engine and block files; you write only under `docs/tests/`, `scripts/diag_stage8_step0_*.py` and `results/stage8_step0/` (gitignored).

Deliver `docs/tests/stage8_step0_audit_2026-10-21.md` with, per season and per game type, with counts (label any cell under 100 events UNDERPOWERED):
1. **Goalie pull.** When the trailing team pulls: distribution of time remaining at the first pull by score deficit (1, 2, 3+) and by whether a penalty is on; share of trailing-by-1 games with a pull; re-pulls after a goal against; pulls on a delayed penalty (distinguish from EN); pulls in the final minute of regulation that end the pull. Empty-net goals for and against per game, and per minute of EN time; the EN time per game. How the pbp and shifts identify the goalie off the ice (describe the rule you used, and its failure cases).
2. **Overtime (regular season).** Share of games tied after regulation; OT length distribution; 3v3 attempts, SOG and goals per 60 (the INV-35 hazard target); share of OT games ending in a goal vs a shootout; any penalty-induced 4v3 / 3v3 states and their rates; the home / away split of OT winners.
3. **Shootout.** Rounds per shootout; per-attempt success rate by round and by home / away; the share of shootouts going past round 3; shooter and goalie identity availability in the pbp (is a per-shooter model feasible with the data on hand: count distinct shooters with >= 10 attempts across the training seasons).
4. **In-game goalie changes.** Relief appearances per season, the score state and period at the change, the share of SOG faced by a relief goalie (Lane E2 found 2.4% on fold 2; report the training-season figure), and whether the pulled starter returns.
5. **Rebounds and faceoffs (stage 7).** Share of unblocked attempts within 3 s of a prior attempt by the same team (rebound proxy) by strength state and by the prior attempt's class; the goal rate on those vs others; faceoff counts per game by zone and strength state, and the faceoff-win share's spread across teams.
6. **Gate targets.** Restate the G7 quantities (regulation tie rate, shootout share, EN goals per game) for the training seasons from `data/reference/gate_targets_*.parquet` and confirm your pbp-derived numbers match them within rounding; list any mismatch.
7. **Candidate constructions** (a list, no fit, no preference): for each sub-model, the two or three constructions the data would support and the data limitation that rules any out.

Commit the report and your scripts, push, verify with `git ls-remote origin main`. Measure a 3-minute slice before any long pass over the pbp; file a box request and report PARTIAL if a step projects over 15 minutes.

Message to the PM: under 400 words, leading with the numbers that most constrain the stage-8 spec (tie rate, OT goal vs shootout split, 3v3 goals per 60, EN goals per game, relief share) and any data limitation.
