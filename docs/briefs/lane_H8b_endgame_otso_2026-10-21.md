# Lane H8b brief: EG-R1 parts B and C, the OT 3v3 level (INV-35) and the shootout (INV-67); then the stage-8 closed loop

Model: Sonnet. Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus L27-L29, D19, D35, D41-D43.
Spec (binding): `docs/models/end_game/experiments.md` **EG-R1 parts B and C and the closed loop**. If it cannot be run as written, stop and report.
Step 0: `docs/tests/stage8_step0_audit_2026-10-21.md` sections 2, 3 and 7; `scripts/diag_stage8_step0_b_ot_so.py`.
Level construction to reuse: the stage-3 as-of levels (`src/nhl_sim/shot_attempt/`, `docs/models/shot_attempt/experiments.md` SA-R2 / SA-R3 and the `league_level_lc1.py` M1 construction), `docs/tests/shot_attempt_sa_r3_2026-10-16.md` for the 3v3 failure (+5.4%). Engine: `src/nhl_sim/engine/sim.py` (`shootout_stub`), `rules.py` (`rs_ot_s`, `shootout`), `defaults.py`, `scripts/run_engine_defaults_v1.py`, `tests/engine/`.
Commit attribution line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`

**sim.py order this afternoon: H8a -> H8b (you) -> B5.** Do all offline work first (steps 1-3) in `src/nhl_sim/end_game/ot_level.py` and `shootout.py`, `scripts/train_end_game_otso_v1.py`, `scripts/grade_end_game_otso_v1.py`. Do not touch `sim.py` or `defaults.py` until a commit with `engine_pull` in its message appears in `git log` (Lane H8a). Then wire on top of it. Your report commit message must contain `engine_otso`; Lane B5 waits for it.

Steps:
1. **Part B offline.** 3v3 attempt rows (OT, regular season) per fold. The level grid (M1 K500, M1 K2000, M2 H30; E reported, not selectable), per-training-season parity on the SA-R2 rule, with the oracle row. Select. Commit the parity table before any fold-2 read. Then the fold-2 parity of the selected level (reported; the gate is the closed-loop G2 cell).
2. **Part C offline.** Shootout attempt rows per fold. S1: the as-of M1 K500 success level and the as-of home-shoots-first share; the rules mechanics as a function with tests (3 rounds, sudden death, alternating, early termination when decided). S2: shooter rating at the D27-form fixed scale, fold-1 s-grid, offline only. Commit the fold-1 table before the fold-2 grade. Blind fold-2: S1 bias checks (per-attempt success within 2 pp, past-round-3 share within 5 pp, winner home share within 5 pp; label UNDERPOWERED), S2 vs S1 per-attempt LL with SE and the shooter R. Commit.
3. Confirm from the code (and add a test) that regular-season OT ends at the first goal, and that 4v3 / 3v4 / 4v4 in OT are served by the regulation cascade with the OT period type. Report what you find; fix nothing in `sim.py` before step 4.
4. **Engine (after `engine_pull`).** Record the fixture from HEAD. Wire the 3v3 level into the served stage-3 table and S1 in place of the shootout stub, behind default-off flags; flag off bit-identical to HEAD; served vs offline within 1e-6; tests. Full suite green.
5. **Stage-8 closed loop** per the spec's closed-loop section: 200 seeds, fold 2, default set + H8a's pull flag + your two flags, oracle goalie. All the tables the spec lists, G7 with PASS / FAIL, G1-G3 re-checks vs Lane E3's loop, G5 / G6 first full read labelled "stage 7 absent". Locally if the slice projects under 15 min; otherwise file a box request, commit and push it, and end your turn with a PARTIAL report naming it.
6. Report `docs/tests/end_game_eg_r1_otso_2026-10-21.md` (plus gate docs); results block under EG-R1 "Results" (parts B, C, closed loop); ledger row. Commit with `engine_otso` in the message, push, verify with `git ls-remote origin main`.

Message to the PM: under 400 words. Lead with: the selected 3v3 level and its fold-2 parity, S1's bias checks, then the closed-loop G7 line (tie rate, shootout share, EN goals per game vs actual, PASS / FAIL each), the G2 3v3 cell, whether G1-G3 moved, and the G5 / G6 first read in one line each.
