# Lane S brief: stage 3 shot-attempt generation, SA-R1 (INV-30)

Model: Opus. **Why Opus:** this is a new cascade sub-model. It needs an exact shared-latent likelihood (A4), and its score-state features are fed from the engine in the closed loop, the failure mode behind L3. That combination needs the diagnosis judgement that caught SS-R1's compensated pass.
Core cap: 6. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`. The AWS bullet applies: Lane O is the operator, so file the box request BEFORE you launch any run whose slice projects past 15 min (D15 process note).
**Binding spec:** `docs/models/shot_attempt/experiments.md` SA-R1, committed before this brief. Do not change it. If it cannot be run as written, stop at that step and report. Make literal interpretation choices and label them.
Read first: LEARNINGS L1-L3, L13, L15, L20-L24; `docs/models/strength_state/` (the incumbent and how it was graded); and the code from Lanes H-H4 (1b3abfe, 9b14319, f1e6399, b513691). Reuse the code; do not rewrite it.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start and around every compute step.
- Stop launching compute at **00:45 EDT**. Commit and push the report by **01:00 EDT**.
- Anything unfinished is marked PARTIAL, with the exact resume command.

## Steps (chained)

1. **Tables.** Build into `data/processed/shot_attempt/` (versioned):
   - the attempt rows;
   - the level/profile offsets;
   - the as-of team ratings, with the writer leak check;
   - the arena factor.

   Write `docs/models/shot_attempt/features.md`. Add tests: one that fails on an unmapped attempt event type, and one for the L20 delayed-penalty state.
2. **Bake-off.** Do the following:
   - tune on fold 1 and freeze, including the per-grid-cell fold-1 spread ratio;
   - fit A0-A5 plus the A3 seed retrain;
   - grade blind with `scripts/grade_shot_attempt.py`;
   - run the bias checks (fold 2 gating, fold 1 diagnostic) and the responsiveness band;
   - apply the decision rule literally.
3. **Closed loop.** Wire the selected arm and the next simpler eligible arm into the engine, alongside the stage-1 incumbent and the labelled goal stub. Add a parity unit test (offline rate vs engine lookup, within 0.5%). Then run G2 as specified, including the decomposition and the closed-loop responsiveness.
4. **Docs.** Write:
   - `docs/tests/shot_attempt_sa_r1_2026-10-15.md`;
   - the results, appended under "Results" in the experiments file (your one PM-file exception);
   - `docs/models/shot_attempt/model.md`;
   - a ledger row (TESTING).

   Stage only your files by explicit path, commit, push, and verify with `git ls-remote origin main`.

## Concurrency

Lane I (lines, network) and Lane O (AWS) are running. Do not touch `data/raw/dratings*`, `data/raw/sbro*` or `data/processed/lines_*`, nor Lane O's files.

## Report to PM (under 400 words)

Include:
- the bake-off table (arm hashes resolved), with SEs;
- the bias-check and responsiveness results per arm;
- the decision-rule outcome;
- the G2 table (regular season / playoffs / overall) with a literal status per cell;
- the decomposition verdict;
- interpretation choices;
- anything PARTIAL;
- AWS use, incidents and commits;
- your recommended next stage.
