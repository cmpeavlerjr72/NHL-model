# Lane A3 brief: SL-R3 (stage 4): baseline-started booster, era flag in GameState, closed loop

Model: Opus. Why not Sonnet: this adds a GameState era flag to the engine core and runs the first closed loop with the new Fenwick cascade order (block-first stub). A wrong plumbing choice there would silently bias every later stage.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L27-L32.
Spec (binding): `docs/models/shot_attribute/experiments.md`, section **SL-R3** (and SL-R1 / SL-R2, which it inherits). Context: D23, D24; `docs/tests/shot_attribute_sl_r2_2026-10-16.md` (9b86012), with its code and the resume commands for `scripts/run_shot_attribute_g3_v2.py`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Steps (chained)

1. **Era flag.** Add a recording-era field to GameState: era 2 from 2023-24 on, fixed per D24 and not fitted. The engine's attribute lookup reads it. Flag-off and parity tests: engine output with the stage-4 option off must stay bit-identical to HEAD.
2. **L0m plumbing closed loop** (not a gate): G3 and the G2 re-check, 200 seeds. Report it fully and label it plumbing.
3. **L3b.** Fit and tune on fold 1, then the in-sample stratum check (stop if it fails), then the blind grade, bias checks, responsiveness and decision.
4. If L3b is selected, run its gate closed loop.
5. **Report** `docs/tests/shot_attribute_sl_r3_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

If a measured 3-minute slice projects over 15 min: Lane O3 serves the box queue until 17:00 EDT; after that, run locally if the projection is under 45 min, otherwise report it pending.

Message to the PM: under 400 words.
