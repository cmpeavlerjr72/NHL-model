# Lane E brief: wire the D32 stand-ins (block B0, stage-4 L0s) into the engine; plumbing closed loop

Model: Opus. Why not Sonnet: this edits the engine core in the new Fenwick order (block, then attributes), with flag-off bit-identity, and it must keep stand-in output from leaking into any fit.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus D23, D24, D26-D32.
Context: Lane A3's engine changes (era flag, `tables["attr"]`, `scripts/run_shot_attribute_g3_v2.py`; `docs/tests/shot_attribute_sl_r3_2026-10-16.md`); Lane A4's L0s (`src/nhl_sim/shot_attribute/models_s.py`, `docs/tests/shot_attribute_sl_r4_2026-10-16.md`); Lane B's B0 and M1 K500 level (`src/nhl_sim/block/`, `docs/tests/block_sb_r1_2026-10-16.md`).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
Lane R (responsiveness helper) runs concurrently and does not touch `sim.py`.

Steps:
1. Replace the empirical block-first stub with block B0: the M1 K500 as-of level by strength group x period type. Add the stage-4 L0s lookup, with EN served the baseline. Both sit behind default-off flags and are labelled STAND-IN in the table metadata and in any gate output header.
2. Tests:
   - flag-off output is bit-identical to HEAD on the existing fixture cases;
   - flag-on, the served probabilities match the offline B0 / L0s predictions to within 1e-6;
   - a test asserting that the sim-output schema carries a `stand_in` marker.
3. Plumbing closed loop, 200 seeds: stage 1 = H3''-LC2 + T2, stage 3 = A3g-c, block B0, stage 4 L0s, goal stub xG_ref.
   - Report G2 (all cells; 4v4 / 3v3 listed per INV-42 / INV-35) and G3 by strength state, plus blocked and unblocked attempts per 60 by strength state vs actual.
   - Label everything STAND-IN / plumbing. Nothing gates.
   - Run locally if it projects under 45 min, otherwise report it pending.
4. Report `docs/tests/engine_standins_2026-10-16.md`. Commit, push, verify.

Message to the PM: under 300 words.
