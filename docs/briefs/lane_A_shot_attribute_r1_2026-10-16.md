# Lane A brief: SL-R1 (stage 4 kickoff): shot location x type audit, bake-off, closed-loop G3

Model: Opus. Why not Sonnet: step 0 decides the cascade order (the block-coordinate semantics), and the bake-off needs judgment on recording-bias and venue terms where a wrong construction can pass by compensation.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus `docs/LEARNINGS.md` (L13-L15, L21-L29) and `docs/SIM_GUARDRAILS.md` (G2, G3).
Spec (binding, do not change it): `docs/models/shot_attribute/experiments.md`, section **SL-R1**. Context: D18-D20 in `ARCHITECTURE_DECISIONS.md`; the stage-3 report `docs/tests/shot_attempt_sa_r3_2026-10-16.md` and its G2 runner `scripts/run_shot_attempt_g2.py` (its `--stage1 lc2t2` option, Lane S4, `docs/tests/shot_attempt_g2_inv36_2026-10-16.md`); the events table in `data/processed/events`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Steps (chained)

1. **Step 0 audit**, then apply the blocks rule (a)/(b) exactly as written. Write the audit and the rule outcome into the report and commit it BEFORE fitting any arm.
2. **Build.** xG_ref per fold, as-of shot-quality ratings with the fold-1 grid (and the L24 spread table), and the as-of arena factor, all versioned under `data/processed/shot_attribute/`. Assert `created_at < puck_drop`.
3. **Fit.** Arms L0-L3, plus L3 under seed 2; tuning on fold 1 only. New versioned trainer files.
4. **Grade blind** with `scripts/grade_shot_attribute.py`. Then the bias checks (fold 2 gates, fold 1 diagnostic), responsiveness, segments, and selection per the decision rule.
5. **Closed loop.** Run the selected arm plus the next simpler eligible arm in `sim.py` behind a default-off flag. Add a pytest parity test: with the flag off, engine output is bit-identical to the current `sim.py` on a fixed seed set. Then run G3 and the G2 re-check, 200 seeds, with stage 1 = H3''-LC2 + T2 and stage 3 = A3g-c. If a measured 3-minute slice projects over 15 min, file a box request (`docs/ops/box_queue/`; Lane O2 serves it until 17:00 EDT; after that, report the request as pending and stop).
6. **Report** `docs/tests/shot_attribute_sl_r1_2026-10-16.md`, with a clock table, every table, labelled interpretation choices, and a results block under SL-R1 plus a ledger row in the same commit. Commit, push, verify with `git ls-remote`.

If no arm is eligible after step 4, skip step 5 and report; the PM rules.
If step 0 turns up something the spec did not anticipate that makes it unworkable as written (not merely inconvenient), stop after step 1 and report.

Message to the PM: under 400 words.
