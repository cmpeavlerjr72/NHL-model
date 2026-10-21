# Lane E4 brief: INV-77 default set (B1a-as + 3v3 OT level on) and the pre-registered G5b read (D53)

Model: Sonnet. Core cap: 8 locally. You may NOT spawn sub-agents.
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-21.md`. Read both first, plus D50, D52, D53 and `docs/gates.yaml` (G5b).
Context: `src/nhl_sim/engine/defaults.py` (`default_attr`, `b1aas_attr`, `att_table(games, ot3v3=True)`), `src/nhl_sim/engine/goal_r4_tables.py` (flag `attr["goal"]["sc_game"]`), `scripts/run_engine_defaults_v1.py`, Lane G4's loop runner (`docs/tests/goal_g_r4_loop_2026-10-21.md` names it), Lane B5's `docs/tests/gates_block_b1aas_engine_2026-10-21.md`, Lane D1's G5b grading code (`scripts/diag_margin_inv71_grade_v1.py`), `tests/engine/`.
Commit attribution line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`

You own `sim.py` and `defaults.py`; no other lane is running. Record the fixture from HEAD before any edit.

Steps:
1. **INV-77.** `default_attr` serves B1a-as (replacing B0) and the 3v3 OT level; the pull process and the shootout stay behind their flags; the `stand_in` marker drops block. Explicit-flag paths stay bit-identical to HEAD on the fixture. A test that the default output carries the `block_model` marker and no block stand-in label.
2. **Paired loops, 200 seeds, fold 2, aligned RNG streams:** (a) the new default set (C1s); (b) the new default set + `sc_game` (C1s-sap). Pull and shootout off in both.
3. **Read, for each loop and the difference:** G5b (tie share and |margin| cells at 55:00, regular season, vs actual with goalie-out goals removed; use Lane D1's method), team-standardised goal O/E by score bucket with z, G4 by group, G1 / G2 / G3 vs Lane E3's loop (G2 3v3 should now pass as in Lane H8b's loop), and G7 reported (pull and shootout off, so it is not a gate read). State PASS / FAIL per G5b cell per loop.
4. Report `docs/tests/engine_defaults_g5b_2026-10-21.md`; ledger rows (block and shot_attempt served by default; goal: closed-loop result for C1s-sap). Commit with `engine_defaults_v2` in the message, push, verify with `git ls-remote origin main`.

Measure a 3-minute slice first (previous loops ran about 6 min locally); if a step projects over 15 min, file a box request and report PARTIAL. If the clock passes 16:50 before the loops finish, let them finish, then report; the PM reads it next session.

Message to the PM: under 300 words. Lead with the G5b tie line for both loops (real / C1s / C1s-sap, PASS / FAIL), the goal O/E trail-1 line, and whether G4 and G1-G3 held.
