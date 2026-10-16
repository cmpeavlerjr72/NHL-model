# Lane L2 brief: LC-2 penalty league level (INV-33), SS-R3c decision rule, INV-29 re-measure

Model: Sonnet. Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first.
Spec (binding, do not change it): `docs/models/strength_state/experiments.md`, section **LC-2** (committed 21fe71e), and the SS-R3c section above it. Context: `docs/tests/strength_state_ss_r3c_2026-10-15.md` (incl. its resume commands), `src/nhl_sim/league_level_lc1.py`, `scripts/train_strength_state_v3c.py`, `scripts/run_strength_state_g1_v3c.py`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Concurrency

Lane S3 (SA-R3) runs at the same time and edits `sim.py` (adding a default-off T2 flag) and stage-3 files. Do not edit `sim.py` or any shot_attempt file. Your G1 runner uses its own engine path as SS-R3c did; if you need `sim.py` changes, stop and report. Never overwrite v3/v4 level tables or existing trainers: write `league_level_v5_f{1,2}`, a new module `src/nhl_sim/league_level_lc2.py` (with tests, including the oracle construction giving parity 0 to rounding), and versioned scripts (`_v3d` or `_lc2`).

## Steps (chained)

1. Step 0 of the spec: build every construction and grid point, the per-season parity table (both folds), the fold-1 test diagnostic, and apply the selection rule exactly as written. Write the step-0 table into the report before step 1.
2. Step 1: refit H0''-H3'' (+ H3'' seed 2) with T2, bias checks, fold-2 grade vs H3'' (old level), G1 + decomposition for H3''-LC2 and H2''-LC2, 200 seeds. Measure a 3-minute slice of G1; if a step projects over 15 min, file a box request in `docs/ops/box_queue/` and wait in-turn for its `done_` file (Lane O serves it).
3. Step 2: INV-29 spread ratios, RS-only and all games, with team-bootstrap CIs.
4. Report `docs/tests/strength_state_lc2_2026-10-16.md`; results block under LC-2 in `experiments.md` and a ledger row, same commit. Commit, push, verify with `git ls-remote`.

If a step-1 bias check fails, do not run G1 (the SS-R2/SS-R3 rule): report and stop.

Message to the PM: under 400 words, per the worker rules.
