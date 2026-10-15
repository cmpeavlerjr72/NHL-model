# Lane H3 brief: SS-R3, the season-phase profile (INV-27)

Model: Sonnet. The work is a re-run of the existing SS-R2 pipeline with one added offset, plus the G1 offset wiring. Core cap: 6. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`, including the AWS bullet: Lane O is the operator until 23:15.
**Binding spec:** `docs/models/strength_state/experiments.md` SS-R3, and the D13 ruling above it. Read `docs/tests/strength_state_ss_r2_2026-10-15.md` first. Reuse the Lane H/H2 code (1b3abfe, 9b14319): extend it, don't rewrite it.
**Interpretation choices:** make the most literal one, label it in the report and keep going. If the spec cannot be run as written, stop and report.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start and around each compute step.
- Stop launching compute at **23:30 EDT**. Commit and push the report by **23:50 EDT**.
- Mark anything unfinished PARTIAL, with the resume command.

## Steps (chained)

1. Build the profile (training seasons only, per fold) and the de-seasonalised level, written as `_v3` tables; leave `_v2` untouched. Tune k on fold 1 only.
2. Fit H0''-H3'' plus the H3'' seed retrain. Grade blind with `scripts/grade_strength_state.py`. Apply the decision rule and the twin-preference rule literally.
3. Run the bias checks on fold 2 (these gate) and on fold 1 (diagnostic).
4. If an arm passes:
   - build the engine offset lookup and its 0.5% parity unit test;
   - run closed-loop G1 for the selected arm and for the next simpler arm that passes (200 seeds, plus the 100-vs-200 check);
   - report G1 for the regular season, the playoffs and overall.

   If no arm passes, skip G1 and report.
5. Write and commit:
   - write `docs/tests/strength_state_ss_r3_2026-10-15.md`;
   - append results under the SS-R3 "Results" heading in experiments.md (your one PM-file exception);
   - update `features.md` and add a ledger row (TESTING);
   - stage only your own files by explicit path. Lane I has uncommitted files in the tree; don't touch them;
   - commit, push, and verify with `git ls-remote origin main`.

## Report to PM (under 400 words)

Include:
- the bake-off table, with the SS-R2 twins;
- the bias checks, fold 2 and fold 1;
- the G1 table with a literal status per cell, or NOT RUN;
- the interpretation choices you made;
- anything PARTIAL;
- AWS use, incidents and commits.
