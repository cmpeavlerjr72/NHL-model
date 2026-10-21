# SB-R5 closed loop, block B1a-as: engine_b1aas_v1, fold 2 (2024-25), 200 seeds

> **SB-R5 closed loop: engine DEFAULT table set + block B1a-as flag** (attr['block_b1aas'], replaces the B0 stand-in). Stage 4 = L1x-as, goal = C1s (provisional, D40), ORACLE GOALIE (D8), miss S0t STAND-IN. Pull and shootout flags OFF (stages 7-8 absent: no rebounds, no goalie pull; OT = stage-1 3v3 OT, shootout 50/50 stub). G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. (Report text produced by the SL-R7 grader.)

Engine markers: block_model in meta `block: B1a-as (SB-R5; B0' INV-54 + frozen SB-R4 B1a terms + as-of Ra scale H90 P2000, AS-1 floor f 0.5)`; stand_in ['miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable']; attr_model `stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)`; goal_model `goal: C1s (provisional, D40)`; oracle_goalie `ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)`.

Served-vs-offline parity before the seeds (max |diff|): l1xas 1.49e-08 over 116,716 rows; block 1.49e-08 over 162,300 rows; miss 2.98e-08 over 116,716 rows; goal 1.11e-16 over 76,926 rows; block_b1aas 1.67e-16 over 162,300 rows.

## Blocked share by team-view state, sim vs actual (SB-R1 bands: overall +/-1.0 pp, strength group +/-1.5 pp with n >= 2,000; states reported). `ref B0'` = the paired default-set loop (Lane E3, B0' stand-in), same seeds.

|                                 |   n_actual |   sim_pct |   act_pct |   diff_pp |   tol_pp | status                  |
|:--------------------------------|-----------:|----------:|----------:|----------:|---------:|:------------------------|
| ('b1aas', 'overall ES+PP+PK')   |     162300 |    28.435 |    28.086 |     0.349 |    1.000 | PASS                    |
| ('b1aas', 'group ES')           |     138184 |    29.117 |    28.867 |     0.250 |    1.500 | PASS                    |
| ('b1aas', 'group PP')           |      21153 |    26.188 |    25.216 |     0.972 |    1.500 | PASS                    |
| ('b1aas', 'group PK')           |       2963 |    12.458 |    12.184 |     0.274 |    1.500 | PASS                    |
| ('b1aas', 'state 5v5')          |     135180 |    29.301 |    29.040 |     0.261 |  nan     | reported                |
| ('b1aas', 'state PP')           |      21153 |    26.188 |    25.216 |     0.972 |  nan     | reported                |
| ('b1aas', 'state PK')           |       2963 |    12.458 |    12.184 |     0.274 |  nan     | reported                |
| ('b1aas', 'state 4v4')          |       1635 |    23.637 |    24.037 |    -0.400 |  nan     | UNDERPOWERED (reported) |
| ('b1aas', 'state 3v3')          |       1369 |    17.387 |    17.531 |    -0.144 |  nan     | UNDERPOWERED (reported) |
| ("ref B0'", 'overall ES+PP+PK') |     162300 |    28.377 |    28.086 |     0.291 |    1.000 | PASS                    |
| ("ref B0'", 'group ES')         |     138184 |    29.062 |    28.867 |     0.196 |    1.500 | PASS                    |
| ("ref B0'", 'group PP')         |      21153 |    26.096 |    25.216 |     0.880 |    1.500 | PASS                    |
| ("ref B0'", 'group PK')         |       2963 |    12.482 |    12.184 |     0.298 |    1.500 | PASS                    |
| ("ref B0'", 'state 5v5')        |     135180 |    29.249 |    29.040 |     0.210 |  nan     | reported                |
| ("ref B0'", 'state PP')         |      21153 |    26.096 |    25.216 |     0.880 |  nan     | reported                |
| ("ref B0'", 'state PK')         |       2963 |    12.482 |    12.184 |     0.298 |  nan     | reported                |
| ("ref B0'", 'state 4v4')        |       1635 |    23.704 |    24.037 |    -0.332 |  nan     | UNDERPOWERED (reported) |
| ("ref B0'", 'state 3v3')        |       1369 |    17.037 |    17.531 |    -0.494 |  nan     | UNDERPOWERED (reported) |

- **Block share bands: PASS** (b1aas arm)

## Team-decile R on the sim block share (D32 slope ratio; ES units (game, shooting team); deciles of the shooting team's Ra ES blocked-against rating (for) / the defending team's Ra ES blocks-for rating (against); 1,000 game bootstrap)

- for: R 0.979 (95% CI 0.617..2.578; UNDERPOWERED), old Q5-Q1 1.035, 2,796 units
- against: R 1.012 (95% CI 0.795..1.403; UNDERPOWERED), old Q5-Q1 1.001, 2,796 units
- **R in [0.8, 1.2]: PASS**

## G3 / closed-loop R vs the paired default-set loop (B0')

| cell          | check                    |   b1aas | status   |     ref | ref_status   |   delta |
|:--------------|:-------------------------|--------:|:---------|--------:|:-------------|--------:|
| all reachable | xG per unblocked         | +0.0036 | PASS     | +0.0034 | PASS         | +0.0002 |
| all reachable | tier high pp             | -0.0503 | PASS     | -0.0546 | PASS         | +0.0043 |
| all reachable | tier medium pp           | -0.3253 | PASS     | -0.3264 | PASS         | +0.0012 |
| all reachable | tier low pp              | +0.3756 | PASS     | +0.3811 | PASS         | -0.0055 |
| 5v5           | xG per unblocked         | +0.0069 | PASS     | +0.0066 | PASS         | +0.0003 |
| 5v5           | tier high pp             | -0.1069 | PASS     | -0.1125 | PASS         | +0.0056 |
| 5v5           | tier medium pp           | -0.2031 | PASS     | -0.2055 | PASS         | +0.0024 |
| 5v5           | tier low pp              | +0.3100 | PASS     | +0.3180 | PASS         | -0.0080 |
| PP            | xG per unblocked         | -0.0002 | PASS     | -0.0003 | PASS         | +0.0001 |
| PP            | tier high pp             | +0.1693 | PASS     | +0.1614 | PASS         | +0.0079 |
| PP            | tier medium pp           | +0.0348 | PASS     | +0.0367 | PASS         | -0.0019 |
| PP            | tier low pp              | -0.2041 | PASS     | -0.1981 | PASS         | -0.0060 |
| PK            | xG per unblocked         | +0.0224 | PASS     | +0.0221 | PASS         | +0.0003 |
| PK            | tier high pp             | +0.7778 | PASS     | +0.7769 | PASS         | +0.0010 |
| PK            | tier medium pp           | -0.6377 | PASS     | -0.6415 | PASS         | +0.0038 |
| PK            | tier low pp              | -0.1401 | PASS     | -0.1354 | PASS         | -0.0048 |
| ES            | closed-loop xG R for     | +1.2452 | reported | +1.2435 | reported     | +0.0017 |
| ES            | closed-loop xG R against | +1.1291 | reported | +1.1259 | reported     | +0.0033 |

- G3 (b1aas): **PASS**. Full G3 / per-60 / G2 reports: `docs/tests/gates_g3_sl_r7_L1xas_engine_b1aas_2026-10-21.md`, `docs/tests/gates_g2_sl_r7_L1xas_engine_b1aas_2026-10-21.md`.

