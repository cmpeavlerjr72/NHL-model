# Lane A5 brief: SL-R5 (stage 4): booster capacity under the L0s start, closed loop on selection

Model: Opus. Why not Sonnet: if L3d is selected, the engine lookup must serve the new L0s strata and route EN rows around the booster. That is the first stage-4 incumbent wired into the engine, with flag-off bit-identity.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L27-L34.
Spec (binding): `docs/models/shot_attribute/experiments.md`, section **SL-R5** (and its parents). Context: D28, D30; `docs/tests/shot_attribute_sl_r4_2026-10-16.md` (8c0e09b) and its code (`scripts/train_shot_attribute_v4.py`, `src/nhl_sim/shot_attribute/models_s.py`, `grade_shot_attribute.py --round r4`).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
Lane B3 (block model, offline) runs concurrently. Do not touch its files or processes.

Steps:
1. Run the fold-1 grid and the selection table. Commit them before any fold-2 prediction.
2. Run the in-sample check and the D28 guard. Stop if either fails.
3. Run the blind fold-2 grade, bias checks, band and decision.
4. If L3d is selected: wire it into the engine lookup (flag off bit-identical to HEAD), then run the closed loop as written, locally if it projects under 45 min, otherwise report it pending.
5. Report `docs/tests/shot_attribute_sl_r5_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

Message to the PM: under 400 words.
