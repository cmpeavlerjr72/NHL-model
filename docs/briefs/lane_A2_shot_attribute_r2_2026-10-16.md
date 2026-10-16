# Lane A2 brief: SL-R2 (stage 4): as-of league mix level, arms, closed-loop G3

Model: Opus. Why not Sonnet: a new multinomial level construction with a parity and oracle test, where a stage-4 level error can be compensated by stage 6 later (D23). This needs the judgment to spot that, not just run a script.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Read both first, plus LEARNINGS L27-L31.
Spec (binding, do not change it): `docs/models/shot_attribute/experiments.md`, section **SL-R2** (and SL-R1, which it inherits). Context: D23 in `ARCHITECTURE_DECISIONS.md`; Lane A's report `docs/tests/shot_attribute_sl_r1_2026-10-16.md` and its committed code (trainers, lookup, the `sim.py` `tables["attr"]` option, the G3 runner); `src/nhl_sim/league_level_lc2.py` for the LC-2 discounting form.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Steps (chained)

1. **Step 0** of the spec: build every construction, the parity table with the oracle row, and the selection. Write them into the report and commit before fitting L1m / L3m.
2. **Fit** L0m, L1m, L3m (+ seed 2) with the explicit L24 tuning rule. Reuse SL-R1's code through new versioned files.
3. **Blind grade**, bias checks (fold 2 gates, fold 1 diagnostic), responsiveness, segments, and selection.
4. **Closed loop** for the selected arm and the next simpler eligible arm: G3 plus the G2 re-check, 200 seeds, with stage 1 = H3''-LC2 + T2, stage 3 = A3g-c, and the block-first stub. If a measured 3-minute slice projects over 15 min, file a box request. Lane O3 serves the queue until 17:00 EDT; after that, run locally if the projection is under 45 min, otherwise report it pending.
5. **Report** `docs/tests/shot_attribute_sl_r2_2026-10-16.md`, plus a results block and ledger row in the same commit. Commit, push, verify.

If no arm is eligible after step 3, skip step 4 and report.

Message to the PM: under 400 words.
