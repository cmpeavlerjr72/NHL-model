# Lane B brief: SB-R1, block-decision bake-off (offline only)

Model: Sonnet. Core cap: 6 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L13, L15, L24, L27-L32.
Spec (binding, do not change it): `docs/models/block/experiments.md`, section **SB-R1**. Context: D23, D24; the level code in `src/nhl_sim/league_level_lc2.py` and Lane A2's mix-level code (see `docs/tests/shot_attribute_sl_r2_2026-10-16.md`); the stage-3 attempt rows and events tables.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Do not edit** `src/nhl_sim/engine/sim.py`, GameState, or any shot_attribute file: Lane A3 is changing them now. Read-only use of their code is fine. Write new versioned files only. If you need the era flag, compute it from the season (era 2 from 2023-24, fixed per D24) in your own code.

Steps:
1. Build the level constructions and the parity table with the oracle row, apply the selection, and commit before fitting B1 / B2.
2. Build the ratings (fold-1 tuning under the explicit L24 rule) and the arena factor, asserting `created_at < puck_drop`.
3. Fit B0, B1 and B2 (+ seed 2), with the B2 in-sample stratum check (stop if it fails).
4. Run the blind grade, bias checks, responsiveness and selection.
5. Report `docs/tests/block_sb_r1_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

No step should come near 15 min. If one projects over 45 min, report it pending instead of running it.

Message to the PM: under 400 words.
