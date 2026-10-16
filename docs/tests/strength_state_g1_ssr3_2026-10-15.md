# SS-R3 closed-loop G1 for H3'' and H2'' (Lane H4, INV-28), 2026-10-15

Spec: SS-R3 "Closed-loop G1" + D14 in `docs/models/strength_state/experiments.md`; G1 as run in SS-R1 (`docs/tests/strength_state_ss_r1_2026-10-15.md`). Worker: Sonnet. Clock: start 20:06 EDT, last compute 20:31 EDT (runs 20:09-20:31, decomposition 20:28-20:35). Detail files: `docs/tests/gates_g1_ss_r3_g1_H3_2026-10-15.md`, `docs/tests/gates_g1_ss_r3_g1_H2_2026-10-15.md` (full G1 tables, per team, stub tables).

## Headline

1. **Offset lookup and parity test: PASS.** `hazard_table_v3` (in `src/nhl_sim/strength_state/lookup.py`) evaluates the arm at level 0 and multiplies by `exp(level_g)`, the per-game de-seasonalised level plus profile p(b). That is exact because the offset has coefficient 1 in both arms. Test `tests/test_ssr3_offset_lookup.py`: 240 random fold-2 games (55,262 reachable-state rows), sample relative error 2.6e-10 (H3'') and 3.2e-10 (H2''), max per-game error 1.4e-8 / 1.8e-8, against the 0.5% limit.
2. **G1, regular season (the binding cells): H3'' and H2'' both PASS every toleranced cell.** PP opps / team-game RS: H3'' 2.625 vs 2.564 (+0.061), H2'' 2.609 vs 2.564 (+0.045), tolerance 0.15. Overall: H3'' +0.051, H2'' +0.034. SS-R1's H3 RS failure (+0.166) is gone.
3. **D14 clean-pass decomposition: CLEAN for H3'' on the regular season** (and for H2'', and for both overall). No single component exceeds the 0.15 tolerance, so none can be an offsetting pair. Playoffs are labelled COMPENSATED, but n = 172 team-games is UNDERPOWERED, so that verdict is a description, not a gate result.
4. **Responsiveness:** the closed-loop sim slopes with the ratings, matching the offline prediction. It is steeper than the actual outcome (see below), a finding and not a pass/fail.

Nothing is PARTIAL. AWS was not used (see "Interpretation choices").

## Interpretation choices (labelled)

- **Local run instead of a Lane O box request.** The brief says to file a request if two parallel arms project past 15 min. A measured 50-seed chunk took 247-267 s, so a 200-seed arm takes about 17 min with two arms in parallel (H3'' also paid a 275 s hazard-table build under contention). The runs were already in flight and finished at 20:27 (H2'') and 20:31 (H3''). A box request (spot boot, inputs to HF, outputs back) could not have finished sooner, so I did not file one. The 3-minute slice rule was met by the first full chunk (257 s), not by a separate slice.
- **Goal stub, type arm, engine:** unchanged from SS-R1. The stub is the 2023-24 league goal rate per skater state, no team terms; T1 is carried over from SS-R1 (`results/strength_state_r3/models/T1_fold2.json` is that file). No goalie pull and the SO is skipped, so TOI 3v3, TOI EN and the share of minors ended by a PP goal are STUB-DEPENDENT.
- **Offset placement:** per (game, team) the level is constant over the game, so it multiplies the whole (minute, state, score, pen-diff) hazard grid of that game.
- **Decomposition identity (D14):** with E = penalty-taking events per team-game (coincidental pairs count for both teams) and f = PP opportunities per event, PPO = f E, so `sim - actual = f_a (E_s - E_a) + (f_s - f_a) E_s` exactly. E_s - E_a is split into (a) offline predicted minus actual events on the actual path in the reachable states 0-4, (a') the actual events in the unreachable state 'other' (trailing-team goalie pulls, 1.5% of events, which the sim cannot visit), (b) state-visit differences (sim time per state minus actual, times the offline mean predicted rate in that state), (d) the remainder on the sim path (score, penalty-differential and clock mix), and (c) the PP-opportunities-per-event term (coincidental/type mix and stacked penalties that open no new advantage). Real time per state comes from the same replay `Recorder` the sim uses. Verdict rule as coded: FAIL if the total is outside 0.15; COMPENSATED if the total is inside but a component exceeds 0.15 in absolute value and an opposite-signed component exists; CLEAN otherwise.
- **Responsiveness quantity:** "PP opportunities conferred" = the opponent's PP opportunities, which are created by this team's penalties, the thing the team taken-rating and the opponent drawn-rating drive. The team's own PP opportunities and the penalties themselves are shown beside it.
- The parity test's `period <= 4` filter excludes no rows (fold 2 has no period >= 5 rows).

## G1 tables (fold 2, 1,398 games x 200 seeds; min/game for TOI; RS n = 1,312 games, PO n = 86 games = 172 team-games)

Status is the literal one from `nhl_sim.eval.g1.evaluate` (tolerances `docs/gates.yaml`: TOI 0.75 min, PP opps 0.15; PO cells under `min_cell_n` = 300 are UNDERPOWERED). Last column: the largest |200-seed minus 100-seed| over the three segments.

| cell | real RS | sim RS | status RS | real PO | sim PO | status PO | real all | sim all | status all | max abs 200-100 |
|---|---|---|---|---|---|---|---|---|---|---|
| **H3''** | | | | | | | | | | |
| TOI 5v5 (min/game) | 50.390 | 50.242 | PASS | 52.197 | 51.594 | UNDERPOWERED | 50.502 | 50.325 | PASS | 0.0094 |
| TOI PP total (min/game) | 8.950 | 9.047 | PASS | 10.244 | 9.590 | UNDERPOWERED | 9.029 | 9.080 | PASS | 0.0013 |
| TOI 4v4 (min/game) | 0.728 | 0.797 | PASS | 0.725 | 0.810 | UNDERPOWERED | 0.728 | 0.798 | PASS | 0.0066 |
| TOI 5v3/3v5 (min/game) | 0.147 | 0.148 | PASS | 0.127 | 0.165 | UNDERPOWERED | 0.146 | 0.149 | PASS | 0.0042 |
| TOI 3v3 (min/game) | 0.567 | 0.452 | STUB-DEPENDENT | 0.000 | 0.001 | STUB-DEPENDENT | 0.532 | 0.425 | STUB-DEPENDENT | 0.0033 |
| TOI EN (min/game) | 1.053 | 0.000 | STUB-DEPENDENT | 1.128 | 0.000 | STUB-DEPENDENT | 1.058 | 0.000 | STUB-DEPENDENT | 0.0000 |
| PP opps / team-game mean | 2.564 | 2.625 | PASS | 2.895 | 2.787 | UNDERPOWERED | 2.584 | 2.635 | PASS | 0.0015 |
| PP opps / team-game SD | 1.261 | 1.382 | PASS | 1.321 | 1.425 | UNDERPOWERED | 1.267 | 1.385 | PASS | 0.0012 |
| PIM / game (strength penalties) | 15.025 | 15.159 | NO-TOLERANCE | 16.651 | 15.995 | NO-TOLERANCE | 15.125 | 15.211 | NO-TOLERANCE | 0.0262 |
| penalty-taking events / team-game | 3.284 | 3.333 | NO-TOLERANCE | 3.796 | 3.526 | NO-TOLERANCE | 3.316 | 3.345 | NO-TOLERANCE | 0.0016 |
| share of minors ended by PP goal | 0.213 | 0.203 | STUB-DEPENDENT | 0.230 | 0.203 | STUB-DEPENDENT | 0.214 | 0.203 | STUB-DEPENDENT | 0.0016 |
| **H2''** | | | | | | | | | | |
| TOI 5v5 (min/game) | 50.390 | 50.281 | PASS | 52.197 | 51.782 | UNDERPOWERED | 50.502 | 50.373 | PASS | 0.0336 |
| TOI PP total (min/game) | 8.950 | 9.011 | PASS | 10.244 | 9.499 | UNDERPOWERED | 9.029 | 9.041 | PASS | 0.0311 |
| TOI 4v4 (min/game) | 0.728 | 0.791 | PASS | 0.725 | 0.805 | UNDERPOWERED | 0.728 | 0.792 | PASS | 0.0037 |
| TOI 5v3/3v5 (min/game) | 0.147 | 0.144 | PASS | 0.127 | 0.160 | UNDERPOWERED | 0.146 | 0.145 | PASS | 0.0027 |
| TOI 3v3 (min/game) | 0.567 | 0.456 | STUB-DEPENDENT | 0.000 | 0.001 | STUB-DEPENDENT | 0.532 | 0.428 | STUB-DEPENDENT | 0.0045 |
| TOI EN (min/game) | 1.053 | 0.000 | STUB-DEPENDENT | 1.128 | 0.000 | STUB-DEPENDENT | 1.058 | 0.000 | STUB-DEPENDENT | 0.0000 |
| PP opps / team-game mean | 2.564 | 2.609 | PASS | 2.895 | 2.756 | UNDERPOWERED | 2.584 | 2.618 | PASS | 0.0109 |
| PP opps / team-game SD | 1.261 | 1.378 | PASS | 1.321 | 1.425 | UNDERPOWERED | 1.267 | 1.382 | PASS | 0.0072 |
| PIM / game (strength penalties) | 15.025 | 15.043 | NO-TOLERANCE | 16.651 | 15.786 | NO-TOLERANCE | 15.125 | 15.089 | NO-TOLERANCE | 0.0987 |
| penalty-taking events / team-game | 3.284 | 3.308 | NO-TOLERANCE | 3.796 | 3.481 | NO-TOLERANCE | 3.316 | 3.319 | NO-TOLERANCE | 0.0159 |
| share of minors ended by PP goal | 0.213 | 0.203 | STUB-DEPENDENT | 0.230 | 0.203 | STUB-DEPENDENT | 0.214 | 0.203 | STUB-DEPENDENT | 0.0018 |

## Per team (n = team-games, every cell UNDERPOWERED at about 87 per team; tables in the per-arm files)

Correlation of PP opps per team-game, sim vs real, over the 32 teams: H3'' 0.64, H2'' 0.69 (SS-R1: 0.66 / 0.69). No per-team cell is graded.

## Reading the decomposition

- **RS, H3'':** sim - actual +0.061 = (a) hazard level +0.046 (offline predicted 3.292 vs actual 3.233 reachable events per team-game, +1.8%, the listed H3'' level bias), (a') -0.040 ('other' state, unreachable), (b) state-visit -0.005, (d) remainder +0.037, (c) PP opps per event +0.023. Every component is under a third of the 0.15 tolerance; the only opposite-signed pair is (a) against (a'), each about 0.04. By the D14 rule as written that is CLEAN. The PM may note that (a') is a known sub-model gap (stage 8 pull model) and (a) is the known level bias, so the +0.061 total is not zero-bias but is also not hiding a large offset.
- **RS, H2'':** +0.045 = +0.024, -0.040, -0.005, +0.040, +0.027. CLEAN.
- **Playoffs (n = 172 team-games, UNDERPOWERED):** both arms under-predict playoff penalty-taking offline (reachable events: predicted 3.48 vs actual 3.75 for H3'', 3.42 vs 3.75 for H2''), (a) = -0.21 / -0.25, offset by (c) and (d). Verdict text COMPENSATED, not a gate result; with 86 games the playoff level is not resolvable. Logged as a monitoring item, not a finding.
- **State-visit (b)** is small everywhere: the sim spends the right time in 5v5 / PP / PK / 4v4 (RS dT within 0.003 h per team-game), and 3v3 time is STUB-DEPENDENT.
- **Dispersion (not graded beyond the SD cell):** the PP-opps SD passes (H3'' 1.385 vs 1.267, +0.118, tolerance 0.15, 79% of it). P(0 PP opps) is 4.2% sim vs 2.6% actual and P(5+) is 9.3% vs 6.8%: the sim is over-dispersed, as SS-R1 was (SD 1.394). P(k) cells are NO-TOLERANCE. Candidate cause: the independent-Poisson hazard cannot reproduce the negative dependence between a team's penalties in a game (make-up calls, discipline); logged as a candidate for a future experiment, not diagnosed here.

## Responsiveness (step 4): H3'' in the closed loop

Quintile tables for both arms follow in the appended detail. H3'' summary (team-games per quintile about 559; actual quintile-mean SE about 0.055):

| quintile of | Q0 conferred actual / sim | Q4 conferred actual / sim | Q4 minus Q0 actual / sim | penalties Q0 actual / sim / offline | penalties Q4 actual / sim / offline |
|---|---|---|---|---|---|
| team taken-rating | 2.336 / 2.337 | 2.748 / 2.971 | 0.412 / 0.634 | 2.871 / 2.977 / 2.978 | 3.646 / 3.761 / 3.841 |
| opponent drawn-rating | 2.446 / 2.434 | 2.687 / 2.878 | 0.241 / 0.444 | 3.025 / 3.080 / 3.108 | 3.581 / 3.674 / 3.655 |

- The sim slopes strongly with both ratings, so the model is matchup-responsive and not flat at the league mean.
- It is steeper than the actual outcome: the Q4-Q0 spread of conferred PP opps is 1.5x (taken) and 1.8x (drawn) the actual spread, about 3 SE on the top quintile. The sim's penalty counts track the OFFLINE predicted counts (3.76 vs 3.84 in the top taken quintile, 2.98 vs 2.98 in the bottom), so the extra slope sits in the hazard model's rating coefficients (offline-predicted spread 0.86 vs actual 0.77 events per team-game), and the engine reproduces it faithfully. It is a mild over-response of the ratings, not an engine defect. Not decided here.
- H2'' shows the same pattern with a larger top-quintile excess (taken Q4 conferred 2.971 vs 2.748 actual).

## Status and recommendation

- G1 regular-season cells PASS for H3'' and H2'' and the D14 decomposition is CLEAN, so the D14 condition for accepting H3'' (a clean G1 pass on the regular-season cells) is met as written. STUB-DEPENDENT cells (3v3 TOI, EN TOI, PP-goal share) remain until stage 6 and stage 8. strength_state stays TESTING in the ledger; the acceptance decision is the PM's.
- Proposed monitoring items: January 2025 level (+8.6%, D14), playoff level (3.48 predicted vs 3.75 actual events), PP-opps over-dispersion, top-quintile rating over-response.

## Resume / reproduce

```
.venv/Scripts/python.exe -m pytest tests/test_ssr3_offset_lookup.py -q
.venv/Scripts/python.exe scripts/run_strength_state_g1_v3.py --arm H3 --seeds 200
.venv/Scripts/python.exe scripts/run_strength_state_g1_v3.py --arm H2 --seeds 200
.venv/Scripts/python.exe scripts/diag_strength_state_g1_decomp_v3.py --arm H3
.venv/Scripts/python.exe scripts/diag_strength_state_g1_decomp_v3.py --arm H2
```

Outputs: `results/ss_r3_g1_{H3,H2}/` (games, strength_toi, run_meta; gitignored). Per-arm decomposition detail is appended below.

---

# Appendix A: H3'' detail

## D14 decomposition and responsiveness, H3'' (SS-R3 offsets), fold 2, 200 seeds

### regular season (actual team-games n = 2624; tolerance 0.15)

PP opps / team-game: actual 2.5640, sim 2.6250, sim - actual +0.0610. Events / team-game: actual 3.2839 (offline rows: reachable 3.2325 + 'other' 0.0514), offline predicted on reachable states 3.2919, sim 3.3330. PP opps per event: actual 0.7808, sim 0.7876.

|                                                                    |   PP opps / team-game |   pct_of_actual |
|:-------------------------------------------------------------------|----------------------:|----------------:|
| (a) hazard level, reachable states (offline pred - actual events)  |                0.0464 |          1.8088 |
| (a') actual events in unreachable state 'other' (sim cannot visit) |               -0.0402 |         -1.5667 |
| (b) state-visit: (sim time per state - actual) x hazard            |               -0.0053 |         -0.2059 |
| (d) remainder (sim-path hazard mix: score / pen-diff / clock)      |                0.0374 |          1.4590 |
| (c) PP opps per event (coincidental / type mix, stacked penalties) |                0.0227 |          0.8846 |

Sum of components = +0.0610 (identity check passed). (b) explained part -0.0068 events/team-game before scaling by f_a.

|                   |   T_sim (h/team-game) |   T_act |      dT |   lam (events/h, offline pred) |   contribution (events/team-game) |
|:------------------|----------------------:|--------:|--------:|-------------------------------:|----------------------------------:|
| 5v5               |                0.8374 |  0.8398 | -0.0025 |                         3.6001 |                           -0.0089 |
| PP-for (incl 5v3) |                0.0754 |  0.0746 |  0.0008 |                         2.2485 |                            0.0018 |
| PK (incl 3v5)     |                0.0754 |  0.0746 |  0.0008 |                         1.4030 |                            0.0011 |
| 4v4               |                0.0133 |  0.0121 |  0.0011 |                         2.7276 |                            0.0031 |
| 3v3               |                0.0075 |  0.0094 | -0.0019 |                         2.0670 |                           -0.0039 |

- No single component exceeds the tolerance (0.15) in absolute value.
- **Verdict (regular season): CLEAN**

### playoffs (actual team-games n = 172; tolerance 0.15)

PP opps / team-game: actual 2.8953, sim 2.7867, sim - actual -0.1086. Events / team-game: actual 3.7965 (offline rows: reachable 3.7500 + 'other' 0.0465), offline predicted on reachable states 3.4786, sim 3.5257. PP opps per event: actual 0.7626, sim 0.7904.

|                                                                    |   PP opps / team-game |   pct_of_actual |
|:-------------------------------------------------------------------|----------------------:|----------------:|
| (a) hazard level, reachable states (offline pred - actual events)  |               -0.2070 |         -7.1497 |
| (a') actual events in unreachable state 'other' (sim cannot visit) |               -0.0355 |         -1.2251 |
| (b) state-visit: (sim time per state - actual) x hazard            |               -0.0407 |         -1.4049 |
| (d) remainder (sim-path hazard mix: score / pen-diff / clock)      |                0.0766 |          2.6457 |
| (c) PP opps per event (coincidental / type mix, stacked penalties) |                0.0979 |          3.3830 |

Sum of components = -0.1086 (identity check passed). (b) explained part -0.0533 events/team-game before scaling by f_a.

|                   |   T_sim (h/team-game) |   T_act |      dT |   lam (events/h, offline pred) |   contribution (events/team-game) |
|:------------------|----------------------:|--------:|--------:|-------------------------------:|----------------------------------:|
| 5v5               |                0.8599 |  0.8700 | -0.0101 |                         3.6604 |                           -0.0368 |
| PP-for (incl 5v3) |                0.0799 |  0.0854 | -0.0054 |                         2.3119 |                           -0.0126 |
| PK (incl 3v5)     |                0.0799 |  0.0854 | -0.0054 |                         1.4731 |                           -0.0080 |
| 4v4               |                0.0135 |  0.0121 |  0.0014 |                         2.9093 |                            0.0041 |
| 3v3               |                0.0000 |  0.0000 |  0.0000 |                         0.0000 |                            0.0000 |

- Component over tolerance: (a) hazard level, reachable states (offline pred - actual events) = -0.2070; opposite-signed components: (d) remainder (sim-path hazard mix: score / pen-diff / clock) +0.0766, (c) PP opps per event (coincidental / type mix, stacked penalties) +0.0979.
- **Verdict (playoffs): COMPENSATED**

### overall (actual team-games n = 2796; tolerance 0.15)

PP opps / team-game: actual 2.5844, sim 2.6350, sim - actual +0.0506. Events / team-game: actual 3.3155 (offline rows: reachable 3.2643 + 'other' 0.0511), offline predicted on reachable states 3.3034, sim 3.3449. PP opps per event: actual 0.7795, sim 0.7878.

|                                                                    |   PP opps / team-game |   pct_of_actual |
|:-------------------------------------------------------------------|----------------------:|----------------:|
| (a) hazard level, reachable states (offline pred - actual events)  |                0.0304 |          1.1778 |
| (a') actual events in unreachable state 'other' (sim cannot visit) |               -0.0399 |         -1.5426 |
| (b) state-visit: (sim time per state - actual) x hazard            |               -0.0074 |         -0.2881 |
| (d) remainder (sim-path hazard mix: score / pen-diff / clock)      |                0.0398 |          1.5403 |
| (c) PP opps per event (coincidental / type mix, stacked penalties) |                0.0277 |          1.0699 |

Sum of components = +0.0506 (identity check passed). (b) explained part -0.0096 events/team-game before scaling by f_a.

|                   |   T_sim (h/team-game) |   T_act |      dT |   lam (events/h, offline pred) |   contribution (events/team-game) |
|:------------------|----------------------:|--------:|--------:|-------------------------------:|----------------------------------:|
| 5v5               |                0.8388 |  0.8417 | -0.0029 |                         3.6039 |                           -0.0106 |
| PP-for (incl 5v3) |                0.0757 |  0.0752 |  0.0004 |                         2.2530 |                            0.0010 |
| PK (incl 3v5)     |                0.0757 |  0.0752 |  0.0004 |                         1.4079 |                            0.0006 |
| 4v4               |                0.0133 |  0.0121 |  0.0012 |                         2.7388 |                            0.0032 |
| 3v3               |                0.0071 |  0.0089 | -0.0018 |                         2.0670 |                           -0.0037 |

- No single component exceeds the tolerance (0.15) in absolute value.
- **Verdict (overall): CLEAN**

### Type mix behind (c) (overall)

|              |   actual share of penalty-taking events |   sim share |
|:-------------|----------------------------------------:|------------:|
| minor        |                                  0.7939 |      0.7989 |
| double       |                                  0.0153 |      0.0138 |
| major        |                                  0.0036 |      0.0043 |
| coincidental |                                  0.1873 |      0.1830 |

### Responsiveness (closed loop, fold 2, RS + PO; sim = mean over seeds per team-game)

Quintiles are over team-games (the as-of rating of that game; Q0 low .. Q4 high). 'PP opps conferred' is the opponent's PP opportunities, i.e. those created by this team's penalties, the quantity the team-taken and opponent-drawn ratings drive in the hazard (literal choice, labelled); 'own PP opps' is the other direction. n = team-games per quintile.

#### by team taken-rating quintile

|   q |        n |   rating |   penalties_actual |   penalties_sim |   penalties_offline_pred |   ppo_conferred_actual |   ppo_conferred_sim |   own_ppo_actual |   own_ppo_sim |   conferred sim/actual |
|----:|---------:|---------:|-------------------:|----------------:|-------------------------:|-----------------------:|--------------------:|-----------------:|--------------:|-----------------------:|
|   0 | 560.0000 |  -0.1648 |             2.8714 |          2.9770 |                   2.9783 |                 2.3357 |              2.3372 |           2.5446 |        2.4637 |                 1.0006 |
|   1 | 559.0000 |  -0.0537 |             3.1360 |          3.1984 |                   3.2228 |                 2.5134 |              2.5159 |           2.5009 |        2.5909 |                 1.0010 |
|   2 | 559.0000 |   0.0140 |             3.3900 |          3.2549 |                   3.2291 |                 2.6315 |              2.5610 |           2.5886 |        2.6108 |                 0.9732 |
|   3 | 559.0000 |   0.0610 |             3.5349 |          3.5337 |                   3.5471 |                 2.6941 |              2.7901 |           2.5725 |        2.6827 |                 1.0356 |
|   4 | 559.0000 |   0.1437 |             3.6458 |          3.7610 |                   3.8407 |                 2.7478 |              2.9712 |           2.7156 |        2.8271 |                 1.0813 |

Slope of PP opps conferred on the rating (quintile means): actual 1.385, sim 2.054 (sim/actual 1.48). Actual quintile-mean SE is about 0.055 (PP-opps SD ~1.3, n ~559 per quintile).

#### by opponent drawn-rating quintile

|   q |        n |   rating |   penalties_actual |   penalties_sim |   penalties_offline_pred |   ppo_conferred_actual |   ppo_conferred_sim |   own_ppo_actual |   own_ppo_sim |   conferred sim/actual |
|----:|---------:|---------:|-------------------:|----------------:|-------------------------:|-----------------------:|--------------------:|-----------------:|--------------:|-----------------------:|
|   0 | 560.0000 |  -0.1224 |             3.0250 |          3.0799 |                   3.1076 |                 2.4464 |              2.4338 |           2.4321 |        2.3881 |                 0.9948 |
|   1 | 559.0000 |  -0.0386 |             3.2665 |          3.2372 |                   3.2782 |                 2.6100 |              2.5599 |           2.6082 |        2.5129 |                 0.9808 |
|   2 | 559.0000 |   0.0023 |             3.3041 |          3.3247 |                   3.3554 |                 2.5653 |              2.6214 |           2.6279 |        2.6239 |                 1.0219 |
|   3 | 559.0000 |   0.0439 |             3.4007 |          3.4086 |                   3.4213 |                 2.6136 |              2.6825 |           2.5850 |        2.7160 |                 1.0264 |
|   4 | 559.0000 |   0.1176 |             3.5814 |          3.6744 |                   3.6552 |                 2.6869 |              2.8777 |           2.6691 |        2.9345 |                 1.0710 |

Slope of PP opps conferred on the rating (quintile means): actual 0.906, sim 1.803 (sim/actual 1.99). Actual quintile-mean SE is about 0.055 (PP-opps SD ~1.3, n ~559 per quintile).


---

# Appendix B: H2'' detail

## D14 decomposition and responsiveness, H2'' (SS-R3 offsets), fold 2, 200 seeds

### regular season (actual team-games n = 2624; tolerance 0.15)

PP opps / team-game: actual 2.5640, sim 2.6093, sim - actual +0.0453. Events / team-game: actual 3.2839 (offline rows: reachable 3.2325 + 'other' 0.0514), offline predicted on reachable states 3.2631, sim 3.3080. PP opps per event: actual 0.7808, sim 0.7888.

|                                                                    |   PP opps / team-game |   pct_of_actual |
|:-------------------------------------------------------------------|----------------------:|----------------:|
| (a) hazard level, reachable states (offline pred - actual events)  |                0.0239 |          0.9322 |
| (a') actual events in unreachable state 'other' (sim cannot visit) |               -0.0402 |         -1.5667 |
| (b) state-visit: (sim time per state - actual) x hazard            |               -0.0046 |         -0.1799 |
| (d) remainder (sim-path hazard mix: score / pen-diff / clock)      |                0.0397 |          1.5469 |
| (c) PP opps per event (coincidental / type mix, stacked penalties) |                0.0265 |          1.0332 |

Sum of components = +0.0453 (identity check passed). (b) explained part -0.0059 events/team-game before scaling by f_a.

|                   |   T_sim (h/team-game) |   T_act |      dT |   lam (events/h, offline pred) |   contribution (events/team-game) |
|:------------------|----------------------:|--------:|--------:|-------------------------------:|----------------------------------:|
| 5v5               |                0.8380 |  0.8398 | -0.0018 |                         3.5716 |                           -0.0065 |
| PP-for (incl 5v3) |                0.0751 |  0.0746 |  0.0005 |                         2.2218 |                            0.0011 |
| PK (incl 3v5)     |                0.0751 |  0.0746 |  0.0005 |                         1.3510 |                            0.0007 |
| 4v4               |                0.0132 |  0.0121 |  0.0010 |                         2.6692 |                            0.0028 |
| 3v3               |                0.0076 |  0.0094 | -0.0018 |                         2.1951 |                           -0.0040 |

- No single component exceeds the tolerance (0.15) in absolute value.
- **Verdict (regular season): CLEAN**

### playoffs (actual team-games n = 172; tolerance 0.15)

PP opps / team-game: actual 2.8953, sim 2.7558, sim - actual -0.1396. Events / team-game: actual 3.7965 (offline rows: reachable 3.7500 + 'other' 0.0465), offline predicted on reachable states 3.4201, sim 3.4810. PP opps per event: actual 0.7626, sim 0.7917.

|                                                                    |   PP opps / team-game |   pct_of_actual |
|:-------------------------------------------------------------------|----------------------:|----------------:|
| (a) hazard level, reachable states (offline pred - actual events)  |               -0.2516 |         -8.6893 |
| (a') actual events in unreachable state 'other' (sim cannot visit) |               -0.0355 |         -1.2251 |
| (b) state-visit: (sim time per state - actual) x hazard            |               -0.0333 |         -1.1518 |
| (d) remainder (sim-path hazard mix: score / pen-diff / clock)      |                0.0798 |          2.7545 |
| (c) PP opps per event (coincidental / type mix, stacked penalties) |                0.1011 |          3.4914 |

Sum of components = -0.1396 (identity check passed). (b) explained part -0.0437 events/team-game before scaling by f_a.

|                   |   T_sim (h/team-game) |   T_act |      dT |   lam (events/h, offline pred) |   contribution (events/team-game) |
|:------------------|----------------------:|--------:|--------:|-------------------------------:|----------------------------------:|
| 5v5               |                0.8630 |  0.8700 | -0.0069 |                         3.6062 |                           -0.0250 |
| PP-for (incl 5v3) |                0.0792 |  0.0854 | -0.0062 |                         2.2534 |                           -0.0140 |
| PK (incl 3v5)     |                0.0792 |  0.0854 | -0.0062 |                         1.3858 |                           -0.0086 |
| 4v4               |                0.0134 |  0.0121 |  0.0013 |                         2.9191 |                            0.0039 |
| 3v3               |                0.0000 |  0.0000 |  0.0000 |                         0.0000 |                            0.0000 |

- Component over tolerance: (a) hazard level, reachable states (offline pred - actual events) = -0.2516; opposite-signed components: (d) remainder (sim-path hazard mix: score / pen-diff / clock) +0.0798, (c) PP opps per event (coincidental / type mix, stacked penalties) +0.1011.
- **Verdict (playoffs): COMPENSATED**

### overall (actual team-games n = 2796; tolerance 0.15)

PP opps / team-game: actual 2.5844, sim 2.6183, sim - actual +0.0339. Events / team-game: actual 3.3155 (offline rows: reachable 3.2643 + 'other' 0.0511), offline predicted on reachable states 3.2727, sim 3.3186. PP opps per event: actual 0.7795, sim 0.7890.

|                                                                    |   PP opps / team-game |   pct_of_actual |
|:-------------------------------------------------------------------|----------------------:|----------------:|
| (a) hazard level, reachable states (offline pred - actual events)  |                0.0066 |          0.2544 |
| (a') actual events in unreachable state 'other' (sim cannot visit) |               -0.0399 |         -1.5426 |
| (b) state-visit: (sim time per state - actual) x hazard            |               -0.0064 |         -0.2473 |
| (d) remainder (sim-path hazard mix: score / pen-diff / clock)      |                0.0421 |          1.6309 |
| (c) PP opps per event (coincidental / type mix, stacked penalties) |                0.0314 |          1.2164 |

Sum of components = +0.0339 (identity check passed). (b) explained part -0.0082 events/team-game before scaling by f_a.

|                   |   T_sim (h/team-game) |   T_act |      dT |   lam (events/h, offline pred) |   contribution (events/team-game) |
|:------------------|----------------------:|--------:|--------:|-------------------------------:|----------------------------------:|
| 5v5               |                0.8396 |  0.8417 | -0.0021 |                         3.5738 |                           -0.0076 |
| PP-for (incl 5v3) |                0.0753 |  0.0752 |  0.0001 |                         2.2240 |                            0.0002 |
| PK (incl 3v5)     |                0.0753 |  0.0752 |  0.0001 |                         1.3534 |                            0.0001 |
| 4v4               |                0.0132 |  0.0121 |  0.0011 |                         2.6846 |                            0.0029 |
| 3v3               |                0.0071 |  0.0089 | -0.0017 |                         2.1951 |                           -0.0038 |

- No single component exceeds the tolerance (0.15) in absolute value.
- **Verdict (overall): CLEAN**

### Type mix behind (c) (overall)

|              |   actual share of penalty-taking events |   sim share |
|:-------------|----------------------------------------:|------------:|
| minor        |                                  0.7939 |      0.7991 |
| double       |                                  0.0153 |      0.0137 |
| major        |                                  0.0036 |      0.0043 |
| coincidental |                                  0.1873 |      0.1828 |

### Responsiveness (closed loop, fold 2, RS + PO; sim = mean over seeds per team-game)

Quintiles are over team-games (the as-of rating of that game; Q0 low .. Q4 high). 'PP opps conferred' is the opponent's PP opportunities, i.e. those created by this team's penalties, the quantity the team-taken and opponent-drawn ratings drive in the hazard (literal choice, labelled); 'own PP opps' is the other direction. n = team-games per quintile.

#### by team taken-rating quintile

|   q |        n |   rating |   penalties_actual |   penalties_sim |   penalties_offline_pred |   ppo_conferred_actual |   ppo_conferred_sim |   own_ppo_actual |   own_ppo_sim |   conferred sim/actual |
|----:|---------:|---------:|-------------------:|----------------:|-------------------------:|-----------------------:|--------------------:|-----------------:|--------------:|-----------------------:|
|   0 | 560.0000 |  -0.1648 |             2.8714 |          2.8232 |                   2.7998 |                 2.3357 |              2.2204 |           2.5446 |        2.3957 |                 0.9506 |
|   1 | 559.0000 |  -0.0537 |             3.1360 |          3.1606 |                   3.1973 |                 2.5134 |              2.4919 |           2.5009 |        2.5571 |                 0.9915 |
|   2 | 559.0000 |   0.0140 |             3.3900 |          3.3447 |                   3.3523 |                 2.6315 |              2.6415 |           2.5886 |        2.6181 |                 1.0038 |
|   3 | 559.0000 |   0.0610 |             3.5349 |          3.5036 |                   3.5103 |                 2.6941 |              2.7674 |           2.5725 |        2.6836 |                 1.0272 |
|   4 | 559.0000 |   0.1437 |             3.6458 |          3.7617 |                   3.8500 |                 2.7478 |              2.9710 |           2.7156 |        2.8374 |                 1.0812 |

Slope of PP opps conferred on the rating (quintile means): actual 1.385, sim 2.425 (sim/actual 1.75). Actual quintile-mean SE is about 0.055 (PP-opps SD ~1.3, n ~559 per quintile).

#### by opponent drawn-rating quintile

|   q |        n |   rating |   penalties_actual |   penalties_sim |   penalties_offline_pred |   ppo_conferred_actual |   ppo_conferred_sim |   own_ppo_actual |   own_ppo_sim |   conferred sim/actual |
|----:|---------:|---------:|-------------------:|----------------:|-------------------------:|-----------------------:|--------------------:|-----------------:|--------------:|-----------------------:|
|   0 | 560.0000 |  -0.1224 |             3.0250 |          2.9770 |                   3.0102 |                 2.4464 |              2.3595 |           2.4321 |        2.3047 |                 0.9644 |
|   1 | 559.0000 |  -0.0386 |             3.2665 |          3.1915 |                   3.2394 |                 2.6100 |              2.5273 |           2.6082 |        2.4960 |                 0.9683 |
|   2 | 559.0000 |   0.0023 |             3.3041 |          3.3312 |                   3.3591 |                 2.5653 |              2.6281 |           2.6279 |        2.6402 |                 1.0245 |
|   3 | 559.0000 |   0.0439 |             3.4007 |          3.4279 |                   3.4455 |                 2.6136 |              2.7007 |           2.5850 |        2.7221 |                 1.0333 |
|   4 | 559.0000 |   0.1176 |             3.5814 |          3.6661 |                   3.6552 |                 2.6869 |              2.8764 |           2.6691 |        2.9291 |                 1.0705 |

Slope of PP opps conferred on the rating (quintile means): actual 0.906, sim 2.146 (sim/actual 2.37). Actual quintile-mean SE is about 0.055 (PP-opps SD ~1.3, n ~559 per quintile).

