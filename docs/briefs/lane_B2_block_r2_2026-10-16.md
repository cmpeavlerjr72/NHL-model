# Lane B2 brief: SB-R2, calibrated-spread rating shrinkage for the block decision (offline only)

Model: Sonnet. Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first.
Spec (binding): `docs/models/block/experiments.md`, section **SB-R2** (and SB-R1). Context: D27 in `ARCHITECTURE_DECISIONS.md`; `docs/tests/block_sb_r1_2026-10-16.md` (d18a694) and its code (`scripts/train_block_v1.py`, `scripts/grade_block.py`, `src/nhl_sim/block/`).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Lane A4 (stage 4) is editing `sim.py` and shot_attribute files concurrently. Do not touch them or its processes. Write new versioned files only (`train_block_v2.py`, and so on).

Steps:
1. Build the extended rating grid and the fold-1 selection table, apply the D27 rule, and commit the table before any fold-2 fit.
2. Refit B1 and B2 with the selected ratings.
3. Run the blind fold-2 grade, bias checks, responsiveness and decision.
4. Report `docs/tests/block_sb_r2_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

Message to the PM: under 400 words.
