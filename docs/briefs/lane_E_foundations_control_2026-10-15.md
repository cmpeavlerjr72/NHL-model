# Lane E brief: seal, independent finals, gate scaffolding, Control R1 (INV-15, INV-14, INV-17, INV-6)

Model: Sonnet. Core cap: 6. Rules: `docs/ops/worker_rules_2026-10-15.md` and `CLAUDE.md` (read both first). Also read `docs/SIM_GUARDRAILS.md`, `docs/gates.yaml`, `docs/LEARNINGS.md`, `docs/tests/data_audit_nhl_api_2026-10-15.md`, and the pre-registered spec `docs/models/control/experiments.md` R1. That spec is binding and must not be changed. If it cannot be run as written, stop and report.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Reference implementation to mine (read-only): `C:\Users\devuser\CBB-clean-sheet`. Use `src/cbb_sim/data/seal.py`, `scripts/build_gate_reference.py`, `scripts/eval_gates.py`, `scripts/grade_control.py`, and its Control engine under `src/cbb_sim/control/`.

## Steps (chained, in order, all in this one turn)

1. **Seal (INV-15).** `src/nhl_sim/data/seal.py` plus a single loader module (`src/nhl_sim/data/load.py`) that every script uses to read `data/processed` and `data/reference`.
   - 2025-26 rows are refused unless `NHL_UNSEAL_2025=1` is set, and that variable is used by nobody this session.
   - Tests prove that the seal holds for games, events, shifts, player_box, goalie_box and verified finals.
2. **Independent finals (INV-14).**
   - Pull the ESPN NHL scoreboard by date for every date in 2021-22 through 2026-10-14. Cache it in `data/raw/espn_scoreboard/`. Do NOT use or write `data/raw/espn/`; Lane D owns that.
   - Match games to NHL `game_id`s and compare final score and REG/OT/SO.
   - Write `data/reference/verified_finals_v2.parquet` with a `verified_sources` column, and list every mismatch with your diagnosis in `docs/tests/finals_independent_check_2026-10-15.md`.
   - Report the match rate. Leave v1 untouched.
3. **Gate scaffolding (INV-17).**
   - Define a sim output schema: per game x seed, final home/away goals, end state, and optional per-player lines. Document it in `docs/ops/sim_output_schema.md`.
   - `scripts/build_gate_reference.py` writes `data/reference/gate_targets_{season}.parquet`. It covers the G5/G6/G7/G9 quantities computable from finals: the P(total=k) cells, margin and total distribution, score correlation, home win %, regulation-tie / OT / SO rates, and EN goals per game.
   - `scripts/eval_gates.py` reads `docs/gates.yaml` and writes PASS / FAIL / UNDERPOWERED / NEEDS-INSTRUMENTATION per gate for any sim output in that schema. Gates that need event-level output (G1-G4, G8) report NEEDS-INSTRUMENTATION for now.
   - Write offline tests.
4. **Control R1 (INV-6).**
   - Implement the arms A0-A4 exactly as specified in `src/nhl_sim/control/`.
   - Tune on fold 1 only, freeze, and run fold 2.
   - Grade blind with `scripts/grade_control.py`, with arm labels hashed until the table is final.
   - Run `eval_gates.py` on the winner.
   - Write `docs/tests/control_r1_2026-10-15.md`, and append a results block under "Results" in `docs/models/control/experiments.md`. Appending below that line is the one PM-file exception granted to you.
   - Add a ledger row in `docs/models/change_ledger.md` with status TESTING. The PM sets ADOPTED.
   - Measure a 3-minute timing slice before any long run.

## Out of scope

Event-level engine, markets/lines, 2025-26 data, any change to the R1 spec, Lane D's files (`data/raw/espn/`, `data/raw/live/`, `scripts/log_*`, `src/nhl_sim/live/`).

## Report

Keep it under 400 words. Cover:
- seal test results;
- the finals match rate and mismatch count;
- gate scaffolding status;
- the Control R1 table: primary metric per arm with bootstrap intervals and the seed floor, the winner under the decision rule, and its G5/G6/G7 gate statuses;
- anything NOT run;
- commit hashes.
