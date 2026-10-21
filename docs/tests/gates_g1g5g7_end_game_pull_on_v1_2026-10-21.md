# Gate report: end_game_pull_on_v1 (season 20242025, segment all)

Generated 2026-10-21 by `scripts/eval_gates.py`. Tolerances `docs/gates.yaml` (provisional). Sim rows 279600. run_meta: {'tag': 'end_game_pull_on_v1', 'pull': 'on', 'seed0': 0, 'nseeds': 50, 'fold': 2, 'season': 20242025, 'sealed_touched': False, 'stand_in': ['block: STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable'], 'attr_model': 'stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)', 'goal_model': 'goal: C1s (provisional, D40)', 'oracle_goalie': 'ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)', 'pull_model': 'goalie pull: P1 hazard (EG-R1 part A, selected on fold 2 after D45)', 'pull_stand_in': ['en_attempts: STAND-IN (EG-R1 part A): EN attempt rates = as-of M1 K500 league level per EN state (EN-for / EN-against attempts per team-hour, stage-3 attempt rows st 5 / 6); flat, no team terms', 'en_goal: STAND-IN (EG-R1 part A): goal per SOG into an empty net = as-of M1 K500 league level on st-6 SOG'], 'pull_info': {'arm': 'P1', 'levels': {'ef': {'20212022': 131.88450791679603, '20222023': 142.68891938554162, '20232024': 158.0782831362029, '20242025': 153.48737697903294}, 'ea': {'20212022': 43.487341593519794, '20222023': 47.545265394661115, '20232024': 44.189732959395194, '20242025': 48.48095849379546}, 'en_goal': {'20212022': 1.0, '20222023': 0.9976019184652278, '20232024': 1.0, '20242025': 1.0}}, 'n_games': 1398, 'block_en': {'groups': 'ENF, ENA (B0 own intercepts, ES level)', 'coef': [-0.7152983631999071, -0.1960372252829194, -1.4264378088021497, -19.254496662424767]}, 'miss_en': {'groups': 'ENF, ENA (S0t own base / coef, ES level group)', 'level': 'M2_H30'}, 'parity': {'hazard': {'n_rows': 523057, 'max_abs_diff': 0.0}, 'goal_eaf': {'n_rows': 1487, 'n_starter': 1464, 'max_abs_diff': 1.1102230246251565e-16, 'relief_rows_mean_abs_diff': 0.003277998669843697, 'served_mean': 0.1270275430891953, 'actual': 0.11499663752521856}, 'block': {'n_rows': 4720, 'max_abs_diff': 1.4743017084928312e-08, 'by_state': {'5': {'served': 0.3582946027306787, 'actual': 0.35433509896849735}, '6': {'served': 0.21513590073923494, 'actual': 0.21270962047661077}}}, 'miss': {'n_rows': 3208, 'max_abs_diff': 2.9798333800457044e-08, 'by_state': {'5': {'served': 0.34815935417427146, 'actual': 0.3579447322970639}, '6': {'served': 0.4719084711087683, 'actual': 0.42152466367713004}}}, 'class': {'n_rows': 3208, 'max_abs_diff': 2.9799554601694922e-08}}}, 'delayed_penalty': 'no engine state (INV-70)', 'info': {'parity': {'hazard': {'n_rows': 523057, 'max_abs_diff': 0.0}, 'goal_eaf': {'n_rows': 1487, 'n_starter': 1464, 'max_abs_diff': 1.1102230246251565e-16, 'relief_rows_mean_abs_diff': 0.003277998669843697, 'served_mean': 0.1270275430891953, 'actual': 0.11499663752521856}, 'block': {'n_rows': 4720, 'max_abs_diff': 1.4743017084928312e-08, 'by_state': {'5': {'served': 0.3582946027306787, 'actual': 0.35433509896849735}, '6': {'served': 0.21513590073923494, 'actual': 0.21270962047661077}}}, 'miss': {'n_rows': 3208, 'max_abs_diff': 2.9798333800457044e-08, 'by_state': {'5': {'served': 0.34815935417427146, 'actual': 0.3579447322970639}, '6': {'served': 0.4719084711087683, 'actual': 0.42152466367713004}}}, 'class': {'n_rows': 3208, 'max_abs_diff': 2.9799554601694922e-08}}}, 'n_seeds': 200, 'engine_tag': 'event_engine_stage3_sa_r1'}

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
| TOI PP total (min/game) | 9.1779 | 9.0293 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI PP home (min/game) | 4.7061 | 4.7101 | 0.75 | PASS | 1398 | delta=-0.0040 |
| TOI PP away (min/game) | 4.4718 | 4.3191 | 0.75 | PASS | 1398 | delta=+0.1527 |
| TOI 4v4 (min/game) | 0.7887 | 0.7282 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI 3v3 (min/game) | 0.5710 | 0.5319 | 0.75 | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: 3v3 time is regular-season OT; OT frequency comes from the stub goals (literal PASS) |
| TOI 5v3/3v5 (min/game) | 0.1733 | 0.1459 | 0.75 | PASS | 1398 | PP minors end on stub goals: duration partly stub-driven |
| TOI EN (min/game) | 1.0997 | 1.0577 | 0.75 | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: no goalie-pull model yet (stage 8) (literal PASS) |
| PP opps / team-game mean | 2.6698 | 2.5844 | 0.15 | PASS | 1398 | delta=+0.0854 |
| PP opps / team-game SD | 1.3805 | 1.2674 | 0.15 | PASS | 1398 | delta=+0.1131 |
| P(PP opps=0) | 0.0388 | 0.0261 |  | NO-TOLERANCE | 1398 | delta=+0.0127 |
| P(PP opps=1) | 0.1611 | 0.1656 |  | NO-TOLERANCE | 1398 | delta=-0.0045 |
| P(PP opps=2) | 0.2787 | 0.3219 |  | NO-TOLERANCE | 1398 | delta=-0.0432 |
| P(PP opps=3) | 0.2657 | 0.2622 |  | NO-TOLERANCE | 1398 | delta=+0.0036 |
| P(PP opps=4) | 0.1605 | 0.1563 |  | NO-TOLERANCE | 1398 | delta=+0.0042 |
| P(PP opps=5) | 0.0674 | 0.0497 |  | NO-TOLERANCE | 1398 | delta=+0.0177 |
| P(PP opps=6) | 0.0212 | 0.0139 |  | NO-TOLERANCE | 1398 | delta=+0.0072 |
| P(PP opps=7+) | 0.0067 | 0.0043 |  | NO-TOLERANCE | 1398 | delta=+0.0024 |
| penalty-taking events / team-game | 3.3527 | 3.3155 |  | NO-TOLERANCE | 1398 | delta=+0.0372 |
| PIM / game (strength penalties) | 15.1679 | 15.1252 |  | NO-TOLERANCE | 1398 | delta=+0.0428 |
| share of minors ended by PP goal | 0.2034 | 0.2141 |  | STUB-DEPENDENT | 1398 | STUB-DEPENDENT: PP-goal frequency is the stub goal rate (league, no team terms) (literal NO-TOLERANCE) |

## G2: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| per60_state 5v5 | 58.8095 | 58.4717 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PP | 101.3675 | 101.7125 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PK | 14.0573 | 14.2473 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 4v4 | 50.2324 | 48.8019 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 3v3 | 58.2266 | 55.2313 | 0.03 | FAIL | 2796 | n=2796 team-games |
| per60_state EN-for | 0.0000 | 153.4874 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_state EN-against | 0.0000 | 48.4810 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_score <=-3 | 65.7519 | 65.4146 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| per60_score -2 | 71.1278 | 68.3894 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score -1 | 66.2197 | 64.3039 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score 0 | 59.0295 | 58.7080 | 0.03 | PASS | 2796 | n=984 team-hours |
| per60_score +1 | 56.3146 | 54.2774 | 0.03 | FAIL | 2796 | n=508 team-hours |
| per60_score +2 | 55.0393 | 51.5720 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score >=+3 | 50.6298 | 49.1341 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| team_game mean | 58.2627 | 59.7353 | 0.03 | PASS | 2796 | n=2796 team-games |
| team_game sd | 10.0781 | 11.8616 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [0,40) | 0.0213 | 0.0279 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [40,50) | 0.1716 | 0.1652 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [50,60) | 0.3771 | 0.3283 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [60,70) | 0.2994 | 0.2800 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P >=70 | 0.1307 | 0.1985 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| game corr_home_away | -0.1571 | -0.3716 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |

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
| P(total=1) | 0.0147 | 0.0136 | 0.01 | PASS | 1398 | stat=0.0011 |
| P(total=2) | 0.0284 | 0.0215 | 0.01 | PASS | 1398 | stat=0.0069 |
| P(total=3) | 0.1084 | 0.1066 | 0.01 | PASS | 1398 | stat=0.0018 |
| P(total=4) | 0.0964 | 0.1159 | 0.01 | FAIL | 1398 | stat=-0.0195 |
| P(total=5) | 0.2069 | 0.1996 | 0.01 | PASS | 1398 | stat=0.0074 |
| P(total=6) | 0.1219 | 0.1338 | 0.01 | FAIL | 1398 | stat=-0.0119 |
| P(total=7) | 0.1781 | 0.1617 | 0.01 | FAIL | 1398 | stat=0.0165 |
| P(total=8) | 0.0791 | 0.0894 | 0.01 | FAIL | 1398 | stat=-0.0103 |
| P(total=9) | 0.0878 | 0.0851 | 0.01 | PASS | 1398 | stat=0.0026 |
| P(total=10) | 0.0767 | 0.0722 | 0.01 | PASS | 1398 | stat=0.0045 |
| total SD ratio | 2.4005 | 2.3155 | (0.95, 1.05) | PASS | 1398 | stat=1.0367 |
| margin SD ratio | 2.5096 | 2.5992 | (0.95, 1.05) | PASS | 1398 | stat=0.9655 |
| score correlation | -0.0444 | -0.1151 | 0.05 | FAIL | 1398 | stat=0.0707 |
| KS total goals (p, n_eff=n_real) | 0.9641 |  | >=0.1 | PASS | 1398 | D=0.0132 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5379 | 0.5651 | 0.015 | FAIL | 1398 | stat=-0.0272 |
| home goal diff | 0.2186 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1111 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.2376 | 0.2082 | 0.015 | FAIL | 1398 | stat=0.0294 |
| shootout rate | 0.0726 | 0.0551 | 0.01 | FAIL | 1398 | stat=0.0175 |
| EN goals / game | 0.3451 | 0.4063 | 0.03 | FAIL | 1398 | stat=-0.0612 |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 6.0625 | 6.0336 | 0.1 | PASS | 1398 | stat=0.0289 |
| margin bias | 0.2186 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1111 |
| margin slope (actual on pred) | 1.0152 | 1.0000 | (0.95, 1.05) | PASS | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.3013 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
