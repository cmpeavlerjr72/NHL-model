# Lane H brief: P2 kickoff: GameState core + strength-state/penalty bake-off SS-R1 (INV-22)

Model: Opus (the one Opus engine-core worker for 2026-10-15). Core cap: 6. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`. Read both first. Then read `docs/SIM_GUARDRAILS.md`, `docs/gates.yaml`, `docs/LEARNINGS.md` (L1, L3, L5, L13, L14 especially), `docs/tests/data_audit_nhl_api_2026-10-15.md`, `docs/ops/sim_output_schema.md`, and `docs/models/control/` (the reference implementation of as-of ratings and blind grading in this repo).
**Binding spec:** `docs/models/strength_state/experiments.md` SS-R1, committed by the PM before this brief. Do not change it. If it cannot be run as written, stop at that step and report why. Do not improvise a substitute.
Reference to mine (read-only): `C:\Users\devuser\CBB-clean-sheet` (`src/cbb_sim/` engine state and RNG streams, closed-loop gate pattern) and `C:\Users\devuser\cfb-props-sim` docs (postmortems, guardrails).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Clock (hard)

- Run `Get-Date` at the start and around every compute step.
- Stop launching new compute at **23:30 EDT**. Commit and push the report by **23:50 EDT**.
- Unfinished steps are marked PARTIAL with the exact resume command.
- Measure a 3-minute slice before any run expected to take more than 10 minutes.

## Steps (chained, in order, all in this one turn)

1. **Engine core.** Write `src/nhl_sim/engine/`:
   - `GameState` (NumPy arrays over games x seeds), clock, period/OT structure, rule-era flags;
   - the penalty-box queue with every rulebook mechanic listed in the spec;
   - an RNG stream factory seeded on (seed, game_id, family).
   - The sim loop is vectorised and uses lookup tables. It makes no live model calls.
   - Write unit tests for every rule with hand-built sequences: `tests/engine/`, offline, fast.
2. **Mechanics replay check.** Replay the real penalty and goal sequences of at least 300 fold-1 games through the mechanics and compare the strength-state timeline second by second with the pbp `situation_code` timeline.
   - Pass is >= 99% agreement.
   - List and diagnose the disagreements: data error vs rule gap. Fix rule gaps in the engine, never by special-casing games.
3. **Tables.** Build:
   - the hazard-row and type-row tables;
   - the as-of team penalty ratings, with the `created_at < puck_drop` check enforced in the writer;
   - the `pen_type`/`pen_desc` mapping test that fails on unmapped combinations.
   - Write them to `data/processed/strength_state/` as versioned files. Document the features in `docs/models/strength_state/features.md`.
4. **Bake-off.** Do the following:
   - Fit H0-H3 and T0-T1 per the spec, tuning on fold 1 only and then freezing.
   - Retrain H3 under a second seed.
   - Grade fold 2 blind with `scripts/grade_strength_state.py`, with the arm labels hashed until the table is final.
   - Report the bootstrap SEs and apply the decision rule literally.
5. **Closed-loop G1.** Do the following:
   - Wire the offline winner and the stub goals into the engine and run fold 2 at >= 200 seeds, with the 100-vs-200 stability check.
   - Extend `build_gate_reference.py` / `eval_gates.py` for G1 if needed.
   - Label stub-driven cells STUB-DEPENDENT.
   - Write sim output per `docs/ops/sim_output_schema.md`, extending it for strength-state TOI. Put the extension in your report; the schema doc is yours to edit.
   - If the winner fails G1 and a simpler arm passes, run that arm too and apply the spec rule.
6. **Docs and commit.** Do the following:
   - Write the full report: `docs/tests/strength_state_ss_r1_2026-10-15.md`. Include the multi-level evidence the spec lists (responsiveness quintiles, per team, per strength state) and timings.
   - Append the results under "Results" in `docs/models/strength_state/experiments.md`. That append is your one PM-file exception.
   - Write `docs/models/strength_state/model.md` per `docs/models/DOCUMENTATION_STANDARD.md`.
   - Add a ledger row in `docs/models/change_ledger.md` with status TESTING. The PM sets the final status.
   - Stage only your files by explicit path, commit, push, and verify with `git ls-remote origin main`.

## Concurrency

Lane I (Sonnet, lines pulls) runs at the same time. It uses network only, with 2 cores, and writes under `data/raw/dratings*`, `data/raw/sbro*` and `data/processed/lines_*`. Do not touch those paths.

## Report to PM (under 400 words)

Give the result per step with numbers, the bake-off table (arm hashes resolved), the decision-rule outcome, a G1 table with PASS/FAIL/STUB-DEPENDENT per cell, what is PARTIAL with resume commands, any incidents, the commits, and your recommended next step (stage 2 deployment vs stage 3 shot generation ordering).
