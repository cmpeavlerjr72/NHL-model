# Lane B4 brief: SB-R4, arena-free block ratings at a fixed, spread-tuned scale (offline only)

Model: Sonnet. Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus D29, D32, D33.
Spec (binding): `docs/models/block/experiments.md`, section **SB-R4**. Responsiveness: `src/nhl_sim/eval/responsiveness.py` `slope_ratio` (D32, Lane R, 22d8f59). Context: `docs/tests/block_sb_r3_2026-10-16.md` and code under `src/nhl_sim/block/`, `scripts/train_block_v2.py`, `grade_block_v2.py`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Lane E edits `sim.py`, and Lane A6 works on shot_attribute files. Touch neither. Write new versioned files only (v4).

Steps:
1. Build Rr and Ra. Assert `created_at < puck_drop`.
2. Step 0: per-season coefficients. Commit before step 1.
3. Run the fold-1 s-grid selection per arm, and commit the table.
4. Fit B1r, B1a and B2x.
5. Run the blind fold-2 grade, bias checks, R responsiveness (also report the old Q5-Q1), the fold-1 R guard, and the decision.
6. Report `docs/tests/block_sb_r4_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

Message to the PM: under 400 words.
