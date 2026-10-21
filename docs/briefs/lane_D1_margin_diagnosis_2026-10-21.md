# Lane D1 brief: INV-71, diagnose the regulation margin compression (compensating bias upstream of stage 8)

Model: Opus. Why not Sonnet: this is a subtle compensating-bias diagnosis across four sub-models (CBB L23 / L27 class). The pull-off engine matched the actual regulation-tie rate only because the real 6-on-5 tying goals were missing; the question is which sub-model compresses margins and by how much, with evidence that separates score effects, team spread, goalie spread and period structure. A wrong attribution sends the next round at the wrong stage.
Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus `docs/SIM_GUARDRAILS.md` (core principle and the compensating-bias inventories it cites), LEARNINGS L23-L29, D32, D33, D41-D46.
Context: `docs/tests/end_game_eg_r1_pull_2026-10-21.md` (the closed-loop section), `docs/tests/engine_defaults_2026-10-21.md` and its G5-G7 doc, `docs/tests/gates_g5g7_engine_defaults_2026-10-21.md`, `scripts/run_engine_defaults_v1.py`, `src/nhl_sim/engine/sim.py` (what the output records: attempts by score bucket, goals by state), `docs/ops/sim_output_schema.md`, `scripts/eval_gates.py`, `data/reference/gate_targets_*.parquet`, the stage-3 spec (`docs/models/shot_attempt/experiments.md`, score-effects features and the D33 over-response watch item).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Scope.** Diagnosis only. No fix, no tuning, no change to any model table. Name the responsible sub-model(s) with the share of the compression each explains, and state the pre-registration each needs. Fold 2 (2024-25) sim output and actuals are in scope (this is a closed-loop gate read, already made); 2025-26 stays sealed.

**Concurrency.** Lane H8b owns `sim.py` and `defaults.py` until its `engine_otso` commit; Lane B5 follows it. You do not edit either. If you need engine instrumentation (score at 55:00, goal times), write a versioned diagnostic runner (`scripts/diag_margin_inv71_*.py`) that drives `simulate` with its own recording hook, or derive what you can from the existing recorded output; say which you did. Lane B5 works in block files; do not touch them.

Deliver `docs/tests/margin_diagnosis_inv71_2026-10-21.md`, fold 2 regular season, pull flag off (the default set; 200 seeds, re-use Lane E3's loop output where it suffices), with actuals from verified finals and pbp:
1. **Margin and score state at 55:00** (before any pull effect): sim vs actual distribution of |margin| (0, 1, 2, 3+) and of the home score state, and the same at 40:00 and 20:00, so the compression is located in time. Then at 60:00 with the actual compared both with and without the EN / 6-on-5 goals removed (so the engine's regulation-without-pulls is compared like with like).
2. **Score effects** (L23 / L27): goals per 60 and attempts per 60 by pre-event score state (trailing 2+, trailing 1, tied, leading 1, leading 2+) and by period, sim vs actual, 5v5 and all states. Over-strong trailing-team scoring compresses margins; state the sign and size.
3. **Team spread:** per-team sim mean margin vs actual mean margin (fold 2, by team), the slope and R (D32 helper) of sim on actual, and the SD of team mean margins sim vs actual. A flat slope means the ratings' effect on margin is under-carried; say at which stage (attempts, quality, finishing, goalie).
4. **Goalie spread:** per-goalie sim save % vs actual (Lane E2 reported correlation 0.71 and R 0.975); the SD of goals against per game by starter, sim vs actual.
5. **Period structure:** goals per period sim vs actual, and the first-goal time distribution if derivable.
6. **G5 / G6 decomposition:** the total-goals distribution P(total = k), the margin distribution, home win %, and the score correlation, sim vs actual, each with the part of the gap that each candidate in 2-4 explains (a counterfactual where possible: e.g. re-weighting the sim by team to the actual team-spread, labelled as a diagnostic, never as a fix).
7. **Conclusion:** the responsible sub-model(s), the share of the tie-rate gap (0.2376 vs 0.2082 with pulls; 0.2045 vs the actual pre-pull tie rate you compute in item 1) each explains, and the pre-registration each needs. Label every underpowered cell.

Measure a 3-minute slice before any new sim run; file a box request and report PARTIAL if a step projects over 15 minutes. Commit the report and scripts, push, verify with `git ls-remote origin main`.

Message to the PM: under 400 words, leading with the located cause(s) and their shares, then the one or two numbers that prove each.
