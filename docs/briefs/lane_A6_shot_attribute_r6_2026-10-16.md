# Lane A6 brief: SL-R6 (stage 4): arena-free shot-quality ratings, L1x fixed-scale quality tilt on L0s

Model: Opus. Why not Sonnet: L1x is a new construction (a fixed-scale tilt along the class log-xG direction on top of a stratified multinomial baseline). On selection it replaces the engine's L0s stand-in. This round is the last one the user granted.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L27-L34 and D28-D33.
Spec (binding): `docs/models/shot_attribute/experiments.md`, section **SL-R6** (and SL-R4, which it inherits). Responsiveness: `src/nhl_sim/eval/responsiveness.py` `slope_ratio` (D32). Context: `docs/tests/shot_attribute_sl_r4_2026-10-16.md`, `sl_r5`, and their code (`src/nhl_sim/shot_attribute/models_s.py`, `scripts/train_shot_attribute_v4.py`, `v5`).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Concurrency.** Lane E is wiring the L0s stand-in into `sim.py` now. Do not edit `sim.py` until Lane E's report commit (`engine_standins`) appears in `git log`. If you reach the closed-loop step before then, wait in-turn (10-min waits), then build on Lane E's code. Lane B4 works on block files; do not touch them.

Steps:
1. Build Qr and Qa. Run step 0 (per-season coefficients) and commit it before step 1.
2. Run the fold-1 s-grid and construction pick, and commit the table.
3. Fit L1x.
4. Run the D28 guard (L1x minus L0s on fold 1), the blind fold-2 grade, bias checks, R (also report the old Q5-Q1) and the decision.
5. If L1x is selected: wire it into the engine behind a flag (flag off bit-identical to HEAD), replacing the L0s stand-in when on, then run the closed loop as SL-R4 states. Run locally if it projects under 45 min, otherwise report it pending.
6. Report `docs/tests/shot_attribute_sl_r6_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

Message to the PM: under 400 words.
