# Gate report: end_game_pull_off_v1 (season 20242025, segment RS)

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
| TOI 5v5 (min/game) | 50.1998 | 50.3903 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP total (min/game) | 9.1325 | 8.9496 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP home (min/game) | 4.6813 | 4.6680 | 0.75 | PASS | 1312 | delta=+0.0133 |
| TOI PP away (min/game) | 4.4513 | 4.2817 | 0.75 | PASS | 1312 | delta=+0.1696 |
| TOI 4v4 (min/game) | 0.7806 | 0.7284 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI 3v3 (min/game) | 0.5234 | 0.5668 | 0.75 | STUB-DEPENDENT | 1312 | STUB-DEPENDENT: 3v3 time is regular-season OT; OT frequency comes from the stub goals (literal PASS) |
| TOI 5v3/3v5 (min/game) | 0.1721 | 0.1472 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI EN (min/game) | 0.0000 | 1.0531 | 0.75 | STUB-DEPENDENT | 1312 | STUB-DEPENDENT: no goalie-pull model yet (stage 8) (literal FAIL) |
| PP opps / team-game mean | 2.6526 | 2.5640 | 0.15 | PASS | 1312 | delta=+0.0886 |
| PP opps / team-game SD | 1.3757 | 1.2611 | 0.15 | PASS | 1312 | delta=+0.1145 |
| P(PP opps=0) | 0.0396 | 0.0259 |  | NO-TOLERANCE | 1312 | delta=+0.0137 |
| P(PP opps=1) | 0.1633 | 0.1711 |  | NO-TOLERANCE | 1312 | delta=-0.0078 |
| P(PP opps=2) | 0.2808 | 0.3243 |  | NO-TOLERANCE | 1312 | delta=-0.0435 |
| P(PP opps=3) | 0.2649 | 0.2584 |  | NO-TOLERANCE | 1312 | delta=+0.0065 |
| P(PP opps=4) | 0.1587 | 0.1543 |  | NO-TOLERANCE | 1312 | delta=+0.0043 |
| P(PP opps=5) | 0.0659 | 0.0484 |  | NO-TOLERANCE | 1312 | delta=+0.0175 |
| P(PP opps=6) | 0.0204 | 0.0133 |  | NO-TOLERANCE | 1312 | delta=+0.0071 |
| P(PP opps=7+) | 0.0064 | 0.0042 |  | NO-TOLERANCE | 1312 | delta=+0.0022 |
| penalty-taking events / team-game | 3.3314 | 3.2839 |  | NO-TOLERANCE | 1312 | delta=+0.0475 |
| PIM / game (strength penalties) | 15.0730 | 15.0252 |  | NO-TOLERANCE | 1312 | delta=+0.0478 |
| share of minors ended by PP goal | 0.2010 | 0.2129 |  | STUB-DEPENDENT | 1312 | STUB-DEPENDENT: PP-goal frequency is the stub goal rate (league, no team terms) (literal NO-TOLERANCE) |

## G2: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| per60_state 5v5 | 58.5310 | 58.3508 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state PP | 101.0279 | 101.6226 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state PK | 14.0039 | 14.3173 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state 4v4 | 50.0066 | 48.6237 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state 3v3 | 58.1633 | 55.2313 | 0.03 | FAIL | 2624 | n=2624 team-games |
| per60_state EN-for | 0.0000 | 154.6454 | 0.03 | NO-TOLERANCE | 2624 | no goalie-pull model (stage 8) |
| per60_state EN-against | 0.0000 | 48.3382 | 0.03 | NO-TOLERANCE | 2624 | no goalie-pull model (stage 8) |
| per60_score <=-3 | 62.8059 | 65.4302 | 0.03 | UNDERPOWERED | 2624 | n=163 team-hours |
| per60_score -2 | 63.5758 | 68.2253 | 0.03 | UNDERPOWERED | 2624 | n=228 team-hours |
| per60_score -1 | 62.4204 | 64.2065 | 0.03 | PASS | 2624 | n=476 team-hours |
| per60_score 0 | 58.8102 | 58.6022 | 0.03 | PASS | 2624 | n=919 team-hours |
| per60_score +1 | 54.7059 | 54.1359 | 0.03 | PASS | 2624 | n=476 team-hours |
| per60_score +2 | 52.1339 | 51.3994 | 0.03 | UNDERPOWERED | 2624 | n=228 team-hours |
| per60_score >=+3 | 49.9236 | 49.2586 | 0.03 | UNDERPOWERED | 2624 | n=163 team-hours |
| team_game mean | 58.8875 | 59.4832 | 0.03 | PASS | 2624 | n=2624 team-games |
| team_game sd | 9.8750 | 11.6141 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [0,40) | 0.0170 | 0.0286 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [40,50) | 0.1542 | 0.1700 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [50,60) | 0.3708 | 0.3266 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [60,70) | 0.3165 | 0.2851 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P >=70 | 0.1415 | 0.1898 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| game corr_home_away | -0.2307 | -0.4126 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |

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
| P(total=0) | 0.0017 | 0.0008 | 0.01 | PASS | 1312 | stat=0.0009 |
| P(total=1) | 0.0255 | 0.0137 | 0.01 | FAIL | 1312 | stat=0.0118 |
| P(total=2) | 0.0399 | 0.0206 | 0.01 | FAIL | 1312 | stat=0.0193 |
| P(total=3) | 0.1361 | 0.1082 | 0.01 | FAIL | 1312 | stat=0.0279 |
| P(total=4) | 0.1115 | 0.1151 | 0.01 | PASS | 1312 | stat=-0.0036 |
| P(total=5) | 0.2168 | 0.2043 | 0.01 | FAIL | 1312 | stat=0.0126 |
| P(total=6) | 0.1183 | 0.1357 | 0.01 | FAIL | 1312 | stat=-0.0173 |
| P(total=7) | 0.1608 | 0.1562 | 0.01 | PASS | 1312 | stat=0.0046 |
| P(total=8) | 0.0654 | 0.0892 | 0.01 | FAIL | 1312 | stat=-0.0237 |
| P(total=9) | 0.0703 | 0.0823 | 0.01 | FAIL | 1312 | stat=-0.0120 |
| P(total=10) | 0.0536 | 0.0739 | 0.01 | FAIL | 1312 | stat=-0.0204 |
| total SD ratio | 2.3474 | 2.3201 | (0.95, 1.05) | PASS | 1312 | stat=1.0118 |
| margin SD ratio | 2.2712 | 2.5904 | (0.95, 1.05) | FAIL | 1312 | stat=0.8768 |
| score correlation | 0.0330 | -0.1098 | 0.05 | FAIL | 1312 | stat=0.1428 |
| KS total goals (p, n_eff=n_real) | 0.0000 |  | >=0.1 | FAIL | 1312 | D=0.0689 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5386 | 0.5625 | 0.015 | FAIL | 1312 | stat=-0.0239 |
| home goal diff | 0.2087 | 0.3163 | 0.08 | FAIL | 1312 | stat=-0.1076 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.2043 | 0.2066 | 0.015 | PASS | 1312 | stat=-0.0022 |
| shootout rate | 0.0666 | 0.0587 | 0.01 | PASS | 1312 | stat=0.0079 |
| EN goals / game | 0.0000 | 0.3994 | 0.03 | FAIL | 1312 | stat=-0.3994 |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 5.6221 | 6.0221 | 0.1 | FAIL | 1312 | stat=-0.4000 |
| margin bias | 0.2087 | 0.3163 | 0.08 | FAIL | 1312 | stat=-0.1076 |
| margin slope (actual on pred) | 1.0902 | 1.0000 | (0.95, 1.05) | FAIL | 1312 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.3340 | 1.0000 | (0.95, 1.05) | FAIL | 1312 | slope near 1 = calibrated spread; noisy at n~1400 |
