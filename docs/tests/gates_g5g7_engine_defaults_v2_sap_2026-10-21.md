# Gate report: engine_defaults_v2_sap (season 20242025, segment all)

Generated 2026-10-21 by `scripts/eval_gates.py`. Tolerances `docs/gates.yaml` (provisional). Sim rows 279600. run_meta: {'arm': 'A3g-c', 'attr_arm': 'L1x-as (SL-R7, H45 P10000)', 'round': 'SL-R7 closed loop (oracle goalie)', 'stand_in': ['miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable'], 'attr_model': 'stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)', 'goal_model': 'goal: C1s-sap (G-R4: as-of score-bucket deviations H90 P2000 + pooled period interactions)', 'oracle_goalie': 'ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)', 'stage1': "H3''-LC2 + T2 (D18; LC-2 level tables v5)", 'stage3': 'A3g-c (D20)', 'stage4': 'stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)', 'block': 'STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss': 'STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable', 'goal': 'goal: C1s (provisional, D40)', 'goalie': 'ORACLE GOALIE: box-score starter (D8)', 'goalie_pull': 'none (EN unreachable)', 'rebounds': 'none', 'overtime': 'stage-1 engine 3v3 OT with C1s goals', 'shootout': '50/50 stub', 'fold': 2, 'season': 20242025, 'sealed_touched': False, 'info': {'parity': {'l1xas': {'n_rows': 116716, 'max_abs_diff': 1.4875245590850739e-08, 'n_en_rows_not_served': 3208, 'note': 'offline file is float32 (rounding about 3e-8)'}, 'block': {'n_rows': 162300, 'max_abs_diff': 1.48918778974938e-08, 'max_abs_diff_st012_vs_sb_r1': 1.48918778974938e-08, 'before_vs_sb_r1_max': 1.48918778974938e-08, 'by_state': [{'state': '5v5', 'n': 135180, 'actual': 0.29039798786802784, 'served_before': 0.29226293342701615, 'served_after': 0.29226293342701615, 'max_abs_diff': 1.4730240027738262e-08}, {'state': 'PP', 'n': 21153, 'actual': 0.25216281378527866, 'served_before': 0.2611349108833808, 'served_after': 0.2611349108833808, 'max_abs_diff': 1.48918778974938e-08}, {'state': 'PK', 'n': 2963, 'actual': 0.12183597705028687, 'served_before': 0.12455453772878612, 'served_after': 0.12455453772878612, 'max_abs_diff': 7.333217533211922e-09}, {'state': '4v4', 'n': 1635, 'actual': 0.24036697247706423, 'served_before': 0.29035935157931675, 'served_after': 0.2369154759710732, 'max_abs_diff': 0.0}, {'state': '3v3', 'n': 1369, 'actual': 0.17531044558071585, 'served_before': 0.20880788266782382, 'served_after': 0.17059122542762026, 'max_abs_diff': 0.0}]}, 'miss': {'n_rows': 116716, 'max_abs_diff': 2.9797081801952174e-08, 'n_en_rows_not_served': 3208, 'by_state': [{'state': '5v5', 'n': 95924, 'actual': 0.34822359367832867, 'served': 0.3416620684589922}, {'state': 'PP', 'n': 15819, 'actual': 0.3234085593273911, 'served': 0.3116285899538505}, {'state': 'PK', 'n': 2602, 'actual': 0.20906994619523445, 'served': 0.2121047820017771}, {'state': '4v4', 'n': 1242, 'actual': 0.30434782608695654, 'served': 0.3265992804560165}, {'state': '3v3', 'n': 1129, 'actual': 0.2630646589902569, 'served': 0.28699904501661727}]}, 'goal': {'n_rows': 76926, 'n_starter_rows': 75045, 'n_relief_rows': 1881, 'max_abs_diff_starter': 1.1102230246251565e-16, 'relief_rows_served_starter_mean_abs_diff': 0.0030229405296047533, 'n_eaf_rows_not_served': 1487, 'max_abs_diff_relief_own_goalie': 1.1102230246251565e-16, 'max_abs_diff': 1.1102230246251565e-16, 'by_state': [{'state': '5v5', 'n': 62477, 'actual_goal_rate': 0.08988907918113866, 'offline': 0.09015991884576069, 'served': 0.09014458561663245}, {'state': 'PP', 'n': 10699, 'actual_goal_rate': 0.15178988690531825, 'offline': 0.1461620715388526, 'served': 0.1461163273029644}, {'state': 'PK', 'n': 2054, 'actual_goal_rate': 0.09104186952288218, 'offline': 0.09022505017515377, 'served': 0.09019330941544577}, {'state': '4v4', 'n': 864, 'actual_goal_rate': 0.11458333333333333, 'offline': 0.12492387027839356, 'served': 0.1249179667001278}, {'state': '3v3', 'n': 832, 'actual_goal_rate': 0.19591346153846154, 'offline': 0.20724828180253135, 'served': 0.2072016904073555}]}, 'block_b1aas': {'n_rows': 162300, 'max_abs_diff': 1.6653345369377348e-16, 'by_state': [{'state': '5v5', 'n': 135180, 'served': 0.29301828808378977, 'max_abs_diff': 1.1102230246251565e-16}, {'state': 'PP', 'n': 21153, 'served': 0.2616207025542262, 'max_abs_diff': 1.6653345369377348e-16}, {'state': 'PK', 'n': 2963, 'served': 0.12404841842436257, 'max_abs_diff': 1.1102230246251565e-16}, {'state': '4v4', 'n': 1635, 'served': 0.2365711554030638, 'max_abs_diff': 1.1102230246251565e-16}, {'state': '3v3', 'n': 1369, 'served': 0.17556962985174332, 'max_abs_diff': 8.326672684688674e-17}]}, 'goal_sap': {'n_rows': 76926, 'n_starter_rows': 75045, 'n_relief_rows': 1881, 'max_abs_diff_starter': 1.1102230246251565e-16, 'n_eaf_rows_not_served': 1487, 'engine': True, 'max_abs_diff_relief_own_goalie': 1.1102230246251565e-16, 'max_abs_diff': 1.1102230246251565e-16, 'by_bucket': [{'bucket': 'trail2+', 'n': 11814, 'actual': 0.09192483494159472, 'offline': 0.09040451173494216, 'served': 0.09040182998871696}, {'bucket': 'trail1', 'n': 14351, 'actual': 0.09776322207511672, 'offline': 0.09762397000115751, 'served': 0.09761057373102534}, {'bucket': 'tied', 'n': 27576, 'actual': 0.10102988105599071, 'offline': 0.09788026851973809, 'served': 0.09787923150815228}, {'bucket': 'lead1', 'n': 13147, 'actual': 0.1017722674374382, 'offline': 0.1030058653667141, 'served': 0.10301929521257373}, {'bucket': 'lead2+', 'n': 10038, 'actual': 0.10719266786212393, 'offline': 0.1061914021646558, 'served': 0.10604681586635123}]}}, 'l0s_level': {'level': 'M1_K500', 's_train': [[0.04711118133459736, 0.05698306736187918, 0.09346526570811609, 0.08980157476167905, 0.0682835624374572, 0.09077592563332806, 0.1003515563280139, 0.13335769210512455, 0.14475035550639911, 0.0923757044293464, 0.05314491494180228, 0.01882538052351609, 0.010773818928740717], [0.07264063883081907, 0.067668606512609, 0.10364050699662881, 0.08469405051132832, 0.07011695576021244, 0.10081548863400945, 0.12633482117633765, 0.17202478482776803, 0.15087481401962446, 0.036442736877789705, 0.006987212083545209, 0.0025236830706066257, 0.005235700698721209], [0.04340239912758997, 0.040567066521264995, 0.10119956379498364, 0.07219193020719739, 0.07644492911668484, 0.08026172300981461, 0.08876772082878953, 0.10632497273718648, 0.04296619411123228, 0.04285714285714286, 0.29465648854961835, 0.005234460196292257, 0.005125408942202835]], 'n_train_unblocked': 366059}, 'l1xas': {'cell': 'H45_P10000', 'sd': [0.022421323616881234, 0.01944876239278704], 'label': 'stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)'}, 'block': {'b0': {'level': 'M1_K500', 's_train': [0.26474304052974745, 0.24690447485993902, 0.12029930928626247], 'coef': [-1.0149500239491085, -1.4647801676278336, -1.1116794404880121, -1.2077237029833, -1.9710288022955673, -2.0457368676755645, -0.7152983631999071, -0.1960372252829194, -1.4264378088021497, -19.254496662424767]}, 'es_level_recompute_max_dev': 0.0, 'groups': {'4v4': {'coef': -1.2839836025921358, 's_train': 0.21938040345821325, 'n_train': 5552, 'n_train_blocked': 1218, 'n_iter': 6, 'n_train_by_ptype': {'0': 5302, '1': 250}}, '3v3': {'coef': -1.7030392051162135, 's_train': 0.15228197017623135, 'n_train': 4426, 'n_train_blocked': 674, 'n_iter': 7, 'n_train_by_ptype': {'0': 3, '1': 4423}}}}, 'miss': {'level': 'M2_H30', 's_train': [0.26836978410527795, 0.27702991452991454, 0.15761689291101055, 0.2926835400603419, 0.2949273617465286, 0.25356478611283323, 0.2955292524300608, 0.2833838142302992, 0.14140320485058466], 'n_train': 366059}, 'goal': {'label': 'goal: C1s (provisional, D40)', 'scale_cell': 'H90_P2000', 'sd_ref': 0.02713045865893978, 'team_cell': 'b10000_w0.7', 'goalie_cell': 'b3000_w0.5', 'spec': {'c_g': -1.779679228985303, 's_g': 0.5, 'c_t': 1.9535036450046972, 's_t': 1.0}, 'coef': [0.004954822570985042, -0.01751216082020263, 0.020411168647428847, 0.0371601701119814, 0.0682346370317749, 0.041514501719140805, -0.06309741456728205, -0.009125378144705104, 0.0535276413524435, 0.0640196861930157, 0.06901101831617736, 0.12362695933588201, -0.014252039336475135, -0.036324518139417276, 0.019607451465146662, 0.6882908764034937], 'level': 'M1_K500'}, 'block_b1aas': {'label': "block: B1a-as (SB-R5; B0' INV-54 + frozen SB-R4 B1a terms + as-of Ra scale H90 P2000, AS-1 floor f 0.5)", 'cell': 'H90_P2000', 'n_games': 1398}}, 'seed0': 0, 'nseeds': 50, 'n_seeds': 200, 'engine_tag': 'event_engine_stage3_sa_r1'}

| gate | status |
|---|---|
| G1 | NEEDS-INSTRUMENTATION |
| G2 | PASS |
| G3 | NEEDS-INSTRUMENTATION |
| G4 | NEEDS-INSTRUMENTATION |
| G5 | FAIL |
| G6 | FAIL |
| G7 | FAIL |
| G8 | NEEDS-INSTRUMENTATION |
| G9 | FAIL |

## G1: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G2: PASS

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| per60_state 5v5 | 58.6940 | 58.4717 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PP | 101.2881 | 101.7125 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PK | 14.0426 | 14.2473 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 4v4 | 50.0089 | 48.8019 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 3v3 | 55.5076 | 55.2313 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state EN-for | 0.0000 | 153.4874 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_state EN-against | 0.0000 | 48.4810 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_score <=-3 | 63.0798 | 65.4146 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| per60_score -2 | 63.8942 | 68.3894 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score -1 | 62.6318 | 64.3039 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score 0 | 58.9568 | 58.7080 | 0.03 | PASS | 2796 | n=984 team-hours |
| per60_score +1 | 54.7980 | 54.2774 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score +2 | 52.1452 | 51.5720 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score >=+3 | 49.8825 | 49.1341 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| team_game mean | 59.0681 | 59.7353 | 0.03 | PASS | 2796 | n=2796 team-games |
| team_game sd | 10.0669 | 11.8616 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [0,40) | 0.0169 | 0.0279 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [40,50) | 0.1526 | 0.1652 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [50,60) | 0.3672 | 0.3283 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [60,70) | 0.3160 | 0.2800 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P >=70 | 0.1474 | 0.1985 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| game corr_home_away | -0.2076 | -0.3716 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |

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
| P(total=0) | 0.0017 | 0.0007 | 0.01 | PASS | 1398 | stat=0.0010 |
| P(total=1) | 0.0267 | 0.0136 | 0.01 | FAIL | 1398 | stat=0.0132 |
| P(total=2) | 0.0417 | 0.0215 | 0.01 | FAIL | 1398 | stat=0.0203 |
| P(total=3) | 0.1392 | 0.1066 | 0.01 | FAIL | 1398 | stat=0.0326 |
| P(total=4) | 0.1150 | 0.1159 | 0.01 | PASS | 1398 | stat=-0.0008 |
| P(total=5) | 0.2166 | 0.1996 | 0.01 | FAIL | 1398 | stat=0.0170 |
| P(total=6) | 0.1187 | 0.1338 | 0.01 | FAIL | 1398 | stat=-0.0151 |
| P(total=7) | 0.1568 | 0.1617 | 0.01 | PASS | 1398 | stat=-0.0048 |
| P(total=8) | 0.0651 | 0.0894 | 0.01 | FAIL | 1398 | stat=-0.0243 |
| P(total=9) | 0.0676 | 0.0851 | 0.01 | FAIL | 1398 | stat=-0.0175 |
| P(total=10) | 0.0507 | 0.0722 | 0.01 | FAIL | 1398 | stat=-0.0215 |
| total SD ratio | 2.3353 | 2.3155 | (0.95, 1.05) | PASS | 1398 | stat=1.0085 |
| margin SD ratio | 2.3156 | 2.5992 | (0.95, 1.05) | FAIL | 1398 | stat=0.8909 |
| score correlation | 0.0085 | -0.1151 | 0.05 | FAIL | 1398 | stat=0.1236 |
| KS total goals (p, n_eff=n_real) | 0.0000 |  | >=0.1 | FAIL | 1398 | D=0.0832 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5390 | 0.5651 | 0.015 | FAIL | 1398 | stat=-0.0261 |
| home goal diff | 0.2148 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1149 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.1927 | 0.2082 | 0.015 | FAIL | 1398 | stat=-0.0155 |
| shootout rate | 0.0619 | 0.0551 | 0.01 | PASS | 1398 | stat=0.0068 |
| EN goals / game | 0.0000 | 0.4063 | 0.03 | FAIL | 1398 | stat=-0.4063 |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 5.5642 | 6.0336 | 0.1 | FAIL | 1398 | stat=-0.4694 |
| margin bias | 0.2148 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1149 |
| margin slope (actual on pred) | 1.0941 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.3397 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
