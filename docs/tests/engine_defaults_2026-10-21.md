# INV-63 (Lane E3): the engine's default table set, 2026-10-21

PLUMBING, NOT A GATE. ORACLE GOALIE (box-score starter faces every SOG, D8). Stages 7-8 absent.

## Result

- **Fixture bit-identity: YES.** Fixture recorded from HEAD 16f877f BEFORE any edit (`tests/fixtures/sim_defaults_flag_parity.json`, `scripts/diag_engine_l1xas_parity_fixture.py --commit HEAD`; all 14 cases of `l1xas_parity_cases`: stage-1 / attempts / T2 / attr cdf / levelled / stand-ins / full INV-60 stack, synthetic and real). `tests/engine/test_sim_defaults.py` asserts every digest. `sim.py` changed in its docstring only, so this holds by construction and by test. Whole `tests/engine`: 147 passed.
- **Loop bit-identity to Lane A7's SL-R7 loop: YES.** 200 seeds, fold 2, 1,398 games, seeds 0-199 in 4 x 50. All four part files have the same pandas content hash AND the same raw file sha256 as `results/sl_r7_g3_L1xas` (`run_engine_defaults_v1.py cmp`). The G3 and G2 report bodies are textually identical to A7's (diff of everything below the header: empty). Meta markers identical.
- **Save % / goals per 60 (all reachable):** sim sv 0.9006 vs actual 0.8994 (C1s expected 0.9005, +0.11 pp), goals per 60 2.785 vs 2.778 (+0.2%). 5v5 sv 0.9099 vs 0.9095, g60 2.480 vs 2.448 (+1.3%); PP sv 0.8533 vs 0.8479, g60 7.54 vs 7.83 (-3.6%); PK sv 0.9074 vs 0.9072, g60 0.895 vs 0.918 (-2.6%). Underpowered (n SOG < 2,000): 4v4 sv 0.8785 vs 0.8854, g60 3.09 vs 2.96; 3v3 sv 0.7979 vs 0.8041, g60 6.91 vs 6.58.

## What "default on" is

The engine core (`simulate`) is a set of default-off flags keyed on `tables` / `tables["attr"]`. There was no single "default table builder" in the engine: each runner had its own `build_attr`. New `src/nhl_sim/engine/defaults.py`:

- `default_attr(games)`: stage 4 L1x-as (`attr["l1x"]`), block B0 stand-in (INV-54 groups), miss S0t stand-in, goal C1s (oracle goalie). Checks all four served components against the offline fold-2 predictions (< 1e-6) before returning (measured 1.5e-8 / 1.5e-8 / 3.0e-8 / 1.1e-16).
- `l0s_attr(games)`: the explicit pre-D43 path (L0s stand-in labelled `attr`), for reproducing the 2026-10-16 and INV-60 loops.
- The xG_ref goal stub (`attr["xg"]` without `attr["goal"]`) and every older variant stay behind their flags. Nothing deleted.
- Stage 1 (H3''-LC2 + T2) and stage 3 (A3g-c) remain the other `tables` keys, loaded by `run_shot_attempt_g2.stage1_tables("lc2t2")` plus `att_lam_A3g-c_fold2.npy` in the runner.
- Markers (checked in the test and in the loop meta): `stand_in` = block B0, miss S0t only (no `attr`); `attr_model` = L1x-as label; `goal_model` = `goal: C1s (provisional, D40)`; `oracle_goalie` present. The explicit L0s path keeps the `attr` label and has no `attr_model`.

Runner: `scripts/run_engine_defaults_v1.py {sim,grade,cmp}` (wraps the A7 grader with `defaults.default_attr`).

## Gates (plumbing loop, identical to A7's)

- **G3: PASS** (overall slice; all reachable / 5v5 / PP / PK). Reports: `docs/tests/gates_g3_sl_r7_L1xas_engine_defaults_2026-10-21.md`. Closed-loop ES responsiveness "for" R 1.243, "against" R 1.126 (reported, UNDERPOWERED CIs).
- **G2 re-check:** per-60 5v5 +0.4%, PP -0.4%, PK -1.4%, 4v4 +2.6% (listed INV-42), 3v3 +5.3% FAIL (listed INV-35), team-game mean -1.0%, responsiveness 1.147 / 1.111 PASS. Report: `gates_g2_sl_r7_L1xas_engine_defaults_2026-10-21.md`.
- **G5-G7 (LABELLED PLUMBING, stages 7-8 absent; not gate results):** `gates_g5g7_engine_defaults_2026-10-21.md`. G5 FAIL (total-goal P(k) cells, margin SD ratio 0.873, KS D 0.072), G6 FAIL (home win 53.9% vs 56.5%), G7: regulation tie rate 0.2045 vs 0.2082 PASS, shootout rate 6.25% vs 5.51% PASS, EN goals 0 vs 0.406 FAIL (no goalie pull). End states REG 79.5% / OT 14.2% / SO 6.2%. All expected from the absent stage 7-8 models and the stand-ins; same as A7's loop.
- **Stage 5b / 6 by state:** table in the G3 report (`## Stage 5b / 6 by state`), summarised above (SOG per 60 all reachable 28.01 vs 27.63, +1.4%; miss share 33.1% vs 34.1%, -1.0 pp, the S0t offline bias).

## Clock

- Slice (2 seeds, includes 4 s table build + parity): 13:17:04-13:17:21, 13 s of sim; bit-identical to A7 rows for seeds 0-1.
- Loop 4 x 50 seeds, 2 threads each: 13:17:29-13:23:32 (6 min); grade 13:23:48-13:24:21 (+ G5-G7). Under the 15 min AWS threshold; no box request.

## Docs touched

`docs/ops/sim_output_schema.md` (markers, default set, explicit flags), `sim.py` docstring, ledger rows (shot_attribute: L1x-as served by default; goal: C1s served by default).

## Incident

I ran a bare `python -` with no stdin (not the venv) that hung as background task bmn75nei2; stopped through the harness (my own task). No other process touched.

## Proposed PM text

HANDOFF / status: "INV-63 done: the engine default table set is L1x-as + C1s (oracle goalie) + stand-ins B0 / S0t; `defaults.default_attr`; L0s via `defaults.l0s_attr`; per-seed outputs bit-identical to SL-R7's loop."
