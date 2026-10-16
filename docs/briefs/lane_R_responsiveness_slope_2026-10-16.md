# Lane R brief: D32 slope-based responsiveness gate; shared helper; re-check stage-1 and stage-3 incumbents

Model: Sonnet. Core cap: 4 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus D18, D20 and D32 in `ARCHITECTURE_DECISIONS.md`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
Lane E (engine stand-ins) edits `sim.py` concurrently. Do not edit `sim.py`.

Steps:
1. Write `src/nhl_sim/eval/responsiveness.py` (or the closest existing eval module, if one already exists) with:
   - `slope_ratio(pred, actual, rating, weights, game_ids, n_buckets=10, n_boot=1000, seed=0)`, returning R = 1/b, the bootstrap CI, an UNDERPOWERED flag (CI wider than [0.8, 1.2]), and the old Q5-Q1 ratio for reporting.
   - Unit tests: a calibrated synthetic case gives R about 1; an over-responding case gives R > 1; the bootstrap resamples games, not rows.
2. Re-check the incumbents, from existing outputs where they exist (no new sim run unless the outputs lack per-row predictions; then re-run the existing runner with the same seeds):
   - **Stage 1 H3''-LC2 + T2:** the closed-loop PP-opportunities-conferred response (own taken-rating, opponent drawn-rating), RS and all games (L2's `run_strength_state_g1_lc2.py` outputs).
   - **Stage 3 A3g-c:** closed-loop 5v5 attempts own / opp response (Lane S4's G2 outputs, `docs/tests/shot_attempt_g2_inv36_2026-10-16.md`).
3. Report R with CI for every cell. Say plainly which cells pass and which fail. The PM rules; do not change any status yourself.

Report `docs/tests/responsiveness_slope_recheck_2026-10-16.md`. Commit, push, verify. Message to the PM: under 300 words.
