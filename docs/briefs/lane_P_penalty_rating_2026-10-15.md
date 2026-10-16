# Lane P brief: SS-R4 penalty team-rating response (INV-29), plus the replay regression rerun

Model: Sonnet. This is a grid re-tune and a re-run of the existing SS-R3 / G1 pipeline. Core cap: 4. Lane S (Opus) needs the rest. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`. Read the new "Process control" section first. AWS goes through Lane O, until 00:30, and you file the box request before you launch.
**Binding spec:** `docs/models/strength_state/experiments.md` SS-R4, plus D15 above it. Reuse the code from f1e6399 and b513691, including `scripts/run_strength_state_g1_v3.py` and `scripts/diag_strength_state_g1_decomp_v3.py`. Make the most literal interpretation choices and label them. If the spec cannot be run as written, stop and report.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start and around each compute step.
- Stop launching compute at **00:30 EDT**. Commit and push the report by **00:45 EDT**.

## Steps (chained)

0. **Replay regression.** Lane I stopped Lane H's `scripts/diag_strength_state_replay.py --expire-first` run at about 19:00. Re-run the replay check on the current engine, both the default and the `--expire-first` variant. Confirm or refute the SS-R1 reported 99.993% gap-aware and 98.13% strict numbers. Report both.
1. **Diagnosis** per the spec, including the stop condition.
2. **Arms** R0-R2 per the spec. Tune on fold 1 only, with the constraint.
3. **Fold-2 grading and decision rule**, including the bias checks and the closed-loop G1 with decomposition for any arm that reaches condition (d).
4. **Docs and commit.**
   - Write `docs/tests/strength_state_ss_r4_2026-10-15.md`.
   - Append results to the SS-R4 "Results" in experiments.md (your one PM-file exception).
   - Add a ledger row.
   - Stage only your own files by explicit path, then commit, push, and verify with `git ls-remote origin main`.

## Concurrency

Lane S (Opus, `data/processed/shot_attempt/`, engine extensions) and Lane O (AWS) are running. Do not edit engine files Lane S may touch. Version any engine change you need as a new module or flag, and list it in your report. Don't touch the Lane I lines files, nor the DRatings scheduled task.

## Report to PM (under 400 words)

Include:
- the replay regression numbers;
- the diagnosis table (spread ratio by fold and phase, H3'' vs H2'');
- the R1 grid choice;
- the fold-2 decision table, conditions (a)-(d);
- G1 and decomposition, if run;
- interpretation choices;
- PARTIAL items;
- AWS use, incidents and commits.
