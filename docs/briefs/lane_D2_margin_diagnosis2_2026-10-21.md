# Lane D2 brief: INV-78, second-pass diagnosis of the 55:00 margin compression

Model: Opus. Why not Sonnet: the first-pass attribution (a Markov chain over margin states) predicted shares that the wired repairs did not realise (goal 53% -> 26%, block 22% -> 10%); finding why needs the chain's independence assumptions checked against the loop's within-game dependence, and a fold-1 read to separate a one-season deviation from a model defect. A wrong call here sends the next round at the wrong stage again.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus `docs/SIM_GUARDRAILS.md`, L23, L27, L39, D46, D48, D53, D54.
Context: `docs/tests/margin_diagnosis_inv71_2026-10-21.md` (first pass; its scripts `scripts/diag_margin_inv71_{sim,grade,chain,markov}_v1.py`), `docs/tests/engine_defaults_g5b_2026-10-21.md` (Lane E4; `scripts/run_engine_defaults_v2.py`), `docs/tests/goal_g_r4_2026-10-21.md` section 7, `src/nhl_sim/engine/defaults.py` (the default set; fold-1 tables exist for every incumbent, check each builder's fold argument), `docs/gates.yaml` G5b (now 2.1 pp).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Scope.** Diagnosis only. No fix, no tuning, no change to any model table or to `sim.py` / `defaults.py` (write a versioned diagnostic runner if you need instrumentation). No other lane is running. 2025-26 stays sealed. Clock: the PM session closes at 17:00; if your work is not done by then, finish it anyway and report; the PM reads it next session.

Deliver `docs/tests/margin_diagnosis_inv78_2026-10-21.md`:
1. **Fold-1 G5b.** The default set built from the fold-1 tables (train through 2022-23) run on 2023-24, 200 seeds, pull off; the same 55:00 read as Lane E4's (tie share, |margin| cells, real with goalie-out goals removed), at 20:00, 40:00 and 55:00. State whether the fold-1 gap is of the same size and time profile as fold 2's (+0.004 / +0.030 / +0.034). If fold 1 is inside 2 SE, say so plainly: the fold-2 gap is then partly a one-season deviation (L23) and the gate is at its noise floor.
2. **Period-2 origin.** On both folds, goals per 60 by (score state before the event x period) sim vs actual, and the stage-1 quantities by score state x period (penalties drawn per 60, PP time) sim vs actual; locate which period x state cells carry the tie excess and which stage's quantity moves first.
3. **Chain vs loop.** Re-run the first pass's Markov attribution on Lane E4's two loops and compare the predicted vs realised tie change for the goal and block repairs; state which independence assumption fails (e.g. the chain treats transitions as time-homogeneous within a period, or ignores strength-state persistence after a goal).
4. **Conclusion.** The share of the fold-2 55:00 gap that is (a) season deviation, (b) a located model defect by stage, (c) unattributed; and the pre-registration, if any, the located defect needs. Label every underpowered cell.

Measure a 3-minute slice before the fold-1 loop (about 6-7 min expected). Commit the report and scripts, push, verify with `git ls-remote origin main`.

Message to the PM: under 400 words, leading with the fold-1 G5b line and the (a) / (b) / (c) split.
