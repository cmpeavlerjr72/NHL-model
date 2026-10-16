# Lane H4 brief: closed-loop G1 for the SS-R3 arms (INV-28)

Model: Sonnet. This is engine wiring and a gate run on existing code. Core cap: 6. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md` (AWS bullet: Lane O is the operator until 23:15).
**Binding:**
- the SS-R3 spec (its "Closed-loop G1" section);
- the D14 ruling in `docs/models/strength_state/experiments.md`;
- G1 as Lane H ran it in SS-R1 (`docs/tests/strength_state_ss_r1_2026-10-15.md`, code 1b3abfe).

Reuse the SS-R3 code (f1e6399). Make the most literal interpretation choices and label them. If something cannot be run as written, stop and report.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start and around each compute step.
- Stop launching compute at **23:30 EDT**. Commit and push the report by **23:50 EDT**.
- SS-R1's G1 took about 17 min per arm locally. Measure a 3-minute slice first. If two arms in parallel project past 15 min, and the request can still finish before 23:15, file a box request with Lane O per the worker rules. Otherwise run locally.

## Steps (chained)

1. **Offset lookup.** Build the engine hazard lookup with the per-game level and profile offsets for H3'' and H2''. Add the unit test that this reproduces the offline predicted rate for a sample of at least 200 fold-2 games within 0.5%.
2. **G1 runs.** Run closed-loop G1 for H3'' and H2'' with T1: 200 seeds, plus the 100-vs-200 check. Report regular season, playoffs and overall separately. Per-team cells carry n and a label. Use the same labelled goal stub as SS-R1, and label stub-driven cells STUB-DEPENDENT.
3. **Clean-pass decomposition (D14).** For PP opportunities per team-game, decompose sim minus actual into:
   - (a) the hazard level: predicted events vs actual events in the offline rows;
   - (b) state-visit differences: the sim's time in each strength state vs actual, times the hazard;
   - (c) the coincidental/type mix;
   - (d) the remainder.

   The pass is clean only if no single component exceeds the gate tolerance with an opposite-signed component cancelling it. State the verdict literally: CLEAN / COMPENSATED / FAIL.
4. **Responsiveness.** For H3'' in the closed loop, report simulated vs actual PP opportunities by team taken-rating quintile and by opponent drawn-rating quintile.
5. **Docs and commit.**
   - Write `docs/tests/strength_state_g1_ssr3_2026-10-15.md`.
   - Append the results to the SS-R3 "Results" in experiments.md (your one PM-file exception).
   - Add a ledger row (TESTING).
   - Stage only your own files by explicit path. Lane I has uncommitted files; don't touch them.
   - Commit, push, and verify with `git ls-remote origin main`.

## Report to PM (under 400 words)

Include:
- the parity test result;
- a G1 table per arm (RS / PO / overall) with a literal status per cell;
- the decomposition and the CLEAN / COMPENSATED / FAIL verdict;
- the responsiveness table;
- anything PARTIAL, AWS use, incidents, and the commits.
