# Gate report: end_game_otso_v1 (season 20242025, segment RS)

Generated 2026-10-21 by `scripts/eval_gates.py`. Tolerances `docs/gates.yaml` (provisional). Sim rows 279600. run_meta: {'tag': 'end_game_otso_v1', 'pull': 'on', 'ot3v3': 'on', 'shootout': 'on', 'seed0': 0, 'nseeds': 67, 'fold': 2, 'season': 20242025, 'sealed_touched': False, 'stand_in': ['block: STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable'], 'attr_model': 'stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)', 'goal_model': 'goal: C1s (provisional, D40)', 'oracle_goalie': 'ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)', 'pull_model': 'goalie pull: P1 hazard (EG-R1 part A, selected on fold 2 after D45)', 'pull_stand_in': ['en_attempts: STAND-IN (EG-R1 part A): EN attempt rates = as-of M1 K500 league level per EN state (EN-for / EN-against attempts per team-hour, stage-3 attempt rows st 5 / 6); flat, no team terms', 'en_goal: STAND-IN (EG-R1 part A): goal per SOG into an empty net = as-of M1 K500 league level on st-6 SOG'], 'pull_info': {'arm': 'P1', 'levels': {'ef': {'20212022': 131.88450791679603, '20222023': 142.68891938554162, '20232024': 158.0782831362029, '20242025': 153.48737697903294}, 'ea': {'20212022': 43.487341593519794, '20222023': 47.545265394661115, '20232024': 44.189732959395194, '20242025': 48.48095849379546}, 'en_goal': {'20212022': 1.0, '20222023': 0.9976019184652278, '20232024': 1.0, '20242025': 1.0}}, 'n_games': 1398, 'block_en': {'groups': 'ENF, ENA (B0 own intercepts, ES level)', 'coef': [-0.7152983631999071, -0.1960372252829194, -1.4264378088021497, -19.254496662424767]}, 'miss_en': {'groups': 'ENF, ENA (S0t own base / coef, ES level group)', 'level': 'M2_H30'}, 'parity': {'hazard': {'n_rows': 523057, 'max_abs_diff': 0.0}, 'goal_eaf': {'n_rows': 1487, 'n_starter': 1464, 'max_abs_diff': 1.1102230246251565e-16, 'relief_rows_mean_abs_diff': 0.003277998669843697, 'served_mean': 0.1270275430891953, 'actual': 0.11499663752521856}, 'block': {'n_rows': 4720, 'max_abs_diff': 1.4743017084928312e-08, 'by_state': {'5': {'served': 0.3582946027306787, 'actual': 0.35433509896849735}, '6': {'served': 0.21513590073923494, 'actual': 0.21270962047661077}}}, 'miss': {'n_rows': 3208, 'max_abs_diff': 2.9798333800457044e-08, 'by_state': {'5': {'served': 0.34815935417427146, 'actual': 0.3579447322970639}, '6': {'served': 0.4719084711087683, 'actual': 0.42152466367713004}}}, 'class': {'n_rows': 3208, 'max_abs_diff': 2.9799554601694922e-08}}}, 'att_info': {'label': '3v3 OT attempt level: own as-of M1 K500 (EG-R1 part B), A3g-c cell refit on the training rows', 'parity': {'n_rows': 1690, 'max_rel_diff': 1.1951186273950754e-07, 'max_abs_diff': 8.379024990290418e-06}, 'train_y': 4426.0, 'train_mu_before_cell': 4494.847134201465, 'mean_delta': 0.0022827214395051334, 'cell_new': -0.015264302775071648, 'cell_old': -0.01333515648516252, 'level_name': 'M1_K500'}, 'shootout_model': 'shootout S1: rules mechanics, as-of M1 K500 per-attempt success, as-of home-first share (EG-R1 part C)', 'delayed_penalty': 'no engine state (INV-70)', 'info': {'parity': {'hazard': {'n_rows': 523057, 'max_abs_diff': 0.0}, 'goal_eaf': {'n_rows': 1487, 'n_starter': 1464, 'max_abs_diff': 1.1102230246251565e-16, 'relief_rows_mean_abs_diff': 0.003277998669843697, 'served_mean': 0.1270275430891953, 'actual': 0.11499663752521856}, 'block': {'n_rows': 4720, 'max_abs_diff': 1.4743017084928312e-08, 'by_state': {'5': {'served': 0.3582946027306787, 'actual': 0.35433509896849735}, '6': {'served': 0.21513590073923494, 'actual': 0.21270962047661077}}}, 'miss': {'n_rows': 3208, 'max_abs_diff': 2.9798333800457044e-08, 'by_state': {'5': {'served': 0.34815935417427146, 'actual': 0.3579447322970639}, '6': {'served': 0.4719084711087683, 'actual': 0.42152466367713004}}}, 'class': {'n_rows': 3208, 'max_abs_diff': 2.9799554601694922e-08}}}, 'n_seeds': 200, 'engine_tag': 'event_engine_stage3_sa_r1'}

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
| TOI 5v5 (min/game) | 50.2060 | 50.3903 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP total (min/game) | 9.1391 | 8.9496 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP home (min/game) | 4.6854 | 4.6680 | 0.75 | PASS | 1312 | delta=+0.0175 |
| TOI PP away (min/game) | 4.4537 | 4.2817 | 0.75 | PASS | 1312 | delta=+0.1720 |
| TOI 4v4 (min/game) | 0.7876 | 0.7284 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI 3v3 (min/game) | 0.6204 | 0.5668 | 0.75 | STUB-DEPENDENT | 1312 | STUB-DEPENDENT: 3v3 time is regular-season OT; OT frequency comes from the stub goals (literal PASS) |
| TOI 5v3/3v5 (min/game) | 0.1721 | 0.1472 | 0.75 | PASS | 1312 | PP minors end on stub goals: duration partly stub-driven |
| TOI EN (min/game) | 1.1004 | 1.0531 | 0.75 | STUB-DEPENDENT | 1312 | STUB-DEPENDENT: no goalie-pull model yet (stage 8) (literal PASS) |
| PP opps / team-game mean | 2.6569 | 2.5640 | 0.15 | PASS | 1312 | delta=+0.0929 |
| PP opps / team-game SD | 1.3769 | 1.2611 | 0.15 | PASS | 1312 | delta=+0.1158 |
| P(PP opps=0) | 0.0394 | 0.0259 |  | NO-TOLERANCE | 1312 | delta=+0.0135 |
| P(PP opps=1) | 0.1628 | 0.1711 |  | NO-TOLERANCE | 1312 | delta=-0.0083 |
| P(PP opps=2) | 0.2803 | 0.3243 |  | NO-TOLERANCE | 1312 | delta=-0.0440 |
| P(PP opps=3) | 0.2651 | 0.2584 |  | NO-TOLERANCE | 1312 | delta=+0.0067 |
| P(PP opps=4) | 0.1591 | 0.1543 |  | NO-TOLERANCE | 1312 | delta=+0.0048 |
| P(PP opps=5) | 0.0663 | 0.0484 |  | NO-TOLERANCE | 1312 | delta=+0.0179 |
| P(PP opps=6) | 0.0206 | 0.0133 |  | NO-TOLERANCE | 1312 | delta=+0.0072 |
| P(PP opps=7+) | 0.0065 | 0.0042 |  | NO-TOLERANCE | 1312 | delta=+0.0023 |
| penalty-taking events / team-game | 3.3367 | 3.2839 |  | NO-TOLERANCE | 1312 | delta=+0.0528 |
| PIM / game (strength penalties) | 15.0971 | 15.0252 |  | NO-TOLERANCE | 1312 | delta=+0.0720 |
| share of minors ended by PP goal | 0.2026 | 0.2129 |  | STUB-DEPENDENT | 1312 | STUB-DEPENDENT: PP-goal frequency is the stub goal rate (league, no team terms) (literal NO-TOLERANCE) |

## G2: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| per60_state 5v5 | 58.6344 | 58.3508 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state PP | 101.0883 | 101.6226 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state PK | 14.0149 | 14.3173 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state 4v4 | 50.1883 | 48.6237 | 0.03 | FAIL | 2624 | n=2624 team-games |
| per60_state 3v3 | 55.5884 | 55.2313 | 0.03 | PASS | 2624 | n=2624 team-games |
| per60_state EN-for | 0.0000 | 154.6454 | 0.03 | NO-TOLERANCE | 2624 | no goalie-pull model (stage 8) |
| per60_state EN-against | 0.0000 | 48.3382 | 0.03 | NO-TOLERANCE | 2624 | no goalie-pull model (stage 8) |
| per60_score <=-3 | 65.5694 | 65.4302 | 0.03 | UNDERPOWERED | 2624 | n=163 team-hours |
| per60_score -2 | 70.9534 | 68.2253 | 0.03 | UNDERPOWERED | 2624 | n=228 team-hours |
| per60_score -1 | 66.0497 | 64.2065 | 0.03 | PASS | 2624 | n=476 team-hours |
| per60_score 0 | 58.7362 | 58.6022 | 0.03 | PASS | 2624 | n=919 team-hours |
| per60_score +1 | 56.1947 | 54.1359 | 0.03 | FAIL | 2624 | n=476 team-hours |
| per60_score +2 | 54.9516 | 51.3994 | 0.03 | UNDERPOWERED | 2624 | n=228 team-hours |
| per60_score >=+3 | 50.5402 | 49.2586 | 0.03 | UNDERPOWERED | 2624 | n=163 team-hours |
| team_game mean | 57.9963 | 59.4832 | 0.03 | PASS | 2624 | n=2624 team-games |
| team_game sd | 9.8582 | 11.6141 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [0,40) | 0.0220 | 0.0286 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [40,50) | 0.1752 | 0.1700 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [50,60) | 0.3809 | 0.3266 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P [60,70) | 0.2985 | 0.2851 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| team_game_P >=70 | 0.1234 | 0.1898 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |
| game corr_home_away | -0.1959 | -0.4126 |  | NO-TOLERANCE | 2624 | SD ratio / P(k) / correlation: reported |

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
| P(total=0) | 0.0018 | 0.0008 | 0.01 | PASS | 1312 | stat=0.0010 |
| P(total=1) | 0.0146 | 0.0137 | 0.01 | PASS | 1312 | stat=0.0009 |
| P(total=2) | 0.0297 | 0.0206 | 0.01 | PASS | 1312 | stat=0.0091 |
| P(total=3) | 0.1079 | 0.1082 | 0.01 | PASS | 1312 | stat=-0.0003 |
| P(total=4) | 0.0994 | 0.1151 | 0.01 | FAIL | 1312 | stat=-0.0157 |
| P(total=5) | 0.2045 | 0.2043 | 0.01 | PASS | 1312 | stat=0.0003 |
| P(total=6) | 0.1246 | 0.1357 | 0.01 | FAIL | 1312 | stat=-0.0111 |
| P(total=7) | 0.1752 | 0.1562 | 0.01 | FAIL | 1312 | stat=0.0190 |
| P(total=8) | 0.0804 | 0.0892 | 0.01 | PASS | 1312 | stat=-0.0088 |
| P(total=9) | 0.0858 | 0.0823 | 0.01 | PASS | 1312 | stat=0.0035 |
| P(total=10) | 0.0761 | 0.0739 | 0.01 | PASS | 1312 | stat=0.0022 |
| total SD ratio | 2.3991 | 2.3201 | (0.95, 1.05) | PASS | 1312 | stat=1.0340 |
| margin SD ratio | 2.5093 | 2.5904 | (0.95, 1.05) | PASS | 1312 | stat=0.9687 |
| score correlation | -0.0449 | -0.1098 | 0.05 | FAIL | 1312 | stat=0.0649 |
| KS total goals (p, n_eff=n_real) | 0.8919 |  | >=0.1 | PASS | 1312 | D=0.0158 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5377 | 0.5625 | 0.015 | FAIL | 1312 | stat=-0.0248 |
| home goal diff | 0.2190 | 0.3163 | 0.08 | FAIL | 1312 | stat=-0.0973 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.2374 | 0.2066 | 0.015 | FAIL | 1312 | stat=0.0308 |
| shootout rate | 0.0810 | 0.0587 | 0.01 | FAIL | 1312 | stat=0.0223 |
| EN goals / game | 0.3449 | 0.3994 | 0.03 | FAIL | 1312 | stat=-0.0545 |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 6.0446 | 6.0221 | 0.1 | PASS | 1312 | stat=0.0225 |
| margin bias | 0.2190 | 0.3163 | 0.08 | FAIL | 1312 | stat=-0.0973 |
| margin slope (actual on pred) | 1.0054 | 1.0000 | (0.95, 1.05) | PASS | 1312 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.3461 | 1.0000 | (0.95, 1.05) | FAIL | 1312 | slope near 1 = calibrated spread; noisy at n~1400 |
