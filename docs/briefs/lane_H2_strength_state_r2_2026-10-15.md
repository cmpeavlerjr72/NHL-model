# Lane H2 brief: SS-R2, the penalty hazard with the SS-R1 biases fixed (INV-26)

Model: Opus. **Why Opus:** this is cascade sub-model work, where the bias checks and the target re-construction need the same judgement that caught SS-R1's compensated pass. Core cap: 6. You may NOT spawn sub-agents.
Rules: `CLAUDE.md`, and `docs/ops/worker_rules_2026-10-15.md`. Its AWS bullet applies: Lane O is the operator, and box requests go in `docs/ops/box_queue/`. Lane O stops accepting requests at 23:15.
**Binding spec:** `docs/models/strength_state/experiments.md` SS-R2 and the PM ruling above it (D12 in `ARCHITECTURE_DECISIONS.md`). Read Lane H's SS-R1 report `docs/tests/strength_state_ss_r1_2026-10-15.md` and code (1b3abfe), and reuse them; do not rewrite them. Read LEARNINGS L20 and L21. If the spec cannot be run as written, stop and report.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start and around each compute step.
- Stop launching local compute at **23:30 EDT**. Commit and push the report by **23:50 EDT**.
- Any closed-loop G1 run whose slice projects past 15 min locally goes to Lane O as a box request (SS-R1's took about 17 min), unless it can no longer finish before 23:15.

## Steps (chained)

1. **Change 1 (delayed-penalty state).** Rebuild the hazard and type rows as `_v2`, leaving `_v1` untouched. Write a test that a penalty following a delayed-penalty signal gets the pre-signal state. Report the 'other'-state counts before and after.
2. **Change 2 (in-season league level).** Build the as-of in-season league level, with the `created_at < puck_drop` check. Remove the season dummies. Change 3: extend the rating grid. Tune k, w and the prior strength on fold 1 only, then freeze.
3. **Bake-off.** Fit H0'-H3' and the H3' seed retrain, and grade blind with `scripts/grade_strength_state.py` (extend it, keep it backward-compatible). Apply the decision rule literally.
4. **Bias checks.** Run the pre-registered bias checks: season level overall and by month, and the 'other'-state shortfall. If any fails, report it and do not run the closed loop on that arm.
5. **Closed-loop G1.** For the offline winner, and for the next simpler arm if the winner fails: 200 seeds and the 100- vs 200-seed check. Report regular season, playoffs and overall separately; per-team cells carry n and a label.
6. **Docs.** Write `docs/tests/strength_state_ss_r2_2026-10-15.md`. Append the results to the experiments.md "Results" of SS-R2, which is your one PM-file exception. Update `docs/models/strength_state/{model,features}.md` and add a ledger row (TESTING). Stage your files by explicit path, commit, push, and verify with `git ls-remote origin main`.

## Concurrency

Lane I (lines, network) and Lane O (AWS) are running. Don't touch `data/raw/dratings*`, `data/raw/sbro*`, `data/processed/lines_*` or the Lane O files.

## Report to PM (under 400 words)

Give the bake-off table, the bias-check results, a G1 table (regular season / playoffs / overall) with a literal status per cell, whether the result is clean (no compensation), what is PARTIAL with the resume command, AWS use, incidents and commits.
