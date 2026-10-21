# Gate report: end_game_pull_off_v1 (season 20242025, segment all)

Generated 2026-10-21 by `scripts/eval_gates.py`. Tolerances `docs/gates.yaml` (provisional). Sim rows 279600. run_meta: {'tag': 'end_game_pull_off_v1', 'pull': 'off', 'seed0': 0, 'nseeds': 50, 'fold': 2, 'season': 20242025, 'sealed_touched': False, 'stand_in': ['block: STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable'], 'attr_model': 'stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)', 'goal_model': 'goal: C1s (provisional, D40)', 'oracle_goalie': 'ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)', 'pull_model': 'none', 'pull_stand_in': [], 'pull_info': None, 'delayed_penalty': 'no engine state (INV-70)', 'info': {'parity': {}}, 'n_seeds': 200, 'engine_tag': 'event_engine_stage3_sa_r1'}

| gate | status |
|---|---|
| G1 | PASS |
| G2 | FAIL |
| G3 | NEEDS-INSTRUMENTATION |
| G4 | NEEDS-INSTRUMENTATION |
| G5 | FAIL |
| G6 | FAIL |
| G7 | FAIL |
| G8 | NEEDS-INSTRUMENTATION |
| G9 | FAIL |

## G1: PASS

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| TOI 5v5 (min/game) | 50.2649 | 50.5015 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP total (min/game) | 9.1714 | 9.0293 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP home (min/game) | 4.7021 | 4.7101 | 0.75 | PASS | 1398 | delta=-0.0080 |
| TOI PP away (min/game) | 4.4693 | 4.3191 | 0.75 | PASS | 1398 | delta=+0.1502 |
| TOI 4v4 (min/game) | 0.7822 | 0.7282 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI 3v3 (min/game) | 0.4913 | 0.5319 | 0.75 | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: 3v3 time is regular-season OT; OT frequency comes from the stub goals (literal PASS) |
| TOI 5v3/3v5 (min/game) | 0.1734 | 0.1459 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI EN (min/game) | 0.0000 | 1.0577 | 0.75 | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: no goalie-pull model yet (stage 8) (literal FAIL) |
| PP opps / team-game mean | 2.6656 | 2.5844 | 0.15 | PASS | 1398 | delta=+0.0812 |
| PP opps / team-game SD | 1.3792 | 1.2674 | 0.15 | PASS | 1398 | delta=+0.1119 |
| P(PP opps=0) | 0.0389 | 0.0261 |  | NO-TOLERANCE | 1398 | delta=+0.0128 |
| P(PP opps=1) | 0.1617 | 0.1656 |  | NO-TOLERANCE | 1398 | delta=-0.0039 |
| P(PP opps=2) | 0.2792 | 0.3219 |  | NO-TOLERANCE | 1398 | delta=-0.0427 |
| P(PP opps=3) | 0.2655 | 0.2622 |  | NO-TOLERANCE | 1398 | delta=+0.0033 |
| P(PP opps=4) | 0.1600 | 0.1563 |  | NO-TOLERANCE | 1398 | delta=+0.0037 |
| P(PP opps=5) | 0.0671 | 0.0497 |  | NO-TOLERANCE | 1398 | delta=+0.0174 |
| P(PP opps=6) | 0.0210 | 0.0139 |  | NO-TOLERANCE | 1398 | delta=+0.0070 |
| P(PP opps=7+) | 0.0066 | 0.0043 |  | NO-TOLERANCE | 1398 | delta=+0.0023 |
| penalty-taking events / team-game | 3.3475 | 3.3155 |  | NO-TOLERANCE | 1398 | delta=+0.0320 |
| PIM / game (strength penalties) | 15.1440 | 15.1252 |  | NO-TOLERANCE | 1398 | delta=+0.0188 |
| share of minors ended by PP goal | 0.2017 | 0.2141 |  | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: PP-goal frequency is the stub goal rate (league, no team terms) (literal NO-TOLERANCE) |

## G2: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| per60_state 5v5 | 58.7016 | 58.4717 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PP | 101.3069 | 101.7125 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PK | 14.0456 | 14.2473 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 4v4 | 50.0594 | 48.8019 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 3v3 | 58.1629 | 55.2313 | 0.03 | FAIL | 2796 | n=2796 team-games |
| per60_state EN-for | 0.0000 | 153.4874 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_state EN-against | 0.0000 | 48.4810 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_score <=-3 | 62.9944 | 65.4146 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| per60_score -2 | 63.7502 | 68.3894 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score -1 | 62.5921 | 64.3039 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score 0 | 59.0224 | 58.7080 | 0.03 | PASS | 2796 | n=984 team-hours |
| per60_score +1 | 54.8224 | 54.2774 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score +2 | 52.2112 | 51.5720 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score >=+3 | 50.0158 | 49.1341 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| team_game mean | 59.1267 | 59.7353 | 0.03 | PASS | 2796 | n=2796 team-games |
| team_game sd | 10.0606 | 11.8616 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [0,40) | 0.0165 | 0.0279 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [40,50) | 0.1510 | 0.1652 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [50,60) | 0.3671 | 0.3283 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [60,70) | 0.3172 | 0.2800 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P >=70 | 0.1482 | 0.1985 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| game corr_home_away | -0.1981 | -0.3716 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |

## G3: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G4: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G5: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| P(total=0) | 0.0016 | 0.0007 | 0.01 | PASS | 1398 | stat=0.0009 |
| P(total=1) | 0.0254 | 0.0136 | 0.01 | FAIL | 1398 | stat=0.0118 |
| P(total=2) | 0.0391 | 0.0215 | 0.01 | FAIL | 1398 | stat=0.0177 |
| P(total=3) | 0.1360 | 0.1066 | 0.01 | FAIL | 1398 | stat=0.0294 |
| P(total=4) | 0.1100 | 0.1159 | 0.01 | PASS | 1398 | stat=-0.0058 |
| P(total=5) | 0.2180 | 0.1996 | 0.01 | FAIL | 1398 | stat=0.0184 |
| P(total=6) | 0.1169 | 0.1338 | 0.01 | FAIL | 1398 | stat=-0.0168 |
| P(total=7) | 0.1624 | 0.1617 | 0.01 | PASS | 1398 | stat=0.0007 |
| P(total=8) | 0.0650 | 0.0894 | 0.01 | FAIL | 1398 | stat=-0.0244 |
| P(total=9) | 0.0716 | 0.0851 | 0.01 | FAIL | 1398 | stat=-0.0136 |
| P(total=10) | 0.0540 | 0.0722 | 0.01 | FAIL | 1398 | stat=-0.0182 |
| total SD ratio | 2.3504 | 2.3155 | (0.95, 1.05) | PASS | 1398 | stat=1.0151 |
| margin SD ratio | 2.2702 | 2.5992 | (0.95, 1.05) | FAIL | 1398 | stat=0.8734 |
| score correlation | 0.0347 | -0.1151 | 0.05 | FAIL | 1398 | stat=0.1499 |
| KS total goals (p, n_eff=n_real) | 0.0000 |  | >=0.1 | FAIL | 1398 | D=0.0723 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5386 | 0.5651 | 0.015 | FAIL | 1398 | stat=-0.0265 |
| home goal diff | 0.2077 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1220 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.2045 | 0.2082 | 0.015 | PASS | 1398 | stat=-0.0036 |
| shootout rate | 0.0625 | 0.0551 | 0.01 | PASS | 1398 | stat=0.0074 |
| EN goals / game | 0.0000 | 0.4063 | 0.03 | FAIL | 1398 | stat=-0.4063 |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 5.6356 | 6.0336 | 0.1 | FAIL | 1398 | stat=-0.3980 |
| margin bias | 0.2077 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1220 |
| margin slope (actual on pred) | 1.1018 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.2894 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
