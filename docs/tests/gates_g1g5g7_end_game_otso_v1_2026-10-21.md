# Gate report: end_game_otso_v1 (season 20242025, segment all)

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
| TOI 5v5 (min/game) | 50.2869 | 50.5015 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP total (min/game) | 9.1789 | 9.0293 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP home (min/game) | 4.7066 | 4.7101 | 0.75 | PASS | 1398 | delta=-0.0035 |
| TOI PP away (min/game) | 4.4723 | 4.3191 | 0.75 | PASS | 1398 | delta=+0.1531 |
| TOI 4v4 (min/game) | 0.7889 | 0.7282 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI 3v3 (min/game) | 0.5823 | 0.5319 | 0.75 | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: 3v3 time is regular-season OT; OT frequency comes from the stub goals (literal PASS) |
| TOI 5v3/3v5 (min/game) | 0.1733 | 0.1459 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI EN (min/game) | 1.0997 | 1.0577 | 0.75 | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: no goalie-pull model yet (stage 8) (literal PASS) |
| PP opps / team-game mean | 2.6702 | 2.5844 | 0.15 | PASS | 1398 | delta=+0.0858 |
| PP opps / team-game SD | 1.3806 | 1.2674 | 0.15 | PASS | 1398 | delta=+0.1132 |
| P(PP opps=0) | 0.0387 | 0.0261 |  | NO-TOLERANCE | 1398 | delta=+0.0126 |
| P(PP opps=1) | 0.1611 | 0.1656 |  | NO-TOLERANCE | 1398 | delta=-0.0045 |
| P(PP opps=2) | 0.2786 | 0.3219 |  | NO-TOLERANCE | 1398 | delta=-0.0432 |
| P(PP opps=3) | 0.2657 | 0.2622 |  | NO-TOLERANCE | 1398 | delta=+0.0036 |
| P(PP opps=4) | 0.1605 | 0.1563 |  | NO-TOLERANCE | 1398 | delta=+0.0042 |
| P(PP opps=5) | 0.0674 | 0.0497 |  | NO-TOLERANCE | 1398 | delta=+0.0177 |
| P(PP opps=6) | 0.0212 | 0.0139 |  | NO-TOLERANCE | 1398 | delta=+0.0072 |
| P(PP opps=7+) | 0.0067 | 0.0043 |  | NO-TOLERANCE | 1398 | delta=+0.0024 |
| penalty-taking events / team-game | 3.3531 | 3.3155 |  | NO-TOLERANCE | 1398 | delta=+0.0376 |
| PIM / game (strength penalties) | 15.1697 | 15.1252 |  | NO-TOLERANCE | 1398 | delta=+0.0445 |
| share of minors ended by PP goal | 0.2034 | 0.2141 |  | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: PP-goal frequency is the stub goal rate (league, no team terms) (literal NO-TOLERANCE) |

## G2: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| per60_state 5v5 | 58.8095 | 58.4717 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PP | 101.3718 | 101.7125 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PK | 14.0575 | 14.2473 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 4v4 | 50.2365 | 48.8019 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 3v3 | 55.5876 | 55.2313 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state EN-for | 0.0000 | 153.4874 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_state EN-against | 0.0000 | 48.4810 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_score <=-3 | 65.7519 | 65.4146 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| per60_score -2 | 71.1277 | 68.3894 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score -1 | 66.2198 | 64.3039 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score 0 | 58.9596 | 58.7080 | 0.03 | PASS | 2796 | n=984 team-hours |
| per60_score +1 | 56.3146 | 54.2774 | 0.03 | FAIL | 2796 | n=508 team-hours |
| per60_score +2 | 55.0393 | 51.5720 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score >=+3 | 50.6297 | 49.1341 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| team_game mean | 58.2493 | 59.7353 | 0.03 | PASS | 2796 | n=2796 team-games |
| team_game sd | 10.0708 | 11.8616 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [0,40) | 0.0213 | 0.0279 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [40,50) | 0.1718 | 0.1652 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [50,60) | 0.3773 | 0.3283 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [60,70) | 0.2994 | 0.2800 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P >=70 | 0.1302 | 0.1985 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| game corr_home_away | -0.1583 | -0.3716 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |

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
| P(total=0) | 0.0017 | 0.0007 | 0.01 | PASS | 1398 | stat=0.0009 |
| P(total=1) | 0.0146 | 0.0136 | 0.01 | PASS | 1398 | stat=0.0010 |
| P(total=2) | 0.0289 | 0.0215 | 0.01 | PASS | 1398 | stat=0.0074 |
| P(total=3) | 0.1079 | 0.1066 | 0.01 | PASS | 1398 | stat=0.0013 |
| P(total=4) | 0.0975 | 0.1159 | 0.01 | FAIL | 1398 | stat=-0.0184 |
| P(total=5) | 0.2059 | 0.1996 | 0.01 | PASS | 1398 | stat=0.0063 |
| P(total=6) | 0.1229 | 0.1338 | 0.01 | FAIL | 1398 | stat=-0.0109 |
| P(total=7) | 0.1771 | 0.1617 | 0.01 | FAIL | 1398 | stat=0.0154 |
| P(total=8) | 0.0796 | 0.0894 | 0.01 | PASS | 1398 | stat=-0.0098 |
| P(total=9) | 0.0872 | 0.0851 | 0.01 | PASS | 1398 | stat=0.0021 |
| P(total=10) | 0.0767 | 0.0722 | 0.01 | PASS | 1398 | stat=0.0045 |
| total SD ratio | 2.4010 | 2.3155 | (0.95, 1.05) | PASS | 1398 | stat=1.0369 |
| margin SD ratio | 2.5089 | 2.5992 | (0.95, 1.05) | PASS | 1398 | stat=0.9652 |
| score correlation | -0.0440 | -0.1151 | 0.05 | FAIL | 1398 | stat=0.0712 |
| KS total goals (p, n_eff=n_real) | 0.9834 |  | >=0.1 | PASS | 1398 | D=0.0122 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5377 | 0.5651 | 0.015 | FAIL | 1398 | stat=-0.0274 |
| home goal diff | 0.2184 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1114 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.2376 | 0.2082 | 0.015 | FAIL | 1398 | stat=0.0294 |
| shootout rate | 0.0760 | 0.0551 | 0.01 | FAIL | 1398 | stat=0.0209 |
| EN goals / game | 0.3451 | 0.4063 | 0.03 | FAIL | 1398 | stat=-0.0612 |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 6.0591 | 6.0336 | 0.1 | PASS | 1398 | stat=0.0254 |
| margin bias | 0.2184 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1114 |
| margin slope (actual on pred) | 1.0153 | 1.0000 | (0.95, 1.05) | PASS | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.3002 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
