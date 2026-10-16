# Lane M brief: SM-R1, miss vs on-goal decision (offline only)

Model: Sonnet. Core cap: 4 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L13, L24, L27-L34 and D23-D33.
Spec (binding): `docs/models/miss/experiments.md`, section **SM-R1**. Helpers:
- `src/nhl_sim/eval/responsiveness.py` (`slope_ratio`, D32);
- the block lane's level code (`src/nhl_sim/block/`), whose construction family you reuse through new versioned files;
- stage-4 cell / type definitions (`src/nhl_sim/shot_attribute/`, read only).

Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Lanes B4 (block files) and A6 (shot_attribute and later `sim.py`) run concurrently. Touch neither their files nor `sim.py`.

Steps:
1. Build the level constructions, the parity table with the oracle, and the selection. Commit before fitting S1 / S2.
2. Build the road-only miss rating and the arena factor (`created_at < puck_drop`). Run the fold-1 s-grid selection and commit the table.
3. Fit S0, S1 and S2 (+ seed 2), and run the S2 in-sample check.
4. Run the blind fold-2 grade, bias checks, R, the fold-1 R guard and the decision. Also report the post / crossbar share by season.
5. Report `docs/tests/miss_sm_r1_2026-10-16.md`, plus a results block and ledger row (new model row `miss`, stage 5b) in the same commit. Commit, push, verify.

Message to the PM: under 400 words.
