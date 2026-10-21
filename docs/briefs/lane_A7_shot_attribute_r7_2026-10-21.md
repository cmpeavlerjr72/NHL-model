# Lane A7 brief: SL-R7 (stage 4): L1x-ot0 with the as-of response scale on Qa (INV-59)

Model: Opus. Why not Sonnet: the as-of scale must be re-derived for a two-slope multinomial logit over 78 classes with a fixed offset and a daily-shrunk Newton step, with a leakage proof, and on selection it replaces the engine's stand-in. A construction slip here (G-R3's 0/0 on all-zero rating dates, SL-R6's OT double count) costs the user's last granted round.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus LEARNINGS L27-L35 and D28-D40.
Spec (binding): `docs/models/shot_attribute/experiments.md`, section **SL-R7** (inherits SL-R6, SL-R4). If it cannot be run as written, stop and report; do not improvise a variant.
Template to port: `src/nhl_sim/goal/scale.py` (G-R3's as-of scale, `asof_scale`, `_newton`), its test `tests/test_goal_asof_scale.py`, and `docs/tests/goal_g_r3_2026-10-16.md` (read its step 1 notes: the all-zero-rating carry-forward fix, the created_at rule).
Stage-4 code: `src/nhl_sim/shot_attribute/models_x.py` (L1x, `Fitter`, `zero_ot_score`, `predict_l1x`), `scripts/train_shot_attribute_v6.py`, `scripts/grade_shot_attribute.py --round r6`, `docs/tests/shot_attribute_sl_r6_2026-10-16.md` and its frozen params `docs/models/shot_attribute/sl_r6_d35_frozen_params.json`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Concurrency.** Lane E2 (INV-60) is editing `src/nhl_sim/engine/sim.py` and `scripts/run_engine_standins_*.py` now. Do not touch `sim.py`, the engine tests, or any goal / block / miss file until Lane E2's report commit (`engine_c1s` in the message) appears in `git log`. Steps 0-4 need none of them. Write new versioned files only: `train_shot_attribute_v7.py`, `grade_shot_attribute.py --round r7`, `src/nhl_sim/shot_attribute/scale.py`.

**Compute.** The daily snapshot over all Fenwick attempts (about 2.5x G-R3's SOG rows, 2 parameters, 78 classes) is the only step that may run long. Measure a 3-minute slice on the first cell; if the 8-cell grid projects over 15 minutes locally, file a box request per the rules (Lane O4 serves it) and keep working on what does not depend on it.

Steps:
1. Build `scale.py`: the two-slope as-of estimator with the frozen offset (log L0s levelled + the SL-R6 L1x-ot0 non-rating terms of the fold), the leakage tests, then the snapshots for the 8-cell grid, per fold. Commit the snapshots (parquet under `data/processed/shot_attribute/`) and the tests before anything is graded.
2. Step 0 table (training dates only) and the parity analogue table with the selection. Commit before any fold-2 prediction. The document must not contain a fold-2 number.
3. Fit nothing new: L1x-as is L0s + the frozen terms + the selected cell's s_t on Qa. Run the in-sample stratum check and the D28 guard; stop and report if either fails.
4. Blind fold-2 grade of L0s / L1x-ot0 (must reproduce SL-R6) / L1x-as: LL per game with SE, every bias check, ES R for / against with CI (also the old Q5-Q1), the D13 guard on fold 1, the decision.
5. If L1x-as is selected: wait for Lane E2's commit, then wire L1x-as behind a flag (flag off bit-identical; the served per-date s_t matches the offline prediction to 1e-6) and run the closed loop as SL-R4 states. Locally if it projects under 15 minutes, otherwise a box request.
6. Report `docs/tests/shot_attribute_sl_r7_2026-10-21.md` (clock table, every step's numbers, per-season and per-strength evidence, UNDERPOWERED labels), plus a results block under SL-R7 "Results" and a ledger row, in the same commit. Commit, push, verify with `git ls-remote origin main`.

Message to the PM: under 400 words.
