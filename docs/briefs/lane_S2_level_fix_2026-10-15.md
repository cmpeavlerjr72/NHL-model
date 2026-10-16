# Lane S2 brief: LC-1 level fix: SA-R2 (stage 3), then SS-R3c (stage 1) (INV-31)

Model: Opus. This continues Lane S in the same agent. **Why Opus:** it is a cross-stage fix of a defect Lane S diagnosed, and it needs Lane S's context. It touches both stage incumbents and the engine.
Core cap: 6 (Lane P2 uses 4 until 00:45; after that you may use 8). You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`, including "Process control". AWS goes through Lane O, until 00:30; file the request before you launch.
**Binding specs:**
- `docs/models/shot_attempt/experiments.md` SA-R2;
- `docs/models/strength_state/experiments.md` SS-R3c;
- D16 in `ARCHITECTURE_DECISIONS.md`.

Make the most literal interpretation choices and label them. If a spec cannot be run as written, stop and report.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

Run `Get-Date` at the start and around each compute step. Stop launching compute at **01:30 EDT**. Commit and push the report by **01:45 EDT**. Anything unfinished is PARTIAL, with the resume command.

## Steps (chained)

1. **LC-1 builder.** Build it once as a shared module used by both stages, with the per-training-season parity test. Version the tables: `_v4` for strength_state, `_v2` for shot_attempt.
2. **SA-R2.** Run the fold-1 diagnostic, the bake-off (incl. A2g and A3g), the bias checks and the responsiveness band, and apply the decision rule. If an arm is eligible, run G2 (+ decomposition + closed-loop responsiveness) on the **current stage-1 incumbent** for the selected arm and the next simpler eligible arm.
3. **SS-R3c.** Lane P2 (SS-R5, penalty type model) is running until 00:45. Do not modify its files. Run SS-R3c with T1 if SS-R5 has not committed a selected type arm by the time you reach this step; otherwise use SS-R5's selected arm and say which you used. Then do bias checks, grading, and G1 regular season / playoffs / overall with the decomposition.
4. **Re-run G2 if needed.** If SS-R3c changes the stage-1 incumbent and SA-R2 ran G2, re-run G2 on the new incumbent for the selected stage-3 arm only (it takes about 6 min).
5. **Docs.** Write:
   - `docs/tests/shot_attempt_sa_r2_2026-10-15.md` and `docs/tests/strength_state_ss_r3c_2026-10-15.md`;
   - the results appends in both experiments files (your PM-file exception);
   - the `model.md`/`features.md` updates;
   - the ledger rows (TESTING).

   Stage by explicit path, commit, push, and verify with `git ls-remote origin main`.

## Report to PM (under 400 words)

- the SA-R2 table, bias checks, responsiveness and decision;
- the G2 cells and verdict;
- the SS-R3c table, bias checks and G1 verdict;
- the step-4 outcome;
- interpretation choices;
- PARTIAL items;
- AWS use, incidents and commits.
