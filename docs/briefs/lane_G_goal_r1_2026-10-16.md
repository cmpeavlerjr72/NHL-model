# Lane G brief: G-R1, goal given shot on goal (stage 6), offline bake-off

Model: Opus. Why not Sonnet: stage 6 is where a stage-4 location bias would be compensated (D23). It needs the conversion level, a rating-trend test (L35) and the goalie-talent prior, all designed so that no compensating pair passes.
Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L1-L35 (at least L16, L24, L27-L35) and D8, D23-D34.
Spec (binding): `docs/models/goal/experiments.md`, section **G-R1**. Helpers:
- `src/nhl_sim/eval/responsiveness.py` (`slope_ratio`);
- the level-construction code from the block lane (`src/nhl_sim/block/`, `data_v4.py`);
- stage-4 cell / type definitions and the arena distance factor (`src/nhl_sim/shot_attribute/`, read only).

Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Lanes A6 (shot_attribute files, later `sim.py`) and M (miss files) run concurrently. Touch neither their files nor `sim.py`. Write new versioned files only.

Steps:
1. Build the level constructions, the parity table with the oracle, and the selection. Commit.
2. Run step 0, the per-season rating coefficients and trend z. Commit before fitting any arm.
3. Build the ratings (`created_at < puck_drop`), run the fold-1 (b, w, s) selection, and commit the table.
4. Fit C0, C1 and C2 (+ seed 2), and run the C2 in-sample check.
5. Run the blind fold-2 grade, bias checks, R, the fold-1 guard and the decision. Also report the G4 cell grid and per-goalie residuals (n >= 500).
6. Report `docs/tests/goal_g_r1_2026-10-16.md`, plus a results block and ledger row (new model row `goal`, stage 6) in the same commit. Commit, push, verify.

If a step projects over 45 minutes locally, report it pending instead.

Message to the PM: under 400 words.
