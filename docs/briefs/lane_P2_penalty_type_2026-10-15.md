# Lane P2 brief: SS-R5 penalty-type model with team terms (INV-29)

Model: Sonnet. This is a small multinomial bake-off plus a re-run of the existing G1 pipeline. Core cap: 4. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`, including the "Process control" section. AWS goes through Lane O until 00:30.
**Binding spec:** `docs/models/strength_state/experiments.md` SS-R5 and the SS-R4 ruling above it. Read `docs/tests/strength_state_ss_r4_2026-10-15.md`. Reuse code from d01e082, b513691 and f1e6399.
Make the most literal interpretation choices and label them. If the spec cannot be run as written, stop and report.
Commit attribution: use the attribution line your system supplies.

## Clock (hard)

- Run `Get-Date` at the start and around each compute step.
- Stop launching compute at **00:30 EDT**. Commit and push the report by **00:45 EDT**.

## Steps (chained)

1. **Fold-1 replication and stop condition**, as the spec defines them.
2. **Fit T2 and T3.** Tune T3's prior strength on fold 1, then grade T1-T3 on fold 2 using a multinomial log-likelihood with game-block bootstrap SEs. Apply the rule.
3. **Closed-loop G1** for the selected arm, if it is not T1. Run 200 seeds plus the 100-vs-200 check, and report regular season, playoffs and overall separately. Include the D14 decomposition and the closed-loop PP-opportunity spread ratio for both rating quintile sets. Version any engine change as a new module or flag: Lane S (Opus) is editing the engine.
4. **Write it up.**
   - Report: `docs/tests/strength_state_ss_r5_2026-10-15.md`.
   - Append the results to the SS-R5 "Results" section in experiments.md (your one PM-file exception).
   - Add a ledger row.
   - Stage only your own files by explicit path, commit, push, and verify with `git ls-remote origin main`.

## Report to PM (under 400 words)

- the fold-1 replication table and the stop-condition outcome;
- the T1-T3 table with SEs;
- the decision;
- the G1 cells and the decomposition verdict;
- the spread ratios;
- interpretation choices;
- what is PARTIAL;
- incidents and commits.
