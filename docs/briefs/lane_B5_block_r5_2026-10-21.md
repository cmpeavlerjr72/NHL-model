# Lane B5 brief: AS-1 (INV-62, prior floor for the as-of scale) then SB-R5 (INV-64, blocks with the as-of scale)

Model: Opus. Why not Sonnet: AS-1 changes the construction under two incumbents and must prove their judged-season snapshots are bit-identical; SB-R5 ports the two-slope as-of estimator to a binary logistic with a frozen offset and, on selection, replaces an engine stand-in. The two prior block rounds failed on exactly this response subtlety (L35).
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus LEARNINGS L34-L38 and D27-D34, D40-D43.
Specs (binding, in this order): `docs/models/asof_scale/experiments.md` **AS-1**, then `docs/models/block/experiments.md` **SB-R5** (inherits SB-R4, SB-R1). If either cannot be run as written, stop and report; do not improvise.
Templates: `src/nhl_sim/shot_attribute/scale.py` and `tests/test_shot_attribute_asof_scale.py` (Lane A7, two-slope multinomial; read its numerics notes in `docs/tests/shot_attribute_sl_r7_2026-10-21.md` step 1), `src/nhl_sim/goal/scale.py` (one-slope logistic), `scripts/train_shot_attribute_v7.py`.
Block code: `src/nhl_sim/block/{data_v4,models,response}.py`, `scripts/train_block_v4.py`, `scripts/grade_block_v4.py`, `docs/tests/block_sb_r4_2026-10-16.md`, frozen params in `docs/models/block/`. Engine B0 as served: `src/nhl_sim/engine/sim.py` (`block_prob`), `docs/tests/engine_c1s_2026-10-21.md` section on INV-54.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Concurrency.** Lane E3 is switching engine default flags in `sim.py` and `scripts/run_engine_c1s_v1.py` right now; do not touch `sim.py` until a commit with `engine_defaults` in its message appears in `git log`. Lane Z reads pbp data only. Write new versioned files: `src/nhl_sim/block/scale.py`, `scripts/train_block_v5.py`, `scripts/grade_block_v5.py`, `scripts/exp_asof_floor_as1.py`. The AS-1 floored snapshots are versioned siblings (`*_v2_*`); never overwrite `goalie_scale_v1_*` or `sq_scale_v1_*`.

**AWS.** No operator is running. If a measured 3-minute slice projects a step over 15 minutes locally, file the box request, commit and push it, and end your turn with a PARTIAL report naming it; the PM launches an operator and resumes you.

Steps:
1. **AS-1.** Implement the floor in both existing scale modules behind a parameter (f = None reproduces the current snapshots bit-for-bit; prove it with a test). Compute I_ref per instance and fold. Run the f grid for both instances and both folds; write the selection table to `docs/tests/asof_floor_as1_2026-10-21.md`; append the results block under AS-1 "Results" and a ledger row (model `asof_scale`). Commit before step 2. If no f passes, stop after this commit and report.
2. **SB-R5 step 0 and snapshots.** Port the two-slope estimator to the block logistic with the selected floor. Leakage tests. Snapshots for the 8-cell grid per fold under `data/processed/block/`. Step-0 table. Commit.
3. **Parity analogue** and the selection table, committed before any fold-2 prediction. The document must not contain a fold-2 number.
4. In-sample check and the D28-form guard; stop and report if either fails.
5. Blind fold-2 grade of B0' / B1a (must reproduce SB-R4 on the original B0) / B1a-as, the D13 guard on fold 1, the decision.
6. If selected: wait for Lane E3's `engine_defaults` commit, wire B1a-as behind a flag, parity tests (flag off bit-identical; served 1e-6), closed loop as the spec states (locally if under 15 min).
7. Report `docs/tests/block_sb_r5_2026-10-21.md` (clock table, per-season and per-state evidence, UNDERPOWERED labels), results block under SB-R5 "Results", ledger row, same commit. Commit, push, verify with `git ls-remote origin main`.

Message to the PM: under 400 words. Lead with the AS-1 selected f and the bit-identity result, then the SB-R5 decision with the R values.
