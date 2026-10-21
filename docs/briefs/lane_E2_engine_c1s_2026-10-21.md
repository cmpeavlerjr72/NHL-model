# Lane E2 brief: INV-60, wire the goal model C1s, the miss stand-in S0t, the L0s level (INV-57) and the B0 groups (INV-54) into the engine; plumbing closed loop

Model: Opus. Why not Sonnet: this splits the engine's single "unblocked attempt -> xG_ref goal draw" into miss (stage 5b) -> SOG -> goal given SOG (stage 6, shooter team x goalie, with a per-date as-of goalie scale), keeps flag-off bit-identity, and keeps stand-in output out of every fit. It is the first time the engine carries a selected goal model and a per-game starting goalie.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus D23, D24, D26-D40 and L33.
Context (read before editing):
- Engine and its stand-ins: `src/nhl_sim/engine/sim.py` (the docstring, `_attribute_draw`, `block_prob`, `class_cdf`), `docs/tests/engine_standins_2026-10-16.md`, `scripts/run_engine_standins_v1.py`, `scripts/diag_engine_standin_parity_fixture.py`, `tests/engine/`.
- Goal C1s (CONFIRMED-INCUMBENT provisional, D40): `src/nhl_sim/goal/{data,models,scale}.py`, `scripts/train_goal_v3.py`, `scripts/grade_goal_v3.py`, `docs/tests/goal_g_r3_2026-10-16.md`, `docs/models/goal/experiments.md` G-R1..G-R3, snapshots `data/processed/goal/goalie_scale_v1_f{1,2}.parquet`. The as-of goalie scale is H90 P2000; team finishing at its fixed scale; level M1 K500.
- Miss S0t (stand-in, D37): `src/nhl_sim/miss/tier.py`, `scripts/train_miss_v2.py`, `docs/tests/miss_sm_r2_2026-10-16.md` (level M2_H30 by tier, S0t flat).
- L0s on M1 K500: Lane A6's D35 re-run, `docs/models/shot_attribute/sl_r6_d35_frozen_params.json`, `docs/tests/shot_attribute_sl_r6_2026-10-16.md`.
- B0 4v4 / 3v3: INV-54 on the board, `src/nhl_sim/block/`, `docs/tests/block_sb_r1_2026-10-16.md`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Concurrency.** Lane A7 (SL-R7) works offline in `src/nhl_sim/shot_attribute/` and `scripts/train_shot_attribute_v7.py`; it does not touch `sim.py` until your report commit lands. Your report commit message must contain `engine_c1s`. Do not touch Lane A7's files. Lane O4 is the AWS operator.

**Principles that bind the wiring.**
- One engine; every new path sits behind a default-off flag; flag-off output is bit-identical to HEAD on the existing fixture cases (record the fixture with the pre-change engine first, as Lane E did).
- The goal model is served from lookup tables keyed by (game, shooting team, strength group, class / tier) with the per-date goalie scale and as-of goalie / team ratings baked in at table-build time; no model call in the sim loop.
- The starting goalie per game is the box-score starter, so the closed loop is labelled **oracle goalie** (D8) in every output header and in the run meta. Goalie changes within a game are out of scope (stage 8); say so in the report.
- Stand-ins stay labelled STAND-IN (block B0, stage-4 L0s, miss S0t). The goal model is labelled `goal: C1s (provisional, D40)`, not stand-in. Any output that carries a stand-in still carries the `stand_in` marker.
- No tuning anywhere. If served and offline numbers disagree beyond 1e-6, find the construction difference; do not adjust.

Steps:
1. **INV-57.** Move the L0s stand-in level from E to M1 K500 (the SL-R6 D35 tables). Flag label updated. Served vs offline L0s (M1 K500) within 1e-6.
2. **INV-54.** Give B0 its own level groups for 4v4 and 3v3 (a construction fix: the M1 K500 as-of level computed on those rows, same code as the ES / PP / PK groups; no coefficient tuning). Report the before / after served block rate by state vs actual on fold 2.
3. **Miss S0t.** After the attribute draw, an unblocked attempt is a miss with the S0t probability (tier-specific M2_H30 as-of level, D37) or a shot on goal. Label STAND-IN. Served vs offline within 1e-6.
4. **Goal C1s.** A shot on goal is a goal with the C1s probability: level M1 K500 + team finishing (fixed scale) + s_t(goalie, H90 P2000) x standardised as-of goalie rating, for the game's starting goalie, keyed by the engine's class / tier and strength group. Replace the xG_ref goal stub when the flag is on. Served vs offline C1s prediction within 1e-6 on the fold-2 rows. The engine records SOG, goals and summed C1s probability by (team, team-view state) and per goalie.
5. **Tests:** flag-off bit-identity; served-vs-offline for each of the four components; a test that the seal still refuses 2025-26; a test that the output carries the `oracle_goalie` and `stand_in` markers; the full suite green.
6. **Plumbing closed loop, 200 seeds, fold 2 (2024-25):** stage 1 H3''-LC2 + T2, stage 3 A3g-c, block B0 (with INV-54), stage 4 L0s (M1 K500), miss S0t, goal C1s, oracle goalie. Report G2, G3 by strength state, and the new stage-5/6 quantities vs actual by strength state: SOG per 60, miss share, save %, goals per 60; per-goalie save % for goalies with >= 500 fold-2 SOG (others pooled, labelled UNDERPOWERED); a goalie-decile responsiveness R on sim save % vs actual (D32 helper). Also run `scripts/eval_gates.py` on the game-level output and report G5-G7 labelled **plumbing, stages 7-8 absent** (no rebounds model, no OT / shootout model: every row ends at regulation or is listed; do not interpret these as gate results). Nothing in this loop gates. Measure a 3-minute slice first; the previous loop took about 9 minutes locally for 200 seeds, so run locally unless the slice projects over 15 minutes, in which case file a box request.
7. Report `docs/tests/engine_c1s_2026-10-21.md` (clock table; each component's parity numbers; the block-rate before / after; the closed-loop tables; what is NOT wired). Ledger rows for goal (C1s wired) and shot_attribute / block / miss (stand-in changes). Commit with `engine_c1s` in the message, push, verify with `git ls-remote origin main`.

Message to the PM: under 400 words. Lead with: flag-off bit-identical (yes / no), the four served-vs-offline maxima, the fold-2 save % and goals per 60 vs actual overall and by strength state, the goalie R, and what was not done.
