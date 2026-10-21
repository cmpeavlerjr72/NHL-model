# Lane H8a brief: EG-R1 part A, goalie pull process and empty-net scoring (INV-66), engine wiring

Model: Opus. Why not Sonnet: this adds a new state process to the engine core (goalie out, return, re-pull, the delayed-penalty rider) that interacts with the stage-1 state machine and the score-effects rule, and it opens the EN team-view states through every downstream stage. A slip here moves G1 and G2 silently.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus `docs/SIM_GUARDRAILS.md`, LEARNINGS L23-L29 and L33, D41-D43.
Spec (binding): `docs/models/end_game/experiments.md` **EG-R1 part A** (and the closed-loop section, which Lane H8b runs). If it cannot be run as written, stop and report.
Step 0 data and code: `docs/tests/stage8_step0_audit_2026-10-21.md` sections 1, 4 and 7; `scripts/diag_stage8_step0_a_pulls.py`, `_common.py`.
Engine: `src/nhl_sim/engine/sim.py`, `src/nhl_sim/engine/defaults.py` (Lane E3, `default_attr`), `src/nhl_sim/engine/rules.py`, `scripts/run_engine_defaults_v1.py`, `docs/tests/engine_defaults_2026-10-21.md`, `tests/engine/`. Stage-1 delayed-penalty state: `src/nhl_sim/strength_state/`, `docs/models/strength_state/experiments.md` SS-R2.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**sim.py order this afternoon: H8a (you) -> H8b -> B5.** You own `sim.py` now. Your report commit message must contain `engine_pull`; Lane H8b waits for it before wiring the OT level and shootout, and Lane B5 waits for H8b. Do not touch block, shot_attribute or goal model files; Lane B5 works there. Lane H8b works offline in `src/nhl_sim/end_game/` on files named `ot_*` and `shootout_*`; you use `src/nhl_sim/end_game/pull.py` and `en.py`.

Steps:
1. Build the pull rows from the audit's detection rule (reuse its code), per fold. Step 0 table (per-season medians by deficit, pulled time per game). Commit before any fit.
2. Fit P1 on the training seasons; build P0's lookup. Fold-1 D13 checks, then the blind fold-2 selection per the spec. Commit the grade before any engine step.
3. EN scoring: inventory which served tables carry EN_FOR / EN_AGAINST (stage 3 A3g-c, stage 4 attr rows 5 / 6, block, miss, goal). Build the as-of M1 K500 EN levels the spec names for whatever is missing (labelled stand-in), with their per-training-season parity. Commit.
4. Engine: record the fixture from HEAD before editing. Add the goalie-out state to GameState (per team), the selected pull arm as a per-second lookup, the return / re-pull / delayed-penalty rules, and the EN states through the cascade. Default-off flag; flag off bit-identical to HEAD on the fixture; served vs offline pull hazard within 1e-6; a test that a delayed-penalty goal is never EN-against; a test that the goalie returns on a tying goal. Full suite green.
5. A 200-seed fold-2 plumbing loop with the pull flag on (everything else default): G7 EN goals per game, the EN table of the spec, and the G1 / G2 / G3 re-checks vs Lane E3's loop. Locally if the slice projects under 15 min (previous loops took about 6 min).
6. Report `docs/tests/end_game_eg_r1_pull_2026-10-21.md`; results block under EG-R1 "Results" (part A), ledger row (model `end_game`). Commit with `engine_pull` in the message, push, verify with `git ls-remote origin main`.

If a step projects over 15 minutes locally, file the box request, commit and push it, and end your turn with a PARTIAL report naming it; the PM launches an operator and resumes you.

Message to the PM: under 400 words. Lead with the selected arm and its bias checks, the fold-2 EN goals per game vs actual (0.34 region) and pulled time per game, whether G1 / G2 / G3 moved, and what was not done.
