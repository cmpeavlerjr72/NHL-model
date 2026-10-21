# Gate report: engine_c1s_plumbing_v1 (season 20242025, segment all) -- PLUMBING, STAGES 7-8 ABSENT

> **PLUMBING RUN (INV-60). NOTHING HERE GATES. ORACLE GOALIE** (the box-score starter faces every shot on goal, D8; no in-game goalie change). Goal = **C1s (provisional, D40)**. STAND-INS: block B0 (own 4v4 / 3v3 groups, INV-54), stage-4 L0s (level M1 K500, INV-57), miss S0t (D37): flat, not adoptable; team-level and responsiveness readings that pass through them are not evidence about any model. Stages 7-8 absent (no rebounds, no goalie pull, no OT / shootout model: OT is the stage-1 engine's 3v3 OT, the shootout a 50 / 50 stub). G2 4v4 is listed under INV-42 and 3v3 under INV-35 (D26).

> **G5-G7 below are labelled plumbing, stages 7-8 absent** (no rebounds model, no goalie pull / EN goals, no OT / shootout model). They are not gate results. End states over 279,600 sim games: REG 221,431 (79.2%), OT 40,370 (14.4%), SO 17,799 (6.4%) (OT = stage-1 engine 3v3 OT with C1s goals; SO = 50/50 stub).

Generated 2026-10-21 by `scripts/eval_gates.py`. Tolerances `docs/gates.yaml` (provisional). Sim rows 279600. run_meta: {'arm': 'A3g-c', 'attr_arm': 'L0s STAND-IN (M1 K500)', 'round': 'INV-60 plumbing (oracle goalie)', 'stand_in': ['attr: STAND-IN (D32): stage-4 L0s (SL-R4 table) levelled by the M1 K500 as-of mix level (D35, INV-57); EN rows on the baseline; flat, not adoptable', 'block: STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable'], 'goal_model': 'goal: C1s (provisional, D40)', 'oracle_goalie': 'ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)', 'stage1': "H3''-LC2 + T2 (D18; LC-2 level tables v5)", 'stage3': 'A3g-c (D20)', 'stage4': 'STAND-IN (D32): stage-4 L0s (SL-R4 table) levelled by the M1 K500 as-of mix level (D35, INV-57); EN rows on the baseline; flat, not adoptable', 'block': 'STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss': 'STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable', 'goal': 'goal: C1s (provisional, D40)', 'goalie': 'ORACLE GOALIE: box-score starter (D8)', 'goalie_pull': 'none (EN unreachable)', 'rebounds': 'none (stage 7 absent)', 'overtime': 'stage-1 engine 3v3 OT with C1s goals (no OT model, stage 8 absent)', 'shootout': '50/50 stub', 'fold': 2, 'season': 20242025, 'sealed_touched': False, 'info': {'parity': {'l0s': {'n_rows': 119924, 'max_abs_diff': 2.9799554601694922e-08, 'max_abs_diff_reachable': 1.4372257273187472e-08, 'n_en_rows': 3208}, 'block': {'n_rows': 162300, 'max_abs_diff': 1.48918778974938e-08, 'max_abs_diff_st012_vs_sb_r1': 1.48918778974938e-08, 'before_vs_sb_r1_max': 1.48918778974938e-08, 'by_state': [{'state': '5v5', 'n': 135180, 'actual': 0.29039798786802784, 'served_before': 0.29226293342701615, 'served_after': 0.29226293342701615, 'max_abs_diff': 1.4730240027738262e-08}, {'state': 'PP', 'n': 21153, 'actual': 0.25216281378527866, 'served_before': 0.2611349108833808, 'served_after': 0.2611349108833808, 'max_abs_diff': 1.48918778974938e-08}, {'state': 'PK', 'n': 2963, 'actual': 0.12183597705028687, 'served_before': 0.12455453772878612, 'served_after': 0.12455453772878612, 'max_abs_diff': 7.333217533211922e-09}, {'state': '4v4', 'n': 1635, 'actual': 0.24036697247706423, 'served_before': 0.29035935157931675, 'served_after': 0.2369154759710732, 'max_abs_diff': 0.0}, {'state': '3v3', 'n': 1369, 'actual': 0.17531044558071585, 'served_before': 0.20880788266782382, 'served_after': 0.17059122542762026, 'max_abs_diff': 0.0}]}, 'miss': {'n_rows': 116716, 'max_abs_diff': 2.9797081801952174e-08, 'n_en_rows_not_served': 3208, 'by_state': [{'state': '5v5', 'n': 95924, 'actual': 0.34822359367832867, 'served': 0.3416620684589922}, {'state': 'PP', 'n': 15819, 'actual': 0.3234085593273911, 'served': 0.3116285899538505}, {'state': 'PK', 'n': 2602, 'actual': 0.20906994619523445, 'served': 0.2121047820017771}, {'state': '4v4', 'n': 1242, 'actual': 0.30434782608695654, 'served': 0.3265992804560165}, {'state': '3v3', 'n': 1129, 'actual': 0.2630646589902569, 'served': 0.28699904501661727}]}, 'goal': {'n_rows': 76926, 'n_starter_rows': 75045, 'n_relief_rows': 1881, 'max_abs_diff_starter': 1.1102230246251565e-16, 'relief_rows_served_starter_mean_abs_diff': 0.0030229405296047533, 'n_eaf_rows_not_served': 1487, 'max_abs_diff_relief_own_goalie': 1.1102230246251565e-16, 'max_abs_diff': 1.1102230246251565e-16, 'by_state': [{'state': '5v5', 'n': 62477, 'actual_goal_rate': 0.08988907918113866, 'offline': 0.09015991884576069, 'served': 0.09014458561663245}, {'state': 'PP', 'n': 10699, 'actual_goal_rate': 0.15178988690531825, 'offline': 0.1461620715388526, 'served': 0.1461163273029644}, {'state': 'PK', 'n': 2054, 'actual_goal_rate': 0.09104186952288218, 'offline': 0.09022505017515377, 'served': 0.09019330941544577}, {'state': '4v4', 'n': 864, 'actual_goal_rate': 0.11458333333333333, 'offline': 0.12492387027839356, 'served': 0.1249179667001278}, {'state': '3v3', 'n': 832, 'actual_goal_rate': 0.19591346153846154, 'offline': 0.20724828180253135, 'served': 0.2072016904073555}]}}, 'l0s': {'level': 'M1_K500', 's_train': [[0.04711118133459736, 0.05698306736187918, 0.09346526570811609, 0.08980157476167905, 0.0682835624374572, 0.09077592563332806, 0.1003515563280139, 0.13335769210512455, 0.14475035550639911, 0.0923757044293464, 0.05314491494180228, 0.01882538052351609, 0.010773818928740717], [0.07264063883081907, 0.067668606512609, 0.10364050699662881, 0.08469405051132832, 0.07011695576021244, 0.10081548863400945, 0.12633482117633765, 0.17202478482776803, 0.15087481401962446, 0.036442736877789705, 0.006987212083545209, 0.0025236830706066257, 0.005235700698721209], [0.04340239912758997, 0.040567066521264995, 0.10119956379498364, 0.07219193020719739, 0.07644492911668484, 0.08026172300981461, 0.08876772082878953, 0.10632497273718648, 0.04296619411123228, 0.04285714285714286, 0.29465648854961835, 0.005234460196292257, 0.005125408942202835]], 'n_train_unblocked': 366059}, 'block': {'b0': {'level': 'M1_K500', 's_train': [0.26474304052974745, 0.24690447485993902, 0.12029930928626247], 'coef': [-1.0149500239491085, -1.4647801676278336, -1.1116794404880121, -1.2077237029833, -1.9710288022955673, -2.0457368676755645, -0.7152983631999071, -0.1960372252829194, -1.4264378088021497, -19.254496662424767]}, 'es_level_recompute_max_dev': 0.0, 'groups': {'4v4': {'coef': -1.2839836025921358, 's_train': 0.21938040345821325, 'n_train': 5552, 'n_train_blocked': 1218, 'n_iter': 6, 'n_train_by_ptype': {'0': 5302, '1': 250}}, '3v3': {'coef': -1.7030392051162135, 's_train': 0.15228197017623135, 'n_train': 4426, 'n_train_blocked': 674, 'n_iter': 7, 'n_train_by_ptype': {'0': 3, '1': 4423}}}}, 'miss': {'level': 'M2_H30', 's_train': [0.26836978410527795, 0.27702991452991454, 0.15761689291101055, 0.2926835400603419, 0.2949273617465286, 0.25356478611283323, 0.2955292524300608, 0.2833838142302992, 0.14140320485058466], 'n_train': 366059}, 'goal': {'label': 'goal: C1s (provisional, D40)', 'scale_cell': 'H90_P2000', 'sd_ref': 0.02713045865893978, 'team_cell': 'b10000_w0.7', 'goalie_cell': 'b3000_w0.5', 'spec': {'c_g': -1.779679228985303, 's_g': 0.5, 'c_t': 1.9535036450046972, 's_t': 1.0}, 'coef': [0.004954822570985042, -0.01751216082020263, 0.020411168647428847, 0.0371601701119814, 0.0682346370317749, 0.041514501719140805, -0.06309741456728205, -0.009125378144705104, 0.0535276413524435, 0.0640196861930157, 0.06901101831617736, 0.12362695933588201, -0.014252039336475135, -0.036324518139417276, 0.019607451465146662, 0.6882908764034937], 'level': 'M1_K500'}}, 'seed0': 0, 'nseeds': 50, 'gates': 'NONE (plumbing; stages 7-8 absent)', 'n_seeds': 200, 'engine_tag': 'event_engine_c1s_inv60'}

| gate | status |
|---|---|
| G1 | NEEDS-INSTRUMENTATION |
| G2 | FAIL |
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

## G2: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| per60_state 5v5 | 58.7083 | 58.4717 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PP | 101.3396 | 101.7125 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state PK | 14.0456 | 14.2473 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 4v4 | 50.0843 | 48.8019 | 0.03 | PASS | 2796 | n=2796 team-games |
| per60_state 3v3 | 58.2375 | 55.2313 | 0.03 | FAIL | 2796 | n=2796 team-games |
| per60_state EN-for | 0.0000 | 153.4874 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_state EN-against | 0.0000 | 48.4810 | 0.03 | NO-TOLERANCE | 2796 | no goalie-pull model (stage 8) |
| per60_score <=-3 | 63.0107 | 65.4146 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| per60_score -2 | 63.7751 | 68.3894 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score -1 | 62.6301 | 64.3039 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score 0 | 59.0362 | 58.7080 | 0.03 | PASS | 2796 | n=984 team-hours |
| per60_score +1 | 54.7735 | 54.2774 | 0.03 | PASS | 2796 | n=508 team-hours |
| per60_score +2 | 52.1525 | 51.5720 | 0.03 | UNDERPOWERED | 2796 | n=242 team-hours |
| per60_score >=+3 | 49.9476 | 49.1341 | 0.03 | UNDERPOWERED | 2796 | n=174 team-hours |
| team_game mean | 59.1439 | 59.7353 | 0.03 | PASS | 2796 | n=2796 team-games |
| team_game sd | 10.0846 | 11.8616 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [0,40) | 0.0165 | 0.0279 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [40,50) | 0.1510 | 0.1652 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [50,60) | 0.3664 | 0.3283 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P [60,70) | 0.3170 | 0.2800 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| team_game_P >=70 | 0.1491 | 0.1985 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |
| game corr_home_away | -0.1955 | -0.3716 |  | NO-TOLERANCE | 2796 | SD ratio / P(k) / correlation: reported |

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
| P(total=0) | 0.0015 | 0.0007 | 0.01 | PASS | 1398 | stat=0.0008 |
| P(total=1) | 0.0249 | 0.0136 | 0.01 | FAIL | 1398 | stat=0.0113 |
| P(total=2) | 0.0391 | 0.0215 | 0.01 | FAIL | 1398 | stat=0.0177 |
| P(total=3) | 0.1357 | 0.1066 | 0.01 | FAIL | 1398 | stat=0.0291 |
| P(total=4) | 0.1107 | 0.1159 | 0.01 | PASS | 1398 | stat=-0.0052 |
| P(total=5) | 0.2182 | 0.1996 | 0.01 | FAIL | 1398 | stat=0.0187 |
| P(total=6) | 0.1151 | 0.1338 | 0.01 | FAIL | 1398 | stat=-0.0187 |
| P(total=7) | 0.1651 | 0.1617 | 0.01 | PASS | 1398 | stat=0.0035 |
| P(total=8) | 0.0642 | 0.0894 | 0.01 | FAIL | 1398 | stat=-0.0252 |
| P(total=9) | 0.0725 | 0.0851 | 0.01 | FAIL | 1398 | stat=-0.0126 |
| P(total=10) | 0.0529 | 0.0722 | 0.01 | FAIL | 1398 | stat=-0.0193 |
| total SD ratio | 2.3432 | 2.3155 | (0.95, 1.05) | PASS | 1398 | stat=1.0120 |
| margin SD ratio | 2.2226 | 2.5992 | (0.95, 1.05) | FAIL | 1398 | stat=0.8551 |
| score correlation | 0.0528 | -0.1151 | 0.05 | FAIL | 1398 | stat=0.1680 |
| KS total goals (p, n_eff=n_real) | 0.0000 |  | >=0.1 | FAIL | 1398 | D=0.0723 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5265 | 0.5651 | 0.015 | FAIL | 1398 | stat=-0.0386 |
| home goal diff | 0.1393 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1905 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.2080 | 0.2082 | 0.015 | PASS | 1398 | stat=-0.0001 |
| shootout rate | 0.0637 | 0.0551 | 0.01 | PASS | 1398 | stat=0.0086 |
| EN goals / game | 0.0000 | 0.4063 | 0.03 | FAIL | 1398 | stat=-0.4063 |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 5.6363 | 6.0336 | 0.1 | FAIL | 1398 | stat=-0.3973 |
| margin bias | 0.1393 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1905 |
| margin slope (actual on pred) | 1.1239 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.1272 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
